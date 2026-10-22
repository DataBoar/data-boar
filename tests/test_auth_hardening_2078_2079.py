"""API-key failure throttle and WebAuthn cookie origin (#2078, #2079)."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from api.auth_failure_throttle import decide_auth_attempt
from core.auth_audit import audit_logger
from core.forwarded_headers import client_host_for_auth
from core.host_resolution import assert_api_key_strength


def _request(host: str, forwarded: str | None = None):
    headers = {}
    if forwarded is not None:
        headers["x-forwarded-for"] = forwarded
    return SimpleNamespace(headers=headers, client=SimpleNamespace(host=host))


def test_forwarded_for_uses_rightmost_untrusted_hop() -> None:
    cfg = {"api": {"trusted_proxy_cidrs": ["10.0.0.0/8"]}}
    req = _request("10.1.2.3", "198.51.100.9, 203.0.113.10, 10.9.9.9")
    assert client_host_for_auth(req, cfg) == "203.0.113.10"


def test_untrusted_peer_ignores_forwarded_for() -> None:
    cfg = {"api": {"trusted_proxy_cidrs": ["10.0.0.0/8"]}}
    req = _request("203.0.113.5", "198.51.100.9")
    assert client_host_for_auth(req, cfg) == "203.0.113.5"


def test_invalid_forwarded_for_falls_back_to_peer() -> None:
    cfg = {"api": {"trusted_proxy_cidrs": ["10.0.0.0/8"]}}
    req = _request("10.1.2.3", "not-an-ip")
    assert client_host_for_auth(req, cfg) == "10.1.2.3"


def test_no_trusted_network_ignores_forwarded_for() -> None:
    req = _request("127.0.0.1", "198.51.100.9")
    assert client_host_for_auth(req, {}) == "127.0.0.1"


def test_concurrent_wrong_keys_stop_at_the_limit() -> None:
    def attempt() -> str:
        outcome, _retry = decide_auth_attempt(
            "198.51.100.20",
            5,
            60,
            provided="wrong-key",
            expected="correct-key-value-32-characters!!",
            cookie_ok=False,
        )
        return outcome

    with ThreadPoolExecutor(max_workers=10) as pool:
        outcomes = list(pool.map(lambda _i: attempt(), range(10)))
    assert outcomes.count("invalid") <= 5
    assert outcomes.count("limited") >= 5
    later, _retry = decide_auth_attempt(
        "198.51.100.20",
        5,
        60,
        provided="correct-key-value-32-characters!!",
        expected="correct-key-value-32-characters!!",
        cookie_ok=False,
    )
    assert later == "limited"


def test_concurrent_correct_keys_are_not_limited() -> None:
    expected = "correct-key-value-32-characters!!"

    def attempt() -> str:
        outcome, _retry = decide_auth_attempt(
            "198.51.100.21",
            5,
            60,
            provided=expected,
            expected=expected,
            cookie_ok=False,
        )
        return outcome

    with ThreadPoolExecutor(max_workers=10) as pool:
        outcomes = list(pool.map(lambda _i: attempt(), range(10)))
    assert outcomes == ["ok"] * 10


def test_non_ascii_credential_is_rejected() -> None:
    outcome, _retry = decide_auth_attempt(
        "198.51.100.22",
        5,
        60,
        provided="senha-\u00e7\u00e3o",
        expected="correct-key-value-32-characters!!",
        cookie_ok=False,
    )
    assert outcome == "invalid"


def test_short_yaml_key_and_short_env_key_are_refused(monkeypatch) -> None:
    with pytest.raises(ValueError, match="openssl rand -hex 32") as raised:
        assert_api_key_strength({"require_api_key": True, "api_key": "short-key"})
    assert "short-key" not in str(raised.value)
    monkeypatch.setenv("API_TEST_KEY", "short-from-env")
    with pytest.raises(ValueError, match="32"):
        assert_api_key_strength(
            {"require_api_key": True, "api_key_from_env": "API_TEST_KEY"}
        )
    monkeypatch.setenv("API_TEST_KEY", "a" * 32)
    assert_api_key_strength(
        {"require_api_key": True, "api_key_from_env": "API_TEST_KEY"}
    ) is None


def _client(tmp_path, key: str):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        f"""targets: []
report:
  output_dir: {tmp_path}
