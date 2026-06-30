"""Regression guard for the pinned Rust prefilter hotspot benchmark.

Pins ``tests/benchmarks/rust_prefilter_hotspot.json`` so marketing cannot claim
the ~11–13× Rust prefilter speedup without a matching artifact and parity check.

Mode A (v1): speedup > 1.0, hit parity, schema fields — not a tight 11.0 floor
so slower CI runners do not false-fail. See private spec
``docs/private/partnerships/BENCHMARK_RUST_PREFILTER_PIN.pt_BR.md``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

boar_fast_filter = pytest.importorskip("boar_fast_filter")

ARTIFACT = (
    Path(__file__).resolve().parents[1]
    / "tests"
    / "benchmarks"
    / "rust_prefilter_hotspot.json"
)


@pytest.fixture(scope="module")
def benchmark_payload() -> dict:
    assert ARTIFACT.exists(), (
        f"Missing benchmark artifact: {ARTIFACT}. "
        "Run tests/benchmarks/run_rust_prefilter_hotspot_bench.py and commit JSON."
    )
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


def test_benchmark_shape_is_rust_prefilter_hotspot_v1(
    benchmark_payload: dict,
) -> None:
    assert benchmark_payload.get("benchmark") == "rust_prefilter_hotspot_v1"
    assert benchmark_payload.get("rows") == 200_000
    assert int(benchmark_payload.get("warmup_iterations", 0)) >= 0
    assert int(benchmark_payload.get("measure_iterations", 0)) >= 1
    assert benchmark_payload.get("host_profile")
    assert benchmark_payload.get("generated_at")


def test_benchmark_rust_faster_than_python_hotspot(
    benchmark_payload: dict,
) -> None:
    python_seconds = float(benchmark_payload["python_seconds"])
    rust_seconds = float(benchmark_payload["rust_seconds"])
    speedup = float(benchmark_payload["speedup_rust_vs_python"])

    assert python_seconds > 0
    assert rust_seconds > 0
    assert rust_seconds < python_seconds, (
        "Rust hotspot is not faster than Python OpenCore in the pinned artifact."
    )
    assert speedup > 1.0, (
        f"speedup_rust_vs_python={speedup} must exceed 1.0 for headline direction."
    )


def test_benchmark_speedup_matches_recorded_ratio(
    benchmark_payload: dict,
) -> None:
    python_seconds = float(benchmark_payload["python_seconds"])
    rust_seconds = float(benchmark_payload["rust_seconds"])
    recorded = float(benchmark_payload["speedup_rust_vs_python"])
    expected = python_seconds / rust_seconds
    assert abs(recorded - expected) < 1e-3, (
        f"speedup_rust_vs_python={recorded} drifted from "
        f"python_seconds/rust_seconds={expected}; regenerate or fix by hand."
    )


def test_benchmark_hit_parity_python_vs_rust(benchmark_payload: dict) -> None:
    python_hits = int(benchmark_payload["python_hit_count"])
    rust_hits = int(benchmark_payload["rust_hit_count"])
    assert python_hits == rust_hits, (
        "Python OpenCore and Rust filter_batch disagree on hit counts; "
        "investigate prefilter parity before trusting speedup."
    )
    assert python_hits > 0, "Pinned corpus must produce at least one hit."
