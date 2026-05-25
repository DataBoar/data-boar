"""Tests for config loader and database layer (no live DB required)."""

import logging
import os
import time
import pytest
from pathlib import Path

from config.loader import load_config, normalize_config
from core.database import DataSourceInventory, DataWipeLog, LocalDBManager, failure_hint


def test_scan_scope_key_emits_warning(caplog):
    """normalize_config warns on obsolete 'scan_scope:' key (AGENTS.md workspace fact)."""
    with caplog.at_level(logging.WARNING, logger="config.loader"):
        normalize_config({"scan_scope": [{"type": "filesystem", "path": "/tmp"}]})
    joined = " ".join(r.message for r in caplog.records)
    assert "scan_scope" in joined
    assert "targets" in joined


def test_normalize_config_empty():
    out = normalize_config({"targets": []})
    assert out["targets"] == []
    assert "file_scan" in out
    assert out["api"].get("port") == 8088
    assert out.get("sql_sampling") == {
        "overrides": {"targets": {}, "patterns": {}},
    }
    assert out.get("sql_sampling_file") == ""
    assert out.get("sql_sampling_files") == []


def test_normalize_config_sql_sampling_overrides():
    out = normalize_config(
        {
            "targets": [],
            "report": {"output_dir": "."},
            "sql_sampling": {
                "overrides": {
                    "targets": {
                        "legacy_oracle": {
                            "sample_limit": 5,
                            "tables": {"PROD.USERS": 99},
                        }
                    },
                    "patterns": {"*_audit": 100, "bad": -1, "nope": "x"},
                },
            },
        }
    )
    sql = out["sql_sampling"]
    assert sql["overrides"]["targets"]["legacy_oracle"]["sample_limit"] == 5
    assert sql["overrides"]["targets"]["legacy_oracle"]["tables"]["PROD.USERS"] == 99
    assert sql["overrides"]["patterns"]["*_audit"] == 100
    assert "bad" not in sql["overrides"]["patterns"]
    assert "nope" not in sql["overrides"]["patterns"]


def test_normalize_config_sets_unique_audit_log_names():
    out = normalize_config(
        {
            "targets": [
                {"name": "db|one", "type": "database", "host": "h"},
                {"name": "db|one", "type": "database", "host": "h2"},
            ],
            "report": {"output_dir": "."},
        }
    )
    names = [t["audit_log_name"] for t in out["targets"]]
    assert names[0] == "db_one"
    assert names[1] == "db_one__2"
    assert len(set(names)) == 2


def test_normalize_config_legacy_databases():
    # Use placeholder for password field; test only verifies normalization (no real credentials).
    out = normalize_config(
        {
            "databases": [
                {
                    "name": "x",
                    "host": "h",
                    "port": 5432,
                    "user": "u",
                    "password": os.environ.get("TEST_DB_PASSWORD", "test-placeholder"),
                    "database": "d",
                }
            ],
            "file_scan": {"directories": [], "extensions": [".txt"]},
        }
    )
    assert len(out["targets"]) >= 1
    db_target = next(t for t in out["targets"] if t.get("type") == "database")
    assert db_target["name"] == "x"
    assert db_target["host"] == "h"
    assert db_target["database"] == "d"


def test_normalize_config_detection_aggregated_identification():
    """Config loader normalizes detection.aggregated_identification_enabled, aggregated_min_categories, quasi_identifier_mapping."""
    out = normalize_config(
        {
            "targets": [],
            "detection": {
                "aggregated_identification_enabled": False,
                "aggregated_min_categories": 3,
                "quasi_identifier_mapping": [
                    {"column_pattern": "cargo", "category": "job_position"},
                    {"pattern_detected": "PHONE_BR", "category": "phone"},
                ],
            },
        }
    )
    det = out.get("detection", {})
    assert det.get("aggregated_identification_enabled") is False
    assert det.get("aggregated_min_categories") == 3
    assert len(det.get("quasi_identifier_mapping", [])) == 2
    assert det["quasi_identifier_mapping"][0]["category"] == "job_position"
    assert det["quasi_identifier_mapping"][1]["category"] == "phone"

    # Defaults when detection section is missing or empty
    out2 = normalize_config({"targets": []})
    det2 = out2.get("detection", {})
    assert det2.get("aggregated_identification_enabled") is True
    assert det2.get("aggregated_min_categories") == 2
    assert det2.get("quasi_identifier_mapping") == []


