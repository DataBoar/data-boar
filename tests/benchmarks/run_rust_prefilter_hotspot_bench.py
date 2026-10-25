#!/usr/bin/env python3
"""
Pinned hotspot benchmark: OpenCore Python prefilter vs Rust ``filter_batch``.

Scope: same ``list[str]`` payload, microbench only — not end-to-end scan or
``official_pro_v1`` (ProcessPool worker path). See ``tests/benchmarks/README.md``.
"""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from core.prefilter import OpenCorePreFilter

from tests.benchmarks.run_official_bench import generate_test_data

BENCHMARK_ID = "rust_prefilter_hotspot_v1"


def _git_sha_short() -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return out.strip() or None
    except (OSError, subprocess.CalledProcessError):
        return None


def _host_profile() -> str:
    machine = platform.machine() or "unknown"
    system = platform.system().lower() or "unknown"
    return f"{system}-{machine}"


def _time_python_filter(data: list[str], iterations: int) -> tuple[float, int]:
    scanner = OpenCorePreFilter()
    timings: list[float] = []
    hit_count = 0
    for _ in range(iterations):
        start = time.perf_counter()
        out = scanner.filter_candidates(data)
        timings.append(time.perf_counter() - start)
        hit_count = len(out)
    return statistics.mean(timings), hit_count


def _time_rust_filter(data: list[str], iterations: int) -> tuple[float, int]:
    from boar_fast_filter import FastFilter  # noqa: PLC0415 — optional extension

    scanner = FastFilter()
    timings: list[float] = []
    hit_count = 0
    for _ in range(iterations):
        start = time.perf_counter()
        indexes = scanner.filter_batch(data)
        timings.append(time.perf_counter() - start)
        hit_count = len(indexes)
    return statistics.mean(timings), hit_count


def run_benchmark(
    *,
    rows: int,
    warmup_iterations: int,
    measure_iterations: int,
) -> dict[str, Any]:
    data = generate_test_data(rows)
    print(f"[*] Rust prefilter hotspot: {len(data):,} rows")

    for label, fn in (
        ("python warmup", lambda: _time_python_filter(data, warmup_iterations)),
        ("rust warmup", lambda: _time_rust_filter(data, warmup_iterations)),
    ):
        print(f"[*] {label} ({warmup_iterations} iter)")
        fn()

    python_seconds, python_hits = _time_python_filter(data, measure_iterations)
    rust_seconds, rust_hits = _time_rust_filter(data, measure_iterations)

    if rust_hits != python_hits:
        raise SystemExit(
            f"Parity failure: python_hits={python_hits} rust_hits={rust_hits}"
        )

    speedup = (python_seconds / rust_seconds) if rust_seconds > 0 else 0.0
    print(f"[OK] Python mean: {python_seconds:.6f}s | hits={python_hits}")
    print(f"[OK] Rust mean:   {rust_seconds:.6f}s | hits={rust_hits}")
    print("-" * 40)
    print(f"SPEEDUP (python/rust): {speedup:.2f}x")
    print("-" * 40)

    return {
        "benchmark": BENCHMARK_ID,
        "rows": len(data),
        "warmup_iterations": warmup_iterations,
        "measure_iterations": measure_iterations,
        "python_seconds": round(python_seconds, 6),
        "rust_seconds": round(rust_seconds, 6),
        "speedup_rust_vs_python": round(speedup, 4),
        "python_hit_count": python_hits,
        "rust_hit_count": rust_hits,
        "host_profile": _host_profile(),
        "git_sha": _git_sha_short(),
        "generated_at": datetime.now(UTC).isoformat(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run OpenCore Python vs Rust filter_batch hotspot benchmark"
    )
    parser.add_argument("--rows", type=int, default=200_000)
    parser.add_argument("--warmup", type=int, default=2)
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument(
        "--output",
        default="tests/benchmarks/rust_prefilter_hotspot.json",
    )
    args = parser.parse_args(argv)

    artifact = run_benchmark(
        rows=max(1, int(args.rows)),
        warmup_iterations=max(0, int(args.warmup)),
        measure_iterations=max(1, int(args.iterations)),
    )
    output = Path(args.output).expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(f"[OK] Benchmark artifact: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
