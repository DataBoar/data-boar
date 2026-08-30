#!/usr/bin/env pwsh
# Single gate script: run lint/format (via pre-commit) + full pytest suite.
# Memory safety: pre-commit-and-tests runs tests/security/test_mem_integrity.py first (Hypothesis),
# then the rest of the suite with --deselect to avoid double-running those examples.
# Regression hooks include tests/test_detector_entertainment_regression.py (ML vs lyrics/OSS Markdown).
# Linux/macOS twin: scripts/check-all.sh
# Usage (from repo root):
#   .\scripts\check-all.ps1
#   .\scripts\check-all.ps1 -SkipPreCommit   # LOCAL ITERATION ONLY - not ADR-0080 push/PR proof (#1153)

param(
    [switch]$SkipPreCommit = $false,
    [switch]$IncludeVersionSmoke = $false,
    [switch]$Enforced = $false
)

$ErrorActionPreference = "Stop"
$repoRoot = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $repoRoot

if ($SkipPreCommit) {
    Write-Host "check-all: WARNING: -SkipPreCommit is LOCAL ITERATION ONLY." -ForegroundColor Yellow
    Write-Host "This run is NOT the ADR-0080 / #1151 / #1153 publish gate. Re-run without -SkipPreCommit before git push / gh pr create." -ForegroundColor Yellow
}

# PII gate: maintainer seeds vs staged paths only (see scripts/gatekeeper-audit.ps1).
& "$repoRoot\scripts\gatekeeper-audit.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "check-all: ABORTED by gatekeeper-audit (PII seed hit in staged files)." -ForegroundColor Red
    exit $LASTEXITCODE
}

# Same range as CI (ci.yml PII gate change tripwire). Fetch may fail offline;
# the Python tool SKIP/fail-opens if origin/main is missing. Do not swallow the
# tripwire exit code (#1385, ADR-0071 / ADR-0080).
# Never `git fetch --depth=1` here: that converts a full clone into a shallow
# repo and breaks merge-base / pii_history_guard / the tripwire itself.
$prevNativePref = $null
if (Get-Variable -Name PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $prevNativePref = $PSNativeCommandUseErrorActionPreference
    $PSNativeCommandUseErrorActionPreference = $false
}
git fetch origin main 2>$null | Out-Null
if ($null -ne $prevNativePref) {
    $PSNativeCommandUseErrorActionPreference = $prevNativePref
}
Write-Host "PII gate change tripwire (ADR-0071)..." -ForegroundColor Yellow
uv run python "$repoRoot\scripts\gate_change_tripwire.py" --base origin/main
if ($LASTEXITCODE -ne 0) {
    Write-Host "check-all: ABORTED by gate_change_tripwire (ADR-0071)." -ForegroundColor Red
    exit $LASTEXITCODE
}

# #1003: login-env parity (cargo/uv/maturin off default PATH in non-interactive shells).
function Ensure-LoginToolPath {
    if (Get-Command cargo -ErrorAction SilentlyContinue) { return $true }
    $homeDir = if ($env:HOME) { $env:HOME } else { $env:USERPROFILE }
    if (-not $homeDir) { return $false }
    $cargoEnv = Join-Path $homeDir ".cargo" "env"
    if (Test-Path $cargoEnv) { . $cargoEnv }
    $localBin = Join-Path $homeDir ".local" "bin"
    if (Test-Path $localBin) { $env:PATH = "$localBin$([IO.Path]::PathSeparator)$env:PATH" }
    $cargoBin = Join-Path $homeDir ".cargo" "bin"
    if (Test-Path $cargoBin) { $env:PATH = "$cargoBin$([IO.Path]::PathSeparator)$env:PATH" }
    return [bool](Get-Command cargo -ErrorAction SilentlyContinue)
}
if (-not (Ensure-LoginToolPath)) {
    Write-Host "Rust Guard... Failed (cargo not on PATH; source ~/.cargo/env?)" -ForegroundColor Red
    exit 1
}

try {
    $prevPyO3Abi3 = $env:PYO3_USE_ABI3_FORWARD_COMPATIBILITY
    $env:PYO3_USE_ABI3_FORWARD_COMPATIBILITY = "1"
    Push-Location (Join-Path $repoRoot "rust\boar_fast_filter")
    try {
        Write-Host "Running Rust guard (cargo fmt, check, test)..." -ForegroundColor Yellow
        cargo fmt -- --check
        if ($LASTEXITCODE -ne 0) { throw "cargo fmt --check failed." }
        cargo check
        if ($LASTEXITCODE -ne 0) { throw "cargo check failed." }
        cargo test --quiet
        if ($LASTEXITCODE -ne 0) { throw "cargo test failed." }
    } finally {
        Pop-Location
        if ($null -ne $prevPyO3Abi3) {
            $env:PYO3_USE_ABI3_FORWARD_COMPATIBILITY = $prevPyO3Abi3
        } else {
            Remove-Item Env:\PYO3_USE_ABI3_FORWARD_COMPATIBILITY -ErrorAction SilentlyContinue
        }
    }
    Write-Host "Rust Guard... Passed" -ForegroundColor Green
} catch {
    Write-Host "Rust Guard... Failed" -ForegroundColor Red
    exit 1
}

Write-Host "=== check-all: lint + tests ===" -ForegroundColor Cyan

# Keep plan dashboard stats in sync before lint/tests.
Write-Host "Refreshing plans status dashboard..." -ForegroundColor Yellow
& python "$repoRoot\scripts\plans-stats.py" --write
if ($LASTEXITCODE -ne 0) {
    Write-Host "check-all: FAILED to refresh plans dashboard." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "Checking hub index links..." -ForegroundColor Yellow
& python "$repoRoot\scripts\check_hubs.py"
if ($LASTEXITCODE -ne 0) {
    Write-Host "check-all: FAILED hub link check (check_hubs.py)." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "Running Pester (PowerShell logic)..." -ForegroundColor Yellow
& "$repoRoot\scripts\run-pester.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "check-all: FAILED Pester suite (run-pester.ps1)." -ForegroundColor Red
    exit $LASTEXITCODE
}

# Delegate to the existing script so we keep behaviour in one place.
$argsList = @()
if ($SkipPreCommit) {
    $argsList += "-SkipPreCommit"
}

& "$repoRoot\scripts\pre-commit-and-tests.ps1" @argsList
$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host "=== check-all: security scans (Bandit + Zizmor; fail-collect) ===" -ForegroundColor Cyan
    $secArgs = @()
    if ($Enforced) { $secArgs += "-Enforced" }
    & "$repoRoot\scripts\check-all-security-scans.ps1" @secArgs
    $exitCode = $LASTEXITCODE
}

if ($exitCode -eq 0 -and $IncludeVersionSmoke) {
    $smokeScript = "$repoRoot\scripts\version-readiness-smoke.ps1"
    if (Test-Path -LiteralPath $smokeScript) {
        Write-Host "Running version readiness smoke..." -ForegroundColor Yellow
        & $smokeScript
        $exitCode = $LASTEXITCODE
    } else {
        Write-Host "Version readiness smoke script not found; skipping." -ForegroundColor Yellow
    }
}

if ($exitCode -eq 0) {
    Write-Host "check-all: OK (pre-commit, pytest, and security scans passed)." -ForegroundColor Green
} else {
    Write-Host "check-all: FAILED (see output above)." -ForegroundColor Red
}

exit $exitCode