def test_normalize_config_rate_limit_and_scan_max_workers(monkeypatch):
    """Config loader normalizes rate_limit block and clamps scan.max_workers."""
    # No env overrides
    cfg = normalize_config(
        {
            "targets": [],
            "scan": {"max_workers": 100},
            "rate_limit": {
                "enabled": True,
                "max_concurrent_scans": 0,  # should be clamped to >= 1
                "min_interval_seconds": -10,  # should be clamped to >= 0
                "grace_for_running_status": -5,  # should be clamped to >= 0
            },
        }
    )
    rl = cfg.get("rate_limit", {})
    assert rl.get("enabled") is True
    assert rl.get("max_concurrent_scans") >= 1
    assert rl.get("min_interval_seconds") >= 0
    assert rl.get("grace_for_running_status") >= 0
    # max_workers capped to a safe upper bound
    assert cfg.get("scan", {}).get("max_workers") <= 32


def test_normalize_config_timeouts_and_per_target():
    """Config loader adds global timeouts (defaults 25/90) and merges per-target overrides."""
    out = normalize_config(
        {
            "targets": [
                {
                    "name": "defaults",
                    "type": "database",
                    "driver": "postgresql",
                    "host": "h",
                    "database": "d",
                },
                {
                    "name": "overrides",
                    "type": "api",
                    "base_url": "http://x",
                    "connect_timeout": 10,
                    "read_timeout": 60,
                },
                {
                    "name": "single",
                    "type": "database",
                    "driver": "mysql",
                    "host": "h",
                    "database": "d",
                    "timeout": 45,
                },
            ],
            "timeouts": {"connect_seconds": 20, "read_seconds": 80},
        }
    )
    assert out.get("timeouts", {}).get("connect_seconds") == 20
    assert out.get("timeouts", {}).get("read_seconds") == 80
    targets = out["targets"]
    t0 = next(t for t in targets if t.get("name") == "defaults")
    assert (
        t0.get("connect_timeout_seconds") == 20 and t0.get("read_timeout_seconds") == 80
    )
    t1 = next(t for t in targets if t.get("name") == "overrides")
    assert (
        t1.get("connect_timeout_seconds") == 10 and t1.get("read_timeout_seconds") == 60
    )
    t2 = next(t for t in targets if t.get("name") == "single")
    assert (
        t2.get("connect_timeout_seconds") == 45 and t2.get("read_timeout_seconds") == 45
    )
    # Empty config: defaults 25/90
    out2 = normalize_config({"targets": []})
    assert out2.get("timeouts", {}).get("connect_seconds") == 25
    assert out2.get("timeouts", {}).get("read_seconds") == 90


def test_failure_hint_timeout_includes_config_guidance():
    """failure_hint('timeout') points operators to config timeouts and USAGE (Phase 4.2)."""
    hint = failure_hint("timeout")
    assert "timeout" in hint.lower()
    assert "USAGE" in hint or "timeouts" in hint
    assert "connect" in hint.lower() or "read" in hint.lower()


def test_failure_hint_other_reasons():
    """failure_hint returns sensible hints for unreachable, auth_failed, permission_denied."""
    assert (
        "connectivity" in failure_hint("unreachable").lower()
        or "network" in failure_hint("unreachable").lower()
    )
    assert "auth" in failure_hint("auth_failed").lower()
    assert "permission" in failure_hint("permission_denied").lower()
    assert (
        "unexpected" in failure_hint("unknown").lower()
        or "error" in failure_hint("unknown").lower()
    )


