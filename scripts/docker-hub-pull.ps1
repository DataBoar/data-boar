#!/usr/bin/env pwsh
# Pull Docker Hub images for local cache, A/B, and Scout workflows.
# Keeps: fabioleitao/data_boar:latest, :<current semver from pyproject.toml>, and optionally :<previous patch>.
#
# Usage (repo root):
#   .\scripts\docker-hub-pull.ps1
#   .\scripts\docker-hub-pull.ps1 -SkipPrevious
#   .\scripts\docker-hub-pull.ps1 -PreviousVersion "1.6.1"
#
# See: docs/DOCKER_SETUP.md, docs/ops/BRANCH_AND_DOCKER_CLEANUP.md, scripts/docker/README.md

param(
    [switch]$SkipPrevious = $false,
    [string]$PreviousVersion = "",
    [string]$HubImage = "fabioleitao/data_boar"
)

$ErrorActionPreference = "Stop"

$common = Join-Path $PSScriptRoot "docker\DataBoarDockerCommon.ps1"
. $common

if (-not (Test-DataBoarDockerAvailable)) {
    Write-Host "docker: command not found. Install Docker Desktop." -ForegroundColor Red
    exit 1
}

$repoRoot = Get-DataBoarRepoRoot -ScriptsDirectory $PSScriptRoot
$version = Get-DataBoarVersionFromPyproject -RepoRoot $repoRoot

$prev = $PreviousVersion
if (-not $SkipPrevious -and -not $prev) {
    $prev = Get-DataBoarPreviousPatchVersion -Version $version
}

Write-Host "=== docker-hub-pull: $HubImage ===" -ForegroundColor Cyan
Write-Host "Project version (pyproject): $version" -ForegroundColor Gray

Write-Host "Pulling ${HubImage}:latest ..." -ForegroundColor Yellow
docker pull "${HubImage}:latest"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Pulling ${HubImage}:$version ..." -ForegroundColor Yellow
docker pull "${HubImage}:$version"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if ($prev) {
    Write-Host "Pulling ${HubImage}:$prev (previous patch) ..." -ForegroundColor Yellow
    docker pull "${HubImage}:$prev"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Note: pull failed for $prev  - tag may not exist on Hub yet; safe to ignore." -ForegroundColor DarkYellow
    }
} else {
    Write-Host "Skipping previous patch (use -PreviousVersion or clear -SkipPrevious when patch > 0)." -ForegroundColor DarkGray
}

Write-Host "docker-hub-pull: done." -ForegroundColor Green
