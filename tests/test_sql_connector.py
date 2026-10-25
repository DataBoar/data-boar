"""Tests for SQL connector discover/run refactors (cognitive complexity S3776).

Ensures refactored helpers _get_skip_schemas, _should_skip_schema, _tables_from_schema,
_discover_fallback_no_schemas preserve behavior so discover() returns expected tables/columns.
"""

import sqlite3
from unittest.mock import MagicMock, patch

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


def test_sql_connect_rejects_private_host_without_opt_in() -> None:
    # regression-anchor: #1556
    from connectors import sql_connector
    from connectors.sql_connector import SQLConnector

    with patch.object(sql_connector, "ensure_sql_driver_available"):
        connector = SQLConnector(
            {
                "name": "probe",
                "driver": "postgresql+psycopg2",
                "host": "169.254.169.254",
                "port": 5432,
                "user": "x",
                "pass": "x",
                "database": "x",
            },
            scanner=MagicMock(),
            db_manager=MagicMock(),
        )
        with pytest.raises(ValueError, match="#832"):
            connector.connect()


def test_sql_connect_rejects_private_host_via_url_override() -> None:
    # regression-anchor: #1556 — url override must not bypass the guard.
    from connectors import sql_connector
    from connectors.sql_connector import SQLConnector

    with patch.object(sql_connector, "ensure_sql_driver_available"):
        connector = SQLConnector(
            {
                "name": "probe",
                "driver": "postgresql+psycopg2",
                "url": "postgresql+psycopg2://x:x@10.1.2.3:5432/x",
            },
            scanner=MagicMock(),
            db_manager=MagicMock(),
        )
        with pytest.raises(ValueError, match="#832"):
            connector.connect()


def test_sql_connect_allows_private_with_opt_in_before_engine() -> None:
    # Guard passes; create_engine may still fail without the driver — mock it.
    from connectors import sql_connector
    from connectors.url_guard import OPT_IN_KEY

    with (
        patch.object(sql_connector, "ensure_sql_driver_available"),
        patch.object(sql_connector, "create_engine") as mock_engine,
    ):
        mock_engine.return_value = MagicMock()
        connector = sql_connector.SQLConnector(
            {
                "name": "lab",
                "driver": "postgresql+psycopg2",
                "host": "10.0.0.8",
                "port": 5432,
                "user": "u",
                "pass": "p",
                "database": "db",
                OPT_IN_KEY: True,
            },
            scanner=MagicMock(),
            db_manager=MagicMock(),
        )
        connector.connect()
        mock_engine.assert_called_once()
        call_kw = mock_engine.call_args.kwargs
        assert call_kw["connect_args"]["hostaddr"] == "10.0.0.8"
        connector.close()