def test_local_db_manager(tmp_path):
    db_path = str(tmp_path / "test_audit.db")
    mgr = LocalDBManager(db_path)
    try:
        mgr.set_current_session_id("test-session-123")
        mgr.create_session_record("test-session-123")
        mgr.save_finding(
            "database",
            target_name="T",
            server_ip="127.0.0.1",
            schema_name="s",
            table_name="t",
            column_name="c",
            data_type="VARCHAR",
            sensitivity_level="HIGH",
            pattern_detected="CPF",
            norm_tag="LGPD",
            ml_confidence=90,
        )
        db_findings, _, _ = mgr.get_findings("test-session-123")
        assert len(db_findings) == 1
        assert db_findings[0]["column_name"] == "c"
        mgr.finish_session("test-session-123")
        sessions = mgr.list_sessions()
        assert any(s["session_id"] == "test-session-123" for s in sessions)
        assert "scan_failures" in sessions[0]
    finally:
        mgr.dispose()


def test_data_source_inventory_save_and_get(tmp_path):
    db_path = str(tmp_path / "test_inventory.db")
    mgr = LocalDBManager(db_path)
    try:
        mgr.set_current_session_id("inv-session-1")
        mgr.create_session_record("inv-session-1")
        mgr.save_data_source_inventory(
            target_name="pg-main",
            source_type="database",
            product="postgresql",
            product_version="PostgreSQL 16.2",
            protocol_or_api_version="postgresql",
            transport_security="sslmode=require",
            raw_details='{"driver":"postgresql"}',
        )
        rows = mgr.get_data_source_inventory("inv-session-1")
        assert len(rows) == 1
        assert rows[0]["target_name"] == "pg-main"
        assert rows[0]["product"] == "postgresql"
        assert rows[0]["transport_security"] == "sslmode=require"
    finally:
        mgr.dispose()


def test_get_previous_session(tmp_path):
    db_path = str(tmp_path / "test_prev.db")
    mgr = LocalDBManager(db_path)
    try:
        mgr.set_current_session_id("session-first")
        mgr.create_session_record("session-first")
        mgr.save_finding(
            "database",
            target_name="T",
            session_id="session-first",
            column_name="c1",
            sensitivity_level="HIGH",
            pattern_detected="CPF",
            norm_tag="LGPD",
            ml_confidence=80,
        )
        mgr.finish_session("session-first")
        mgr.set_current_session_id("session-second")
        mgr.create_session_record("session-second")
        mgr.save_finding(
            "database",
            target_name="T",
            session_id="session-second",
            column_name="c2",
            sensitivity_level="HIGH",
            pattern_detected="EMAIL",
            norm_tag="GDPR",
            ml_confidence=85,
        )
        mgr.finish_session("session-second")
        prev = mgr.get_previous_session("session-second")
        assert prev is not None
        assert prev["session_id"] == "session-first"
        assert prev["database_findings"] == 1
        assert mgr.get_previous_session("session-first") is None
    finally:
        mgr.dispose()


def test_running_sessions_count_and_last_session(tmp_path):
    """LocalDBManager helpers for rate limiting: running count and last session metadata."""
    db_path = str(tmp_path / "test_running.db")
    mgr = LocalDBManager(db_path)
    try:
        # No sessions yet
        assert mgr.get_running_sessions_count() == 0
        assert mgr.get_last_session() is None

        # First session: running
        mgr.set_current_session_id("s1")
        mgr.create_session_record("s1")
        running_count = mgr.get_running_sessions_count()
        assert running_count == 1
        last = mgr.get_last_session()
        assert last is not None
        assert last["session_id"] == "s1"
        assert last["status"] == "running"

        # Mark as completed and add a newer running session
        mgr.finish_session("s1")
        mgr.set_current_session_id("s2")
        mgr.create_session_record("s2")
        running_count2 = mgr.get_running_sessions_count()
        assert running_count2 == 1  # only s2 is running
        last2 = mgr.get_last_session()
        assert last2 is not None
        assert last2["session_id"] == "s2"
        assert last2["status"] == "running"
    finally:
        mgr.dispose()


