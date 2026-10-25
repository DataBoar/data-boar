#Requires -Version 5.1
<#
.SYNOPSIS
  For each LAB-OP host in docs/private/homelab/lab-op-hosts.manifest.json: SSH, git fetch, print short status.

.DESCRIPTION
  Read-only by default (no merge). Use -PullFfOnly to run git pull --ff-only on each repo path after fetch.
  Safe first step before lab-completao-orchestrate.ps1 when clones are "ahead/behind" origin/main.

.EXAMPLE
  .\scripts\lab-op-repo-status.ps1

.EXAMPLE
  .\scripts\lab-op-repo-status.ps1 -PullFfOnly
#>
param(
    [string] $ManifestPath = "",
    [string] $RepoRoot = "",
    [switch] $PullFfOnly,
    [switch] $SkipFping
)

$ErrorActionPreference = "Stop"
if (-not $RepoRoot) {
    $RepoRoot = (Get-Item $PSScriptRoot).Parent.FullName
}
$primaryManifest = Join-Path $RepoRoot "docs\private\homelab\lab-op-hosts.manifest.json"
if (-not $ManifestPath) {
    $ManifestPath = $primaryManifest
}
if (-not (Test-Path -LiteralPath $ManifestPath)) {
    throw "Missing manifest: $primaryManifest - copy docs/private.example/homelab/lab-op-hosts.manifest.example.json and edit."
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

$master = [System.Text.StringBuilder]::new()
[void]$master.AppendLine("=== lab-op-repo-status $stamp ===")
[void]$master.AppendLine("PullFfOnly: $PullFfOnly")
[void]$master.AppendLine("repo: $RepoRoot")

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

    $probeCmd = "ssh.exe -o BatchMode=yes -o ConnectTimeout=12 $alias `"echo LABOP_SSH_OK`" 2>&1"
    $probeText = Invoke-CmdCapture -CmdLine $probeCmd
    if ($LASTEXITCODE -ne 0 -or $probeText -notmatch "LABOP_SSH_OK") {
        Write-Warning "SSH probe failed for $alias - skip."
        [void]$master.AppendLine("SSH probe FAILED")
        continue
    }

    foreach ($rp in $h.repoPaths) {
        if (-not $rp) { continue }
        $rpEsc = $rp -replace "'", "'\''"
        if ($PullFfOnly) {
            $remoteCmd = "cd '$rpEsc' && git fetch origin && git pull --ff-only && git status -sb && git rev-parse --short HEAD 2>&1"
        }
        else {
            $remoteCmd = "cd '$rpEsc' && git fetch origin && git status -sb && git rev-parse --short HEAD 2>&1"
        }
        $remoteCmdEsc = $remoteCmd.Replace('"', '\"')
        $remoteLine = "ssh.exe -o BatchMode=yes -o ConnectTimeout=120 $alias `"$remoteCmdEsc`" 2>&1"
        $remoteOut = Invoke-CmdCapture -CmdLine $remoteLine
        Write-Host "--- repo: $rp ---"
        Write-Host $remoteOut
        [void]$master.AppendLine("--- repo: $rp ---")
        [void]$master.AppendLine($remoteOut)
    }
}

$allFile = Join-Path $outDir "lab_op_repo_status_${stamp}.log"
Set-Content -LiteralPath $allFile -Value $master.ToString() -Encoding utf8
Write-Host "Wrote $allFile" -ForegroundColor Green
Write-Host "If ff-only fails, reconcile on the host (merge/rebase/reset) - see LAB_COMPLETAO_RUNBOOK.md." -ForegroundColor DarkGray
