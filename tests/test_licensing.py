"""Tests for optional commercial licensing (open by default)."""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi.testclient import TestClient

from core.licensing import LicenseBlockedError, reset_license_guard_for_tests
from core.licensing.fingerprint import compute_machine_fingerprint
from core.licensing.guard import LicenseGuard


def _pem_public(priv: Ed25519PrivateKey) -> str:
    pub = priv.public_key()
    return (
        pub.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode("ascii")
        .strip()
    )


def _make_token(
    priv: Ed25519PrivateKey,
    *,
    sub: str = "lic-test-1",
    exp_delta_days: int = 7,
    extra: dict | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
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
def _reset_guard():
    reset_license_guard_for_tests()
    yield
    reset_license_guard_for_tests()
    for k in (
        "DATA_BOAR_LICENSE_MODE",
        "DATA_BOAR_LICENSE_PATH",
        "DATA_BOAR_LICENSE_PUBLIC_KEY_PEM",
        "DATA_BOAR_LICENSE_PUBLIC_KEY_PATH",
        "DATA_BOAR_LICENSE_REVOCATION_PATH",
        "DATA_BOAR_EXPECTED_BUILD_DIGEST",
        "DATA_BOAR_RELEASE_MANIFEST_PATH",
    ):
        os.environ.pop(k, None)


def test_open_mode_allows_scan_without_files():
    cfg = {"licensing": {"mode": "open"}}
    g = LicenseGuard(cfg)
    assert g.allows_scan() is True
    assert g.context.state == "OPEN"


def test_enforced_missing_license_unlicensed(tmp_path, ed25519_priv):
    pem = _pem_public(ed25519_priv)
    cfg = {
        "licensing": {
            "mode": "enforced",
            "license_path": str(tmp_path / "missing.lic"),
        }
    }
    os.environ["DATA_BOAR_LICENSE_PUBLIC_KEY_PEM"] = pem
    g = LicenseGuard(cfg)
    assert g.allows_scan() is False
    assert g.context.state == "UNLICENSED"


def test_enforced_valid_token(ed25519_priv, tmp_path):
    pem = _pem_public(ed25519_priv)
    lic = tmp_path / "t.lic"
    lic.write_text(_make_token(ed25519_priv), encoding="utf-8")
    cfg = {"licensing": {"mode": "enforced", "license_path": str(lic)}}
    os.environ["DATA_BOAR_LICENSE_PUBLIC_KEY_PEM"] = pem
    g = LicenseGuard(cfg)
    assert g.allows_scan() is True
    assert g.context.state == "VALID"
    assert g.context.customer_name == "Test Customer"


def test_enforced_grace_when_past_exp_before_dbgrace(ed25519_priv, tmp_path):
    """#1212 — GRACE is reachable when exp < now <= dbgrace (PyJWT must not block on exp)."""
    pem = _pem_public(ed25519_priv)
    now = datetime.now(timezone.utc)
    grace_ts = int((now + timedelta(days=7)).timestamp())
    lic = tmp_path / "grace.lic"
    lic.write_text(
        _make_token(
            ed25519_priv,
            exp_delta_days=-1,
            extra={"dbgrace": grace_ts},
        ),
        encoding="utf-8",
    )
    cfg = {"licensing": {"mode": "enforced", "license_path": str(lic)}}
    os.environ["DATA_BOAR_LICENSE_PUBLIC_KEY_PEM"] = pem
    g = LicenseGuard(cfg)
    assert g.context.state == "GRACE"
    assert g.allows_scan() is True
    assert g.context.state in ("OPEN", "VALID", "GRACE")


def test_enforced_expired_when_past_dbgrace(ed25519_priv, tmp_path):
    """#1212 — past both exp and dbgrace → EXPIRED (grace boundary)."""
    pem = _pem_public(ed25519_priv)
    now = datetime.now(timezone.utc)
    past_grace = int((now - timedelta(days=1)).timestamp())
    lic = tmp_path / "expired.lic"
    lic.write_text(
        _make_token(
            ed25519_priv,
            exp_delta_days=-3,
            extra={"dbgrace": past_grace},
        ),
        encoding="utf-8",
    )
    cfg = {"licensing": {"mode": "enforced", "license_path": str(lic)}}
    os.environ["DATA_BOAR_LICENSE_PUBLIC_KEY_PEM"] = pem
    g = LicenseGuard(cfg)
    assert g.context.state == "EXPIRED"
    assert g.allows_scan() is False


def test_enforced_token_dbtier_claim_exposed(ed25519_priv, tmp_path):
    """JWT ``dbtier`` is stored for feature gates (e.g. maturity POC) — see LICENSING_SPEC.md."""
    pem = _pem_public(ed25519_priv)
    lic = tmp_path / "t.lic"
    lic.write_text(
        _make_token(ed25519_priv, extra={"dbtier": "pro"}),
        encoding="utf-8",
    )
    cfg = {"licensing": {"mode": "enforced", "license_path": str(lic)}}
    os.environ["DATA_BOAR_LICENSE_PUBLIC_KEY_PEM"] = pem
    g = LicenseGuard(cfg)
    assert g.context.state == "VALID"
    assert g.context.dbtier == "pro"
    assert g.context.to_public_dict().get("dbtier") == "pro"


def test_enforced_revoked(ed25519_priv, tmp_path):
    pem = _pem_public(ed25519_priv)
    lic = tmp_path / "t.lic"
    lic.write_text(_make_token(ed25519_priv, sub="rev-me"), encoding="utf-8")
    rev = tmp_path / "rev.json"
    rev.write_text(json.dumps({"revoked_license_ids": ["rev-me"]}), encoding="utf-8")
    cfg = {
        "licensing": {
            "mode": "enforced",
            "license_path": str(lic),
            "revocation_list_path": str(rev),
        }
    }
    os.environ["DATA_BOAR_LICENSE_PUBLIC_KEY_PEM"] = pem
    g = LicenseGuard(cfg)
    assert g.allows_scan() is False
    assert g.context.state == "REVOKED"
    assert g.context.detail == "license_revoked:sub"


def _revoked_guard(priv, tmp_path, *, token_extra: dict, revoked_ids: list[str]):
    """#717 helper: enforced guard with a token + revocation list on disk."""
    pem = _pem_public(priv)
    lic = tmp_path / "t.lic"
    lic.write_text(_make_token(priv, extra=token_extra), encoding="utf-8")
    rev = tmp_path / "rev.json"
    rev.write_text(json.dumps({"revoked_license_ids": revoked_ids}), encoding="utf-8")
    cfg = {
        "licensing": {
            "mode": "enforced",
            "license_path": str(lic),
            "revocation_list_path": str(rev),
        }
    }
    os.environ["DATA_BOAR_LICENSE_PUBLIC_KEY_PEM"] = pem
    return LicenseGuard(cfg)


def test_enforced_revoked_by_jti(ed25519_priv, tmp_path, caplog):
    """#717: a revoked token id (jti) kills the token — fail-closed + WARNING."""
    import logging

    with caplog.at_level(logging.WARNING, logger="data_boar.licensing.audit"):
        g = _revoked_guard(
            ed25519_priv,
            tmp_path,
            token_extra={"jti": "tok-123", "dbtier": "enterprise"},
            revoked_ids=["tok-123"],
        )
    assert g.allows_scan() is False
    assert g.context.state == "REVOKED"
    assert g.context.detail == "license_revoked:jti"
    # Fail-closed: REVOKED resolves to Community for feature gates.
    assert g.product_tier_for_features().value == "community"
    revoked_events = [
        r
        for r in caplog.records
        if "license_revoked" in r.message and r.levelno == logging.WARNING
    ]
    assert revoked_events, "expected a WARNING license_revoked audit event"


def test_enforced_revoked_by_kid_kills_all_tokens_of_key(ed25519_priv, tmp_path):
    """#717: revoking a signing key id (dbkid) disables every token it signed."""
    g = _revoked_guard(
        ed25519_priv,
        tmp_path,
        token_extra={"dbkid": "k-compromised"},
        revoked_ids=["k-compromised"],
    )
    assert g.allows_scan() is False
    assert g.context.state == "REVOKED"
    assert g.context.detail == "license_revoked:dbkid"
    assert g.context.key_id == "k-compromised"


def test_enforced_not_revoked_when_ids_do_not_match(ed25519_priv, tmp_path):
    """#717: an unrelated revocation entry must not block a valid license."""
    g = _revoked_guard(
        ed25519_priv,
        tmp_path,
        token_extra={"jti": "tok-ok"},
        revoked_ids=["someone-else", "other-jti", "other-kid"],
    )
    assert g.context.state == "VALID"
    assert g.allows_scan() is True


def test_enforced_machine_mismatch(ed25519_priv, tmp_path):
    pem = _pem_public(ed25519_priv)
    lic = tmp_path / "t.lic"
    lic.write_text(
        _make_token(ed25519_priv, extra={"dbmfp": "deadbeef" * 8}),
        encoding="utf-8",
    )
    cfg = {"licensing": {"mode": "enforced", "license_path": str(lic)}}
    os.environ["DATA_BOAR_LICENSE_PUBLIC_KEY_PEM"] = pem
    g = LicenseGuard(cfg)
    assert g.context.state == "MACHINE_MISMATCH"
    assert g.allows_scan() is False


def test_enforced_machine_match(ed25519_priv, tmp_path):
    mfp = compute_machine_fingerprint()
    pem = _pem_public(ed25519_priv)
    lic = tmp_path / "t.lic"
    lic.write_text(_make_token(ed25519_priv, extra={"dbmfp": mfp}), encoding="utf-8")
    cfg = {"licensing": {"mode": "enforced", "license_path": str(lic)}}
    os.environ["DATA_BOAR_LICENSE_PUBLIC_KEY_PEM"] = pem
    g = LicenseGuard(cfg)
    assert g.context.state == "VALID"


def test_engine_start_audit_raises_when_blocked(tmp_path, ed25519_priv, monkeypatch):
    from config.loader import normalize_config
    from core.engine import AuditEngine

    pem = _pem_public(ed25519_priv)
    cfg = normalize_config(
        {
            "targets": [],
            "sqlite_path": str(tmp_path / "db.sqlite"),
            "report": {"output_dir": str(tmp_path)},
            "licensing": {
                "mode": "enforced",
                "license_path": str(tmp_path / "none.lic"),
            },
        }
    )
    os.environ["DATA_BOAR_LICENSE_PUBLIC_KEY_PEM"] = pem
    reset_license_guard_for_tests()
    eng = AuditEngine(cfg, db_path=str(tmp_path / "db.sqlite"))
    with pytest.raises(LicenseBlockedError):
        eng.start_audit()


def test_api_scan_forbidden_when_blocked(tmp_path, ed25519_priv, monkeypatch):
    """POST /scan returns 403 when licensing enforcement blocks."""
    import api.routes as routes

    pem = _pem_public(ed25519_priv)
    cfg = {
        "targets": [],
        "sqlite_path": str(tmp_path / "api.db"),
        "report": {"output_dir": str(tmp_path)},
        "api": {"port": 8099, "require_api_key": False},
        "licensing": {
            "mode": "enforced",
            "license_path": str(tmp_path / "missing.lic"),
        },
    }
    p = tmp_path / "cfg.yaml"
    import yaml

    p.write_text(yaml.dump(cfg), encoding="utf-8")

    os.environ["DATA_BOAR_LICENSE_PUBLIC_KEY_PEM"] = pem
    reset_license_guard_for_tests()
    monkeypatch.setattr(routes, "_config_path", str(p))
    routes._config = None
    routes._audit_engine = None
    client = TestClient(routes.app)
    r = client.post("/scan", json={})
    assert r.status_code == 403
    assert r.json().get("detail", {}).get("error") == "license_blocked"


def test_health_includes_license(tmp_path, monkeypatch):
    import api.routes as routes

    cfg = {
        "targets": [],
        "sqlite_path": str(tmp_path / "h.db"),
        "report": {"output_dir": str(tmp_path)},
        "api": {"port": 8098, "require_api_key": False},
    }
    p = tmp_path / "c.yaml"
    import yaml

    p.write_text(yaml.dump(cfg), encoding="utf-8")
    reset_license_guard_for_tests()
    monkeypatch.setattr(routes, "_config_path", str(p))
    routes._config = None
    routes._audit_engine = None
    client = TestClient(routes.app)
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body.get("status") == "ok"
    assert "license" in body
    assert body["license"].get("license_state") == "OPEN"