def test_wipe_all_data_logs_and_clears(tmp_path):
    db_path = str(tmp_path / "test_wipe.db")
    mgr = LocalDBManager(db_path)
    try:
        # Create two sessions with findings
        mgr.set_current_session_id("s1")
        mgr.create_session_record("s1")
        mgr.save_finding(
            "database",
            target_name="T1",
            schema_name="s",
            table_name="t",
            column_name="c1",
            data_type="VARCHAR",
            sensitivity_level="HIGH",
            pattern_detected="CPF",
            norm_tag="LGPD",
            ml_confidence=90,
        )
        mgr.finish_session("s1")

        mgr.set_current_session_id("s2")
        mgr.create_session_record("s2")
        mgr.save_finding(
            "database",
            target_name="T2",
            schema_name="s",
            table_name="t",
            column_name="c2",
            data_type="VARCHAR",
            sensitivity_level="HIGH",
            pattern_detected="EMAIL",
            norm_tag="GDPR",
            ml_confidence=85,
        )
        mgr.finish_session("s2")
        mgr.save_data_source_inventory(
            target_name="db-host",
            source_type="database",
            product="sqlite",
            product_version="3.x",
        )
        mgr.save_maturity_assessment_answers(
            batch_id="batch-wipe-test",
            locale_slug="en",
            pack_version=1,
            answers={"q1": "yes", "q2": "no"},
        )
        assert mgr.count_maturity_assessment_answers() == 2

        # Sanity check: we have sessions and findings
        assert mgr.list_sessions()
        db_rows, _, _ = mgr.get_findings("s1")
        assert db_rows

        # Wipe everything and ensure sessions/findings are gone but a wipe log exists
        mgr.wipe_all_data("pytest wipe")

        sessions_after = mgr.list_sessions()
        assert sessions_after == []
        assert mgr.count_maturity_assessment_answers() == 0

        # Directly inspect DataWipeLog via a new session factory
        s = mgr._session_factory()
        try:
            wipes = s.query(DataWipeLog).all()
            assert len(wipes) == 1
            assert "pytest wipe" in wipes[0].reason
            inventories = s.query(DataSourceInventory).all()
            assert inventories == []
        finally:
            s.close()
    finally:
        mgr.dispose()


def test_maturity_assessment_batch_summaries_newest_first(tmp_path):
    db_path = str(tmp_path / "batch_hist.db")
    mgr = LocalDBManager(db_path)
    try:
        mgr.save_maturity_assessment_answers(
            batch_id="a" * 32,
            locale_slug="en",
            pack_version=1,
            answers={"q1": "yes"},
        )
        time.sleep(0.05)
        mgr.save_maturity_assessment_answers(
            batch_id="b" * 32,
            locale_slug="en",
            pack_version=1,
            answers={"q2": "no"},
        )
        rows = mgr.maturity_assessment_batch_summaries(limit=10)
        assert len(rows) == 2
        assert rows[0]["batch_id"] == "b" * 32
        assert rows[1]["batch_id"] == "a" * 32
        assert rows[0]["answer_count"] == 1
    finally:
        mgr.dispose()


def test_normalize_config_notifications_defaults():
    out = normalize_config({"targets": []})
    assert "notifications" in out
    assert out["notifications"]["enabled"] is False
    assert out["notifications"]["operator"]["slack_webhook_url"] is None
    assert out["notifications"]["operator"]["channels"] == []
    assert out["notifications"]["tenant"]["by_tenant"] == {}
    assert out["notifications"]["dedupe_scan_complete_per_session"] is True
    assert out["notifications"]["notify_audit_log"] is True


