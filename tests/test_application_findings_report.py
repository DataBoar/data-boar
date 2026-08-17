"""#1613 — Application/API/CRM findings are not Filesystem findings."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from core.database import LocalDBManager
from report.generator import generate_report


def test_application_finding_persists_and_lists_separately(tmp_path: Path) -> None:
    db_path = str(tmp_path / "app.db")
    mgr = LocalDBManager(db_path)
    try:
        sid = "app-findings-session-1"
        mgr.set_current_session_id(sid)
        mgr.create_session_record(sid)
        mgr.save_finding(
            "application",
            target_name="HubSpot-lab",
            path="contacts",
            file_name="email",
            data_type="application/json",
            sensitivity_level="HIGH",
            pattern_detected="EMAIL",
            norm_tag="LGPD",
            ml_confidence=90,
        )
        mgr.save_finding(
            "api",
            target_name="REST-lab",
            path="https://example.com/users",
            file_name="GET /users | phone",
            data_type="application/json",
            sensitivity_level="MEDIUM",
            pattern_detected="PHONE",
            norm_tag="",
            ml_confidence=70,
        )
        db_rows, fs_rows, app_rows, fail_rows = mgr.get_findings(sid)
        assert db_rows == []
        assert fs_rows == []
        assert fail_rows == []
        assert len(app_rows) == 2
        sessions = mgr.list_sessions()
        assert sessions[0]["application_findings"] == 2
        assert sessions[0]["filesystem_findings"] == 0
    finally:
        mgr.dispose()


def test_hubspot_only_report_omits_filesystem_sheet(tmp_path: Path) -> None:
    db_path = str(tmp_path / "report.db")
    mgr = LocalDBManager(db_path)
    try:
        sid = "hubspot-only-report-sess"
        mgr.set_current_session_id(sid)
        mgr.create_session_record(sid)
        mgr.save_finding(
            "crm",
            target_name="HubSpot",
            path="contacts",
            file_name="firstname",
            data_type="application/json",
            sensitivity_level="MEDIUM",
            pattern_detected="PII_AMBIGUOUS",
            norm_tag="LGPD",
            ml_confidence=75,
        )
        out = generate_report(mgr, sid, output_dir=str(tmp_path), config={})
        assert out
        with pd.ExcelFile(out) as xl:
            assert "Application findings" in xl.sheet_names
            assert "Filesystem findings" not in xl.sheet_names
            app = pd.read_excel(xl, sheet_name="Application findings")
        assert len(app) == 1
        assert app.iloc[0]["file_name"] == "firstname"
    finally:
        mgr.dispose()


def test_filesystem_sheet_still_present_when_fs_findings(tmp_path: Path) -> None:
    db_path = str(tmp_path / "fs.db")
    mgr = LocalDBManager(db_path)
    try:
        sid = "fs-and-app-report-sess"
        mgr.set_current_session_id(sid)
        mgr.create_session_record(sid)
        mgr.save_finding(
            "filesystem",
            target_name="docs",
            path="/tmp",
            file_name="a.txt",
            data_type="TXT",
            sensitivity_level="HIGH",
            pattern_detected="EMAIL",
            norm_tag="",
            ml_confidence=80,
        )
        mgr.save_finding(
            "application",
            target_name="API",
            path="/v1",
            file_name="email",
            data_type="application/json",
            sensitivity_level="HIGH",
            pattern_detected="EMAIL",
            norm_tag="",
            ml_confidence=80,
        )
        out = generate_report(mgr, sid, output_dir=str(tmp_path), config={})
        assert out
        with pd.ExcelFile(out) as xl:
            assert "Filesystem findings" in xl.sheet_names
            assert "Application findings" in xl.sheet_names
    finally:
        mgr.dispose()
