#Requires -Version 5.1
<#
.SYNOPSIS
  For each host in docs/private/homelab/lab-op-hosts.manifest.json: SSH and git fetch + reset --hard origin/main
  on each repoPaths entry (LAB-OP clones aligned with GitHub main).

.DESCRIPTION
  Destructive: discards local commits and dirty state on the lab clone. Operator-only; requires SSH keys.
  See docs/ops/LAB_COMPLETAO_RUNBOOK.md.

.EXAMPLE
  .\scripts\lab-op-git-align-main.ps1
#>
param(
    [string] $ManifestPath = ""
)

$ErrorActionPreference = "Stop"
# SSH target: use DATA_BOAR_LAB_SSH_USER (e.g. "you") if your ~/.ssh/config does not set User per Host; otherwise omit and pass host alias only.
$LabSshUser = [string]$env:DATA_BOAR_LAB_SSH_USER
if ([string]::IsNullOrWhiteSpace($LabSshUser)) { $LabSshUser = "" } else { $LabSshUser = $LabSshUser.Trim() }
$RepoRoot = (Get-Item $PSScriptRoot).Parent.FullName
if (-not $ManifestPath) {
    $ManifestPath = Join-Path $RepoRoot "docs\private\homelab\lab-op-hosts.manifest.json"
}
if (-not (Test-Path -LiteralPath $ManifestPath)) {
    throw "Missing manifest: $ManifestPath"
}

$manifest = Get-Content -LiteralPath $ManifestPath -Raw -Encoding utf8 | ConvertFrom-Json
foreach ($h in $manifest.hosts) {
    $alias = $h.sshHost
    if (-not $alias) { continue }
    Write-Host "=== $alias ===" -ForegroundColor Cyan
    foreach ($rp in $h.repoPaths) {
        $remotePath = ($rp -replace "\\", "/").Trim()
        $remoteCmd = "cd $remotePath && git fetch origin && git reset --hard origin/main && git rev-parse --short HEAD"
        $sshTarget = if ($LabSshUser) { "${LabSshUser}@${alias}" } else { $alias }
        & ssh -o BatchMode=yes -o ConnectTimeout=30 $sshTarget $remoteCmd
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "git align failed on $alias $remotePath (exit $LASTEXITCODE)"
        }
    }
}
Write-Host "Done." -ForegroundColor Green
