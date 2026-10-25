"""API-key failure throttle and WebAuthn cookie origin (#2078, #2079)."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from api.auth_failure_throttle import auth_failure_limits, decide_auth_attempt
from api.webauthn_html_gate import cookie_mutation_origin_allowed
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


def test_string_trusted_proxy_cidr_is_accepted() -> None:
    cfg = {"api": {"trusted_proxy_cidrs": "10.0.0.0/8"}}
    req = _request("10.1.2.3", "198.51.100.9, 10.9.9.9")
    assert client_host_for_auth(req, cfg) == "198.51.100.9"


def test_invalid_cidr_is_skipped_and_does_not_trust_the_peer() -> None:
    cfg = {"api": {"trusted_proxy_cidrs": ["not-a-cidr", "10.0.0.0/8"]}}
    req = _request("10.1.2.3", "198.51.100.9")
    assert client_host_for_auth(req, cfg) == "198.51.100.9"
    only_junk = {"api": {"trusted_proxy_cidrs": ["not-a-cidr", ""]}}
    assert client_host_for_auth(req, only_junk) == "10.1.2.3"


def test_all_forwarded_hops_trusted_falls_back_to_peer() -> None:
    cfg = {"api": {"trusted_proxy_cidrs": ["10.0.0.0/8"]}}
    req = _request("10.1.2.3", "10.9.9.9, 10.8.8.8")
    assert client_host_for_auth(req, cfg) == "10.1.2.3"


def test_non_ip_peer_is_unknown_and_ignores_forwarded_for() -> None:
    cfg = {"api": {"trusted_proxy_cidrs": ["10.0.0.0/8"]}}
    req = _request("proxy.internal", "198.51.100.9")
    assert client_host_for_auth(req, cfg) == "unknown"


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


def test_cookie_only_is_not_limited_and_a_key_still_is() -> None:
    source = "198.51.100.30"
    expected = "correct-key-value-32-characters!!"
    for _i in range(5):
        outcome, _retry = decide_auth_attempt(
            source, 5, 60, provided="wrong", expected=expected, cookie_ok=False
        )
        assert outcome == "invalid"
    cookie_only, _retry = decide_auth_attempt(
        source, 5, 60, provided="", expected=expected, cookie_ok=True
    )
    assert cookie_only == "cookie"
    still_limited, _retry = decide_auth_attempt(
        source, 5, 60, provided=expected, expected=expected, cookie_ok=False
    )
    assert still_limited == "limited"


def test_audit_path_cannot_forge_a_field(caplog) -> None:
    from core.auth_audit import record_auth_failure

    with caplog.at_level(logging.WARNING, logger=audit_logger.name):
        record_auth_failure(
            method="GET",
            path="/scan\n source=1.2.3.4 ",
            source="127.0.0.1",
            reason="invalid_key",
        )
    message = caplog.records[-1].getMessage()
    assert "\n" not in message
    sources = [item for item in message.split() if item.startswith("source=")]
    assert sources == ["source=127.0.0.1"]
    assert "/scan" in message
    assert "invalid_key" in message


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


def test_auth_failure_limits_default_on_and_can_be_disabled() -> None:
    assert auth_failure_limits({}) == (5, 60)
    assert auth_failure_limits({"auth_failure_throttle": {"enabled": False}}) is None
    assert auth_failure_limits({"auth_failure_throttle": {"enabled": True}}) == (5, 60)


def test_auth_failure_limits_clamps_and_recovers_bad_yaml() -> None:
    assert auth_failure_limits(
        {"auth_failure_throttle": {"max_failures": 0, "window_seconds": 0}}
    ) == (1, 1)
    assert auth_failure_limits(
        {"auth_failure_throttle": {"max_failures": "nope", "window_seconds": "also"}}
    ) == (5, 60)
    assert auth_failure_limits(
        {"auth_failure_throttle": {"max_failures": 3, "window_seconds": 15}}
    ) == (3, 15)


def test_wrong_key_with_cookie_does_not_fill_the_throttle() -> None:
    source = "198.51.100.40"
    expected = "correct-key-value-32-characters!!"
    for _i in range(8):
        outcome, _retry = decide_auth_attempt(
            source, 5, 60, provided="wrong", expected=expected, cookie_ok=True
        )
        assert outcome == "cookie"
    ok, _retry = decide_auth_attempt(
        source, 5, 60, provided=expected, expected=expected, cookie_ok=False
    )
    assert ok == "ok"


def test_expired_failures_are_pruned_from_the_bucket(monkeypatch) -> None:
    source = "198.51.100.41"
    expected = "correct-key-value-32-characters!!"
    clock = {"now": 1_000.0}

    def _now() -> float:
        return clock["now"]

    monkeypatch.setattr("api.auth_failure_throttle.time.monotonic", _now)
    for _i in range(5):
        outcome, _retry = decide_auth_attempt(
            source, 5, 10, provided="wrong", expected=expected, cookie_ok=False
        )
        assert outcome == "invalid"
    limited, retry = decide_auth_attempt(
        source, 5, 10, provided=expected, expected=expected, cookie_ok=False
    )
    assert limited == "limited"
    assert retry >= 1
    clock["now"] = 1_011.0
    ok, _retry = decide_auth_attempt(
        source, 5, 10, provided=expected, expected=expected, cookie_ok=False
    )
    assert ok == "ok"


def test_cookie_mutation_origin_allows_get_and_same_origin_post() -> None:
    cfg = {"api": {"webauthn": {"enabled": True, "origin": "http://testserver"}}}
    get_req = SimpleNamespace(
        method="GET",
        headers={},
    )
    assert cookie_mutation_origin_allowed(cfg, get_req) is True
    post_missing = SimpleNamespace(method="POST", headers={})
    assert cookie_mutation_origin_allowed(cfg, post_missing) is False
    post_same = SimpleNamespace(
        method="POST", headers={"sec-fetch-site": "same-origin"}
    )
    assert cookie_mutation_origin_allowed(cfg, post_same) is True
    post_ok = SimpleNamespace(method="POST", headers={"origin": "http://testserver/"})
    assert cookie_mutation_origin_allowed(cfg, post_ok) is True
    post_sibling = SimpleNamespace(
        method="POST", headers={"origin": "http://sibling.testserver"}
    )
    assert cookie_mutation_origin_allowed(cfg, post_sibling) is False


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


def _client(tmp_path, key: str, extra_api: str = ""):
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
  {extra_api}
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


def test_disabled_throttle_does_not_return_429(tmp_path) -> None:
    key = "k" * 32
    client, routes, saved = _client(
        tmp_path, key, extra_api="auth_failure_throttle:\n    enabled: false"
    )
    try:
        for _i in range(8):
            denied = client.get("/status", headers={"X-API-Key": "wrong-secret"})
            assert denied.status_code == 401
        accepted = client.get("/status", headers={"X-API-Key": key})
        assert accepted.status_code != 429
        assert accepted.status_code != 401
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
    uid = user_id_bytes(webauthn_block(loaded))
    routes._get_engine().db_manager.webauthn_save_credential(
        user_id=uid,
        credential_id=b"unit-test-credential-id-32bytes!!",
        public_key=b"k" * 64,
        sign_count=0,
    )
    cookie = sign_session("unit-test-webauthn-secret-min-16", uid)
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
