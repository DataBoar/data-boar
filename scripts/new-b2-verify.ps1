#Requires -Version 5.1
<#
.SYNOPSIS
    Post-remediation audit: temp clone + git checks focused on non-public-identity leaks.

.DESCRIPTION
    Clones the repo under %TEMP%, then:
    - When -TargetUserSegment is empty or allowlisted (fabio): skips Windows profile path
      pickaxe/grep across all refs (maintainer public identity per PII_CONTEXT / Session B).
    - Otherwise: runs git log -S and batched git grep across refs for C:\Users\<segment>,
      with UTF-8 file output to avoid Windows console encoding failures.
    - Always: HEAD grep for the documented placeholder C:\Users\<username> (expected present in docs).

    SAFE here means "no unexpected Windows username segment probe hits", not full PII coverage -
    use PII_LOCAL_SEEDS / pii-fresh-audit for third-party literals.

.PARAMETER RepoUrl
    Repository URL to clone.

.PARAMETER TempCloneName
    Folder name under $env:TEMP for the temporary clone.

.PARAMETER KeepClone
    Keep the temporary clone after execution.

.PARAMETER RunCheckAll
    Also run full validation gate (uv sync + scripts/check-all.ps1).

.PARAMETER TargetUserSegment
    Windows profile segment to probe (incident response). Omit or use allowlisted value
    to skip maintainer-path history checks.

.PARAMETER RevListBatchSize
    Max refs per git grep invocation (avoids command-line length limits).

.PARAMETER MaxRefsToScan
    Cap git rev-list --all (0 = no cap). Use e.g. 20000 for a smoke pass on huge repos.

.EXAMPLE
    .\scripts\new-b2-verify.ps1

.EXAMPLE
    .\scripts\new-b2-verify.ps1 -RunCheckAll -KeepClone

.EXAMPLE
    .\scripts\new-b2-verify.ps1 -TargetUserSegment contractorX
