"""#2162 upgrade-path smoke logic tests (no network)."""

from __future__ import annotations

from pathlib import Path
import pytest


CONFIG_FIXTURE = Path("tests/data/upgrade_2162/pre_1_8_0_legacy_credentials.yaml")


def test_legacy_config_fixture_exists():
    assert CONFIG_FIXTURE.exists(), "fixture missing"
    data = yaml_safe_load(CONFIG_FIXTURE.read_text())
    assert "targets" in data
    assert any(t.get("name") == "pg-legacy" for t in data["targets"])


def test_smoke_script_exists():
    from pathlib import Path as P

    assert P("scripts/smoke_upgrade_path.sh").exists()
    assert P("scripts/smoke_upgrade_path.ps1").exists()


@pytest.mark.parametrize("prev", ["1.7.4", "1.8.0"])
def test_smoke_decision_matrix(prev: str):
    # Decision matrix: upgrade should not produce TAMPER / -alpha / config rejection.
    script = Path("scripts/smoke_upgrade_path.sh").read_text()
    assert "PREV_VERSION" in script
    assert (
        str(CONFIG_FIXTURE) in script or "pre_1_8_0_legacy_credentials.yaml" in script
    )
    assert "INTEGRITY TAMPER DETECTED" in script
    assert "-alpha" in script


def evaluate_upgrade(version_out: str, run_out: str, exit_code: int) -> bool:
    """Return True if upgrade smoke would PASS."""
    if exit_code != 0:
        return False
    if "alpha" in version_out.lower():
        return False
    if "INTEGRITY TAMPER DETECTED" in run_out:
        return False
    if "tampered" in run_out.lower():
        return False
    return True


@pytest.mark.parametrize(
    "version_out,run_out,exit_code,expected",
    [
        ("Data Boar 1.8.1", "OK", 0, True),
        ("Data Boar 1.8.1-alpha", "OK", 0, False),
        ("Data Boar 1.8.1", "INTEGRITY TAMPER DETECTED", 0, False),
        ("Data Boar 1.8.1", "tampered files", 0, False),
        ("Data Boar 1.8.1", "OK", 1, False),
    ],
)
def test_evaluate_upgrade_decision(version_out, run_out, exit_code, expected):
    assert evaluate_upgrade(version_out, run_out, exit_code) is expected


def yaml_safe_load(text: str):
    import yaml

    return yaml.safe_load(text)
