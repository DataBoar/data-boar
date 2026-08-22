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
POST7_MATURITY_BUILD = 245
POST8_FIX_COUNT = 5
POST8_MATURITY_BUILD = 250
POST9_FIX_COUNT = 7
POST9_MATURITY_BUILD = 257
POST10_FIX_COUNT = 4
POST10_MATURITY_BUILD = 261
POST11_FIX_COUNT = 1
POST11_MATURITY_BUILD = 262
POST12_FIX_COUNT = 1
POST12_MATURITY_BUILD = 263
# New public line 1.8.0-beta (ADR-0073): octet resets into beta band; first beta = 1.
# Reconciled 2026-08-22: 115 fix/feat commits since cut 604c1b5c (exclusive) → 1 + 115 = 116.
LINE_180_BETA_FIX_COUNT_SINCE_CUT = 115
LINE_180_BETA_MATURITY_BUILD = 1 + LINE_180_BETA_FIX_COUNT_SINCE_CUT


def _load_pyproject() -> dict:
    with (Path(__file__).resolve().parents[1] / "pyproject.toml").open("rb") as f:
        return tomllib.load(f)


def test_post5_maturity_build_accounting_uses_post4_publish_row_not_225() -> None:
    """post4 publish row is .226; .225 is the last unpublished fix before post4."""
    assert POST4_PUBLISHED_MATURITY_BUILD == 226
    assert POST4_PUBLISHED_MATURITY_BUILD + POST5_FIX_COUNT == POST5_MATURITY_BUILD
    # False baseline from conflating .225 with post4 would imply delta 15:
    assert (POST5_MATURITY_BUILD - 225) != POST5_FIX_COUNT


def test_post12_canonical_map_arithmetic_is_internally_consistent() -> None:
    """Historic 1.7.4.postN chain stays auditable after the 1.8.0 line opens."""
    assert POST11_MATURITY_BUILD + POST12_FIX_COUNT == POST12_MATURITY_BUILD
    assert POST10_MATURITY_BUILD + POST11_FIX_COUNT == POST11_MATURITY_BUILD
    assert POST9_MATURITY_BUILD + POST10_FIX_COUNT == POST10_MATURITY_BUILD
    assert POST8_MATURITY_BUILD + POST9_FIX_COUNT == POST9_MATURITY_BUILD
    assert POST7_MATURITY_BUILD + POST8_FIX_COUNT == POST8_MATURITY_BUILD


def test_pyproject_maturity_build_matches_180_beta_reconciled_octet() -> None:
    data = _load_pyproject()
    version = data.get("project", {}).get("version")
    maturity = data.get("tool", {}).get("databoar", {}).get("maturity_build")
    assert version == "1.8.0-beta"
    assert maturity == LINE_180_BETA_MATURITY_BUILD
    assert maturity == 116
    assert maturity != POST12_MATURITY_BUILD  # must not carry .263 across lines
