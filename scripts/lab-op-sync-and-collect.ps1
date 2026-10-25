#Requires -Version 5.1
<#
.SYNOPSIS
  For each LAB-OP host in a private manifest: optional fping, SSH probe, git pull on listed repo paths, run homelab-host-report.sh, save logs under docs/private/homelab/reports/.

.DESCRIPTION
  Runs from the operator dev PC (same LAN as lab). Requires SSH Host aliases in ~/.ssh/config and
  docs/private/homelab/lab-op-hosts.manifest.json (copy from docs/private.example/homelab/lab-op-hosts.manifest.example.json).
  SSH probe flattens stdout+stderr (MOTD) so success is detected reliably.

.EXAMPLE
  .\scripts\lab-op-sync-and-collect.ps1

.EXAMPLE
  .\scripts\lab-op-sync-and-collect.ps1 -ManifestPath docs\private\homelab\lab-op-hosts.manifest.json -SkipFping
#>
param(
    [string] $ManifestPath = "",
    [switch] $SkipFping,
    [switch] $SkipGitPull,
    [string] $RepoRoot = "",
    [switch] $Privileged,
    [switch] $Deep
)

$ErrorActionPreference = "Stop"
if (-not $RepoRoot) {
    $RepoRoot = (Get-Item $PSScriptRoot).Parent.FullName
}
$primaryManifest = Join-Path $RepoRoot "docs\private\homelab\lab-op-hosts.manifest.json"
$fallbackManifest = Join-Path $RepoRoot "docs\private\homelab\lab-op-hosts.manifest.example.json"
if (-not $ManifestPath) {
    if (Test-Path -LiteralPath $primaryManifest) {
        $ManifestPath = $primaryManifest
    } elseif (Test-Path -LiteralPath $fallbackManifest) {
        $ManifestPath = $fallbackManifest
        Write-Warning "Using $fallbackManifest - rename to lab-op-hosts.manifest.json when final; replace REPLACE_USER / paths."
    }
}
if (-not $ManifestPath -or -not (Test-Path -LiteralPath $ManifestPath)) {
    throw "Missing manifest: $primaryManifest - copy docs/private.example/homelab/lab-op-hosts.manifest.example.json to docs/private/homelab/, edit SSH hosts + repoPaths, save as lab-op-hosts.manifest.json."
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

$reportArgs = @()
if ($Privileged) { $reportArgs += "--privileged" }
if ($Deep) { $reportArgs += "--deep" }
$reportArgsText = ""
if ($reportArgs.Count -gt 0) {
    $reportArgsText = " " + ($reportArgs -join " ")
}

# Prevent a single host from hanging the whole run.
# Uses GNU timeout if present on the remote host; otherwise runs without a hard timeout.
$remoteReportTimeoutSecs = 600

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
    param(
        [Parameter(Mandatory = $true)]
        [string] $CmdLine
    )
    # Use cmd.exe to avoid Windows PowerShell 5.1 NativeCommandError noise on stderr.
    # Caller can read $LASTEXITCODE for the exit code.
    return (& cmd.exe /c $CmdLine | Out-String)
}

foreach ($h in $manifest.hosts) {
    $alias = $h.sshHost
    if (-not $alias) { continue }
    Write-Host "=== Host: $alias ===" -ForegroundColor Cyan

    if (-not $SkipFping -and $fping) {
        $hn = Get-SshHostname -Alias $alias
        if ($hn) {
            & fping -c 1 -t 400 $hn 2>&1 | Write-Host
            if ($LASTEXITCODE -ne 0) {
                Write-Warning "fping failed for $hn - continuing with SSH probe."
            }
        }
    }

    # Flatten stdout+stderr (MOTD on stderr) so -match works; capture exit code immediately.
    $probeCmd = "ssh.exe -o BatchMode=yes -o ConnectTimeout=12 $alias `"echo LABOP_SSH_OK`" 2>&1"
    $probeText = Invoke-CmdCapture -CmdLine $probeCmd
    $probeExit = $LASTEXITCODE
    Write-Host $probeText
    if ($probeExit -ne 0 -or $probeText -notmatch "LABOP_SSH_OK") {
        Write-Warning "SSH probe failed for $alias - skip repos for this host."
        continue
    }

    $sb = [System.Text.StringBuilder]::new()
    [void]$sb.AppendLine("=== lab-op-sync-and-collect $stamp ===")
    [void]$sb.AppendLine("sshHost: $alias")
    foreach ($rp in $h.repoPaths) {
        if (-not $rp) { continue }
        [void]$sb.AppendLine("--- repo: $rp ---")
        $rpEsc = $rp -replace "'", "'\''"
        if ($SkipGitPull) {
            $remoteCmd = "cd '$rpEsc' && (command -v timeout >/dev/null 2>&1 && timeout $remoteReportTimeoutSecs bash scripts/homelab-host-report.sh$reportArgsText || bash scripts/homelab-host-report.sh$reportArgsText) 2>&1"
        }
        else {
            $remoteCmd = "cd '$rpEsc' && git fetch origin && git pull --ff-only && (command -v timeout >/dev/null 2>&1 && timeout $remoteReportTimeoutSecs bash scripts/homelab-host-report.sh$reportArgsText || bash scripts/homelab-host-report.sh$reportArgsText) 2>&1"
        }
        # Single argument for remote command (paths with spaces: avoid or use manifest carefully).
        $remoteCmdEsc = $remoteCmd.Replace('"', '\"')
        $remoteLine = "ssh.exe -o BatchMode=yes -o ConnectTimeout=120 $alias `"$remoteCmdEsc`" 2>&1"
        $remoteOut = Invoke-CmdCapture -CmdLine $remoteLine
        [void]$sb.AppendLine($remoteOut)
    }

    $safe = ($alias -replace '[^\w\-\.]', '_')
    $outFile = Join-Path $outDir "${safe}_${stamp}_labop_sync_collect.log"
    Set-Content -LiteralPath $outFile -Value $sb.ToString() -Encoding utf8
    Write-Host "Wrote $outFile" -ForegroundColor Green
}

Write-Host "Done. Redact before sharing; compare with prior logs in the same folder." -ForegroundColor DarkGray
