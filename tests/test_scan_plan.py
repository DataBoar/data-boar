"""Scan plan preview (#1329): estimation and enumeration without live remote I/O."""

from __future__ import annotations

import socket
import threading
from typing import Any

import pytest

from core.scan_plan import (
    LOCAL_RTT_MS,
    REMOTE_RTT_MS,
    SLOW_RTT_FLOOR_SECONDS,
    classify_latency,
    estimate_sql_rtt_floor_seconds,
    format_scan_plan_report,
    measure_tcp_rtt_ms,
    plan_one_target,
    resolve_tcp_peer,
    run_scan_plan,
    should_warn_slow,
    sql_engine_key,
)


def test_estimate_matches_column_plus_two_per_table() -> None:
    # 4257 columns, 300 tables, 140 ms — RTT floor ≈ 10.2 min, not 53 min.
    rtt_ms = 140.0
    n_tables = 300
    n_columns = 4257
    got = estimate_sql_rtt_floor_seconds(
        n_tables=n_tables, n_columns=n_columns, rtt_ms=rtt_ms
    )
    expected = (n_columns + 2 * n_tables) * (rtt_ms / 1000.0)
    assert got == expected
    assert abs(got - 679.98) < 0.02


def test_estimate_snowflake_skips_row_estimate_query() -> None:
    got = estimate_sql_rtt_floor_seconds(
        n_tables=10,
        n_columns=100,
        rtt_ms=100.0,
        include_table_row_estimate=False,
    )
    assert got == 11.0  # 100 samples + 10 get_columns; no estimate_table_rows
    got = estimate_sql_rtt_floor_seconds(
        n_tables=1,
        n_columns=10,
        rtt_ms=100.0,
        inter_query_delay_s=0.05,
    )
    # 10 samples + 2 catalog/estimate RTs = 12 * 0.1s + 10 * 0.05s
    assert got == pytest.approx(1.7)


def test_estimate_none_without_rtt() -> None:
    assert estimate_sql_rtt_floor_seconds(n_tables=3, n_columns=9, rtt_ms=None) is None


def test_classify_loopback_is_local_even_with_high_rtt() -> None:
    assert classify_latency("127.0.0.1", 200.0) == "local"
    assert classify_latency("localhost", 200.0) == "local"


def test_classify_rtt_thresholds() -> None:
    assert classify_latency("db.example.com", LOCAL_RTT_MS - 0.1) == "local"
    assert classify_latency("db.example.com", 10.0) == "lan"
    assert classify_latency("db.example.com", REMOTE_RTT_MS) == "remote"
    assert classify_latency("db.example.com", None) == "unknown"


def test_should_warn_on_ten_minute_floor() -> None:
    assert should_warn_slow(
        classification="lan",
        rtt_ms=10.0,
        n_columns=10,
        estimated_s=SLOW_RTT_FLOOR_SECONDS,
    )
    assert not should_warn_slow(
        classification="lan",
        rtt_ms=10.0,
        n_columns=10,
        estimated_s=SLOW_RTT_FLOOR_SECONDS - 1,
    )


def test_should_warn_remote_fat_catalog() -> None:
    assert should_warn_slow(
        classification="remote",
        rtt_ms=50.0,
        n_columns=200,
        estimated_s=30.0,
    )
    assert not should_warn_slow(
        classification="remote",
        rtt_ms=49.0,
        n_columns=200,
        estimated_s=30.0,
    )
    assert not should_warn_slow(
        classification="remote",
        rtt_ms=140.0,
        n_columns=199,
        estimated_s=30.0,
    )


def test_resolve_peer_sql_default_port() -> None:
    assert resolve_tcp_peer(
        {"type": "database", "driver": "postgresql", "host": "db.example.com"}
    ) == ("db.example.com", 5432)
    assert resolve_tcp_peer({"type": "mysql", "host": "db.example.com"}) == (
        "db.example.com",
        3306,
    )
    assert resolve_tcp_peer({"type": "sqlite", "database": "x.db"}) is None


def test_sql_engine_key() -> None:
    assert sql_engine_key({"type": "database", "driver": "postgresql+psycopg2"}) == (
        "postgresql"
    )
    assert sql_engine_key({"type": "filesystem", "path": "/tmp"}) is None


