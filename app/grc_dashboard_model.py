"""
Pure helpers for the GRC executive JSON dashboard (no Streamlit).

Contract: ``data_boar_grc_executive_report_v1`` — see ``docs/GRC_EXECUTIVE_REPORT_SCHEMA.md``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION_EXPECTED = "data_boar_grc_executive_report_v1"


def load_grc_json(path: Path) -> dict[str, Any]:
    """Load and validate a GRC v1 JSON file from disk."""
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    validate_grc_v1(data)
    return data


def validate_grc_v1(data: dict[str, Any]) -> None:
    if data.get("schema_version") != SCHEMA_VERSION_EXPECTED:
        raise ValueError(
            "Unsupported schema_version "
            f"{data.get('schema_version')!r}; expected {SCHEMA_VERSION_EXPECTED!r}"
        )
    if not isinstance(data.get("report_metadata"), dict):
        raise ValueError("Missing or invalid report_metadata")
    if not isinstance(data.get("executive_summary"), dict):
        raise ValueError("Missing or invalid executive_summary")
    if not isinstance(data.get("detailed_findings"), list):
        raise ValueError("Missing or invalid detailed_findings")
    if not isinstance(data.get("recommendations"), list):
        raise ValueError("Missing or invalid recommendations")


def grc_remediation_table_rows(data: dict[str, Any]) -> list[dict[str, Any]]:
    """
    One flat row per ``pii_types[]`` entry (remediation / technical cleanup workbook).

    Columns match ``data_boar_grc_executive_report_v1`` — not the legacy ``findings`` shape.
    """
    out: list[dict[str, Any]] = []
    for asset in data.get("detailed_findings") or []:
        if not isinstance(asset, dict):
            continue
        aid = str(asset.get("asset_id", "") or "")
        base = {
            "asset_id": aid,
            "asset_class": str(asset.get("asset_class", "") or ""),
            "data_category": str(asset.get("data_category", "") or ""),
            "risk_score": float(asset.get("risk_score", 0.0) or 0.0),
            "remediation_priority": str(
                asset.get("remediation_priority", "LOW") or "LOW"
            ),
            "regulatory_impact": str(asset.get("regulatory_impact", "") or ""),
            "location_summary": str(asset.get("location_summary", "") or ""),
            "violation_desc": str(asset.get("violation_desc", "") or ""),
        }
        nt = asset.get("norm_tags")
        norm_join = "; ".join(str(x) for x in nt) if isinstance(nt, list) else ""
        base["norm_tags"] = norm_join
        pii_list = asset.get("pii_types")
        if not isinstance(pii_list, list) or not pii_list:
            row = dict(base)
            row.update(
                {
                    "pii_type": "",
                    "count": 0,
                    "exposure": "",
                }
            )
            out.append(row)
            continue
        for pii in pii_list:
            if not isinstance(pii, dict):
                continue
            row = dict(base)
            try:
                cnt = int(pii.get("count", 0) or 0)
            except (TypeError, ValueError):
                cnt = 0
            row["pii_type"] = str(pii.get("type", "") or "")
            row["count"] = cnt
            row["exposure"] = str(pii.get("exposure", "") or "")
            out.append(row)
    return out


def findings_chart_rows(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten ``detailed_findings`` for charts and tables."""
    rows: list[dict[str, Any]] = []
    for f in data.get("detailed_findings") or []:
        if not isinstance(f, dict):
            continue
        rows.append(
            {
                "asset_id": str(f.get("asset_id", "") or ""),
                "risk_score": float(f.get("risk_score", 0.0) or 0.0),
                "remediation_priority": str(
                    f.get("remediation_priority", "LOW") or "LOW"
                ),
                "data_category": str(f.get("data_category", "unknown") or "unknown"),
                "asset_class": str(f.get("asset_class", "") or ""),
                "regulatory_impact": str(f.get("regulatory_impact", "") or ""),
            }
        )
    return rows


def peak_asset_risk_score(data: dict[str, Any]) -> float:
    """Maximum ``risk_score`` across matrix rows (executive JSON has no single total risk)."""
    scores = [r["risk_score"] for r in findings_chart_rows(data)]
    return max(scores) if scores else 0.0


def compliance_mapping_hints(data: dict[str, Any]) -> str:
    """Short display string for workshop article hints."""
    cm = data.get("compliance_mapping")
    if not isinstance(cm, dict):
        return ""
    parts: list[str] = []
    lg = cm.get("lgpd_articles_hint")
    if isinstance(lg, list) and lg:
        parts.append("LGPD hints: " + ", ".join(str(x) for x in lg[:6]))
        if len(lg) > 6:
            parts.append("…")
    gd = cm.get("gdpr_articles_hint")
    if isinstance(gd, list) and gd:
        parts.append("GDPR hints: " + ", ".join(str(x) for x in gd[:6]))
        if len(gd) > 6:
            parts.append("…")
    return " | ".join(parts)
