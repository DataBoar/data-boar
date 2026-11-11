"""Record of Processing Activities (RoPA) evidence export (#837).

GDPR Art. 30 / LGPD Art. 37 style register, built from what a Data Boar scan
actually observed. The scan knows WHICH personal-data categories were detected,
WHERE (source / location), at what sensitivity and under which norm tags. It
does NOT know the controller/DPO, purposes, legal basis, recipients, transfers,
retention or security measures (Art. 30(1)(a)-(g)). Those come from an optional
``ropa:`` config block; whatever is missing is written as ``A COMPLETAR``.

Language is EVIDENCE, never a legal conclusion: this is a technical inventory a
DPO can complete and review. Metadata only — no samples, no content.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from core.about import get_about_info
from core.findings_common import (
    SENSITIVITY_RANK,
    FindingRecord,
    collect_session_findings,
    session_meta,
)
from report.excel_sanitizer import excel_sanitize_cell
from report.safe_prefix import safe_session_prefix

ROPA_SCHEMA_VERSION = 1
PENDING = "A COMPLETAR"
STATUS_DECLARED = "declared_in_config"
STATUS_PENDING = "pending"
MAX_LOCATIONS_PER_SOURCE = 200

CONTROLLER_FIELDS = ("name", "contact", "representative", "dpo_name", "dpo_contact")
LIST_FIELDS = (
    "data_subject_categories",
    "purposes",
    "legal_basis",
    "recipients",
    "transfers",
    "security_measures",
)
SCALAR_FIELDS = ("retention",)
ACTIVITY_FIELDS = LIST_FIELDS + SCALAR_FIELDS

# Art. 30(1) letter for each non-scan field (documentation in the export).
ARTICLE_REF = {
    "controller": "Art. 30(1)(a)",
    "purposes": "Art. 30(1)(b)",
    "data_subject_categories": "Art. 30(1)(c)",
    "personal_data_categories": "Art. 30(1)(c)",
    "recipients": "Art. 30(1)(d)",
    "transfers": "Art. 30(1)(e)",
    "retention": "Art. 30(1)(f)",
    "security_measures": "Art. 30(1)(g)",
    "legal_basis": "Art. 6 GDPR / Art. 7 LGPD (not part of Art. 30(1); DPO input)",
}

EVIDENCE_NOTICE = (
    "Technical inventory built from Data Boar scan metadata (detector labels, "
    "locations, sensitivity, norm tags). It is evidence to support a Record of "
    "Processing Activities, not a legal conclusion and not a complete register. "
    "Fields marked 'A COMPLETAR' are NOT known to the scanner and must be "
    "completed and reviewed by the controller / DPO. No sample content is exported."
)


def _field(value: Any) -> dict[str, Any]:
    """Wrap a value with its provenance; empty values become ``A COMPLETAR``."""
    if value in (None, "", [], ()):
        return {"value": PENDING, "status": STATUS_PENDING}
    return {"value": value, "status": STATUS_DECLARED}


def _merge_activity(
    defaults: dict[str, Any], override: dict[str, Any] | None
) -> dict[str, Any]:
    merged: dict[str, Any] = {k: defaults.get(k) for k in ACTIVITY_FIELDS}
    for key in ACTIVITY_FIELDS:
        if override and override.get(key):
            merged[key] = override[key]
    return merged


def _find_activity(
    activities: list[dict[str, Any]], target: str
) -> dict[str, Any] | None:
    for act in activities:
        if act.get("target") == target:
            return act
    low = target.lower()
    for act in activities:
        if str(act.get("target") or "").lower() == low:
            return act
    return None


def _top_sensitivity(records: list[FindingRecord]) -> str:
    best = max((SENSITIVITY_RANK.get(r.sensitivity, 0) for r in records), default=0)
    for name, rank in SENSITIVITY_RANK.items():
        if rank == best:
            return name
    return "UNSPECIFIED"


def _source_entry(
    target: str,
    records: list[FindingRecord],
    ropa_cfg: dict[str, Any],
) -> dict[str, Any]:
    activity = _find_activity(ropa_cfg.get("activities") or [], target)
    fields = _merge_activity(ropa_cfg.get("defaults") or {}, activity)

    categories: dict[str, dict[str, Any]] = {}
    norms: set[str] = set()
    sens_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for rec in records:
        if rec.sensitivity in sens_counts:
            sens_counts[rec.sensitivity] += 1
        if rec.norm_tag:
            norms.add(rec.norm_tag)
        for label in rec.patterns:
            cat = categories.setdefault(
                label, {"label": label, "findings": 0, "max_sensitivity": ""}
            )
            cat["findings"] += 1
            if SENSITIVITY_RANK.get(rec.sensitivity, 0) > SENSITIVITY_RANK.get(
                cat["max_sensitivity"], 0
            ):
                cat["max_sensitivity"] = rec.sensitivity

    locations = [
        {
            "location": rec.location,
            "sensitivity": rec.sensitivity or "UNSPECIFIED",
            "patterns": rec.patterns,
            "norm_tag": rec.norm_tag,
        }
        for rec in records[:MAX_LOCATIONS_PER_SOURCE]
    ]

    source_type = records[0].kind if records else "unknown"
    return {
        "target": target,
        "source_type": source_type,
        "processing_activity": _field((activity or {}).get("name")),
        "scan_evidence": {
            "personal_data_categories": sorted(
                categories.values(), key=lambda c: (-c["findings"], c["label"])
            ),
            "max_sensitivity": _top_sensitivity(records),
            "sensitivity_counts": sens_counts,
            "norm_tags": sorted(norms),
            "findings_total": len(records),
            "locations": locations,
            "locations_total": len(records),
            "locations_truncated": len(records) > MAX_LOCATIONS_PER_SOURCE,
        },
        "art30_fields": {name: _field(fields.get(name)) for name in ACTIVITY_FIELDS},
    }


def build_ropa_payload(
    db_manager: Any,
    *,
    session_id: str,
    ropa_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the JSON-serializable RoPA evidence register for one session.

    Raises :class:`core.findings_common.UnknownSessionError` for an unknown
    session (a silently empty register would read as "no processing").
    """
    sid = (session_id or "").strip()
    cfg = ropa_config or {}
    meta = session_meta(db_manager, sid)
    records, failures = collect_session_findings(db_manager, sid)
    about = get_about_info()

    by_target: dict[str, list[FindingRecord]] = {}
    for rec in records:
        by_target.setdefault(rec.target, []).append(rec)

    sources = [
        _source_entry(target, recs, cfg) for target, recs in sorted(by_target.items())
    ]

    declared_only = sorted(
        str(act.get("target"))
        for act in (cfg.get("activities") or [])
        if act.get("target") and not _find_in_targets(str(act["target"]), by_target)
    )

    controller_cfg = cfg.get("controller") or {}
    controller = {name: _field(controller_cfg.get(name)) for name in CONTROLLER_FIELDS}

    pending = sum(
        1 for c in controller.values() if c["status"] == STATUS_PENDING
    ) + sum(
        1
        for src in sources
        for f in src["art30_fields"].values()
        if f["status"] == STATUS_PENDING
    )
    categories_all = sorted({lb for r in records for lb in r.patterns})

    return {
        "schema_version": ROPA_SCHEMA_VERSION,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "session_id": sid,
        "application": {"name": about["name"], "version": about["version"]},
        "framework": {
            "gdpr": "GDPR Art. 30 (records of processing activities)",
            "lgpd": "LGPD Art. 37 (registro das operações de tratamento)",
        },
        "article_30_reference": dict(ARTICLE_REF),
        "evidence_notice": EVIDENCE_NOTICE,
        "session": {
            "status": meta.get("status"),
            "started_at": meta.get("started_at"),
            "finished_at": meta.get("finished_at"),
            "tenant_name": meta.get("tenant_name"),
        },
        "controller": controller,
        "summary": {
            "sources_with_findings": len(sources),
            "total_findings": len(records),
            "personal_data_categories_detected": categories_all,
            "scan_failures": failures,
            "fields_pending_completion": pending,
            "declared_activities_without_scan_evidence": declared_only,
        },
        "records": sources,
        "export_options": {"metadata_only": True},
    }


