#Requires -Version 7.0
<#
.NAME
 scripts/maestro-benchmark-run.ps1

.SYNOPSIS
 Launcher for long-running Maestro A/B benchmark outside Cursor's shell timeout.

.DESCRIPTION
 The full A/B benchmark (maestro-benchmark-ab.ps1) takes 15-25 minutes across
 two rounds + SleepBeforeCollect waits. Cursor's integrated terminal kills
 background jobs after ~10 minutes. This wrapper:

   1. Prints copy-paste commands for running in a REAL terminal (PowerShell
      window, Windows Terminal, or tmux on the dev PC).
   2. Optionally launches a new PowerShell window via Start-Process (Windows).
   3. Writes all output to docs/private/homelab/reports/ regardless of terminal.

 MANUAL RUN (copy-paste into any PS terminal, run from repo root):
 -----------------------------------------------------------------------
   cd "C:\Users\fabio\Documents\dev\data-boar"
   .\scripts\maestro-benchmark-ab.ps1 `
     -LegacyRef "v1.7.3" -LegacyTrack stable -LegacyWebPort 18088 `
     -CandidateRef "WorkingTree" -CandidateTrack beta -CandidateWebPort 28088 `
     -BenchCompare -RunId "ab_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
 -----------------------------------------------------------------------

 The report lands at:
   docs/private/homelab/reports/MAESTRO_BENCHMARK_AB_<RunId>.md

.PARAMETER RunId
 Optional run identifier (default: timestamp).

.PARAMETER LaunchWindow
 If set, opens a NEW PowerShell window and runs the benchmark there.
 Default: print instructions only (safe, no side effects).

.PARAMETER SleepBeforeCollect
 Seconds to wait between Deep dispatch and Collect phase (default: 120).

.EXAMPLE
 # Print manual instructions:
 .\scripts\maestro-benchmark-run.ps1

 # Launch in a new PS window (Windows only):
 .\scripts\maestro-benchmark-run.ps1 -LaunchWindow

 # Custom run id + longer sleep:
 .\scripts\maestro-benchmark-run.ps1 -RunId "ab_post_pyo3_fix" -SleepBeforeCollect 180 -LaunchWindow
#>
[CmdletBinding()]
param(
    [string]$RunId = "",
    [switch]$LaunchWindow,
    [int]$SleepBeforeCollect = 120
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Continue'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if ([string]::IsNullOrWhiteSpace($RunId)) {
    $RunId = Get-Date -Format "yyyyMMdd_HHmmss"
}

$benchScript = Join-Path $RepoRoot "scripts\maestro-benchmark-ab.ps1"
$reportsDir  = Join-Path $RepoRoot "docs\private\homelab\reports"

$args = @(
    "-LegacyRef", '"v1.7.3"',
    "-LegacyTrack", "stable",
    "-LegacyWebPort", "18088",
    "-CandidateRef", '"WorkingTree"',
    "-CandidateTrack", "beta",
    "-CandidateWebPort", "28088",
    "-BenchCompare",
    "-RunId", "`"$RunId`"",
    "-SleepBeforeCollect", $SleepBeforeCollect
)
$argLine = $args -join " "
$fullCmd  = ".\scripts\maestro-benchmark-ab.ps1 $argLine"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Maestro A/B Benchmark Launcher" -ForegroundColor Cyan
Write-Host "  Run ID: $RunId" -ForegroundColor Cyan
Write-Host "  Estimated duration: ~20-25 min (2 rounds + ${SleepBeforeCollect}s sleep each)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "MANUAL RUN (copy-paste into PowerShell terminal from repo root):" -ForegroundColor Yellow
Write-Host ""
Write-Host "  cd `"$RepoRoot`"" -ForegroundColor White
Write-Host "  $fullCmd" -ForegroundColor White
Write-Host ""
Write-Host "Output report will be at:" -ForegroundColor Green
Write-Host "  $reportsDir\MAESTRO_BENCHMARK_AB_$RunId.md" -ForegroundColor Green
Write-Host ""

if (-not $LaunchWindow) {
    Write-Host "Tip: run with -LaunchWindow to open a new PS window automatically." -ForegroundColor DarkGray
    Write-Host "     Or paste the commands above into Windows Terminal / tmux on dev PC." -ForegroundColor DarkGray
    return
}

# ---------------------------------------------------------------------------
# Launch in a new PowerShell window (Windows only)
# ---------------------------------------------------------------------------
Write-Host "Launching new PowerShell window..." -ForegroundColor Cyan

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logFile   = Join-Path $reportsDir "benchmark_console_${timestamp}.log"

$scriptBlock = @"
Set-Location '$RepoRoot'
`$ErrorActionPreference = 'Continue'
Write-Host 'Maestro A/B Benchmark starting...' -ForegroundColor Cyan
& '$benchScript' -LegacyRef 'v1.7.3' -LegacyTrack stable -LegacyWebPort 18088 ``
    -CandidateRef 'WorkingTree' -CandidateTrack beta -CandidateWebPort 28088 ``
    -BenchCompare -RunId '$RunId' -SleepBeforeCollect $SleepBeforeCollect ``
    *>&1 | Tee-Object -FilePath '$logFile'
Write-Host ''
Write-Host 'Benchmark complete. Press any key to close.' -ForegroundColor Green
`$null = `$host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
"@

$encodedCmd = [Convert]::ToBase64String([System.Text.Encoding]::Unicode.GetBytes($scriptBlock))

Start-Process pwsh -ArgumentList "-NoExit", "-EncodedCommand", $encodedCmd -WindowStyle Normal

Write-Host "Window launched. Monitor progress there." -ForegroundColor Green
Write-Host "Console log: $logFile" -ForegroundColor Green
