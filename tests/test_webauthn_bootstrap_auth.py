"""WebAuthn first-passkey bootstrap auth (#1553) — first registration always needs API key."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

import api.webauthn_routes as wa_routes


@pytest.fixture
def bootstrap_app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv(
        "DATA_BOAR_WEBAUTHN_TOKEN_SECRET", "unit-test-webauthn-secret-min-16"
    )
    monkeypatch.delenv("API_HOST", raising=False)
    cfg = tmp_path / "config.yaml"
    db = tmp_path / "audit.db"
    cfg.write_text(
        f"""targets: []
report:
  output_dir: {tmp_path}
sqlite_path: {db}
api:
  host: 127.0.0.1
  port: 8088
  api_key: bootstrap-secret-key
  webauthn:
    enabled: true
    rp_id: localhost
    rp_name: Data Boar Test
    origin: http://testserver
    user_display_name: tester
scan:
  max_workers: 1
""",
        encoding="utf-8",
    )
    import api.routes as routes

    prev_path = routes._config_path
    prev_cfg = routes._config
    prev_eng = routes._audit_engine
    routes._config_path = str(cfg)
    routes._config = None
    routes._audit_engine = None
    yield routes, cfg
    routes._config_path = prev_path
    routes._config = prev_cfg
    routes._audit_engine = prev_eng
    monkeypatch.delenv("DATA_BOAR_WEBAUTHN_TOKEN_SECRET", raising=False)


def _client(routes_mod, peer: str = "127.0.0.1") -> TestClient:
    return TestClient(routes_mod.app, client=(peer, 54321))


def test_bootstrap_options_without_key_returns_401_even_on_loopback(bootstrap_app):
    # regression-anchor: #1553 — no key-free exemption (proxy can forge loopback).
    routes_mod, _cfg = bootstrap_app
    client = _client(routes_mod, "127.0.0.1")
    r = client.post("/auth/webauthn/registration/options")
    assert r.status_code == 401
    assert "#1553" in r.json()["detail"]


def test_bootstrap_options_without_configured_key_returns_503(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    # regression-anchor: #1553 — first registration needs a configured API key.
    monkeypatch.setenv(
        "DATA_BOAR_WEBAUTHN_TOKEN_SECRET", "unit-test-webauthn-secret-min-16"
    )
    monkeypatch.delenv("API_HOST", raising=False)
    cfg = tmp_path / "config.yaml"
    db = tmp_path / "audit.db"
    cfg.write_text(
        f"""targets: []
report:
  output_dir: {tmp_path}
sqlite_path: {db}
api:
  host: 127.0.0.1
  port: 8088
  webauthn:
    enabled: true
    rp_id: localhost
    origin: http://testserver
scan:
  max_workers: 1
""",
        encoding="utf-8",
    )
    import api.routes as routes

    prev_path, prev_cfg, prev_eng = (
        routes._config_path,
        routes._config,
        routes._audit_engine,
    )
    routes._config_path = str(cfg)
    routes._config = None
    routes._audit_engine = None
    try:
        client = TestClient(routes.app, client=("127.0.0.1", 54321))
        r = client.post("/auth/webauthn/registration/options")
        assert r.status_code == 503
        assert "#1553" in r.json()["detail"]
    finally:
        routes._config_path = prev_path
        routes._config = prev_cfg
        routes._audit_engine = prev_eng
        monkeypatch.delenv("DATA_BOAR_WEBAUTHN_TOKEN_SECRET", raising=False)


def test_bootstrap_options_with_valid_key_succeeds(bootstrap_app):
    # regression-anchor: #1553 — correct API key unlocks first registration.
    routes_mod, _cfg = bootstrap_app
    client = _client(routes_mod, "10.0.0.55")
    r = client.post(
        "/auth/webauthn/registration/options",
        headers={"X-API-Key": "bootstrap-secret-key"},
    )
    assert r.status_code == 200
    body = r.json()
    assert "options" in body and "state" in body


def test_bootstrap_options_accepts_bearer_key(bootstrap_app):
    routes_mod, _cfg = bootstrap_app
    client = _client(routes_mod, "127.0.0.1")
    # Build header without a contiguous "Bearer <20+ token>" literal (PII guard).
    r = client.post(
        "/auth/webauthn/registration/options",
        headers={"Authorization": "Bearer " + "bootstrap-secret-key"},
    )
    assert r.status_code == 200


def test_registration_verify_toctou_rejects_when_credential_appears(bootstrap_app):
    # regression-anchor: #1553 — re-check count==0 before save.
    routes_mod, _cfg = bootstrap_app
    client = _client(routes_mod, "127.0.0.1")
    opts = client.post(
        "/auth/webauthn/registration/options",
        headers={"X-API-Key": "bootstrap-secret-key"},
    )
    assert opts.status_code == 200
    state = opts.json()["state"]

    fake_verified = MagicMock()
    fake_verified.credential_id = b"cred-id-toctou-test-32bytes!!!!"
    fake_verified.credential_public_key = b"k" * 64
    fake_verified.sign_count = 0
    after_crypto = {"done": False}

    def fake_verify(*_a, **_k):
        after_crypto["done"] = True
        return fake_verified

    def fake_count() -> int:
        return 1 if after_crypto["done"] else 0

    with patch.object(
        wa_routes, "verify_registration_response", side_effect=fake_verify
    ):
        with patch.object(
            routes_mod._get_engine().db_manager,
            "webauthn_credential_count",
            side_effect=fake_count,
        ):
            r = client.post(
                "/auth/webauthn/registration/verify",
                headers={"X-API-Key": "bootstrap-secret-key"},
                json={
                    "state": state,
                    "credential": {
                        "id": "x",
                        "rawId": "x",
                        "type": "public-key",
                        "response": {},
                    },
                },
            )
    assert r.status_code == 403
    assert "already registered" in r.json()["detail"].lower()


def test_authentication_options_not_gated_by_bootstrap_key(bootstrap_app):
    # regression-anchor: #1553 — auth ceremony stays public (no bootstrap key gate).
    routes_mod, _cfg = bootstrap_app
    client = _client(routes_mod, "10.0.0.55")
    r = client.post("/auth/webauthn/authentication/options")
    assert r.status_code == 404
    assert "no passkey" in r.json()["detail"].lower()
