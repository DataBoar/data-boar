"""SARIF 2.1.0 export of one scan session's findings (#838).

Metadata only: every result carries a location, a detector label, a
sensitivity-derived level and a norm tag. Never sample content. SARIF here is
*evidence of where a detector matched*, not a legal conclusion.

Mapping
-------
* ``rules``   — one per distinct detector label in ``pattern_detected``
  (the detector joins several hits with ``", "``; each hit becomes its own rule).
* ``results`` — one per (finding row, detector label).
* ``level``   — HIGH -> ``error``, MEDIUM -> ``warning``, LOW -> ``note``.
* ``locations`` — filesystem rows: ``physicalLocation.artifactLocation.uri``
  (percent-encoded); database rows: ``logicalLocations`` (target.schema.table.column);
  application rows: ``logicalLocations`` (target / object / field).
* ``partialFingerprints`` — SHA-256 prefix of the same identity key
  ``--diff`` uses, so downstream tools can deduplicate across runs.
* ``baselineState`` — only when a previous comparable session exists.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from pathlib import PurePosixPath, PureWindowsPath
from typing import Any
from urllib.parse import quote

from core.about import get_about_info
from core.findings_common import (
    NO_DELTA,
    FindingRecord,
    SessionDelta,
    collect_session_findings,
    compute_session_delta,
    session_meta,
)

SARIF_VERSION = "2.1.0"
SARIF_SCHEMA = "https://json.schemastore.org/sarif-2.1.0.json"
RULE_ID_PREFIX = "DATABOAR."
FINGERPRINT_NAME = "dataBoarFindingKey/v1"

_LEVEL_BY_SENSITIVITY = {"HIGH": "error", "MEDIUM": "warning", "LOW": "note"}
_LEVEL_RANK = {"note": 1, "warning": 2, "error": 3}
_SLUG_RE = re.compile(r"[^A-Za-z0-9_.-]+")
_WIN_DRIVE_RE = re.compile(r"^[A-Za-z]:[\\/]")


def sarif_level(sensitivity: str) -> str:
    return _LEVEL_BY_SENSITIVITY.get((sensitivity or "").upper(), "note")


def _slug(label: str) -> str:
    s = _SLUG_RE.sub("_", label).strip("_.-")
    return s[:60] or "UNSPECIFIED"


def build_rule_ids(labels: set[str]) -> dict[str, str]:
    """Stable, SARIF-safe rule id per detector label.

    Two labels whose slugs collide both get a short hash suffix, so an id never
    silently merges two different detectors.
    """
    by_slug: dict[str, list[str]] = {}
    for label in sorted(labels):
        by_slug.setdefault(_slug(label), []).append(label)
    out: dict[str, str] = {}
    for slug, group in by_slug.items():
        for label in group:
            if len(group) == 1:
                out[label] = f"{RULE_ID_PREFIX}{slug}"
            else:
                digest = hashlib.sha256(label.encode("utf-8")).hexdigest()[:6]
                out[label] = f"{RULE_ID_PREFIX}{slug}-{digest}"
    return out


def artifact_uri(path: str | None, file_name: str | None) -> str | None:
    """Percent-encoded URI reference for a filesystem finding (metadata only)."""
    if not path and not file_name:
        return None
    raw = (path or "").rstrip("/\\")
    if file_name:
        raw = f"{raw}/{file_name}" if raw else file_name
    if _WIN_DRIVE_RE.match(raw):
        return PureWindowsPath(raw.replace("/", "\\")).as_uri()
    if raw.startswith("/"):
        return PurePosixPath(raw).as_uri()
    return quote(raw.replace("\\", "/"), safe="/")


def _logical_locations(rec: FindingRecord) -> list[dict[str, Any]]:
    if rec.kind == "database":
        parts = [rec.target, rec.schema, rec.table, rec.column]
        fq = ".".join(str(p) for p in parts if p)
        name = str(rec.column or rec.table or rec.target)
        kind = "member" if rec.column else "type"
        return [{"name": name, "fullyQualifiedName": fq, "kind": kind}]
    fq = "/".join(str(p) for p in (rec.target, rec.path, rec.file_name) if p)
    return [
        {
            "name": str(rec.file_name or rec.path or rec.target),
            "fullyQualifiedName": fq,
            "kind": "member",
        }
    ]


def _locations(rec: FindingRecord) -> list[dict[str, Any]]:
    loc: dict[str, Any] = {"logicalLocations": _logical_locations(rec)}
    if rec.kind == "filesystem":
        uri = artifact_uri(rec.path, rec.file_name)
        if uri:
            loc["physicalLocation"] = {"artifactLocation": {"uri": uri}}
    return [loc]


def _message(rec: FindingRecord, label: str) -> str:
    where = rec.location or rec.target
    norm = f" Norm reference: {rec.norm_tag}." if rec.norm_tag else ""
    sens = rec.sensitivity or "UNSPECIFIED"
    return (
        f"Detector '{label}' matched metadata at {where} (sensitivity {sens}; "
        f"source {rec.target}).{norm} Evidence only: no content sampled, "
        "not a legal conclusion."
    )


def build_sarif_document(
    records: list[FindingRecord],
    *,
    session_id: str,
    meta: dict[str, Any] | None = None,
    delta: SessionDelta = NO_DELTA,
    scan_failures: int = 0,
    extra_run_properties: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a SARIF 2.1.0 log from already-collected records."""
    about = get_about_info()
    meta = meta or {}

    labels: set[str] = set()
    for rec in records:
        labels.update(rec.patterns)
    rule_ids = build_rule_ids(labels)

    # Highest level + norm tags seen per label (drives rule defaults).
    rule_level: dict[str, str] = {}
    rule_norms: dict[str, set[str]] = {}
    for rec in records:
        lvl = sarif_level(rec.sensitivity)
        for label in rec.patterns:
            if _LEVEL_RANK[lvl] > _LEVEL_RANK.get(rule_level.get(label, ""), 0):
                rule_level[label] = lvl
            if rec.norm_tag:
                rule_norms.setdefault(label, set()).add(rec.norm_tag)

    ordered_labels = sorted(labels, key=lambda lb: rule_ids[lb])
    rule_index = {label: i for i, label in enumerate(ordered_labels)}
    rules: list[dict[str, Any]] = []
    for label in ordered_labels:
        rules.append(
            {
                "id": rule_ids[label],
                "name": _slug(label),
                "shortDescription": {"text": f"Personal-data indicator: {label}"},
                "fullDescription": {
                    "text": (
                        f"Metadata evidence that the Data Boar detector '{label}' "
                        "matched at this location. Content is never exported. "
                        "Review with your DPO; this is not a legal conclusion."
                    )
                },
                "defaultConfiguration": {"level": rule_level.get(label, "note")},
                "properties": {
                    "tags": ["privacy", "personal-data", "data-boar"],
                    "norm_tags": sorted(rule_norms.get(label, set())),
                },
            }
        )

    results: list[dict[str, Any]] = []
    for rec in records:
        for label in rec.patterns:
            result: dict[str, Any] = {
                "ruleId": rule_ids[label],
                "ruleIndex": rule_index[label],
                "level": sarif_level(rec.sensitivity),
                "message": {"text": _message(rec, label)},
                "locations": _locations(rec),
                "partialFingerprints": {FINGERPRINT_NAME: rec.fingerprint(label)},
                "properties": {
                    "sensitivity": rec.sensitivity or "UNSPECIFIED",
                    "norm_tag": rec.norm_tag,
                    "source_type": rec.kind,
                    "target": rec.target,
                },
            }
            if delta.available:
                result["baselineState"] = "new" if delta.is_new(rec) else "unchanged"
            results.append(result)

    run_props: dict[str, Any] = {
        "session_id": session_id,
        "metadata_only": True,
        "scan_failures": scan_failures,
        "previous_session_id": delta.previous_session_id,
        "new_findings_count": delta.new_findings_count,
        "resolved_count": delta.resolved_count,
        "delta_available": delta.available,
    }
    if meta.get("tenant_name"):
        run_props["tenant_name"] = meta["tenant_name"]
    if extra_run_properties:
        run_props.update(extra_run_properties)

    invocation: dict[str, Any] = {
        "executionSuccessful": (meta.get("status") or "") != "failed",
    }
    for src, dst in (("started_at", "startTimeUtc"), ("finished_at", "endTimeUtc")):
        val = meta.get(src)
        if val:
            invocation[dst] = _utc_iso(str(val))

    return {
        "$schema": SARIF_SCHEMA,
        "version": SARIF_VERSION,
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "Data Boar",
                        "version": str(about.get("version") or "0"),
                        "informationUri": "https://github.com/DataBoar/data-boar",
                        "rules": rules,
                    }
                },
                "automationDetails": {"id": f"data-boar/{session_id}"},
                "invocations": [invocation],
                "results": results,
                "properties": run_props,
            }
        ],
    }


def _utc_iso(value: str) -> str:
    """Best-effort ISO-8601 UTC ``Z`` timestamp (SARIF wants a date-time)."""
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return value
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def build_sarif_payload(db_manager: Any, *, session_id: str) -> dict[str, Any]:
    """CLI entry: SARIF for a stored session, with ``baselineState`` when a
    previous comparable session exists.

    Raises :class:`core.findings_common.UnknownSessionError` for an unknown id.
    """
    sid = (session_id or "").strip()
    meta = session_meta(db_manager, sid)
    records, failures = collect_session_findings(db_manager, sid)
    delta = compute_session_delta(db_manager, sid)
    return build_sarif_document(
        records, session_id=sid, meta=meta, delta=delta, scan_failures=failures
    )
