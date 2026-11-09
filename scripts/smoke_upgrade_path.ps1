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
$ConfigFixture = Join-Path $RepoRoot 'tests/data/upgrade_2162/pre_1_8_0_legacy_credentials.yaml'

$WorkDir = Join-Path ([System.IO.Path]::GetTempPath()) ("smoke_upgrade_$([guid]::NewGuid().ToString('N'))")
New-Item -ItemType Directory -Path $WorkDir | Out-Null
$Venv = Join-Path $WorkDir 'venv'

# Isolate user data
$env:HOME = Join-Path $WorkDir 'home'
$env:XDG_CONFIG_HOME = Join-Path $WorkDir 'xdg_config'
$env:XDG_DATA_HOME = Join-Path $WorkDir 'xdg_data'
$env:XDG_CACHE_HOME = Join-Path $WorkDir 'xdg_cache'
@($env:HOME, $env:XDG_CONFIG_HOME, $env:XDG_DATA_HOME, $env:XDG_CACHE_HOME) | ForEach-Object { New-Item -ItemType Directory -Path $_ -Force | Out-Null }

# Provide dummy values for legacy credential env vars
$env:DATABOAR_PG_PASSWORD = 'dummy'
$env:MEU_BANCO_SENHA = 'dummy'
$env:DATABOAR_MONGO_PASS = 'dummy'
$env:DATABOAR_REDIS_PASS = 'dummy'

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

    & "$Venv\Scripts\pip.exe" install pymongo redis pysmb

    # Detect anchor feature by checking if --version creates the anchor
    # The anchor is created by _run_startup_integrity_check() at main.py:1070 via --version
    $HasAnchorFeature = $false
    $helpOutput = & "$Venv\Scripts\data-boar.exe" --help 2>&1
    if ($helpOutput -match '\-\-plan') {
        $HasAnchorFeature = $true
        Log "Previous version $PrevVersion has integrity anchor feature (main.py:1070 -> --version)"
    } else {
        Log "Previous version $PrevVersion does NOT have integrity anchor feature (expected for 1.7.4)"
    }

    Set-Location $WorkDir
    $AnchorDb = Join-Path $WorkDir 'audit_legacy_upgrade.db'

    if ($HasAnchorFeature) {
        Log "First run to create SQLite anchor via previous version (main.py:1070 -> --version)"
        # The real user command that creates the anchor is: data-boar --version
        # This triggers _run_startup_integrity_check at main.py:1070 with sqlite_path: audit_results.db
        $null = & "$Venv\Scripts\data-boar.exe" --version 2>$null
        $AuditResultsDb = Join-Path $WorkDir 'audit_results.db'
        if (Test-Path $AuditResultsDb) {
            Move-Item $AuditResultsDb $AnchorDb -Force
            Log "Anchor created at $AnchorDb via --version (main.py:1070)"
        } else {
            throw "FAIL: integrity anchor DB not created at $AnchorDb"
        }
    } else {
        Log "Creating empty anchor DB (previous version $PrevVersion lacks integrity anchor feature)"
        # Create empty anchor DB for upgrade test (candidate will have the feature)
        & "$Venv\Scripts\python.exe" -c @"
import sqlite3
conn = sqlite3.connect('$AnchorDb')
conn.execute('CREATE TABLE IF NOT EXISTS build_integrity_anchor (anchor_version INTEGER PRIMARY KEY, release_label TEXT NOT NULL, manifest_content_hash TEXT NOT NULL, file_hashes_json TEXT NOT NULL, validated_at TEXT NOT NULL, build_digest_matched INTEGER NOT NULL, validator_version TEXT NOT NULL, signed_release_label TEXT)')
conn.commit()
conn.close()
"@
    }

    Log "Upgrading to candidate wheel $(Split-Path $CandidateWheel -Leaf)"
    & "$Venv\Scripts\pip.exe" install --force-reinstall $CandidateWheel
    & "$Venv\Scripts\pip.exe" install pymongo redis pysmb

    Log "Verifying version"
    $VersionOut = & "$Venv\Scripts\data-boar.exe" --version 2>&1
    Log "Version output: $VersionOut"

    Log "Running with legacy config fixture (--plan to verify acceptance)"
    $RunOut = & "$Venv\Scripts\data-boar.exe" --plan --config $ConfigFixture 2>&1
    $RunExit = $LASTEXITCODE
    Log "Run output: $RunOut"

    if ($RunExit -ne 0) {
        throw "FAIL: validate-config exited with $RunExit (legacy config rejected - regression of #2164)"
    }

    # Check if candidate has valid signed manifest (not tampered)
    # For unsigned local builds, the integrity is NOT evaluated - this is PARTIAL mode
    # The anchor (validated anchor ()) appears empty for unsigned builds
    if ($VersionOut -match 'validated anchor \(\)') {
        Log "integridade NAO avaliada: candidato sem manifesto assinado"
        Log "Upgrade path PARTIAL (unsigned candidate)"
        Write-Host "UPGRADE_PATH_PARTIAL $PrevVersion -> $(Split-Path $CandidateWheel -Leaf)"
        exit 1
    }

    # Check for TAMPER / -alpha issues (for signed releases)
    if ($VersionOut -match 'alpha') {
        throw "FAIL: version contains -alpha (candidate appears unsigned)"
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