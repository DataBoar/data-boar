"""HubSpot CRM connector tests (#1229): schema discovery, pagination, custom-field PII, url_guard."""

from __future__ import annotations

import ipaddress
import os
from unittest.mock import MagicMock, patch

import httpx
import pytest

from connectors.hubspot_connector import (
    _DEFAULT_TOKEN_ENV,
    _HTTPX_AVAILABLE,
    HubSpotConnector,
    normalize_hubspot_api_base_url,
)
from tests.fixtures.hubspot.synthetic_crm import (
    SYNTHETIC_CPF_FORMATTED,
    contact_schema_and_pages,
    objects_page,
    properties_response,
    synthetic_contact_properties,
)

pytestmark = pytest.mark.skipif(not _HTTPX_AVAILABLE, reason="httpx not installed")


def _mk_scanner_passthrough():
    """Use real DataScanner so CPF in custom field is actually detected."""
    from core.scanner import DataScanner

    return DataScanner()


def _mk_scanner_mock(level: str = "HIGH", pattern: str = "CPF"):
    scanner = MagicMock()
    scanner.scan_column.return_value = {
        "sensitivity_level": level,
        "pattern_detected": pattern,
        "norm_tag": "CPF",
        "ml_confidence": 0.9,
    }
    return scanner


def _cfg(**overrides):
    cfg = {
        "name": "crm-hubspot",
        "type": "hubspot",
        "objects": ["contacts"],
        "base_url": "https://api.hubapi.com",
    }
    cfg.update(overrides)
    return cfg


@pytest.fixture
def hubspot_token(monkeypatch):
    monkeypatch.setenv(_DEFAULT_TOKEN_ENV, "pat-synthetic-test-token-not-real")
    yield
    monkeypatch.delenv(_DEFAULT_TOKEN_ENV, raising=False)


def _json_response(
    payload: dict, url: str = "https://api.hubapi.com/"
) -> httpx.Response:
    req = httpx.Request("GET", url)
    return httpx.Response(200, json=payload, request=req)


@patch("connectors.hubspot_connector.time.sleep", return_value=None)
@patch("connectors.hubspot_connector.build_pinned_httpx_client")
@patch("connectors.hubspot_connector.resolve_and_validate_outbound_url")
def test_property_discovery_includes_custom_fields(
    mock_resolve, mock_client_cls, _sleep, hubspot_token
):
    mock_resolve.return_value = (None, [ipaddress.ip_address("104.16.0.1")])
    client = MagicMock()
    mock_client_cls.return_value = client

    schema = properties_response("email", "cpf_custom")
    page = objects_page([synthetic_contact_properties()])

    def _get(url, *args, **kwargs):
        path = str(url)
        if "/crm/v3/properties/" in path:
            return _json_response(schema, path)
        if "/crm/v3/objects/" in path:
            return _json_response(page, path)
        raise AssertionError(f"unexpected GET {path}")

    client.get.side_effect = _get

    dbm = MagicMock()
    HubSpotConnector(_cfg(), _mk_scanner_mock(), dbm).run()

    prop_calls = [
        c.args[0]
        for c in client.get.call_args_list
        if "/crm/v3/properties/contacts" in str(c.args[0])
    ]
    assert prop_calls, "must discover properties before objects"
    obj_calls = [
        c.args[0]
        for c in client.get.call_args_list
        if "/crm/v3/objects/contacts" in str(c.args[0])
    ]
    assert obj_calls, "must fetch objects after property discovery"
    assert "cpf_custom" in str(obj_calls[0]) or "properties=" in str(obj_calls[0])


