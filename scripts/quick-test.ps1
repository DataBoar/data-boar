#!/usr/bin/env pwsh
# Run a subset of tests (by path or keyword). Use when iterating on one area to save tokens vs full pytest.
# Linux/macOS twin: scripts/quick-test.sh
# Usage (from repo root):
#   .\scripts\quick-test.ps1                           # runs all tests (same as check-all -SkipPreCommit)
#   .\scripts\quick-test.ps1 -Path tests/test_foo.py    # single file
#   .\scripts\quick-test.ps1 -Keyword "content_type"    # pytest -k "content_type"
#   .\scripts\quick-test.ps1 -Path tests/test_foo.py -Keyword "test_bar"

param(
    [string]$Path = "",
    [string]$Keyword = ""
)

$ErrorActionPreference = "Stop"
$repoRoot = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $repoRoot

$pytestArgs = @("-v", "-W", "error", "--tb=short")
if ($Path) {
    $pytestArgs += $Path
}
if ($Keyword) {
    $pytestArgs += "-k", $Keyword
}

Write-Host "=== quick-test: pytest (subset) ===" -ForegroundColor Cyan
if ($Path) { Write-Host "  Path: $Path" }
if ($Keyword) { Write-Host "  Keyword: $Keyword" }
uv run pytest @pytestArgs
$exitCode = $LASTEXITCODE
if ($exitCode -eq 0) {
    Write-Host "quick-test: OK." -ForegroundColor Green
} else {
    Write-Host "quick-test: FAILED." -ForegroundColor Red
}
exit $exitCode
