"""
PoC slice: manifest YAML (evidência) + ``POC_SUMMARY.md`` (vista executiva) + APG via
:class:`~report.recommendation_engine.RecommendationEngine`.

**Artigo I** — :class:`~report.evidence_collector.EvidenceCollector` alimenta ``audit_trail``.
**Artigo II** — recomendações fixas (sem ML).
**Artigo III** — resumo para e-mail/Slack.
"""

from __future__ import annotations

import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from connectors.sql_sampling import (
    resolve_sql_sample_limit,
    resolve_statement_timeout_ms_for_sampling,
)
from core.sampling import SamplingProvider
from report.evidence_collector import EvidenceCollector
from report.executive_report import generate_executive_report
from report.recommendation_engine import RecommendationEngine, apg_row_for_pattern
from report.safe_prefix import safe_session_prefix

# Env keys (documented in USAGE.md).
_ENV_SQL_SAMPLE_LIMIT = "DATA_BOAR_SQL_SAMPLE_LIMIT"
_ENV_SAMPLE_STMT_TIMEOUT_MS = "DATA_BOAR_SAMPLE_STATEMENT_TIMEOUT_MS"
_ENV_PG_TABLESAMPLE_SYSTEM_PERCENT = "DATA_BOAR_PG_TABLESAMPLE_SYSTEM_PERCENT"

EVIDENCE_SCHEMA_VERSION = "1"

