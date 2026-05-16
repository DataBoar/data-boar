#Requires -Version 5.1
<#
.SYNOPSIS
  For each LAB-OP host: verify or reset each repoPaths clone to a specific git ref (tag, origin/main, branch tip, or SHA).

.DESCRIPTION
  Use -Mode Check to fail fast when lab clones are not at the resolved commit (reproducible completao).
  Use -Mode Reset to align clones destructively (discard local commits / move HEAD) - same risk class as lab-op-git-align-main.ps1.

  Ref resolution after git fetch:
  - "main" or "origin/main" -> origin/main tip
  - Otherwise: tag or full SHA via rev-parse, else remote branch origin/<name>

  Remote bash runs "git fetch origin --prune" first (required), then "git fetch origin --tags --prune"
  as best-effort (|| true). Divergent local tags can make tag fetch exit non-zero; that must not
  abort the chain before HEAD vs resolved ref - otherwise logs show SSH exit != 0 with no LABOP_REF_* line.

  When pinning to a release tag, run lab-completao-orchestrate.ps1 with -SkipGitPullOnInventoryRefresh so
  lab-op-sync-and-collect does not git pull to main before this step - see LAB_COMPLETAO_RUNBOOK.md.

.EXAMPLE
  .\scripts\lab-op-git-ensure-ref.ps1 -Ref origin/main -Mode Check

.EXAMPLE
  .\scripts\lab-op-git-ensure-ref.ps1 -Ref v1.2.0 -Mode Reset
#>
param(
    [Parameter(Mandatory = $true)]
    [string] $Ref,
    [ValidateSet("Check", "Reset")]
    [string] $Mode = "Check",
    [string] $ManifestPath = "",
    [string] $RepoRoot = "",
    [switch] $SkipFping
)

$ErrorActionPreference = "Stop"
# PowerShell 7+: native stderr from ssh (e.g. git fetch progress) becomes ErrorRecord and can break
# StrictMode + Stop. Lab scripts need exit codes, not stderr-as-terminating-error.
if ($PSVersionTable.PSVersion.Major -ge 7) {
    $PSNativeCommandUseErrorActionPreference = $false
}
if (-not $RepoRoot) {
    $RepoRoot = (Get-Item $PSScriptRoot).Parent.FullName
}
$primaryManifest = Join-Path $RepoRoot "docs\private\homelab\lab-op-hosts.manifest.json"
if (-not $ManifestPath) {
    $ManifestPath = $primaryManifest
}
if (-not (Test-Path -LiteralPath $ManifestPath)) {
    throw "Missing manifest: $ManifestPath - copy docs/private.example/homelab/lab-op-hosts.manifest.example.json and edit."
}

$manifest = Get-Content -LiteralPath $ManifestPath -Raw -Encoding utf8 | ConvertFrom-Json
$outDir = Join-Path $RepoRoot "docs\private\homelab\reports"
if ($manifest.outDir) {
    $outDir = $manifest.outDir -replace "/", [IO.Path]::DirectorySeparatorChar
    if (-not [IO.Path]::IsPathRooted($outDir)) {
        $outDir = Join-Path $RepoRoot $outDir
    }
}
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$fping = Get-Command fping -ErrorAction SilentlyContinue

function Get-SshHostname {
    param([string]$Alias)
    $g = & ssh -G $Alias 2>$null
    if ($LASTEXITCODE -ne 0) { return $null }
    foreach ($line in $g) {
        if ($line -match '^hostname (.+)$') {
            return $Matches[1].Trim()
        }
    }
    return $null
}

function Invoke-CmdCapture {
    param([Parameter(Mandatory = $true)][string]$CmdLine)
    return (& cmd.exe /c $CmdLine | Out-String)
}

function Escape-BashSingleQuoted {
    param([string]$S)
    return ($S -replace "'", "'\''")
}

