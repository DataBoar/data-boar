#!/usr/bin/env pwsh
# Run pre-commit (Ruff + plans-stats --check + markdown + pt-BR + commercial guard) and full pytest via uv.
# Linux/macOS twin: scripts/pre-commit-and-tests.sh
# Usage (from repo root):
#   .\scripts\pre-commit-and-tests.ps1
#   .\scripts\pre-commit-and-tests.ps1 -SkipPreCommit   # only pytest

param(
    [switch]$SkipPreCommit = $false
)

$ErrorActionPreference = "Stop"
$repoRoot = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $repoRoot

# Recover from a broken/missing project venv (uv run needs .venv/pyvenv.cfg).
$venvCfg = Join-Path $repoRoot ".venv/pyvenv.cfg"
if (-not (Test-Path -LiteralPath $venvCfg)) {
    Write-Host "No .venv/pyvenv.cfg - running uv sync to recreate the environment..." -ForegroundColor Yellow
    uv sync
    if (-not (Test-Path -LiteralPath $venvCfg)) {
        Write-Host "check gate: uv sync did not create .venv; fix disk path or UV_* env and retry." -ForegroundColor Red
        exit 2
    }
}

if (-not $SkipPreCommit) {
    Write-Host "Running pre-commit (Ruff + markdown + pt-BR locale guards)..." -ForegroundColor Cyan
    uv run pre-commit run --all-files
    if ($LASTEXITCODE -ne 0) {
        Write-Host "pre-commit failed. Attempting to auto-apply Ruff formatting and re-run pre-commit once..." -ForegroundColor Yellow
        try {
            # Best-effort: format the codebase with Ruff, then re-run pre-commit.
            uv run ruff format .
            uv run pre-commit run --all-files
        } catch {
            Write-Host "Auto-format step failed: $($_.Exception.Message)" -ForegroundColor Red
        }
        if ($LASTEXITCODE -ne 0) {
            Write-Host "pre-commit still failing after auto-format. Fix issues above before committing or pushing." -ForegroundColor Red
            exit $LASTEXITCODE
        }
    }
}

Write-Host "Memory safety gate (Hypothesis + PyO3, tests/security/test_mem_integrity.py)..." -ForegroundColor Cyan
uv run pytest tests/security/test_mem_integrity.py -v -W error --tb=short
if ($LASTEXITCODE -ne 0) {
    Write-Host "Memory safety pytest failed. Fix failures before committing or pushing." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "Running pytest (full suite, warnings treated as errors)..." -ForegroundColor Cyan
uv run pytest -v -W error --tb=short --deselect tests/security/test_mem_integrity.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "pytest failed. Fix test failures before committing or pushing." -ForegroundColor Red
}

exit $LASTEXITCODE

