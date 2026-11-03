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
    # This test verifies the script's expectations without running network install.
    # We only validate that the script references the fixture and version params.
    script = Path("scripts/smoke_upgrade_path.sh").read_text()
    assert "PREV_VERSION" in script
    assert (
        str(CONFIG_FIXTURE) in script or "pre_1_8_0_legacy_credentials.yaml" in script
    )
    assert "INTEGRITY TAMPER DETECTED" in script
    assert "-alpha" in script


def yaml_safe_load(text: str):
    import yaml

    return yaml.safe_load(text)
