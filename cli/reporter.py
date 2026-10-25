"""
CLI ``data-boar-report``: session report export from local SQLite (#1326).

Formats: md, docx, pdf, xlsx, heatmap, dsar, json, audit-trail, all.

Enterprise data discovery & risk governance desk output — no live connector required.

Doctrine references:

- ``docs/ops/inspirations/DEFENSIVE_SCANNING_MANIFESTO.md`` §1 — read-only against SQLite.
- ``docs/ops/inspirations/INTERNAL_DIAGNOSTIC_AESTHETICS.md`` §2.2 / §3 — RCA block on failure.
- ``docs/ops/inspirations/THE_ART_OF_THE_FALLBACK.md`` §3 — no silent partial export.
"""

from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path

from report.session_export import ALL_FORMATS, SINGLE_FORMATS, export_session_formats

_STEP_PARSE_ARGS = "parse_args"
_STEP_LOAD_CONFIG = "load_config"
_STEP_OPEN_SQLITE = "open_sqlite"
_STEP_FETCH_FINDINGS = "fetch_findings"
_STEP_BUILD_MANIFEST = "build_manifest"
_STEP_RENDER_MARKDOWN = "render_markdown"
_STEP_WRITE_OUTPUT = "write_output"
_STEP_EXPORT = "export_formats"

_FORMAT_CHOICES = (*SINGLE_FORMATS, "all")


def _emit_rca_block(
    *,
    step: str,
    error: BaseException,
    config_path: Path,
    sqlite_path: str,
    session_id: str,
    output_path: Path | None,
    export_format: str,
) -> None:
    sid_show = session_id[:16] if session_id else "(empty)"
    error_type = type(error).__name__
    error_msg = (
        str(error).strip().splitlines()[0] if str(error).strip() else "(no message)"
    )
    out_show = str(output_path) if output_path is not None else "(default — auto path)"

    hypothesis = _narrow_hypothesis(step=step, error=error)
    next_cmd = _next_manual_command(
        step=step,
        config_path=config_path,
        sqlite_path=sqlite_path,
        session_id=session_id,
        export_format=export_format,
    )

    lines = [
        "",
        "[data-boar-report] RCA — session report export failed",
        f"  step              {step}",
        f"  format            {export_format}",
        f"  error_type        {error_type}",
        f"  error_message     {error_msg}",
        f"  config_path       {config_path}",
        f"  sqlite_path       {sqlite_path or '(unset)'}",
        f"  session_id        {sid_show}",
        f"  output_path       {out_show}",
        f"  hypothesis        {hypothesis}",
        f"  next_command      {next_cmd}",
        "  doctrine          docs/ops/inspirations/INTERNAL_DIAGNOSTIC_AESTHETICS.md §2.2",
        "                    docs/ops/inspirations/DEFENSIVE_SCANNING_MANIFESTO.md §1",
        "",
    ]
    sys.stderr.write("\n".join(lines))
    sys.stderr.flush()


def _narrow_hypothesis(*, step: str, error: BaseException) -> str:
    error_type = type(error).__name__
    if step == _STEP_PARSE_ARGS:
        return "caller omitted --session-id, invalid --format, or incompatible -o with --format all"
    if step == _STEP_LOAD_CONFIG:
        if error_type in {"FileNotFoundError", "PermissionError"}:
            return "config YAML missing or unreadable on this workstation"
        return "config YAML parsed but rejected (schema, types, or key constraints)"
    if step == _STEP_OPEN_SQLITE:
        return (
            "sqlite_path resolved but driver could not open the file (path, lock, fs)"
        )
    if step in {_STEP_FETCH_FINDINGS, _STEP_EXPORT}:
        if "Unknown session" in str(error):
            return "session_id absent in this SQLite"
        if "No findings" in str(error):
            return "session exists but has no findings for xlsx/heatmap export"
        return "export pipeline rejected session or finding shape"
    if step == _STEP_BUILD_MANIFEST:
        return (
            "manifest builder rejected config or finding shape (audit_trail invariants)"
        )
    if step == _STEP_RENDER_MARKDOWN:
        return "report renderer received unexpected None / shape after manifest build"
    if step == _STEP_WRITE_OUTPUT:
        if error_type in {"PermissionError", "OSError", "FileNotFoundError"}:
            return "output directory missing or read-only for the current user"
        return "output path rejected by sandbox guard (resolves outside config dir)"
    return "unclassified — re-run with the manual command and capture full stderr"


