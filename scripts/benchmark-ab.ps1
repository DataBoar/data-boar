<#
.SYNOPSIS
  Git A/B benchmark: checkout legacy tag, run lab-completao-orchestrate, capture artifacts; restore HEAD, repeat.

.DESCRIPTION
  Creates repo-local benchmark_runs/ with subfolders for each round, measures wall time with Measure-Command,
  writes benchmark_runs/times.txt, and copies completao logs (and optional SQLite / executive Markdown).

  Round A runs completao with -LabGitRef matching the legacy tag so LAB clones align to that tag.
  By default the local clone is NOT checked out to the legacy tag (orchestrator stays on your branch so
  scripts like lab-op-git-ensure-ref.ps1 stay current; Debian ssh banners on stderr otherwise break older
  script revisions under StrictMode). Pass -LocalLegacyCheckout to restore the old "checkout tag A then B"
  behaviour when you need local files to match the tag.

  Round B runs completao with -CurrentLabGitRef (default origin/main). Requires a clean working tree unless
  -AutoStash or -AllowDirty. Restores git state in a finally block when -LocalLegacyCheckout was used.

  ASCII-only for Windows PowerShell 5.1. See LAB_COMPLETAO_RUNBOOK.md for manifest and SSH.

.PARAMETER AutoStash
  If the tree is dirty, run git stash push -u before checkouts; try git stash pop in finally.

.PARAMETER AllowDirty
  Skip the clean-tree guard (risk losing uncommitted work on checkout).

.PARAMETER MoveCapturedArtifacts
  Use Move-Item instead of Copy-Item for matched report files (empties matching files from reports dir).

.NOTES
  Default report dir: docs/private/homelab/reports (gitignored). SQLite is not produced by the orchestrator;
  use -SqlitePath to copy a known audit DB after each round, or rely on audit_results.db at repo root if touched.