#>
param(
    [string]$RepoUrl = "https://github.com/DataBoar/data-boar.git",
    [string]$TempCloneName = "data-boar-reaudit-short",
    [switch]$KeepClone,
    [switch]$RunCheckAll,
    [string]$TargetUserSegment = "",
    [int]$RevListBatchSize = 48,
    [int]$MaxRefsToScan = 0
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Maintainer public identity: path probes must not FAIL for these (Session B taxonomy).
$script:MaintainerPathSegments = @(
    "fabio"
)

function Test-IsAllowlistedMaintainerSegment {
    param([string]$Segment)
    if ([string]::IsNullOrWhiteSpace($Segment)) { return $true }
    $t = $Segment.Trim()
    foreach ($m in $script:MaintainerPathSegments) {
        if ($t.Equals($m, [System.StringComparison]::OrdinalIgnoreCase)) {
            return $true
        }
    }
    return $false
}

function Write-Step {
    param([string]$Message)
    Write-Host "`n=== $Message ===" -ForegroundColor Cyan
}

function Invoke-AuditCheck {
    param(
        [string]$Name,
        [string]$CommandText,
        [scriptblock]$Command,
        [ValidateSet("zero","any")]
        [string]$Expected = "zero"
    )

    Write-Host ""
    Write-Host ">>> $CommandText" -ForegroundColor Yellow
    $prevEap = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $output = & $Command 2>&1
    $ErrorActionPreference = $prevEap
    $exitCode = $LASTEXITCODE
    $lines = @($output)

    if ($exitCode -gt 1) {
        Write-Host "Exit code: $exitCode (error)" -ForegroundColor Red
        if ($lines.Count -gt 0) { $lines | ForEach-Object { Write-Host $_ } }
        return [PSCustomObject]@{
            Name      = $Name
            Command   = $CommandText
            ExitCode  = $exitCode
            MatchCount= $lines.Count
            Passed    = $false
        }
    }

    $passed = $true
    if ($Expected -eq "zero" -and $lines.Count -ne 0) {
        $passed = $false
    }

    Write-Host "Exit code: $exitCode"
    Write-Host "Match count: $($lines.Count)"
    if ($lines.Count -gt 0) { $lines | ForEach-Object { Write-Host $_ } }

    return [PSCustomObject]@{
        Name       = $Name
        Command    = $CommandText
        ExitCode   = $exitCode
        MatchCount = $lines.Count
        Passed     = $passed
    }
}

function Invoke-GitGrepFixedStringAcrossRefs {
    <#
    Returns @{ ExitCode = int; MatchLineCount = int; OutFile = string }
    git grep: 0 = matches, 1 = no matches, >1 error. Output streamed to UTF-8 file to avoid console crashes.
    #>
    param(
        [string]$RepoRoot,
        [string]$Pattern,
        [int]$BatchSize,
        [int]$MaxRefs
    )

    $outFile = Join-Path $env:TEMP ("new-b2-verify-grep-{0}.txt" -f [Guid]::NewGuid().ToString("n"))
    $revFile = Join-Path $env:TEMP ("new-b2-verify-revs-{0}.txt" -f [Guid]::NewGuid().ToString("n"))
    try {
        Push-Location $RepoRoot
        $revArgs = @("-c", "core.quotepath=false", "rev-list", "--all")
        if ($MaxRefs -gt 0) {
            $revArgs += @("--max-count=$MaxRefs")
        }
        $null = & git @revArgs 2>&1 | Out-File -FilePath $revFile -Encoding utf8
        if ($LASTEXITCODE -ne 0) {
            return @{ ExitCode = $LASTEXITCODE; MatchLineCount = -1; OutFile = $revFile; Error = "rev-list failed" }
        }

        $revs = [System.Collections.Generic.List[string]]::new()
        $sr = New-Object System.IO.StreamReader($revFile, [System.Text.UTF8Encoding]::new($false), $true)
        try {
            while ($null -ne ($line = $sr.ReadLine())) {
                $t = $line.Trim()
                if ($t.Length -gt 0) { $revs.Add($t) }
            }
        }
        finally {
            $sr.Dispose()
        }

        $fs = [System.IO.File]::Open($outFile, [System.IO.FileMode]::Create, [System.IO.FileAccess]::Write, [System.IO.FileShare]::Read)
        $sw = New-Object System.IO.StreamWriter($fs, [System.Text.UTF8Encoding]::new($false))
        $sw.NewLine = "`n"
        $totalMatches = 0
        $grepExit = 1
        try {
            for ($i = 0; $i -lt $revs.Count; $i += $batchSize) {
                $end = [Math]::Min($i + $batchSize - 1, $revs.Count - 1)
                $batch = $revs.GetRange($i, $end - $i + 1)
                $grepArgs = @("-c", "core.quotepath=false", "grep", "--no-color", "-n", "-i", "-F", $Pattern, "--") + $batch
                $prevEap = $ErrorActionPreference
                $ErrorActionPreference = "Continue"
                $chunk = & git @grepArgs 2>&1
                $ec = $LASTEXITCODE
                $ErrorActionPreference = $prevEap
                if ($ec -eq 0) {
                    $grepExit = 0
                    foreach ($ln in @($chunk)) {
                        $sw.WriteLine([string]$ln)
                        $totalMatches++
                    }
                }
                elseif ($ec -gt 1) {
                    foreach ($ln in @($chunk)) { $sw.WriteLine([string]$ln) }
                    $sw.Flush()
                    return @{ ExitCode = $ec; MatchLineCount = $totalMatches; OutFile = $outFile; Error = "git grep error" }
                }
            }
        }
        finally {
            $sw.Dispose()
            $fs.Dispose()
        }

        return @{ ExitCode = $grepExit; MatchLineCount = $totalMatches; OutFile = $outFile; Error = "" }
    }
    finally {
        Pop-Location
        if (Test-Path -LiteralPath $revFile) { Remove-Item -LiteralPath $revFile -Force -ErrorAction SilentlyContinue }
    }
}

function Invoke-AuditCheckGrepRefsToFile {
    param(
        [string]$Name,
        [string]$RepoRoot,
        [string]$Pattern,
        [int]$BatchSize,
        [int]$MaxRefs
    )

    $cmdHint = "git grep (batched refs, output UTF-8 temp file) pattern=$Pattern"
    Write-Host ""
    Write-Host ">>> $cmdHint" -ForegroundColor Yellow

    $r = Invoke-GitGrepFixedStringAcrossRefs -RepoRoot $RepoRoot -Pattern $Pattern -BatchSize $BatchSize -MaxRefs $MaxRefs
    $exitCode = [int]$r.ExitCode
    $matchCount = [int]$r.MatchLineCount
    $outFile = [string]$r.OutFile

    Write-Host "Exit code: $exitCode"
    Write-Host "Match line count (aggregated): $matchCount"
    if ($r.Error) { Write-Host "Note: $($r.Error)" -ForegroundColor DarkYellow }
    if ($matchCount -gt 0 -and (Test-Path -LiteralPath $outFile)) {
        Write-Host "First lines (max 40) from $outFile :" -ForegroundColor DarkGray
        $shown = 0
        $lr = New-Object System.IO.StreamReader($outFile, [System.Text.UTF8Encoding]::new($false), $true)
        try {
            while (($null -ne ($gline = $lr.ReadLine())) -and $shown -lt 40) {
                Write-Host $gline
                $shown++
            }
        }
        finally {
            $lr.Dispose()
        }
        if ($matchCount -gt 40) {
            Write-Host "... ($($matchCount - 40) more lines in temp file)" -ForegroundColor DarkGray
        }
    }

    $passed = ($exitCode -le 1) -and ($matchCount -eq 0)
    if (-not $passed -and $exitCode -le 1 -and $matchCount -gt 0) {
        $passed = $false
    }
    if ($exitCode -gt 1) { $passed = $false }

    if (Test-Path -LiteralPath $outFile) {
        Remove-Item -LiteralPath $outFile -Force -ErrorAction SilentlyContinue
    }

    return [PSCustomObject]@{
        Name       = $Name
        Command    = $cmdHint
        ExitCode   = $exitCode
        MatchCount = $matchCount
        Passed     = $passed
    }
}

$tempRoot = $env:TEMP
$clonePath = Join-Path $tempRoot $TempCloneName
$skipMaintainerPathProbe = Test-IsAllowlistedMaintainerSegment -Segment $TargetUserSegment
$targetUserPath = if ($TargetUserSegment) {
    "C:\Users\" + $TargetUserSegment.Trim()
} else {
    "C:\Users\<username>"
}
$targetUserPathLower = $targetUserPath.ToLowerInvariant()
$targetPlaceholder = "C:\Users\<username>"

Write-Step "Preparing fresh clone"
Write-Host "RepoUrl: $RepoUrl"
Write-Host "ClonePath: $clonePath"
Write-Host "TargetUserSegment: $(if ($TargetUserSegment) { $TargetUserSegment } else { '(none)' })"
Write-Host "Skip maintainer-path history probes: $skipMaintainerPathProbe"
if (Test-Path -LiteralPath $clonePath) {
    Remove-Item -LiteralPath $clonePath -Recurse -Force
}
git clone $RepoUrl $clonePath
if ($LASTEXITCODE -ne 0) {
    throw "git clone failed."
}

Push-Location $clonePath
try {
    Write-Step "Running audit checks"
    $results = @()

    if (-not $skipMaintainerPathProbe) {
        $results += Invoke-AuditCheck `
            -Name "log_s_users_path_uppercase" `
            -CommandText ("git log --all -S `"{0}`" --oneline" -f $targetUserPath) `
            -Command { git log --all -S $targetUserPath --oneline } `
            -Expected "zero"

        $results += Invoke-AuditCheck `
            -Name "log_s_users_path_lowercase" `
            -CommandText ("git log --all -S `"{0}`" --oneline" -f $targetUserPathLower) `
            -Command { git log --all -S $targetUserPathLower --oneline } `
            -Expected "zero"

        $results += Invoke-AuditCheckGrepRefsToFile `
            -Name "grep_all_revs_users_path_case_insensitive" `
            -RepoRoot $clonePath `
            -Pattern $targetUserPath `
            -BatchSize $RevListBatchSize `
            -MaxRefs $MaxRefsToScan
    }
    else {
        Write-Host ""
        Write-Host "[Skipped] Windows profile path history probes (empty or allowlisted maintainer segment)." -ForegroundColor DarkYellow
        Write-Host "          FabioLeitao / C:\Users\fabio / /home/leitao are treated as public maintainer identity." -ForegroundColor DarkYellow
    }

    $results += Invoke-AuditCheck `
        -Name "grep_head_placeholder" `
        -CommandText ("git grep -n -F `"{0}`" -- `":(exclude)*.lock`"" -f $targetPlaceholder) `
        -Command { git grep -n -F $targetPlaceholder -- ":(exclude)*.lock" } `
        -Expected "any"

    if ($RunCheckAll) {
        Write-Step "Optional full gate"
        Write-Host ">>> uv sync"
        uv sync
        if ($LASTEXITCODE -ne 0) { throw "uv sync failed." }
        Write-Host ">>> .\scripts\check-all.ps1"
        .\scripts\check-all.ps1
        if ($LASTEXITCODE -ne 0) { throw "check-all failed." }
    }

    Write-Step "Summary"
    $results | Format-Table Name, ExitCode, MatchCount, Passed -AutoSize
    $failed = @($results | Where-Object { -not $_.Passed })
    if ($failed.Count -gt 0) {
        Write-Host ""
        Write-Host "FINAL STATUS: NOT SAFE (one or more checks failed)" -ForegroundColor Red
        exit 1
    }

    Write-Host ""
    Write-Host "FINAL STATUS: SAFE (no unexpected username-segment probe hits)" -ForegroundColor Green
    exit 0
}
finally {
    Pop-Location
    if (-not $KeepClone -and (Test-Path -LiteralPath $clonePath)) {
        Remove-Item -LiteralPath $clonePath -Recurse -Force
        Write-Host "Removed temp clone: $clonePath" -ForegroundColor DarkGray
    } elseif ($KeepClone) {
        Write-Host "Kept temp clone: $clonePath" -ForegroundColor DarkGray
    }
}
