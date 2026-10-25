"""Tests for GRC v1 multi-format export (XLSX + PDF)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd

from app.grc_dashboard_model import grc_remediation_table_rows, load_grc_json
from report.grc_export_multiformat import (
    build_remediation_dataframe,
    export_grc_executive_pdf,
    export_grc_xlsx,
)

_REPO = Path(__file__).resolve().parents[1]
_EXAMPLE = _REPO / "schemas" / "grc_executive_report.v1.example.json"


def test_grc_remediation_table_row_count() -> None:
    data = load_grc_json(_EXAMPLE)
    rows = grc_remediation_table_rows(data)
    assert len(rows) == 3
    assert rows[0]["pii_type"] == "CPF"
    assert rows[0]["remediation_priority"] == "CRITICAL"


def test_export_xlsx_and_pdf_roundtrip(tmp_path: Path) -> None:
    data = load_grc_json(_EXAMPLE)
    xlsx = tmp_path / "out.xlsx"
    pdf = tmp_path / "out.pdf"
    export_grc_xlsx(data, xlsx)
    export_grc_executive_pdf(data, pdf)
    assert xlsx.is_file() and xlsx.stat().st_size > 0
    assert pdf.is_file() and pdf.stat().st_size > 0
    df = pd.read_excel(xlsx, engine="openpyxl")
    assert len(df) == 3
    assert "asset_id" in df.columns and "pii_type" in df.columns


def test_build_remediation_dataframe_matches_rows() -> None:
    data = load_grc_json(_EXAMPLE)
    df = build_remediation_dataframe(data)
    assert len(df) == len(grc_remediation_table_rows(data))


def test_export_reports_cli(tmp_path: Path) -> None:
    script = _REPO / "scripts" / "export_reports.py"
    xlsx = tmp_path / "cli.xlsx"
    pdf = tmp_path / "cli.pdf"
    cmd = [
        sys.executable,
        str(script),
        "--input",
        str(_EXAMPLE),
        "--format",
        "all",
        "--xlsx",
        str(xlsx),
        "--pdf",
        str(pdf),
    ]
    proc = subprocess.run(
        cmd, cwd=str(_REPO), capture_output=True, text=True, check=False
    )
    assert proc.returncode == 0, proc.stderr
    assert xlsx.is_file() and pdf.is_file()
