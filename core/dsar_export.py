"""
DSAR-oriented export: structured JSON for data-subject access workflows.

Assists technical inventory (LGPD Art. 18 / GDPR Art. 15 style access narratives);
does not determine legal rights, exemptions, or response deadlines.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from core.about import get_about_info

DSAR_SCHEMA_VERSION = 1

_DSAR_LEGAL_BASIS = {
    "lgpd": (
        "LGPD Art. 18 — O titular tem direito de acesso aos dados pessoais tratados."
    ),
    "gdpr": "GDPR Art. 15 — Right of access by the data subject.",
    "ccpa": (
        "CCPA § 1798.110 — Right to know categories and specific pieces of "
        "personal information."
    ),
}

# Keys that may hold raw sample values when present on finding rows (opt-in only).
_SAMPLE_FIELD_KEYS = frozenset({"sample_content", "sample_value", "raw_sample"})


def _db_location(row: dict[str, Any]) -> str:
    parts = [row.get("schema_name"), row.get("table_name"), row.get("column_name")]
    return ".".join(p for p in parts if p)


def _finding_entry(
    row: dict[str, Any],
    *,
    source_type: str,
    include_samples: bool,
) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "sensitivity": row.get("sensitivity_level"),
        "pattern": row.get("pattern_detected"),
        "norm_tag": row.get("norm_tag"),
    }
    if source_type == "database":
        entry["location"] = _db_location(row)
    else:
        entry["location"] = row.get("path")
        entry["file"] = row.get("file_name")
    if include_samples:
        for key in _SAMPLE_FIELD_KEYS:
            if row.get(key) is not None:
                entry[key] = row[key]
    return entry


def build_dsar_payload(
    db_manager: Any,
    *,
    session_id: str,
    include_samples: bool = False,
) -> dict[str, Any]:
    """
    Build a JSON-serializable DSAR export for one scan session.

    Parameters
    ----------
    db_manager
        ``LocalDBManager`` instance (typed as Any to avoid circular imports).
    session_id
        UUID of the scan session to export.
    include_samples
        When True, include raw sample fields from finding rows when stored.
        SQLite findings are metadata-only by default (no sample columns).
    """
    sid = (session_id or "").strip()
    about = get_about_info()

    db_rows, fs_rows, _failures = db_manager.get_findings(sid)

    findings_by_source: dict[str, Any] = {}

    for row in db_rows:
        target = row.get("target_name") or "unknown"
        bucket = findings_by_source.setdefault(
            target,
            {"source_type": "database", "findings": []},
        )
        bucket["findings"].append(
            _finding_entry(row, source_type="database", include_samples=include_samples)
        )

    for row in fs_rows:
        target = row.get("target_name") or "unknown"
        bucket = findings_by_source.setdefault(
            target,
            {"source_type": "filesystem", "findings": []},
        )
        bucket["findings"].append(
            _finding_entry(
                row, source_type="filesystem", include_samples=include_samples
            )
        )

    all_rows = list(db_rows) + list(fs_rows)
    total = len(all_rows)
    high = sum(1 for r in all_rows if r.get("sensitivity_level") == "HIGH")

    return {
        "schema_version": DSAR_SCHEMA_VERSION,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "legal_basis": dict(_DSAR_LEGAL_BASIS),
        "session_id": sid,
        "application": {
            "name": about["name"],
            "version": about["version"],
        },
        "summary": {
            "total_findings": total,
            "high_sensitivity": high,
            "sources_scanned": len(findings_by_source),
        },
        "findings_by_source": findings_by_source,
        "export_options": {
            "include_samples": include_samples,
        },
        "notes": (
            "Technical inventory export only — not legal advice. "
            "Review with DPO/legal counsel before sharing with a data subject. "
            "Finding rows in SQLite store metadata by default; raw cell samples "
            "are omitted unless explicitly requested and present on stored rows."
        ),
    }
