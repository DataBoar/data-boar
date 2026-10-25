#Requires -Version 5.1
<#
.SYNOPSIS
  Hcusehold finance dashboard (stub -- real script in docs/private/scripts/).
.DESCRIPTION
  The full household-finance.ps1 contains personal financial and medical
  information that must not be tracked in the public repository.
  The real script lives in docs/private/scripts/household-finance.ps1
  (stacked private repo, synced to lab-op hosts).
.NOTES
  GUARDRAIL: This stub exists only so tests that check script syntax
  do not fail. All functionality is in the private copy.
#>
param([string]$Mode = "status")

$privatePath = Join-Path $PSScriptRoot "..\docs\private\scripts\household-finance.ps1"
if (Test-Path $privatePath) {
    & $privatePath -Mode $Mode
} else {
    Write-Warning "household-finance.ps1: full script not found at $privatePath"
    Write-Warning "This script contains personal data and lives only in docs/private/scripts/"
    Write-Warning "See docs/PRIVATE_OPERATOR_NOTES.md for setup."
}
