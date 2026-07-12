from __future__ import annotations

from core.host_resolution import (
    auth_boundary_resolved,
    api_bind_exposes_non_loopback,
    resolve_api_host,
    should_block_non_loopback_without_auth,
    should_warn_insecure_api_bind,
)


def test_resolve_api_host_prefers_cli_host_when_provided() -> None:
    config = {"api": {"host": "1.2.3.4"}}
    assert resolve_api_host(config, cli_host="127.0.0.1") == "127.0.0.1"


def test_resolve_api_host_uses_config_host_when_cli_missing() -> None:
    config = {"api": {"host": "10.0.0.1"}}
    assert resolve_api_host(config, cli_host=None) == "10.0.0.1"


def test_resolve_api_host_falls_back_to_loopback_default() -> None:
    config = {"api": {}}
    assert resolve_api_host(config, cli_host=None) == "127.0.0.1"


def test_resolve_api_host_handles_missing_api_block() -> None:
    config = {}
    assert resolve_api_host(config, cli_host=None) == "127.0.0.1"


def test_resolve_api_host_uses_env_api_host_when_no_config() -> None:
    import os

    old = os.environ.get("API_HOST")
    try:
        os.environ["API_HOST"] = "0.0.0.0"
        assert resolve_api_host({}, cli_host=None) == "0.0.0.0"
    finally:
        if old is None:
            os.environ.pop("API_HOST", None)
        else:
            os.environ["API_HOST"] = old


def test_api_bind_exposes_non_loopback() -> None:
    assert api_bind_exposes_non_loopback("0.0.0.0") is True
    assert api_bind_exposes_non_loopback("10.0.1.1") is True
    assert api_bind_exposes_non_loopback("127.0.0.1") is False
    assert api_bind_exposes_non_loopback("localhost") is False


def test_should_warn_insecure_api_bind() -> None:
    cfg_open = {"api": {"require_api_key": False}}
    assert should_warn_insecure_api_bind(cfg_open, "0.0.0.0") is True
    assert should_warn_insecure_api_bind(cfg_open, "127.0.0.1") is False
    cfg_key = {
        "api": {"require_api_key": True, "api_key": "secret"},
    }
    assert should_warn_insecure_api_bind(cfg_key, "0.0.0.0") is False
    cfg_require_no_key = {"api": {"require_api_key": True, "api_key": ""}}
    assert should_warn_insecure_api_bind(cfg_require_no_key, "0.0.0.0") is True


def test_should_warn_insecure_api_bind_false_when_key_from_env(
    monkeypatch,
) -> None:
    monkeypatch.setenv("AUDIT_API_KEY", "x")
    cfg = {
        "api": {
            "require_api_key": True,
            "api_key": "",
            "api_key_from_env": "AUDIT_API_KEY",
        }
    }
    assert should_warn_insecure_api_bind(cfg, "0.0.0.0") is False


def test_auth_boundary_resolved_with_api_key() -> None:
    cfg = {"api": {"api_key": "secret"}}
    assert auth_boundary_resolved(cfg) is True


def test_auth_boundary_resolved_with_webauthn_secret(monkeypatch) -> None:
    monkeypatch.setenv("DATA_BOAR_WEBAUTHN_TOKEN_SECRET", "secret-min-16")
    cfg = {
        "api": {
            "webauthn": {
                "enabled": True,
                "token_secret_from_env": "DATA_BOAR_WEBAUTHN_TOKEN_SECRET",
            }
        }
    }
    assert auth_boundary_resolved(cfg) is True


def test_should_block_non_loopback_without_auth() -> None:
    cfg = {"api": {"require_api_key": False}}
    assert should_block_non_loopback_without_auth(cfg, "0.0.0.0") is True
    assert should_block_non_loopback_without_auth(cfg, "127.0.0.1") is False
