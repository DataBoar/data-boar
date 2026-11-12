"""#2226: tests that evaluate "no token" must not depend on the developer's license.

``resolve_license_path`` falls back to ``<user config dir>/databoar/license.jwt``. On a machine
with a real license installed, enforced-mode tests that expect "no token" saw a VALID license
and failed locally while CI (no file) was green.

``isolate_license_environment`` (fixture ``hermetic_license_env``) points ``HOME`` and
``XDG_CONFIG_HOME`` at a temp dir and drops the license / tier environment variables.
The tests below plant a license at the *simulated developer* canonical path and prove that:

1. without isolation the leak is real (control), so the regression test can fail;
2. with isolation the "no token" evaluation blocks again (fail-closed, nothing weakened);
3. the modules that assert "no token" opt in to the fixture.
"""

from __future__ import annotations

import importlib
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from core.licensing import reset_license_guard_for_tests
from core.licensing.guard import LicenseGuard
from core.licensing.paths import canonical_org_license_jwt_path, resolve_license_path
from core.licensing.runtime_feature_tier import get_runtime_tier_for_features
from core.licensing.tier_features import Tier
from tests.license_config_home import (
    LICENSE_ENV_VARS_CLEARED,
    isolate_license_environment,
)
from tests.license_verify_pin import pin_embedded_ed25519_pem

ENFORCED_CFG = {"licensing": {"mode": "enforced"}}

NO_TOKEN_MODULES = (
    "tests.test_licensing_enforcement_no_bypass",
    "tests.test_prefilter_cli_scan_path_1411",
    "tests.test_rust_regex_stage_parity",
    "tests.test_governance_exports_tier_gating",
)


def _plant_dev_license(dev_home: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Install a valid enterprise license at the canonical path of a simulated dev machine."""
    from tests.hybrid_license_fixture import seal_enforced_test_token

    priv = Ed25519PrivateKey.generate()
    pem = (
        priv.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode("ascii")
        .strip()
    )
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "sub": "lic-dev-machine",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(days=30)).timestamp()),
            "dbcid": "dev",
            "dbcname": "Dev Machine",
            "dbenv": "qa",
            "dbissuer": "test-issuer",
            "dbkid": "k1",
            "dbtier": "enterprise",
        },
        priv,
        algorithm="EdDSA",
    )
    token = seal_enforced_test_token(priv, token)
    pin_embedded_ed25519_pem(pem)

    xdg = dev_home / "xdg"
    monkeypatch.setenv("HOME", str(dev_home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg))
    monkeypatch.setenv("USERPROFILE", str(dev_home))
    monkeypatch.setenv("APPDATA", str(dev_home / "AppData" / "Roaming"))
    lic = canonical_org_license_jwt_path()
    lic.parent.mkdir(parents=True)
    lic.write_text(token, encoding="utf-8")
    return lic


@pytest.fixture(autouse=True)
def _guard_reset():
    reset_license_guard_for_tests()
    yield
    reset_license_guard_for_tests()


def test_control_dev_license_at_canonical_path_leaks_without_isolation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Proves the failure mode behind #2226: a dev license changes the "no token" outcome."""
    lic = _plant_dev_license(tmp_path / "dev", monkeypatch)
    assert resolve_license_path(None) == str(lic)
    assert get_runtime_tier_for_features(ENFORCED_CFG) == Tier.ENTERPRISE


def test_isolation_makes_no_token_block_again(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _plant_dev_license(tmp_path / "dev", monkeypatch)
    reset_license_guard_for_tests()

    isolate_license_environment(monkeypatch, tmp_path / "sandbox")

    assert resolve_license_path(None) == ""
    assert not canonical_org_license_jwt_path().exists()
    guard = LicenseGuard(ENFORCED_CFG)
    assert guard.allows_scan() is False
    assert get_runtime_tier_for_features(ENFORCED_CFG) == Tier.COMMUNITY


def test_isolation_moves_home_and_xdg_under_the_given_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sandbox = tmp_path / "sandbox"
    isolate_license_environment(monkeypatch, sandbox)
    for name in ("HOME", "XDG_CONFIG_HOME"):
        assert Path(os.environ[name]).resolve().is_relative_to(sandbox.resolve()), name
    assert canonical_org_license_jwt_path().resolve().is_relative_to(sandbox.resolve())


def test_isolation_clears_license_and_tier_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for name in LICENSE_ENV_VARS_CLEARED:
        monkeypatch.setenv(name, "x")
    assert "DATA_BOAR_LICENSE_PATH" in LICENSE_ENV_VARS_CLEARED
    assert "DATA_BOAR_LICENSE_MODE" in LICENSE_ENV_VARS_CLEARED
    assert "DATA_BOAR_TIER_OVERRIDE" in LICENSE_ENV_VARS_CLEARED

    isolate_license_environment(monkeypatch, tmp_path / "sandbox")

    assert [n for n in LICENSE_ENV_VARS_CLEARED if n in os.environ] == []


def test_isolation_does_not_enable_anything(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The sandbox must be strictly "no license": explicit config paths still work."""
    isolate_license_environment(monkeypatch, tmp_path / "sandbox")
    assert resolve_license_path("/some/explicit.jwt") == "/some/explicit.jwt"


@pytest.mark.parametrize("module_name", NO_TOKEN_MODULES)
def test_no_token_modules_opt_in_to_hermetic_fixture(module_name: str) -> None:
    module = importlib.import_module(module_name)
    marks = getattr(module, "pytestmark", [])
    marks = marks if isinstance(marks, list) else [marks]
    used = {
        arg
        for mark in marks
        if getattr(mark, "name", "") == "usefixtures"
        for arg in mark.args
    }
    assert "hermetic_license_env" in used, (
        f"{module_name} asserts 'no token' and must use the hermetic_license_env fixture (#2226)"
    )
