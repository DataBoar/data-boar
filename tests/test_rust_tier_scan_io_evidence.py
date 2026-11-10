"""Pinned evidence for tier-capped filesystem scan I/O (#2182)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("boar_fast_filter")

ARTIFACT = Path(__file__).resolve().parent / "benchmarks" / "rust_tier_scan_io.json"


@pytest.fixture(scope="module")
def benchmark_payload() -> dict:
    assert ARTIFACT.exists(), (
        f"Missing benchmark artifact: {ARTIFACT}. "
        "Run tests/benchmarks/run_rust_tier_scan_io_bench.py and commit JSON."
    )
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


def test_benchmark_shape_is_rust_tier_scan_io_v1(benchmark_payload: dict) -> None:
    assert benchmark_payload.get("benchmark") == "rust_tier_scan_io_v1"
    assert benchmark_payload.get("git_sha")
    assert benchmark_payload.get("generated_at")
    assert benchmark_payload.get("host_profile")
    assert "gil_enabled" in benchmark_payload
    runs = benchmark_payload.get("tier_runs") or []
    assert len(runs) >= 4
    tiers = {r.get("dbtier") for r in runs}
    assert {"community", "std", "pro", "pro_plus"}.issubset(tiers)


def test_worker_caps_match_tier_table(benchmark_payload: dict) -> None:
    expected = {"community": 2, "std": 2, "pro": 4, "pro_plus": 8}
    for row in benchmark_payload["tier_runs"]:
        tier = row.get("dbtier")
        if tier not in expected:
            continue
        assert row.get("effective_max_workers") == expected[tier]


def test_tier_recommendation_documents_negative_speed_upsell(
    benchmark_payload: dict,
) -> None:
    rec = benchmark_payload.get("tier_differentiator_recommendation") or {}
    assert rec.get("rust_as_headline_speed_differentiator") is False
    assert rec.get("keep_rust_regex_stage_on_pro_plus") is True
    assert rec.get("rationale_en")


def test_cp314t_limitation_documented(benchmark_payload: dict) -> None:
    cp = benchmark_payload.get("cp314t_wheel_status") or {}
    assert cp.get("published_in_repo_ci") is False
    assert "abi3" in str(cp.get("blocker", "")).lower()
