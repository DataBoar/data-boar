"""
Export ``data_boar_grc_executive_report_v1`` to XLSX (technical remediation table) and PDF (executive one-pager).

Uses **pandas** + **openpyxl** for spreadsheets and **reportlab** for PDF (same stack as other repo PDF helpers).
"""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any

import pandas as pd

from core.licensing.feature_gate import require_feature
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.grc_dashboard_model import grc_remediation_table_rows
from report.excel_sanitizer import excel_safe_dataframe


def build_remediation_dataframe(data: dict[str, Any]) -> pd.DataFrame:
    """DataFrame of flattened PII rows for Excel operators."""
    rows = grc_remediation_table_rows(data)
    return pd.DataFrame(rows)


def export_grc_xlsx(data: dict[str, Any], path: Path) -> None:
    """Write remediation-style XLSX (one row per ``pii_types`` line)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df = build_remediation_dataframe(data)
    excel_safe_dataframe(df).to_excel(path, index=False, engine="openpyxl")


def _p(text: str) -> str:
    """Escape text for ReportLab ``Paragraph`` (subset of HTML)."""
    return html.escape(str(text or ""), quote=False).replace("\n", "<br/>")


def export_grc_executive_pdf(
    data: dict[str, Any],
    path: Path,
    *,
    config: dict[str, Any] | None = None,
) -> None:
    """Short board-ready PDF: metadata, executive summary, asset summary, recommendations."""
    if config is not None:
        require_feature(config, "report_pdf")
    path.parent.mkdir(parents=True, exist_ok=True)
    meta = data["report_metadata"]
    exe = data["executive_summary"]
    styles = getSampleStyleSheet()
    title_st = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontSize=16,
        textColor=colors.HexColor("#1a4a7a"),
        spaceAfter=12,
    )
    h2 = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        fontSize=12,
        textColor=colors.HexColor("#2c6496"),
        spaceBefore=10,
        spaceAfter=6,
    )
    body = ParagraphStyle("Body", parent=styles["Normal"], fontSize=10, leading=14)

    story: list[Any] = []
    story.append(Paragraph(_p("Data Boar — GRC executive report"), title_st))
    client = meta.get("client_display_name") or "—"
    story.append(Paragraph(_p(f"Client label: {client}"), body))
    story.append(Paragraph(_p(f"Report ID: {meta.get('report_id', '—')}"), body))
    story.append(Paragraph(_p(f"Scan date (UTC): {meta.get('scan_date', '—')}"), body))
    story.append(Paragraph(_p(f"Scope: {meta.get('scope', '—')}"), body))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph(_p("Executive summary (heuristic)"), h2))
    story.append(
        Paragraph(
            _p(
                f"Compliance score: {exe.get('compliance_score', '—')} — "
                f"Risk level: {exe.get('risk_level', '—')} — "
                f"PII instances (metadata hits): {exe.get('pii_instances_found', '—')} — "
                f"Critical assets: {exe.get('critical_assets_at_risk', '—')} — "
                f"Records scanned (as reported): {exe.get('total_records_scanned', '—')}"
            ),
            body,
        )
    )
    story.append(
        Paragraph(
            _p(
                f"Method: {exe.get('compliance_score_method', '—')}. "
                "Workshop signals only — not legal adequacy."
            ),
            body,
        )
    )
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph(_p("Risk matrix (assets)"), h2))
    table_data: list[list[str]] = [
        ["Asset", "Risk", "Priority", "Data category"],
    ]
    for row in data.get("detailed_findings") or []:
        if not isinstance(row, dict):
            continue
        table_data.append(
            [
                str(row.get("asset_id", "") or "")[:80],
                str(row.get("risk_score", "")),
                str(row.get("remediation_priority", "") or ""),
                str(row.get("data_category", "") or ""),
            ]
        )
    if len(table_data) == 1:
        table_data.append(["(no rows)", "", "", ""])

    tbl = Table(table_data, colWidths=[7 * cm, 2 * cm, 3 * cm, 3 * cm])
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8eef4")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(tbl)
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph(_p("Recommendations"), h2))
    for rec in data.get("recommendations") or []:
        if not isinstance(rec, dict):
            continue
        rid = rec.get("id", "—")
        pri = rec.get("priority", "—")
        action = rec.get("action", "")
        story.append(Paragraph(_p(f"{rid} ({pri}): {action}"), body))

    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    doc.build(story)