def test_normalize_config_notifications_env(monkeypatch):
    monkeypatch.setenv("TEST_NOTIFY_SLACK", "https://hooks.example/test")
    out = normalize_config(
        {
            "targets": [],
            "notifications": {
                "enabled": True,
                "operator": {"slack_webhook_url": "${TEST_NOTIFY_SLACK}"},
            },
        }
    )
    assert (
        out["notifications"]["operator"]["slack_webhook_url"]
        == "https://hooks.example/test"
    )


def test_get_session_scan_summary_for_notification(tmp_path):
    db = tmp_path / "notify_sum.db"
    mgr = LocalDBManager(str(db))
    mgr.set_current_session_id("n1")
    mgr.create_session_record("n1", tenant_name="ACME", technician_name="op")
    mgr.save_finding(
        "database",
        target_name="T",
        schema_name="s",
        table_name="t",
        column_name="c",
        data_type="VARCHAR",
        sensitivity_level="HIGH",
        pattern_detected="DOB_POSSIBLE_MINOR, CPF",
        norm_tag="LGPD",
        ml_confidence=80,
    )
    mgr.save_failure("x", "timeout", "slow")
    mgr.finish_session("n1", "completed")
    s = mgr.get_session_scan_summary_for_notification("n1")
    assert s["high"] == 1
    assert s["dob_possible_minor"] >= 1
    assert s["scan_failures"] == 1
    assert s["tenant_name"] == "ACME"
    assert s["status"] == "completed"


def test_save_failure_persists_sanitized_details_no_raw_pii(tmp_path):
    """scan_failures.details must not store raw CPF, emails, or URL passwords (SQLite audit)."""
    from sqlalchemy import text

    dbp = tmp_path / "scan_fail_redact.db"
    mgr = LocalDBManager(str(dbp))
    sid = "sess-redact-1"
    mgr.set_current_session_id(sid)
    mgr.create_session_record(sid, tenant_name="ACME", technician_name="op")
    raw = (
        "DriverException: row operator@client.com CPF 529.982.247-25 "
        "postgresql://app:SuperSecret@db:5432/internals"
    )
    mgr.save_failure("target-a", "error", raw)
    with mgr.engine.connect() as conn:
        row = conn.execute(
            text("SELECT details FROM scan_failures WHERE session_id=:sid"),
            {"sid": sid},
        ).fetchone()
    assert row and row[0]
    stored = row[0]
    assert "529.982.247-25" not in stored
    assert "operator@client.com" not in stored
    assert "SuperSecret" not in stored
    assert "***REDACTED***" in stored


def test_notification_send_log_table(tmp_path):
    """notification_send_log is created and record_notification_send_log is append-only."""
    from sqlalchemy import text

    db = tmp_path / "audit_notify.db"
    mgr = LocalDBManager(str(db))
    mgr.record_notification_send_log(
        session_id="sess_a",
        trigger="scan_complete",
        recipient="operator",
        channel="slack",
        success=True,
        error_message=None,
    )
    mgr.record_notification_send_log(
        session_id=None,
        trigger="manual",
        recipient="operator",
        channel="slack",
        success=False,
        error_message="connection reset",
    )
    with mgr.engine.connect() as conn:
        n = conn.execute(text("SELECT COUNT(*) FROM notification_send_log")).scalar()
        assert n == 2


def test_load_config_file(config_path=None):
    path = Path("config.yaml")
    if not path.exists():
        path = Path("config/config.json")
    if not path.exists():
        pytest.skip("No config.yaml or config/config.json")
    config = load_config(path)
    assert "targets" in config
    assert "file_scan" in config


# ---------------------------------------------------------------------------
# Phase 1 incremental-scan schema: file-identity fields on FilesystemFinding
# ---------------------------------------------------------------------------


