#!/usr/bin/env pwsh
<#
.SYNOPSIS
Autonomous pytest subset for the maturity self-assessment POC (PLAN_MATURITY_* gate 1).

.DESCRIPTION
Runs API, DB batch summaries, integrity, and audit-export parity tests tied to the POC.
Does not replace full .\scripts\check-all.ps1 before merge.

.EXAMPLE
.\scripts\smoke-maturity-assessment-poc.ps1
#>

param(
    [switch] $Quiet
)

$ErrorActionPreference = "Stop"
$repoRoot = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $repoRoot

$tests = @(
    "tests/test_api_assessment_poc.py",
    "tests/test_maturity_assessment_integrity.py",
    "tests/test_database.py::test_maturity_assessment_batch_summaries_newest_first",
    "tests/test_audit_export.py::test_build_audit_trail_maturity_integrity_matches_verify"
)

if (-not $Quiet) {
    Write-Host "=== smoke-maturity-assessment-poc: pytest subset ===" -ForegroundColor Cyan
}

& uv run pytest @tests -v --tb=short
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

if (-not $Quiet) {
    Write-Host "smoke-maturity-assessment-poc: OK." -ForegroundColor Green
}
