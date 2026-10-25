"""L1 metadata_manifest producer (#1333)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from core.database import LocalDBManager
from core.l1_metadata_manifest import (
    RAW_VALUE_FIELDS,
    SELECTION_RULE,
    L1ContractError,
    assert_l1_contract,
    build_l1_metadata_manifest,
    dumps_l1_manifest,
    load_l1_schema,
    load_pin_metadata,
    sanitize_locator,
    schema_pin_paths,
)

LONG_DIGIT_FILE = "migration_20240725123045.csv"


def _seed_session(db_path: str) -> str:
    sid = "l1-sess-01"
    mgr = LocalDBManager(db_path)
    try:
        mgr.create_session_record(sid)
        mgr.set_current_session_id(sid)
        mgr.save_finding(
            "database",
            target_name="lab-db",
            schema_name="public",
            table_name="customers",
            column_name="email",
            sensitivity_level="HIGH",
            pattern_detected="EMAIL",
            norm_tag="LGPD Art. 5(I)",
        )
        mgr.save_finding(
            "filesystem",
            target_name="lab-fs",
            path="/data/exports",
            file_name=LONG_DIGIT_FILE,
            sensitivity_level="HIGH",
            pattern_detected="LGPD_CPF",
            norm_tag="LGPD Art. 5(II)",
        )
        mgr.finish_session(sid)
    finally:
        mgr.dispose()
    return sid


def test_sanitize_locator_long_digit_filename_preserves_role() -> None:
    """July Sage SAFE-HOLD: 14-digit migration timestamp in the file name."""
    raw = f"/data/exports/{LONG_DIGIT_FILE}"
    out = sanitize_locator(raw)
    assert out is not None
    assert "20240725123045" not in out
    assert "d14" in out
    assert "migration_" in out
    assert out.endswith(".csv")


def test_pin_offline_matches_schema_id() -> None:
    schema_path, pin_path = schema_pin_paths()
    assert schema_path.is_file()
    assert pin_path.is_file()
    pin = load_pin_metadata()
    schema = load_l1_schema()
    assert pin["id"] == schema["$id"]
    assert pin["contract_version"] == "1.0.0"
    assert pin["canonical_repo"] == "DataBoar/data-boar-sdk"
    assert "not a second contract" in str(pin["$comment"]).lower()


def test_build_manifest_validates_and_omits_raw_fields(tmp_path: Path) -> None:
    db_path = str(tmp_path / "audit.db")
    sid = _seed_session(db_path)
    mgr = LocalDBManager(db_path)
    try:
        payload = build_l1_metadata_manifest(mgr, session_id=sid)
    finally:
        mgr.dispose()

    assert payload["kind"] == "metadata_manifest"
    assert payload["plane"] == "L1"
    assert payload["summary"]["excluded_count"] == 0
    assert payload["summary"]["selection_rule"] == SELECTION_RULE
    assert payload["summary"]["total_findings"] == 2
    body_obj = json.loads(json.dumps(payload))

    def _keys(obj: object) -> set[str]:
        found: set[str] = set()
        if isinstance(obj, dict):
            found.update(obj.keys())
            for v in obj.values():
                found.update(_keys(v))
        elif isinstance(obj, list):
            for v in obj:
                found.update(_keys(v))
        return found

    present = _keys(body_obj)
    for key in RAW_VALUE_FIELDS:
        assert key not in present
    assert "co_columns" not in present
    fs = next(f for f in payload["findings"] if f["source_type"] == "filesystem")
    assert "20240725123045" not in (fs.get("location") or "")
    assert "d14" in (fs.get("location") or "")
    assert fs["finding_id"] == "filesystem#1" or fs["finding_id"].startswith(
        "filesystem#"
    )
    db = next(f for f in payload["findings"] if f["source_type"] == "database")
    assert db["sensitivity"] == "high"
    assert db["pattern"] == "EMAIL"
    assert db["norm_tag"] == "lgpd_art_5_i"
    assert fs["value_length"] is None


def test_manifest_is_deterministic(tmp_path: Path) -> None:
    db_path = str(tmp_path / "audit.db")
    sid = _seed_session(db_path)
    mgr = LocalDBManager(db_path)
    try:
        a = dumps_l1_manifest(build_l1_metadata_manifest(mgr, session_id=sid))
        b = dumps_l1_manifest(build_l1_metadata_manifest(mgr, session_id=sid))
    finally:
        mgr.dispose()
    assert a == b


def test_empty_session_emits_empty_findings(tmp_path: Path) -> None:
    db_path = str(tmp_path / "audit.db")
    mgr = LocalDBManager(db_path)
    try:
        payload = build_l1_metadata_manifest(mgr, session_id="no-such-session")
    finally:
        mgr.dispose()
    assert payload["findings"] == []
    assert payload["summary"]["excluded_count"] == 0


def test_fail_closed_on_raw_value_field() -> None:
    bad = {
        "contract_version": "1.0.0",
        "kind": "metadata_manifest",
        "plane": "L1",
        "findings": [
            {
                "finding_id": "database#0",
                "source_type": "database",
                "pattern": "EMAIL",
                "sample_value": "not-emitted",
            }
        ],
    }
    with pytest.raises(L1ContractError, match="raw-value"):
        assert_l1_contract(bad)


def test_cli_export_l1_stdout(tmp_path: Path) -> None:
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
            "--export-l1",
            sid,
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["kind"] == "metadata_manifest"
    assert payload["summary"]["total_findings"] == 2


def test_cli_export_l1_output_file(tmp_path: Path) -> None:
    db_path = str(tmp_path / "audit.db")
    sid = _seed_session(db_path)
    cfg = tmp_path / "config.yaml"
    out = tmp_path / "l1.json"
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
            "--export-l1",
            sid,
            "--l1-output",
            str(out),
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["plane"] == "L1"