sqlite_path: {tmp_path}/audit.db
api:
  port: 8088
  require_api_key: true
  api_key: "{key}"
scan:
  max_workers: 1
""",
        encoding="utf-8",
    )
    import api.routes as routes

    saved = (routes._config_path, routes._config, routes._audit_engine)
    routes._config_path = str(cfg)
    routes._config = None
    routes._audit_engine = None
    return TestClient(routes.app), routes, saved


def test_http_failures_are_audited_without_the_key(tmp_path, caplog) -> None:
    key = "k" * 32
    client, routes, saved = _client(tmp_path, key)
    try:
        with caplog.at_level(logging.WARNING, logger=audit_logger.name):
            for _i in range(5):
                denied = client.get("/status", headers={"X-API-Key": "wrong-secret"})
                assert denied.status_code == 401
            blocked = client.get("/status", headers={"X-API-Key": key})
        assert blocked.status_code == 429
        assert blocked.headers["retry-after"]
        text = caplog.text
        assert "auth_failure" in text
        assert "wrong-secret" not in text
        assert key not in text
    finally:
        routes._config_path, routes._config, routes._audit_engine = saved


def test_non_ascii_authorization_is_401(tmp_path) -> None:
    import anyio

    key = "k" * 32
    _http, routes, saved = _client(tmp_path, key)
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/status",
        "raw_path": b"/status",
        "query_string": b"",
        "headers": [
            (b"authorization", "Bearer senha-\u00e7".encode("latin-1")),
            (b"host", b"testserver"),
        ],
        "client": ("127.0.0.1", 50000),
        "server": ("testserver", 80),
    }
    messages: list[dict] = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        messages.append(message)

    try:
        anyio.run(routes.app, scope, receive, send)
    finally:
        routes._config_path, routes._config, routes._audit_engine = saved
    assert messages[0]["status"] == 401
    assert messages[0]["status"] != 500


def test_cookie_scan_requires_dashboard_origin(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv(
        "DATA_BOAR_WEBAUTHN_TOKEN_SECRET", "unit-test-webauthn-secret-min-16"
    )
    key = "k" * 32
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        f"""targets: []
report:
  output_dir: {tmp_path}
sqlite_path: {tmp_path}/audit.db
api:
  port: 8088
  require_api_key: true
  api_key: "{key}"
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
    import yaml

    import api.routes as routes
    from core.webauthn_rp.session_cookie import COOKIE_NAME, sign_session
    from core.webauthn_rp.settings import user_id_bytes, webauthn_block

    saved = (routes._config_path, routes._config, routes._audit_engine)
    routes._config_path = str(cfg)
    routes._config = None
    routes._audit_engine = None
    client = TestClient(routes.app)
    loaded = yaml.safe_load(cfg.read_text(encoding="utf-8"))
    cookie = sign_session(
        "unit-test-webauthn-secret-min-16", user_id_bytes(webauthn_block(loaded))
    )
    client.cookies.set(COOKIE_NAME, cookie)
    try:
        missing = client.post("/scan", json={})
        assert missing.status_code == 403
        assert (
            missing.json()["detail"] == "Cookie session requires the dashboard origin"
        )
        same_site = client.post(
            "/scan", json={}, headers={"Sec-Fetch-Site": "same-origin"}
        )
        assert same_site.status_code != 403
        client.cookies.clear()
        bearer = client.post(
            "/scan", json={}, headers={"Authorization": f"Bearer {key}"}
        )
        assert bearer.status_code != 403
        client.cookies.set(COOKIE_NAME, cookie)
        allowed = client.post("/scan", json={}, headers={"Origin": "http://testserver"})
        assert allowed.status_code != 403
    finally:
        routes._config_path, routes._config, routes._audit_engine = saved