#>
[CmdletBinding()]
param(
    [string] $RepoRoot = "",
    [string] $BenchmarkDirName = "benchmark_runs",
    [string] $LegacyTag = "v1.7.3",
    [string] $CurrentLabGitRef = "origin/main",
    [string] $CurrentCaptureDir = "v1.7.4-rc",
    [string] $ReportsRelative = "docs\private\homelab\reports",
    [string] $SqlitePath = "",
    [string] $ReportConfigYaml = "",
    [string] $ReportSessionId = "",
    [switch] $Privileged,
    [switch] $AutoStash,
    [switch] $AllowDirty,
    [switch] $MoveCapturedArtifacts,
    [switch] $LocalLegacyCheckout,
    [switch] $WhatIf
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
    param([string] $Root)
    if (-not [string]::IsNullOrWhiteSpace($Root)) {
        return (Resolve-Path $Root).Path
    }
    # Inside a function, $MyInvocation.MyCommand is the function, not this .ps1 (no .Path).
    if (-not [string]::IsNullOrWhiteSpace($PSScriptRoot)) {
        return (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
    }
    $parent = Split-Path -Parent $PSCommandPath
    return (Resolve-Path (Join-Path $parent "..")).Path
}

function Get-GitPorcelain {
    param([string] $Repo)
    Push-Location $Repo
    try {
        return (& git status --porcelain 2>$null)
    } finally {
        Pop-Location
    }
}

function Copy-OrMove-File {
    param(
        [string] $SourcePath,
        [string] $DestDir,
        [switch] $Move
    )
    if (-not (Test-Path -LiteralPath $SourcePath)) { return }
    $name = Split-Path -Leaf $SourcePath
    $dest = Join-Path $DestDir $name
    if ($Move) {
        Move-Item -LiteralPath $SourcePath -Destination $dest -Force
    } else {
        Copy-Item -LiteralPath $SourcePath -Destination $dest -Force
    }
}

function Copy-CompletaoReportsSince {
    param(
        [string] $ReportsPath,
        [string] $DestDir,
        [datetime] $RoundStartLocal,
        [switch] $Move
    )
    if (-not (Test-Path -LiteralPath $ReportsPath)) { return }
    $buffer = $RoundStartLocal.AddSeconds(-3)
    $files = Get-ChildItem -LiteralPath $ReportsPath -File -ErrorAction SilentlyContinue
    foreach ($f in $files) {
        if ($f.LastWriteTime -lt $buffer) { continue }
        $dest = Join-Path $DestDir $f.Name
        if ($Move) {
            Move-Item -LiteralPath $f.FullName -Destination $dest -Force
        } else {
            Copy-Item -LiteralPath $f.FullName -Destination $dest -Force
        }
    }
}

function Copy-SqliteCandidatesSince {
    param(
        [string] $Repo,
        [string] $DestDir,
        [datetime] $RoundStartLocal,
        [string] $ExplicitSqlite,
        [switch] $Move
    )
    $buffer = $RoundStartLocal.AddSeconds(-3)
    if (-not [string]::IsNullOrWhiteSpace($ExplicitSqlite)) {
        $p = Resolve-Path -LiteralPath $ExplicitSqlite -ErrorAction SilentlyContinue
        if ($p) {
            Copy-OrMove-File -SourcePath $p.Path -DestDir $DestDir -Move:$Move
        }
        return
    }
    $candidates = @(
        (Join-Path $Repo "audit_results.db"),
        (Join-Path $Repo "data\lab_completao_benchmark.db")
    )
    foreach ($c in $candidates) {
        if (-not (Test-Path -LiteralPath $c)) { continue }
        $fi = Get-Item -LiteralPath $c
        if ($fi.LastWriteTime -ge $buffer) {
            Copy-OrMove-File -SourcePath $c -DestDir $DestDir -Move:$Move
        }
    }
}

$r = Resolve-RepoRoot -Root $RepoRoot
$bench = Join-Path $r $BenchmarkDirName
$dirLegacy = Join-Path $bench $LegacyTag
$dirCurrent = Join-Path $bench $CurrentCaptureDir
$timesFile = Join-Path $bench "times.txt"
$reports = Join-Path $r $ReportsRelative
$orch = Join-Path $r "scripts\lab-completao-orchestrate.ps1"
$stashCreated = $false
$savedBranch = ""
$savedHead = ""
$moveSwitch = [bool]$MoveCapturedArtifacts
$didLegacyLocalCheckout = $false
$script:benchLegacyShellMb = $null
$script:benchCurrentShellMb = $null

function Get-LocalShellWorkingSetMbMax {
    $maxMb = 0.0
    foreach ($name in @("powershell", "pwsh")) {
        Get-Process -Name $name -ErrorAction SilentlyContinue | ForEach-Object {
            $mb = [double]($_.WorkingSet64 / 1MB)
            if ($mb -gt $maxMb) { $maxMb = $mb }
        }
    }
    if ($maxMb -eq 0.0) { return $null }
    return [math]::Round($maxMb, 2)
}

if ($WhatIf) {
    Write-Host "WhatIf: benchmark_runs under $bench ; legacy $LegacyTag then restore HEAD."
    exit 0
}

if (-not (Test-Path -LiteralPath $orch)) {
    throw "missing orchestrator: $orch"
}

$dirty = Get-GitPorcelain -Repo $r
if ($dirty -and -not $AllowDirty) {
    if ($AutoStash) {
        Write-Host "[benchmark-ab] working tree dirty; git stash push -u"
        Push-Location $r
        try {
            & git stash push -u -m "benchmark-ab $(Get-Date -Format o)"
            if ($LASTEXITCODE -ne 0) { throw "git stash failed" }
            $stashCreated = $true
        } finally {
            Pop-Location
        }
    } else {
        throw "working tree is not clean. Commit, stash, or pass -AutoStash or -AllowDirty (risky)."
    }
}

Push-Location $r
try {
    $savedHead = (& git rev-parse HEAD).Trim()
    $br = & git branch --show-current 2>$null
    if ($null -eq $br) { $savedBranch = "" } else { $savedBranch = $br.Trim() }
}
finally {
    Pop-Location
}

if (Test-Path -LiteralPath $bench) {
    Remove-Item -LiteralPath $bench -Recurse -Force
}
New-Item -ItemType Directory -Path $dirLegacy -Force | Out-Null
New-Item -ItemType Directory -Path $dirCurrent -Force | Out-Null

function Invoke-CompletaoRound {
    param(
        [string] $LabGitRef,
        [switch] $TagPinInventorySkip
    )
    $argList = @("-NoProfile", "-File", $orch, "-LabGitRef", $LabGitRef)
    if ($Privileged) { $argList += "-Privileged" }
    if ($TagPinInventorySkip) { $argList += "-SkipGitPullOnInventoryRefresh" }
    $sw = Measure-Command {
        Push-Location $r
        try {
            & powershell.exe @argList
            if ($LASTEXITCODE -ne 0) {
                throw "lab-completao-orchestrate exit $LASTEXITCODE (ref=$LabGitRef)"
            }
        } finally {
            Pop-Location
        }
    }
    return $sw
}

try {
    Write-Host "[benchmark-ab] fetch tags (best effort)"
    Push-Location $r
    try {
        & git fetch origin --tags 2>$null | Out-Null
    } finally {
        Pop-Location
    }

    if ($LocalLegacyCheckout) {
        Write-Host "[benchmark-ab] Round A: git checkout $LegacyTag (local tree matches tag)"
        Push-Location $r
        try {
            & git checkout $LegacyTag
            if ($LASTEXITCODE -ne 0) { throw "git checkout $LegacyTag failed" }
            $didLegacyLocalCheckout = $true
        } finally {
            Pop-Location
        }
    } else {
        Write-Host "[benchmark-ab] Round A: lab ref $LegacyTag (local tree unchanged; orchestrator from current branch)"
    }

    $startA = Get-Date
    $tagPin = $LegacyTag -match '^v[0-9]'
    $swA = Invoke-CompletaoRound -LabGitRef $LegacyTag -TagPinInventorySkip:$tagPin
    $script:benchLegacyShellMb = Get-LocalShellWorkingSetMbMax
    Copy-CompletaoReportsSince -ReportsPath $reports -DestDir $dirLegacy -RoundStartLocal $startA -Move:$moveSwitch
    Copy-SqliteCandidatesSince -Repo $r -DestDir $dirLegacy -RoundStartLocal $startA -ExplicitSqlite $SqlitePath -Move:$moveSwitch

    if ($didLegacyLocalCheckout) {
        Write-Host "[benchmark-ab] Round B: restore branch or HEAD then run completao ($CurrentLabGitRef)"
        Push-Location $r
        try {
            if ($savedBranch) {
                & git checkout $savedBranch
            } else {
                & git checkout $savedHead
            }
            if ($LASTEXITCODE -ne 0) { throw "git checkout back to saved state failed" }
        } finally {
            Pop-Location
        }
    } else {
        Write-Host "[benchmark-ab] Round B: completao ($CurrentLabGitRef) (local tree unchanged)"
    }

    $startB = Get-Date
    $pinB = $CurrentLabGitRef -match '^v[0-9]'
    $swB = Invoke-CompletaoRound -LabGitRef $CurrentLabGitRef -TagPinInventorySkip:$pinB
    $script:benchCurrentShellMb = Get-LocalShellWorkingSetMbMax
    Copy-CompletaoReportsSince -ReportsPath $reports -DestDir $dirCurrent -RoundStartLocal $startB -Move:$moveSwitch
    Copy-SqliteCandidatesSince -Repo $r -DestDir $dirCurrent -RoundStartLocal $startB -ExplicitSqlite $SqlitePath -Move:$moveSwitch

    if (-not [string]::IsNullOrWhiteSpace($ReportConfigYaml) -and -not [string]::IsNullOrWhiteSpace($ReportSessionId)) {
        $cfgR = Resolve-Path -LiteralPath $ReportConfigYaml
        $mdOut = Join-Path $dirCurrent "executive_report_benchmark.md"
        $argsUv = @(
            "run", "python", "-m", "cli.reporter",
            "--config", $cfgR.Path,
            "--session-id", $ReportSessionId,
            "-o", $mdOut
        )
        Push-Location $r
        try {
            & uv @argsUv
            if ($LASTEXITCODE -ne 0) { Write-Warning "data-boar-report exit $LASTEXITCODE" }
        } finally {
            Pop-Location
        }
    }

    $lines = @()
    $lines += "generated_utc=$(Get-Date -Format o)"
    $lines += "legacy_tag=$LegacyTag"
    $lines += "legacy_total_seconds=$($swA.TotalSeconds)"
    $lines += "legacy_total_milliseconds=$($swA.TotalMilliseconds)"
    $lines += "current_lab_git_ref=$CurrentLabGitRef"
    $lines += "current_capture_dir=$CurrentCaptureDir"
    $lines += "current_total_seconds=$($swB.TotalSeconds)"
    $lines += "current_total_milliseconds=$($swB.TotalMilliseconds)"
    $lines += "restored_branch=$savedBranch"
    $lines += "restored_head_sha=$savedHead"
    Set-Content -LiteralPath $timesFile -Value ($lines -join "`r`n") -Encoding ascii
    Write-Host "[benchmark-ab] wrote $timesFile"

    $telemetryPath = Join-Path $bench "telemetry.json"
    $telemetry = [ordered]@{
        generated_utc = (Get-Date -Format o)
        computer_name = $env:COMPUTERNAME
        user_name       = $env:USERNAME
        legacy_tag      = $LegacyTag
        current_lab_git_ref = $CurrentLabGitRef
        current_capture_dir = $CurrentCaptureDir
        local_legacy_checkout = [bool]$LocalLegacyCheckout
        restored_branch = $savedBranch
        restored_head_sha = $savedHead
        legacy_wall_seconds = [math]::Round($swA.TotalSeconds, 3)
        current_wall_seconds = [math]::Round($swB.TotalSeconds, 3)
        delta_seconds = [math]::Round(($swB.TotalSeconds - $swA.TotalSeconds), 3)
        local_process_note = "post_each_round snapshot of powershell/pwsh WorkingSet64 on dev PC (orchestrator host), not lab CPU during remote smoke"
        legacy_post_round_local_shell_mb = $script:benchLegacyShellMb
        current_post_round_local_shell_mb = $script:benchCurrentShellMb
    }
    $telemetryJson = ($telemetry | ConvertTo-Json -Depth 6 -Compress)
    Set-Content -LiteralPath $telemetryPath -Value $telemetryJson -Encoding ascii
    Write-Host "[benchmark-ab] wrote $telemetryPath"
}
finally {
    if ($didLegacyLocalCheckout) {
        Write-Host "[benchmark-ab] restoring git checkout after legacy local checkout"
        Push-Location $r
        try {
            if ($savedBranch) {
                & git checkout $savedBranch
            } else {
                & git checkout $savedHead
            }
            if ($LASTEXITCODE -ne 0) {
                Write-Warning "git checkout restore returned non-zero; fix branch/detached state manually."
            }
        } catch {
            Write-Warning "git restore checkout may need manual fix: $_"
        } finally {
            Pop-Location
        }
    }
    if ($stashCreated) {
        Write-Host "[benchmark-ab] attempting git stash pop"
        Push-Location $r
        try {
            & git stash pop
            if ($LASTEXITCODE -ne 0) {
                Write-Warning "git stash pop failed; resolve manually (stash still exists)."
            }
        } finally {
            Pop-Location
        }
    }
}