def test_sql_postgres_connect_pins_hostaddr_from_guard_dns(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """#1586 slice A: hostname stays in URL; TCP peer is guard-validated hostaddr."""
    import ipaddress
    import socket
    from urllib.parse import urlsplit

    from connectors import sql_connector

    host = "db.example.com"

    def fake_getaddrinfo(name, *args, **kwargs):
        if name == host:
            return [
                (
                    socket.AF_INET,
                    socket.SOCK_STREAM,
                    6,
                    "",
                    ("1.1.1.1", 0),
                ),
                (
                    socket.AF_INET6,
                    socket.SOCK_STREAM,
                    6,
                    "",
                    ("2606:4700:4700::1111", 0, 0, 0),
                ),
            ]
        raise socket.gaierror(f"unexpected host {name!r}")

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    # url_guard imports socket at module level for _resolve_host_ips
    monkeypatch.setattr(
        "connectors.url_guard.socket.getaddrinfo",
        fake_getaddrinfo,
    )

    with (
        patch.object(sql_connector, "ensure_sql_driver_available"),
        patch.object(sql_connector, "create_engine") as mock_engine,
    ):
        mock_engine.return_value = MagicMock()
        connector = sql_connector.SQLConnector(
            {
                "name": "pg-pin",
                "driver": "postgresql+psycopg2",
                "host": host,
                "port": 5432,
                "user": "u",
                "pass": "p",
                "database": "db",
            },
            scanner=MagicMock(),
            db_manager=MagicMock(),
        )
        connector.connect()
        mock_engine.assert_called_once()
        (url,) = mock_engine.call_args.args
        call_kw = mock_engine.call_args.kwargs
        parsed = urlsplit(url)
        # Authority hostname (not substring) — precise vs pin IP; CodeQL-safe.
        assert parsed.hostname == host
        assert call_kw["connect_args"]["hostaddr"] == "1.1.1.1"
        assert "hostaddr" not in (parsed.query or "")
        # Prefer IPv4 pin (same order as HTTP #1565 / _prefer_pin_order)
        assert call_kw["connect_args"]["hostaddr"] != str(
            ipaddress.IPv6Address("2606:4700:4700::1111")
        )
        connector.close()


def test_sql_mysql_connect_installs_host_resolution_pin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """#1586 MySQL: URL hostname kept; getaddrinfo only returns guard pins."""
    import socket
    from urllib.parse import urlsplit

    from connectors import sql_connector

    host = "mysql.example.com"

    def fake_getaddrinfo(name, *args, **kwargs):
        if name == host:
            return [
                (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("1.1.1.1", 0)),
                (
                    socket.AF_INET6,
                    socket.SOCK_STREAM,
                    6,
                    "",
                    ("2606:4700:4700::1111", 0, 0, 0),
                ),
            ]
        raise socket.gaierror(f"unexpected host {name!r}")

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    monkeypatch.setattr(
        "connectors.url_guard.socket.getaddrinfo",
        fake_getaddrinfo,
    )

    with (
        patch.object(sql_connector, "ensure_sql_driver_available"),
        patch.object(sql_connector, "create_engine") as mock_engine,
    ):
        mock_engine.return_value = MagicMock()
        connector = sql_connector.SQLConnector(
            {
                "name": "mysql-pin",
                "driver": "mysql",
                "host": host,
                "port": 3306,
                "user": "u",
                "pass": "p",
                "database": "db",
            },
            scanner=MagicMock(),
            db_manager=MagicMock(),
        )
        connector.connect()
        mock_engine.assert_called_once()
        (url,) = mock_engine.call_args.args
        assert urlsplit(url).hostname == host
        peers = {info[4][0] for info in socket.getaddrinfo(host, 3306)}
        assert peers == {"1.1.1.1", "2606:4700:4700::1111"}
        assert connector._dns_pin is not None
        connector.close()
        assert getattr(connector, "_dns_pin", None) is None


def test_sql_mysql_pin_released_when_create_engine_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """#1586 — failed create_engine must not leave a process-wide DNS pin."""
    import socket

    import connectors.tcp_pin as tcp_pin
    from connectors import sql_connector
    from connectors.tcp_pin import normalize_pin_hostname

    host = "mysql-fail.example.com"
    key = normalize_pin_hostname(host)

    def fake_getaddrinfo(name, *args, **kwargs):
        if name == host:
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("1.1.1.1", 0))]
        raise socket.gaierror(f"unexpected host {name!r}")

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    monkeypatch.setattr(
        "connectors.url_guard.socket.getaddrinfo",
        fake_getaddrinfo,
    )

    with (
        patch.object(sql_connector, "ensure_sql_driver_available"),
        patch.object(
            sql_connector,
            "create_engine",
            side_effect=RuntimeError("boom"),
        ),
    ):
        connector = sql_connector.SQLConnector(
            {
                "name": "mysql-fail",
                "driver": "mysql+pymysql",
                "host": host,
                "port": 3306,
                "user": "u",
                "pass": "p",
                "database": "db",
            },
            scanner=MagicMock(),
            db_manager=MagicMock(),
        )
        with pytest.raises(RuntimeError, match="boom"):
            connector.connect()
    assert key not in tcp_pin._HOST_PINS
    assert getattr(connector, "_dns_pin", None) is None


