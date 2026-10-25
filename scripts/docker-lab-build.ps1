#!/usr/bin/env pwsh
# Build local lab image as data_boar:lab (mutable tag  - overwrites each run).
# Optionally preserves the previous lab digest as data_boar:lab-prev before rebuilding.
# Optionally tags data_boar:smoke for A/B (Hub vs local, or two locals).
#
# Usage (repo root):
#   .\scripts\docker-lab-build.ps1
#   .\scripts\docker-lab-build.ps1 -NoCache
#   .\scripts\docker-lab-build.ps1 -TagSmoke   # copy lab -> smoke after build (A/B slot)
#   .\scripts\docker-lab-build.ps1 -SkipLabPrev
#
# See: docs/DOCKER_SETUP.md S.7, scripts/docker/README.md

param(
    [switch]$NoCache = $false,
    [switch]$SkipLabPrev = $false,
    [switch]$TagSmoke = $false,
    [string]$Dockerfile = "Dockerfile",
    [string]$LabTag = "data_boar:lab",
    [string]$LabPrevTag = "data_boar:lab-prev",
    [string]$SmokeTag = "data_boar:smoke"
)

$ErrorActionPreference = "Stop"

$common = Join-Path $PSScriptRoot "docker\DataBoarDockerCommon.ps1"
. $common

if (-not (Test-DataBoarDockerAvailable)) {
    Write-Host "docker: command not found. Install Docker Desktop." -ForegroundColor Red
    exit 1
}

$repoRoot = Get-DataBoarRepoRoot -ScriptsDirectory $PSScriptRoot
$dockerfilePath = Join-Path $repoRoot $Dockerfile
if (-not (Test-Path -LiteralPath $dockerfilePath)) {
    Write-Host "Dockerfile not found: $dockerfilePath" -ForegroundColor Red
    exit 1
}

Write-Host "=== docker-lab-build: $LabTag ===" -ForegroundColor Cyan
Set-Location $repoRoot

if (-not $SkipLabPrev) {
    $inspect = docker images -q $LabTag 2>$null
    if ($inspect) {
        Write-Host "Tagging current $LabTag -> $LabPrevTag (rollback / comparison)" -ForegroundColor Yellow
        docker tag $LabTag $LabPrevTag
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }
}

$buildArgs = @("build", "-t", $LabTag, "-f", $Dockerfile, ".")
if ($NoCache) { $buildArgs = @("build", "--no-cache", "-t", $LabTag, "-f", $Dockerfile, ".") }

Write-Host "docker $($buildArgs -join ' ')" -ForegroundColor Gray
& docker @buildArgs
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if ($TagSmoke) {
    Write-Host "Tagging $LabTag -> $SmokeTag (A/B slot)" -ForegroundColor Yellow
    docker tag $LabTag $SmokeTag
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

$pwdPath = (Get-Location).Path
Write-Host ('docker-lab-build: done. Example: docker run --rm -p 8088:8088 -v "{0}/data:/data" -e CONFIG_PATH=/data/config.yaml {1}' -f $pwdPath, $LabTag) -ForegroundColor Green
