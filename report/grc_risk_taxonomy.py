"""
LGPD-aligned PII taxonomy weights for GRC **risk density** scoring.

Classification and per-unit weights are implemented in ``core.intelligence`` (English
``RiskCategory`` keys). This module maps those categories to Portuguese **taxonomy**
tier labels used in ``data_boar_grc_executive_report_v1`` rows and applies the
0–100 dashboard scale.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping, Sequence

from core.intelligence import (
    RiskCategory,
    TAXONOMY_WEIGHTS,
    classify_pii_category,
    normalize_pii_type_key,
)

TaxonomyTier = Literal[
    "identificadores",
    "financeiros_gov",
    "sensitive",
    "infantil",
    "unknown",
]

DENSITY_TAXONOMY_VERSION = "lgpd_aligned_density_v1"

_GRCP_TIER_BY_CATEGORY: dict[RiskCategory, TaxonomyTier] = {
    "IDENTIFIER": "identificadores",
    "FINANCIAL": "financeiros_gov",
    "SENSITIVE": "sensitive",
    "CHILD_DATA": "infantil",
}

_TIER_RANK: dict[TaxonomyTier, int] = {
    "unknown": 0,
    "identificadores": 1,
    "financeiros_gov": 2,
    "sensitive": 3,
    "infantil": 4,
}


@dataclass(frozen=True, slots=True)
class LgpdDensityRiskConfig:
    """
    When passed to ``GRCReporter.add_detailed_finding`` / ``add_finding``, the row
    ``risk_score`` is derived from the LGPD-aligned density table (caller-supplied
    scalar score is ignored for that row).

    ``cap_raw`` scales ``sum(count * weight)`` to the 0-100 dashboard scale; tune per
    engagement when volumes are atypical.
    """

    cap_raw: float = 2500.0


def map_pii_type_to_taxonomy(type_str: str) -> TaxonomyTier:
    """
    Map a single ``pii_types[].type`` label to a GRC taxonomy tier (Portuguese labels).

    Empty labels return ``unknown`` (same per-unit weight as identificadores).
    """
    if not normalize_pii_type_key(type_str):
        return "unknown"
    cat = classify_pii_category(type_str)
    return _GRCP_TIER_BY_CATEGORY[cat]


def dominant_taxonomy_from_lines(lines: Sequence[Mapping[str, Any]]) -> TaxonomyTier:
    """Return the highest-rank tier among lines with positive ``line_score``."""
    best: TaxonomyTier = "unknown"
    best_rank = -1
    for row in lines:
        if float(row.get("line_score", 0.0)) <= 0.0:
            continue
        tier_raw = str(row.get("taxonomy", "unknown"))
        tier: TaxonomyTier = tier_raw if tier_raw in _TIER_RANK else "unknown"
        r = _TIER_RANK[tier]
        if r > best_rank:
            best_rank = r
            best = tier
    return best


def compute_asset_risk_density(
    pii_types: Sequence[Mapping[str, Any]],
    *,
    cap_raw: float = 2500.0,
) -> tuple[float, float, list[dict[str, Any]], TaxonomyTier]:
    """
    Compute density risk for one asset row.

    Raw density equals ``sum(count * TAXONOMY_WEIGHTS[classify(type)])`` — same as
    ``core.intelligence.calculate_risk``.
    """
    density_raw = 0.0
    breakdown: list[dict[str, Any]] = []
    for item in pii_types:
        if not isinstance(item, dict):
            continue
        t = str(item.get("type", "")).strip()
        if not t:
            continue
        try:
            count = int(item["count"])
        except (KeyError, TypeError, ValueError):
            count = 0
        if count <= 0:
            continue
        cat = classify_pii_category(t)
        tier = map_pii_type_to_taxonomy(t)
        w = float(TAXONOMY_WEIGHTS[cat])
        line_score = float(count) * w
        density_raw += line_score
        breakdown.append(
            {
                "pii_type": t,
                "count": count,
                "risk_category": cat,
                "taxonomy": tier,
                "weight": w,
                "line_score": line_score,
            }
        )
    cap = max(1.0, float(cap_raw))
    risk_0_100 = min(100.0, (density_raw / cap) * 100.0)
    dominant = dominant_taxonomy_from_lines(breakdown) if breakdown else "unknown"
    return round(risk_0_100, 2), round(density_raw, 2), breakdown, dominant
