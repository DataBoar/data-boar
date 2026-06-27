"""Tests for SQL connector discover/run refactors (cognitive complexity S3776).

Ensures refactored helpers _get_skip_schemas, _should_skip_schema, _tables_from_schema,
_discover_fallback_no_schemas preserve behavior so discover() returns expected tables/columns.
"""

import sqlite3
from unittest.mock import MagicMock

from connectors.sql_connector import (
    DRIVER_MAP,
    SQLConnector,
    _connect_args_from_target,
    _discover_fallback_no_schemas,
    _get_skip_schemas,
    _resolve_sample_statement_timeout_ms,
    _should_skip_schema,
)
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine.url import make_url


def test_driver_map_uses_registered_sqlalchemy_dialects():
    """DRIVER_MAP URLs must resolve to installed dialects (unit tests do not connect)."""
    for driver, drivername in DRIVER_MAP.items():
        url_str = (
            "sqlite:///:memory:"
            if driver == "sqlite"
            else f"{drivername}://user:pass@localhost:1/db"
        )
        dialect = make_url(url_str).get_dialect()
        assert dialect is not None, f"{driver} -> {drivername}"
    assert DRIVER_MAP["mariadb"] == "mariadb+mariadbconnector"


def test_resolve_sample_statement_timeout_ms_default():
    assert _resolve_sample_statement_timeout_ms({}) == 5000


def test_resolve_sample_statement_timeout_ms_explicit_zero_disables():
    assert (
        _resolve_sample_statement_timeout_ms({"sample_statement_timeout_ms": 0}) is None
    )


def test_get_skip_schemas_oracle_uses_system_schemas():
    """_get_skip_schemas('oracle') returns Oracle system set."""
    skip = _get_skip_schemas("oracle")
    assert "SYS" in skip
    assert "SYSTEM" in skip


def test_get_skip_schemas_non_oracle_uses_default():
    """_get_skip_schemas for postgresql/mysql returns default skip set."""
    skip = _get_skip_schemas("postgresql")
    assert "information_schema" in skip
    assert "pg_catalog" in skip
    assert "mysql" in skip


def test_get_skip_schemas_mssql_system_schemas():
    skip = _get_skip_schemas("mssql")
    assert "SYS" in skip
    assert "GUEST" in skip
    assert "INFORMATION_SCHEMA" in skip


def test_get_skip_schemas_snowflake_account_noise():
    skip = _get_skip_schemas("snowflake")
    assert "INFORMATION_SCHEMA" in skip
    assert "ACCOUNT_USAGE" in skip


def test_should_skip_schema_empty():
    """_should_skip_schema returns True for None or empty."""
    assert _should_skip_schema(None, "postgresql", set()) is True
    assert _should_skip_schema("", "postgresql", set()) is True


def test_should_skip_schema_when_in_set():
    """_should_skip_schema returns True when schema is in skip_schemas."""
    assert (
        _should_skip_schema("information_schema", "postgresql", {"information_schema"})
        is True
    )
    assert _should_skip_schema("SYS", "oracle", {"SYS"}) is True


def test_should_skip_schema_oracle_uppercase():
    """Oracle dialect: comparison uses schema.upper()."""
    assert _should_skip_schema("sys", "oracle", {"SYS"}) is True


def test_should_skip_schema_mssql_guest_case_insensitive():
    assert _should_skip_schema("guest", "mssql", _get_skip_schemas("mssql")) is True


def test_should_skip_schema_postgresql_information_schema_mixed_case():
    skip = _get_skip_schemas("postgresql")
    assert _should_skip_schema("Information_Schema", "postgresql", skip) is True


