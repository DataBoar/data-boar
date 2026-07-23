"""Tests for SQL connector discover/run refactors (cognitive complexity S3776).

Ensures refactored helpers _get_skip_schemas, _should_skip_schema, _tables_from_schema,
_discover_fallback_no_schemas preserve behavior so discover() returns expected tables/columns.
"""

import sqlite3
from unittest.mock import MagicMock

import pytest
from connectors.sql_connector import (
    DRIVER_MAP,
    SCAN_FAILURE_REASON_SAMPLING_ERROR,
    ColumnSampleError,
    SQLConnector,
    _build_url,
    _connect_args_from_target,
    _discover_fallback_no_schemas,
    _get_skip_schemas,
    _resolve_driver,
    _resolve_sample_statement_timeout_ms,
    _should_skip_schema,
    format_column_sample_failure_details,
)
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine.url import make_url
from sqlalchemy.exc import ProgrammingError


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
    assert DRIVER_MAP["mssql"] == "mssql+pymssql"


def test_resolve_driver_honors_explicit_dialect_plus_driver() -> None:
    drivername, base = _resolve_driver("mssql+pyodbc")
    assert drivername == "mssql+pyodbc"
    assert base == "mssql"


def test_resolve_driver_maps_bare_mssql_to_pymssql() -> None:
    drivername, base = _resolve_driver("mssql")
    assert drivername == "mssql+pymssql"
    assert base == "mssql"


def test_build_url_honors_explicit_mssql_pyodbc() -> None:
    url = _build_url(
        {
            "driver": "mssql+pyodbc",
            "host": "sql.example.com",
            "port": 1433,
            "user": "u",
            "password": "p",
            "database": "db",
        }
    )
    assert url.startswith("mssql+pyodbc://")


def test_build_url_maps_bare_mssql_to_pymssql() -> None:
    url = _build_url(
        {
            "driver": "mssql",
            "host": "sql.example.com",
            "port": 1433,
            "user": "u",
            "password": "p",
            "database": "db",
        }
    )
    assert url.startswith("mssql+pymssql://")


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


def test_get_skip_schemas_oracle_includes_12c_plus_system_schemas():
    """Oracle 12c+/23c maintained schemas skipped (issue #1315 — AUDSYS cascade)."""
    skip = _get_skip_schemas("oracle")
    assert "AUDSYS" in skip
    assert "GGSYS" in skip
    assert "SYSBACKUP" in skip
    assert "PDBADMIN" in skip
    # Already present before #1315 — must not regress
    assert "DVF" in skip
    assert "DVSYS" in skip
    assert "GSMADMIN_INTERNAL" in skip


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


def test_sql_connector_run_sqlite_sampling_persists_findings_without_sampling_error(
    tmp_path,
):
    """Regression #1194: sampling must produce findings without sampling_error side effects."""
    db_path = tmp_path / "sampling_scan.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE people (email TEXT)")
    conn.execute("INSERT INTO people VALUES ('alice@example.com')")
    conn.execute("INSERT INTO people VALUES ('bob@example.com')")
    conn.commit()
    conn.close()

    target = {
        "type": "database",
        "driver": "sqlite",
        "database": str(db_path),
        "name": "SQLiteSamplingTarget",
    }
    scanner = MagicMock()
    scanner.scan_column.return_value = {
        "sensitivity_level": "HIGH",
        "pattern_detected": "EMAIL",
        "norm_tag": "Personal email",
        "ml_confidence": 95,
    }
    db_manager = MagicMock()
    connector = SQLConnector(target, scanner, db_manager)
    connector.run()

    scanner.scan_column.assert_called()
    db_manager.save_finding.assert_called()
    sampling_failures = [
        call.args[1]
        for call in db_manager.save_failure.call_args_list
        if len(call.args) >= 2
    ]
    assert SCAN_FAILURE_REASON_SAMPLING_ERROR not in sampling_failures


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
    assert "login_timeout" not in args
    assert "tcp_connect_timeout" not in args


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
    assert "login_timeout" not in args
    assert "tcp_connect_timeout" not in args


def test_connect_args_from_target_mssql_bare_maps_to_pymssql():
    """Bare mssql resolves to mssql+pymssql → login_timeout/timeout (not connect_timeout)."""
    target = {
        "driver": "mssql",
        "connect_timeout_seconds": 20,
        "read_timeout_seconds": 80,
    }
    args = _connect_args_from_target(target)
    assert args == {"login_timeout": 20, "timeout": 80}
    assert "connect_timeout" not in args


def test_connect_args_from_target_mssql_pymssql_explicit():
    """Explicit mssql+pymssql keeps login_timeout/timeout (#1297 / #1302)."""
    target = {
        "driver": "mssql+pymssql",
        "connect_timeout_seconds": 20,
        "read_timeout_seconds": 80,
    }
    args = _connect_args_from_target(target)
    assert args == {"login_timeout": 20, "timeout": 80}
    assert "connect_timeout" not in args
    assert "login_timeout" in args


def test_connect_args_from_target_mssql_pyodbc():
    """mssql+pyodbc uses pyodbc timeout only — never login_timeout (#1302)."""
    target = {
        "driver": "mssql+pyodbc",
        "connect_timeout_seconds": 20,
        "read_timeout_seconds": 80,
    }
    args = _connect_args_from_target(target)
    assert args == {"timeout": 20}
    assert "login_timeout" not in args
    assert "connect_timeout" not in args


