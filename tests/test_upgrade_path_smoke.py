"""#2162 upgrade-path smoke logic tests (no network)."""

from __future__ import annotations

from pathlib import Path
import pytest


CONFIG_FIXTURE = Path("tests/data/upgrade_2162/pre_1_8_0_legacy_credentials.yaml")


def test_legacy_config_fixture_exists():
    import yaml

    assert CONFIG_FIXTURE.exists(), "fixture missing"
    data = yaml.safe_load(CONFIG_FIXTURE.read_text())
    assert "targets" in data
    # Verify all 4 legacy targets are present
    target_names = {t.get("name") for t in data["targets"]}
    expected = {"pg-legacy", "smb-legacy", "mongo-legacy", "redis-legacy"}
    assert target_names == expected, f"Expected {expected}, got {target_names}"
    # Verify they use legacy DATABOAR_* env var names (pre-1.8.0 style)
    for t in data["targets"]:
        assert (
            t.get("pass_from_env", "").startswith("DATABOAR_")
            or t.get("pass_from_env") == "MEU_BANCO_SENHA"
        )
    # Verify sqlite_path is present
    assert data.get("sqlite_path") == "audit_legacy_upgrade.db"
    # Verify database targets use 'engine' (pre-1.8.0 schema), not 'driver'
    for t in data["targets"]:
        if t.get("type") == "database":
            assert "engine" in t, (
                f"Database target {t.get('name')} should use 'engine' not 'driver'"
            )
            assert "driver" not in t, (
                f"Database target {t.get('name')} should not use 'driver'"
            )


def test_smoke_script_exists():
    from pathlib import Path as P

    assert P("scripts/smoke_upgrade_path.sh").exists()
    assert P("scripts/smoke_upgrade_path.ps1").exists()


@pytest.mark.parametrize("prev", ["1.7.4", "1.8.0"])
def test_smoke_decision_matrix(prev: str):
    script_sh = Path("scripts/smoke_upgrade_path.sh").read_text()
    script_ps1 = Path("scripts/smoke_upgrade_path.ps1").read_text()

    # Both scripts must parameterize previous version
    assert "PREV_VERSION" in script_sh or "PrevVersion" in script_sh
    assert "PrevVersion" in script_ps1

    # Both scripts must reference the legacy config fixture
    assert "pre_1_8_0_legacy_credentials.yaml" in script_sh
    assert "pre_1_8_0_legacy_credentials.yaml" in script_ps1

    # Both scripts must check for TAMPER / -alpha
    assert "INTEGRITY TAMPER DETECTED" in script_sh
    assert "INTEGRITY TAMPER DETECTED" in script_ps1
    assert "-alpha" in script_sh or "alpha" in script_sh
    assert "alpha" in script_ps1

    # Both scripts must use the CLI command that creates the anchor (main.py:1593 -> _run_startup_integrity_check)
    assert "main.py:1593" in script_sh
    assert "main.py:1593" in script_ps1

    # Both scripts must NOT use || true for exit code handling
    assert "|| true" not in script_sh
    # PowerShell doesn't have || true equivalent but should check $LASTEXITCODE

    # Both scripts must install candidate WITH dependencies (not --no-deps)
    assert "pip install --force-reinstall" in script_sh and "--no-deps" not in script_sh
    assert (
        "pip.exe" in script_ps1
        and "install --force-reinstall" in script_ps1
        and "--no-deps" not in script_ps1
    )

    # Both scripts must isolate HOME/XDG to mktemp
    assert "mktemp" in script_sh or "GetTempPath" in script_sh
    assert "GetTempPath" in script_ps1
    assert "HOME" in script_sh and "XDG" in script_sh
    assert "HOME" in script_ps1 and "XDG" in script_ps1

    # Both scripts must NOT relax any gates (no CREDENTIAL_STRICT=0, HOSTS_UNRESTRICTED=1)
    assert "CREDENTIAL_STRICT" not in script_sh
    assert "HOSTS_UNRESTRICTED" not in script_sh
    assert "CREDENTIAL_STRICT" not in script_ps1
    assert "HOSTS_UNRESTRICTED" not in script_ps1


def evaluate_upgrade(version_out: str, run_out: str, exit_code: int) -> bool:
    """Return True if upgrade smoke would PASS."""
    if exit_code != 0:
        return False
    if "alpha" in version_out.lower():
        return False
    if "INTEGRITY TAMPER DETECTED" in run_out.upper():
        return False
    if "tampered" in run_out.lower():
        return False
    return True


@pytest.mark.parametrize(
    "version_out,run_out,exit_code,expected",
    [
        # Baseline passing cases
        ("Data Boar 1.8.1", "OK", 0, True),
        ("Data Boar 1.8.1", "Configuration valid", 0, True),
        # Failure: version contains -alpha
        ("Data Boar 1.8.1-alpha", "OK", 0, False),
        ("Data Boar 1.7.4-alpha", "OK", 0, False),
        # Failure: INTEGRITY TAMPER DETECTED in run output
        ("Data Boar 1.8.1", "INTEGRITY TAMPER DETECTED", 0, False),
        (
            "Data Boar 1.8.1",
            "ERROR: INTEGRITY TAMPER DETECTED in core/engine.py",
            0,
            False,
        ),
        # Failure: tampered in run output (case-insensitive)
        ("Data Boar 1.8.1", "tampered files", 0, False),
        ("Data Boar 1.8.1", "Files are TAMPERED", 0, False),
        # Failure: non-zero exit code (config rejected or other error)
        ("Data Boar 1.8.1", "OK", 1, False),
        ("Data Boar 1.8.1", "Config validation failed", 2, False),
        # Combined failures
        ("Data Boar 1.8.1-alpha", "INTEGRITY TAMPER DETECTED", 1, False),
    ],
)
def test_evaluate_upgrade_decision(version_out, run_out, exit_code, expected):
    assert evaluate_upgrade(version_out, run_out, exit_code) is expected