def test_sql_mariadb_default_driver_fails_closed_without_python_pin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """#1586 / #1597 Security: bare mariadb → mariadbconnector must not no-op pin."""
    import socket

    from connectors import sql_connector

    host = "mariadb.example.com"

    def fake_getaddrinfo(name, *args, **kwargs):
        if name == host:
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("1.1.1.1", 0))]
        raise socket.gaierror(f"unexpected host {name!r}")

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    monkeypatch.setattr(
        "connectors.url_guard.socket.getaddrinfo",
        fake_getaddrinfo,
    )

    with patch.object(sql_connector, "ensure_sql_driver_available"):
        connector = sql_connector.SQLConnector(
            {
                "name": "mdb",
                "driver": "mariadb",
                "host": host,
                "port": 3306,
                "user": "u",
                "pass": "p",
                "database": "db",
            },
            scanner=MagicMock(),
            db_manager=MagicMock(),
        )
        with pytest.raises(ValueError, match="#1586|pymysql|mariadbconnector"):
            connector.connect()


def test_sql_mysql_mysqldb_fails_closed_without_python_pin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """#1586 — mysql+mysqldb uses libc resolve; refuse hostname targets."""
    import socket

    from connectors import sql_connector

    host = "mysql-native.example.com"

    def fake_getaddrinfo(name, *args, **kwargs):
        if name == host:
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("1.1.1.1", 0))]
        raise socket.gaierror(f"unexpected host {name!r}")

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    monkeypatch.setattr(
        "connectors.url_guard.socket.getaddrinfo",
        fake_getaddrinfo,
    )

    with patch.object(sql_connector, "ensure_sql_driver_available"):
        connector = sql_connector.SQLConnector(
            {
                "name": "mysqldb",
                "driver": "mysql+mysqldb",
                "host": host,
                "port": 3306,
                "user": "u",
                "pass": "p",
                "database": "db",
            },
            scanner=MagicMock(),
            db_manager=MagicMock(),
        )
        with pytest.raises(ValueError, match="#1586|pymysql"):
            connector.connect()


def test_sql_mariadb_pymysql_installs_host_resolution_pin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """#1586 — explicit mariadb+pymysql is pin-capable like mysql+pymysql."""
    import socket
    from urllib.parse import urlsplit

    from connectors import sql_connector

    host = "mariadb-py.example.com"

    def fake_getaddrinfo(name, *args, **kwargs):
        if name == host:
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("1.1.1.1", 0))]
        raise socket.gaierror(f"unexpected host {name!r}")

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    monkeypatch.setattr(
        "connectors.url_guard.socket.getaddrinfo",
        fake_getaddrinfo,
    )

    with (
        patch.object(sql_connector, "ensure_sql_driver_available"),
        patch.object(sql_connector, "create_engine") as mock_engine,
    ):
        mock_engine.return_value = MagicMock()
        connector = sql_connector.SQLConnector(
            {
                "name": "mdb-py",
                "driver": "mariadb+pymysql",
                "host": host,
                "port": 3306,
                "user": "u",
                "pass": "p",
                "database": "db",
            },
            scanner=MagicMock(),
            db_manager=MagicMock(),
        )
        connector.connect()
        assert urlsplit(mock_engine.call_args.args[0]).hostname == host
        assert connector._dns_pin is not None
        connector.close()


def test_mysql_family_python_dns_pin_supported() -> None:
    from connectors.sql_connector import _mysql_family_python_dns_pin_supported

    assert _mysql_family_python_dns_pin_supported("mysql+pymysql") is True
    assert _mysql_family_python_dns_pin_supported("mariadb+pymysql") is True
    assert _mysql_family_python_dns_pin_supported("mariadb+mariadbconnector") is False
    assert _mysql_family_python_dns_pin_supported("mysql+mysqldb") is False
    assert _mysql_family_python_dns_pin_supported("mysql") is False


