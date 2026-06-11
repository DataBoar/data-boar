"""
#719 regression — env vars can NEVER bypass licensing enforcement.

Contract under test:

1. ``DATA_BOAR_ENV=development`` / ``DEBUG=1`` / ``DATA_BOAR_TIER_OVERRIDE``
   have zero effect when ``licensing.mode: enforced`` — the gate still bites.
2. ``DATA_BOAR_LICENSE_MODE=open`` cannot downgrade YAML ``mode: enforced``.
3. Enforced without a valid signed license fails CLOSED (scan denied,
   tier capped to Community) — never "open".
4. Every enforcement decision lands on the ``data_boar.licensing.audit``
   logger (allow / deny / clamp / expire).
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from core.licensing.guard import LicenseGuard, reset_license_guard_for_tests
from core.licensing.runtime_feature_tier import get_runtime_tier_for_features
from core.licensing.tier_features import Tier

AUDIT_LOGGER = "data_boar.licensing.audit"


def _pem_public(priv: Ed25519PrivateKey) -> str:
    return (
        priv.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode("ascii")
        .strip()
    )


def _make_token(
    priv: Ed25519PrivateKey,
    *,
    exp_delta_days: int = 7,
    extra: dict | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "lic-no-bypass",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=exp_delta_days)).timestamp()),
        "dbcid": "cust-1",
        "dbcname": "Test Customer",
        "dbenv": "qa",
        "dbissuer": "test-issuer",
        "dbkid": "k1",
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, priv, algorithm="EdDSA")


@pytest.fixture
def ed25519_priv() -> Ed25519PrivateKey:
    return Ed25519PrivateKey.generate()


@pytest.fixture(autouse=True)
def _clean_env():
    reset_license_guard_for_tests()
    keys = (
        "DATA_BOAR_ENV",
        "DEBUG",
        "DATA_BOAR_TIER_OVERRIDE",
        "DATA_BOAR_LICENSE_MODE",
        "DATA_BOAR_LICENSE_PATH",
        "DATA_BOAR_LICENSE_PUBLIC_KEY_PEM",
        "DATA_BOAR_LICENSE_PUBLIC_KEY_PATH",
        "DATA_BOAR_LICENSE_REVOCATION_PATH",
    )
    saved = {k: os.environ.get(k) for k in keys}
    for k in keys:
        os.environ.pop(k, None)
    yield
    reset_license_guard_for_tests()
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


def _audit_records(caplog):
    return [r for r in caplog.records if r.name == AUDIT_LOGGER]


# --- 1. dev env vars do not bypass enforced mode -------------------------


def test_dev_env_and_tier_override_do_not_bypass_enforced(monkeypatch, caplog):
    """THE #719 regression: DATA_BOAR_ENV=development + enforced still bites."""
    monkeypatch.setenv("DATA_BOAR_ENV", "development")
    monkeypatch.setenv("DEBUG", "1")
    monkeypatch.setenv("DATA_BOAR_TIER_OVERRIDE", "enterprise")
    cfg = {"licensing": {"mode": "enforced"}}
    with caplog.at_level(logging.DEBUG, logger=AUDIT_LOGGER):
        g = LicenseGuard(cfg)
        assert g.allows_scan() is False  # fail-closed: no key, no license
        assert get_runtime_tier_for_features(cfg) == Tier.COMMUNITY
    crit = [r for r in _audit_records(caplog) if r.levelno == logging.CRITICAL]
    assert crit, "deny decisions in enforced mode must be CRITICAL audit records"
    assert any("scan_gate" in r.message for r in crit)
    assert any("tier_fail_closed" in r.message for r in crit)


def test_debug_env_alone_does_not_grant_tier(monkeypatch):
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("DATA_BOAR_TIER_OVERRIDE", "enterprise")
    cfg = {"licensing": {"mode": "open", "effective_tier": "community"}}
    assert get_runtime_tier_for_features(cfg) == Tier.COMMUNITY


# --- 2. env cannot downgrade enforced -> open -----------------------------


def test_env_license_mode_cannot_downgrade_enforced(monkeypatch, caplog):
    monkeypatch.setenv("DATA_BOAR_LICENSE_MODE", "open")
    cfg = {"licensing": {"mode": "enforced"}}
    with caplog.at_level(logging.DEBUG, logger=AUDIT_LOGGER):
        g = LicenseGuard(cfg)
    assert g.mode == "enforced"
    assert g.allows_scan() is False
    assert any(
        "env_mode_downgrade_ignored" in r.message for r in _audit_records(caplog)
    )


def test_env_license_mode_can_escalate_open_to_enforced(monkeypatch):
    monkeypatch.setenv("DATA_BOAR_LICENSE_MODE", "enforced")
    cfg = {"licensing": {"mode": "open"}}
    g = LicenseGuard(cfg)
    assert g.mode == "enforced"
    assert g.allows_scan() is False


