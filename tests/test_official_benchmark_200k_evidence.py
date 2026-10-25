"""Regression guard for the 200k A/B benchmark evidence (OpenCore vs Pro).

Pin the published numbers in ``tests/benchmarks/official_benchmark_200k.json``
so executive material cannot accidentally claim a Pro+ "speedup" that
contradicts the recorded artifact.

Why this lives in the test suite (Julia Evans-style note):

- The Slack handoff for this run added context that the 200k A/B confirmed the
  Pro profile is **0.574x mais lento** than OpenCore. Strictly, the JSON stores
  ``speedup_vs_opencore = 0.574``, which means Pro is *0.574x as fast as*
  OpenCore (i.e. Pro takes roughly ``1 / 0.574 ~= 1.74x`` more time). Either
  reading agrees on direction: **Pro is slower in this profile**.
- The hub (`docs/ops/LAB_LESSONS_LEARNED.md`) and the post-mortem
  (`docs/ops/SPRINT_GREAT_LEAP_POSTMORTEM.md`) already separate verified vs
  aspirational claims; this test is the **machine-readable** echo so a future
  doc PR or executive deck cannot silently flip the sign without also touching
  the JSON artifact.

Defensive posture (DEFENSIVE_SCANNING_MANIFESTO spirit):

- The check is a **read-only** JSON parse. No database connection, no SQLite
  write, no file lock acquisition; safe to run alongside scans.

Fallback posture (THE_ART_OF_THE_FALLBACK spirit):

- If the artifact is ever regenerated with a different profile (larger chunks,
  heavier downstream stage), the assertions surface the change immediately so
  the operator updates marketing prose **and** the JSON together, instead of
  one drifting from the other.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ARTIFACT = (
    Path(__file__).resolve().parents[1]
    / "tests"
    / "benchmarks"
    / "official_benchmark_200k.json"
)


@pytest.fixture(scope="module")
def benchmark_payload() -> dict:
    assert ARTIFACT.exists(), (
        f"Missing benchmark artifact: {ARTIFACT}. "
        "Re-run tests/benchmarks/run_official_bench.py and commit the JSON."
    )
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


def test_benchmark_shape_is_official_pro_v1(benchmark_payload: dict) -> None:
    """The pinned artifact must declare its provenance fields."""
    assert benchmark_payload.get("benchmark") == "official_pro_v1"
    assert benchmark_payload.get("rows") == 200_000
    assert benchmark_payload.get("workers") == 8


def test_benchmark_pro_path_is_slower_in_this_profile(
    benchmark_payload: dict,
) -> None:
    """Direction of the recorded A/B: Pro path is slower than OpenCore.

    If a future profile flips this (Pro faster), update the JSON **and** the
    LAB_LESSONS / post-mortem prose in the same commit so they stop disagreeing.
    """
    opencore_seconds = float(benchmark_payload["opencore_seconds"])
    pro_seconds = float(benchmark_payload["pro_seconds"])
    speedup = float(benchmark_payload["speedup_vs_opencore"])

    assert opencore_seconds > 0
    assert pro_seconds > 0
    assert pro_seconds > opencore_seconds, (
        "Recorded Pro time is not greater than OpenCore: artifact disagrees "
        "with LAB_LESSONS_LEARNED narrative; refresh both together."
    )
    assert speedup < 1.0, (
        f"speedup_vs_opencore={speedup} >= 1.0 contradicts the documented "
        "'Pro slower in this profile' result."
    )


def test_benchmark_speedup_matches_recorded_ratio(
    benchmark_payload: dict,
) -> None:
    """Recorded speedup field must match opencore/pro arithmetic (rounded).

    We use a generous tolerance because the JSON stores ``round(speedup, 4)``.
    """
    opencore_seconds = float(benchmark_payload["opencore_seconds"])
    pro_seconds = float(benchmark_payload["pro_seconds"])
    recorded = float(benchmark_payload["speedup_vs_opencore"])
    expected = opencore_seconds / pro_seconds
    assert abs(recorded - expected) < 1e-3, (
        f"speedup_vs_opencore={recorded} drifted from "
        f"opencore_seconds/pro_seconds={expected}; regenerate or fix by hand."
    )


def test_benchmark_findings_parity(benchmark_payload: dict) -> None:
    """Both paths must report the same finding count for the seeded corpus.

    A divergence here would mean the Pro path silently dropped detections,
    which is more important than performance for a defensive scanner.
    """
    opencore_hits = int(benchmark_payload["opencore_hits"])
    pro_hits = int(benchmark_payload["pro_hits"])
    assert opencore_hits == pro_hits, (
        "Pro and OpenCore disagree on hit counts at 200k. "
        "Investigate prefilter/worker logic before any performance tuning."
    )
