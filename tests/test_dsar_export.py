"""DSAR export: core/dsar_export.py and CLI --export-dsar."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from core.database import LocalDBManager
from core.dsar_export import build_dsar_payload


def _seed_session(db_path: str) -> str:
    sid = "dsar-sess-01"
    mgr = LocalDBManager(db_path)
    try:
        mgr.create_session_record(sid)
        mgr.set_current_session_id(sid)
        mgr.save_finding(
            "database",
            target_name="prod-postgres",
            schema_name="public",
            table_name="users",
            column_name="email",
            sensitivity_level="HIGH",
            pattern_detected="EMAIL",
            norm_tag="LGPD Art. 5(I), GDPR Art. 4(1)",
        )
        mgr.save_finding(
            "filesystem",
            target_name="files-export",
            path="/data/exports",
            file_name="report_may.csv",
            sensitivity_level="HIGH",
            pattern_detected="LGPD_CPF",
            norm_tag="LGPD Art. 5(II)",
        )
        mgr.finish_session(sid)
    finally:
        mgr.dispose()
    return sid


def test_build_dsar_payload_groups_and_summary(tmp_path):
    db_path = str(tmp_path / "audit.db")
    sid = _seed_session(db_path)
    mgr = LocalDBManager(db_path)
    try:
        payload = build_dsar_payload(mgr, session_id=sid)
    finally:
        mgr.dispose()

    assert payload["schema_version"] == 1
    assert payload["session_id"] == sid
    assert payload["summary"]["total_findings"] == 2
    assert payload["summary"]["high_sensitivity"] == 2
    assert payload["summary"]["sources_scanned"] == 2
    assert "prod-postgres" in payload["findings_by_source"]
    assert payload["findings_by_source"]["prod-postgres"]["source_type"] == "database"
    assert (
        payload["findings_by_source"]["prod-postgres"]["findings"][0]["location"]
        == "public.users.email"
    )
    assert payload["export_options"]["include_samples"] is False
    assert (
        "sample_content"
        not in payload["findings_by_source"]["prod-postgres"]["findings"][0]
    )


def test_build_dsar_payload_unknown_session_empty(tmp_path):
    db_path = str(tmp_path / "audit.db")
    mgr = LocalDBManager(db_path)
    try:
        payload = build_dsar_payload(mgr, session_id="no-such-session")
    finally:
        mgr.dispose()

    assert payload["summary"]["total_findings"] == 0
    assert payload["findings_by_source"] == {}


def test_cli_export_dsar_stdout(tmp_path):
    db_path = str(tmp_path / "audit.db")
    sid = _seed_session(db_path)
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        f"sqlite_path: {db_path.replace(chr(92), '/')}\n"
        "targets: []\n"
        "report:\n  output_dir: reports\n",
        encoding="utf-8",
    )
    repo = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [
            sys.executable,
            str(repo / "main.py"),
            "--config",
            str(cfg),
            "--export-dsar",
            sid,
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["session_id"] == sid
    assert payload["summary"]["total_findings"] == 2


def test_cli_export_dsar_output_file(tmp_path):
    db_path = str(tmp_path / "audit.db")
    sid = _seed_session(db_path)
    cfg = tmp_path / "config.yaml"
    out = tmp_path / "dsar_out.json"
    cfg.write_text(
        f"sqlite_path: {db_path.replace(chr(92), '/')}\n"
        "targets: []\n"
        "report:\n  output_dir: reports\n",
        encoding="utf-8",
    )
    repo = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [
            sys.executable,
            str(repo / "main.py"),
            "--config",
            str(cfg),
            "--export-dsar",
            sid,
            "--dsar-output",
            str(out),
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert out.is_file()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["session_id"] == sid


def test_cli_export_dsar_incompatible_with_web(tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "sqlite_path: audit.db\ntargets: []\nreport:\n  output_dir: reports\n",
        encoding="utf-8",
    )
    repo = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [
            sys.executable,
            str(repo / "main.py"),
            "--config",
            str(cfg),
            "--export-dsar",
            "any",
            "--web",
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 2
    assert "Cannot combine" in proc.stderr
