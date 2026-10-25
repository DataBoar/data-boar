"""Tests for ``core.discovery_orchestrator.BoarDiscovery``."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, text

from core.discovery_orchestrator import BoarDiscovery


def _fixture_db(path: Path) -> None:
    eng = create_engine(f"sqlite:///{path}")
    with eng.begin() as conn:
        conn.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, notes TEXT)"))
        conn.execute(
            text(
                "INSERT INTO users (notes) VALUES "
                "('cpf válido 390.533.447-05'),"
                "('sem cpf válido 12345678901'),"
                "('outro válido 39053344705')"
            )
        )
    eng.dispose()


def test_run_full_scan_returns_asset_findings(tmp_path: Path) -> None:
    db = tmp_path / "scan.db"
    _fixture_db(db)
    disc = BoarDiscovery(f"sqlite:///{db}", sample_limit=100)
    try:
        out = disc.run_full_scan()
    finally:
        disc.db.engine.dispose()

    assert "assets" in out
    assets = out["assets"]
    assert len(assets) == 1
    assert assets[0]["id"] == "users"
    findings = assets[0]["findings"]
    assert findings == [{"type": "BRAZIL_CPF", "count": 2}]


def test_run_full_scan_skips_tables_without_hits(tmp_path: Path) -> None:
    db = tmp_path / "scan.db"
    eng = create_engine(f"sqlite:///{db}")
    with eng.begin() as conn:
        conn.execute(
            text("CREATE TABLE clean_table (id INTEGER PRIMARY KEY, notes TEXT)")
        )
        conn.execute(text("INSERT INTO clean_table (notes) VALUES ('no pii here')"))
    eng.dispose()

    disc = BoarDiscovery(f"sqlite:///{db}")
    try:
        out = disc.run_full_scan()
    finally:
        disc.db.engine.dispose()

    assert out == {"assets": []}


def test_parallel_scan_matches_sequential(tmp_path: Path) -> None:
    db = tmp_path / "scan.db"
    _fixture_db(db)

    seq = BoarDiscovery(f"sqlite:///{db}", sample_limit=100, worker_processes=1)
    par = BoarDiscovery(f"sqlite:///{db}", sample_limit=100, worker_processes=2)
    try:
        out_seq = seq.run_full_scan()
        out_par = par.run_full_scan()
    finally:
        seq.db.engine.dispose()
        par.db.engine.dispose()

    assert out_par == out_seq


def test_adaptive_rate_limit_records_latency_and_calls_sleep(tmp_path: Path) -> None:
    db = tmp_path / "scan.db"
    _fixture_db(db)

    slept: list[float] = []

    def _fake_sleep(seconds: float) -> None:
        slept.append(seconds)

    disc = BoarDiscovery(
        f"sqlite:///{db}",
        sample_limit=100,
        worker_processes=2,
        adaptive_rate_limit=True,
        target_latency_ms=0.001,  # force backoff on normal local latency
        sleep_fn=_fake_sleep,
    )
    try:
        out = disc.run_full_scan()
    finally:
        disc.db.engine.dispose()

    assert out["assets"]
    assert disc.throttler.latency_history
    assert slept
