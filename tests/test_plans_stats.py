"""
Regression tests for scripts/plans-stats.py status parsing/counting.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_plans_stats_module():
    root = Path(__file__).resolve().parent.parent
    script_path = root / "scripts" / "plans-stats.py"
    spec = importlib.util.spec_from_file_location("plans_stats", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_compute_stats_counts_tracked_partially_done_as_incomplete_tracked():
    plans_stats = _load_plans_stats_module()
    sample = "\n".join(
        [
            "### H0/U0 Priority",
            "| Step | Task | Status |",
            "| ---- | ---- | ------ |",
            "| A1 | Dependabot triage | Tracked (partially done) |",
            "| A2 | Scout triage | 🔄 Tracked |",
            "| A3 | Hub hygiene | ⬜ Pending |",
            "| A4 | Release docs | ✅ Done |",
        ]
    )

    stats = plans_stats.compute_stats(sample)
    assert stats["total_rows"] == 4
    assert stats["done"] == 1
    assert stats["incomplete"] == 3
    assert stats["tracked"] == 2
    assert stats["pending"] == 1
    assert stats["by_h_total"]["H0"] == 4
    assert stats["by_h_done"]["H0"] == 1
    assert stats["by_h_incomplete"]["H0"] == 3
