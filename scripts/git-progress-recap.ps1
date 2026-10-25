#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Print a token-aware, date-grouped recap of recent commits on origin/main (pace check).

.DESCRIPTION
    Groups one-line subjects by commit date so operators can see busy vs quiet days and
    high-level themes (Conventional Commit prefixes). Default window: last 3 calendar days.
    Uses origin/main when available after a best-effort fetch; falls back to main.

    Pair with today-mode / carryover-sweep / eod-sync  - does not replace PLANS_TODO.md.

.PARAMETER Days
    How many calendar days back from today (local midnight) to include. Default 3.

.PARAMETER MaxPerDay
    Cap subjects printed per calendar day (oldest commits dropped first within that day).
    Default 40. Use -1 for no cap.

.PARAMETER NoFetch
    Skip `git fetch origin` (offline or you already fetched).

.EXAMPLE
    .\scripts\git-progress-recap.ps1

.EXAMPLE
    .\scripts\git-progress-recap.ps1 -Days 7

.EXAMPLE
    .\scripts\git-progress-recap.ps1 -Days 14 -MaxPerDay 25 -NoFetch
#>
param(
    [int]$Days = 3,
    [int]$MaxPerDay = 40,
    [switch]$NoFetch
)

$ErrorActionPreference = "Stop"
$repoRoot = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $repoRoot

if (-not $NoFetch) {
    try {
        git fetch origin 2>$null | Out-Null
    } catch {
        # best-effort
    }
}

$ref = "main"
if (git rev-parse --verify "origin/main" 2>$null) {
    $ref = "origin/main"
}

$since = (Get-Date).Date.AddDays(-[math]::Max(1, $Days))
$sinceStr = $since.ToString("yyyy-MM-dd") + " 00:00"

Write-Host "=== Git progress recap ($ref since $sinceStr, local dates) ===" -ForegroundColor Cyan
Write-Host "Tip: widen with -Days 7 or -Days 14; cap noise with -MaxPerDay 20" -ForegroundColor DarkGray
Write-Host ""

$raw = git -c log.date=iso log $ref "--since=$sinceStr" --pretty=format:"%ad`t%h`t%s" 2>$null
if (-not $raw) {
    Write-Host "No commits in range (or not a git repo)." -ForegroundColor Yellow
    exit 0
}

$lines = @($raw -split "`n" | Where-Object { $_.Trim() -ne "" })
$byDay = [ordered]@{}
foreach ($line in $lines) {
    $parts = $line -split "`t", 3
    if ($parts.Count -lt 3) { continue }
    $dt = [datetime]::Parse($parts[0])
    $dayKey = $dt.ToString("yyyy-MM-dd")
    if (-not $byDay.Contains($dayKey)) {
        $byDay[$dayKey] = New-Object System.Collections.Generic.List[string]
    }
    $byDay[$dayKey].Add("  $($parts[1])  $($parts[2])")
}

foreach ($day in $byDay.Keys) {
    $items = $byDay[$day]
    Write-Host "$day  ($($items.Count) commits)" -ForegroundColor Green
    $show = $items
    if ($MaxPerDay -ge 0 -and $items.Count -gt $MaxPerDay) {
        $show = $items | Select-Object -First $MaxPerDay
        Write-Host "  (showing first $MaxPerDay of $($items.Count); increase -MaxPerDay or narrow -Days)" -ForegroundColor DarkGray
    }
    $show | ForEach-Object { Write-Host $_ }
    Write-Host ""
}
