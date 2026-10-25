#Requires -Version 5.1
<#
.SYNOPSIS
  Check private lab inventory markdown freshness; optionally run lab-op-sync-and-collect before completao.

.DESCRIPTION
  Compares docs/private/homelab/LAB_SOFTWARE_INVENTORY.md and OPERATOR_SYSTEM_MAP.md against a max age
  (default 15 days). Dates are taken from an explicit line if present (see docs/ops/LAB_COMPLETAO_RUNBOOK.md),
  otherwise from file LastWriteTime.

  When stale and -AutoRefresh is set, runs scripts/lab-op-sync-and-collect.ps1 (homelab-host-report per host).
  Markdown matrices still require operator/assistant merge from docs/private/homelab/reports/*.log - the script
  only refreshes remote telemetry.

.PARAMETER MaxAgeDays
  Stale threshold (default 15).

.EXAMPLE
  .\scripts\lab-completao-inventory-preflight.ps1 -AutoRefresh

.EXAMPLE
  .\scripts\lab-completao-inventory-preflight.ps1 -MaxAgeDays 30
  (without -AutoRefresh: prints stale status and exits 2 if refresh is needed)
#>
param(
    [string] $RepoRoot = "",
    [string] $ManifestPath = "",
    [int] $MaxAgeDays = 15,
    [switch] $AutoRefresh,
    [switch] $SkipFping,
    [switch] $SkipGitPullOnRefresh,
    [switch] $Quiet
)

$ErrorActionPreference = "Stop"
if (-not $RepoRoot) {
    $RepoRoot = (Get-Item $PSScriptRoot).Parent.FullName
}

$inventoryFiles = @(
    (Join-Path $RepoRoot "docs\private\homelab\LAB_SOFTWARE_INVENTORY.md"),
    (Join-Path $RepoRoot "docs\private\homelab\OPERATOR_SYSTEM_MAP.md")
)

function Get-InventoryEffectiveDate {
    param([string] $FilePath)
    if (-not (Test-Path -LiteralPath $FilePath)) {
        return $null
    }
    $lines = @(Get-Content -LiteralPath $FilePath -TotalCount 120 -Encoding utf8 -ErrorAction SilentlyContinue)
    foreach ($line in $lines) {
        if ($line -match '<!--\s*lab-op-inventory-as-of:\s*(\d{4}-\d{2}-\d{2})\s*-->') {
            return [datetime]::ParseExact($Matches[1], "yyyy-MM-dd", $null)
        }
        if ($line -match '(?i)\*?\*?Lab inventory as-of:?\*?\*?\s*(\d{4}-\d{2}-\d{2})') {
            return [datetime]::ParseExact($Matches[1], "yyyy-MM-dd", $null)
        }
        if ($line -match '(?i)Inventario\s+(LAB-OP\s+)?as-of:?\s*(\d{4}-\d{2}-\d{2})') {
            return [datetime]::ParseExact($Matches[2], "yyyy-MM-dd", $null)
        }
        if ($line -match ('(?i)Invent' + [char]0x00E1 + 'rio\s+(LAB-OP\s+)?as-of:?\s*(\d{4}-\d{2}-\d{2})')) {
            return [datetime]::ParseExact($Matches[2], "yyyy-MM-dd", $null)
        }
    }
    return (Get-Item -LiteralPath $FilePath).LastWriteTime.Date
}

$now = (Get-Date).Date
$stale = @()
$missing = @()
foreach ($f in $inventoryFiles) {
    if (-not (Test-Path -LiteralPath $f)) {
        $missing += $f
        continue
    }
    $d = Get-InventoryEffectiveDate -FilePath $f
    $age = ($now - $d.Date).Days
    if ($age -gt $MaxAgeDays) {
        $stale += [pscustomobject]@{ Path = $f; AsOf = $d; AgeDays = $age }
    }
}

if ($missing.Count -gt 0 -and -not $Quiet) {
    Write-Host "lab-completao-inventory-preflight: missing inventory file(s) - treating as stale:" -ForegroundColor Yellow
    foreach ($m in $missing) { Write-Host "  $m" }
}

if ($stale.Count -gt 0 -and -not $Quiet) {
    Write-Host "lab-completao-inventory-preflight: stale vs ${MaxAgeDays}d threshold:" -ForegroundColor Yellow
    foreach ($s in $stale) {
        Write-Host ("  {0} (as-of {1:yyyy-MM-dd}, age {2}d)" -f $s.Path, $s.AsOf, $s.AgeDays)
    }
}

$needsAction = ($missing.Count -gt 0) -or ($stale.Count -gt 0)

if (-not $needsAction) {
    if (-not $Quiet) {
        Write-Host "lab-completao-inventory-preflight: LAB_SOFTWARE_INVENTORY / OPERATOR_SYSTEM_MAP are within ${MaxAgeDays}d - OK." -ForegroundColor Green
    }
    exit 0
}

if (-not $AutoRefresh) {
    Write-Host "lab-completao-inventory-preflight: run with -AutoRefresh to run lab-op-sync-and-collect.ps1, or refresh markdown manually." -ForegroundColor Yellow
    exit 2
}

$sync = Join-Path $RepoRoot "scripts\lab-op-sync-and-collect.ps1"
if (-not (Test-Path -LiteralPath $sync)) {
    throw "Missing $sync"
}

Write-Host "lab-completao-inventory-preflight: running lab-op-sync-and-collect.ps1 ..." -ForegroundColor Cyan
if ($ManifestPath) {
    & $sync -RepoRoot $RepoRoot -ManifestPath $ManifestPath -SkipFping:$SkipFping -SkipGitPull:$SkipGitPullOnRefresh
}
else {
    & $sync -RepoRoot $RepoRoot -SkipFping:$SkipFping -SkipGitPull:$SkipGitPullOnRefresh
}

Write-Host @"

lab-completao-inventory-preflight: remote host reports written under docs/private/homelab/reports/.
Next: merge findings into LAB_SOFTWARE_INVENTORY.md and OPERATOR_SYSTEM_MAP.md, then set an explicit line near the top:
  **Lab inventory as-of:** YYYY-MM-DD
  or <!-- lab-op-inventory-as-of: YYYY-MM-DD -->
See docs/ops/LAB_COMPLETAO_RUNBOOK.md (Inventory freshness).
"@ -ForegroundColor DarkGray

exit 0
