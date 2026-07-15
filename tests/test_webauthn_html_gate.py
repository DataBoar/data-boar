"""WebAuthn HTML session gate and CSRF (Phase 1b, GitHub #86)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from core.webauthn_rp.session_cookie import COOKIE_NAME, sign_session
from core.webauthn_rp.settings import user_id_bytes, webauthn_block


@pytest.fixture
def webauthn_gate_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv(
        "DATA_BOAR_WEBAUTHN_TOKEN_SECRET", "unit-test-webauthn-secret-min-16"
    )
    cfg = tmp_path / "config.yaml"
    db = tmp_path / "audit.db"
    cfg.write_text(
        f"""targets: []
report:
  output_dir: {tmp_path}
sqlite_path: {db}
api:
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
    client = TestClient(routes.app)
    yield client, routes
    routes._config_path = prev_path
    routes._config = prev_cfg
    routes._audit_engine = prev_eng
    monkeypatch.delenv("DATA_BOAR_WEBAUTHN_TOKEN_SECRET", raising=False)


def test_gate_off_when_no_credentials_allows_dashboard(webauthn_gate_client):
    client, _routes = webauthn_gate_client
    r = client.get("/en/", follow_redirects=False)
    assert r.status_code == 200


def test_gate_on_redirects_dashboard_to_login(webauthn_gate_client):
    client, routes_mod = webauthn_gate_client
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
    r = client.get("/en/", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"].startswith("/en/login?next=")


def test_gate_on_allows_help(webauthn_gate_client):
    client, routes_mod = webauthn_gate_client
    cfg = yaml.safe_load(Path(routes_mod._config_path).read_text(encoding="utf-8"))
    wa = webauthn_block(cfg)
    uid = user_id_bytes(wa)
    dbm = routes_mod._get_engine().db_manager
    dbm.webauthn_save_credential(
        user_id=uid,
        credential_id=b"unit-test-credential-id-32bytes!!",
        public_key=b"k" * 64,
        sign_count=0,
    )
    r = client.get("/en/help")
    assert r.status_code == 200


def test_gate_on_allows_login_page(webauthn_gate_client):
    client, routes_mod = webauthn_gate_client
    cfg = yaml.safe_load(Path(routes_mod._config_path).read_text(encoding="utf-8"))
    wa = webauthn_block(cfg)
    uid = user_id_bytes(wa)
    dbm = routes_mod._get_engine().db_manager
    dbm.webauthn_save_credential(
        user_id=uid,
        credential_id=b"unit-test-credential-id-32bytes!!",
        public_key=b"k" * 64,
        sign_count=0,
    )
    r = client.get("/en/login")
    assert r.status_code == 200


def test_gate_on_session_cookie_allows_dashboard(webauthn_gate_client):
    client, routes_mod = webauthn_gate_client
    cfg = yaml.safe_load(Path(routes_mod._config_path).read_text(encoding="utf-8"))
    wa = webauthn_block(cfg)
    uid = user_id_bytes(wa)
    secret = "unit-test-webauthn-secret-min-16"
    dbm = routes_mod._get_engine().db_manager
    dbm.webauthn_save_credential(
        user_id=uid,
        credential_id=b"unit-test-credential-id-32bytes!!",
        public_key=b"k" * 64,
        sign_count=0,
    )
    cookie_val = sign_session(secret, uid)
    client.cookies.set(COOKIE_NAME, cookie_val)
    r = client.get("/en/")
    assert r.status_code == 200


def test_csrf_required_on_config_post_when_gate_on(webauthn_gate_client):
    client, routes_mod = webauthn_gate_client
    cfg = yaml.safe_load(Path(routes_mod._config_path).read_text(encoding="utf-8"))
    wa = webauthn_block(cfg)
    uid = user_id_bytes(wa)
    secret = "unit-test-webauthn-secret-min-16"
    dbm = routes_mod._get_engine().db_manager
    dbm.webauthn_save_credential(
        user_id=uid,
        credential_id=b"unit-test-credential-id-32bytes!!",
        public_key=b"k" * 64,
        sign_count=0,
    )
    cookie_val = sign_session(secret, uid)
    client.cookies.set(COOKIE_NAME, cookie_val)
    r = client.post(
        "/en/config",
        data={"yaml": "targets: []\n"},
    )
    assert r.status_code == 403


@pytest.fixture
def html_csrf_gate_off_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Default out-of-box: no WebAuthn gate — CSRF must still fail closed (#1231)."""
    monkeypatch.setenv("DATA_BOAR_HTML_CSRF_SECRET", "unit-test-html-csrf-secret")
    cfg = tmp_path / "config.yaml"
    db = tmp_path / "audit.db"
    cfg.write_text(
        f"""targets: []
report:
  output_dir: {tmp_path}
sqlite_path: {db}
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
    client = TestClient(routes.app)
    yield client, routes
    routes._config_path = prev_path
    routes._config = prev_cfg
    routes._audit_engine = prev_eng
    monkeypatch.delenv("DATA_BOAR_HTML_CSRF_SECRET", raising=False)


def test_csrf_required_on_config_post_when_gate_off(html_csrf_gate_off_client):
    client, _routes = html_csrf_gate_off_client
    r = client.post("/en/config", data={"yaml": "targets: []\n"})
    assert r.status_code == 403


def test_config_get_emits_csrf_when_gate_off(html_csrf_gate_off_client):
    client, _routes = html_csrf_gate_off_client
    r = client.get("/en/config")
    assert r.status_code == 200
    assert 'name="csrf_token"' in r.text
    assert 'value="' in r.text


def test_config_post_accepts_valid_csrf_when_gate_off(html_csrf_gate_off_client):
    import re

    client, _routes = html_csrf_gate_off_client
    page = client.get("/en/config")
    assert page.status_code == 200
    m = re.search(r'name="csrf_token"\s+value="([^"]+)"', page.text)
    assert m, "expected csrf_token hidden field on config GET"
    token = m.group(1)
    r = client.post(
        "/en/config",
        data={"yaml": "targets: []\n", "csrf_token": token},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert "/en/config?saved=1" in r.headers.get("location", "")


def test_config_post_rejects_forged_csrf_when_gate_off(html_csrf_gate_off_client):
    client, _routes = html_csrf_gate_off_client
    r = client.post(
        "/en/config",
        data={"yaml": "targets: []\n", "csrf_token": "forged.not.valid"},
        follow_redirects=False,
    )
    assert r.status_code == 403
