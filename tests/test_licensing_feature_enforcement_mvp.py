"""JWT tier enforcement at Pro/Enterprise feature call sites (#699 MVP)."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi.testclient import TestClient

from app.grc_dashboard_model import load_grc_json
from core.licensing.errors import FeatureTierBlockedError
from core.licensing.guard import reset_license_guard_for_tests
from report.grc_export_multiformat import export_grc_executive_pdf

_REPO = Path(__file__).resolve().parents[1]
_GRC_EXAMPLE = _REPO / "schemas" / "grc_executive_report.v1.example.json"


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


def _make_token(priv: Ed25519PrivateKey, *, dbtier: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "mvp-tier-enforcement",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=7)).timestamp()),
        "dbcid": "cust-test",
        "dbcname": "Tier Test",
        "dbenv": "qa",
        "dbissuer": "pytest",
        "dbkid": "k1",
        "dbtier": dbtier,
    }
    return jwt.encode(payload, priv, algorithm="EdDSA")


@pytest.fixture
def ed25519_priv() -> Ed25519PrivateKey:
    return Ed25519PrivateKey.generate()


@pytest.fixture(autouse=True)
def _clean_license_env():
    reset_license_guard_for_tests()
    keys = (
        "DATA_BOAR_LICENSE_PUBLIC_KEY_PEM",
        "DATA_BOAR_LICENSE_PUBLIC_KEY_PATH",
        "DATA_BOAR_LICENSE_PATH",
        "DATA_BOAR_LICENSE_MODE",
    )
    saved = {k: os.environ.get(k) for k in keys}
    yield
    reset_license_guard_for_tests()
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


def _enforced_community_cfg(tmp_path: Path, priv: Ed25519PrivateKey) -> dict:
    lic = tmp_path / "community.lic"
    lic.write_text(_make_token(priv, dbtier="community"), encoding="utf-8")
    return {
        "targets": [],
        "sqlite_path": str(tmp_path / "audit.db"),
        "report": {"output_dir": str(tmp_path)},
        "api": {"port": 8099, "require_api_key": False},
        "licensing": {
            "mode": "enforced",
            "license_path": str(lic),
        },
    }


def _setup_routes(tmp_path: Path, cfg: dict, monkeypatch: pytest.MonkeyPatch):
    import yaml

    import api.routes as routes

    p = tmp_path / "cfg.yaml"
    p.write_text(yaml.dump(cfg), encoding="utf-8")
    reset_license_guard_for_tests()
    monkeypatch.setattr(routes, "_config_path", str(p))
    routes._config = None
    routes._audit_engine = None
    return routes, TestClient(routes.app)


def test_report_pdf_blocked_for_community_tier(
    tmp_path: Path, ed25519_priv: Ed25519PrivateKey, monkeypatch: pytest.MonkeyPatch
):
    os.environ["DATA_BOAR_LICENSE_PUBLIC_KEY_PEM"] = _pem_public(ed25519_priv)
    cfg = _enforced_community_cfg(tmp_path, ed25519_priv)
    data = load_grc_json(_GRC_EXAMPLE)
    pdf = tmp_path / "out.pdf"
    with pytest.raises(FeatureTierBlockedError) as exc_info:
        export_grc_executive_pdf(data, pdf, config=cfg)
    assert exc_info.value.feature == "report_pdf"
    assert not pdf.exists()


def test_scheduled_scans_blocked_for_community_tier_api(
    tmp_path: Path, ed25519_priv: Ed25519PrivateKey, monkeypatch: pytest.MonkeyPatch
):
    os.environ["DATA_BOAR_LICENSE_PUBLIC_KEY_PEM"] = _pem_public(ed25519_priv)
    cfg = _enforced_community_cfg(tmp_path, ed25519_priv)
    routes, client = _setup_routes(tmp_path, cfg, monkeypatch)
    try:
        r = client.post("/scan", json={"scheduled": True})
        assert r.status_code == 403
        detail = r.json().get("detail", {})
        assert detail.get("error") == "feature_tier_blocked"
        assert detail.get("feature") == "scheduled_scans"
    finally:
        routes._audit_engine = None
        routes._config = None


def test_snowflake_scan_database_blocked_for_community_tier_api(
    tmp_path: Path, ed25519_priv: Ed25519PrivateKey, monkeypatch: pytest.MonkeyPatch
):
    os.environ["DATA_BOAR_LICENSE_PUBLIC_KEY_PEM"] = _pem_public(ed25519_priv)
    cfg = _enforced_community_cfg(tmp_path, ed25519_priv)
    routes, client = _setup_routes(tmp_path, cfg, monkeypatch)
    try:
        r = client.post(
            "/scan_database",
            json={
                "name": "sf-lab",
                "host": "example.snowflakecomputing.com",
                "port": 443,
                "user": "user",
                "password": "secret",
                "database": "DB",
                "driver": "snowflake",
            },
        )
        assert r.status_code == 403
        detail = r.json().get("detail", {})
        assert detail.get("error") == "feature_tier_blocked"
        assert detail.get("feature") == "connector_snowflake"
    finally:
        routes._audit_engine = None
        routes._config = None


def test_community_tier_manual_scan_still_allowed(
    tmp_path: Path, ed25519_priv: Ed25519PrivateKey, monkeypatch: pytest.MonkeyPatch
):
    """Regression: community JWT must not block a normal (non-scheduled) scan start."""
    os.environ["DATA_BOAR_LICENSE_PUBLIC_KEY_PEM"] = _pem_public(ed25519_priv)
    cfg = _enforced_community_cfg(tmp_path, ed25519_priv)
    routes, client = _setup_routes(tmp_path, cfg, monkeypatch)
    try:
        r = client.post("/scan", json={})
        assert r.status_code == 200
        assert r.json().get("session_id")
    finally:
        routes._audit_engine = None
        routes._config = None
