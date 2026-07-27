"""Executive desk report as PDF from Markdown-shaped text (reportlab)."""

from __future__ import annotations

import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def _escape(text: str) -> str:
    return html.escape(text or "", quote=False).replace("\n", "<br/>")


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
    body = ParagraphStyle("ExecBody", parent=styles["Normal"], fontSize=10, leading=13)
    bullet = ParagraphStyle(
        "ExecBullet", parent=body, leftIndent=12, bulletIndent=0, spaceBefore=2
    )

    story: list = []
    for raw_line in markdown_text.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            story.append(Spacer(1, 0.15 * cm))
            continue
        if line.startswith("# "):
            story.append(Paragraph(_escape(line[2:].strip()), h1))
            continue
        if line.startswith("## "):
            story.append(Paragraph(_escape(line[3:].strip()), h2))
            continue
        if line.startswith("### "):
            story.append(Paragraph(_escape(line[4:].strip()), h2))
            continue
        plain = re.sub(r"`([^`]+)`", r"\1", line)
        plain = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", plain)
        if line.startswith("- "):
            story.append(Paragraph(f"• {_escape(line[2:].strip())}", bullet))
        else:
            story.append(Paragraph(plain, body))

    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    doc.build(story)