def test_sql_connector_discover_sqlite_in_memory(tmp_path):
    """SQLConnector.discover() with in-memory SQLite returns tables (fallback path)."""
    db_path = tmp_path / "audit.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE t1 (a TEXT, b INTEGER)")
    conn.execute("CREATE TABLE t2 (id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()

    target = {
        "type": "database",
        "driver": "sqlite",
        "database": str(db_path),
        "name": "TestDB",
    }
    scanner = MagicMock()
    db_manager = MagicMock()
    connector = SQLConnector(target, scanner, db_manager)
    connector.connect()
    try:
        result = connector.discover()
    finally:
        connector.close()

    assert len(result) >= 2
    tables = {r["table"] for r in result}
    assert "t1" in tables
    assert "t2" in tables
    t1 = next(r for r in result if r["table"] == "t1")
    # SQLite file DB may report schema "main" or ""
    assert t1["schema"] in ("", "main")
    col_names = [c["name"] for c in t1["columns"]]
    assert "a" in col_names
    assert "b" in col_names


def test_sql_connector_run_saves_inventory_row(tmp_path):
    """run() persists one inventory row through db_manager.save_data_source_inventory."""
    db_path = tmp_path / "inventory_scan.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE t1 (a TEXT)")
    conn.execute("INSERT INTO t1 VALUES ('x')")
    conn.commit()
    conn.close()

    target = {
        "type": "database",
        "driver": "sqlite",
        "database": str(db_path),
        "name": "SQLiteTarget",
    }
    scanner = MagicMock()
    scanner.scan_column.return_value = {
        "sensitivity_level": "LOW",
        "pattern_detected": "SUGGESTED_REVIEW_ID_LIKE",
        "norm_tag": "Generic identifier",
        "ml_confidence": 10,
    }
    db_manager = MagicMock()
    connector = SQLConnector(target, scanner, db_manager)
    connector.run()

    assert db_manager.save_data_source_inventory.called
    kwargs = db_manager.save_data_source_inventory.call_args.kwargs
    assert kwargs["target_name"] == "SQLiteTarget"
    assert kwargs["source_type"] == "database"
    assert kwargs["product"] == "sqlite"


def test_discover_fallback_no_schemas_returns_list():
    """_discover_fallback_no_schemas returns a list (empty or with tables)."""
    engine = create_engine("sqlite:///:memory:")
    inspector = inspect(engine)
    out = _discover_fallback_no_schemas(inspector)
    assert isinstance(out, list)
    engine.dispose()


def test_connect_args_from_target_postgresql():
    """_connect_args_from_target returns connect_timeout and statement_timeout for PostgreSQL."""
    target = {
        "driver": "postgresql",
        "connect_timeout_seconds": 15,
        "read_timeout_seconds": 120,
    }
    args = _connect_args_from_target(target)
    assert args["connect_timeout"] == 15
    assert "options" in args
    assert "statement_timeout=120000" in args["options"]


def test_connect_args_from_target_mysql():
    """_connect_args_from_target returns connect_timeout for MySQL."""
    target = {
        "driver": "mysql",
        "connect_timeout_seconds": 10,
        "read_timeout_seconds": 60,
    }
    args = _connect_args_from_target(target)
    assert args["connect_timeout"] == 10
    assert "options" not in args


def test_connect_args_from_target_sqlite():
    """_connect_args_from_target returns timeout (lock wait) for SQLite."""
    target = {"driver": "sqlite", "read_timeout_seconds": 30}
    args = _connect_args_from_target(target)
    assert args["timeout"] == 30


def test_connect_args_from_target_defaults():
    """_connect_args_from_target uses defaults 25/90 when keys missing."""
    target = {"driver": "postgresql"}
    args = _connect_args_from_target(target)
    assert args["connect_timeout"] == 25
    assert "statement_timeout=90000" in args["options"]


def test_connect_args_from_target_clamped():
    """_connect_args_from_target clamps timeouts to at least 1."""
    target = {
        "driver": "mysql",
        "connect_timeout_seconds": 0,
        "read_timeout_seconds": -1,
    }
    args = _connect_args_from_target(target)
    assert args["connect_timeout"] >= 1


def test_sql_connector_sample_sparse_column_prefers_non_null(tmp_path):
    """Many leading NULLs then a value: IS NOT NULL in SQL still returns the value within LIMIT."""
    db_path = tmp_path / "sparse_sample.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE sparse_t (c TEXT)")
    for _ in range(25):
        conn.execute("INSERT INTO sparse_t (c) VALUES (NULL)")
    conn.execute("INSERT INTO sparse_t (c) VALUES ('marker_value')")
    conn.commit()
    conn.close()

    target = {
        "type": "database",
        "driver": "sqlite",
        "database": str(db_path),
        "name": "SparseDB",
    }
    connector = SQLConnector(target, MagicMock(), MagicMock(), sample_limit=5)
    connector.connect()
    try:
        sample = connector.sample("", "sparse_t", "c")
    finally:
        connector.close()

    assert "marker_value" in sample
