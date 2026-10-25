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

# PATH prelude (was Initialize-MaestroLoginToolPath in Lab-MaestroCommon; inlined so
# rust builds do not require a sibling DataBoar/maestro clone - maestro#8 purge).
$homeDir = if ($env:HOME) { $env:HOME } else { $env:USERPROFILE }
if ($homeDir) {
    $cargoEnv = Join-Path (Join-Path $homeDir ".cargo") "env"
    if (Test-Path -LiteralPath $cargoEnv) { . $cargoEnv }
    foreach ($dir in @(
            (Join-Path (Join-Path $homeDir ".local") "bin"),
            (Join-Path (Join-Path $homeDir ".cargo") "bin")
        )) {
        if (Test-Path -LiteralPath $dir) {
            $env:PATH = "$dir$([IO.Path]::PathSeparator)$env:PATH"
        }
    }
}

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
