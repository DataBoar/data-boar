"""ADR-0049: Dataverse/Power BI must not treat HTTP errors as empty API results."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from connectors.dataverse_connector import DataverseConnector
from connectors.powerbi_connector import PowerBIConnector


def _mk_scanner():
    scanner = MagicMock()
    scanner.scan_column.return_value = {
        "sensitivity_level": "LOW",
        "pattern_detected": "",
        "norm_tag": "",
        "ml_confidence": 0,
    }
    return scanner


def _oauth_token_response_ok() -> MagicMock:
    m = MagicMock()
    m.raise_for_status.return_value = None
    m.json.return_value = {"access_token": "tok"}
    return m


@patch("connectors.dataverse_connector.httpx.Client")
@patch("connectors.dataverse_connector.httpx.post")
def test_dataverse_run_save_failure_on_entity_definitions_http_error(
    mock_post, mock_client_cls
):
    mock_post.return_value = _oauth_token_response_ok()
    req = httpx.Request(
        "GET", "https://org.api.crm.dynamics.com/api/data/v9.2/EntityDefinitions"
    )
    mock_client_cls.return_value.get.return_value = httpx.Response(
        403, request=req, text="Forbidden"
    )

    dbm = MagicMock()
    cfg = {
        "name": "dv-test",
        "org_url": "https://org.crm.dynamics.com",
        "tenant_id": "t",
        "client_id": "c",
        "client_secret": "sec",
    }
    DataverseConnector(cfg, _mk_scanner(), dbm).run()

    assert dbm.save_failure.called
    _target, kind, msg = dbm.save_failure.call_args[0]
    assert _target == "dv-test"
    assert kind == "error"
    assert "403" in msg or "Forbidden" in msg


@patch("connectors.powerbi_connector.httpx.Client")
@patch("connectors.powerbi_connector.httpx.post")
def test_powerbi_run_save_failure_on_groups_http_error(mock_post, mock_client_cls):
    mock_post.return_value = _oauth_token_response_ok()
    req = httpx.Request("GET", "https://api.powerbi.com/v1.0/myorg/groups")
    mock_client_cls.return_value.get.return_value = httpx.Response(
        401, request=req, text="Unauthorized"
    )

    dbm = MagicMock()
    cfg = {
        "name": "pbi-test",
        "tenant_id": "t",
        "client_id": "c",
        "client_secret": "sec",
    }
    PowerBIConnector(cfg, _mk_scanner(), dbm).run()

    assert dbm.save_failure.called
    _target, kind, msg = dbm.save_failure.call_args[0]
    assert _target == "pbi-test"
    assert kind == "error"
    assert "401" in msg or "Unauthorized" in msg


def _dataverse_auth_cfg(**overrides):
    cfg = {
        "name": "dv-ssrf",
        "org_url": "https://org.crm.dynamics.com",
        "tenant_id": "t",
        "client_id": "c",
        "client_secret": "sec",
    }
    cfg.update(overrides)
    return cfg


@patch("connectors.dataverse_connector.httpx.Client")
@patch("connectors.dataverse_connector.httpx.post")
def test_dataverse_connect_rejects_link_local_org_url_before_token_post(
    mock_post, mock_client_cls
):
    """#1232: raw link-local org_url must raise before any token POST."""
    cfg = _dataverse_auth_cfg(org_url="http://169.254.169.254")
    with pytest.raises(ValueError, match="#832|org_url|private|link-local|blocked"):
        DataverseConnector(cfg, _mk_scanner(), MagicMock()).connect()
    mock_post.assert_not_called()
    mock_client_cls.assert_not_called()


@patch("connectors.dataverse_connector.httpx.Client")
@patch("connectors.dataverse_connector.httpx.post")
def test_dataverse_connect_rejects_rfc1918_org_url_before_token_post(
    mock_post, mock_client_cls
):
    cfg = _dataverse_auth_cfg(org_url="http://10.0.0.5")
    with pytest.raises(ValueError, match="#832|org_url|private|blocked"):
        DataverseConnector(cfg, _mk_scanner(), MagicMock()).connect()
    mock_post.assert_not_called()
    mock_client_cls.assert_not_called()


@patch("connectors.dataverse_connector.httpx.Client")
@patch("connectors.dataverse_connector.httpx.post")
def test_dataverse_connect_rejects_private_token_url_before_post(
    mock_post, mock_client_cls
):
    """Public org_url + private auth.token_url must fail before httpx.post."""
    cfg = _dataverse_auth_cfg(
        auth={"token_url": "http://169.254.169.254/token"},
    )
    with pytest.raises(ValueError, match="#832|token_url|private|link-local|blocked"):
        DataverseConnector(cfg, _mk_scanner(), MagicMock()).connect()
    mock_post.assert_not_called()
    mock_client_cls.assert_not_called()


@patch("connectors.dataverse_connector.httpx.Client")
@patch("connectors.dataverse_connector.httpx.post")
def test_dataverse_connect_allow_private_networks_opts_in(mock_post, mock_client_cls):
    """#832 parity: allow_private_networks: true must not reject private org_url."""
    mock_post.return_value = _oauth_token_response_ok()
    mock_client_cls.return_value = MagicMock()
    cfg = _dataverse_auth_cfg(
        org_url="http://10.0.0.5",
        allow_private_networks=True,
    )
    DataverseConnector(cfg, _mk_scanner(), MagicMock()).connect()
    mock_post.assert_called_once()
    mock_client_cls.assert_called_once()
