"""Pinned evidence for Rust per-call vs batch cost (#2182)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.rust_regex_stage import RUST_REGEX_STAGE_MIN_TEXT_CHARS

pytest.importorskip("boar_fast_filter")

ARTIFACT = Path(__file__).resolve().parent / "benchmarks" / "rust_per_call_cost.json"


@pytest.fixture(scope="module")
def benchmark_payload() -> dict:
    assert ARTIFACT.exists(), (
        f"Missing benchmark artifact: {ARTIFACT}. "
        "Run tests/benchmarks/run_rust_per_call_cost_bench.py and commit JSON."
    )
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


def test_benchmark_shape_is_rust_per_call_cost_v1(benchmark_payload: dict) -> None:
    assert benchmark_payload.get("benchmark") == "rust_per_call_cost_v1"
    assert benchmark_payload.get("git_sha")
    assert benchmark_payload.get("generated_at")
    assert benchmark_payload.get("host_profile")
    assert "gil_enabled" in benchmark_payload
    assert benchmark_payload.get("host_load") is not None
    profiles = benchmark_payload.get("profiles") or []
    assert len(profiles) >= 2
    labels = {p.get("profile") for p in profiles}
    assert "short_70_chars" in labels
    assert "long_2300_chars" in labels


def test_activation_constant_matches_artifact(benchmark_payload: dict) -> None:
    activation = (benchmark_payload.get("activation") or {}).get(
        "activation_min_text_chars"
    )
    assert activation is not None
    assert RUST_REGEX_STAGE_MIN_TEXT_CHARS == int(activation)


def test_short_profile_rust_per_call_slower_than_batch(
    benchmark_payload: dict,
) -> None:
    short = next(
        p for p in benchmark_payload["profiles"] if p.get("profile") == "short_70_chars"
    )
    per_ratio = float(short["ratio_per_call_python_over_rust_filter"])
    batch_ratio = float(short["ratio_batch_python_over_rust_filter"])
    assert per_ratio < 1.0, "short corpus: per-call Rust should lose vs Python"
    assert batch_ratio > 1.0, "short corpus: batch Rust should beat Python"
