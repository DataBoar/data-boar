"""Executive PDF/DOCX must render Markdown inline (no literal ** / #### / `)."""

from __future__ import annotations

from pathlib import Path

import pytest
from docx import Document
from pypdf import PdfReader

from report.executive_docx import write_executive_docx
from report.executive_pdf import write_executive_pdf
from report.executive_report import generate_executive_report


def _synthetic_executive_markdown() -> str:
    manifest = {
        "engine_signature": {"manifest_generated_at_utc": "2026-07-28T00:00:00+00:00"},
        "scan_window": {"duration_minutes": 1.0},
        "audit_trail": {"dba_facing_summary_pt": []},
        "safety_tags": {"sampling_row_cap_resolved": 500},
        "scope_snapshot": {
            "findings_counts": {
                "database_findings": 1,
                "filesystem_findings": 0,
                "scan_failures": 0,
            },
            "unique_database_tables_with_findings": 1,
        },
    }
    apg_rows = [
        {
            "pattern_detected": "LGPD_CPF, EMAIL",
            "finding_count": 1,
            "risk_band": "Alto",
            "recommended_action": "Mascarar em relatórios.",
            "business_impact": "Exposição regulatória.",
        },
        {
            "pattern_detected": "ML_DETECTED",
            "finding_count": 1,
            "risk_band": "Médio",
            "recommended_action": "Revisar modelo.",
        },
    ]
    return generate_executive_report(
        session_id="session-markdown-export-test",
        about={"name": "Data Boar", "version": "1.7.4-test"},
        manifest=manifest,
        db_rows=[
            {
                "sensitivity_level": "HIGH",
                "pattern_detected": "LGPD_CPF, EMAIL",
                "table_name": "t_users",
                "column_name": "email",
            }
        ],
        fs_rows=[],
        _fail_rows=[],
        apg_rows=apg_rows,
        report_rows_capped=False,
    )


def _pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _docx_text(path: Path) -> str:
    doc = Document(str(path))
    chunks: list[str] = []
    for paragraph in doc.paragraphs:
        chunks.append(paragraph.text)
    return "\n".join(chunks)


@pytest.mark.parametrize(
    "writer, suffix", [(write_executive_pdf, ".pdf"), (write_executive_docx, ".docx")]
)
def test_executive_export_strips_literal_markdown(tmp_path, writer, suffix) -> None:
    md = _synthetic_executive_markdown()
    assert "####" in md
    assert "**" in md
    assert "`" in md

    out = tmp_path / f"executive{suffix}"
    writer(md, out)
    assert out.is_file()

    text = _pdf_text(out) if suffix == ".pdf" else _docx_text(out)
    assert "**" not in text, f"literal ** in exported text: {text[:500]!r}"
    assert "####" not in text, f"literal #### in exported text: {text[:500]!r}"
    assert "`" not in text, f"literal backtick in exported text: {text[:500]!r}"
    assert "LGPD_CPF, EMAIL" in text
    assert "ML_DETECTED" in text
