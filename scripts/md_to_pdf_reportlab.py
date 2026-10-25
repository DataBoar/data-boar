"""md_to_pdf_reportlab.py -- MD para PDF com reportlab (robusto)."""

import re
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
from reportlab.lib.units import cm


def _safe(txt: str) -> str:
    # Remove raw markdown bold/italic markers before XML parsing
    txt = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", txt)
    txt = re.sub(r"\*(.+?)\*", r"<i>\1</i>", txt)
    txt = re.sub(r"`([^`]+)`", r"<font face='Courier' size=9>\1</font>", txt)
    txt = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", txt)
    # Strip any remaining naked ** or *
    txt = txt.replace("**", "").replace("*", "")
    return txt


def md_to_pdf(md_path: Path, pdf_path: Path) -> None:
    text = md_path.read_text(encoding="utf-8")
    styles = getSampleStyleSheet()
    BLUE = colors.HexColor("#1a4a7a")
    MID = colors.HexColor("#2c6496")
    h1 = ParagraphStyle(
        "H1", parent=styles["Heading1"], textColor=BLUE, fontSize=18, spaceAfter=10
    )
    h2 = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        textColor=BLUE,
        fontSize=14,
        spaceAfter=8,
        spaceBefore=14,
    )
    h3 = ParagraphStyle(
        "H3",
        parent=styles["Heading3"],
        textColor=MID,
        fontSize=12,
        spaceAfter=6,
        spaceBefore=10,
    )
    body = ParagraphStyle(
        "Body", parent=styles["Normal"], fontSize=10, leading=14, spaceAfter=5
    )
    code_st = ParagraphStyle(
        "Code",
        parent=styles["Code"],
        fontSize=8.5,
        backColor=colors.HexColor("#f5f5f5"),
        spaceAfter=8,
        leftIndent=12,
        rightIndent=12,
    )
    qst = ParagraphStyle(
        "Q",
        parent=styles["Normal"],
        fontSize=9.5,
        leading=13,
        leftIndent=16,
        backColor=colors.HexColor("#f0f7ff"),
        spaceAfter=8,
    )
    bst = ParagraphStyle(
        "B",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        leftIndent=20,
        spaceAfter=4,
    )

    story = []
    in_code, code_buf = False, []
    for line in text.splitlines():
        if line.strip().startswith("```"):
            if in_code:
                story.append(Preformatted("\n".join(code_buf), code_st))
                code_buf = []
                in_code = False
            else:
                in_code = True
            continue
        if in_code:
            code_buf.append(line)
            continue
        if re.match(r"<div|</div>", line.strip()):
            continue
        if re.match(r"^-{3,}$", line.strip()):
            story.append(Spacer(1, 0.25 * cm))
            continue
        if line.startswith("# ") and not line.startswith("## "):
            story.append(Paragraph(_safe(line[2:]), h1))
            continue
        if line.startswith("## ") and not line.startswith("### "):
            story.append(Paragraph(_safe(line[3:]), h2))
            continue
        if line.startswith("### "):
            story.append(Paragraph(_safe(line[4:]), h3))
            continue
        if line.startswith("> "):
            story.append(Paragraph(_safe(line[2:]), qst))
            continue
        if re.match(r"^\s*[-*] ", line):
            txt = re.sub(r"^\s*[-*]\s+", "", line)
            story.append(Paragraph(f"&bull; {_safe(txt)}", bst))
            continue
        if line.startswith("|"):
            continue
        if line.strip():
            try:
                story.append(Paragraph(_safe(line.strip()), body))
            except Exception:
                story.append(Paragraph(re.sub(r"<[^>]+>", "", line.strip()), body))
        else:
            story.append(Spacer(1, 0.15 * cm))

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    doc.build(story)
    print(f"  PDF ok: {pdf_path.name}")


if __name__ == "__main__":
    v2_dir = Path(
        "docs/private/commercial/candidates/linkedin_peer_review/individual/v2"
    )
    pdf_dir = Path("docs/private/commercial/ats_sli_hub/exports/v2/pdf")
    pdf_dir.mkdir(parents=True, exist_ok=True)
    for md in sorted(v2_dir.glob("*.md")):
        pdf = pdf_dir / (md.stem + ".pdf")
        try:
            md_to_pdf(md, pdf)
        except Exception as e:
            print(f"  ERR {md.name}: {e}")
