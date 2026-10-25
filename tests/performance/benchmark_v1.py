#!/usr/bin/env python3
"""
Benchmark v1: discovery scan sequential vs multiprocessing.

Writes a JSON artifact with wall-clock timings and speedup.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import time
from pathlib import Path
from typing import Any

from core.discovery_orchestrator import BoarDiscovery
from scripts.setup_lab_db import create_mock_db


def _inflate_fixture(db_path: Path, extra_rows: int) -> None:
    if extra_rows <= 0:
        return
    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        batch = []
        for i in range(extra_rows):
            # Alternate valid and invalid CPF-shaped payloads to mimic mixed signal.
            cpf = "390.533.447-05" if i % 2 == 0 else "123.456.789-00"
            batch.append((10_000 + i, f"User {i}", cpf, f"user{i}@example.test"))
        cur.executemany(
            "INSERT INTO users (id, nome, cpf, email) VALUES (?, ?, ?, ?)",
            batch,
        )
        conn.commit()
    finally:
        conn.close()


def _run_scan(
    db_path: Path, workers: int, sample_limit: int
) -> tuple[float, dict[str, Any]]:
    scan = BoarDiscovery(
        f"sqlite:///{db_path}",
        sample_limit=sample_limit,
        worker_processes=workers,
    )
    t0 = time.perf_counter()
    try:
        out = scan.run_full_scan()
    finally:
        scan.db.engine.dispose()
    elapsed = time.perf_counter() - t0
    return elapsed, out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Benchmark discovery sequential vs parallel"
    )
    parser.add_argument("--db", default="data/lab_completao_benchmark.db")
    parser.add_argument("--extra-rows", type=int, default=20_000)
    parser.add_argument("--sample-limit", type=int, default=50_000)
    parser.add_argument("--parallel-workers", type=int, default=8)
    parser.add_argument("--output", default="tests/performance/benchmarks.json")
    args = parser.parse_args(argv)

    db_path = Path(args.db).expanduser()
    out_path = Path(args.output).expanduser()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    create_mock_db(db_path)
    _inflate_fixture(db_path, extra_rows=max(0, int(args.extra_rows)))

    t_seq, out_seq = _run_scan(db_path, workers=1, sample_limit=int(args.sample_limit))
    t_par, out_par = _run_scan(
        db_path,
        workers=max(1, int(args.parallel_workers)),
        sample_limit=int(args.sample_limit),
    )

    speedup = (t_seq / t_par) if t_par > 0 else 0.0
    artifact = {
        "benchmark": "discovery_v1",
        "db_path": str(db_path),
        "sample_limit": int(args.sample_limit),
        "extra_rows": int(args.extra_rows),
        "sequential_seconds": round(t_seq, 6),
        "parallel_seconds": round(t_par, 6),
        "parallel_workers": max(1, int(args.parallel_workers)),
        "speedup_vs_sequential": round(speedup, 4),
        "sequential_assets": len(out_seq.get("assets", [])),
        "parallel_assets": len(out_par.get("assets", [])),
        "results_match": out_seq == out_par,
        "generated_at_epoch": time.time(),
    }
    out_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    print(json.dumps(artifact, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
