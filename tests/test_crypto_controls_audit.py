"""Phase 2a/2c: crypto_controls_audit persistence + connector wiring + report sheet."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

import openpyxl

from connectors.mongodb_connector import MongoDBConnector
from connectors.redis_connector import RedisConnector
from connectors.smb_connector import SMBConnector
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


def test_mongodb_connect_honors_tls_flag() -> None:
    target = {
        "name": "mongo-tls",
        "host": "localhost",
        "port": 27017,
        "database": "test",
        "tls": True,
    }
    connector = MongoDBConnector(target, MagicMock(), MagicMock())
    with patch("connectors.mongodb_connector.MongoClient") as mongo_mock:
        with patch("connectors.mongodb_connector._MONGO_AVAILABLE", True):
            mongo_mock.return_value = MagicMock()
            connector.connect()
    assert connector._tls_enabled is True
    assert mongo_mock.call_args.kwargs.get("tls") is True


def test_redis_connect_honors_tls_and_cert_reqs() -> None:
    target = {
        "name": "redis-tls",
        "host": "localhost",
        "port": 6379,
        "tls": True,
        "ssl_cert_reqs": "required",
    }
    connector = RedisConnector(target, MagicMock(), MagicMock())
    fake_redis = MagicMock()
    fake_redis.Redis.return_value = MagicMock()
    with patch("connectors.redis_connector._REDIS_AVAILABLE", True):
        with patch("connectors.redis_connector.redis", fake_redis):
            connector.connect()
    assert connector._tls_enabled is True
    kwargs = fake_redis.Redis.call_args.kwargs
    assert kwargs.get("ssl") is True
    assert kwargs.get("ssl_cert_reqs") == "required"


def test_mongodb_connector_saves_crypto_audit_when_flag_on() -> None:
    target = {
        "name": "mongo-crypto",
        "host": "localhost",
        "port": 27017,
        "database": "test",
        "tls": True,
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
    client = MagicMock()
    client.__getitem__.return_value = MagicMock()
    client.__getitem__.return_value.list_collection_names.return_value = []
    client.__getitem__.return_value.command.return_value = {"version": "7.0.0"}
    connector = MongoDBConnector(target, scanner, db_manager)
    with patch("connectors.mongodb_connector.MongoClient", return_value=client):
        with patch("connectors.mongodb_connector._MONGO_AVAILABLE", True):
            connector.run()
    assert db_manager.save_crypto_controls_audit.called
    kwargs = db_manager.save_crypto_controls_audit.call_args.kwargs
    assert kwargs["target_name"] == "mongo-crypto"
    assert kwargs["connection_type"] == "mongodb"
    assert kwargs["strong_crypto_result"] in {
        "ok",
        "warning",
        "fail",
        "not_available",
        "not_applicable",
    }
    details = kwargs["strong_crypto_details"] or ""
    assert "password=" not in details.lower()


def test_redis_connector_saves_crypto_audit_when_flag_on() -> None:
    target = {
        "name": "redis-crypto",
        "host": "localhost",
        "port": 6379,
        "tls": False,
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
    client = MagicMock()
    client.info.return_value = {"redis_version": "7.2.0"}
    client.scan_iter.return_value = iter([])
    fake_redis = MagicMock()
    fake_redis.Redis.return_value = client
    connector = RedisConnector(target, scanner, db_manager)
    with patch("connectors.redis_connector._REDIS_AVAILABLE", True):
        with patch("connectors.redis_connector.redis", fake_redis):
            connector.run()
    assert db_manager.save_crypto_controls_audit.called
    kwargs = db_manager.save_crypto_controls_audit.call_args.kwargs
    assert kwargs["target_name"] == "redis-crypto"
    assert kwargs["connection_type"] == "redis"
    assert kwargs["strong_crypto_result"] == "fail"  # plaintext
    details = kwargs["strong_crypto_details"] or ""
    assert "password=" not in details.lower()


def test_smb_connect_honors_encrypt_and_signing() -> None:
    target = {
        "name": "smb-tls",
        "host": "files.example.com",
        "share": "data",
        "user": "u",
        "password": "p",
        "encrypt": True,
        "require_signing": True,
        "_validate_crypto": False,
    }
    scanner = MagicMock()
    db_manager = MagicMock()
    session = MagicMock()
    session.signing_required = True
    session.encrypt_data = True
    session.connection.dialect = 0x0311
    session.connection.supports_encryption = True
    fake_smb = MagicMock()
    fake_smb.register_session.return_value = session
    fake_smb.walk.return_value = []
    connector = SMBConnector(target, scanner, db_manager)
    with patch("connectors.smb_connector._SMB_AVAILABLE", True):
        with patch("connectors.smb_connector.smbclient", fake_smb):
            connector.run()
    kwargs = fake_smb.register_session.call_args.kwargs
    assert kwargs.get("encrypt") is True
    assert kwargs.get("require_signing") is True


def test_smb_connector_saves_crypto_audit_when_flag_on() -> None:
    secret = "must-not-appear-in-crypto-details"
    target = {
        "name": "smb-crypto",
        "host": "files.example.com",
        "share": "data",
        "user": "u",
        "password": secret,
        "encrypt": True,
        "_validate_crypto": True,
    }
    scanner = MagicMock()
    db_manager = MagicMock()
    session = MagicMock()
    session.signing_required = True
    session.encrypt_data = True
    session.connection.dialect = 0x0311
    session.connection.supports_encryption = True
    fake_smb = MagicMock()
    fake_smb.register_session.return_value = session
    fake_smb.walk.return_value = []
    connector = SMBConnector(target, scanner, db_manager)
    with patch("connectors.smb_connector._SMB_AVAILABLE", True):
        with patch("connectors.smb_connector.smbclient", fake_smb):
            connector.run()
    assert db_manager.save_crypto_controls_audit.called
    kwargs = db_manager.save_crypto_controls_audit.call_args.kwargs
    assert kwargs["target_name"] == "smb-crypto"
    assert kwargs["connection_type"] == "smb"
    assert kwargs["strong_crypto_result"] == "ok"
    details = kwargs["strong_crypto_details"] or ""
    assert secret not in details
    assert "password=" not in details.lower()


def test_smb_connector_skips_crypto_audit_when_flag_off() -> None:
    target = {
        "name": "smb-off",
        "host": "files.example.com",
        "share": "data",
        "user": "u",
        "password": "p",
        "_validate_crypto": False,
    }
    scanner = MagicMock()
    db_manager = MagicMock()
    session = MagicMock()
    fake_smb = MagicMock()
    fake_smb.register_session.return_value = session
    fake_smb.walk.return_value = []
    connector = SMBConnector(target, scanner, db_manager)
    with patch("connectors.smb_connector._SMB_AVAILABLE", True):
        with patch("connectors.smb_connector.smbclient", fake_smb):
            connector.run()
    assert not db_manager.save_crypto_controls_audit.called


def test_mongodb_connector_skips_crypto_audit_when_flag_off() -> None:
    target = {
        "name": "mongo-off",
        "host": "localhost",
        "database": "test",
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
    client = MagicMock()
    client.__getitem__.return_value = MagicMock()
    client.__getitem__.return_value.list_collection_names.return_value = []
    client.__getitem__.return_value.command.return_value = {"version": "7.0.0"}
    connector = MongoDBConnector(target, scanner, db_manager)
    with patch("connectors.mongodb_connector.MongoClient", return_value=client):
        with patch("connectors.mongodb_connector._MONGO_AVAILABLE", True):
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
