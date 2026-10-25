"""Executive desk report as PDF from Markdown-shaped text (reportlab)."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from report.executive_markdown_render import (
    LineKind,
    markdown_inline_to_reportlab,
    parse_executive_line,
)


def write_executive_pdf(markdown_text: str, path: Path) -> None:
    """Write a readable PDF from executive Markdown (headings + bullets)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle(
        "ExecH1",
        parent=styles["Heading1"],
        fontSize=14,
        textColor=colors.HexColor("#1a4a7a"),
        spaceAfter=8,
    )
    h2 = ParagraphStyle(
        "ExecH2",
        parent=styles["Heading2"],
        fontSize=12,
        textColor=colors.HexColor("#2c6496"),
        spaceBefore=8,
        spaceAfter=4,
    )
    h3 = ParagraphStyle(
        "ExecH3",
        parent=h2,
        fontSize=11,
        textColor=colors.HexColor("#2c6496"),
    )
    body = ParagraphStyle("ExecBody", parent=styles["Normal"], fontSize=10, leading=13)
    bullet = ParagraphStyle(
        "ExecBullet", parent=body, leftIndent=12, bulletIndent=0, spaceBefore=2
    )

    heading_styles = {
        LineKind.H1: h1,
        LineKind.H2: h2,
        LineKind.H3: h3,
        LineKind.H4: h3,
        LineKind.H5: h3,
    }

    story: list = []
    for raw_line in markdown_text.splitlines():
        parsed = parse_executive_line(raw_line)
        if parsed.kind == LineKind.BLANK:
            story.append(Spacer(1, 0.15 * cm))
            continue
        if parsed.kind in heading_styles:
            story.append(
                Paragraph(
                    markdown_inline_to_reportlab(parsed.text),
                    heading_styles[parsed.kind],
                )
            )
            continue
        if parsed.kind == LineKind.BULLET:
            story.append(
                Paragraph(
                    f"• {markdown_inline_to_reportlab(parsed.text)}",
                    bullet,
                )
            )
            continue
        story.append(Paragraph(markdown_inline_to_reportlab(parsed.text), body))

    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    doc.build(story)
