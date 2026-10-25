"""
generate_talent_playbooks_v2.py  --  LinkedIn Talent Pool Playbooks v2
Gera playbooks copy-paste ready + exporta MD/HTML/PDF/DOCX via pandoc.
Uso: uv run python scripts/generate_talent_playbooks_v2.py [--no-export]
"""

from __future__ import annotations

import argparse
import pathlib
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(pathlib.Path(__file__).parent))

ROOT = Path(__file__).resolve().parent.parent
V2_DIR = ROOT / "docs/private/commercial/candidates/linkedin_peer_review/individual/v2"
EXPORT = ROOT / "docs/private/commercial/ats_sli_hub/exports/v2"

CSS = (
    "body{font-family:Helvetica,Arial,sans-serif;max-width:900px;margin:40px auto;padding:0 20px;color:#222}"
    "h1{color:#1a4a7a;border-bottom:3px solid #1a4a7a;padding-bottom:8px}"
    "h2{color:#1a4a7a;border-bottom:1px solid #ccc;padding-bottom:4px;margin-top:2em}"
    "h3{color:#2c6496;margin-top:1.5em}"
    "blockquote{background:#f0f7ff;border-left:4px solid #1a4a7a;padding:10px 16px;margin:12px 0;font-style:italic}"
    "pre{background:#f5f5f5;border:1px solid #ddd;padding:14px;border-radius:4px;white-space:pre-wrap}"
    "code{background:#f0f0f0;padding:2px 5px;border-radius:3px;font-size:.9em}"
    "table{border-collapse:collapse;width:100%;margin:1em 0}"
    "th{background:#1a4a7a;color:#fff;padding:8px 12px;text-align:left}"
    "td{padding:7px 12px;border-bottom:1px solid #ddd}"
    "tr:nth-child(even){background:#f8f8f8}"
)


def _wkhtmltopdf_exe() -> str:
    wk = shutil.which("wkhtmltopdf")
    if wk:
        return wk
    if sys.platform == "win32":
        wk_pf = Path(r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")
        if wk_pf.is_file():
            return str(wk_pf)
    return "wkhtmltopdf"


def _export(md: Path, base: Path) -> None:
    stem = md.stem
    css = base / "style.css"
    if not css.exists():
        css.parent.mkdir(parents=True, exist_ok=True)
        css.write_text(CSS, encoding="utf-8")
    # --self-contained embeds CSS so wkhtmltopdf does not choke on Windows
    # absolute paths like href="C:\..." (ProtocolUnknownError).
    for fmt, ext, extra in [
        ("html5", "html", ["--css", str(css), "--standalone", "--self-contained"]),
        ("docx", "docx", []),
    ]:
        out = base / ext / f"{stem}.{ext}"
        out.parent.mkdir(parents=True, exist_ok=True)
        r = subprocess.run(
            ["pandoc", str(md), "-f", "markdown", "-t", fmt, "-o", str(out)] + extra,
            capture_output=True,
            text=True,
            timeout=60,
        )
        print(
            f"    {ext.upper()}: {'ok' if r.returncode == 0 else 'WARN ' + r.stderr[:60]}"
        )
    # PDF
    html_src = base / "html" / f"{stem}.html"
    pdf_out = base / "pdf" / f"{stem}.pdf"
    pdf_out.parent.mkdir(parents=True, exist_ok=True)
    if html_src.exists():
        wk_exe = _wkhtmltopdf_exe()
        try:
            r = subprocess.run(
                [wk_exe, "--quiet", str(html_src), str(pdf_out)],
                capture_output=True,
                timeout=120,
                text=True,
            )
            if r.returncode == 0:
                print("    PDF: ok")
            else:
                err = (r.stderr or r.stdout or "").strip()[:200]
                print(f"    PDF: skipped (wkhtmltopdf err: {err})")
        except FileNotFoundError:
            print("    PDF: skipped (wkhtmltopdf not installed)")


from _talent_playbooks_content import PLAYBOOKS  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--no-export", action="store_true")
    p.add_argument("--export-only", action="store_true")
    args = p.parse_args()
    V2_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n{'=' * 56}\nLinkedIn Talent Playbooks v2\n{'=' * 56}")
    if not args.export_only:
        print("\n[1] Writing playbooks...")
        for slug, content in PLAYBOOKS.items():
            path = V2_DIR / f"{slug}_PLAYBOOK_V2.pt_BR.md"
            path.write_text(content, encoding="utf-8")
            print(f"  ok  {path.name}")
    if not args.no_export:
        print("\n[2] Exporting...")
        for md in sorted(V2_DIR.glob("*.md")):
            print(f"  {md.stem}")
            _export(md, EXPORT)
    print("\nDone. Files in docs/private/ (not tracked by Git).\n")


if __name__ == "__main__":
    main()
