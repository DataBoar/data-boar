"""
CLI ``data-boar-report``: executive Markdown from local SQLite (same core as ``POC_SUMMARY_*.md``).


Enterprise data discovery & risk governance desk output — no live connector required.

Doctrine references:

- ``docs/ops/inspirations/DEFENSIVE_SCANNING_MANIFESTO.md`` §1 — the regen path is
  read-only against the customer SQLite. No DDL, no temp objects, no surprise side
  effects on the customer database. The CLI never opens a network connection.
- ``docs/ops/inspirations/INTERNAL_DIAGNOSTIC_AESTHETICS.md`` §2.2 / §3 — failures
  emit an RCA block (which step, which input, narrowed hypothesis, next manual
  command), not a one-line ``Traceback`` dump. Sysinternals bar: short, technical,
  factual; no invented numbers; one concept per line.
- ``docs/ops/inspirations/THE_ART_OF_THE_FALLBACK.md`` §3 — every demotion has a
  diagnostic. The reporter never falls through to a partial Markdown silently;
  if any step fails, we surface the RCA and exit non-zero.
"""

from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path
from typing import Any

from config.loader import load_config
from core.about import get_about_info
from core.database import LocalDBManager
from report.executive_report import generate_executive_report
from report.safe_prefix import safe_session_prefix
from report.scan_evidence import _aggregate_apg, _build_manifest


def _session_meta(db_manager: LocalDBManager, session_id: str) -> dict[str, Any]:
    for s in db_manager.list_sessions() or []:
        if s.get("session_id") == session_id:
            return {
                "started_at": s.get("started_at"),
                "finished_at": s.get("finished_at"),
                "tenant_name": s.get("tenant_name"),
                "technician_name": s.get("technician_name"),
                "config_scope_hash": s.get("config_scope_hash"),
                "jurisdiction_hint": bool(s.get("jurisdiction_hint")),
            }
    return {
        "started_at": None,
        "finished_at": None,
        "tenant_name": None,
        "technician_name": None,
        "config_scope_hash": None,
        "jurisdiction_hint": False,
    }


# Pipeline step labels surfaced inside the RCA block. Keep stable so DBAs/SREs
# can grep operator transcripts; new steps must be appended (not reordered) to
# preserve the "additive" audit contract documented in
# INTERNAL_DIAGNOSTIC_AESTHETICS.md §2.3.
_STEP_PARSE_ARGS = "parse_args"
_STEP_LOAD_CONFIG = "load_config"
_STEP_OPEN_SQLITE = "open_sqlite"
_STEP_FETCH_FINDINGS = "fetch_findings"
_STEP_BUILD_MANIFEST = "build_manifest"
_STEP_RENDER_MARKDOWN = "render_markdown"
_STEP_WRITE_OUTPUT = "write_output"