def test_apply_mssql_tcp_peer_pin_rewrites_hostname_to_ip() -> None:
    """#1586 slice E — FreeTDS dials the guard IP; no HostResolutionPin."""
    from connectors.sql_connector import _apply_mssql_tcp_peer_pin

    out = _apply_mssql_tcp_peer_pin(
        "mssql+pymssql://u:p@sql.example.com:1433/db",
        ["1.1.1.1", "2606:4700:4700::1111"],
    )
    assert out == "mssql+pymssql://u:p@1.1.1.1:1433/db"


def test_apply_mssql_tcp_peer_pin_formats_ipv6() -> None:
    from connectors.sql_connector import _apply_mssql_tcp_peer_pin

    out = _apply_mssql_tcp_peer_pin(
        "mssql+pymssql://u:p@sql.example.com:1433/db",
        ["2606:4700:4700::1111"],
    )
    assert out == "mssql+pymssql://u:p@[2606:4700:4700::1111]:1433/db"


def test_apply_mssql_tcp_peer_pin_pyodbc_injects_hostname_in_certificate() -> None:
    from connectors.sql_connector import _apply_mssql_tcp_peer_pin
    from sqlalchemy.engine.url import make_url

    out = _apply_mssql_tcp_peer_pin(
        "mssql+pyodbc://u:p@sql.example.com:1433/db"
        "?driver=ODBC+Driver+18+for+SQL+Server",
        ["1.1.1.1"],
    )
    parsed = make_url(out)
    assert parsed.host == "1.1.1.1"
    q = {str(k).lower(): v for k, v in parsed.query.items()}
    assert q["hostnameincertificate"] == "sql.example.com"
    assert "driver" in q


def test_apply_mssql_tcp_peer_pin_preserves_existing_hostname_in_certificate() -> None:
    from connectors.sql_connector import _apply_mssql_tcp_peer_pin
    from sqlalchemy.engine.url import make_url

    out = _apply_mssql_tcp_peer_pin(
        "mssql+pyodbc://u:p@sql.example.com:1433/db"
        "?HostNameInCertificate=custom.cert.name",
        ["1.1.1.1"],
    )
    parsed = make_url(out)
    assert parsed.host == "1.1.1.1"
    q = {str(k).lower(): v for k, v in parsed.query.items()}
    assert q["hostnameincertificate"] == "custom.cert.name"


def test_apply_mssql_tcp_peer_pin_literal_ip_noop() -> None:
    from connectors.sql_connector import _apply_mssql_tcp_peer_pin

    url = "mssql+pymssql://u:p@1.1.1.1:1433/db"
    assert _apply_mssql_tcp_peer_pin(url, ["9.9.9.9"]) == url


def test_apply_mssql_tcp_peer_pin_unsupported_dbapi_fails_closed() -> None:
    from connectors.sql_connector import _apply_mssql_tcp_peer_pin

    with pytest.raises(ValueError, match="#1586|pymssql|pyodbc"):
        _apply_mssql_tcp_peer_pin(
            "mssql+adodbapi://u:p@sql.example.com:1433/db",
            ["1.1.1.1"],
        )


