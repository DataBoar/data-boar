#!/usr/bin/env pwsh
# Grype release-image gate (#1028 PR-B).
# Contract (mirror docker-scout-critical-gate.ps1):
#   - Fail only on actionable High/Critical (--only-fixed).
#   - Load repo .grype.yaml for documented VEX (audit posture; does not weaken only-fixed).
# Compatible with operator build-push-podman.sh step 4.
#
# Usage:
#   .\scripts\grype-image-gate.ps1
#   .\scripts\grype-image-gate.ps1 -Image "fabioleitao/data_boar:1.7.4"
#   .\scripts\grype-image-gate.ps1 -SaveLog "docs\ops\evidence\grype-last.txt"

param(
    [string]$Image = "fabioleitao/data_boar:latest",
    [string]$SaveLog = "",
    [string]$Config = ""
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
if (-not $Config) {
    $Config = Join-Path $repoRoot ".grype.yaml"
}

if (-not (Get-Command grype -ErrorAction SilentlyContinue)) {
    Write-Host "grype-image-gate.ps1: ABORTED: grype not on PATH." -ForegroundColor Red
    exit 2
}

Write-Host "=== grype image gate (#1028) ===" -ForegroundColor Cyan
Write-Host "Image:  $Image" -ForegroundColor Gray
Write-Host "Policy: --fail-on high --only-fixed (actionable High/Critical only)" -ForegroundColor Gray

$grypeArgs = @(
    $Image,
    "--fail-on", "high",
    "--only-fixed"
)

if (Test-Path -LiteralPath $Config) {
    Write-Host "Config: $Config" -ForegroundColor Gray
    $grypeArgs += @("--config", $Config)
}
else {
    Write-Host "Config: (none - $Config missing)" -ForegroundColor Yellow
}

if ($SaveLog) {
    $logDir = Split-Path -Parent $SaveLog
    if ($logDir -and -not (Test-Path -LiteralPath $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }
    Write-Host "Log:    $SaveLog" -ForegroundColor Gray
    & grype @grypeArgs | Tee-Object -FilePath $SaveLog
    exit $LASTEXITCODE
}

& grype @grypeArgs
exit $LASTEXITCODE
