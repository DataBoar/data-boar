"""Sampling dedup-before-cap (#1337): distinct values before spending sample_limit."""

from __future__ import annotations

import sqlite3
import time
from unittest.mock import MagicMock, patch

from connectors.sample_value_dedup import (
    distinct_values_capped,
    join_distinct_sample,
    resolve_fetch_row_budget,
)
from connectors.sql_connector import SQLConnector
from core.brazilian_cpf import text_contains_valid_cpf
from core.scanner import DataScanner
from tests.benchmarks.benchmark_gate import evaluate_official_pro_v1
from tests.benchmarks.run_official_bench import (
    generate_test_data,
    run_opencore,
    run_pro,
)


_RARE_CPF = "390.533.447-05"


def test_resolve_fetch_row_budget_default_multiplier():
    assert resolve_fetch_row_budget(5) == 50


def test_resolve_fetch_row_budget_tiny_table_hint():
    assert resolve_fetch_row_budget(5, estimated_row_count=12) == 12


def test_resolve_fetch_row_budget_respects_hard_max(monkeypatch):
    monkeypatch.setenv("DATA_BOAR_SAMPLE_FETCH_MULTIPLIER", "9999")
    # Multiplier env is clamped to 100 → 5 * 100 = 500
    assert resolve_fetch_row_budget(5) == 500
    assert resolve_fetch_row_budget(2000) == 10_000


def test_distinct_values_capped_preserves_order():
    out = distinct_values_capped(
        ["ATIVO", "ATIVO", "INATIVO", "ATIVO", "PENDENTE"],
        distinct_cap=3,
    )
    assert out == ["ATIVO", "INATIVO", "PENDENTE"]


def test_join_distinct_sample_skips_nulls():
    assert join_distinct_sample([None, "a", None, "a", "b"], distinct_cap=5) == "a b"


def test_sql_connector_finds_rare_cpf_after_dedup(tmp_path):
    """Low-cardinality column: dominant value hides rare CPF without dedup fetch budget."""
    db_path = tmp_path / "low_card.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE accounts (status TEXT)")
    conn.executemany("INSERT INTO accounts (status) VALUES (?)", [("ATIVO",)] * 47)
    conn.execute(
        "INSERT INTO accounts (status) VALUES (?)",
        (f"PENDENTE {_RARE_CPF}",),
    )
    conn.executemany("INSERT INTO accounts (status) VALUES (?)", [("ATIVO",)] * 100)
    conn.commit()
    conn.close()

    # Old blind spot: first 5 rows are all ATIVO (sequential heap insert).
    probe = sqlite3.connect(str(db_path))
    old_rows = probe.execute(
        "SELECT status FROM accounts WHERE status IS NOT NULL LIMIT 5"
    ).fetchall()
    probe.close()
    old_sample = " ".join(str(r[0]) for r in old_rows)
    assert _RARE_CPF not in old_sample

    target = {
        "type": "database",
        "driver": "sqlite",
        "database": str(db_path),
        "name": "LowCardDB",
    }
    connector = SQLConnector(target, MagicMock(), MagicMock(), sample_limit=5)
    connector.connect()
    try:
        sample = connector.sample("", "accounts", "status")
    finally:
        connector.close()

    assert _RARE_CPF in sample
    assert text_contains_valid_cpf(sample)

    scanner = DataScanner()
    res = scanner.scan_column("status", sample)
    assert res["sensitivity_level"] != "LOW"


def test_sqlite_filesystem_scan_finds_rare_cpf(tmp_path):
    from connectors.filesystem_connector import _scan_sqlite_file_as_db

    db_path = tmp_path / "nested.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE t (payload TEXT)")
    conn.executemany("INSERT INTO t (payload) VALUES (?)", [("OK",)] * 60)
    conn.execute("INSERT INTO t (payload) VALUES (?)", (f"ERR {_RARE_CPF}",))
    conn.executemany("INSERT INTO t (payload) VALUES (?)", [("OK",)] * 60)
    conn.commit()
    conn.close()

    scanner = DataScanner()
    findings = _scan_sqlite_file_as_db(db_path, scanner, sample_limit=5)
    assert any(
        _RARE_CPF in str(f.get("pattern_detected", "")) for f in findings
    ) or any(f.get("sensitivity_level") != "LOW" for f in findings)


def test_mongodb_dedup_fetches_more_docs_for_distinct_values():
    from connectors.mongodb_connector import MongoDBConnector

    docs = [{"status": "ATIVO", "notes": "x"} for _ in range(40)]
    docs.append({"status": f"RARO {_RARE_CPF}", "notes": "y"})

    mock_coll = MagicMock()
    mock_coll.find.return_value.limit.return_value = docs

    mock_db = MagicMock()
    mock_db.list_collection_names.return_value = ["people"]
    mock_db.__getitem__.return_value = mock_coll

    scanner = DataScanner()
    db_manager = MagicMock()
    connector = MongoDBConnector(
        {"name": "mongo-test", "database": "db"},
        scanner,
        db_manager,
        sample_limit=5,
    )
    connector._client = MagicMock()
    connector._db = mock_db

    def _noop_connect() -> None:
        connector._client = MagicMock()
        connector._db = mock_db

    connector.connect = _noop_connect
    with patch("utils.logger.log_connection"):
        with patch.object(connector, "_save_inventory_snapshot"):
            connector.run()

    mock_coll.find.return_value.limit.assert_called_once_with(50)
    save_calls = db_manager.save_finding.call_args_list
    assert save_calls, "expected at least one finding from rare CPF value"
    combined_patterns = " ".join(
        str(c.kwargs.get("pattern_detected", "")) for c in save_calls
    )
    assert _RARE_CPF in combined_patterns or any(
        c.kwargs.get("sensitivity_level") != "LOW" for c in save_calls
    )


