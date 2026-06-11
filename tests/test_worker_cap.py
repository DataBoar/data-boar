"""
#551 — licensing worker cap (``dbmax_workers``).

Contract under test:

1. Open mode (no ``licensing:`` block or ``mode: open``) NEVER caps
   ``scan.max_workers`` — ``worker_cap()`` returns ``None``.
2. Enforced mode with a usable (VALID/GRACE) license: a positive
   ``dbmax_workers`` claim wins.
3. Enforced mode without the claim: tier fallback defaults apply —
   Community 2 / Pro 5 / Enterprise unlimited (``None``).
4. Enforced fail-closed states (no license, invalid) resolve the tier to
   Community → inherit the Community cap. Dev env vars do not lift it (#719).
5. Engine integration: ``start_audit`` clamps ``_max_workers`` to the cap
   (fail-soft, scan still runs) and records a ``workers_clamped`` WARNING on
   the audit logger.
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


def _make_token(priv: Ed25519PrivateKey, *, extra: dict | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "lic-worker-cap",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=7)).timestamp()),
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


def _enforced_guard(
    priv: Ed25519PrivateKey, tmp_path, *, extra: dict | None = None
) -> LicenseGuard:
    lic = tmp_path / "t.lic"
    lic.write_text(_make_token(priv, extra=extra), encoding="utf-8")
    os.environ["DATA_BOAR_LICENSE_PUBLIC_KEY_PEM"] = _pem_public(priv)
    return LicenseGuard({"licensing": {"mode": "enforced", "license_path": str(lic)}})


# --- 1. open mode: never capped --------------------------------------------


def test_open_mode_no_cap():
    g = LicenseGuard({})
    assert g.worker_cap() is None


def test_open_mode_explicit_no_cap():
    g = LicenseGuard({"licensing": {"mode": "open", "effective_tier": "community"}})
    assert g.worker_cap() is None


# --- 2. enforced: dbmax_workers claim wins ----------------------------------


def test_enforced_claim_wins(ed25519_priv, tmp_path):
    g = _enforced_guard(
        ed25519_priv, tmp_path, extra={"dbtier": "enterprise", "dbmax_workers": 3}
    )
    assert g.context.state == "VALID"
    assert g.worker_cap() == 3


def test_enforced_malformed_claim_falls_back_to_tier(ed25519_priv, tmp_path):
    g = _enforced_guard(
        ed25519_priv,
        tmp_path,
        extra={"dbtier": "pro", "dbmax_workers": "not-a-number"},
    )
    assert g.context.state == "VALID"
    assert g.context.max_workers == 0  # fail-soft: malformed claim treated as absent
    assert g.worker_cap() == 5


def test_enforced_negative_claim_treated_as_absent(ed25519_priv, tmp_path):
    g = _enforced_guard(
        ed25519_priv, tmp_path, extra={"dbtier": "pro", "dbmax_workers": -4}
    )
    assert g.worker_cap() == 5


# --- 3. enforced: tier fallback defaults ------------------------------------


def test_enforced_community_default_cap(ed25519_priv, tmp_path):
    g = _enforced_guard(ed25519_priv, tmp_path, extra={"dbtier": "community"})
    assert g.worker_cap() == 2


def test_enforced_pro_default_cap(ed25519_priv, tmp_path):
    g = _enforced_guard(ed25519_priv, tmp_path, extra={"dbtier": "pro"})
    assert g.worker_cap() == 5


def test_enforced_enterprise_unlimited(ed25519_priv, tmp_path):
    g = _enforced_guard(ed25519_priv, tmp_path, extra={"dbtier": "enterprise"})
    assert g.worker_cap() is None


# --- 4. enforced fail-closed inherits Community cap; no env lift ------------


def test_enforced_unlicensed_inherits_community_cap():
    g = LicenseGuard({"licensing": {"mode": "enforced"}})
    assert g.context.state == "UNLICENSED"
    assert g.worker_cap() == 2


def test_dev_env_does_not_lift_cap(monkeypatch):
    """#719 regression applied to #551: dev env vars never lift the worker cap."""
    monkeypatch.setenv("DATA_BOAR_ENV", "development")
    monkeypatch.setenv("DEBUG", "1")
    monkeypatch.setenv("DATA_BOAR_TIER_OVERRIDE", "enterprise")
    g = LicenseGuard({"licensing": {"mode": "enforced"}})
    assert g.worker_cap() == 2


# --- 5. engine integration: start_audit clamps + audits ---------------------


def _engine(tmp_path, max_workers: int, licensing: dict | None = None):
    from core.engine import AuditEngine

    cfg: dict = {
        "targets": [],
        "scan": {"max_workers": max_workers},
        "sqlite_path": str(tmp_path / "audit.db"),
    }
    if licensing:
        cfg["licensing"] = licensing
    return AuditEngine(cfg, db_path=str(tmp_path / "audit.db"))


def test_engine_clamps_workers_in_enforced(ed25519_priv, tmp_path, caplog):
    from core.licensing.guard import get_license_guard

    lic = tmp_path / "t.lic"
    lic.write_text(
        _make_token(ed25519_priv, extra={"dbtier": "enterprise", "dbmax_workers": 2}),
        encoding="utf-8",
    )
    os.environ["DATA_BOAR_LICENSE_PUBLIC_KEY_PEM"] = _pem_public(ed25519_priv)
    licensing = {"mode": "enforced", "license_path": str(lic)}
    engine = _engine(tmp_path, max_workers=8, licensing=licensing)
    # Prime the singleton with the same config the engine will use.
    get_license_guard(engine.config)
    with caplog.at_level(logging.DEBUG, logger=AUDIT_LOGGER):
        engine.start_audit()
    assert engine._max_workers == 2
    clamps = [
        r
        for r in caplog.records
        if r.name == AUDIT_LOGGER and "workers_clamped" in r.message
    ]
    assert clamps and clamps[0].levelno == logging.WARNING
    assert "requested=8" in clamps[0].message
    assert "cap=2" in clamps[0].message


def test_engine_open_mode_never_clamps(tmp_path, caplog):
    engine = _engine(tmp_path, max_workers=16)
    with caplog.at_level(logging.DEBUG, logger=AUDIT_LOGGER):
        engine.start_audit()
    assert engine._max_workers == 16
    assert not any(
        "workers_clamped" in r.message for r in caplog.records if r.name == AUDIT_LOGGER
    )


def test_engine_cap_failure_is_fail_soft(ed25519_priv, tmp_path, monkeypatch, caplog):
    """A cap-resolution error must not abort a scan the gate already allowed."""
    from core.licensing.guard import LicenseGuard as _LG
    from core.licensing.guard import get_license_guard

    lic = tmp_path / "t.lic"
    lic.write_text(
        _make_token(ed25519_priv, extra={"dbtier": "enterprise"}), encoding="utf-8"
    )
    os.environ["DATA_BOAR_LICENSE_PUBLIC_KEY_PEM"] = _pem_public(ed25519_priv)
    licensing = {"mode": "enforced", "license_path": str(lic)}
    engine = _engine(tmp_path, max_workers=4, licensing=licensing)
    get_license_guard(engine.config)

    def _boom(self):
        raise RuntimeError("cap backend exploded")

    monkeypatch.setattr(_LG, "worker_cap", _boom)
    with caplog.at_level(logging.WARNING):
        session_id = engine.start_audit()
    assert session_id  # scan completed despite the cap failure
    assert engine._max_workers == 4  # uncapped fail-soft
    assert any("fail-soft" in r.message for r in caplog.records)
