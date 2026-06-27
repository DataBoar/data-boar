param(
    [switch]$Release = $true,
    [string]$Target = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
# Nested Join-Path keeps the separator portable across Windows PowerShell 5.1 and
# PowerShell Core on Linux/musl (the multi-segment Join-Path form needs PS 6+).
$manifestPath = Join-Path (Join-Path (Join-Path $repoRoot "rust") "boar_fast_filter") "Cargo.toml"

if (-not (Test-Path -LiteralPath $manifestPath)) {
    throw "Rust manifest not found: $manifestPath"
}

. (Join-Path $PSScriptRoot "maestro/Lab-MaestroCommon.ps1")
Initialize-MaestroLoginToolPath

Push-Location $repoRoot
try {
    # maturin is a dev dependency (pyproject [dependency-groups].dev, #892), so it is
    # already in the uv-managed .venv. Run it via `uv run maturin` (uv-first) rather
    # than installing it with pip, which would pollute the env outside the lockfile.
    $maturinArgs = @("develop", "--manifest-path", $manifestPath)
    if ($Release) {
        $maturinArgs += "--release"
    }
    if ($Target) {
        $maturinArgs += @("--target", $Target)
    }

    & uv run maturin @maturinArgs
    if ($LASTEXITCODE -ne 0) {
        throw "maturin develop failed"
    }
    Write-Host "[OK] boar_fast_filter installed in current Python environment." -ForegroundColor Green
}
finally {
    Pop-Location
}