def _emit_rca_block(
    *,
    step: str,
    error: BaseException,
    config_path: Path,
    sqlite_path: str,
    session_id: str,
    output_path: Path | None,
) -> None:
    """
    Print a Sysinternals-style RCA block to stderr.

    Why this exists (Julia Evans-style note):

    - A bare Python traceback tells the reader *where in the source tree* an
      exception was raised. It does **not** tell the operator which **stage of
      the regen pipeline** failed, which input to suspect first, or which
      manual command would reproduce the failure on this same SQLite.
    - The RCA block answers those three questions without paging the
      maintainer. It mirrors the post-mortem shape used by Cloudflare and
      NASA SEL: state the symptom, name the narrowed hypothesis, give the
      next manual command. See
      ``docs/ops/inspirations/DEFENSIVE_SCANNING_MANIFESTO.md`` §1 and
      ``docs/ops/inspirations/INTERNAL_DIAGNOSTIC_AESTHETICS.md`` §2.2.
    - Output goes to **stderr** so it never contaminates a piped Markdown
      capture; stdout remains reserved for stakeholder content.
    """
    sid_show = safe_session_prefix(session_id, max_len=16) if session_id else "(empty)"
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
    )

    lines = [
        "",
        "[data-boar-report] RCA — executive Markdown regeneration failed",
        f"  step              {step}",
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
    """
    Map ``(step, exception type)`` to a one-line, factual hypothesis.

    The mapping is intentionally narrow: we name *only* what the symptom
    supports. Wider speculation belongs in the operator runbook, not the RCA.
    """
    error_type = type(error).__name__
    if step == _STEP_PARSE_ARGS:
        return "caller omitted --session-id or passed whitespace-only value"
    if step == _STEP_LOAD_CONFIG:
        if error_type in {"FileNotFoundError", "PermissionError"}:
            return "config YAML missing or unreadable on this workstation"
        return "config YAML parsed but rejected (schema, types, or key constraints)"
    if step == _STEP_OPEN_SQLITE:
        return (
            "sqlite_path resolved but driver could not open the file (path, lock, fs)"
        )
    if step == _STEP_FETCH_FINDINGS:
        return "session_id absent in this SQLite, or schema older than reporter expects"
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
) -> str:
    """Suggest the smallest deterministic command that reproduces the failure."""
    if step == _STEP_PARSE_ARGS:
        return (
            f"python -m cli.reporter --config {config_path} "
            "--session-id <UUID-from-scan_sessions>"
        )
    if step == _STEP_LOAD_CONFIG:
        return f"python -c 'from config.loader import load_config; load_config({str(config_path)!r})'"
    if step in {_STEP_OPEN_SQLITE, _STEP_FETCH_FINDINGS}:
        return (
            "python -c 'from core.database import LocalDBManager; "
            f"m=LocalDBManager({sqlite_path!r}); "
            f"print(len(m.list_sessions())); m.dispose()'"
        )
    if step == _STEP_BUILD_MANIFEST or step == _STEP_RENDER_MARKDOWN:
        return (
            f"python -m cli.reporter --config {config_path} "
            f"--session-id {session_id or '<session>'}"
        )
    if step == _STEP_WRITE_OUTPUT:
        return f"ls -ld {config_path.parent} && touch {config_path.parent}/.write_probe"
    return f"python -m cli.reporter --config {config_path} --session-id {session_id or '<session>'}"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=(
            "Data Boar — enterprise data discovery & risk governance: regenerate executive Markdown "
            "(methodology, security evidence, full APG inventory, Top 3 priorities) from local SQLite "
            "for a completed scan session."
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
        "-o",
        "--output",
        default="",
        help=(
            "Arquivo .md de saída. Se omitido, grava ao lado do YAML de config: "
            "`executive_report_<prefix>.md` (evita expor relatório em stdout/logs de CI)."
        ),
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
        "--debug-traceback",
        action="store_true",
        help=(
            "Após o bloco RCA, imprime o traceback completo no stderr. Útil em "
            "lab; em produção a mensagem narrowed do RCA já é suficiente."
        ),
    )
    args = p.parse_args(argv)

    cfg_path = Path(args.config).expanduser().resolve()
    sid = (args.session_id or "").strip()
    if not sid:
        print("session-id vazio", file=sys.stderr)
        _emit_rca_block(
            step=_STEP_PARSE_ARGS,
            error=ValueError("--session-id is empty after trimming."),
            config_path=cfg_path,
            sqlite_path="",
            session_id="",
            output_path=None,
        )
        return 2

    # Track which pipeline step is in flight so the RCA block can name it
    # without relying on traceback frame inspection (which is fragile across
    # Python versions and minifiers). Mirrors the "step k/N" convention in
    # INTERNAL_DIAGNOSTIC_AESTHETICS.md §2.2.
    current_step = _STEP_LOAD_CONFIG
    out_for_rca: Path | None = None
    db_path = ""
    mgr: LocalDBManager | None = None

    try:
        cfg = load_config(cfg_path)
        db_path = (args.sqlite or "").strip() or str(
            cfg.get("sqlite_path") or "audit_results.db"
        )

        current_step = _STEP_OPEN_SQLITE
        mgr = LocalDBManager(db_path)

        current_step = _STEP_FETCH_FINDINGS
        db_rows, fs_rows, fail_rows = mgr.get_findings(sid)
        meta = _session_meta(mgr, sid)
        about = get_about_info()

        current_step = _STEP_BUILD_MANIFEST
        manifest = _build_manifest(
            session_id=sid,
            meta=meta,
            about=about,
            config=cfg if isinstance(cfg, dict) else {},
            db_rows=db_rows,
            fs_rows=fs_rows,
            fail_rows=fail_rows,
            report_rows_capped=bool(args.trial_rows_capped),
        )
        apg_rows = _aggregate_apg(db_rows, fs_rows)

        current_step = _STEP_RENDER_MARKDOWN
        md = generate_executive_report(
            session_id=sid,
            about=about,
            manifest=manifest,
            db_rows=db_rows,
            fs_rows=fs_rows,
            _fail_rows=fail_rows,
            apg_rows=apg_rows,
            report_rows_capped=bool(args.trial_rows_capped),
        )

        current_step = _STEP_WRITE_OUTPUT
        out_arg = (args.output or "").strip()
        if out_arg:
            out = Path(out_arg).expanduser().resolve()
        else:
            prefix = safe_session_prefix(sid, max_len=8)
            base = cfg_path.parent.resolve()
            out = (base / f"executive_report_{prefix}.md").resolve()
            if not out.is_relative_to(base):
                # Sandbox guard: refuse to write outside the config dir, even
                # if Path.resolve produces a surprising parent. Same posture as
                # report/scan_evidence.py output_dir join check.
                raise ValueError("refuse output path outside config directory")
        out_for_rca = out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md, encoding="utf-8")
        return 0
    except BaseException as exc:  # noqa: BLE001 — RCA must observe every failure mode
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        _emit_rca_block(
            step=current_step,
            error=exc,
            config_path=cfg_path,
            sqlite_path=db_path,
            session_id=sid,
            output_path=out_for_rca,
        )
        if args.debug_traceback:
            sys.stderr.write("\n[data-boar-report] full traceback (debug):\n")
            traceback.print_exc(file=sys.stderr)
        return 3

    finally:
        if mgr is not None:
            mgr.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
