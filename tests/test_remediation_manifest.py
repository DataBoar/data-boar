"""Remediation manifest export: core/remediation_manifest.py and CLI (#649)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from core.about import _package_version
from core.database import LocalDBManager
from core.remediation_manifest import (
    build_remediation_manifest,
    pattern_to_pii_type,
    stable_finding_id,
    suggested_profile_for_pii_type,
)


def _seed_session(db_path: str) -> str:
    sid = "remed-sess-01"
    mgr = LocalDBManager(db_path)
    try:
        mgr.create_session_record(sid)
        mgr.set_current_session_id(sid)
        mgr.save_finding(
            "database",
            target_name="primary_db",
            schema_name="public",
            table_name="customers",
            column_name="cpf",
            sensitivity_level="HIGH",
            pattern_detected="LGPD_CPF",
            norm_tag="LGPD Art. 5(II)",
            ml_confidence=97,
        )
        mgr.save_finding(
            "database",
            target_name="primary_db",
            schema_name="public",
            table_name="customers",
            column_name="email",
            sensitivity_level="HIGH",
            pattern_detected="EMAIL",
            norm_tag="LGPD Art. 5(I)",
        )
        mgr.save_finding(
            "filesystem",
            target_name="files-export",
            path="/data/exports",
            file_name="report_may.csv",
            sensitivity_level="MEDIUM",
            pattern_detected="PHONE",
            norm_tag="LGPD Art. 5(II)",
        )
        mgr.finish_session(sid)
    finally:
        mgr.dispose()
    return sid


def test_pattern_to_pii_type_and_profile_mapping():
    assert pattern_to_pii_type("LGPD_CPF") == "cpf_br"
    assert suggested_profile_for_pii_type("cpf_br") == "TGCPF"
    assert suggested_profile_for_pii_type("unknown_xyz") == "TGGENERIC"


def test_stable_finding_id_is_deterministic():
    a = stable_finding_id("s1", table="customers", column="cpf", pii_type="cpf_br")
    b = stable_finding_id("s1", table="customers", column="cpf", pii_type="cpf_br")
    c = stable_finding_id("s1", table="customers", column="email", pii_type="email")
    assert a == b
    assert a != c
    assert a.startswith("find_")


def test_build_remediation_manifest_with_findings(tmp_path):
    db_path = str(tmp_path / "audit.db")
    sid = _seed_session(db_path)
    cfg = {
        "targets": [
            {"name": "primary_db", "type": "postgresql"},
            {"name": "files-export", "type": "filesystem"},
        ]
    }
    mgr = LocalDBManager(db_path)
    try:
        payload = build_remediation_manifest(mgr, session_id=sid, config=cfg)
    finally:
        mgr.dispose()

    assert payload["schema_version"] == "1.0"
    assert payload["generator"] == "data-boar"
    assert payload["data_boar_version"] == _package_version()
    assert payload["session_id"] == sid
    assert "exported_at" in payload
    targets = payload["remediation_targets"]
    assert len(targets) == 3

    cpf = next(t for t in targets if t["column"] == "cpf")
    assert cpf["source_type"] == "postgresql"
    assert cpf["connection_ref"] == "primary_db"
    assert cpf["schema"] == "public"
    assert cpf["table"] == "customers"
    assert cpf["pii_type"] == "cpf_br"
    assert cpf["suggested_profile"] == "TGCPF"
    assert cpf["confidence"] == 0.97
    assert cpf["occurrence_count_estimated"] == 1
    assert "sample_content" not in cpf
    assert "sample_value" not in cpf

    # No credential-shaped keys
    blob = json.dumps(payload)
    for forbidden in ("password", "secret", "api_key"):
        assert forbidden not in blob.lower()


def test_build_remediation_manifest_empty_findings(tmp_path):
    db_path = str(tmp_path / "audit.db")
    sid = "empty-sess"
    mgr = LocalDBManager(db_path)
    try:
        mgr.create_session_record(sid)
        mgr.finish_session(sid)
        payload = build_remediation_manifest(mgr, session_id=sid)
    finally:
        mgr.dispose()

    assert payload["remediation_targets"] == []
    assert payload["session_id"] == sid


def test_build_remediation_manifest_unknown_session(tmp_path):
    db_path = str(tmp_path / "audit.db")
    mgr = LocalDBManager(db_path)
    try:
        try:
            build_remediation_manifest(mgr, session_id="no-such-session")
            raise AssertionError("expected ValueError")
        except ValueError as e:
            assert "Unknown session" in str(e)
    finally:
        mgr.dispose()


def test_cli_export_remediation_manifest_file(tmp_path):
    db_path = str(tmp_path / "audit.db")
    sid = _seed_session(db_path)
    cfg = tmp_path / "config.yaml"
    out = tmp_path / "remediation.json"
    cfg.write_text(
        f"sqlite_path: {db_path.replace(chr(92), '/')}\n"
        "targets:\n"
        "  - name: primary_db\n"
        "    type: postgresql\n"
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
            "--session",
            sid,
            "--export-remediation-manifest",
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
    assert len(payload["remediation_targets"]) == 3
    assert payload["data_boar_version"] == _package_version()


def test_cli_export_remediation_manifest_requires_session(tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        f"sqlite_path: {(tmp_path / 'a.db').as_posix()}\ntargets: []\n",
        encoding="utf-8",
    )
    repo = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [
            sys.executable,
            str(repo / "main.py"),
            "--config",
            str(cfg),
            "--export-remediation-manifest",
            str(tmp_path / "out.json"),
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 2
    assert "--session" in proc.stderr


def test_cli_export_remediation_manifest_invalid_path(tmp_path):
    db_path = str(tmp_path / "audit.db")
    sid = _seed_session(db_path)
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        f"sqlite_path: {db_path.replace(chr(92), '/')}\ntargets: []\n",
        encoding="utf-8",
    )
    # Directory path (not a file) → write fails
    bad = tmp_path / "not_a_file_dir"
    bad.mkdir()
    repo = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [
            sys.executable,
            str(repo / "main.py"),
            "--config",
            str(cfg),
            "--session",
            sid,
            "--export-remediation-manifest",
            str(bad),
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 1
    assert "cannot write" in proc.stderr.lower() or "Error" in proc.stderr
