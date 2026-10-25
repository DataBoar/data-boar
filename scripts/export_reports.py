#!/usr/bin/env python3
"""
Export ``data_boar_grc_executive_report_v1`` JSON to XLSX and/or PDF.

XLSX: one row per ``pii_types`` entry (technical remediation / cleanup list).
PDF: short executive one-pager (metadata, summary metrics, asset table, recommendations).

Example::

    uv run python scripts/export_reports.py --input schemas/grc_executive_report.v1.example.json
"""

from __future__ import annotations

import argparse
from pathlib import Path
from app.grc_dashboard_model import load_grc_json

from report.grc_export_multiformat import export_grc_executive_pdf, export_grc_xlsx


def _default_paths(
    input_path: Path, want_xlsx: bool, want_pdf: bool
) -> tuple[Path | None, Path | None]:
    stem = input_path.stem
    parent = input_path.parent
    xlsx_out = (parent / f"{stem}_remediation.xlsx") if want_xlsx else None
    pdf_out = (parent / f"{stem}_executive.pdf") if want_pdf else None
    return xlsx_out, pdf_out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Export GRC executive JSON (v1) to XLSX and/or PDF."
    )
    p.add_argument(
        "--input",
        required=True,
        help="Path to data_boar_grc_executive_report_v1 JSON.",
    )
    p.add_argument(
        "--xlsx",
        default="",
        help="Output XLSX path (default: <input_stem>_remediation.xlsx next to input).",
    )
    p.add_argument(
        "--pdf",
        default="",
        help="Output PDF path (default: <input_stem>_executive.pdf next to input).",
    )
    p.add_argument(
        "--format",
        choices=("all", "xlsx", "pdf"),
        default="all",
        help="Which artefact(s) to write.",
    )
    args = p.parse_args(argv)

    input_path = Path(args.input).expanduser().resolve()
    data = load_grc_json(input_path)

    want_xlsx = args.format in ("all", "xlsx")
    want_pdf = args.format in ("all", "pdf")
    dxlsx, dpdf = _default_paths(input_path, want_xlsx, want_pdf)

    xlsx_path = Path(args.xlsx).expanduser() if str(args.xlsx).strip() else dxlsx
    pdf_path = Path(args.pdf).expanduser() if str(args.pdf).strip() else dpdf

    if want_xlsx:
        if xlsx_path is None:
            raise SystemExit("XLSX output path missing")
        export_grc_xlsx(data, xlsx_path)
        print(f"Wrote XLSX: {xlsx_path}")
    if want_pdf:
        if pdf_path is None:
            raise SystemExit("PDF output path missing")
        export_grc_executive_pdf(data, pdf_path)
        print(f"Wrote PDF: {pdf_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
