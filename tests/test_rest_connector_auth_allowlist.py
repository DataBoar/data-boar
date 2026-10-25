"""REST connector credential host allowlist (#1977, pattern from HubSpot #1607)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from connectors.rest_connector import (
    RESTConnector,
    _assert_rest_credential_hosts_allowlisted,
    _build_auth,
    _host_from_url,
)


def _target_exfil_bearer() -> dict:
    return {
        "base_url": "https://attacker.example",
        "auth": {
            "type": "bearer",
            "token_from_env": "API_TOKEN",
            "allowed_hosts": ["api.trusted.example"],
        },
    }


def test_bearer_rejects_non_allowlisted_base_before_authorization_header() -> None:
    client = MagicMock()
    client.headers = {}
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setenv("API_TOKEN", "stolen-secret-value")
    try:
        with pytest.raises(ValueError, match="#1977"):
            _build_auth(client, _target_exfil_bearer())
    finally:
        monkeypatch.delenv("API_TOKEN", raising=False)
    assert "Authorization" not in client.headers


def test_bearer_token_from_env_requires_explicit_allowed_hosts() -> None:
    client = MagicMock()
    client.headers = {}
    target = {
        "base_url": "https://api.trusted.example",
        "auth": {"type": "bearer", "token_from_env": "API_TOKEN"},
    }
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("API_TOKEN", "tok")
        with pytest.raises(ValueError, match="allowed_hosts.*#1977"):
            _build_auth(client, target)
    assert "Authorization" not in client.headers


def test_bearer_token_from_env_rejects_disallowed_env_name_prefix() -> None:
    client = MagicMock()
    client.headers = {}
    target = {
        "base_url": "https://api.trusted.example",
        "auth": {
            "type": "bearer",
            "token_from_env": "AWS_SECRET_ACCESS_KEY",
            "allowed_hosts": ["api.trusted.example"],
        },
    }
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("AWS_SECRET_ACCESS_KEY", "leak")
        with pytest.raises(ValueError, match="token_from_env.*#1977"):
            _build_auth(client, target)
    assert "Authorization" not in client.headers


def test_oauth2_client_secret_post_blocked_for_non_allowlisted_token_host() -> None:
    client = MagicMock()
    client.headers = {}
    target = {
        "base_url": "https://api.trusted.example",
        "auth": {
            "type": "oauth2_client",
            "token_url": "https://attacker.example/oauth/token",
            "client_id": "cid",
            "client_secret": "csecret",
            "allowed_hosts": ["api.trusted.example"],
        },
    }
    with patch("connectors.rest_connector.pinned_httpx_request") as mock_post:
        with pytest.raises(ValueError, match="#1977"):
            _build_auth(client, target)
        mock_post.assert_not_called()
    assert "Authorization" not in client.headers


def test_inline_bearer_allows_implicit_host_from_base_url() -> None:
    client = MagicMock()
    client.headers = {}
    target = {
        "base_url": "https://api.trusted.example",
        "auth": {"type": "bearer", "token": "inline-token"},
    }
    _build_auth(client, target)
    assert client.headers.get("Authorization") == "Bearer inline-token"


@patch("connectors.rest_connector.build_pinned_httpx_client")
@patch("connectors.rest_connector.resolve_and_validate_outbound_url")
def test_connect_rejects_exfil_target_before_pinned_client(
    mock_resolve, mock_client_cls
) -> None:
    """Connect must fail before httpx client when bearer would exfiltrate (#1977)."""
    cfg = {
        "name": "evil",
        "base_url": "https://attacker.example",
        "paths": ["/x"],
        "auth": {
            "type": "bearer",
            "token": "secret",
            "allowed_hosts": ["api.good.example"],
        },
    }
    conn = RESTConnector(cfg, scanner=None, db_manager=MagicMock())
    with pytest.raises(ValueError, match="#1977"):
        conn.connect()
    mock_client_cls.assert_not_called()


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://API.Trusted.Example:8443/v1", "api.trusted.example"),
        ("https://user:pass@api.trusted.example/oauth/token", "api.trusted.example"),
        ("https://[2001:db8::1]/token", "2001:db8::1"),
    ],
)
def test_host_from_url_normalizes_credential_endpoints(url: str, expected: str) -> None:
    """Allowlist compare is hostname-only; userinfo and port must not widen the match (#1977)."""
    assert _host_from_url(url) == expected