def test_localdbmanager_migrates_filesystem_findings_columns(tmp_path):
    """Legacy filesystem_findings tables gain Phase 1 columns on LocalDBManager init."""
    from sqlalchemy import create_engine, text

    from core.database import LocalDBManager

    db_path = str(tmp_path / "legacy_fs_findings.db")
    engine = create_engine(f"sqlite:///{db_path}")
    with engine.connect() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE filesystem_findings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id VARCHAR(64) NOT NULL,
                    target_name VARCHAR(100),
                    path VARCHAR(512),
                    file_name VARCHAR(255),
                    data_type VARCHAR(50),
                    sensitivity_level VARCHAR(20),
                    pattern_detected VARCHAR(100),
                    norm_tag VARCHAR(100),
                    ml_confidence INTEGER,
                    created_at DATETIME
                )
                """
            )
        )
        conn.commit()
    engine.dispose()

    mgr = LocalDBManager(db_path)
    try:
        with mgr.engine.connect() as conn:
            for col in ("source_mtime_ns", "source_size", "content_fingerprint"):
                r = conn.execute(
                    text(
                        "SELECT 1 FROM pragma_table_info('filesystem_findings') "
                        f"WHERE name='{col}'"
                    )
                )
                assert r.fetchone() is not None, f"missing column {col}"
    finally:
        mgr.dispose()


def test_filesystem_finding_has_file_identity_columns(tmp_path):
    """FilesystemFinding rows accept and persist source_mtime_ns, source_size,
    content_fingerprint — Phase 1 of incremental scan (ADR-0051).
    """
    from core.database import LocalDBManager

    db_path = str(tmp_path / "identity_test.db")
    mgr = LocalDBManager(db_path)
    try:
        session_id = "idem-test-001"
        mgr.set_current_session_id(session_id)
        mgr.create_session_record(session_id)
        mgr.save_finding(
            "filesystem",
            target_name="target-docs",
            path="/tmp/docs",
            file_name="test.txt",
            data_type="TXT",
            sensitivity_level="HIGH",
            pattern_detected="CPF",
            norm_tag="LGPD",
            ml_confidence=80,
            source_mtime_ns=1_700_000_000_000_000_000,
            source_size=1024,
            content_fingerprint="abcdef0123456789",
        )
        _, fs_findings, _ = mgr.get_findings(session_id)
        assert len(fs_findings) == 1
        f = fs_findings[0]
        assert f.get("source_mtime_ns") == 1_700_000_000_000_000_000
        assert f.get("source_size") == 1024
        assert f.get("content_fingerprint") == "abcdef0123456789"
    finally:
        mgr.dispose()


def test_filesystem_finding_identity_nullable(tmp_path):
    """FilesystemFinding rows without file-identity fields (legacy behaviour)
    remain valid — fields are nullable (ADR-0051 backward-compat).
    """
    from core.database import LocalDBManager

    db_path = str(tmp_path / "identity_null_test.db")
    mgr = LocalDBManager(db_path)
    try:
        session_id = "idem-test-null"
        mgr.set_current_session_id(session_id)
        mgr.create_session_record(session_id)
        mgr.save_finding(
            "filesystem",
            target_name="target-docs",
            path="/tmp/docs",
            file_name="legacy.txt",
            data_type="TXT",
            sensitivity_level="MEDIUM",
            pattern_detected="EMAIL",
            norm_tag="",
            ml_confidence=0,
            # No source_mtime_ns / source_size / content_fingerprint
        )
        _, fs_findings, _ = mgr.get_findings(session_id)
        assert len(fs_findings) == 1
        f = fs_findings[0]
        assert f.get("source_mtime_ns") is None
        assert f.get("source_size") is None
        assert f.get("content_fingerprint") is None
    finally:
        mgr.dispose()


def test_file_content_fingerprint_helper():
    """_file_content_fingerprint returns a 16-char hex string for non-empty bytes."""
    from connectors.filesystem_connector import _file_content_fingerprint

    fp = _file_content_fingerprint(b"hello world")
    assert fp is not None
    assert len(fp) == 16
    assert all(c in "0123456789abcdef" for c in fp)
    # Same input -> same fingerprint (deterministic)
    assert _file_content_fingerprint(b"hello world") == fp
    # Different input -> different fingerprint (with overwhelming probability)
    assert _file_content_fingerprint(b"hello worl!") != fp
    # None/empty -> None
    assert _file_content_fingerprint(None) is None  # type: ignore[arg-type]
    assert _file_content_fingerprint(b"") is None


# ---------------------------------------------------------------------------
# Phase 2 — ScanObjectState table + upsert_object_state / get_object_state
# ---------------------------------------------------------------------------


def test_scan_object_state_upsert_insert(tmp_path):
    """upsert_object_state inserts a new row when the path is unseen."""
    from core.database import LocalDBManager

    db = LocalDBManager(str(tmp_path / "ph2.db"))
    db.set_current_session_id("sess-001")
    db.create_session_record("sess-001")
    try:
        db.upsert_object_state(
            target_name="tgt-a",
            abs_path="/data/file.txt",
            session_id="sess-001",
            mtime_ns=1_700_000_000_000_000_000,
            size=512,
            content_fingerprint="aabbccdd00112233",
            sensitivity_level="HIGH",
        )
        row = db.get_object_state("tgt-a", "/data/file.txt")
        assert row is not None
        assert row["last_session_id"] == "sess-001"
        assert row["mtime_ns"] == 1_700_000_000_000_000_000
        assert row["size"] == 512
        assert row["content_fingerprint"] == "aabbccdd00112233"
        assert row["last_sensitivity"] == "HIGH"
    finally:
        db.dispose()


def test_scan_object_state_upsert_update(tmp_path):
    """upsert_object_state updates the existing row on repeat (same path, new session)."""
    from core.database import LocalDBManager

    db = LocalDBManager(str(tmp_path / "ph2_update.db"))
    db.set_current_session_id("sess-001")
    db.create_session_record("sess-001")
    try:
        db.upsert_object_state(
            "tgt", "/data/x.csv", "sess-001", 1_000, 100, "abc", "LOW"
        )
        db.upsert_object_state(
            "tgt", "/data/x.csv", "sess-002", 2_000, 200, "xyz", "HIGH"
        )

        row = db.get_object_state("tgt", "/data/x.csv")
        assert row is not None
        # Row must be updated, not doubled.
        assert row["last_session_id"] == "sess-002"
        assert row["mtime_ns"] == 2_000
        assert row["content_fingerprint"] == "xyz"
        assert row["last_sensitivity"] == "HIGH"
    finally:
        db.dispose()


def test_scan_object_state_no_double_rows(tmp_path):
    """Repeated upserts must not create duplicate rows."""
    from core.database import LocalDBManager, ScanObjectState

    db = LocalDBManager(str(tmp_path / "ph2_no_dup.db"))
    db.set_current_session_id("sess-001")
    db.create_session_record("sess-001")
    try:
        for i in range(3):
            db.upsert_object_state(
                "tgt", "/data/dup.txt", f"sess-{i}", i, i * 10, None, None
            )

        with db._session_factory() as s:
            count = (
                s.query(ScanObjectState)
                .filter_by(target_name="tgt", abs_path="/data/dup.txt")
                .count()
            )
        assert count == 1
    finally:
        db.dispose()


def test_get_object_state_missing_returns_none(tmp_path):
    """get_object_state returns None for an unknown (target, path) pair."""
    from core.database import LocalDBManager

    db = LocalDBManager(str(tmp_path / "ph2_missing.db"))
    try:
        result = db.get_object_state("nonexistent", "/nowhere.txt")
        assert result is None
    finally:
        db.dispose()