def test_sql_mssql_pymssql_connect_rewrites_url_host_to_pin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """#1586 — bare mssql → pymssql; create_engine sees pin IP, not hostname."""
    import socket
    from urllib.parse import urlsplit

    from connectors import sql_connector

    host = "mssql.example.com"

    def fake_getaddrinfo(name, *args, **kwargs):
        if name == host:
            return [
                (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("1.1.1.1", 0)),
                (
                    socket.AF_INET6,
                    socket.SOCK_STREAM,
                    6,
                    "",
                    ("2606:4700:4700::1111", 0, 0, 0),
                ),
            ]
        raise socket.gaierror(f"unexpected host {name!r}")

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    monkeypatch.setattr(
        "connectors.url_guard.socket.getaddrinfo",
        fake_getaddrinfo,
    )

    with (
        patch.object(sql_connector, "ensure_sql_driver_available"),
        patch.object(sql_connector, "create_engine") as mock_engine,
    ):
        mock_engine.return_value = MagicMock()
        connector = sql_connector.SQLConnector(
            {
                "name": "mssql-pin",
                "driver": "mssql",
                "host": host,
                "port": 1433,
                "user": "u",
                "pass": "p",
                "database": "db",
            },
            scanner=MagicMock(),
            db_manager=MagicMock(),
        )
        connector.connect()
        mock_engine.assert_called_once()
        (url,) = mock_engine.call_args.args
        assert urlsplit(url).hostname == "1.1.1.1"
        assert connector._dns_pin is None
        connector.close()


def test_sql_mssql_pyodbc_connect_pins_ip_and_tls_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """#1586 — pyodbc: SERVER=pin IP + HostNameInCertificate=hostname."""
    import socket

    from connectors import sql_connector
    from sqlalchemy.engine.url import make_url

    host = "mssql-odbc.example.com"

    def fake_getaddrinfo(name, *args, **kwargs):
        if name == host:
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("1.1.1.1", 0))]
        raise socket.gaierror(f"unexpected host {name!r}")

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    monkeypatch.setattr(
        "connectors.url_guard.socket.getaddrinfo",
        fake_getaddrinfo,
    )

    with (
        patch.object(sql_connector, "ensure_sql_driver_available"),
        patch.object(sql_connector, "create_engine") as mock_engine,
    ):
        mock_engine.return_value = MagicMock()
        connector = sql_connector.SQLConnector(
            {
                "name": "mssql-odbc-pin",
                "driver": "mssql+pyodbc",
                "host": host,
                "port": 1433,
                "user": "u",
                "pass": "p",
                "database": "db",
            },
            scanner=MagicMock(),
            db_manager=MagicMock(),
        )
        connector.connect()
        parsed = make_url(mock_engine.call_args.args[0])
        assert parsed.host == "1.1.1.1"
        q = {str(k).lower(): v for k, v in parsed.query.items()}
        assert q["hostnameincertificate"] == host
        connector.close()


def test_sql_guard_allows_mssql_hostnameincertificate_query() -> None:
    from connectors.sql_connector import _guard_sql_connection_url

    _guard_sql_connection_url(
        "mssql+pyodbc://x:x@1.1.1.1:1433/db?HostNameInCertificate=sql.example.com",
        {"name": "ok"},
    )


def test_apply_oracle_tcp_peer_pin_rewrites_hostname_to_ip() -> None:
    """#1586 slice F — oracledb Thin dials the guard IP; no HostResolutionPin."""
    from connectors.sql_connector import _apply_oracle_tcp_peer_pin

    out = _apply_oracle_tcp_peer_pin(
        "oracle+oracledb://u:p@ora.example.com:1521/?service_name=ORCL",
        ["1.1.1.1", "2606:4700:4700::1111"],
    )
    assert out == "oracle+oracledb://u:p@1.1.1.1:1521/?service_name=ORCL"


def test_apply_oracle_tcp_peer_pin_formats_ipv6() -> None:
    from connectors.sql_connector import _apply_oracle_tcp_peer_pin

    out = _apply_oracle_tcp_peer_pin(
        "oracle+oracledb://u:p@ora.example.com:1521/?service_name=ORCL",
        ["2606:4700:4700::1111"],
    )
    assert out == (
        "oracle+oracledb://u:p@[2606:4700:4700::1111]:1521/?service_name=ORCL"
    )