def _next_manual_command(
    *,
    step: str,
    config_path: Path,
    sqlite_path: str,
    session_id: str,
    export_format: str,
) -> str:
    base = (
        f"python -m cli.reporter --config {config_path} "
        f"--session-id {session_id or '<session>'} --format {export_format}"
    )
    if step == _STEP_PARSE_ARGS:
        return base.replace(session_id or "<session>", "<UUID-from-scan_sessions>")
    if step == _STEP_LOAD_CONFIG:
        return f"python -c 'from config.loader import load_config; load_config({str(config_path)!r})'"
    if step in {_STEP_OPEN_SQLITE, _STEP_FETCH_FINDINGS}:
        return (
            "python -c 'from core.database import LocalDBManager; "
            f"m=LocalDBManager({sqlite_path!r}); "
            f"print(len(m.list_sessions())); m.dispose()'"
        )
    return base


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=(
            "Data Boar — export session reports from local SQLite (no re-scan, no --web). "
            "Formats: md, docx, pdf, xlsx, heatmap, dsar, json, audit-trail, all."
        )
    )
    p.add_argument(
        "--config",
        required=True,
        help="Caminho do YAML de configuração (usa sqlite_path salvo no scan).",
    )
    p.add_argument(
        "--session-id",
        required=True,
        dest="session_id",
        help="ID da sessão (UUID) gravado em scan_sessions.",
    )
    p.add_argument(
        "--format",
        default="md",
        choices=_FORMAT_CHOICES,
        help=(
            "Formato de saída (default: md). "
            "'all' grava md, docx, pdf, xlsx, heatmap, dsar, json e audit-trail."
        ),
    )
    p.add_argument(
        "-o",
        "--output",
        default="",
        help=(
            "Arquivo de saída para um único formato (md, docx, pdf, dsar, json, audit-trail). "
            "Incompatível com --format all ou xlsx/heatmap."
        ),
    )
    p.add_argument(
        "--output-dir",
        default="",
        help="Diretório de saída (default: report.output_dir do config).",
    )
    p.add_argument(
        "--sqlite",
        default="",
        help="Sobrescreve sqlite_path do config (útil em homelab sem editar YAML).",
    )
    p.add_argument(
        "--trial-rows-capped",
        action="store_true",
        help="Propaga nota de linhas limitadas no Excel (licença trial).",
    )
    p.add_argument(
        "--dsar-include-samples",
        action="store_true",
        help="Com --format dsar ou all: inclui amostras brutas quando presentes no SQLite.",
    )
    p.add_argument(
        "--debug-traceback",
        action="store_true",
        help="Após o bloco RCA, imprime traceback completo no stderr.",
    )
    args = p.parse_args(argv)

    cfg_path = Path(args.config).expanduser().resolve()
    sid = (args.session_id or "").strip()
    fmt = args.format
    out_arg = (args.output or "").strip()
    out_dir_arg = (args.output_dir or "").strip()

    if not sid:
        print("session-id vazio", file=sys.stderr)
        _emit_rca_block(
            step=_STEP_PARSE_ARGS,
            error=ValueError("--session-id is empty after trimming."),
            config_path=cfg_path,
            sqlite_path="",
            session_id="",
            output_path=None,
            export_format=fmt,
        )
        return 2

    if fmt == "all" and out_arg:
        print("Cannot use -o/--output with --format all", file=sys.stderr)
        _emit_rca_block(
            step=_STEP_PARSE_ARGS,
            error=ValueError("--output incompatible with --format all"),
            config_path=cfg_path,
            sqlite_path="",
            session_id=sid,
            output_path=Path(out_arg),
            export_format=fmt,
        )
        return 2

    if out_arg and fmt in {"xlsx", "heatmap", "all"}:
        print(
            f"Cannot use -o/--output with --format {fmt}",
            file=sys.stderr,
        )
        _emit_rca_block(
            step=_STEP_PARSE_ARGS,
            error=ValueError(f"--output incompatible with --format {fmt}"),
            config_path=cfg_path,
            sqlite_path="",
            session_id=sid,
            output_path=Path(out_arg),
            export_format=fmt,
        )
        return 2

    formats = list(ALL_FORMATS) if fmt == "all" else [fmt]
    output_file = Path(out_arg).expanduser().resolve() if out_arg else None
    output_dir = Path(out_dir_arg).expanduser().resolve() if out_dir_arg else None

    current_step = _STEP_EXPORT
    out_for_rca: Path | None = output_file
    db_path = ""

    try:
        written = export_session_formats(
            config_path=cfg_path,
            session_id=sid,
            formats=formats,
            sqlite_path=(args.sqlite or "").strip() or None,
            output_dir=output_dir,
            output_file=output_file,
            trial_rows_capped=bool(args.trial_rows_capped),
            dsar_include_samples=bool(args.dsar_include_samples),
        )
        for label, path in written.items():
            print(f"Wrote {label}: {path}")
        return 0
    except BaseException as exc:  # noqa: BLE001 — RCA must observe every failure mode
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        if isinstance(exc, FileNotFoundError):
            msg = str(exc)
            if str(cfg_path) in msg or "Config file not found" in msg:
                current_step = _STEP_LOAD_CONFIG
            else:
                current_step = _STEP_WRITE_OUTPUT
        elif "Unknown session" in str(exc):
            current_step = _STEP_FETCH_FINDINGS
            print(str(exc), file=sys.stderr)
            return 2
        elif "No findings" in str(exc):
            current_step = _STEP_EXPORT
        _emit_rca_block(
            step=current_step,
            error=exc,
            config_path=cfg_path,
            sqlite_path=db_path,
            session_id=sid,
            output_path=out_for_rca,
            export_format=fmt,
        )
        if args.debug_traceback:
            sys.stderr.write("\n[data-boar-report] full traceback (debug):\n")
            traceback.print_exc(file=sys.stderr)
        return 3

    finally:
        pass


if __name__ == "__main__":
    raise SystemExit(main())