_SHADOW_NAME_MARKERS = (
    "copy_of",
    "backup_",
    "_backup",
    "test_",
    "_test",
    "tmp_",
    "_tmp",
    "shadow",
    "sandbox",
    "staging_copy",
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _parse_iso(dt: str | None) -> datetime | None:
    if not dt:
        return None
    try:
        return datetime.fromisoformat(dt.replace("Z", "+00:00"))
    except ValueError:
        return None


def _duration_minutes(started: str | None, finished: str | None) -> float | None:
    a = _parse_iso(started)
    b = _parse_iso(finished)
    if not a or not b:
        return None
    sec = (b - a).total_seconds()
    if sec < 0:
        return None
    return round(sec / 60.0, 2)


def _shadow_hit(row: dict) -> bool:
    parts = [
        (row.get("table_name") or "").lower(),
        (row.get("column_name") or "").lower(),
        (row.get("schema_name") or "").lower(),
    ]
    blob = " ".join(parts)
    return any(m in blob for m in _SHADOW_NAME_MARKERS)


def _sampling_policy_block(config: dict[str, Any]) -> dict[str, Any]:
    pol = SamplingProvider.from_config(config)
    targets_out: dict[str, Any] = {}
    for name, tcfg in pol.targets.items():
        if not isinstance(tcfg, dict):
            continue
        slim: dict[str, Any] = {}
        if "sample_limit" in tcfg:
            slim["sample_limit"] = tcfg.get("sample_limit")
        tables = tcfg.get("tables")
        if isinstance(tables, dict) and tables:
            slim["tables_override_count"] = len(tables)
        if slim:
            targets_out[str(name)] = slim
    return {
        "hierarchical_caps": {
            "targets": targets_out,
            "pattern_rules_count": len(pol.patterns),
            "pattern_globs": sorted(pol.patterns.keys()),
        },
        "note": (
            "Effective per-column cap = policy resolution then "
            f"{_ENV_SQL_SAMPLE_LIMIT} env override inside resolve_sql_sample_limit()."
        ),
    }


def _file_scan_block(config: dict[str, Any]) -> dict[str, Any]:
    fs = config.get("file_scan") if isinstance(config.get("file_scan"), dict) else {}
    exts = fs.get("extensions")
    if not isinstance(exts, list):
        exts = []
    return {
        "sample_limit": fs.get("sample_limit"),
        "extensions_count": len(exts),
        "extensions_sample": [str(x) for x in exts[:25]],
    }


def _targets_scope(config: dict[str, Any]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for t in config.get("targets", []) or []:
        if not isinstance(t, dict):
            continue
        name = (t.get("name") or "").strip() or "(unnamed)"
        typ = (t.get("type") or "").strip() or "unknown"
        out.append({"name": name, "type": typ})
    return out


def _statement_timeout_manifest(config: dict[str, Any]) -> dict[str, Any]:
    targets = config.get("targets", []) or []
    first_explicit: int | None = None
    if isinstance(targets, list):
        for t in targets:
            if (
                not isinstance(t, dict)
                or (t.get("type") or "").strip().lower() != "database"
            ):
                continue
            for key in (
                "sample_statement_timeout_ms",
                "sample_statement_timeout_seconds",
            ):
                if key not in t:
                    continue
                v = t.get(key)
                if key.endswith("seconds"):
                    try:
                        first_explicit = int(float(v) * 1000)
                    except (TypeError, ValueError):
                        continue
                else:
                    try:
                        first_explicit = int(v)
                    except (TypeError, ValueError):
                        continue
                break
            if first_explicit is not None:
                break
    resolved = resolve_statement_timeout_ms_for_sampling(first_explicit)
    env_set = bool((os.environ.get(_ENV_SAMPLE_STMT_TIMEOUT_MS) or "").strip())
    return {
        "first_database_target_explicit_ms": first_explicit,
        "resolved_sql_hint_ms": resolved,
        "env_DATA_BOAR_SAMPLE_STATEMENT_TIMEOUT_MS_set": env_set,
        "disclaimer": (
            "PostgreSQL may still apply SET LOCAL statement_timeout in the connector even when "
            "SQL-hint ms is None; see USAGE.md database sampling section."
        ),
    }


def _build_poc_summary_markdown(
    *,
    session_id: str,
    about: dict[str, str],
    manifest: dict[str, Any],
    db_rows: list[dict],
    fs_rows: list[dict],
    fail_rows: list[dict],
    apg_rows: list[dict[str, Any]],
    report_rows_capped: bool,
) -> str:
    return generate_executive_report(
        session_id=session_id,
        about=about,
        manifest=manifest,
        db_rows=db_rows,
        fs_rows=fs_rows,
        _fail_rows=fail_rows,
        apg_rows=apg_rows,
        report_rows_capped=report_rows_capped,
    )


def _aggregate_apg(
    db_rows: list[dict], fs_rows: list[dict] | None = None
) -> list[dict[str, Any]]:
    by_pattern: Counter[str] = Counter()
    shadow_by_pattern: Counter[str] = Counter()
    for r in db_rows:
        pat = (r.get("pattern_detected") or "").strip() or "(empty)"
        by_pattern[pat] += 1
        if _shadow_hit(r):
            shadow_by_pattern[pat] += 1
    for r in fs_rows or []:
        pat = (r.get("pattern_detected") or "").strip() or "(empty)"
        by_pattern[pat] += 1
        if _shadow_hit(r):
            shadow_by_pattern[pat] += 1
    rows: list[dict[str, Any]] = []
    for pat, n in sorted(by_pattern.items(), key=lambda x: (-x[1], x[0])):
        base = RecommendationEngine.row_for_pattern(pat, shadow_context=False)
        rows.append(
            {
                "pattern_detected": pat,
                "finding_count": n,
                "shadow_name_heuristic_count": shadow_by_pattern.get(pat, 0),
                **base,
            }
        )
    return rows


def _build_manifest(
    *,
    session_id: str,
    meta: dict[str, Any],
    about: dict[str, str],
    config: dict[str, Any],
    db_rows: list[dict],
    fs_rows: list[dict],
    fail_rows: list[dict],
    report_rows_capped: bool,
) -> dict[str, Any]:
    file_scan = (
        config.get("file_scan") if isinstance(config.get("file_scan"), dict) else {}
    )
    global_lim = int(file_scan.get("sample_limit") or 1000)
    effective_limit = resolve_sql_sample_limit(global_lim)
    stmt_payload = _statement_timeout_manifest(config)
    collector = EvidenceCollector(
        config=config,
        db_rows=db_rows,
        effective_sample_row_cap=effective_limit,
        statement_timeout_payload=stmt_payload,
    )

    started = meta.get("started_at")
    finished = meta.get("finished_at")
    if isinstance(started, datetime):
        started = started.isoformat()
    if isinstance(finished, datetime):
        finished = finished.isoformat()

    # #1412 — rust-regex-stage / detection_prefilter observability (does not change findings).
    runtime = config.get("_runtime") if isinstance(config.get("_runtime"), dict) else {}
    pf_raw = (
        runtime.get("prefilter") if isinstance(runtime.get("prefilter"), dict) else {}
    )
    detection_prefilter = {
        "active": bool(pf_raw.get("active")),
        "name": pf_raw.get("name"),
        "backend": pf_raw.get("backend"),  # rust | python | null
        "tier": pf_raw.get("tier"),
        "reason": pf_raw.get("reason"),
        "engine": pf_raw.get("engine"),  # pro | core
    }

    return {
        "evidence_schema_version": EVIDENCE_SCHEMA_VERSION,
        "kind": "data_boar_scan_manifest",
        "engine_signature": {
            "product": about.get("name", "Data Boar"),
            "version": about.get("version", ""),
            "manifest_generated_at_utc": _utc_now_iso(),
            "session_id": session_id,
            "config_scope_hash": meta.get("config_scope_hash"),
        },
        "scan_window": {
            "started_at": started,
            "finished_at": finished,
            "duration_minutes": _duration_minutes(
                str(started) if started else None,
                str(finished) if finished else None,
            ),
        },
        "detection_prefilter": detection_prefilter,
        "audit_trail": collector.to_manifest_dict(),
        "safety_tags": {
            "sampling_row_cap_resolved": effective_limit,
            "sampling_policy": _sampling_policy_block(config),
            "statement_timeout": stmt_payload,
            "leading_sql_comment": "-- Data Boar Compliance Scan",
            "env_flags_present": {
                _ENV_SQL_SAMPLE_LIMIT: bool(
                    (os.environ.get(_ENV_SQL_SAMPLE_LIMIT) or "").strip()
                ),
                _ENV_SAMPLE_STMT_TIMEOUT_MS: bool(
                    (os.environ.get(_ENV_SAMPLE_STMT_TIMEOUT_MS) or "").strip()
                ),
                _ENV_PG_TABLESAMPLE_SYSTEM_PERCENT: bool(
                    (os.environ.get(_ENV_PG_TABLESAMPLE_SYSTEM_PERCENT) or "").strip()
                ),
            },
        },
        "scope_snapshot": {
            "targets": _targets_scope(config),
            "file_scan": _file_scan_block(config),
            "findings_counts": {
                "database_findings": len(db_rows),
                "filesystem_findings": len(fs_rows),
                "scan_failures": len(fail_rows),
            },
            "unique_database_tables_with_findings": len(
                {
                    (
                        (r.get("target_name") or ""),
                        (r.get("schema_name") or ""),
                        (r.get("table_name") or ""),
                    )
                    for r in db_rows
                    if (r.get("table_name") or "").strip()
                }
            ),
        },
        "report_disclosure": {
            "excel_rows_may_be_capped_under_trial_license": bool(report_rows_capped),
            "manifest_counts_reflect_full_session_store": True,
        },
        "disclaimer": (
            "This manifest describes product defaults and configured knobs; it is not a legal "
            "certificate or a guarantee of zero production impact. Confirm with your DBA/SRE."
        ),
    }


def write_scan_evidence_artifacts(
    *,
    output_dir: str,
    session_id: str,
    meta: dict[str, Any],
    about: dict[str, str],
    config: dict[str, Any] | None,
    db_rows: list[dict],
    fs_rows: list[dict],
    fail_rows: list[dict],
    report_rows_capped: bool = False,
) -> tuple[str, str]:
    """
    Write ``scan_manifest_<session_prefix>.yaml`` and ``POC_SUMMARY_<prefix>.md``.

    Returns ``(manifest_path, poc_summary_md_path)``.
    """
    cfg = config if isinstance(config, dict) else {}
    prefix = safe_session_prefix(session_id, max_len=16)
    out = Path(output_dir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)

    manifest = _build_manifest(
        session_id=session_id,
        meta=meta,
        about=about,
        config=cfg,
        db_rows=db_rows,
        fs_rows=fs_rows,
        fail_rows=fail_rows,
        report_rows_capped=report_rows_capped,
    )
    apg_rows = _aggregate_apg(db_rows, fs_rows)
    manifest["apg_phase_a"] = apg_rows

    man_path = (out / f"scan_manifest_{prefix}.yaml").resolve()
    poc_path = (out / f"POC_SUMMARY_{prefix}.md").resolve()
    try:
        man_path.relative_to(out)
        poc_path.relative_to(out)
    except ValueError as exc:
        raise ValueError(
            "output_dir resolves outside allowed base after artifact join"
        ) from exc

    man_path.write_text(
        yaml.safe_dump(
            manifest,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
        ),
        encoding="utf-8",
    )
    poc_path.write_text(
        _build_poc_summary_markdown(
            session_id=session_id,
            about=about,
            manifest=manifest,
            db_rows=db_rows,
            fs_rows=fs_rows,
            fail_rows=fail_rows,
            apg_rows=apg_rows,
            report_rows_capped=report_rows_capped,
        ),
        encoding="utf-8",
    )
    return str(man_path), str(poc_path)


__all__ = [
    "EVIDENCE_SCHEMA_VERSION",
    "apg_row_for_pattern",
    "write_scan_evidence_artifacts",
]