def test_apply_oracle_tcp_peer_pin_literal_ip_noop() -> None:
    from connectors.sql_connector import _apply_oracle_tcp_peer_pin

    url = "oracle+oracledb://u:p@1.1.1.1:1521/?service_name=ORCL"
    assert _apply_oracle_tcp_peer_pin(url, ["9.9.9.9"]) == url


def test_apply_oracle_tcp_peer_pin_cx_oracle_fails_closed() -> None:
    from connectors.sql_connector import _apply_oracle_tcp_peer_pin

    with pytest.raises(ValueError, match="#1586|oracledb"):
        _apply_oracle_tcp_peer_pin(
            "oracle+cx_oracle://u:p@ora.example.com:1521/?service_name=ORCL",
            ["1.1.1.1"],
        )


def test_sql_oracle_oracledb_connect_rewrites_url_host_to_pin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """#1586 — bare oracle → oracledb; create_engine sees pin IP, not hostname."""
    import socket
    from urllib.parse import urlsplit

    from connectors import sql_connector

    host = "ora.example.com"

    def fake_getaddrinfo(name, *args, **kwargs):
        if name == host:
            return [
                (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("1.1.1.1", 0)),
                (
                    socket.AF_INET6,
                    socket.SOCK_STREAM,
                    6,
                    "",
                    ("2606:4700:4700::1111", 0, 0, 0),
                ),
            ]
        raise socket.gaierror(f"unexpected host {name!r}")

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    monkeypatch.setattr(
        "connectors.url_guard.socket.getaddrinfo",
        fake_getaddrinfo,
    )

    with (
        patch.object(sql_connector, "ensure_sql_driver_available"),
        patch.object(sql_connector, "create_engine") as mock_engine,
    ):
        mock_engine.return_value = MagicMock()
        connector = sql_connector.SQLConnector(
            {
                "name": "oracle-pin",
                "driver": "oracle",
                "host": host,
                "port": 1521,
                "user": "u",
                "pass": "p",
                "database": "ORCL",
            },
            scanner=MagicMock(),
            db_manager=MagicMock(),
        )
        connector.connect()
        mock_engine.assert_called_once()
        (url,) = mock_engine.call_args.args
        assert urlsplit(url).hostname == "1.1.1.1"
        assert "service_name=ORCL" in url
        assert connector._dns_pin is None
        connector.close()


def test_sql_oracle_cx_oracle_fails_closed_without_python_pin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """#1586 — oracle+cx_oracle uses native resolve; refuse hostname targets."""
    import socket

    from connectors import sql_connector

    host = "ora-cx.example.com"

    def fake_getaddrinfo(name, *args, **kwargs):
        if name == host:
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("1.1.1.1", 0))]
        raise socket.gaierror(f"unexpected host {name!r}")

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    monkeypatch.setattr(
        "connectors.url_guard.socket.getaddrinfo",
        fake_getaddrinfo,
    )

    with patch.object(sql_connector, "ensure_sql_driver_available"):
        connector = sql_connector.SQLConnector(
            {
                "name": "ora-cx",
                "driver": "oracle+cx_oracle",
                "host": host,
                "port": 1521,
                "user": "u",
                "pass": "p",
                "database": "ORCL",
            },
            scanner=MagicMock(),
            db_manager=MagicMock(),
        )
        with pytest.raises(ValueError, match="#1586|oracledb"):
            connector.connect()


def test_apply_postgres_hostaddr_pin_formats_ipv6() -> None:
    from connectors.sql_connector import _apply_postgres_hostaddr_pin

    out = _apply_postgres_hostaddr_pin(
        {"connect_timeout": 5},
        ["2001:db8::1"],
    )
    assert out["hostaddr"] == "2001:db8::1"
    assert "[" not in out["hostaddr"]


def test_tcp_pin_primary_pin_str_empty_raises() -> None:
    from connectors.tcp_pin import primary_pin_str

    with pytest.raises(ValueError, match="#1586"):
        primary_pin_str([])


