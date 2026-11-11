#!/usr/bin/env python3
"""
Rust per-call vs batch cost (#2182).

Measures the PyO3 boundary that dominates ``RegexStageEngine.match_names`` (one
call per sample, as ``core/rust_regex_stage.py``) versus ``FastFilter.filter_batch``
(one call per batch). Includes short- and long-text corpora and recommends a
minimum text length before the product should invoke the Rust regex stage.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from core.prefilter import OpenCorePreFilter

from tests.benchmarks.run_official_bench import generate_test_data

BENCHMARK_ID = "rust_per_call_cost_v1"

_SHORT_SEED = "texto curto 70 chars cpf 123.456.789-00 e email a@b.co"
_LONG_REPEAT = 33  # ~len(_SHORT_SEED) * 33 ≈ 2.3k chars


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


def _host_load() -> dict[str, float]:
    try:
        la1, la5, la15 = os.getloadavg()
        return {"load_1m": la1, "load_5m": la5, "load_15m": la15}
    except (AttributeError, OSError):
        return {}


def _gil_enabled() -> bool | None:
    fn = getattr(sys, "_is_gil_enabled", None)
    if callable(fn):
        try:
            return bool(fn())
        except Exception:  # noqa: BLE001
            return None
    return None


def _median_seconds(fn: Callable[[], None], *, iterations: int) -> float:
    timings: list[float] = []
    for _ in range(iterations):
        start = time.perf_counter()
        fn()
        timings.append(time.perf_counter() - start)
    return statistics.median(timings)


def _per_call_python_prefilter(lines: list[str]) -> int:
    scanner = OpenCorePreFilter()
    hits = 0
    for line in lines:
        hits += len(scanner.filter_candidates([line]))
    return hits


def _batch_python_prefilter(lines: list[str]) -> int:
    scanner = OpenCorePreFilter()
    return len(scanner.filter_candidates(lines))


def _per_call_rust_filter_batch(lines: list[str]) -> int:
    from boar_fast_filter import FastFilter  # noqa: PLC0415

    scanner = FastFilter()
    hits = 0
    for line in lines:
        hits += len(scanner.filter_batch([line]))
    return hits


def _batch_rust_filter_batch(lines: list[str]) -> int:
    from boar_fast_filter import FastFilter  # noqa: PLC0415

    scanner = FastFilter()
    return len(scanner.filter_batch(lines))


def _per_call_rust_regex_stage(lines: list[str]) -> int:
    from boar_fast_filter import RegexStageEngine  # noqa: PLC0415

    engine = RegexStageEngine.compile_patterns(
        ["CPF", "EMAIL"],
        [
            r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b",
            r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        ],
        None,
    )
    hits = 0
    for line in lines:
        hits += len(engine.match_names(line))
    return hits


def _build_corpus(profile: str, rows: int) -> tuple[list[str], str]:
    if profile == "short":
        unit = _SHORT_SEED[:70].ljust(70, " ")
        lines = [unit for _ in range(rows)]
        return lines, "short_70_chars"
    if profile == "long":
        unit = (_SHORT_SEED * _LONG_REPEAT)[:2300]
        lines = [unit for _ in range(rows)]
        return lines, "long_2300_chars"
    raise ValueError(f"unknown profile {profile!r}")


def _measure_profile(
    *,
    profile: str,
    rows: int,
    warmup: int,
    iterations: int,
) -> dict[str, Any]:
    lines, label = _build_corpus(profile, rows)

    for _ in range(warmup):
        _per_call_python_prefilter(lines[: min(50, len(lines))])

    py_per = _median_seconds(
        lambda: _per_call_python_prefilter(lines), iterations=iterations
    )
    py_batch = _median_seconds(
        lambda: _batch_python_prefilter(lines), iterations=iterations
    )
    rust_per = _median_seconds(
        lambda: _per_call_rust_filter_batch(lines), iterations=iterations
    )
    rust_batch = _median_seconds(
        lambda: _batch_rust_filter_batch(lines), iterations=iterations
    )
    rust_stage_per = _median_seconds(
        lambda: _per_call_rust_regex_stage(lines), iterations=iterations
    )

    py_hits = _per_call_python_prefilter(lines)
    rust_batch_hits = _batch_rust_filter_batch(lines)

    def ratio(py_s: float, rust_s: float) -> float | None:
        if rust_s <= 0:
            return None
        return py_s / rust_s

    return {
        "profile": label,
        "rows": rows,
        "python_seconds_per_call_loop": round(py_per, 6),
        "python_seconds_single_batch": round(py_batch, 6),
        "rust_seconds_per_call_loop": round(rust_per, 6),
        "rust_seconds_single_batch": round(rust_batch, 6),
        "rust_regex_stage_seconds_per_call_loop": round(rust_stage_per, 6),
        "ratio_per_call_python_over_rust_filter": round(
            ratio(py_per, rust_per) or 0.0, 4
        ),
        "ratio_batch_python_over_rust_filter": round(
            ratio(py_batch, rust_batch) or 0.0, 4
        ),
        "ratio_per_call_python_over_rust_stage": round(
            ratio(py_per, rust_stage_per) or 0.0, 4
        ),
        "python_hit_count": py_hits,
        "rust_batch_hit_count": rust_batch_hits,
        "per_call_us_python": round((py_per / rows) * 1e6, 3) if rows else 0.0,
        "per_call_us_rust_filter": round((rust_per / rows) * 1e6, 3) if rows else 0.0,
        "per_call_us_rust_stage": round((rust_stage_per / rows) * 1e6, 3)
        if rows
        else 0.0,
    }


def _activation_min_text_chars(*, sweep_iterations: int = 3) -> dict[str, Any]:
    """Find smallest text length where Rust stage per-call is not worse than Python."""
    from boar_fast_filter import RegexStageEngine  # noqa: PLC0415

    engine = RegexStageEngine.compile_patterns(
        ["CPF", "EMAIL"],
        [
            r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b",
            r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        ],
        None,
    )
    scanner = OpenCorePreFilter()
    lengths = [64, 96, 128, 256, 512, 768, 1024, 1536, 2048, 3072, 4096]
    sweep: list[dict[str, Any]] = []
    activation: int | None = None
    base_unit = _SHORT_SEED

    for length in lengths:
        text = (base_unit * ((length // len(base_unit)) + 1))[:length]
        line = [text]

        py_s = _median_seconds(
            lambda t=text, ln=line: scanner.filter_candidates(ln),
            iterations=sweep_iterations,
        )
        ru_s = _median_seconds(
            lambda t=text: engine.match_names(t),
            iterations=sweep_iterations,
        )
        row = {
            "text_chars": length,
            "python_seconds": round(py_s, 6),
            "rust_stage_seconds": round(ru_s, 6),
            "ratio_python_over_rust": round((py_s / ru_s) if ru_s > 0 else 0.0, 4),
        }
        sweep.append(row)
        if activation is None and ru_s > 0 and py_s >= ru_s:
            activation = length

    if activation is None:
        activation = lengths[-1] + 1

    return {
        "activation_min_text_chars": activation,
        "length_sweep": sweep,
    }


def run_benchmark(
    *,
    rows: int,
    warmup: int,
    measure_iterations: int,
) -> dict[str, Any]:
    short = _measure_profile(
        profile="short",
        rows=rows,
        warmup=warmup,
        iterations=measure_iterations,
    )
    long_ = _measure_profile(
        profile="long",
        rows=max(500, rows // 40),
        warmup=warmup,
        iterations=max(2, measure_iterations - 1),
    )
    activation = _activation_min_text_chars()

    _ = generate_test_data(4)  # keep import parity with hotspot runner

    artifact: dict[str, Any] = {
        "benchmark": BENCHMARK_ID,
        "rows_default": rows,
        "warmup_iterations": warmup,
        "measure_iterations": measure_iterations,
        "profiles": [short, long_],
        "activation": activation,
        "host_profile": _host_profile(),
        "host_load": _host_load(),
        "gil_enabled": _gil_enabled(),
        "python_version": platform.python_version(),
        "git_sha": _git_sha_short(),
        "generated_at": datetime.now(UTC).isoformat(),
    }
    return artifact


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run Rust per-call vs batch cost benchmark (#2182)"
    )
    parser.add_argument("--rows", type=int, default=20_000)
    parser.add_argument("--warmup", type=int, default=1)
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument(
        "--output",
        default="tests/benchmarks/rust_per_call_cost.json",
    )
    args = parser.parse_args(argv)

    artifact = run_benchmark(
        rows=max(100, int(args.rows)),
        warmup=max(0, int(args.warmup)),
        measure_iterations=max(1, int(args.iterations)),
    )
    output = Path(args.output).expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(artifact, indent=2))
    print(f"[OK] Benchmark artifact: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