@pytest.mark.parametrize(
    "url",
    ["", "   ", "not-a-url", "/relative", "https:///nohost"],
)
def test_host_from_url_rejects_unusable_urls(url: str) -> None:
    with pytest.raises(ValueError, match="#1977"):
        _host_from_url(url)


def test_oauth2_interpolated_client_secret_requires_explicit_allowed_hosts() -> None:
    """${ENV} client_secret is env-loaded; implicit token_url host must not allowlist (#1977)."""
    client = MagicMock()
    client.headers = {}
    target = {
        "base_url": "https://api.trusted.example",
        "auth": {
            "type": "oauth2_client",
            "token_url": "https://attacker.example/oauth/token",
            "client_id": "cid",
            "client_secret": "${API_CLIENT_SECRET}",
        },
    }
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("API_CLIENT_SECRET", "stolen-client-secret")
        with patch("connectors.rest_connector.pinned_httpx_request") as mock_post:
            with pytest.raises(ValueError, match="allowed_hosts.*#1977"):
                _build_auth(client, target)
            mock_post.assert_not_called()
    assert "Authorization" not in client.headers


def test_oauth2_interpolated_client_secret_rejects_non_allowlisted_token_host() -> None:
    client = MagicMock()
    client.headers = {}
    target = {
        "base_url": "https://api.trusted.example",
        "auth": {
            "type": "oauth2_client",
            "token_url": "https://attacker.example/oauth/token",
            "client_id": "cid",
            "client_secret": "${API_CLIENT_SECRET}",
            "allowed_hosts": ["api.trusted.example"],
        },
    }
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("API_CLIENT_SECRET", "stolen-client-secret")
        with patch("connectors.rest_connector.pinned_httpx_request") as mock_post:
            with pytest.raises(ValueError, match="token_url host.*#1977"):
                _build_auth(client, target)
            mock_post.assert_not_called()
    assert "Authorization" not in client.headers


def test_oauth2_client_secret_from_env_rejects_disallowed_env_name_prefix() -> None:
    """client_secret_from_env is counted as env-loaded even when oauth still uses client_secret."""
    target = {
        "base_url": "https://api.trusted.example",
        "auth": {
            "type": "oauth2_client",
            "token_url": "https://api.trusted.example/oauth/token",
            "client_id": "cid",
            "client_secret": "inline-secret",
            "client_secret_from_env": "AWS_SECRET_ACCESS_KEY",
            "allowed_hosts": ["api.trusted.example"],
        },
    }
    with pytest.raises(ValueError, match="client_secret_from_env.*#1977"):
        _assert_rest_credential_hosts_allowlisted(target)


def test_allowed_hosts_string_is_equivalent_to_a_one_item_list() -> None:
    target = {
        "base_url": "https://api.trusted.example",
        "auth": {
            "type": "bearer",
            "token": "inline-token",
            "allowed_hosts": "API.Trusted.Example",
        },
    }
    _assert_rest_credential_hosts_allowlisted(target)


def test_custom_authorization_header_requires_explicit_or_matching_allowlist() -> None:
    client = MagicMock()
    client.headers = {}
    target = {
        "base_url": "https://attacker.example",
        "auth": {
            "type": "custom",
            "headers": {"Authorization": "Bearer stolen"},
            "allowed_hosts": ["api.trusted.example"],
        },
    }
    with pytest.raises(ValueError, match="#1977"):
        _build_auth(client, target)
    assert "Authorization" not in client.headers


def test_custom_x_api_key_header_is_treated_as_a_credential() -> None:
    client = MagicMock()
    client.headers = {}
    target = {
        "auth": {
            "type": "custom",
            "headers": {"X-API-Key": "k"},
        },
    }
    with pytest.raises(ValueError, match="allowed_hosts.*#1977"):
        _build_auth(client, target)
    assert "X-API-Key" not in client.headers

    target["base_url"] = "https://api.trusted.example"
    _build_auth(client, target)
    assert client.headers.get("X-API-Key") == "k"


def test_custom_non_credential_headers_skip_host_allowlist() -> None:
    client = MagicMock()
    client.headers = {}
    target = {
        "base_url": "https://attacker.example",
        "auth": {
            "type": "custom",
            "headers": {"Accept": "application/json"},
        },
    }
    _build_auth(client, target)
    assert client.headers.get("Accept") == "application/json"
