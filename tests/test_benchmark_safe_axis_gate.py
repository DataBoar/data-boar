"""Blocking safe-axis gate for benchmark harness (#1338)."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from tests.benchmarks.benchmark_gate import (
    SAFE_HOLD_MIN_SPEEDUP,
    evaluate_ab_recall_parity,
    evaluate_official_pro_v1,
    format_gate_report,
)

ARTIFACT = (
    Path(__file__).resolve().parent / "benchmarks" / "official_benchmark_200k.json"
)


@pytest.fixture(scope="module")
def benchmark_payload() -> dict:
    assert ARTIFACT.exists(), f"Missing benchmark artifact: {ARTIFACT}"
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


def test_pinned_artifact_passes_gate(benchmark_payload: dict) -> None:
    result = evaluate_official_pro_v1(benchmark_payload)
    assert result.safe_axis_pass
    assert result.speed_axis_pass
    assert result.passed
    assert result.opencore_hits == result.pro_hits == 100_000


def test_gate_report_includes_time_and_recall(benchmark_payload: dict) -> None:
    result = evaluate_official_pro_v1(benchmark_payload)
    report = format_gate_report(result)
    assert "time:" in report
    assert "recall:" in report
    assert "speed_axis:" in report
    assert "safe_axis:" in report


def test_safe_axis_rejects_recall_regression_even_when_faster() -> None:
    """Mutation: faster Pro path that drops one hit must REPROVE."""
    artifact = {
        "benchmark": "official_pro_v1",
        "opencore_seconds": 0.25,
        "pro_seconds": 0.20,
        "speedup_vs_opencore": 1.25,
        "opencore_hits": 100_000,
        "pro_hits": 99_999,
    }
    result = evaluate_official_pro_v1(artifact, manifest_path=None)
    assert result.speed_axis_pass
    assert not result.safe_axis_pass
    assert not result.passed
    assert any("safe_axis" in reason for reason in result.failure_reasons)


def test_speed_axis_rejects_safe_hold_breach() -> None:
    artifact = {
        "benchmark": "official_pro_v1",
        "opencore_seconds": 0.25,
        "pro_seconds": 1.0,
        "speedup_vs_opencore": SAFE_HOLD_MIN_SPEEDUP - 0.01,
        "opencore_hits": 50,
        "pro_hits": 50,
    }
    result = evaluate_official_pro_v1(artifact, manifest_path=None)
    assert not result.speed_axis_pass
    assert result.safe_axis_pass
    assert not result.passed


def test_ab_recall_parity_matches_lab_precedent() -> None:
    ok, failures = evaluate_ab_recall_parity(26, 26, expected_findings=26)
    assert ok
    assert failures == ()

    ok_bad, failures_bad = evaluate_ab_recall_parity(26, 25, expected_findings=26)
    assert not ok_bad
    assert failures_bad


def test_run_official_bench_attaches_gate_block() -> None:
    from tests.benchmarks.run_official_bench import run_benchmark

    artifact = run_benchmark(rows=400, workers=2)
    assert "gate" in artifact
    assert artifact["gate"]["safe_axis"] in {"pass", "fail"}
    assert artifact["gate"]["speed_axis"] in {"pass", "fail"}
    assert artifact["opencore_hits"] == artifact["pro_hits"]


def test_mutated_artifact_fails_gate_helper() -> None:
    payload = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    mutated = copy.deepcopy(payload)
    mutated["pro_hits"] = int(mutated["pro_hits"]) - 1
    mutated["speedup_vs_opencore"] = 0.99
    result = evaluate_official_pro_v1(mutated)
    assert not result.passed
