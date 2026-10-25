#!/usr/bin/env python3
"""
Build ``data_boar_grc_executive_report_v1`` JSON for lab completão close-out.

Reads an optional *raw scan* payload (operator-supplied structured counts) and/or
``lab_result.json`` from the orchestrator for scope/session context. When no asset
rows exist, emits a connectivity-only report with a single recommendation stub.

**Input shapes (both supported):**

- Canonical: ``assets[].asset_id`` + ``pii_types`` as ``[{ "type", "count" }, ...]``.
- Workshop / "slice" shape: ``assets[].id`` + ``findings`` (same list-of-dicts).

Taxonomy weights and law **hints** live in ``core.intelligence`` — extend there for
new pattern labels; subclass :class:`GRCReportBuilder` to add ingest or post-steps.

This is **not** a substitute for a full product scan; it wires the GRC consolidator
into automation (PowerShell orchestrator).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from core.intelligence import regulatory_impact_from_findings

from report.grc_reporter import GRCReporter
from report.grc_risk_taxonomy import LgpdDensityRiskConfig


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _scope_from_lab(lab: dict[str, Any]) -> tuple[str, str | None]:
    stamp = str(lab.get("run_stamp", "") or "").strip()
    status = str(lab.get("overall_status", "") or "").strip()
    conn = lab.get("connectivity_status")
    summary = ""
    if isinstance(conn, dict):
        summary = str(conn.get("summary", "") or "").strip()
    scope = (
        "Lab completão (orchestrator)"
        + (f"; run_stamp={stamp}" if stamp else "")
        + (f"; overall_status={status}" if status else "")
        + (f"; connectivity_summary={summary}" if summary else "")
    )
    return scope, stamp or None


def _entries_from_type_count_list(
    items: list[Any], *, count_default_if_missing: int
) -> list[dict[str, Any]]:
    """Parse ``[{type, count?}, ...]`` into positive-count rows."""
    out: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, Mapping):
            continue
        t = str(item.get("type", "")).strip()
        if not t:
            continue
        raw_c = item.get("count", count_default_if_missing)
        try:
            c = int(raw_c)
        except (TypeError, ValueError):
            c = count_default_if_missing
        if c <= 0:
            continue
        out.append({"type": t, "count": c})
    return out


def _normalize_pii_entries(row: dict[str, Any]) -> list[dict[str, Any]]:
    """Return ``[{type, count}, ...]`` from ``pii_types`` and/or ``findings``."""
    pii = row.get("pii_types")
    if isinstance(pii, list) and pii:
        out = _entries_from_type_count_list(pii, count_default_if_missing=0)
        if out:
            return out
    find = row.get("findings")
    if isinstance(find, list):
        return _entries_from_type_count_list(find, count_default_if_missing=1)
    return []


def _normalize_asset_row(row: dict[str, Any]) -> dict[str, Any] | None:
    """Unify ``asset_id`` / ``id`` and attach normalized ``pii_types``."""
    aid = str(row.get("asset_id") or row.get("id") or "").strip()
    if not aid:
        return None
    merged = _normalize_pii_entries(row)
    out = dict(row)
    out["asset_id"] = aid
    out["pii_types"] = merged
    return out


def _norm_tags(norm: dict[str, Any]) -> list[str]:
    nt = norm.get("norm_tags")
    return [str(x) for x in nt] if isinstance(nt, list) else []


def _regulatory_impact_for_row(norm: dict[str, Any], pii: list[dict[str, Any]]) -> str:
    reg = str(norm.get("regulatory_impact", "") or "").strip()
    if reg or not pii:
        return reg
    return regulatory_impact_from_findings(pii)


def _parse_use_density_flag(norm: dict[str, Any]) -> bool:
    use_density = norm.get("use_lgpd_density_risk", True)
    if isinstance(use_density, str):
        return use_density.strip().lower() in ("1", "true", "yes")
    return bool(use_density)


def _add_one_asset_row(r: GRCReporter, norm: dict[str, Any]) -> None:
    aid = str(norm["asset_id"])
    pii = norm.get("pii_types") or []
    if not isinstance(pii, list):
        pii = []
    asset_class = str(norm.get("asset_class", "database_table") or "database_table")
    loc = str(norm.get("location_summary", "") or "")
    vdesc = str(norm.get("violation_desc", "") or "")
    dc = str(norm.get("data_category", "unknown") or "unknown")
    reg = _regulatory_impact_for_row(norm, pii)
    use_density = _parse_use_density_flag(norm)
    kwargs: dict[str, Any] = {
        "asset_class": asset_class,
        "location_summary": loc,
        "violation_desc": vdesc,
        "norm_tags": _norm_tags(norm),
        "data_category": dc,
        "regulatory_impact": reg,
    }
    if use_density:
        cap = norm.get("density_cap_raw")
        cfg = (
            LgpdDensityRiskConfig(cap_raw=float(cap))
            if cap is not None
            else LgpdDensityRiskConfig()
        )
        r.add_finding(aid, pii, 0.0, lgpd_density=cfg, **kwargs)
        return
    rs = float(norm.get("risk_score", 0.0) or 0.0)
    r.add_finding(aid, pii, rs, **kwargs)


def _apply_raw_assets(r: GRCReporter, raw: dict[str, Any]) -> None:
    assets = raw.get("assets")
    if not isinstance(assets, list):
        return
    for row in assets:
        if not isinstance(row, dict):
            continue
        norm = _normalize_asset_row(row)
        if norm is None:
            continue
        _add_one_asset_row(r, norm)


def _attach_compliance_mapping(r: GRCReporter, raw: dict[str, Any]) -> None:
    cm = raw.get("compliance_mapping")
    if not isinstance(cm, dict):
        return
    lg = cm.get("lgpd_articles_hint")
    gd = cm.get("gdpr_articles_hint")
    conf = cm.get("mapping_confidence")
    r.set_compliance_mapping(
        lgpd_articles_hint=list(lg) if isinstance(lg, list) else None,
        gdpr_articles_hint=list(gd) if isinstance(gd, list) else None,
        mapping_confidence=str(conf) if conf is not None else None,
    )


class GRCReportBuilder:
    """
    Thin facade over :class:`GRCReporter` for lab hooks and agent extension.

    Override :meth:`ingest_raw_assets` in a subclass to add pre/post processing;
    keep exports on ``data_boar_grc_executive_report_v1``.
    """

    def __init__(self, reporter: GRCReporter) -> None:
        self._reporter = reporter

    @property
    def reporter(self) -> GRCReporter:
        return self._reporter

    def attach_compliance_mapping(self, raw: dict[str, Any]) -> None:
        _attach_compliance_mapping(self._reporter, raw)

    def ingest_raw_assets(self, raw: dict[str, Any]) -> None:
        _apply_raw_assets(self._reporter, raw)

    def finalize_recommendations(self) -> None:
        """Connectivity stub when empty; P0 crypto nudge when density marks critical assets."""
        snap = self._reporter.to_dict()
        findings = snap.get("detailed_findings") or []
        if not findings:
            self._reporter.add_recommendation(
                "REC-LAB-ORCH-01",
                "P2",
                "No structured PII rows in raw scan input; this JSON reflects lab orchestration context only. "
                "Run a Data Boar product scan and pass ``assets`` in the raw payload (or SQLite ingest when available) "
                "for density-based GRC rows.",
                estimated_effort="Low",
                regulatory_impact_note="Workshop placeholder; not a legal adequacy statement.",
            )
            return
        crit = int(snap["executive_summary"].get("critical_assets_at_risk", 0) or 0)
        if crit <= 0:
            return
        ids = {
            str(x.get("id", ""))
            for x in (snap.get("recommendations") or [])
            if isinstance(x, dict)
        }
        if "REC-GRC-CRITICAL-CRYPTO" in ids:
            return
        self._reporter.add_recommendation(
            "REC-GRC-CRITICAL-CRYPTO",
            "P0",
            "Encrypt or strongly restrict fields classified as FINANCIAL or SENSITIVE; "
            "narrow retention and access pending DPO review.",
            estimated_effort="Medium",
            regulatory_impact_note="Workshop placeholder; not a legal adequacy statement.",
        )

    def export(self, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self._reporter.export_json(output_path)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Generate GRC executive JSON (lab hook).")
    p.add_argument("--output", required=True, help="Path to write GRC JSON.")
    p.add_argument(
        "--input",
        default="",
        help="Optional raw scan JSON (see schemas/grc_raw_scan_input.example.json).",
    )
    p.add_argument(
        "--lab-result",
        default="",
        help="Optional lab_result.json from lab-completao-orchestrate.ps1.",
    )
    args = p.parse_args(argv)

    out_path = Path(args.output)
    raw: dict[str, Any] = {}
    if args.input:
        ip = Path(args.input)
        if ip.is_file():
            raw = _load_json(ip)

    lab: dict[str, Any] = {}
    if args.lab_result:
        lp = Path(args.lab_result)
        if lp.is_file():
            lab = _load_json(lp)

    if lab:
        scope, session_id = _scope_from_lab(lab)
    else:
        scope = str(
            raw.get("scope") or "GRC generate_grc_report (no lab_result.json)"
        ).strip()
        session_id = str(raw.get("session_id") or "").strip() or None

    if str(raw.get("scope", "")).strip():
        scope = str(raw["scope"]).strip()

    client = str(raw.get("client_display_name") or "Lab (operator)").strip()
    trs = raw.get("total_records_scanned")
    total_records: int | None
    try:
        total_records = int(trs) if trs is not None else None
    except (TypeError, ValueError):
        total_records = None

    r = GRCReporter(
        scope,
        client_display_name=client,
        session_id=session_id,
        total_records_scanned=total_records,
    )
    builder = GRCReportBuilder(r)
    builder.attach_compliance_mapping(raw)
    builder.ingest_raw_assets(raw)
    builder.finalize_recommendations()
    builder.export(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