def test_plan_one_target_uses_injected_rtt_and_enum() -> None:
    def fake_rtt(host: str, port: int) -> float:
        assert host == "8.8.8.8"
        assert port == 5432
        return 140.0

    def fake_enum(target: dict[str, Any]) -> tuple[int, int, None]:
        assert target["name"] == "prod-pg"
        return 300, 4257, None

    row = plan_one_target(
        {
            "name": "prod-pg",
            "type": "database",
            "driver": "postgresql",
            "host": "8.8.8.8",
        },
        measure_rtt=fake_rtt,
        enumerate_sql=fake_enum,
    )
    assert row["classification"] == "remote"
    assert row["n_tables"] == 300
    assert row["n_columns"] == 4257
    assert row["warn"] is True
    assert row["estimated_s"] is not None
    assert row["estimated_s"] > 600


def test_run_scan_plan_filesystem_no_network() -> None:
    text = run_scan_plan(
        {
            "targets": [
                {"name": "files", "type": "filesystem", "path": "/tmp/corpus"},
            ]
        },
        measure_rtt=lambda host, port: (_ for _ in ()).throw(
            AssertionError("must not probe RTT without a peer")
        ),
        enumerate_sql=lambda t: (_ for _ in ()).throw(
            AssertionError("must not enumerate SQL for filesystem")
        ),
    )
    assert "files" in text
    assert "not a SQL/Snowflake catalog target" in text
    assert "  WARN:" not in text
    assert "No slow/remote WARN" in text


def test_plan_skips_rfc1918_rtt_without_allow_private_networks() -> None:
    """Live SQL/Mongo refuse RFC1918 unless allow_private_networks; --plan must too."""

    def boom_rtt(host: str, port: int) -> float:
        raise AssertionError(f"must not TCP-probe {host}:{port}")

    def boom_enum(target: dict[str, Any]) -> tuple[int, int, None]:
        raise AssertionError("must not catalog-connect a guard-rejected peer")

    row = plan_one_target(
        {
            "name": "lab-pg",
            "type": "database",
            "driver": "postgresql",
            "host": "10.0.0.5",
            "port": 5432,
        },
        measure_rtt=boom_rtt,
        enumerate_sql=boom_enum,
    )
    assert row["rtt_ms"] is None
    assert row["rtt_skip_reason"]
    assert "10.0.0.5" in row["rtt_skip_reason"]
    assert "allow_private_networks" in row["rtt_skip_reason"]
    assert "#832" in row["rtt_skip_reason"]
    text = format_scan_plan_report([row])
    assert "skipped (network policy" in text
    assert "allow_private_networks" in text


def test_plan_skips_link_local_metadata_without_opt_in() -> None:
    def boom_rtt(host: str, port: int) -> float:
        raise AssertionError(f"must not TCP-probe {host}:{port}")

    row = plan_one_target(
        {
            "name": "meta",
            "type": "mongodb",
            "host": "169.254.169.254",
            "port": 27017,
        },
        measure_rtt=boom_rtt,
        enumerate_sql=lambda t: (_ for _ in ()).throw(
            AssertionError("must not enumerate")
        ),
    )
    assert row["rtt_ms"] is None
    assert row["rtt_skip_reason"]
    assert "169.254.169.254" in row["rtt_skip_reason"]
    assert "link-local" in row["rtt_skip_reason"]


def test_plan_probes_rfc1918_when_allow_private_networks() -> None:
    seen: list[tuple[str, int]] = []

    def fake_rtt(host: str, port: int) -> float:
        seen.append((host, port))
        return 12.0

    row = plan_one_target(
        {
            "name": "lab-pg",
            "type": "database",
            "driver": "postgresql",
            "host": "10.0.0.5",
            "port": 5432,
            "allow_private_networks": True,
        },
        measure_rtt=fake_rtt,
        enumerate_sql=lambda t: (2, 5, None),
    )
    assert seen == [("10.0.0.5", 5432)]
    assert row["rtt_ms"] == 12.0
    assert row["rtt_skip_reason"] is None
    assert row["n_tables"] == 2


def test_format_includes_documented_ruler() -> None:
    body = format_scan_plan_report([])
    assert "local = loopback or RTT < 5 ms" in body
    assert "remote = RTT ≥ 20 ms" in body
    assert "≥ 10 min" in body


def test_measure_tcp_rtt_ms_localhost_is_fast() -> None:
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    port = srv.getsockname()[1]
    stop = threading.Event()

    def _accept() -> None:
        srv.settimeout(2.0)
        try:
            conn, _addr = srv.accept()
            conn.close()
        except OSError:
            pass
        finally:
            stop.set()

    t = threading.Thread(target=_accept, daemon=True)
    t.start()
    try:
        rtt = measure_tcp_rtt_ms("127.0.0.1", port, timeout_s=1.0)
        assert rtt is not None
        assert rtt < 500.0
    finally:
        srv.close()
        stop.wait(1.0)
        t.join(1.0)
