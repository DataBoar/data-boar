#!/usr/bin/env pwsh
# Evaluate Docker Scout CRITICAL CVEs with low-noise gating.
# - Passes when there are no CRITICAL findings.
# - Passes (with warning) when CRITICAL findings exist but all are "not fixed" upstream.
# - Fails when at least one CRITICAL has a fixed version available.
#
# Usage:
#   .\scripts\docker-scout-critical-gate.ps1
#   .\scripts\docker-scout-critical-gate.ps1 -Image "fabioleitao/data_boar:1.6.7"
#   .\scripts\docker-scout-critical-gate.ps1 -FailOnAnyCritical

param(
    [string]$Image = "fabioleitao/data_boar:latest",
    [switch]$FailOnAnyCritical = $false
)

$ErrorActionPreference = "Stop"

Write-Host "=== Docker Scout CRITICAL gate ===" -ForegroundColor Cyan
Write-Host "Image: $Image" -ForegroundColor Gray

$output = (& docker scout cves $Image --only-severity critical 2>&1 | Out-String)
$exitCode = $LASTEXITCODE

if ($exitCode -ne 0) {
    Write-Host "docker-scout-critical-gate: FAILED to query Scout output." -ForegroundColor Red
    Write-Host $output
    exit $exitCode
}

$lines = $output -split "`r?`n"
$criticalFindings = @()

for ($i = 0; $i -lt $lines.Length; $i++) {
    $line = $lines[$i]
    if ($line -match "^\s*x CRITICAL (CVE-\d{4}-\d+)") {
        $cve = $Matches[1]
        $fixedVersion = ""

        for ($j = $i + 1; $j -lt [Math]::Min($i + 12, $lines.Length); $j++) {
            if ($lines[$j] -match "^\s*Fixed version\s*:\s*(.+)\s*$") {
                $fixedVersion = $Matches[1].Trim()
                break
            }
        }

        $criticalFindings += [PSCustomObject]@{
            CVE          = $cve
            FixedVersion = $fixedVersion
        }
    }
}

if ($criticalFindings.Count -eq 0) {
    Write-Host "No CRITICAL CVEs found." -ForegroundColor Green
    exit 0
}

$actionable = @(
    $criticalFindings | Where-Object {
        $_.FixedVersion -and $_.FixedVersion.ToLowerInvariant() -ne "not fixed"
    }
)

$notFixed = @(
    $criticalFindings | Where-Object {
        -not $_.FixedVersion -or $_.FixedVersion.ToLowerInvariant() -eq "not fixed"
    }
)

Write-Host ("Critical findings: {0} (actionable: {1}, not-fixed: {2})" -f $criticalFindings.Count, $actionable.Count, $notFixed.Count) -ForegroundColor Yellow

if ($criticalFindings.Count -gt 0) {
    $criticalFindings | Format-Table -AutoSize | Out-String | Write-Host
}

if ($FailOnAnyCritical -and $criticalFindings.Count -gt 0) {
    Write-Host "FailOnAnyCritical=true -> failing on any CRITICAL finding." -ForegroundColor Red
    exit 2
}

if ($actionable.Count -gt 0) {
    Write-Host "Actionable CRITICAL CVEs found (fixed version available)." -ForegroundColor Red
    exit 2
}

Write-Host "Only 'not fixed' CRITICAL CVEs detected upstream. Keep monitoring and rebuild cadence." -ForegroundColor Yellow
exit 0
