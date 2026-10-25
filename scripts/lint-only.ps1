#!/usr/bin/env pwsh
# Lint and format only (no tests). Use when you changed docs, templates, or style and want fast feedback without full pytest.
# Saves tokens: run this instead of check-all when only lint/format matters.
# Linux/macOS twin: scripts/lint-only.sh
# Usage (from repo root): .\scripts\lint-only.ps1

$ErrorActionPreference = "Stop"
$repoRoot = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $repoRoot

Write-Host "=== lint-only: pre-commit (Ruff + format + markdown) ===" -ForegroundColor Cyan
uv run pre-commit run --all-files
$exitCode = $LASTEXITCODE
if ($exitCode -eq 0) {
    Write-Host "lint-only: OK." -ForegroundColor Green
} else {
    Write-Host "lint-only: FAILED." -ForegroundColor Red
}
exit $exitCode