@patch("connectors.hubspot_connector.time.sleep", return_value=None)
@patch("connectors.hubspot_connector.build_pinned_httpx_client")
@patch("connectors.hubspot_connector.resolve_and_validate_outbound_url")
def test_pagination_follows_after_cursor(
    mock_resolve, mock_client_cls, _sleep, hubspot_token
):
    mock_resolve.return_value = (None, [ipaddress.ip_address("104.16.0.1")])
    client = MagicMock()
    mock_client_cls.return_value = client
    schema, pages = contact_schema_and_pages()
    object_hits = {"n": 0}

    def _get(url, *args, **kwargs):
        path = str(url)
        if "/crm/v3/properties/" in path:
            return _json_response(schema, path)
        if "/crm/v3/objects/" in path:
            idx = object_hits["n"]
            object_hits["n"] += 1
            return _json_response(pages[idx], path)
        raise AssertionError(f"unexpected GET {path}")

    client.get.side_effect = _get
    dbm = MagicMock()
    HubSpotConnector(_cfg(), _mk_scanner_mock(level="LOW", pattern=""), dbm).run()
    assert object_hits["n"] == 2
    second = str(client.get.call_args_list[-1].args[0])
    assert "after=cursor-page-2" in second


@patch("connectors.hubspot_connector.time.sleep", return_value=None)
@patch("connectors.hubspot_connector.build_pinned_httpx_client")
@patch("connectors.hubspot_connector.resolve_and_validate_outbound_url")
def test_detects_pii_in_custom_field(
    mock_resolve, mock_client_cls, _sleep, hubspot_token
):
    mock_resolve.return_value = (None, [ipaddress.ip_address("104.16.0.1")])
    client = MagicMock()
    mock_client_cls.return_value = client
    schema = properties_response("email", "cpf_custom")
    page = objects_page([synthetic_contact_properties()])

    def _get(url, *args, **kwargs):
        path = str(url)
        if "/crm/v3/properties/" in path:
            return _json_response(schema, path)
        return _json_response(page, path)

    client.get.side_effect = _get
    dbm = MagicMock()
    HubSpotConnector(_cfg(), _mk_scanner_passthrough(), dbm).run()

    assert dbm.save_finding.called
    file_names = [c.kwargs.get("file_name") for c in dbm.save_finding.call_args_list]
    assert "cpf_custom" in file_names, (
        f"custom CPF field must produce a finding; got {file_names}"
    )
    paths = [c.kwargs.get("path") for c in dbm.save_finding.call_args_list]
    assert "contacts" in paths
    cpf_calls = [
        c
        for c in dbm.save_finding.call_args_list
        if c.kwargs.get("file_name") == "cpf_custom"
    ]
    assert cpf_calls
    assert cpf_calls[0].kwargs.get("sensitivity_level") in ("HIGH", "MEDIUM")
    assert SYNTHETIC_CPF_FORMATTED in synthetic_contact_properties()["cpf_custom"]


@patch("connectors.hubspot_connector.time.sleep", return_value=None)
@patch("connectors.hubspot_connector.build_pinned_httpx_client")
@patch("connectors.hubspot_connector.resolve_and_validate_outbound_url")
def test_uses_url_guard_not_raw_httpx(
    mock_resolve, mock_client_cls, _sleep, hubspot_token
):
    mock_resolve.return_value = (None, [ipaddress.ip_address("104.16.0.1")])
    client = MagicMock()
    mock_client_cls.return_value = client
    client.get.return_value = _json_response(properties_response("email"))

    # Empty objects after schema so run completes
    calls = {"n": 0}

    def _get(url, *args, **kwargs):
        calls["n"] += 1
        path = str(url)
        if "/properties/" in path:
            return _json_response(properties_response("email"), path)
        return _json_response(objects_page([]), path)

    client.get.side_effect = _get
    HubSpotConnector(_cfg(), _mk_scanner_mock(level="LOW"), MagicMock()).run()

    mock_resolve.assert_called()
    assert mock_resolve.call_args.kwargs.get("label") == "base_url" or (
        len(mock_resolve.call_args.args) >= 1
    )
    mock_client_cls.assert_called_once()
    # Must never construct a bare httpx.Client in the connector module path
    assert "host_to_ips" in mock_client_cls.call_args.kwargs


def test_connect_rejects_private_base_url_without_opt_in(hubspot_token):
    # Private literal IP fails host allowlist (#1607) before SSRF private-IP path.
    cfg = _cfg(base_url="http://10.0.0.5")
    with pytest.raises(ValueError, match="#1607|#832|private|blocked|base_url|https"):
        HubSpotConnector(cfg, _mk_scanner_mock(), MagicMock()).connect()


