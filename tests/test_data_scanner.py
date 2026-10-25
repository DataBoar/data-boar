"""Tests for connector registry and engine (no live DB/FS required)."""

import pytest

# Ensure connectors register themselves (registry is populated on import)
import connectors.filesystem_connector  # noqa: F401
import connectors.sql_connector  # noqa: F401

try:
    import connectors.rest_connector  # noqa: F401
except ImportError as rest_import_error:
    _ = str(rest_import_error)

import connectors.nfs_connector  # noqa: F401 - always registers `nfs`
import connectors.mongodb_connector  # noqa: F401 - registers `mongodb` even without pymongo

from core.connector_registry import connector_for_target, list_connector_types


def test_registry_has_sql_and_filesystem():
    types = list_connector_types()
    assert "filesystem" in types
    assert "postgresql" in types or "mysql" in types


def test_registry_has_nfs_connector():
    """NFS targets use a local mount point; connector is always registered."""
    assert "nfs" in list_connector_types()
    resolved = connector_for_target({"type": "nfs", "name": "LabNFS", "path": "/tmp"})
    assert resolved is not None


def test_registry_has_smb_always_registered():
    """SMB/CIFS always register; missing smbprotocol fails at run() with named extra (#1402)."""
    import connectors.smb_connector  # noqa: F401

    types = list_connector_types()
    assert "smb" in types
    assert "cifs" in types
    assert (
        connector_for_target(
            {
                "type": "smb",
                "name": "LabSMB",
                "host": "127.0.0.1",
                "share": "test",
                "path": "/",
            }
        )
        is not None
    )
    assert (
        connector_for_target(
            {
                "type": "cifs",
                "name": "LabCIFS",
                "host": "127.0.0.1",
                "share": "s",
                "path": "/",
            }
        )
        is not None
    )


def test_connector_for_filesystem():
    target = {"type": "filesystem", "path": "/tmp", "name": "FS"}
    resolved = connector_for_target(target)
    assert resolved is not None
    cls, _ = resolved
    assert cls is not None


def test_mongodb_driver_always_resolves_in_registry():
    """YAML with driver: mongodb must resolve; connect() requires pymongo (nosql extra)."""
    assert "mongodb" in list_connector_types()
    resolved = connector_for_target(
        {
            "type": "database",
            "driver": "mongodb",
            "name": "M",
            "host": "127.0.0.1",
            "port": 27017,
            "database": "test",
        }
    )
    assert resolved is not None


def test_connector_for_database_postgres():
    target = {
        "type": "database",
        "driver": "postgresql+psycopg2",
        "name": "PG",
        "host": "localhost",
    }
    resolved = connector_for_target(target)
    assert resolved is not None


def test_connector_for_unknown():
    target = {"type": "database", "driver": "unknown_db", "name": "X"}
    resolved = connector_for_target(target)
    assert resolved is None


def test_connector_for_api():
    """REST connector is registered when rest_connector is importable."""
    target = {
        "type": "api",
        "name": "TestAPI",
        "base_url": "https://example.com",
        "paths": ["/users"],
    }
    resolved = connector_for_target(target)
    if resolved is None:
        pytest.skip(
            "REST connector not registered (httpx or rest_connector not available)"
        )
    cls, _ = resolved
    assert cls is not None
    target_rest = {"type": "rest", "name": "R", "base_url": "https://x.com"}
    assert connector_for_target(target_rest) is not None
