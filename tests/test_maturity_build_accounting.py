"""ADR-0073 maturity_build accounting guards (#1261).

Ensures published post rows (not preceding unpublished fix rows) anchor `N` counts.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

# Canonical anchors from docs/releases/1.7.4.post5.md (git-literal appendix).
POST4_PUBLISHED_MATURITY_BUILD = 226
POST5_FIX_COUNT = 14
POST5_MATURITY_BUILD = 240
POST6_MATURITY_BUILD = 241
POST7_FIX_COUNT = 4
POST7_MATURITY_BUILD = 245


def _load_pyproject() -> dict:
    with (Path(__file__).resolve().parents[1] / "pyproject.toml").open("rb") as f:
        return tomllib.load(f)


def test_post5_maturity_build_accounting_uses_post4_publish_row_not_225() -> None:
    """post4 publish row is .226; .225 is the last unpublished fix before post4."""
    assert POST4_PUBLISHED_MATURITY_BUILD == 226
    assert POST4_PUBLISHED_MATURITY_BUILD + POST5_FIX_COUNT == POST5_MATURITY_BUILD
    # False baseline from conflating .225 with post4 would imply delta 15:
    assert (POST5_MATURITY_BUILD - 225) != POST5_FIX_COUNT


def test_pyproject_maturity_build_matches_post7_canonical_map() -> None:
    data = _load_pyproject()
    maturity = data.get("tool", {}).get("databoar", {}).get("maturity_build")
    assert maturity == POST7_MATURITY_BUILD
    assert POST6_MATURITY_BUILD + POST7_FIX_COUNT == POST7_MATURITY_BUILD
