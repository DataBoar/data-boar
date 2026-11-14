"""Pinned evidence for the filesystem intra-target worker pool (#1820).

Four artifacts from ``tests/benchmarks/run_filesystem_intra_target_bench.py``:
free-threaded CPython 3.14t (GIL off) and CPython 3.14 (GIL), each with the
code as shipped (``variant: none``) and with option (a) of the profile
(``variant: ml_lock``: one lock around the detector ML step, applied by the
bench harness only). All rows must record exact serial/parallel finding
parity, >= 3 iterations and the median.

The claims below are the **measured** ones written in
PLAN_FILESYSTEM_INTRA_TARGET_PARALLELISM.md — including the negative results.
A re-run (or a detector fix) that changes them must update the plan and this
test together.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

_BENCH = Path(__file__).resolve().parent / "benchmarks"
# (runtime, variant, detector ML fix) -> artifact
ARTIFACTS = {
    ("nogil", "none", "fix"): _BENCH / "filesystem_intra_target_nogil.json",
    ("gil", "none", "fix"): _BENCH / "filesystem_intra_target_gil.json",
    ("nogil", "none", "before"): _BENCH
    / "filesystem_intra_target_nogil_before_fix.json",
    ("gil", "none", "before"): _BENCH / "filesystem_intra_target_gil_before_fix.json",
    ("nogil", "ml_lock", "before"): _BENCH
    / "filesystem_intra_target_nogil_ml_lock_before_fix.json",
    ("gil", "ml_lock", "before"): _BENCH
    / "filesystem_intra_target_gil_ml_lock_before_fix.json",
}


def _load(runtime: str, variant: str, fix: str = "fix") -> dict:
    path = ARTIFACTS[(runtime, variant, fix)]
    assert path.exists(), (
        f"Missing benchmark artifact: {path}. Run "
        "tests/benchmarks/run_filesystem_intra_target_bench.py and commit the JSON."
    )
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module", params=sorted(ARTIFACTS), ids=lambda k: "-".join(k))
def payload(request: pytest.FixtureRequest) -> tuple[str, str, dict]:
    runtime, variant, fix = request.param
    data = _load(runtime, variant, fix)
    assert bool(data.get("detector_joblib_free_ml", False)) is (fix == "fix")
    return runtime, variant, data


def _rows(data: dict, profile: str) -> dict[int, dict]:
    for prof in data.get("profiles") or []:
        if prof.get("name") == profile:
            return {int(r["workers"]): r for r in prof["rows"]}
    raise AssertionError(f"profile {profile!r} missing")


def _speedups(data: dict, profile: str) -> dict[int, float]:
    return {w: float(r["speedup_vs_serial"]) for w, r in _rows(data, profile).items()}


def test_d1820_bench_header(payload: tuple[str, str, dict]) -> None:
    runtime, variant, data = payload
    assert data.get("benchmark") == "filesystem_intra_target_v1"
    assert data.get("variant") == variant
    for key in ("git_sha", "generated_at", "host_profile", "python_version"):
        assert data.get(key), key
    assert str(data["python_version"]).startswith("3.14")
    assert isinstance(data.get("cpu_count"), int) and data["cpu_count"] >= 1
    assert data.get("gil_enabled_before") == data.get("gil_enabled_after")
    if runtime == "nogil":
        assert data.get("free_threaded_build") is True
        assert data.get("gil_enabled_before") is False
    else:
        assert data.get("gil_enabled_before") is True


def test_d1820_bench_rows_have_median_and_exact_parity(
    payload: tuple[str, str, dict],
) -> None:
    _, _, data = payload
    names = {p.get("name") for p in data.get("profiles") or []}
    assert {"local_disk", "simulated_read_latency"} <= names
    for prof in data["profiles"]:
        rows = prof.get("rows") or []
        serial = [r for r in rows if r["workers"] == 1]
        assert len(serial) == 1, prof["name"]
        assert {2, 4, 8} <= {r["workers"] for r in rows}, prof["name"]
        for row in rows:
            assert row["iterations"] >= 3
            assert len(row["wall_seconds"]) == row["iterations"]
            assert row["wall_seconds_median"] > 0
            assert row["effective_max_workers"] == row["workers"]
            assert row["finding_count"] == serial[0]["finding_count"] > 0
            assert row["parity_exact_ordered"] is True
            assert row["parity_exact_sorted"] is True
    sim = next(p for p in data["profiles"] if p["name"] == "simulated_read_latency")
    local = next(p for p in data["profiles"] if p["name"] == "local_disk")
    assert sim.get("simulated") is True
    assert local.get("simulated") is False


def test_d1820_gil_threads_give_no_cpu_gain_and_little_io_overlap() -> None:
    """With the GIL: local disk gets slower with threads; 2 ms waits overlap only a little."""
    for fix in ("before", "fix"):
        data = _load("gil", "none", fix)
        local = _speedups(data, "local_disk")
        assert max(v for w, v in local.items() if w > 1) < 1.0, fix
        sim = _speedups(data, "simulated_read_latency")
        assert 1.0 <= max(v for w, v in sim.items() if w > 1) < 1.5, fix


def test_d1820_free_threaded_pool_collapses_without_detector_fix() -> None:
    """Negative result as shipped: joblib.Parallel inside the ML step collapses at N >= 4."""
    data = _load("nogil", "none", "before")
    for profile in ("local_disk", "simulated_read_latency"):
        sp = _speedups(data, profile)
        assert sp[4] < 0.5 and sp[8] < 0.5, profile


def test_d1820_ml_lock_removes_collapse_but_gives_no_gain() -> None:
    """Option (a): no collapse on either runtime, and no speed-up worth claiming."""
    for runtime in ("nogil", "gil"):
        data = _load(runtime, "ml_lock", "before")
        for profile in ("local_disk", "simulated_read_latency"):
            sp = _speedups(data, profile)
            assert min(sp.values()) >= 0.8, (runtime, profile)
            assert max(sp.values()) < 1.5, (runtime, profile)


def _serial_median(data: dict, profile: str) -> float:
    return float(_rows(data, profile)[1]["wall_seconds_median"])


def test_d1820_detector_fix_speeds_up_the_serial_scan() -> None:
    """The joblib-free ML step alone cuts the serial scan time on both runtimes."""
    for runtime in ("nogil", "gil"):
        before = _serial_median(_load(runtime, "none", "before"), "local_disk")
        after = _serial_median(_load(runtime, "none", "fix"), "local_disk")
        assert before / after >= 1.5, runtime


def test_d1820_free_threaded_pool_gains_after_detector_fix() -> None:
    """With the fix, 3.14t gains on local disk (bounded by the serial writer) and more on waits."""
    data = _load("nogil", "none", "fix")
    local = _speedups(data, "local_disk")
    assert max(v for w, v in local.items() if w > 1) >= 1.4
    assert all(v >= 1.0 for v in local.values())
    sim = _speedups(data, "simulated_read_latency")
    assert max(v for w, v in sim.items() if w > 1) >= 2.0