def test_normalize_hubspot_api_base_url_defaults_and_regionals():
    assert normalize_hubspot_api_base_url(None) == "https://api.hubapi.com"
    assert normalize_hubspot_api_base_url("") == "https://api.hubapi.com"
    assert (
        normalize_hubspot_api_base_url("https://api.hubapi.com/")
        == "https://api.hubapi.com"
    )
    assert (
        normalize_hubspot_api_base_url("https://API-EU1.hubapi.com")
        == "https://api-eu1.hubapi.com"
    )
    assert (
        normalize_hubspot_api_base_url("https://api-na2.hubapi.com")
        == "https://api-na2.hubapi.com"
    )


def test_normalize_hubspot_api_base_url_rejects_token_exfil_hosts():
    """#1607: free-form public hosts must not receive the Private App Bearer."""
    for bad in (
        "https://evil.example",
        "https://api.hubapi.com.evil.example",
        "https://not-hubapi.com",
        "http://api.hubapi.com",
        "https://user:pass@api.hubapi.com",
        "https://api.hubapi.com:8443",
        "https://api.hubapi.com/crm",
        "https://api.hubapi.com?x=1",
        "https://api_hubapi.com",
    ):
        with pytest.raises(ValueError, match="#1607"):
            normalize_hubspot_api_base_url(bad)


@patch("connectors.hubspot_connector.build_pinned_httpx_client")
@patch("connectors.hubspot_connector.resolve_and_validate_outbound_url")
def test_connect_rejects_public_non_hubspot_host_before_client(
    mock_resolve, mock_client_cls, hubspot_token
):
    """Bearer must never be attached for a non-allowlisted public base_url (#1607)."""
    cfg = _cfg(base_url="https://attacker.example")
    with pytest.raises(ValueError, match="#1607"):
        HubSpotConnector(cfg, _mk_scanner_mock(), MagicMock()).connect()
    mock_resolve.assert_not_called()
    mock_client_cls.assert_not_called()


def test_connect_requires_token_env():
    os.environ.pop(_DEFAULT_TOKEN_ENV, None)
    with pytest.raises(ValueError, match="HUBSPOT_PRIVATE_APP_TOKEN|Private App"):
        HubSpotConnector(_cfg(), _mk_scanner_mock(), MagicMock()).connect()


@patch("connectors.hubspot_connector.time.sleep")
@patch("connectors.hubspot_connector.build_pinned_httpx_client")
@patch("connectors.hubspot_connector.resolve_and_validate_outbound_url")
def test_rate_limit_429_retries(
    mock_resolve, mock_client_cls, mock_sleep, hubspot_token
):
    mock_resolve.return_value = (None, [ipaddress.ip_address("104.16.0.1")])
    client = MagicMock()
    mock_client_cls.return_value = client
    req = httpx.Request("GET", "https://api.hubapi.com/crm/v3/properties/contacts")
    limited = httpx.Response(429, headers={"Retry-After": "1"}, request=req)
    ok = _json_response(properties_response("email"), str(req.url))
    empty = _json_response(objects_page([]))
    seq = {"i": 0}

    def _get(url, *args, **kwargs):
        path = str(url)
        if "/properties/" in path:
            if seq["i"] == 0:
                seq["i"] += 1
                return limited
            return ok
        return empty

    client.get.side_effect = _get
    HubSpotConnector(_cfg(), _mk_scanner_mock(level="LOW"), MagicMock()).run()
    mock_sleep.assert_called()


def test_registry_resolves_hubspot_type():
    # Ensure module registered
    import connectors.hubspot_connector  # noqa: F401
    from core.connector_registry import connector_for_target

    resolved = connector_for_target({"type": "hubspot", "name": "x"})
    assert resolved is not None
    cls, keys = resolved
    assert cls is HubSpotConnector
    assert "name" in keys and "type" in keys
