# smoke_upgrade_path.ps1 — upgrade-path smoke for data-boar #2162
# Usage: .\scripts\smoke_upgrade_path.ps1 [-PrevVersion '1.7.4'] [-CandidateWheel 'C:\path\to\wheel.whl']
# Reproducible: clean venv with previous PyPI version, create SQLite anchor, upgrade to candidate wheel built via uv build, verify no TAMPER / -alpha / config rejection.
[CmdletBinding()]
param(
    [string]$PrevVersion = '1.7.4',
    [string]$CandidateWheel = ''
)

$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$WorkDir = Join-Path ([System.IO.Path]::GetTempPath()) ("smoke_upgrade_$([guid]::NewGuid().ToString('N'))")
New-Item -ItemType Directory -Path $WorkDir | Out-Null
$Venv = Join-Path $WorkDir 'venv'
$ConfigFixture = Join-Path $RepoRoot 'tests/data/upgrade_2162/pre_1_8_0_legacy_credentials.yaml'

# Isolate user data
$env:HOME = Join-Path $WorkDir 'home'
$env:XDG_CONFIG_HOME = Join-Path $WorkDir 'xdg_config'
$env:XDG_DATA_HOME = Join-Path $WorkDir 'xdg_data'
$env:XDG_CACHE_HOME = Join-Path $WorkDir 'xdg_cache'
@($env:HOME, $env:XDG_CONFIG_HOME, $env:XDG_DATA_HOME, $env:XDG_CACHE_HOME) | ForEach-Object { New-Item -ItemType Directory -Path $_ -Force | Out-Null }

function Log { param([string]$msg) Write-Host "[smoke] $msg" }

try {
    Log "Creating venv"
    python -m venv $Venv
    & "$Venv\Scripts\python.exe" -m pip install --upgrade pip

    if ([string]::IsNullOrWhiteSpace($CandidateWheel)) {
        Log "Building candidate wheel"
        uv build --wheel --out-dir "$WorkDir\dist" | Out-Null
        $CandidateWheel = Get-ChildItem "$WorkDir\dist\data_boar-*.whl" | Select-Object -First 1 -ExpandProperty FullName
    }

    Log "Installing previous version $PrevVersion"
    & "$Venv\Scripts\pip.exe" install "data-boar==$PrevVersion"

    Log "First run to create SQLite anchor"
    # --validate-config triggers _run_startup_integrity_check (main.py:265) -> ensure_integrity_anchor
    & "$Venv\Scripts\data-boar.exe" --validate-config --config $ConfigFixture
    # Verify anchor DB exists
    $sqlitePath = Select-String -Path $ConfigFixture -Pattern '^\s*sqlite_path:' | ForEach-Object { $_.Line -replace '^\s*sqlite_path:\s*','' }
    if (-not [string]::IsNullOrWhiteSpace($sqlitePath) -and -not (Test-Path $sqlitePath)) {
        throw "FAIL: integrity anchor DB not created at $sqlitePath"
    }
    Log "Anchor created at $sqlitePath"

    Log "Upgrading to candidate wheel $(Split-Path $CandidateWheel -Leaf)"
    & "$Venv\Scripts\pip.exe" install --force-reinstall $CandidateWheel

    Log "Verifying version"
    $VersionOut = & "$Venv\Scripts\data-boar.exe" --version 2>&1
    Log "Version output: $VersionOut"
    if ($VersionOut -match 'alpha') {
        throw "FAIL: version contains -alpha"
    }

    Log "Running with legacy config fixture"
    $RunOut = & "$Venv\Scripts\data-boar.exe" --validate-config --config $ConfigFixture 2>&1
    $RunExit = $LASTEXITCODE
    Log "Run output: $RunOut"
    if ($RunExit -ne 0) {
        throw "FAIL: validate-config exited with $RunExit (config rejected?)"
    }
    if ($RunOut -match 'INTEGRITY TAMPER DETECTED') {
        throw "FAIL: INTEGRITY TAMPER DETECTED after upgrade"
    }
    if ($RunOut -match 'tampered') {
        throw "FAIL: tampered signal after upgrade"
    }

    Log "Smoke passed: $PrevVersion -> candidate"
    Write-Host "UPGRADE_PATH_OK $PrevVersion -> $(Split-Path $CandidateWheel -Leaf)"
}
finally {
    Remove-Item -Recurse -Force $WorkDir -ErrorAction SilentlyContinue
}