def _find_in_targets(target: str, by_target: dict[str, Any]) -> bool:
    low = target.lower()
    return any(t == target or t.lower() == low for t in by_target)


def ropa_json_text(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def _join(value: Any) -> str:
    if isinstance(value, list):
        return "; ".join(str(v) for v in value)
    return "" if value is None else str(value)


_HEADER_FILL = PatternFill("solid", fgColor="DDE6F0")
_PENDING_FILL = PatternFill("solid", fgColor="FFF2CC")


def _write_row(ws: Any, row: list[Any], *, header: bool = False) -> None:
    ws.append([excel_sanitize_cell(v) for v in row])
    if header:
        for cell in ws[ws.max_row]:
            cell.font = Font(bold=True)
            cell.fill = _HEADER_FILL
            cell.alignment = Alignment(wrap_text=True, vertical="top")


def _autosize(ws: Any, *, max_width: int = 60) -> None:
    widths: dict[int, int] = {}
    for row in ws.iter_rows():
        for cell in row:
            if cell.value is None:
                continue
            longest = max(len(line) for line in str(cell.value).splitlines() or [""])
            widths[cell.column] = max(widths.get(cell.column, 8), longest + 2)
    for col, width in widths.items():
        ws.column_dimensions[get_column_letter(col)].width = min(width, max_width)
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")


def write_ropa_xlsx(payload: dict[str, Any], dest: Path) -> Path:
    """Write the register as an Excel workbook (cells sanitized against formulas)."""
    wb = Workbook()

    ws = wb.active
    ws.title = "RoPA"
    _write_row(
        ws,
        [
            "Source / Fonte",
            "Source type",
            "Processing activity (declared)",
            "Data subject categories - Art. 30(1)(c)",
            "Personal data categories detected (scan evidence) - Art. 30(1)(c)",
            "Max sensitivity",
            "Findings",
            "Norm references (scan)",
            "Purposes - Art. 30(1)(b)",
            "Legal basis (DPO input)",
            "Recipients - Art. 30(1)(d)",
            "Transfers to third countries - Art. 30(1)(e)",
            "Retention / erasure time limits - Art. 30(1)(f)",
            "Security measures - Art. 30(1)(g)",
        ],
        header=True,
    )
    for src in payload["records"]:
        ev = src["scan_evidence"]
        cats = "; ".join(
            f"{c['label']} ({c['findings']})" for c in ev["personal_data_categories"]
        )
        f = src["art30_fields"]
        row = [
            src["target"],
            src["source_type"],
            _join(src["processing_activity"]["value"]),
            _join(f["data_subject_categories"]["value"]),
            cats,
            ev["max_sensitivity"],
            ev["findings_total"],
            "; ".join(ev["norm_tags"]),
            _join(f["purposes"]["value"]),
            _join(f["legal_basis"]["value"]),
            _join(f["recipients"]["value"]),
            _join(f["transfers"]["value"]),
            _join(f["retention"]["value"]),
            _join(f["security_measures"]["value"]),
        ]
        _write_row(ws, row)
        for cell in ws[ws.max_row]:
            if cell.value == PENDING:
                cell.fill = _PENDING_FILL
    _autosize(ws)

    wc = wb.create_sheet("Controller")
    _write_row(wc, ["Field", "Reference", "Value", "Status"], header=True)
    labels = {
        "name": "Controller name",
        "contact": "Controller contact",
        "representative": "Representative (if applicable)",
        "dpo_name": "DPO / Encarregado",
        "dpo_contact": "DPO contact",
    }
    for key, label in labels.items():
        fld = payload["controller"][key]
        _write_row(
            wc, [label, ARTICLE_REF["controller"], _join(fld["value"]), fld["status"]]
        )
        if fld["status"] == STATUS_PENDING:
            wc[wc.max_row][2].fill = _PENDING_FILL
    _autosize(wc)

    wl = wb.create_sheet("Locations")
    _write_row(
        wl,
        ["Source", "Location (metadata)", "Sensitivity", "Detectors", "Norm reference"],
        header=True,
    )
    for src in payload["records"]:
        for loc in src["scan_evidence"]["locations"]:
            _write_row(
                wl,
                [
                    src["target"],
                    loc["location"],
                    loc["sensitivity"],
                    "; ".join(loc["patterns"]),
                    loc["norm_tag"],
                ],
            )
        if src["scan_evidence"]["locations_truncated"]:
            _write_row(
                wl,
                [
                    src["target"],
                    f"... truncated at {MAX_LOCATIONS_PER_SOURCE} of "
                    f"{src['scan_evidence']['locations_total']} locations",
                    "",
                    "",
                    "",
                ],
            )
    _autosize(wl)

    wn = wb.create_sheet("Notes")
    summ = payload["summary"]
    app = payload["application"]
    notes = [
        ("Evidence notice", payload["evidence_notice"]),
        ("Session", payload["session_id"]),
        ("Exported at (UTC)", payload["exported_at"]),
        ("Application", f"{app['name']} {app['version']}"),
        (
            "Frameworks",
            f"{payload['framework']['gdpr']} | {payload['framework']['lgpd']}",
        ),
        ("Sources with findings", summ["sources_with_findings"]),
        ("Total findings", summ["total_findings"]),
        ("Scan failures (coverage gap)", summ["scan_failures"]),
        ("Fields pending completion (A COMPLETAR)", summ["fields_pending_completion"]),
        (
            "Declared activities without scan evidence",
            "; ".join(summ["declared_activities_without_scan_evidence"]) or "-",
        ),
    ]
    _write_row(wn, ["Item", "Value"], header=True)
    for item in notes:
        _write_row(wn, list(item))
    _autosize(wn, max_width=100)

    dest.parent.mkdir(parents=True, exist_ok=True)
    wb.save(dest)
    return dest


def write_ropa_outputs(payload: dict[str, Any], out_dir: Path) -> dict[str, Path]:
    """Write ``ropa_<session>.json`` and ``ropa_<session>.xlsx`` under ``out_dir``."""
    prefix = safe_session_prefix(payload["session_id"], max_len=16)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"ropa_{prefix}.json"
    json_path.write_text(ropa_json_text(payload), encoding="utf-8")
    xlsx_path = write_ropa_xlsx(payload, out_dir / f"ropa_{prefix}.xlsx")
    return {"json": json_path, "xlsx": xlsx_path}
