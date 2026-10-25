#Requires -Version 5.1
<#
.SYNOPSIS
  Run scripts/homelab-host-report.sh on a remote Linux host via SSH and save stdout to docs/private/homelab/reports/.

.DESCRIPTION
  The AI assistant cannot reach your LAN; you run this from the Cursor terminal on your dev PC (same machine as the repo).
  Requires: OpenSSH client (ssh), a working SSH Host entry (see docs/private.example/homelab/README.md).

.EXAMPLE
  .\scripts\collect-homelab-report-remote.ps1 -SshHost lab-op

.EXAMPLE
  .\scripts\collect-homelab-report-remote.ps1 -SshHost <lab-host-2> -ExtraSshArgs @("-o","BatchMode=yes")
#>
param(
    [Parameter(Mandatory = $true)]
    [string] $SshHost,
    [string] $RepoRoot = "",
    [string] $OutDir = "",
    [string[]] $ExtraSshArgs = @()
)

$ErrorActionPreference = "Stop"
if (-not $RepoRoot) {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}
$scriptPath = Join-Path $RepoRoot "scripts\homelab-host-report.sh"
if (-not (Test-Path -LiteralPath $scriptPath)) {
    throw "Missing $scriptPath"
}
if (-not $OutDir) {
    $OutDir = Join-Path $RepoRoot "docs\private\homelab\reports"
}
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$stamp = Get-Date -Format "yyyyMMdd_HHmm"
$safeHost = ($SshHost -replace '[^\w\-\.]', '_')
$outFile = Join-Path $OutDir "${safeHost}_${stamp}_homelab_host_report.log"

$argList = [System.Collections.ArrayList]@()
foreach ($a in $ExtraSshArgs) { [void]$argList.Add($a) }
[void]$argList.Add($SshHost)
[void]$argList.Add("bash")
[void]$argList.Add("-s")
# Keep room for optional script args in the future.
[void]$argList.Add("--")

$errFile = Join-Path $env:TEMP "homelab-ssh-stderr-$stamp.txt"
Remove-Item -LiteralPath $errFile -ErrorAction SilentlyContinue
$p = Start-Process -FilePath "ssh" `
    -ArgumentList ($argList.ToArray()) `
    -RedirectStandardInput $scriptPath `
    -RedirectStandardOutput $outFile `
    -RedirectStandardError $errFile `
    -Wait -NoNewWindow -PassThru

if ($p.ExitCode -ne 0) {
    if (Test-Path -LiteralPath $errFile) {
        Write-Warning (Get-Content -LiteralPath $errFile -Raw -ErrorAction SilentlyContinue)
    }
    throw "ssh exited with $($p.ExitCode) (check host, keys, and PATH to ssh)"
}
Remove-Item -LiteralPath $errFile -ErrorAction SilentlyContinue
Write-Host "Wrote $outFile"
