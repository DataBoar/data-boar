# smoke_upgrade_path.ps1 — upgrade-path smoke for data-boar #2162
# Usage: .\scripts\smoke_upgrade_path.ps1 [-PrevVersion '1.7.4'] [-CandidateWheel 'C:\path\to\wheel.whl']
# Reprodutive: clean venv with previous PyPI version, create SQLite anchor, upgrade to candidate wheel built via uv build, verify no TAMPER / -alpha / config rejection.
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
    & "$Venv\Scripts\data-boar.exe" --config $ConfigFixture --check-extras *> $null

    Log "Upgrading to candidate wheel $(Split-Path $CandidateWheel -Leaf)"
    & "$Venv\Scripts\pip.exe" install --force-reinstall --no-deps $CandidateWheel

    Log "Verifying version"
    $VersionOut = & "$Venv\Scripts\data-boar.exe" --version 2>&1
    Log "Version output: $VersionOut"
    if ($VersionOut -match 'alpha') {
        throw "FAIL: version contains -alpha"
    }

    Log "Running with legacy config fixture"
    $RunOut = & "$Venv\Scripts\data-boar.exe" --config $ConfigFixture --check-extras 2>&1
    Log "Run output: $RunOut"
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
