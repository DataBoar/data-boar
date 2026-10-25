#!/usr/bin/env pwsh
# Ensure GitHub CLI has a default repository set for this workspace.
# Usage: .\scripts\gh-ensure-default.ps1

param(
    [switch]$Quiet
)

$ErrorActionPreference = "Stop"
$repoRoot = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $repoRoot

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host "GitHub CLI ('gh') not found in PATH." -ForegroundColor Yellow
    exit 0
}

$currentDefault = & gh repo view --json nameWithOwner -q ".nameWithOwner" 2>$null
if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($currentDefault)) {
    if (-not $Quiet) {
        Write-Host "gh default repository already configured: $currentDefault"
    }
    exit 0
}

$remoteUrl = git remote get-url origin 2>$null
if (-not $remoteUrl) {
    Write-Host "Could not read 'origin' URL. Set default manually: gh repo set-default <owner>/<repo>" -ForegroundColor Yellow
    exit 1
}

if ($remoteUrl -notmatch 'github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$') {
    Write-Host "Origin is not a GitHub remote. Set default manually: gh repo set-default <owner>/<repo>" -ForegroundColor Yellow
    exit 1
}

$owner = $Matches[1]
$repo = ($Matches[2] -replace '\.git$', '')
$repoSlug = "$owner/$repo"
if (-not $Quiet) {
    Write-Host "Configuring gh default repository from origin: $repoSlug"
}
& gh repo set-default $repoSlug
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to configure gh default repository '$repoSlug'." -ForegroundColor Red
    exit $LASTEXITCODE
}

$verifiedDefault = & gh repo view --json nameWithOwner -q ".nameWithOwner" 2>$null
if ($LASTEXITCODE -eq 0 -and $verifiedDefault -eq $repoSlug) {
    if (-not $Quiet) {
        Write-Host "gh default repository set to: $verifiedDefault"
    }
    exit 0
}

Write-Host "gh default repository was set, but verification failed. You can run: gh repo set-default $repoSlug" -ForegroundColor Yellow
exit 1
