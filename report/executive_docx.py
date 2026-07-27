"""Executive desk report as Word (.docx) from Markdown-shaped text (python-docx)."""

from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.shared import Pt


def write_executive_docx(markdown_text: str, path: Path) -> None:
    """Write a simple Word document from executive Markdown (headings + bullets)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = Document()
    style = doc.styles["Normal"]
    style.font.size = Pt(11)

    for raw_line in markdown_text.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue
        if line.startswith("# "):
            doc.add_heading(line[2:].strip(), level=1)
            continue
        if line.startswith("## "):
            doc.add_heading(line[3:].strip(), level=2)
            continue
        if line.startswith("### "):
            doc.add_heading(line[4:].strip(), level=3)
            continue
        if line.startswith("- "):
            doc.add_paragraph(line[2:].strip(), style="List Bullet")
            continue
        plain = re.sub(r"`([^`]+)`", r"\1", line)
        plain = re.sub(r"\*\*([^*]+)\*\*", r"\1", plain)
        plain = plain.replace("*", "")
        doc.add_paragraph(plain)

    doc.save(str(path))
