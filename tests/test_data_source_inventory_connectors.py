"""Connector inventory persistence tests (Phase 1 data-source inventory)."""

from unittest.mock import MagicMock

from connectors.dataverse_connector import DataverseConnector
from connectors.mongodb_connector import MongoDBConnector
from connectors.powerbi_connector import PowerBIConnector
from connectors.redis_connector import RedisConnector
from connectors.rest_connector import RESTConnector


def _mk_scanner():
    scanner = MagicMock()
    scanner.scan_column.return_value = {
        "sensitivity_level": "LOW",
        "pattern_detected": "",
        "norm_tag": "",
        "ml_confidence": 0,
    }
    return scanner


def test_mongodb_inventory_snapshot_calls_db_manager():
    dbm = MagicMock()
    conn = MongoDBConnector({"name": "mongo-a"}, _mk_scanner(), dbm)
    conn._db = MagicMock()
    conn._db.command.return_value = {"version": "8.0.1"}
    conn._save_inventory_snapshot("mongo-a")
    assert dbm.save_data_source_inventory.called
    kwargs = dbm.save_data_source_inventory.call_args.kwargs
    assert kwargs["product"] == "mongodb"
    assert kwargs["target_name"] == "mongo-a"


def test_redis_inventory_snapshot_calls_db_manager():
    dbm = MagicMock()
    conn = RedisConnector({"name": "redis-a"}, _mk_scanner(), dbm)
    conn._client = MagicMock()
    conn._client.info.return_value = {"redis_version": "7.2.5"}
    conn._save_inventory_snapshot("redis-a")
    assert dbm.save_data_source_inventory.called
    kwargs = dbm.save_data_source_inventory.call_args.kwargs
    assert kwargs["product"] == "redis"
    assert kwargs["target_name"] == "redis-a"


def test_rest_inventory_snapshot_infers_version():
    dbm = MagicMock()
    cfg = {
        "name": "api-a",
        "base_url": "https://api.example.com",
        "paths": ["/v2/users"],
    }
    conn = RESTConnector(cfg, _mk_scanner(), dbm)
    conn._save_inventory_snapshot("api-a")
    assert dbm.save_data_source_inventory.called
    kwargs = dbm.save_data_source_inventory.call_args.kwargs
    assert kwargs["source_type"] == "api"
    assert kwargs["protocol_or_api_version"] == "v2"
    assert kwargs["transport_security"] == "tls=https"


def test_powerbi_inventory_snapshot_calls_db_manager():
    dbm = MagicMock()
    cfg = {"name": "pbi-a", "tenant_id": "tenant-1"}
    conn = PowerBIConnector(cfg, _mk_scanner(), dbm)
    conn._save_inventory_snapshot("pbi-a")
    assert dbm.save_data_source_inventory.called
    kwargs = dbm.save_data_source_inventory.call_args.kwargs
    assert kwargs["product"] == "powerbi"
    assert kwargs["protocol_or_api_version"] == "v1.0"


def test_dataverse_inventory_snapshot_calls_db_manager():
    dbm = MagicMock()
    cfg = {"name": "dv-a", "org_url": "https://org.crm.dynamics.com"}
    conn = DataverseConnector(cfg, _mk_scanner(), dbm)
    conn._save_inventory_snapshot("dv-a")
    assert dbm.save_data_source_inventory.called
    kwargs = dbm.save_data_source_inventory.call_args.kwargs
    assert kwargs["product"] == "dataverse"
    assert kwargs["protocol_or_api_version"] == "v9.2"
