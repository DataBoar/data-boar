#!/usr/bin/env pwsh
# Remove extra local Data Boar image tags (not containers). Keeps a small, documented set:
#   hub: fabioleitao/data_boar:latest, :<current>, :<previous patch>
#   local: data_boar:lab, optionally data_boar:lab-prev, optionally data_boar:smoke
#
# Usage (repo root):
#   .\scripts\docker-prune-local.ps1 -WhatIf        # list only
#   .\scripts\docker-prune-local.ps1                # remove other data_boar:* / extra hub tags
#   .\scripts\docker-prune-local.ps1 -KeepSmoke:$false
#
# Does not remove containers; stop/remove them first if docker rmi fails.
# See: docs/ops/BRANCH_AND_DOCKER_CLEANUP.md S.4, scripts/docker/README.md

param(
    [switch]$WhatIf = $false,
    [switch]$KeepSmoke = $true,
    [switch]$KeepLabPrev = $true,
    [string]$HubImage = "fabioleitao/data_boar",
    [string]$LocalRepo = "data_boar",
    [string]$PreviousVersion = ""
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
if (-not $prev) {
    $prev = Get-DataBoarPreviousPatchVersion -Version $version
}

$keep = [System.Collections.ArrayList]@()
[void]$keep.Add("${HubImage}:latest".ToLowerInvariant())
[void]$keep.Add("${HubImage}:$version".ToLowerInvariant())
if ($prev) {
    [void]$keep.Add("${HubImage}:$prev".ToLowerInvariant())
}

[void]$keep.Add("${LocalRepo}:lab".ToLowerInvariant())
if ($KeepLabPrev) {
    [void]$keep.Add("${LocalRepo}:lab-prev".ToLowerInvariant())
}
if ($KeepSmoke) {
    [void]$keep.Add("${LocalRepo}:smoke".ToLowerInvariant())
}

Write-Host "=== docker-prune-local ===" -ForegroundColor Cyan
Write-Host "Project version: $version | Keep set (hub+local):" -ForegroundColor Gray
$keep | Sort-Object -Unique | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }

function Get-ImageRefs {
    param([string]$RepoName)
    $out = docker images $RepoName --format "{{.Repository}}:{{.Tag}}" 2>$null
    if (-not $out) { return @() }
    return ($out | Where-Object { $_ -and ($_ -notmatch ':<none>') })
}

$allRefs = @()
$allRefs += Get-ImageRefs -RepoName $HubImage
$allRefs += Get-ImageRefs -RepoName $LocalRepo

$toRemove = foreach ($ref in $allRefs) {
    $r = $ref.ToLowerInvariant()
    if ($keep -notcontains $r) { $ref }
}

if (-not $toRemove) {
    Write-Host "Nothing to remove (all tags match keep set or no extra tags)." -ForegroundColor Green
    exit 0
}

Write-Host "`nCandidates to remove:" -ForegroundColor Yellow
$toRemove | ForEach-Object { Write-Host "  $_" }

if ($WhatIf) {
    Write-Host "`n-WhatIf: no images removed." -ForegroundColor Cyan
    exit 0
}

$failed = 0
foreach ($ref in $toRemove) {
    Write-Host "Removing $ref ..." -ForegroundColor Yellow
    docker rmi $ref 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  (failed  - may be in use by a container; docker stop/rm first)" -ForegroundColor DarkYellow
        $failed++
    }
}

if ($failed -eq 0) {
    Write-Host "docker image prune: reclaiming dangling layers ..." -ForegroundColor Gray
    docker image prune -f
}

Write-Host "docker-prune-local: done." -ForegroundColor Green
