"""
Remediation manifest JSON export (issue #649 / PLAN_REMEDIATION_INTERFACE phase export).

Machine-readable map of *where* PII was found and *which type*, for third-party
remediation plugins. Metadata only — never embeds raw PII samples or credentials.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.about import _package_version

REMEDIATION_MANIFEST_SCHEMA_VERSION = "1.0"
GENERATOR_NAME = "data-boar"

# Canonical pii_type → suggested_profile (plugin-facing tokens). Unknown types
# fall back to a stable TGGENERIC profile so the plugin always receives a hint.
_PII_TYPE_TO_PROFILE: dict[str, str] = {
    "cpf_br": "TGCPF",
    "cnpj_br": "TGCNPJ",
    "rg_br": "TGRG",
    "email": "TGEMAIL",
    "phone": "TGPHONE",
    "phone_br": "TGPHONE",
    "ssn_us": "TGSSN",
    "credit_card": "TGPAN",
    "pan": "TGPAN",
    "name": "TGNAME",
    "address": "TGADDRESS",
    "dob": "TGDOB",
    "ip_address": "TGIP",
    "identifier": "TGGENERIC",
}

# pattern_detected (engine labels) → pii_type slug used in the manifest.
_PATTERN_TO_PII_TYPE: dict[str, str] = {
    "LGPD_CPF": "cpf_br",
    "CPF": "cpf_br",
    "LGPD_CNPJ": "cnpj_br",
    "CNPJ": "cnpj_br",
    "LGPD_RG": "rg_br",
    "RG": "rg_br",
    "EMAIL": "email",
    "PHONE": "phone",
    "PHONE_BR": "phone_br",
    "CCPA_SSN": "ssn_us",
    "SSN": "ssn_us",
    "CREDIT_CARD": "credit_card",
    "PAN": "pan",
    "NAME": "name",
    "ADDRESS": "address",
    "DOB": "dob",
    "DOB_POSSIBLE_MINOR": "dob",
    "IP": "ip_address",
    "IP_ADDRESS": "ip_address",
}


def _slugify_pattern(pattern: str) -> str:
    raw = (pattern or "").strip()
    if not raw:
        return "identifier"
    return re.sub(r"[^a-z0-9]+", "_", raw.lower()).strip("_") or "identifier"


def pattern_to_pii_type(pattern_detected: str | None) -> str:
    """Map an engine pattern label to a stable pii_type slug."""
    key = (pattern_detected or "").strip().upper()
    if key in _PATTERN_TO_PII_TYPE:
        return _PATTERN_TO_PII_TYPE[key]
    return _slugify_pattern(pattern_detected or "")


def suggested_profile_for_pii_type(pii_type: str) -> str:
    """Return the canonical suggested_profile for a pii_type slug."""
    return _PII_TYPE_TO_PROFILE.get((pii_type or "").strip().lower(), "TGGENERIC")


def stable_finding_id(
    session_id: str,
    *,
    table: str | None,
    column: str | None,
    pii_type: str,
    path: str | None = None,
    file_name: str | None = None,
) -> str:
    """
    Stable id across re-scans of the same logical source.

    Hash of session_id + table + column + pii_type (and path/file for filesystem).
    """
    material = "|".join(
        [
            (session_id or "").strip(),
            (table or "").strip(),
            (column or "").strip(),
            (pii_type or "").strip(),
            (path or "").strip(),
            (file_name or "").strip(),
        ]
    )
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]
    return f"find_{digest}"


def _confidence_from_row(row: dict[str, Any]) -> float | None:
    """Normalize ml_confidence (0–100 int or 0–1 float) to a 0–1 float when present."""
    raw = row.get("ml_confidence")
    if raw is None:
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if value > 1.0:
        value = value / 100.0
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


def _target_type_map(config: dict[str, Any] | None) -> dict[str, str]:
    """Map config target name → connector type (e.g. postgresql)."""
    out: dict[str, str] = {}
    if not config:
        return out
    for t in config.get("targets") or []:
        if not isinstance(t, dict):
            continue
        name = t.get("name")
        ttype = t.get("type")
        if name and ttype:
            out[str(name)] = str(ttype).strip().lower()
    return out


def _source_type_for_row(
    row: dict[str, Any],
    *,
    kind: str,
    target_types: dict[str, str],
) -> str:
    if kind == "filesystem":
        return "filesystem"
    if kind in ("application", "api", "crm", "saas"):
        name = row.get("target_name") or ""
        if name in target_types:
            return target_types[name]
        return "application"
    name = row.get("target_name") or ""
    if name in target_types:
        return target_types[name]
    engine = (row.get("engine_details") or "").strip().lower()
    if engine:
        # engine_details is free-form; take first token as coarse type hint.
        return engine.split()[0]
    return "database"


def _db_target(
    row: dict[str, Any],
    *,
    session_id: str,
    target_types: dict[str, str],
) -> dict[str, Any]:
    pii_type = pattern_to_pii_type(row.get("pattern_detected"))
    table = row.get("table_name")
    column = row.get("column_name")
    confidence = _confidence_from_row(row)
    target: dict[str, Any] = {
        "finding_id": stable_finding_id(
            session_id, table=table, column=column, pii_type=pii_type
        ),
        "source_type": _source_type_for_row(
            row, kind="database", target_types=target_types
        ),
        "connection_ref": row.get("target_name") or "unknown",
        "schema": row.get("schema_name"),
        "table": table,
        "column": column,
        "pii_type": pii_type,
        "suggested_profile": suggested_profile_for_pii_type(pii_type),
        "occurrence_count_estimated": 1,
    }
    if confidence is not None:
        target["confidence"] = confidence
    return target


def _fs_target(
    row: dict[str, Any],
    *,
    session_id: str,
    target_types: dict[str, str],
    kind: str = "filesystem",
) -> dict[str, Any]:
    pii_type = pattern_to_pii_type(row.get("pattern_detected"))
    path = row.get("path")
    file_name = row.get("file_name")
    confidence = _confidence_from_row(row)
    target: dict[str, Any] = {
        "finding_id": stable_finding_id(
            session_id,
            table=None,
            column=None,
            pii_type=pii_type,
            path=path,
            file_name=file_name,
        ),
        "source_type": _source_type_for_row(row, kind=kind, target_types=target_types),
        "connection_ref": row.get("target_name") or "unknown",
        "schema": None,
        "table": None,
        "column": None,
        "pii_type": pii_type,
        "suggested_profile": suggested_profile_for_pii_type(pii_type),
        "occurrence_count_estimated": 1,
    }
    if confidence is not None:
        target["confidence"] = confidence
    return target


def build_remediation_manifest(
    db_manager: Any,
    *,
    session_id: str,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build a schema v1 remediation manifest for one scan session.

    Raises
    ------
    ValueError
        When ``session_id`` is empty or the session does not exist in SQLite.
    """
    sid = (session_id or "").strip()
    if not sid:
        raise ValueError("session_id is required for remediation manifest export")
    if not db_manager._session_exists(sid):
        raise ValueError(f"Unknown session: {sid}")

    db_rows, fs_rows, app_rows, _failures = db_manager.get_findings(sid)
    target_types = _target_type_map(config)

    remediation_targets: list[dict[str, Any]] = []
    for row in db_rows:
        remediation_targets.append(
            _db_target(row, session_id=sid, target_types=target_types)
        )
    for row in fs_rows:
        remediation_targets.append(
            _fs_target(row, session_id=sid, target_types=target_types)
        )
    for row in app_rows:
        remediation_targets.append(
            _fs_target(
                row, session_id=sid, target_types=target_types, kind="application"
            )
        )

    return {
        "schema_version": REMEDIATION_MANIFEST_SCHEMA_VERSION,
        "generator": GENERATOR_NAME,
        "data_boar_version": _package_version(),
        "session_id": sid,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "remediation_targets": remediation_targets,
    }


def write_findings_jsonl(
    db_manager: Any,
    *,
    session_id: str,
    path: Path | str,
    config: dict[str, Any] | None = None,
) -> Path | None:
    """
    Write metadata-only findings JSONL for the remediation plugin hook (#1443).

    Each line is one ``remediation_targets`` object from
    :func:`build_remediation_manifest` (same taxonomy as #649). Never embeds
    raw PII samples or credentials.

    Returns
    -------
    Path
        The written file path (may contain zero lines when the session has no
        findings).
    None
        Safe-Hold skip when ``session_id`` is empty/unknown (does not raise).
    """
    out = Path(path)
    try:
        payload = build_remediation_manifest(
            db_manager, session_id=session_id, config=config
        )
    except ValueError:
        return None

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        for target in payload["remediation_targets"]:
            fh.write(json.dumps(target, ensure_ascii=False) + "\n")
    return out
