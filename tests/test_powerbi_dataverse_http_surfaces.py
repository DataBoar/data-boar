"""ADR-0049: Dataverse/Power BI must not treat HTTP errors as empty API results."""

from unittest.mock import MagicMock, patch

import httpx

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
