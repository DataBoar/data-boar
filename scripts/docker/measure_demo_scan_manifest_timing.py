#!/usr/bin/env python3
"""Run synthetic demo scan and emit internal manifest timing (#1398).

No uvicorn — mirrors the ``--demo`` scan + report path only. Prints one JSON line
with ``scan_window.duration_minutes`` from ``scan_manifest_*.yaml`` (report
evidence), plus GIL/SQLAlchemy cext flags for variant comparison.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import sys

import yaml


def main() -> int:
    from core.demo.runtime import prepare_demo_workspace
    from core.engine import AuditEngine
    from core.validation import sanitize_tenant_technician

    import sqlalchemy

    gil_after_sqlalchemy = sys._is_gil_enabled()
    demo_dir, config_path, config = prepare_demo_workspace(register_cleanup=False)
    engine = AuditEngine(config, config_path=str(config_path))
    scan_buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(scan_buf):
            session_id = engine.start_audit(
                tenant_name=sanitize_tenant_technician("demo"),
                technician_name=sanitize_tenant_technician("operator"),
                jurisdiction_hint=False,
            )
            report_path = engine.generate_final_reports(session_id)
        reports = demo_dir / "reports"
        manifests = sorted(reports.glob("scan_manifest_*.yaml"))
        if not manifests:
            print(
                json.dumps(
                    {
                        "error": "scan_manifest_missing",
                        "session_id": session_id,
                        "report_path": report_path,
                    }
                )
            )
            return 1
        manifest = yaml.safe_load(manifests[-1].read_text(encoding="utf-8")) or {}
        window = manifest.get("scan_window") or {}
        findings = (manifest.get("scope_snapshot") or {}).get("findings_counts") or {}
        payload = {
            "variant": os.environ.get("DATA_BOAR_IMAGE_VARIANT", "unknown"),
            "session_id": session_id,
            "report_path": report_path,
            "manifest_path": str(manifests[-1]),
            "duration_minutes": window.get("duration_minutes"),
            "started_at": window.get("started_at"),
            "finished_at": window.get("finished_at"),
            "findings_total": sum(int(v or 0) for v in findings.values()),
            "gil_after_sqlalchemy": gil_after_sqlalchemy,
            "gil_after_scan": sys._is_gil_enabled(),
            "disable_sqlalchemy_cext": os.environ.get("DISABLE_SQLALCHEMY_CEXT"),
            "sqlalchemy_version": sqlalchemy.__version__,
        }
        print(json.dumps(payload, sort_keys=True))
        return 0
    finally:
        engine.db_manager.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