def test_connect_args_from_target_oracle_oracledb():
    """oracle+oracledb uses tcp_connect_timeout — never connect_timeout (#1302)."""
    target = {
        "driver": "oracle+oracledb",
        "connect_timeout_seconds": 30,
        "read_timeout_seconds": 90,
    }
    args = _connect_args_from_target(target)
    assert args == {"tcp_connect_timeout": 30}
    assert "connect_timeout" not in args


def test_connect_args_from_target_oracle_bare():
    """Bare oracle maps to oracle+oracledb → tcp_connect_timeout."""
    target = {
        "driver": "oracle",
        "connect_timeout_seconds": 12,
    }
    args = _connect_args_from_target(target)
    assert args == {"tcp_connect_timeout": 12}
    assert "connect_timeout" not in args


def test_connect_args_from_target_sqlite():
    """_connect_args_from_target returns timeout (lock wait) for SQLite."""
    target = {
        "driver": "sqlite",
        "connect_timeout_seconds": 25,
        "read_timeout_seconds": 30,
    }
    args = _connect_args_from_target(target)
    assert args == {"timeout": 30}
    assert "connect_timeout" not in args
    assert "login_timeout" not in args


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


def test_format_column_sample_failure_details_includes_location_and_dialect():
    err = ProgrammingError("stmt", {}, Exception("Incorrect syntax near 'OPTION'"))
    detail = format_column_sample_failure_details(
        schema="dbo",
        table="users",
        column_name="email",
        dialect="mssql",
        exc=err,
    )
    assert "dbo.users.email" in detail
    assert "dialect=mssql" in detail
    assert "ProgrammingError" in detail


def test_sql_connector_sample_syntax_error_records_scan_failure():
    """Sampling SQL errors must persist scan_failures, not return empty clean samples (#1140)."""
    target = {"type": "database", "driver": "mssql", "name": "ProdDB"}
    scanner = MagicMock()
    db_manager = MagicMock()
    connector = SQLConnector(target, scanner, db_manager, sample_limit=5)
    connector.engine = MagicMock()
    connector.engine.dialect.name = "mssql"
    conn_ctx = MagicMock()
    conn = MagicMock()
    connector.engine.connect.return_value = conn_ctx
    conn_ctx.__enter__.return_value = conn
    conn_ctx.__exit__.return_value = False
    tx_ctx = MagicMock()
    conn.begin.return_value = tx_ctx
    tx_ctx.__enter__.return_value = None
    tx_ctx.__exit__.return_value = False
    conn.execute.side_effect = ProgrammingError(
        "SELECT",
        {},
        Exception("Incorrect syntax near 'OPTION'"),
    )

    with pytest.raises(ColumnSampleError):
        connector.sample("dbo", "users", "email")

    db_manager.save_failure.assert_called_once()
    args = db_manager.save_failure.call_args[0]
    assert args[0] == "ProdDB"
    assert args[1] == SCAN_FAILURE_REASON_SAMPLING_ERROR
    assert "users" in args[2]


def test_process_one_finding_sampling_error_skips_scan_column():
    """Failed sampling must not run detection on an empty pseudo-clean sample."""
    target = {"type": "database", "driver": "sqlite", "name": "T"}
    scanner = MagicMock()
    db_manager = MagicMock()
    connector = SQLConnector(target, scanner, db_manager)
    connector.sample = MagicMock(side_effect=ColumnSampleError())

    connector._process_one_finding("T", "localhost", "sqlite", "", "t1", "c1", "TEXT")

    scanner.scan_column.assert_not_called()


def test_minor_full_scan_sample_error_keeps_first_pass_dob_and_records_failure():
    """Full-scan ColumnSampleError must not discard DOB_POSSIBLE_MINOR from the first pass (#1140)."""
    target = {"type": "database", "driver": "sqlite", "name": "MinorDB"}
    scanner = MagicMock()
    scanner.scan_column.return_value = {
        "sensitivity_level": "MEDIUM",
        "pattern_detected": "DOB_POSSIBLE_MINOR",
        "norm_tag": "",
        "ml_confidence": 50,
    }
    db_manager = MagicMock()
    connector = SQLConnector(
        target,
        scanner,
        db_manager,
        detection_config={"minor_full_scan": True, "minor_full_scan_limit": 100},
    )

    def sample_side_effect(schema, table, cname, limit=None):
        if limit is not None:
            db_manager.save_failure(
                "MinorDB",
                SCAN_FAILURE_REASON_SAMPLING_ERROR,
                "dbo.minors.dob dialect=sqlite: ProgrammingError: full scan failed",
            )
            raise ColumnSampleError()
        return "2005-01-01"

    connector.sample = MagicMock(side_effect=sample_side_effect)

    connector._process_one_finding(
        "MinorDB", "localhost", "sqlite", "", "minors", "dob", "DATE"
    )

    db_manager.save_failure.assert_called_once_with(
        "MinorDB",
        SCAN_FAILURE_REASON_SAMPLING_ERROR,
        "dbo.minors.dob dialect=sqlite: ProgrammingError: full scan failed",
    )
    db_manager.save_finding.assert_called_once()
    finding_kwargs = db_manager.save_finding.call_args.kwargs
    assert "DOB_POSSIBLE_MINOR" in finding_kwargs["pattern_detected"]
    assert "(full-scan confirmed)" not in (finding_kwargs.get("norm_tag") or "")
