"""Spreadsheet ODS output when report.formats includes ods (#553)."""

from __future__ import annotations

from pathlib import Path

from config.loader import normalize_config
from core.database import LocalDBManager
from report.generator import generate_report, spreadsheet_formats


def _seed(db_path: str, sid: str = "ods-sess-01") -> str:
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
            norm_tag="LGPD Art. 5(I)",
        )
        mgr.finish_session(sid)
    finally:
        mgr.dispose()
    return sid


def test_normalize_config_report_formats_allowlist():
    out = normalize_config(
        {"targets": [], "report": {"formats": ["ODS", "xlsx", "pdf"]}}
    )
    assert out["report"]["formats"] == ["ods", "xlsx"]
    dropped = normalize_config({"targets": [], "report": {"formats": ["docx", "pdf"]}})
    assert dropped["report"]["formats"] == ["xlsx"]


def test_spreadsheet_formats_default_xlsx_only():
    assert spreadsheet_formats({}) == ["xlsx"]
    assert spreadsheet_formats({"report": {}}) == ["xlsx"]
    assert spreadsheet_formats({"report": {"formats": ["ods", "xlsx", "ods"]}}) == [
        "ods",
        "xlsx",
    ]


def test_report_generates_ods_when_configured(tmp_path: Path):
    out_dir = tmp_path / "reports"
    out_dir.mkdir()
    db_path = tmp_path / "audit.db"
    sid = _seed(str(db_path))
    cfg = {
        "sqlite_path": str(db_path),
        "report": {"output_dir": str(out_dir), "formats": ["xlsx", "ods"]},
    }
    mgr = LocalDBManager(str(db_path))
    try:
        mgr.set_current_session_id(sid)
        path = generate_report(mgr, sid, output_dir=str(out_dir), config=cfg)
    finally:
        mgr.dispose()
    assert path
    xlsx = Path(path)
    assert xlsx.suffix == ".xlsx"
    assert xlsx.is_file()
    ods = xlsx.with_suffix(".ods")
    assert ods.is_file()
    assert ods.stat().st_size > 0
