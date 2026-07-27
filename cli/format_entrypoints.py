"""Thin console-script wrappers for ``data-boar-report --format <X>`` (#1326)."""

from __future__ import annotations

import sys


def _run_format(fmt: str, argv: list[str] | None = None) -> int:
    from cli.reporter import main as report_main

    args = list(argv if argv is not None else sys.argv[1:])
    return report_main(["--format", fmt, *args])


def main_xlsx(argv: list[str] | None = None) -> int:
    return _run_format("xlsx", argv)


def main_pdf(argv: list[str] | None = None) -> int:
    return _run_format("pdf", argv)


def main_docx(argv: list[str] | None = None) -> int:
    return _run_format("docx", argv)


def main_heatmap(argv: list[str] | None = None) -> int:
    return _run_format("heatmap", argv)


def main_dsar(argv: list[str] | None = None) -> int:
    return _run_format("dsar", argv)


def main_audit(argv: list[str] | None = None) -> int:
    return _run_format("audit-trail", argv)
