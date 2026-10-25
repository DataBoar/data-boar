"""
GRC executive report consolidator — builds ``data_boar_grc_executive_report_v1`` JSON.

Maps scanner-style metadata (assets, PII category counts, risk scores) into the stable
shape described in ``docs/GRC_EXECUTIVE_REPORT_SCHEMA.md``. This is **not** legal advice;
``compliance_score`` and ``risk_level`` are **heuristics** for workshop / dashboard use.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from core.about import get_about_info

from report import nist_csf_hints
from report.grc_risk_taxonomy import (
    DENSITY_TAXONOMY_VERSION,
    LgpdDensityRiskConfig,
    compute_asset_risk_density,
)

SCHEMA_VERSION = "data_boar_grc_executive_report_v1"
COMPLIANCE_SCORE_METHOD = "heuristic_v1_weighted_excess_risk"
# Method label for the optional NIST CSF 2.0 function-hint block (see issue #760).
NIST_CSF_HINT_METHOD = "heuristic_norm_tag_to_csf_v1"

RiskLevel = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
RemediationPriority = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
DataCategory = Literal["personal", "sensitive", "unknown"]
HeatmapQuadrant = Literal[
    "impact_high_likelihood_high",
    "impact_high_likelihood_low",
    "impact_low_likelihood_high",
    "impact_low_likelihood_low",
]

# LGPD-style rigour: sensitive personal data should not score lower than generic personal
# when other signals are equal (tunable per engagement).
SENSITIVE_RISK_MULTIPLIER = 1.22
SENSITIVE_RISK_ADDEND = 6.0


def _utc_now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _new_report_id() -> str:
    return f"DB-{uuid.uuid4().hex[:10].upper()}"


def remediation_priority_from_score(risk_score: float) -> RemediationPriority:
    if risk_score > 80:
        return "CRITICAL"
    if risk_score > 60:
        return "HIGH"
    if risk_score > 40:
        return "MEDIUM"
    return "LOW"


def risk_level_from_findings(risk_scores: list[float]) -> RiskLevel:
    if not risk_scores:
        return "LOW"
    mx = max(risk_scores)
    if mx >= 90:
        return "CRITICAL"
    if mx >= 75:
        return "HIGH"
    if mx >= 50:
        return "MEDIUM"
    return "LOW"


def apply_data_category_risk_weight(
    base_risk: float,
    data_category: str,
    *,
    multiplier: float = SENSITIVE_RISK_MULTIPLIER,
    addend: float = SENSITIVE_RISK_ADDEND,
) -> float:
    """
    Raise ``risk_score`` when ``data_category`` is ``sensitive`` (LGPD Art. 11-style rigour).

    ``personal`` leaves the base score unchanged; ``unknown`` applies a tiny nudge only
    when the base score is already elevated (operator-tunable later).
    """
    b = max(0.0, min(100.0, float(base_risk)))
    cat = (data_category or "unknown").strip().lower()
    if cat == "sensitive":
        return max(b, min(100.0, b * multiplier + addend))
    if cat == "personal":
        return b
    if cat == "unknown" and b >= 55.0:
        return min(100.0, b + 2.0)
    return b


def default_heatmap_axes_from_risk(risk_score: float) -> tuple[float, float]:
    """
    Interim **Impact × Likelihood** (0–100) when the engagement has not supplied both axes.

    Splits a single consolidated score so dashboards can plot a point; replace with real
    likelihood models (controls maturity, exposure window) when data exists.
    """
    rs = max(0.0, min(100.0, float(risk_score)))
    impact = rs
    likelihood = min(100.0, 35.0 + rs * 0.55)
    return round(impact, 1), round(likelihood, 1)


def heatmap_quadrant(impact_score: float, likelihood_score: float) -> HeatmapQuadrant:
    """2×2 board view: thresholds at 50 (tune per engagement)."""
    i_hi = impact_score >= 50.0
    l_hi = likelihood_score >= 50.0
    if i_hi and l_hi:
        return "impact_high_likelihood_high"
    if i_hi and not l_hi:
        return "impact_high_likelihood_low"
    if not i_hi and l_hi:
        return "impact_low_likelihood_high"
    return "impact_low_likelihood_low"


def compliance_score_heuristic_v1(
    risk_scores: list[float],
    *,
    risk_floor: float = 50.0,
    weight: float = 0.35,
) -> float:
    """
    Start at 100; subtract ``weight * max(0, risk_score - risk_floor)`` per asset row.

    Documented in ``docs/GRC_EXECUTIVE_REPORT_SCHEMA.md`` (§4). Not a legal adequacy score.
    """
    score = 100.0
    for rs in risk_scores:
        excess = max(0.0, float(rs) - risk_floor)
        score -= weight * excess
    return max(0.0, min(100.0, round(score, 1)))


def _normalize_pii_types(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        t = str(item.get("type", "")).strip()
        if not t:
            continue
        try:
            count = int(item["count"])
        except (KeyError, TypeError, ValueError):
            count = 0
        exposure = str(item.get("exposure", "Unknown")).strip() or "Unknown"
        out.append({"type": t, "count": max(0, count), "exposure": exposure})
    return out


@dataclass
class GRCReporter:
    """
    Accumulate findings and emit ``data_boar_grc_executive_report_v1`` JSON.

    Parameters
    ----------
    scope
        Human-readable scan scope (targets, limits).
    client_display_name
        Optional operator-supplied label (may be redacted in exports).
    client_name
        Deprecated alias for ``client_display_name`` (if both are set, values must match).
    session_id
        Optional SQLite session id.
    report_id
        Stable id; generated when omitted.
    scanner_version
        App version string; defaults to ``get_about_info()["version"]``.
    total_records_scanned
        Optional aggregate (cells/files inspected — operator-defined unit).
    """

    scope: str
    client_display_name: str | None = None
    session_id: str | None = None
    report_id: str | None = None
    scanner_version: str | None = None
    total_records_scanned: int | None = None
    client_name: str | None = None

    _detailed_findings: list[dict[str, Any]] = field(default_factory=list)
    _recommendations: list[dict[str, Any]] = field(default_factory=list)
    _compliance_mapping: dict[str, Any] = field(default_factory=dict)
    _scan_date_iso: str = field(default_factory=_utc_now_iso)
    _report_id: str = field(init=False)
    _scanner_version: str = field(init=False)
    _client_label: str | None = field(init=False)

    def __post_init__(self) -> None:
        if self.client_display_name is not None and self.client_name is not None:
            if self.client_display_name != self.client_name:
                raise ValueError(
                    "client_display_name and client_name differ; pass only one label."
                )
        self._client_label = self.client_display_name or self.client_name
        self._report_id = self.report_id or _new_report_id()
        self._scanner_version = (
            self.scanner_version.strip()
            if self.scanner_version
            else str(get_about_info()["version"])
        )

    def set_compliance_mapping(
        self,
        *,
        lgpd_articles_hint: list[str] | None = None,
        gdpr_articles_hint: list[str] | None = None,
        mapping_confidence: str | None = None,
    ) -> None:
        """Attach non-authoritative article hints for DPO workshop use."""
        if lgpd_articles_hint is not None:
            self._compliance_mapping["lgpd_articles_hint"] = list(lgpd_articles_hint)
        if gdpr_articles_hint is not None:
            self._compliance_mapping["gdpr_articles_hint"] = list(gdpr_articles_hint)
        if mapping_confidence is not None:
            self._compliance_mapping["mapping_confidence"] = mapping_confidence

    def add_recommendation(
        self,
        rec_id: str,
        priority: str,
        action: str,
        *,
        estimated_effort: str = "Unknown",
        regulatory_impact_note: str = "",
    ) -> None:
        self._recommendations.append(
            {
                "id": rec_id,
                "priority": priority,
                "action": action,
                "estimated_effort": estimated_effort,
                "regulatory_impact_note": regulatory_impact_note,
            }
        )

    def add_detailed_finding(
        self,
        asset_id: str,
        asset_class: str,
        risk_score: float,
        pii_types: list[dict[str, Any]],
        *,
        location_summary: str = "",
        violation_desc: str = "",
        norm_tags: list[str] | None = None,
        remediation_priority: RemediationPriority | str | None = None,
        data_category: DataCategory | str = "unknown",
        regulatory_impact: str = "",
        impact_score: float | None = None,
        likelihood_score: float | None = None,
        lgpd_density: LgpdDensityRiskConfig | None = None,
    ) -> None:
        """Append one risk-matrix row (schema §3 + boardroom fields)."""
        pii_norm = _normalize_pii_types(pii_types)
        cat = str(data_category or "unknown").strip().lower()
        if cat not in ("personal", "sensitive", "unknown"):
            cat = "unknown"
        density_meta: dict[str, Any] = {}
        if lgpd_density is not None:
            cap = float(lgpd_density.cap_raw)
            normalized, raw, breakdown, dominant = compute_asset_risk_density(
                pii_norm,
                cap_raw=cap,
            )
            # Density weights already encode LGPD-style rigour; do not apply
            # ``apply_data_category_risk_weight`` on top (avoids double counting).
            adjusted = max(0.0, min(100.0, float(normalized)))
            density_meta = {
                "risk_density_raw": raw,
                "risk_density_scaled_cap": cap,
                "risk_density_breakdown": breakdown,
                "risk_density_taxonomy_version": DENSITY_TAXONOMY_VERSION,
                "dominant_risk_taxonomy": dominant,
            }
            risk_input = adjusted
        else:
            adjusted = apply_data_category_risk_weight(risk_score, cat)
            risk_input = float(risk_score)
        imp = impact_score if impact_score is not None else None
        like = likelihood_score if likelihood_score is not None else None
        d_imp, d_like = default_heatmap_axes_from_risk(adjusted)
        if imp is None:
            imp = d_imp
        if like is None:
            like = d_like
        quadrant = heatmap_quadrant(float(imp), float(like))
        rp: str
        if remediation_priority is None:
            rp = remediation_priority_from_score(adjusted)
        else:
            rp = str(remediation_priority)
        row: dict[str, Any] = {
            "asset_id": asset_id,
            "asset_class": asset_class,
            "data_category": cat,
            "risk_score": float(adjusted),
            "risk_score_input": risk_input,
            "impact_score": float(imp),
            "likelihood_score": float(like),
            "heatmap_quadrant": quadrant,
            "pii_types": pii_norm,
            "location_summary": location_summary,
            "violation_desc": violation_desc,
            "norm_tags": list(norm_tags or []),
            "remediation_priority": rp,
            "regulatory_impact": str(regulatory_impact or ""),
        }
        row.update(density_meta)
        # Optional, non-breaking NIST CSF 2.0 function hint (issue #760): derived from
        # ``norm_tags`` via the shipped, versioned mapping table. Heuristic only, never a
        # compliance determination (ADR-0025); omit the field entirely when nothing maps.
        csf_hint = nist_csf_hints.csf_functions_for_norm_tags(row["norm_tags"])
        if csf_hint:
            row["nist_csf_function_hint"] = csf_hint
            self._ensure_nist_csf_hint_meta()
        self._detailed_findings.append(row)

    def _ensure_nist_csf_hint_meta(self) -> None:
        """
        Surface the CSF-hint disclaimer + mapping version once in ``compliance_mapping``.

        Keeps each ``detailed_findings`` row a plain array of short codes while the
        ADR-0025 disclaimer stays visible next to the other framework hints. Called only
        when at least one finding carries a ``nist_csf_function_hint``.
        """
        if "nist_csf_mapping_version" in self._compliance_mapping:
            return
        self._compliance_mapping["nist_csf_function_hint_method"] = NIST_CSF_HINT_METHOD
        self._compliance_mapping["nist_csf_mapping_version"] = (
            nist_csf_hints.mapping_version()
        )
        self._compliance_mapping["nist_csf_function_hint_disclaimer"] = (
            nist_csf_hints.disclaimer()
        )

    def add_finding(
        self,
        asset: str,
        pii_results: list[dict[str, Any]],
        risk_score: float,
        *,
        asset_class: str = "unspecified_asset",
        location_summary: str = "",
        violation_desc: str = "",
        norm_tags: list[str] | None = None,
        remediation_priority: RemediationPriority | str | None = None,
        data_category: DataCategory | str = "unknown",
        regulatory_impact: str = "",
        impact_score: float | None = None,
        likelihood_score: float | None = None,
        lgpd_density: LgpdDensityRiskConfig | None = None,
    ) -> None:
        """
        Thin API compatible with a simple consolidator: ``asset`` + ``pii_results`` + score.

        ``pii_results`` entries should include ``type`` and ``count``; ``exposure`` optional.

        When ``lgpd_density`` is set, ``risk_score`` is ignored and the row score is derived
        from ``report.grc_risk_taxonomy`` (LGPD-aligned density table).
        """
        self.add_detailed_finding(
            asset,
            asset_class,
            risk_score,
            pii_results,
            location_summary=location_summary,
            violation_desc=violation_desc,
            norm_tags=norm_tags,
            remediation_priority=remediation_priority,
            data_category=data_category,
            regulatory_impact=regulatory_impact,
            impact_score=impact_score,
            likelihood_score=likelihood_score,
            lgpd_density=lgpd_density,
        )

    def _pii_instance_total(self) -> int:
        total = 0
        for f in self._detailed_findings:
            for p in f.get("pii_types") or []:
                if isinstance(p, dict):
                    total += int(p.get("count", 0) or 0)
        return total

    def _critical_asset_count(self, threshold: float = 80.0) -> int:
        return sum(
            1
            for f in self._detailed_findings
            if float(f.get("risk_score", 0)) > threshold
        )

    def _build_executive_summary(self) -> dict[str, Any]:
        scores = [float(f.get("risk_score", 0.0)) for f in self._detailed_findings]
        trs = self.total_records_scanned
        if trs is None:
            trs = 0
        return {
            "total_records_scanned": int(trs),
            "pii_instances_found": self._pii_instance_total(),
            "critical_assets_at_risk": self._critical_asset_count(),
            "compliance_score": compliance_score_heuristic_v1(scores),
            "risk_level": risk_level_from_findings(scores),
            "compliance_score_method": COMPLIANCE_SCORE_METHOD,
        }

    def to_dict(self) -> dict[str, Any]:
        """Return the full ``data_boar_grc_executive_report_v1`` payload."""
        meta: dict[str, Any] = {
            "report_id": self._report_id,
            "scan_date": self._scan_date_iso,
            "scanner_version": self._scanner_version,
            "scope": self.scope,
        }
        if self._client_label:
            meta["client_display_name"] = self._client_label
        if self.session_id:
            meta["session_id"] = self.session_id

        payload: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "report_metadata": meta,
            "executive_summary": self._build_executive_summary(),
            "compliance_mapping": dict(self._compliance_mapping),
            "detailed_findings": list(self._detailed_findings),
            "recommendations": list(self._recommendations),
        }
        return payload

    def export_json(self, filepath: str | Path) -> None:
        """Write UTF-8 JSON with stable key ordering for readable diffs."""
        path = Path(filepath)
        text = json.dumps(self.to_dict(), indent=2, ensure_ascii=False) + "\n"
        path.write_text(text, encoding="utf-8")
