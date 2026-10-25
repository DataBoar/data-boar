"""
Session report export — regenerate artifacts from SQLite without re-scan (#1326).

Dispatches ``data-boar-report --format`` to Markdown, Office/PDF, Excel, heatmap,
DSAR JSON, scan manifest JSON, and audit-trail JSON.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from config.loader import load_config
from core.about import get_about_info
from core.audit_export import build_audit_trail_payload
from core.database import LocalDBManager
from core.dsar_export import build_dsar_payload
from core.learned_patterns import write_learned_patterns
from core.output_paths import ensure_config_output_directories
from report.executive_docx import write_executive_docx
from report.executive_pdf import write_executive_pdf
from report.executive_report import generate_executive_report
from report.generator import generate_report, generate_session_heatmap
from report.safe_prefix import safe_session_prefix
from report.scan_evidence import _aggregate_apg, _build_manifest

ExportFormat = Literal[
    "md",
    "docx",
    "pdf",
    "xlsx",
    "heatmap",
    "dsar",
    "json",
    "audit-trail",
    "all",
]

SINGLE_FORMATS: tuple[str, ...] = (
    "md",
    "docx",
    "pdf",
    "xlsx",
    "heatmap",
    "dsar",
    "json",
    "audit-trail",
)

ALL_FORMATS: tuple[str, ...] = SINGLE_FORMATS


def resolve_output_dir(
    config: dict[str, Any],
    override: str | None,
    *,
    config_path: Path | None = None,
) -> Path:
    if override and override.strip():
        return Path(override).expanduser().resolve()
    raw = (config.get("report") or {}).get("output_dir")
    if raw and str(raw).strip() not in {"", "."}:
        return Path(str(raw)).expanduser().resolve()
    if config_path is not None:
        return config_path.parent.resolve()
    return Path(".").expanduser().resolve()


def _session_meta(db_manager: LocalDBManager, session_id: str) -> dict[str, Any]:
    for s in db_manager.list_sessions() or []:
        if s.get("session_id") == session_id:
            return {
                "started_at": s.get("started_at"),
                "finished_at": s.get("finished_at"),
                "tenant_name": s.get("tenant_name"),
                "technician_name": s.get("technician_name"),
                "config_scope_hash": s.get("config_scope_hash"),
                "jurisdiction_hint": bool(s.get("jurisdiction_hint")),
            }
    return {
        "started_at": None,
        "finished_at": None,
        "tenant_name": None,
        "technician_name": None,
        "config_scope_hash": None,
        "jurisdiction_hint": False,
    }


def _executive_markdown(
    *,
    session_id: str,
    about: dict[str, str],
    manifest: dict[str, Any],
    db_rows: list[dict],
    fs_rows: list[dict],
    fail_rows: list[dict],
    report_rows_capped: bool,
    app_rows: list[dict] | None = None,
) -> str:
    app = list(app_rows or [])
    apg_rows = _aggregate_apg(db_rows, list(fs_rows) + app)
    return generate_executive_report(
        session_id=session_id,
        about=about,
        manifest=manifest,
        db_rows=db_rows,
        fs_rows=fs_rows,
        _fail_rows=fail_rows,
        apg_rows=apg_rows,
        report_rows_capped=report_rows_capped,
        app_rows=app,
    )


def _build_manifest_dict(
    *,
    session_id: str,
    meta: dict[str, Any],
    about: dict[str, str],
    config: dict[str, Any],
    db_rows: list[dict],
    fs_rows: list[dict],
    fail_rows: list[dict],
    report_rows_capped: bool,
    app_rows: list[dict] | None = None,
) -> dict[str, Any]:
    app = list(app_rows or [])
    manifest = _build_manifest(
        session_id=session_id,
        meta=meta,
        about=about,
        config=config,
        db_rows=db_rows,
        fs_rows=fs_rows,
        fail_rows=fail_rows,
        report_rows_capped=report_rows_capped,
        app_rows=app,
    )
    manifest["apg_phase_a"] = _aggregate_apg(db_rows, list(fs_rows) + app)
    return manifest


def export_session_formats(
    *,
    config_path: Path,
    session_id: str,
    formats: list[str],
    sqlite_path: str | None = None,
    output_dir: Path | None = None,
    output_file: Path | None = None,
    trial_rows_capped: bool = False,
    dsar_include_samples: bool = False,
) -> dict[str, Path]:
    """
    Export one or more report formats for ``session_id``. Returns map format -> path.

    Raises ``ValueError`` for unknown session or invalid paths.
    """
    cfg = load_config(config_path)
    ensure_config_output_directories(cfg)
    db_path = (sqlite_path or "").strip() or str(
        cfg.get("sqlite_path") or "audit_results.db"
    )
    sid = session_id.strip()
    out_dir = output_dir or resolve_output_dir(cfg, None, config_path=config_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = safe_session_prefix(sid, max_len=8)
    prefix_long = safe_session_prefix(sid, max_len=16)

    mgr = LocalDBManager(db_path)
    try:
        known = {row["session_id"] for row in mgr.list_sessions()}
        if sid not in known:
            raise ValueError(f"Unknown session: {sid}")

        db_rows, fs_rows, app_rows, fail_rows = mgr.get_findings(sid)
        meta = _session_meta(mgr, sid)
        about = get_about_info()
        manifest = _build_manifest_dict(
            session_id=sid,
            meta=meta,
            about=about,
            config=cfg,
            db_rows=db_rows,
            fs_rows=fs_rows,
            fail_rows=fail_rows,
            report_rows_capped=trial_rows_capped,
            app_rows=app_rows,
        )
        written: dict[str, Path] = {}

        for fmt in formats:
            if fmt == "md":
                dest = output_file or (out_dir / f"executive_report_{prefix}.md")
                dest = dest.expanduser().resolve()
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(
                    _executive_markdown(
                        session_id=sid,
                        about=about,
                        manifest=manifest,
                        db_rows=db_rows,
                        fs_rows=fs_rows,
                        fail_rows=fail_rows,
                        report_rows_capped=trial_rows_capped,
                    ),
                    encoding="utf-8",
                )
                written["md"] = dest
            elif fmt == "docx":
                dest = output_file or (out_dir / f"executive_report_{prefix}.docx")
                dest = dest.expanduser().resolve()
                dest.parent.mkdir(parents=True, exist_ok=True)
                md = _executive_markdown(
                    session_id=sid,
                    about=about,
                    manifest=manifest,
                    db_rows=db_rows,
                    fs_rows=fs_rows,
                    fail_rows=fail_rows,
                    report_rows_capped=trial_rows_capped,
                    app_rows=app_rows,
                )
                write_executive_docx(md, dest)
                written["docx"] = dest
            elif fmt == "pdf":
                dest = output_file or (out_dir / f"executive_report_{prefix}.pdf")
                dest = dest.expanduser().resolve()
                dest.parent.mkdir(parents=True, exist_ok=True)
                md = _executive_markdown(
                    session_id=sid,
                    about=about,
                    manifest=manifest,
                    db_rows=db_rows,
                    fs_rows=fs_rows,
                    fail_rows=fail_rows,
                    report_rows_capped=trial_rows_capped,
                    app_rows=app_rows,
                )
                write_executive_pdf(md, dest)
                written["pdf"] = dest
            elif fmt == "xlsx":
                path = generate_report(mgr, sid, output_dir=str(out_dir), config=cfg)
                if not path:
                    raise ValueError("No findings to report for xlsx export")
                written["xlsx"] = Path(path).resolve()
                learned = write_learned_patterns(mgr, sid, cfg)
                if learned:
                    written["learned_patterns"] = Path(learned).resolve()
            elif fmt == "heatmap":
                path = generate_session_heatmap(
                    mgr, sid, output_dir=str(out_dir), config=cfg
                )
                if not path:
                    raise ValueError("No findings to render heatmap")
                written["heatmap"] = Path(path).resolve()
            elif fmt == "dsar":
                dest = output_file or (out_dir / f"dsar_export_{prefix_long}.json")
                dest = dest.expanduser().resolve()
                dest.parent.mkdir(parents=True, exist_ok=True)
                payload = build_dsar_payload(
                    mgr, session_id=sid, include_samples=dsar_include_samples
                )
                dest.write_text(
                    json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )
                written["dsar"] = dest
            elif fmt == "json":
                dest = output_file or (out_dir / f"scan_manifest_{prefix_long}.json")
                dest = dest.expanduser().resolve()
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(
                    json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )
                written["json"] = dest
            elif fmt == "audit-trail":
                dest = output_file or (out_dir / f"audit_trail_{prefix_long}.json")
                dest = dest.expanduser().resolve()
                dest.parent.mkdir(parents=True, exist_ok=True)
                payload = build_audit_trail_payload(
                    mgr,
                    config=cfg,
                    config_path=str(config_path),
                    sqlite_path=db_path,
                )
                dest.write_text(
                    json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )
                written["audit-trail"] = dest
            else:
                raise ValueError(f"Unsupported export format: {fmt}")
        return written
    finally:
        mgr.dispose()
