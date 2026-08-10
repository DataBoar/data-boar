"""OAuth token exchange must never disable TLS verify (Order 5 follow-up).

Target ``verify`` / ``verify_ssl: false`` may apply to the data-plane Client,
but client_credentials POSTs carry client_secret and return bearer tokens —
those must keep httpx's default certificate verification.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from connectors.dataverse_connector import _dataverse_token
from connectors.powerbi_connector import _get_access_token
from connectors.rest_connector import _build_auth


def _token_response(access_token: str = "access-token-xyz") -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = {"access_token": access_token}
    return resp


def test_rest_oauth_token_post_never_gets_verify_false() -> None:
    captured: dict = {}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured["kwargs"] = kwargs
        return _token_response()

    client = MagicMock()
    client.headers = {}
    target = {
        "verify": False,
        "verify_ssl": False,
        "auth": {
            "type": "oauth2_client",
            "token_url": "https://login.example.com/oauth/token",
            "client_id": "cid",
            "client_secret": "csecret",
        },
    }
    with patch("connectors.rest_connector.httpx") as hx:
        hx.post.side_effect = fake_post
        _build_auth(client, target)

    assert "verify" not in captured["kwargs"]
    assert captured["kwargs"].get("verify") is not False
    assert client.headers.get("Authorization") == "Bearer access-token-xyz"


def test_powerbi_token_post_never_gets_verify_false() -> None:
    captured: dict = {}

    def fake_post(url, **kwargs):
        captured["kwargs"] = kwargs
        return _token_response("pbi-token")

    target = {
        "tenant_id": "tenant",
        "client_id": "cid",
        "client_secret": "csecret",
        "verify": False,
        "verify_ssl": False,
    }
    with patch("connectors.powerbi_connector.httpx") as hx:
        hx.post.side_effect = fake_post
        token = _get_access_token(target)

    assert token == "pbi-token"
    assert "verify" not in captured["kwargs"]
    assert captured["kwargs"].get("verify") is not False


def test_dataverse_token_post_never_gets_verify_false() -> None:
    captured: dict = {}

    def fake_post(url, **kwargs):
        captured["kwargs"] = kwargs
        return _token_response("dv-token")

    target = {
        "org_url": "https://org.crm.dynamics.com",
        "tenant_id": "tenant",
        "client_id": "cid",
        "client_secret": "csecret",
        "verify": False,
        "verify_ssl": False,
    }
    with patch("connectors.dataverse_connector.httpx") as hx:
        hx.post.side_effect = fake_post
        token = _dataverse_token(target)

    assert token == "dv-token"
    assert "verify" not in captured["kwargs"]
    assert captured["kwargs"].get("verify") is not False