# --- 3. fail-closed tier resolution in enforced mode ----------------------


def test_yaml_effective_tier_ignored_in_enforced(monkeypatch):
    """YAML effective_tier cannot grant tier without a valid license."""
    cfg = {"licensing": {"mode": "enforced", "effective_tier": "enterprise"}}
    assert get_runtime_tier_for_features(cfg) == Tier.COMMUNITY


def test_enforced_valid_license_dbtier_governs(ed25519_priv, tmp_path):
    lic = tmp_path / "t.lic"
    lic.write_text(_make_token(ed25519_priv, extra={"dbtier": "pro"}), encoding="utf-8")
    os.environ["DATA_BOAR_LICENSE_PUBLIC_KEY_PEM"] = _pem_public(ed25519_priv)
    cfg = {
        "licensing": {
            "mode": "enforced",
            "license_path": str(lic),
            # YAML tier must lose to the JWT claim in enforced mode:
            "effective_tier": "enterprise",
        }
    }
    g = LicenseGuard(cfg)
    assert g.context.state == "VALID"
    assert g.allows_scan() is True
    assert get_runtime_tier_for_features(cfg) == Tier.PRO


def test_enforced_valid_license_without_dbtier_falls_to_community(
    ed25519_priv, tmp_path
):
    lic = tmp_path / "t.lic"
    lic.write_text(_make_token(ed25519_priv), encoding="utf-8")
    os.environ["DATA_BOAR_LICENSE_PUBLIC_KEY_PEM"] = _pem_public(ed25519_priv)
    cfg = {"licensing": {"mode": "enforced", "license_path": str(lic)}}
    assert get_runtime_tier_for_features(cfg) == Tier.COMMUNITY


def test_enforced_expired_license_fails_closed(ed25519_priv, tmp_path, caplog):
    lic = tmp_path / "t.lic"
    lic.write_text(
        _make_token(ed25519_priv, exp_delta_days=-2, extra={"dbtier": "enterprise"}),
        encoding="utf-8",
    )
    os.environ["DATA_BOAR_LICENSE_PUBLIC_KEY_PEM"] = _pem_public(ed25519_priv)
    cfg = {"licensing": {"mode": "enforced", "license_path": str(lic)}}
    with caplog.at_level(logging.DEBUG, logger=AUDIT_LOGGER):
        g = LicenseGuard(cfg)
        # PyJWT rejects expired tokens at decode time (INVALID); the guard's
        # own EXPIRED state covers grace-window logic. Both fail closed.
        assert g.context.state in ("EXPIRED", "INVALID")
        assert g.allows_scan() is False
        assert get_runtime_tier_for_features(cfg) == Tier.COMMUNITY
    assert any(
        "license_evaluated" in r.message and r.levelno == logging.CRITICAL
        for r in _audit_records(caplog)
    )


# --- 4. audit log coverage (allow / deny / clamp) --------------------------


def test_audit_allow_decisions_recorded(ed25519_priv, tmp_path, caplog):
    lic = tmp_path / "t.lic"
    lic.write_text(
        _make_token(ed25519_priv, extra={"dbtier": "enterprise"}), encoding="utf-8"
    )
    os.environ["DATA_BOAR_LICENSE_PUBLIC_KEY_PEM"] = _pem_public(ed25519_priv)
    cfg = {"licensing": {"mode": "enforced", "license_path": str(lic)}}
    with caplog.at_level(logging.DEBUG, logger=AUDIT_LOGGER):
        g = LicenseGuard(cfg)
        assert g.allows_scan() is True
    records = _audit_records(caplog)
    assert any(
        "license_evaluated" in r.message and "allowed=true" in r.message
        for r in records
    )
    assert any(
        "scan_gate" in r.message and "allowed=true" in r.message for r in records
    )


def test_audit_feature_denial_recorded(caplog):
    cfg = {"licensing": {"mode": "open", "effective_tier": "community"}}
    with caplog.at_level(logging.DEBUG, logger=AUDIT_LOGGER):
        g = LicenseGuard(cfg)
        result = g.check_feature("governance_lens_pro")
    assert not result.allowed
    assert any("feature_denied" in r.message for r in _audit_records(caplog))


def test_audit_trial_clamp_recorded(ed25519_priv, tmp_path, caplog):
    lic = tmp_path / "t.lic"
    lic.write_text(
        _make_token(ed25519_priv, extra={"dbtrial": True, "dbmaxrows": 100}),
        encoding="utf-8",
    )
    os.environ["DATA_BOAR_LICENSE_PUBLIC_KEY_PEM"] = _pem_public(ed25519_priv)
    cfg = {"licensing": {"mode": "enforced", "license_path": str(lic)}}
    with caplog.at_level(logging.DEBUG, logger=AUDIT_LOGGER):
        g = LicenseGuard(cfg)
        assert g.trial_cap_rows() == 100
    assert any("report_rows_clamped" in r.message for r in _audit_records(caplog))
