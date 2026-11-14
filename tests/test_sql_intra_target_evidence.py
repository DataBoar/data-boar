"""Pinned evidence for the SQL per-table worker pool (#1322).

Two artifacts from ``tests/benchmarks/run_sql_intra_target_bench.py``:
free-threaded CPython 3.14t (GIL off) and CPython 3.14 (GIL). Every row must
record exact serial/parallel finding parity (ordered and sorted), >= 5
iterations and the median; the run must start with host load < 1.5.

The claims below are the **measured** ones written in
PLAN_DB_PER_TABLE_PARALLELISM.md, including the negative result (threads
are slower on a local SQLite source with the GIL). ``simulated_query_latency``
is a fixture (a sleep before each column sample), not a remote database.
A re-run that changes them must update the plan and this test together.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

_BENCH = Path(__file__).resolve().parent / "benchmarks"
ARTIFACTS = {
    "nogil": _BENCH / "sql_intra_target_nogil.json",
    "gil": _BENCH / "sql_intra_target_gil.json",
}


def _load(runtime: str) -> dict:
    path = ARTIFACTS[runtime]
    assert path.exists(), (
        f"Missing benchmark artifact: {path}. Run "
        "tests/benchmarks/run_sql_intra_target_bench.py and commit the JSON."
    )
    return json.loads(path.read_text(encoding="utf-8"))


def _speedups(data: dict, profile: str) -> dict[int, float]:
    for prof in data.get("profiles") or []:
        if prof.get("name") == profile:
            return {
                int(r["workers"]): float(r["speedup_vs_serial"]) for r in prof["rows"]
            }
    raise AssertionError(f"profile {profile!r} missing")


@pytest.mark.parametrize("runtime", sorted(ARTIFACTS))
def test_d1322_bench_header(runtime: str) -> None:
    data = _load(runtime)
    assert data.get("benchmark") == "sql_intra_target_v1"
    for key in ("git_sha", "generated_at", "host_profile", "python_version"):
        assert data.get(key), key
    assert str(data["python_version"]).startswith("3.14")
    assert data.get("gil_enabled_before") == data.get("gil_enabled_after")
    assert float(data["host_load_before"]["load_1m"]) < 1.5
    if runtime == "nogil":
        assert data.get("free_threaded_build") is True
        assert data.get("gil_enabled_before") is False
    else:
        assert data.get("gil_enabled_before") is True


@pytest.mark.parametrize("runtime", sorted(ARTIFACTS))
def test_d1322_bench_rows_have_exact_parity(runtime: str) -> None:
    data = _load(runtime)
    names = {p["name"]: p for p in data["profiles"]}
    assert set(names) == {"local_sqlite", "simulated_query_latency"}
    assert names["simulated_query_latency"]["simulated"] is True
    assert names["local_sqlite"]["simulated"] is False
    for prof in data["profiles"]:
        rows = prof["rows"]
        assert [r["workers"] for r in rows] == [1, 2, 4, 8]
        for row in rows:
            assert row["iterations"] >= 5
            assert len(row["wall_seconds"]) == row["iterations"]
            assert row["effective_max_workers"] == row["workers"]
            assert row["finding_count"] == rows[0]["finding_count"] > 0
            assert row["parity_exact_ordered"] is True
            assert row["parity_exact_sorted"] is True


def test_d1322_waits_overlap_on_both_runtimes() -> None:
    """With a simulated per-query wait the pool overlaps it with or without the GIL."""
    for runtime in ARTIFACTS:
        sp = _speedups(_load(runtime), "simulated_query_latency")
        assert sp[2] >= 1.8 and sp[4] >= 3.5 and sp[8] >= 6.0, runtime


def test_d1322_local_sqlite_gains_only_without_the_gil() -> None:
    """Local SQLite, no wait: 3.14t gains a little; with the GIL threads are slower."""
    nogil = _speedups(_load("nogil"), "local_sqlite")
    assert max(v for w, v in nogil.items() if w > 1) >= 1.4
    assert all(v >= 1.0 for v in nogil.values())
    gil = _speedups(_load("gil"), "local_sqlite")
    assert max(v for w, v in gil.items() if w > 1) < 1.0
