"""
WebAuthn RP JSON routes (opt-in). Full browser ceremonies are manual; here we assert
404 when disabled and happy-path JSON shape when enabled with token secret.
"""

from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from core.webauthn_rp.settings import user_id_bytes, webauthn_block


@pytest.fixture
def webauthn_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
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
    from core.host_resolution import set_effective_api_listen_host

    set_effective_api_listen_host("127.0.0.1")
    # Loopback peer + Host: first-passkey bootstrap (#1553) allows registration without API key.
    client = TestClient(
        routes.app, base_url="http://127.0.0.1", client=("127.0.0.1", 50000)
    )
    yield client, routes
    set_effective_api_listen_host(None)
    routes._config_path = prev_path
    routes._config = prev_cfg
    routes._audit_engine = prev_eng
    monkeypatch.delenv("DATA_BOAR_WEBAUTHN_TOKEN_SECRET", raising=False)


def test_webauthn_disabled_returns_404(tmp_path: Path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        f"""targets: []
report:
  output_dir: {tmp_path}
sqlite_path: {tmp_path}/audit.db
api:
  port: 8088
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
    try:
        client = TestClient(routes.app)
        r = client.post("/auth/webauthn/registration/options")
        assert r.status_code == 404
    finally:
        routes._config_path = prev_path
        routes._config = prev_cfg
        routes._audit_engine = prev_eng


def test_webauthn_registration_options_returns_options_and_state(webauthn_client):
    client, _routes = webauthn_client
    r = client.post("/auth/webauthn/registration/options")
    assert r.status_code == 200
    data = r.json()
    assert "options" in data and "state" in data
    assert "challenge" in data["options"]


def test_webauthn_status_shows_registered_zero(webauthn_client):
    client, _routes = webauthn_client
    r = client.get("/auth/webauthn/status")
    assert r.status_code == 200
    data = r.json()
    assert data["enabled"] is True
    assert data["registered_credentials"] == 0
    assert data["session_authenticated"] is False


def test_webauthn_authentication_options_404_when_no_credentials(webauthn_client):
    client, _routes = webauthn_client
    r = client.post("/auth/webauthn/authentication/options")
    assert r.status_code == 404
    assert "no passkey" in r.json()["detail"].lower()


def test_webauthn_registration_options_403_when_credential_exists(webauthn_client):
    client, routes_mod = webauthn_client
    client.get("/health")
    cfg = yaml.safe_load(Path(routes_mod._config_path).read_text(encoding="utf-8"))
    wa = webauthn_block(cfg)
    assert wa is not None
    uid = user_id_bytes(wa)
    dbm = routes_mod._get_engine().db_manager
    dbm.webauthn_save_credential(
        user_id=uid,
        credential_id=b"unit-test-credential-id-32bytes!!",
        public_key=b"k" * 64,
        sign_count=0,
    )
    r = client.post("/auth/webauthn/registration/options")
    assert r.status_code == 403
    assert "already registered" in r.json()["detail"].lower()


def test_webauthn_registration_verify_rejects_bad_state(webauthn_client):
    client, _routes = webauthn_client
    r = client.post(
        "/auth/webauthn/registration/verify",
        json={"state": "not-a-valid-token", "credential": {"rawId": "abc"}},
    )
    assert r.status_code == 400
    assert "state" in r.json()["detail"].lower()


def test_webauthn_logout_returns_ok(webauthn_client):
    client, _routes = webauthn_client
    r = client.post("/auth/webauthn/logout")
    assert r.status_code == 200
    assert r.json().get("ok") is True


def test_startup_fails_when_enabled_without_secret(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.delenv("DATA_BOAR_WEBAUTHN_TOKEN_SECRET", raising=False)
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        f"""targets: []
report:
  output_dir: {tmp_path}
sqlite_path: {tmp_path}/audit.db
api:
  port: 8088
  webauthn:
    enabled: true
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
    try:
        with pytest.raises(RuntimeError, match="token secret"):
            with TestClient(routes.app):
                pass
    finally:
        routes._config_path = prev_path
        routes._config = prev_cfg
        routes._audit_engine = prev_eng
