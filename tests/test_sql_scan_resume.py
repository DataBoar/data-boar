"""SQL/Snowflake per-table scan resume (#1330). Not filesystem identity (ADR-0051)."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from sqlalchemy import text

from connectors.sql_connector import SQLConnector
from core.database import LocalDBManager, ScanTableCheckpoint
from core.engine import AuditEngine


def test_scan_table_checkpoints_table_migrates_legacy_db(tmp_path) -> None:
    import sqlite3

    db_path = tmp_path / "legacy.db"
    con = sqlite3.connect(str(db_path))
    try:
        con.execute(
            "CREATE TABLE scan_sessions ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "session_id VARCHAR(64) NOT NULL UNIQUE,"
            "started_at DATETIME,"
            "finished_at DATETIME,"
            "status VARCHAR(20)"
            ")"
        )
        con.commit()
    finally:
        con.close()

    db = LocalDBManager(str(db_path))
    try:
        with db.engine.connect() as conn:
            names = {
                row[0]
                for row in conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table'")
                ).fetchall()
            }
        assert "scan_table_checkpoints" in names
    finally:
        db.dispose()


def test_completed_table_is_not_demoted_by_in_progress(tmp_path) -> None:
    db = LocalDBManager(str(tmp_path / "ck.db"))
    try:
        db.create_session_record("sess-1")
        db.set_current_session_id("sess-1")
        db.mark_sql_table_completed("lab-pg", "public", "done_tbl")
        db.mark_sql_table_in_progress("lab-pg", "public", "done_tbl")
        assert db.list_completed_sql_tables("lab-pg") == {("public", "done_tbl")}
        with db._session_factory() as s:
            rec = (
                s.query(ScanTableCheckpoint)
                .filter_by(session_id="sess-1", table_name="done_tbl")
                .one()
            )
            assert rec.status == "completed"
    finally:
        db.dispose()


def test_sql_connector_skips_completed_tables_on_resume(tmp_path, monkeypatch) -> None:
    db = LocalDBManager(str(tmp_path / "scan.db"))
    processed: list[str] = []
    try:
        db.create_session_record("sess-resume")
        db.set_current_session_id("sess-resume")
        db.mark_sql_table_completed("lab-pg", "public", "t1")

        target = {
            "name": "lab-pg",
            "type": "database",
            "driver": "sqlite",
            "database": ":memory:",
        }
        connector = SQLConnector(
            target,
            MagicMock(),
            db,
            sample_limit=1,
        )

        monkeypatch.setattr(connector, "connect", lambda: None)
        monkeypatch.setattr(connector, "close", lambda: None)
        monkeypatch.setattr(connector, "_save_inventory_snapshot", lambda *a, **k: None)
        monkeypatch.setattr(
            connector, "_save_crypto_controls_audit", lambda *a, **k: None
        )
        monkeypatch.setattr(
            connector, "_save_inferred_controls_summary", lambda *a, **k: None
        )
        monkeypatch.setattr(
            connector,
            "discover",
            lambda: [
                {
                    "schema": "public",
                    "table": "t1",
                    "columns": [{"name": "c1", "type": "TEXT"}],
                },
                {
                    "schema": "public",
                    "table": "t2",
                    "columns": [{"name": "c2", "type": "TEXT"}],
                },
            ],
        )

        def capture_process(
            _tn: str,
            _ip: str,
            _eng: str,
            _schema: str,
            table: str,
            _col: str,
            _typ: str,
            **_k: Any,
        ) -> None:
            processed.append(table)

        monkeypatch.setattr(connector, "_process_one_finding", capture_process)
        connector.engine = MagicMock()
        connector.engine.dialect.name = "sqlite"
        connector.run()
        assert processed == ["t2"]
        assert ("public", "t2") in db.list_completed_sql_tables("lab-pg")
        assert ("public", "t1") in db.list_completed_sql_tables("lab-pg")
    finally:
        db.dispose()


def test_mid_table_crash_does_not_mark_completed(tmp_path, monkeypatch) -> None:
    db = LocalDBManager(str(tmp_path / "crash.db"))
    try:
        db.create_session_record("sess-crash")
        db.set_current_session_id("sess-crash")
        target = {
            "name": "lab-pg",
            "type": "database",
            "driver": "sqlite",
            "database": ":memory:",
        }
        connector = SQLConnector(
            target,
            MagicMock(),
            db,
            sample_limit=1,
        )
        monkeypatch.setattr(connector, "connect", lambda: None)
        monkeypatch.setattr(connector, "close", lambda: None)
        monkeypatch.setattr(connector, "_save_inventory_snapshot", lambda *a, **k: None)
        monkeypatch.setattr(
            connector, "_save_crypto_controls_audit", lambda *a, **k: None
        )
        monkeypatch.setattr(
            connector, "_save_inferred_controls_summary", lambda *a, **k: None
        )
        monkeypatch.setattr(
            connector,
            "discover",
            lambda: [
                {
                    "schema": "public",
                    "table": "partial",
                    "columns": [
                        {"name": "a", "type": "TEXT"},
                        {"name": "b", "type": "TEXT"},
                    ],
                }
            ],
        )

        def boom_on_second(
            _tn: str,
            _ip: str,
            _eng: str,
            _schema: str,
            _table: str,
            cname: str,
            _typ: str,
            **_k: Any,
        ) -> None:
            if cname == "b":
                raise RuntimeError("died mid-table")

        monkeypatch.setattr(connector, "_process_one_finding", boom_on_second)
        connector.engine = MagicMock()
        connector.engine.dialect.name = "sqlite"
        connector.run()
        assert db.list_completed_sql_tables("lab-pg") == set()
        with db._session_factory() as s:
            rec = (
                s.query(ScanTableCheckpoint)
                .filter_by(session_id="sess-crash", table_name="partial")
                .one()
            )
            assert rec.status == "in_progress"
    finally:
        db.dispose()


def _engine_cfg() -> dict[str, Any]:
    return {
        "targets": [
            {
                "name": "files",
                "type": "filesystem",
                "path": "/tmp",
            }
        ],
        "file_scan": {"sample_limit": 5, "extensions": [".txt"]},
        "detection": {},
    }


def test_resume_completed_session_is_noop(tmp_path, monkeypatch) -> None:
    eng = AuditEngine(_engine_cfg(), db_path=str(tmp_path / "e.db"))
    try:
        eng.db_manager.create_session_record("done-sess")
        eng.db_manager.finish_session("done-sess", "completed")
        called: list[int] = []
        monkeypatch.setattr(eng, "_run_audit_targets", lambda: called.append(1))
        out = eng.start_audit(resume_session_id="done-sess")
        assert out == "done-sess"
        assert called == []
        assert eng.db_manager.get_session_status("done-sess") == "completed"
    finally:
        eng.db_manager.dispose()


def test_resume_unknown_session_raises(tmp_path) -> None:
    eng = AuditEngine(_engine_cfg(), db_path=str(tmp_path / "u.db"))
    try:
        with pytest.raises(ValueError, match="#1330"):
            eng.start_audit(resume_session_id="no-such-session")
    finally:
        eng.db_manager.dispose()
