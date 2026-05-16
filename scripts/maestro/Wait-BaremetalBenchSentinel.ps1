#Requires -Version 7.6.1
<#
.NAME
 scripts/maestro/Wait-BaremetalBenchSentinel.ps1

.SYNOPSIS
 Poll SSH targets (baremetal lab_members) until bench host-smoke writes .baremetal_scan_complete.

.DESCRIPTION
 lab-completao-host-smoke.sh writes /tmp/databoar_bench/<track>/.baremetal_scan_complete when
 --bench-track is set. Maestro benchmark A/B uses this instead of relying only on Start-Sleep
 before -Collect. Missing inventory or no baremetal nodes: exit 0 (nothing to wait for).
#>

param(
    [ValidateSet("stable", "beta")]
    [Parameter(Mandatory = $true)]
    [string]$BenchTrack,
    [Parameter(Mandatory = $true)]
    [string]$BenchRunId,
    [int]$TimeoutSec = 900,
    [int]$PollSec = 5
)

Set-StrictMode -Version 2
$ErrorActionPreference = "Continue"

$inventoryPath = Join-Path $PSScriptRoot "../../docs/private/homelab/data/inventory.json"
if (-not (Test-Path -LiteralPath $inventoryPath)) {
    exit 0
}

$inventory = Get-Content -LiteralPath $inventoryPath -Raw | ConvertFrom-Json
$nodes = @($inventory.lab_members | Where-Object { $_.personas -contains "baremetal" })
if ($nodes.Count -eq 0) {
    exit 0
}

$path = "/tmp/databoar_bench/$BenchTrack/.baremetal_scan_complete"
$needle = "run_id=$BenchRunId"
$deadline = (Get-Date).AddSeconds($TimeoutSec)

Write-Host ("      [Bench sentinel] Waiting for {0} (run_id match on baremetal hosts)..." -f $path) -ForegroundColor DarkGray

while ((Get-Date) -lt $deadline) {
    foreach ($node in $nodes) {
        $remote = "$($node.user)@$($node.hostname)"
        $rcmd = "test -f $path && grep -Fxq '$needle' $path"
        & ssh -q -o BatchMode=yes -o ConnectTimeout=10 $remote $rcmd 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host ("      [Bench sentinel] OK on {0}" -f $node.hostname) -ForegroundColor DarkGray
            exit 0
        }
    }
    Start-Sleep -Seconds $PollSec
}

Write-Warning "      [Bench sentinel] Timeout after ${TimeoutSec}s; caller may fall back to SleepBeforeCollect."
exit 1
