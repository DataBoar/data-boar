"""Tests for report trends / session comparison sheet."""

import pandas as pd
from pathlib import Path

from core.database import LocalDBManager
from report.generator import _heatmap_path_under_output_dir, generate_report


def test_report_includes_trends_sheet(tmp_path):
    db_path = str(tmp_path / "audit.db")
    out_dir = str(tmp_path / "out")
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    mgr = LocalDBManager(db_path)
    try:
        # First session: 2 DB findings
        mgr.set_current_session_id("s1")
        mgr.create_session_record("s1")
        mgr.save_finding(
            "database",
            target_name="T1",
            column_name="cpf",
            sensitivity_level="HIGH",
            pattern_detected="CPF",
            norm_tag="LGPD",
            ml_confidence=90,
        )
        mgr.save_finding(
            "database",
            target_name="T1",
            column_name="email",
            sensitivity_level="HIGH",
            pattern_detected="EMAIL",
            norm_tag="GDPR",
            ml_confidence=88,
        )
        mgr.finish_session("s1")
        # Second session: 1 DB finding (improvement)
        mgr.set_current_session_id("s2")
        mgr.create_session_record("s2")
        mgr.save_finding(
            "database",
            target_name="T1",
            column_name="cpf",
            sensitivity_level="HIGH",
            pattern_detected="CPF",
            norm_tag="LGPD",
            ml_confidence=90,
        )
        mgr.finish_session("s2")
        path = generate_report(mgr, "s2", output_dir=out_dir)
        assert path is not None
        with pd.ExcelFile(path) as xl:
            assert "Trends - Session comparison" in xl.sheet_names
            df = pd.read_excel(xl, sheet_name="Trends - Session comparison")
        assert len(df) == 4
        assert (
            "Metric" in df.columns and "Note" in df.columns and "Change" in df.columns
        )
        # Total findings: 1 this run vs 2 previous -> improvement
        total_row = df[df["Metric"] == "Total findings (DB + filesystem)"].iloc[0]
        assert (
            "Improvement" in str(total_row["Note"])
            or "reduced" in str(total_row["Note"]).lower()
        )
    finally:
        mgr.dispose()


def test_report_includes_report_info_tenant_and_technician(tmp_path):
    """Report has 'Report info' sheet with Session ID, Started at, Tenant/Customer, Technician/Operator."""
    db_path = str(tmp_path / "audit2.db")
    out_dir = str(tmp_path / "out2")
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    mgr = LocalDBManager(db_path)
    try:
        mgr.set_current_session_id("s-tenant-tech")
        mgr.create_session_record(
            "s-tenant-tech",
            tenant_name="Acme Corp",
            technician_name="Maria Colleague-V",
        )
        mgr.save_finding(
            "database",
            target_name="T1",
            column_name="email",
            sensitivity_level="HIGH",
            pattern_detected="EMAIL",
            norm_tag="GDPR",
            ml_confidence=80,
        )
        mgr.finish_session("s-tenant-tech")
        path = generate_report(mgr, "s-tenant-tech", output_dir=out_dir)
        assert path is not None
        with pd.ExcelFile(path) as xl:
            assert "Report info" in xl.sheet_names
            df = pd.read_excel(xl, sheet_name="Report info")
        assert "Field" in df.columns and "Value" in df.columns
        row_tenant = df[df["Field"] == "Tenant / Customer"].iloc[0]
        assert row_tenant["Value"] == "Acme Corp"
        row_tech = df[df["Field"] == "Technician / Operator"].iloc[0]
        assert row_tech["Value"] == "Maria Colleague-V"
    finally:
        mgr.dispose()


def test_heatmap_embed_only_accepts_path_under_output_dir(tmp_path):
    """Paths outside output_dir are rejected (CodeQL path-injection guard for Excel embed)."""
    out = tmp_path / "report_out"
    out.mkdir()
    good = out / "heatmap_sess123456.png"
    good.write_bytes(b"\x89PNG\r\n\x1a\n")
    assert _heatmap_path_under_output_dir(str(good), str(out)) == good.resolve()
    bad = tmp_path / "outside.png"
    bad.write_bytes(b"x")
    assert _heatmap_path_under_output_dir(str(bad), str(out)) is None


def test_report_excel_and_heatmap_data_sheet_no_regression(tmp_path):
    """Regression: generate_report produces Excel with Heatmap data sheet; heatmap PNG in output_dir when findings exist."""
    db_path = str(tmp_path / "audit_hm.db")
    out_dir = tmp_path / "out_hm"
    out_dir.mkdir(parents=True, exist_ok=True)
    mgr = LocalDBManager(db_path)
    try:
        mgr.set_current_session_id("s-hm")
        mgr.create_session_record("s-hm")
        mgr.save_finding(
            "database",
            target_name="T1",
            column_name="cpf",
            sensitivity_level="HIGH",
            pattern_detected="CPF",
            norm_tag="LGPD",
            ml_confidence=90,
        )
        mgr.finish_session("s-hm")
        path = generate_report(mgr, "s-hm", output_dir=str(out_dir))
        assert path is not None
        with pd.ExcelFile(path) as xl:
            assert "Heatmap data" in xl.sheet_names
            df = pd.read_excel(xl, sheet_name="Heatmap data")
        assert len(df) >= 1
        # Heatmap data is target x sensitivity counts; has index (target) and at least one sensitivity column
        assert df.shape[1] >= 1
        # Heatmap PNG in output_dir when matplotlib available (0 if missing, 1 if present)
        list(
            out_dir.glob("heatmap_*.png")
        )  # no assertion: count is environment-dependent
    finally:
        mgr.dispose()


def test_trends_sheet_shows_up_to_three_previous_runs(tmp_path):
    """Trends sheet includes Prev run 1/2/3 (count and date) and aggregate Note when enough history exists."""
    db_path = str(tmp_path / "audit_trend3.db")
    out_dir = str(tmp_path / "out_trend3")
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    mgr = LocalDBManager(db_path)
    try:
        # Four sessions: 3 -> 2 -> 1 -> 1 findings (improvement then stable; report needs at least one finding)
        for sid, count in [("s1", 3), ("s2", 2), ("s3", 1), ("s4", 1)]:
            mgr.set_current_session_id(sid)
            mgr.create_session_record(sid)
            for _ in range(count):
                mgr.save_finding(
                    "database",
                    target_name="T1",
                    column_name="c",
                    sensitivity_level="HIGH",
                    pattern_detected="CPF",
                    norm_tag="LGPD",
                    ml_confidence=90,
                )
            mgr.finish_session(sid)
        path = generate_report(mgr, "s4", output_dir=out_dir)
        assert path is not None
        with pd.ExcelFile(path) as xl:
            df = pd.read_excel(xl, sheet_name="Trends - Session comparison")
        assert "Prev run 1 (count)" in df.columns and "Prev run 1 (date)" in df.columns
        assert "Prev run 2 (count)" in df.columns and "Prev run 3 (count)" in df.columns
        total_row = df[df["Metric"] == "Total findings (DB + filesystem)"].iloc[0]
        assert total_row["This run (count)"] == 1
        assert total_row["Prev run 1 (count)"] == 1
        assert total_row["Prev run 2 (count)"] == 2
        assert total_row["Prev run 3 (count)"] == 3
        note = str(total_row["Note"])
        assert (
            "Improvement" in note
            or "reduced" in note.lower()
            or "stable" in note.lower()
            or "change" in note.lower()
        )
    finally:
        mgr.dispose()