function Build-RemoteCheckCmd {
    param([string]$RpEsc, [string]$RefEsc)
    $s = 'cd '''
    $s += $RpEsc
    $s += ''' && git fetch origin --prune && (git fetch origin --tags --prune || true) && R='''
    $s += $RefEsc
    $s += ''' && if [ "$R" = "main" ] || [ "$R" = "origin/main" ]; then W=$(git rev-parse "origin/main^{commit}"); elif W=$(git rev-parse "$R^{commit}" 2>/dev/null); then :; elif W=$(git rev-parse "origin/$R^{commit}" 2>/dev/null); then :; else echo "LABOP_REF_UNRESOLVED: $R"; exit 2; fi && G=$(git rev-parse HEAD) && if [ "$W" != "$G" ]; then echo "LABOP_REF_MISMATCH want=$W got=$G"; exit 1; else echo "LABOP_REF_OK $(git rev-parse --short HEAD)"; fi'
    return $s
}

function Build-RemoteResetCmd {
    param([string]$RpEsc, [string]$RefEsc)
    $s = 'cd '''
    $s += $RpEsc
    $s += ''' && git fetch origin --prune && (git fetch origin --tags --prune || true) && R='''
    $s += $RefEsc
    $s += ''' && if [ "$R" = "main" ] || [ "$R" = "origin/main" ]; then git reset --hard origin/main; elif git show-ref --verify --quiet "refs/tags/$R" 2>/dev/null; then git checkout -f --detach "$R"; elif git rev-parse -q --verify "$R^{commit}" >/dev/null 2>&1; then git checkout -f --detach "$R"; else git reset --hard "origin/$R"; fi && git rev-parse --short HEAD'
    return $s
}

function Invoke-SshRemoteCapture {
    param(
        [Parameter(Mandatory = $true)][string]$Alias,
        [Parameter(Mandatory = $true)][string]$RemoteCmd,
        [int]$ConnectTimeout = 180
    )
    $gid = [Guid]::NewGuid().ToString("n")
    $stdoutPath = Join-Path ([IO.Path]::GetTempPath()) ("labop_ssh_out_" + $gid + ".txt")
    $stderrPath = Join-Path ([IO.Path]::GetTempPath()) ("labop_ssh_err_" + $gid + ".txt")
    try {
        $null = New-Item -ItemType File -Path $stdoutPath -Force
        $null = New-Item -ItemType File -Path $stderrPath -Force
        $p = Start-Process -FilePath "ssh.exe" -ArgumentList @(
            "-q",
            "-o", "BatchMode=yes",
            "-o", ("ConnectTimeout={0}" -f $ConnectTimeout),
            $Alias,
            $RemoteCmd
        ) -Wait -PassThru -NoNewWindow -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath
        $exitCode = $p.ExitCode
        $outText = ""
        if (Test-Path -LiteralPath $stdoutPath) {
            $outText = [IO.File]::ReadAllText($stdoutPath)
        }
        return [pscustomobject]@{ ExitCode = $exitCode; StdOut = $outText }
    } finally {
        Remove-Item -LiteralPath $stdoutPath -Force -ErrorAction SilentlyContinue
        Remove-Item -LiteralPath $stderrPath -Force -ErrorAction SilentlyContinue
    }
}

$master = [System.Text.StringBuilder]::new()
[void]$master.AppendLine("=== lab-op-git-ensure-ref $stamp ===")
[void]$master.AppendLine("Mode: $Mode  Ref: $Ref")
[void]$master.AppendLine("repo: $RepoRoot")

$anyFailure = $false

foreach ($h in $manifest.hosts) {
    $alias = $h.sshHost
    if (-not $alias) { continue }
    Write-Host "=== Host: $alias ===" -ForegroundColor Cyan
    [void]$master.AppendLine("")
    [void]$master.AppendLine("### $alias ###")

    if (-not $SkipFping -and $fping) {
        $hn = Get-SshHostname -Alias $alias
        if ($hn) {
            $fp = & fping -c 1 -t 400 $hn 2>&1 | Out-String
            Write-Host $fp
            [void]$master.AppendLine($fp)
        }
    }

    $probeCmd = "ssh.exe -q -o BatchMode=yes -o ConnectTimeout=12 $alias `"echo LABOP_SSH_OK`" 2>&1"
    $probeText = Invoke-CmdCapture -CmdLine $probeCmd
    if ($LASTEXITCODE -ne 0 -or $probeText -notmatch "LABOP_SSH_OK") {
        Write-Warning "SSH probe failed for $alias - skip."
        [void]$master.AppendLine("SSH probe FAILED")
        $anyFailure = $true
        continue
    }

    $refEsc = Escape-BashSingleQuoted -S $Ref
    foreach ($rp in $h.repoPaths) {
        if (-not $rp) { continue }
        $rpEsc = Escape-BashSingleQuoted -S $rp
        $remoteCmd = if ($Mode -eq "Reset") {
            Build-RemoteResetCmd -RpEsc $rpEsc -RefEsc $refEsc
        } else {
            Build-RemoteCheckCmd -RpEsc $rpEsc -RefEsc $refEsc
        }
        # Do not route the remote bash through cmd.exe /c: cmd treats ^ as escape, which breaks
        # git's "ref^{commit}" syntax (becomes "ref{commit}" and rev-parse fails).
        # Use Start-Process so git fetch progress on stderr never becomes a PowerShell ErrorRecord (Stop mode).
        $sshResult = Invoke-SshRemoteCapture -Alias $alias -RemoteCmd $remoteCmd -ConnectTimeout 180
        $exitCode = $sshResult.ExitCode
        $remoteOut = $sshResult.StdOut
        Write-Host "--- repo: $rp ---"
        Write-Host $remoteOut
        [void]$master.AppendLine("--- repo: $rp ---")
        [void]$master.AppendLine($remoteOut)
        if ($exitCode -ne 0) {
            $anyFailure = $true
        }
    }
}

$allFile = Join-Path $outDir "lab_op_git_ensure_ref_${stamp}.log"
Set-Content -LiteralPath $allFile -Value $master.ToString() -Encoding utf8
Write-Host "Wrote $allFile" -ForegroundColor Green
if ($anyFailure) {
    Write-Host "lab-op-git-ensure-ref: one or more hosts failed ($Mode). See log." -ForegroundColor Red
    exit 1
}
Write-Host "Done ($Mode OK)." -ForegroundColor Green
