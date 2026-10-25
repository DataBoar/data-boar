"""Tests for live scan progress reporting (#1328)."""

from __future__ import annotations

import io
from typing import Any

from core.scan_progress import (
    ScanProgress,
    ScanProgressConfig,
    scan_progress_from_config,
)


class _FakeClock:
    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += seconds


def test_scan_progress_disabled_emits_nothing() -> None:
    buf = io.StringIO()
    prog = ScanProgress(ScanProgressConfig(enabled=False), stream=buf)
    prog.start_run(2)
    prog.begin_target(1, "db1")
    prog.set_tables_total(10)
    prog.advance_table(1, table_label="public.users")
    assert buf.getvalue() == ""


def test_scan_progress_table_line_includes_target_and_percent() -> None:
    clock = _FakeClock()
    buf = io.StringIO()
    prog = ScanProgress(
        ScanProgressConfig(enabled=True, interval_seconds=999, interval_tables=1),
        stream=buf,
        monotonic=clock,
    )
    prog.start_run(1)
    prog.begin_target(1, "prod-rds")
    prog.set_tables_total(4)
    prog.advance_table(1, table_label="public.a")
    clock.advance(60)
    prog.advance_table(2, table_label="public.b")
    out = buf.getvalue()
    assert "target 1/1 (prod-rds)" in out
    assert "table 2/4" in out
    assert "~50%" in out
    assert "ETA" in out


def test_scan_progress_without_table_total_omits_percent_and_eta() -> None:
    buf = io.StringIO()
    prog = ScanProgress(
        ScanProgressConfig(enabled=True, interval_seconds=0, interval_tables=1),
        stream=buf,
        monotonic=_FakeClock(),
    )
    prog.start_run(1)
    prog.begin_target(1, "fs1")
    prog.advance_table(3, table_label="docs/file.txt")
    out = buf.getvalue()
    assert "table 3" in out
    assert "pending discovery" in out
    assert "~" not in out.split("pending")[0] or "~" not in out  # no percent line


def test_scan_progress_from_config_defaults_enabled() -> None:
    prog = scan_progress_from_config({"scan": {}})
    assert prog.enabled is True


def test_scan_progress_from_config_respects_false() -> None:
    prog = scan_progress_from_config({"scan": {"progress": False}})
    assert prog.enabled is False


def test_sql_connector_calls_discover_once(monkeypatch: Any) -> None:
    """Regression: table total for progress uses discover() list length, not per-iteration rediscovery."""
    from connectors.sql_connector import SQLConnector

    calls = {"discover": 0}

    class _FakeEngine:
        dialect = type("D", (), {"name": "postgresql"})()

    def fake_discover(self: SQLConnector) -> list[dict[str, Any]]:
        calls["discover"] += 1
        return [
            {
                "schema": "public",
                "table": "t1",
                "columns": [{"name": "c1", "type": "text"}],
            }
        ]

    monkeypatch.setattr(SQLConnector, "discover", fake_discover)
    monkeypatch.setattr(SQLConnector, "connect", lambda self: None)
    monkeypatch.setattr(SQLConnector, "close", lambda self: None)
    monkeypatch.setattr(SQLConnector, "_save_inventory_snapshot", lambda *a, **k: None)
    monkeypatch.setattr(
        SQLConnector,
        "_process_one_finding",
        lambda *a, **k: None,
    )

    buf = io.StringIO()
    progress = ScanProgress(
        ScanProgressConfig(enabled=True, interval_seconds=0, interval_tables=1),
        stream=buf,
    )
    progress.start_run(1)
    progress.begin_target(1, "lab-db")

    connector = SQLConnector(
        {"name": "lab-db", "type": "postgresql", "_scan_progress": progress},
        scanner=object(),
        db_manager=object(),
    )
    connector.engine = _FakeEngine()
    connector.run()
    assert calls["discover"] == 1
    assert "table 1/1" in buf.getvalue()
