#!/usr/bin/env python3
"""
Official benchmark: OpenCore baseline vs Pro+ worker path.

This benchmark is intentionally simple and reproducible for operator evidence.
"""

from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

from core.prefilter import OpenCorePreFilter
from pro.engine import process_chunk_worker
from tests.benchmarks.benchmark_gate import evaluate_official_pro_v1, format_gate_report


def generate_test_data(rows: int = 200_000) -> list[str]:
    seed = [
        "123.456.789-00",
        "apenas um texto comum",
        "4532 1123 4456 7789",
        "email@teste.com",
    ]
    repeat = max(1, rows // len(seed))
    return (seed * repeat)[:rows]


def run_opencore(data: list[str]) -> tuple[float, int]:
    scanner = OpenCorePreFilter()
    start = time.perf_counter()
    out = scanner.filter_candidates(data)
    elapsed = time.perf_counter() - start
    return elapsed, len(out)


def run_pro(data: list[str], workers: int) -> tuple[float, int]:
    safe_workers = max(1, int(workers))
    chunk_size = max(1, len(data) // safe_workers)
    chunks = [data[i : i + chunk_size] for i in range(0, len(data), chunk_size)]

    start = time.perf_counter()
    findings_count = 0
    with ProcessPoolExecutor(max_workers=safe_workers) as pool:
        for findings in pool.map(process_chunk_worker, chunks):
            findings_count += len(findings)
    elapsed = time.perf_counter() - start
    return elapsed, findings_count


def run_benchmark(rows: int, workers: int) -> dict[str, Any]:
    data = generate_test_data(rows)
    print(f"[*] Iniciando Benchmark Oficial: {len(data):,} registros.")

    core_time, core_hits = run_opencore(data)
    print(f"[OK] OpenCore (Python): {core_time:.4f}s | hits={core_hits}")

    pro_time, pro_hits = run_pro(data, workers=workers)
    print(f"[OK] Pro+ (Rust/Process): {pro_time:.4f}s | hits={pro_hits}")

    speedup = (core_time / pro_time) if pro_time > 0 else 0.0
    print("-" * 40)
    print(f"GANHO DE PERFORMANCE: {speedup:.2f}x")
    print("-" * 40)

    artifact: dict[str, Any] = {
        "benchmark": "official_pro_v1",
        "rows": len(data),
        "workers": max(1, int(workers)),
        "opencore_seconds": round(core_time, 6),
        "pro_seconds": round(pro_time, 6),
        "speedup_vs_opencore": round(speedup, 4),
        "opencore_hits": core_hits,
        "pro_hits": pro_hits,
        "rust_worker_path": True,
        "generated_at_epoch": time.time(),
    }
    gate = evaluate_official_pro_v1(artifact)
    artifact["gate"] = gate.to_gate_dict()
    print(format_gate_report(gate))
    return artifact


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run official OpenCore vs Pro benchmark"
    )
    parser.add_argument("--rows", type=int, default=200_000)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--output", default="tests/benchmarks/official_benchmark.json")
    parser.add_argument(
        "--enforce-gate",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Exit 1 when speed or safe axis fails (default: on)",
    )
    args = parser.parse_args(argv)

    artifact = run_benchmark(
        rows=max(1, int(args.rows)), workers=max(1, int(args.workers))
    )
    output = Path(args.output).expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    print(f"[OK] Benchmark artifact: {output}")
    gate = artifact.get("gate") or {}
    if args.enforce_gate and gate.get("safe_axis") == "fail":
        return 1
    if args.enforce_gate and gate.get("speed_axis") == "fail":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
