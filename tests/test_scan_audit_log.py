"""Declarative ``audit_log`` / ``build_scan_audit_log`` (sampling + SRE posture)."""

from core.scan_audit_log import build_scan_audit_log


def test_audit_log_strategy_sampling_and_row_cap() -> None:
    log = build_scan_audit_log(
        {
            "targets": [],
            "file_scan": {"sample_limit": 10},
        }
    )
    assert log["strategy"] == "sampling"
    assert log["sampling_row_cap_per_column"] >= 1
    assert log["nolock"] is False


def test_audit_log_nolock_when_sql_server_driver() -> None:
    log = build_scan_audit_log(
        {
            "targets": [
                {
                    "type": "database",
                    "name": "legacy",
                    "driver": "mssql+pyodbc",
                }
            ],
            "file_scan": {"sample_limit": 5},
        }
    )
    assert log["nolock"] is True
    assert any(
        t.get("driver", "").lower().find("mssql") >= 0
        for t in log.get("database_targets_drivers", [])
    )


def test_audit_log_postgres_and_timeout_seconds() -> None:
    log = build_scan_audit_log(
        {
            "targets": [
                {
                    "type": "database",
                    "name": "pg1",
                    "driver": "postgresql+psycopg2",
                    "sample_statement_timeout_ms": 2000,
                }
            ],
            "file_scan": {"sample_limit": 50},
        }
    )
    assert log["postgresql_tablesample_on_large_tables"] is True
    assert log["statement_timeout_ms"] == 2000
    assert log["statement_timeout_seconds"] == 2.0