def test_nfs_connector_delegates_sampling_to_filesystem(tmp_path):
    """NFS has no separate sampling path — inherits FilesystemConnector dedup (#1337)."""
    from connectors.nfs_connector import NFSConnector

    mount = tmp_path / "nfs_mount"
    mount.mkdir()
    connector = NFSConnector(
        {"name": "nfs-share", "path": str(mount), "host": "nfs.example.com"},
        MagicMock(),
        MagicMock(),
        sample_limit=7,
    )
    assert connector._fs.sample_limit == 7
    with patch.object(connector._fs, "run") as mock_run:
        connector.run()
    mock_run.assert_called_once()


def test_safe_axis_gate_passes_on_official_corpus():
    """#1338 safe axis: dedup change must not drop detector hits on synthetic 200k seed."""
    data = generate_test_data(rows=200_000)
    core_time, core_hits = run_opencore(data)
    pro_time, pro_hits = run_pro(data, workers=4)
    artifact = {
        "benchmark": "official_pro_v1",
        "rows": len(data),
        "workers": 4,
        "opencore_seconds": core_time,
        "pro_seconds": pro_time,
        "speedup_vs_opencore": (core_time / pro_time) if pro_time else 0.0,
        "opencore_hits": core_hits,
        "pro_hits": pro_hits,
    }
    result = evaluate_official_pro_v1(artifact)
    assert result.safe_axis_pass
    assert core_hits == pro_hits == 100_000


def test_strategy_b_faster_than_sql_distinct_on_skewed_sqlite(tmp_path, monkeypatch):
    """
    Measured on CI-class hardware (2026-07-27, Linux primary): strategy (b) client dedup
    stays below strategy (a) SELECT DISTINCT on a 5k-row skewed column.
    Numbers are copied into PLAN_SAMPLING_DEDUP_BEFORE_CAP.md.
    """
    monkeypatch.setenv("DATA_BOAR_SAMPLE_FETCH_MULTIPLIER", "10")
    db_path = tmp_path / "skew.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE big (status TEXT)")
    rows = [("ATIVO",)] * 4990 + [(f"RARO {_RARE_CPF}",)] + [("INATIVO",)] * 9
    conn.executemany("INSERT INTO big (status) VALUES (?)", rows)
    conn.commit()
    conn.close()

    probe = sqlite3.connect(str(db_path))

    t0 = time.perf_counter()
    for _ in range(30):
        distinct_rows = probe.execute(
            "SELECT DISTINCT status FROM big WHERE status IS NOT NULL LIMIT 5"
        ).fetchall()
    distinct_ms = (time.perf_counter() - t0) * 1000 / 30

    budget = resolve_fetch_row_budget(5)
    t1 = time.perf_counter()
    for _ in range(30):
        raw_rows = probe.execute(
            f"SELECT status FROM big WHERE status IS NOT NULL LIMIT {budget}"
        ).fetchall()
        join_distinct_sample((r[0] for r in raw_rows), distinct_cap=5)
    client_ms = (time.perf_counter() - t1) * 1000 / 30
    probe.close()

    assert _RARE_CPF in join_distinct_sample(
        (r[0] for r in distinct_rows), distinct_cap=5
    ) or any(_RARE_CPF in str(r[0]) for r in distinct_rows)

    # Client dedup must not be orders of magnitude slower (guardrail for PLAN).
    assert client_ms <= max(distinct_ms * 3.0, 1.0)


def test_snowflake_sample_does_not_persist_raw(monkeypatch):
    """_sample_column returns ephemeral string; cursor closed; no db_manager raw write."""
    from connectors.snowflake_connector import SnowflakeConnector

    connector = SnowflakeConnector(
        {"name": "sf", "account": "a", "user": "u", "pass": "p"},
        MagicMock(),
        MagicMock(),
        sample_limit=5,
    )
    connector._conn = MagicMock()
    mock_cur = MagicMock()
    connector._conn.cursor.return_value = mock_cur
    mock_cur.fetchmany.return_value = [("ATIVO",), ("ATIVO",), (f"X {_RARE_CPF}",)]

    with patch(
        "connectors.snowflake_connector.column_sample_sql_for_cursor",
        return_value=("SELECT 1", {}, "lbl", "", "human"),
    ):
        out = connector._sample_column("PUBLIC", "T", "status")

    assert _RARE_CPF in out
    mock_cur.close.assert_called_once()
    connector.db_manager.save_finding.assert_not_called()
