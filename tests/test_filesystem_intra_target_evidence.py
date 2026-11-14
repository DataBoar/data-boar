"""Pinned evidence for the filesystem intra-target worker pool (#1820).

Two artifacts from ``tests/benchmarks/run_filesystem_intra_target_bench.py``:
one on free-threaded CPython 3.14t (GIL off) and one on CPython 3.14 with the
GIL. Both must record exact finding parity between serial and parallel runs,
at least three iterations per row (median), and the interpreter header.
The speed claims in PLAN_FILESYSTEM_INTRA_TARGET_PARALLELISM.md are pinned
here so a re-run that contradicts them fails instead of drifting.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

_BENCH = Path(__file__).resolve().parent / "benchmarks"
ARTIFACTS = {
    "nogil": _BENCH / "filesystem_intra_target_nogil.json",
    "gil": _BENCH / "filesystem_intra_target_gil.json",
}


def _load(kind: str) -> dict:
    path = ARTIFACTS[kind]
    assert path.exists(), (
        f"Missing benchmark artifact: {path}. Run "
        "tests/benchmarks/run_filesystem_intra_target_bench.py and commit the JSON."
    )
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module", params=sorted(ARTIFACTS))
def payload(request: pytest.FixtureRequest) -> tuple[str, dict]:
    return request.param, _load(request.param)


def _profile(data: dict, name: str) -> dict:
    for prof in data.get("profiles") or []:
        if prof.get("name") == name:
            return prof
    raise AssertionError(f"profile {name!r} missing")


def _best_speedup(prof: dict) -> float:
    return max(float(r["speedup_vs_serial"]) for r in prof["rows"] if r["workers"] > 1)


def test_d1820_bench_header(payload: tuple[str, dict]) -> None:
    kind, data = payload
    assert data.get("benchmark") == "filesystem_intra_target_v1"
    for key in ("git_sha", "generated_at", "host_profile", "python_version"):
        assert data.get(key), key
    assert str(data["python_version"]).startswith("3.14")
    assert isinstance(data.get("cpu_count"), int) and data["cpu_count"] >= 1
    assert data.get("gil_enabled_before") == data.get("gil_enabled_after")
    if kind == "nogil":
        assert data.get("free_threaded_build") is True
        assert data.get("gil_enabled_before") is False
    else:
        assert data.get("gil_enabled_before") is True


def test_d1820_bench_rows_have_median_and_exact_parity(
    payload: tuple[str, dict],
) -> None:
    _, data = payload
    names = {p.get("name") for p in data.get("profiles") or []}
    assert {"local_disk", "simulated_read_latency"} <= names
    for prof in data["profiles"]:
        rows = prof.get("rows") or []
        serial = [r for r in rows if r["workers"] == 1]
        assert len(serial) == 1, prof["name"]
        assert any(r["workers"] > 1 for r in rows), prof["name"]
        for row in rows:
            assert row["iterations"] >= 3
            assert len(row["wall_seconds"]) == row["iterations"]
            assert row["wall_seconds_median"] > 0
            assert row["finding_count"] == serial[0]["finding_count"] > 0
            assert row["parity_exact_ordered"] is True
            assert row["parity_exact_sorted"] is True
    assert _profile(data, "simulated_read_latency").get("simulated") is True
    assert _profile(data, "local_disk").get("simulated") is False


def test_d1820_gil_build_only_overlaps_io() -> None:
    """With the GIL, threads give no real gain on CPU-bound local reads, only on I/O waits."""
    data = _load("gil")
    assert _best_speedup(_profile(data, "local_disk")) < 1.5
    assert _best_speedup(_profile(data, "simulated_read_latency")) >= 1.5


def test_d1820_free_threaded_build_scales_cpu_bound_scan() -> None:
    data = _load("nogil")
    assert _best_speedup(_profile(data, "local_disk")) >= 1.5
    assert _best_speedup(_profile(data, "simulated_read_latency")) >= 1.5
