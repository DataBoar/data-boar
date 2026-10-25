# Priority band A6  - licensing smoke (fast, no network).
# Runs the pytest slice that covers JWT / licensing helpers used in production paths.
# From repo root: .\scripts\license-smoke.ps1
# Equivalent: uv run pytest tests/test_licensing.py tests/test_licensing_fingerprint.py -q

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
uv run pytest tests/test_licensing.py tests/test_licensing_fingerprint.py -q --tb=short
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "license-smoke: OK"
