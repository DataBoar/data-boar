"""MongoDB connector SSRF guard (#1559)."""

from __future__ import annotations

import importlib.util
from unittest.mock import MagicMock

import pytest

from connectors.mongodb_connector import MongoDBConnector
from connectors.url_guard import OPT_IN_KEY


def _has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


@pytest.mark.skipif(not _has_module("pymongo"), reason="pymongo not installed")
def test_mongodb_connect_rejects_private_host_without_opt_in() -> None:
    conn = MongoDBConnector(
        {"name": "m", "host": "10.0.0.5", "port": 27017},
        scanner=MagicMock(),
        db_manager=MagicMock(),
    )
    with pytest.raises(ValueError, match="#832"):
        conn.connect()


@pytest.mark.skipif(not _has_module("pymongo"), reason="pymongo not installed")
def test_mongodb_connect_allows_private_with_opt_in() -> None:
    conn = MongoDBConnector(
        {
            "name": "m",
            "host": "127.0.0.1",
            "port": 1,
            OPT_IN_KEY: True,
            "connect_timeout_seconds": 1,
            "read_timeout_seconds": 1,
        },
        scanner=MagicMock(),
        db_manager=MagicMock(),
    )
    try:
        conn.connect()
    except ValueError as exc:
        pytest.fail(f"SSRF guard must not reject opted-in private host: {exc}")
    except Exception:
        pass
    finally:
        conn.close()
