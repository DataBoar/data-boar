"""Tests for JSON audit trail export (CLI --export-audit-trail)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from core.audit_export import AUDIT_TRAIL_SCHEMA_VERSION, build_audit_trail_payload
from core.database import LocalDBManager


def _expected_empty_maturity_integrity() -> dict:
    return {
        "secret_configured": False,
        "rows_checked": 0,
        "rows_ok": 0,
        "rows_mismatch": 0,
        "rows_unsealed": 0,
        "rows_unknown_sealed": 0,
    }


def test_build_audit_trail_payload_structure(tmp_path, monkeypatch):
    # Make the assertion deterministic regardless of other tests / environment.
    monkeypatch.delenv("DATA_BOAR_DASHBOARD_TRANSPORT", raising=False)
    monkeypatch.delenv("DATA_BOAR_DASHBOARD_INSECURE_OPT_IN", raising=False)
    db_path = str(tmp_path / "a.db")
    mgr = LocalDBManager(db_path)
    try:
        mgr.wipe_all_data("first wipe for test")
        payload = build_audit_trail_payload(
            mgr,
            config={},
            config_path=str(tmp_path / "config.yaml"),
            sqlite_path=db_path,
        )
    finally:
        mgr.dispose()

    assert payload["schema_version"] == AUDIT_TRAIL_SCHEMA_VERSION
    assert "exported_at" in payload
    assert payload["application"]["name"] == "Data Boar"
    assert payload["paths"]["config"].endswith("config.yaml")
    assert payload["paths"]["sqlite"] == db_path
    assert payload["runtime_trust"]["trust_level"] == "expected"
    assert payload["runtime_trust"]["trust_state"] == "trusted"
    assert payload["trust_state"] == "trusted"
    assert payload["trust_reasons"] == []
    assert payload["output_confidence"] == "full"
    assert payload["dashboard_transport"]["mode"] == "not_configured"
    assert "enterprise_surface" in payload
    assert payload["enterprise_surface"]["access_surface"]["mode"] == "open_html"
    assert len(payload["data_wipe_log"]) == 1
    assert "first wipe for test" in payload["data_wipe_log"][0]["reason"]
    assert payload["scan_sessions_summary"]["count"] == 0
    assert payload["integrity_anchor"] is None
    assert (
        payload["maturity_assessment_integrity"] == _expected_empty_maturity_integrity()
    )
    assert "data_wipe_log" in payload["notes"].lower()
    assert "maturity_assessment_integrity" in payload["notes"].lower()


def test_build_audit_trail_maturity_integrity_matches_verify(tmp_path, monkeypatch):
    """Export must include the same maturity HMAC summary as LocalDBManager.verify_maturity_assessment_integrity."""
    monkeypatch.delenv("DATA_BOAR_MATURITY_INTEGRITY_SECRET", raising=False)
    monkeypatch.setenv("DATA_BOAR_MATURITY_INTEGRITY_SECRET", "export-parity-secret")
    db_path = str(tmp_path / "m.db")
    mgr = LocalDBManager(db_path)
    try:
        mgr.save_maturity_assessment_answers(
            batch_id="b1",
            locale_slug="en",
            pack_version=1,
            answers={"q1": "a"},
            integrity_secret=b"export-parity-secret",
        )
        cfg = {"api": {}}
        payload = build_audit_trail_payload(
            mgr,
            config=cfg,
            config_path=str(tmp_path / "cfg.yaml"),
            sqlite_path=db_path,
        )
        direct = mgr.verify_maturity_assessment_integrity(b"export-parity-secret")
        assert payload["maturity_assessment_integrity"] == direct
        assert direct["rows_ok"] == 1
        assert direct["secret_configured"] is True
    finally:
        mgr.dispose()


def test_export_audit_trail_cli_stdout(tmp_path):
    cfg = tmp_path / "config.yaml"
    db = tmp_path / "audit.db"
    cfg.write_text(
        f"""targets: []
report:
  output_dir: {tmp_path}
sqlite_path: {db}
scan:
  max_workers: 1
""",
        encoding="utf-8",
    )
    repo = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    env.pop("DATA_BOAR_DASHBOARD_TRANSPORT", None)
    env.pop("DATA_BOAR_DASHBOARD_INSECURE_OPT_IN", None)
    r = subprocess.run(
        [
            sys.executable,
            str(repo / "main.py"),
            "--config",
            str(cfg),
            "--export-audit-trail",
            "-",
        ],
        capture_output=True,
        text=True,
        cwd=str(repo),
        check=False,
        env=env,
    )
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data["schema_version"] == AUDIT_TRAIL_SCHEMA_VERSION
    assert data["runtime_trust"]["license_state"] == "OPEN"
    assert data["runtime_trust"]["trust_state"] == "trusted"
    assert data["trust_state"] == "trusted"
    assert data["output_confidence"] == "full"
    assert "enterprise_surface" in data
    assert data["scan_sessions_summary"]["count"] == 0
    assert data["dashboard_transport"]["mode"] == "not_configured"
    assert "[INFO] runtime-trust:" in r.stderr


def test_export_audit_trail_rejects_web(tmp_path):
    cfg = tmp_path / "c.yaml"
    db = tmp_path / "x.db"
    cfg.write_text(
        f"""targets: []
report:
  output_dir: {tmp_path}
sqlite_path: {db}
api:
  port: 8099
scan:
  max_workers: 1
""",
        encoding="utf-8",
    )
    repo = Path(__file__).resolve().parents[1]
    r = subprocess.run(
        [
            sys.executable,
            str(repo / "main.py"),
            "--config",
            str(cfg),
            "--web",
            "--export-audit-trail",
            "-",
        ],
        capture_output=True,
        text=True,
        cwd=str(repo),
        check=False,
    )
    assert r.returncode == 2
    assert "Cannot combine" in r.stderr


def test_cli_emits_runtime_trust_info_to_stdout_and_stderr(tmp_path):
    cfg = tmp_path / "run.yaml"
    db = tmp_path / "run.db"
    cfg.write_text(
        f"""targets: []
report:
  output_dir: {tmp_path}
sqlite_path: {db}
scan:
  max_workers: 1
""",
        encoding="utf-8",
    )
    repo = Path(__file__).resolve().parents[1]
    r = subprocess.run(
        [
            sys.executable,
            str(repo / "main.py"),
            "--config",
            str(cfg),
        ],
        capture_output=True,
        text=True,
        cwd=str(repo),
        check=False,
    )
    assert r.returncode == 0, r.stderr
    assert "[INFO] runtime-trust:" in r.stdout
    assert "[INFO] runtime-trust:" in r.stderr
