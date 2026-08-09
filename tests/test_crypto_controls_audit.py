"""Phase 2a: crypto_controls_audit persistence + SQL probe wiring + report sheet."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest.mock import MagicMock

import openpyxl

from connectors.sql_connector import SQLConnector
from core.crypto_audit import collect_sql_crypto_facts
from core.database import LocalDBManager
from report.generator import generate_report


def test_crypto_controls_audit_save_and_get(tmp_path: Path) -> None:
    db_path = str(tmp_path / "crypto_audit.db")
    mgr = LocalDBManager(db_path)
    try:
        mgr.set_current_session_id("crypto-sess-1")
        mgr.create_session_record("crypto-sess-1")
        mgr.save_crypto_controls_audit(
            target_name="pg-main",
            connection_type="database",
            strong_crypto_result="ok",
            strong_crypto_details="source=pg_stat_ssl; tls=TLSv1.3",
        )
        rows = mgr.get_crypto_controls_audit("crypto-sess-1")
        assert len(rows) == 1
        assert rows[0]["target_name"] == "pg-main"
        assert rows[0]["strong_crypto_result"] == "ok"
        assert "TLSv1.3" in (rows[0]["strong_crypto_details"] or "")
        assert rows[0]["inferred_controls_summary"] is None
    finally:
        mgr.dispose()


def test_crypto_controls_audit_table_created_on_init(tmp_path: Path) -> None:
    """LocalDBManager ensures crypto_controls_audit exists."""
    from sqlalchemy import text

    db_path = str(tmp_path / "legacy.db")
    mgr = LocalDBManager(db_path)
    try:
        with mgr.engine.connect() as c:
            names = {
                row[0]
                for row in c.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
        assert "crypto_controls_audit" in names
    finally:
        mgr.dispose()


def test_collect_sql_crypto_facts_sqlite() -> None:
    from sqlalchemy import create_engine

    eng = create_engine("sqlite:///:memory:")
    facts = collect_sql_crypto_facts(eng, {"name": "local"})
    assert facts.source == "sqlite"


def test_collect_sql_crypto_facts_postgres_pg_stat_ssl() -> None:
    """Mock SQLAlchemy connect/execute to simulate pg_stat_ssl row."""

    class _FakeResult:
        def fetchone(self):
            return (True, "TLSv1.3", "ECDHE-RSA-AES256-GCM-SHA384")

    class _FakeConn:
        def execute(self, *_a, **_k):
            return _FakeResult()

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    class _FakeDialect:
        name = "postgresql"

    class _FakeEngine:
        dialect = _FakeDialect()

        def connect(self):
            return _FakeConn()

    facts = collect_sql_crypto_facts(
        _FakeEngine(), {"sslmode": "verify-full", "name": "pg"}
    )
    assert facts.source == "pg_stat_ssl"
    assert facts.tls_in_use is True
    assert facts.tls_version == "TLSv1.3"
    assert facts.sslmode == "verify-full"


def test_sql_connector_saves_crypto_audit_when_flag_on(tmp_path: Path) -> None:
    db_path = tmp_path / "scan.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE t1 (a TEXT)")
    conn.execute("INSERT INTO t1 VALUES ('x')")
    conn.commit()
    conn.close()

    target = {
        "type": "database",
        "driver": "sqlite",
        "database": str(db_path),
        "name": "SQLiteCrypto",
        "_validate_crypto": True,
    }
    scanner = MagicMock()
    scanner.scan_column.return_value = {
        "sensitivity_level": "LOW",
        "pattern_detected": "NONE",
        "norm_tag": "",
        "ml_confidence": 0,
    }
    db_manager = MagicMock()
    connector = SQLConnector(target, scanner, db_manager)
    connector.run()

    assert db_manager.save_crypto_controls_audit.called
    kwargs = db_manager.save_crypto_controls_audit.call_args.kwargs
    assert kwargs["target_name"] == "SQLiteCrypto"
    assert kwargs["connection_type"] == "database"
    assert kwargs["strong_crypto_result"] == "not_applicable"


def test_sql_connector_skips_crypto_audit_when_flag_off(tmp_path: Path) -> None:
    db_path = tmp_path / "scan_off.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE t1 (a TEXT)")
    conn.commit()
    conn.close()

    target = {
        "type": "database",
        "driver": "sqlite",
        "database": str(db_path),
        "name": "SQLiteOff",
        "_validate_crypto": False,
    }
    scanner = MagicMock()
    scanner.scan_column.return_value = {
        "sensitivity_level": "LOW",
        "pattern_detected": "NONE",
        "norm_tag": "",
        "ml_confidence": 0,
    }
    db_manager = MagicMock()
    connector = SQLConnector(target, scanner, db_manager)
    connector.run()

    assert not db_manager.save_crypto_controls_audit.called


def test_generate_report_includes_crypto_controls_sheet(tmp_path: Path) -> None:
    out_dir = str(tmp_path / "out")
    Path(out_dir).mkdir()
    db_path = str(tmp_path / "report.db")
    mgr = LocalDBManager(db_path)
    try:
        mgr.set_current_session_id("rep-crypto")
        mgr.create_session_record("rep-crypto")
        mgr.save_finding(
            "database",
            target_name="T1",
            column_name="email",
            sensitivity_level="LOW",
            pattern_detected="EMAIL",
            norm_tag="",
            ml_confidence=10,
        )
        mgr.save_crypto_controls_audit(
            target_name="pg1",
            connection_type="database",
            strong_crypto_result="warning",
            strong_crypto_details="source=config_sslmode; sslmode=require",
        )
        mgr.finish_session("rep-crypto")
        path = generate_report(mgr, "rep-crypto", output_dir=out_dir, config={})
        assert path
        wb = openpyxl.load_workbook(path)
        assert "Crypto & controls" in wb.sheetnames
        ws = wb["Crypto & controls"]
        values = [[c.value for c in row] for row in ws.iter_rows(min_row=1, max_row=4)]
        assert values[0][0] == "Target"
        assert any(row[0] == "pg1" for row in values[1:])
        assert any(row[2] == "warning" for row in values[1:])
    finally:
        mgr.dispose()


def test_generate_report_omits_crypto_sheet_when_no_rows(tmp_path: Path) -> None:
    out_dir = str(tmp_path / "out2")
    Path(out_dir).mkdir()
    db_path = str(tmp_path / "report2.db")
    mgr = LocalDBManager(db_path)
    try:
        mgr.set_current_session_id("rep-empty")
        mgr.create_session_record("rep-empty")
        mgr.save_finding(
            "database",
            target_name="T1",
            column_name="email",
            sensitivity_level="LOW",
            pattern_detected="EMAIL",
            norm_tag="",
            ml_confidence=10,
        )
        mgr.finish_session("rep-empty")
        path = generate_report(mgr, "rep-empty", output_dir=out_dir, config={})
        assert path
        wb = openpyxl.load_workbook(path)
        assert "Crypto & controls" not in wb.sheetnames
    finally:
        mgr.dispose()
