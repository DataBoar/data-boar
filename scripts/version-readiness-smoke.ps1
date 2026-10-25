#!/usr/bin/env pwsh
<#
.SYNOPSIS
Smoke check for working vs published version readiness.

.DESCRIPTION
Compares:
- local working version (pyproject.toml)
- latest published GitHub release tag
- Docker Hub tags (best effort)
- open PRs (best effort)

Policy signal:
- If working base version is ahead of published base version and has no suffix,
  recommend using "-beta" or "-rc" until final publish choreography.
#>

param()

$ErrorActionPreference = "Stop"
$repoRoot = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $repoRoot

function Parse-Version([string]$value) {
    if ($value -notmatch '^(\d+)\.(\d+)\.(\d+)(?:-([a-z0-9]+))?$') {
        throw "Invalid version format '$value'. Expected X.Y.Z or X.Y.Z-suffix"
    }
    return [pscustomobject]@{
        Raw    = $value
        Major  = [int]$Matches[1]
        Minor  = [int]$Matches[2]
        Patch  = [int]$Matches[3]
        Suffix = if ($Matches[4]) { $Matches[4] } else { "" }
    }
}

function Compare-BaseVersion($a, $b) {
    foreach ($k in @("Major", "Minor", "Patch")) {
        if ($a.$k -gt $b.$k) { return 1 }
        if ($a.$k -lt $b.$k) { return -1 }
    }
    return 0
}

function Get-WorkingVersion {
    $line = Select-String -Path "$repoRoot\pyproject.toml" -Pattern '^version\s*=\s*"([^"]+)"' | Select-Object -First 1
    if (-not $line) { throw "Could not find version in pyproject.toml" }
    if ($line.Matches.Count -eq 0) { throw "Could not parse version line in pyproject.toml" }
    return $line.Matches[0].Groups[1].Value
}

function Get-LatestGitHubTag {
    if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { return "" }
    $tag = gh release view --json tagName -q ".tagName" 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $tag) { return "" }
    return ($tag -replace '^v', '')
}

function Get-DockerLatestSemverTag {
    try {
        $uri = "https://hub.docker.com/v2/repositories/fabioleitao/data_boar/tags?page_size=20"
        $resp = Invoke-RestMethod -Uri $uri -Method Get -TimeoutSec 20
        $tags = @($resp.results.name) | Where-Object { $_ -match '^\d+\.\d+\.\d+$' }
        if (-not $tags) { return "" }
        $parsed = $tags | ForEach-Object { Parse-Version $_ }
        $sorted = $parsed | Sort-Object Major, Minor, Patch -Descending
        return $sorted[0].Raw
    } catch {
        return ""
    }
}

$workingRaw = Get-WorkingVersion
$working = Parse-Version $workingRaw
$ghTagRaw = Get-LatestGitHubTag
$dockerTagRaw = Get-DockerLatestSemverTag

if (-not $ghTagRaw) {
    Write-Host "WARN: Could not resolve latest GitHub release tag via gh." -ForegroundColor Yellow
}

$publishedBaselineRaw = if ($ghTagRaw) { $ghTagRaw } elseif ($dockerTagRaw) { $dockerTagRaw } else { "" }
if (-not $publishedBaselineRaw) {
    Write-Host "WARN: Could not resolve published baseline from GitHub or Docker Hub." -ForegroundColor Yellow
    Write-Host "working_version=$workingRaw"
    exit 0
}

$published = Parse-Version $publishedBaselineRaw
$delta = Compare-BaseVersion $working $published
$openPrCount = 0
if (Get-Command gh -ErrorAction SilentlyContinue) {
    $openPrJson = gh pr list --state open --limit 20 --json number 2>$null
    if ($LASTEXITCODE -eq 0 -and $openPrJson) {
        try {
            $openPrCount = @($openPrJson | ConvertFrom-Json).Count
        } catch {
            $openPrCount = 0
        }
    }
}

Write-Host "working_version:        $($working.Raw)"
Write-Host "published_github_tag:   $($ghTagRaw)"
Write-Host "published_docker_tag:   $($dockerTagRaw)"
Write-Host "open_pr_count:          $openPrCount"

if ($delta -gt 0 -and [string]::IsNullOrWhiteSpace($working.Suffix)) {
    Write-Host ""
    Write-Host "FAIL: Working version is ahead of published baseline but has no pre-release suffix." -ForegroundColor Red
    Write-Host "Recommendation: set working version to '$($working.Major).$($working.Minor).$($working.Patch)-rc' (or -beta earlier)." -ForegroundColor Yellow
    exit 2
}

if ($delta -eq 0 -and -not [string]::IsNullOrWhiteSpace($working.Suffix)) {
    Write-Host ""
    Write-Host "FAIL: Published baseline already matches base version, but working version still has suffix '$($working.Suffix)'." -ForegroundColor Red
    Write-Host "Recommendation: remove suffix for final publish consistency." -ForegroundColor Yellow
    exit 3
}

Write-Host ""
Write-Host "OK: Version readiness signal is coherent with published baseline." -ForegroundColor Green
exit 0