def test_sql_guard_rejects_private_peer_via_query_host_override() -> None:
    # regression-anchor: #1556 — query peer overrides are not allowlisted.
    from connectors.sql_connector import _guard_sql_connection_url

    with pytest.raises(ValueError, match="#1556"):
        _guard_sql_connection_url(
            "postgresql+psycopg2://x:x@1.1.1.1:5432/db?host=169.254.169.254",
            {"name": "probe"},
        )


def test_sql_guard_rejects_private_peer_via_query_hostaddr() -> None:
    from connectors.sql_connector import _guard_sql_connection_url

    with pytest.raises(ValueError, match="#1556"):
        _guard_sql_connection_url(
            "postgresql+psycopg2://x:x@1.1.1.1:5432/db?hostaddr=10.0.0.9",
            {"name": "probe"},
        )


def test_sql_guard_rejects_unix_socket_query() -> None:
    from connectors.sql_connector import _guard_sql_connection_url
    from connectors.url_guard import OPT_IN_KEY

    # Socket selectors are never allowlisted (opt-in does not reopen peer overrides).
    with pytest.raises(ValueError, match="#1556"):
        _guard_sql_connection_url(
            "postgresql+psycopg2://x:x@1.1.1.1:5432/db?unix_socket=/var/run/postgresql",
            {"name": "probe", OPT_IN_KEY: True},
        )


def test_sql_guard_rejects_libpq_host_socket_path() -> None:
    # regression-anchor: Bugbot — libpq host=/dir is a peer override, not allowlisted.
    from connectors.sql_connector import _guard_sql_connection_url
    from connectors.url_guard import OPT_IN_KEY

    with pytest.raises(ValueError, match="#1556"):
        _guard_sql_connection_url(
            "postgresql+psycopg2://x:x@127.0.0.1:5432/db?host=/var/run/postgresql",
            {"name": "lab", OPT_IN_KEY: True},
        )


def test_sql_guard_rejects_odbc_connect_and_dsn_query() -> None:
    # regression-anchor: Bugbot round 3 — pyodbc odbc_connect / DSN bypass.
    from connectors.sql_connector import _guard_sql_connection_url
    from connectors.url_guard import OPT_IN_KEY

    for url in (
        "mssql+pyodbc://x:x@1.1.1.1:1433/db?odbc_connect=DRIVER%3D%7BODBC%20Driver%7D%3BSERVER%3D169.254.169.254",
        "mssql+pyodbc://x:x@1.1.1.1:1433/db?DSN=evil",
    ):
        with pytest.raises(ValueError, match="#1556"):
            _guard_sql_connection_url(url, {"name": "probe", OPT_IN_KEY: True})


def test_sql_guard_rejects_query_on_unvetted_dialect() -> None:
    from connectors.sql_connector import _guard_sql_connection_url

    with pytest.raises(ValueError, match="#1556"):
        _guard_sql_connection_url(
            "somethingdb://x:x@1.1.1.1:1234/db?sslmode=require",
            {"name": "probe"},
        )


def test_sql_guard_allows_safe_postgresql_query() -> None:
    from connectors.sql_connector import _guard_sql_connection_url

    _guard_sql_connection_url(
        "postgresql+psycopg2://x:x@1.1.1.1:5432/db?sslmode=require",
        {"name": "ok"},
    )


def test_sql_guard_allows_oracle_service_name_query() -> None:
    # _build_url emits ?service_name= for Oracle — must stay allowlisted.
    from connectors.sql_connector import _build_url, _guard_sql_connection_url
    from connectors.url_guard import OPT_IN_KEY

    url = _build_url(
        {
            "driver": "oracle+oracledb",
            "host": "10.0.0.8",
            "port": 1521,
            "user": "u",
            "pass": "p",
            "database": "ORCL",
            OPT_IN_KEY: True,
        }
    )
    assert "service_name=" in url
    _guard_sql_connection_url(url, {"name": "lab", OPT_IN_KEY: True})
