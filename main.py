#!/usr/bin/env python3
"""
CLI entry point: load config (YAML/JSON), run audit and report (optionally tagged with tenant/customer and technician/operator), or start API (--web) on --host/--port (defaults: loopback, 8088; see resolve_api_host).
"""

import argparse
import json
import os
import ssl
import sys
from pathlib import Path
from typing import Any

# Ensure project root on path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config.loader import load_config
from core.database import LocalDBManager
from core.engine import AuditEngine
from core.licensing import LicenseBlockedError
from core.runtime_trust import get_runtime_trust_snapshot


def _cli_public_version_line() -> str:
    """Public CLI --version string (no maturity_build octet; see ADR-0073)."""
    from core.about import _package_version
    from core.integrity_anchor import alpha_version_suffix

    return f"Data Boar {_package_version()}{alpha_version_suffix()}"


def _run_startup_integrity_check(config: dict[str, Any] | None) -> dict[str, Any]:
    """First-run validate / startup re-verify (#856); stderr banner when tampered."""
    from core.integrity_anchor import ALPHA_LABEL, ALPHA_NOTE, ensure_integrity_anchor

    snap = ensure_integrity_anchor(config)
    if snap.get("integrity_state") == "tampered":
        print(
            "*** INTEGRITY: behaviour-critical modules diverge from the "
            f"validated anchor — runtime self-marked {ALPHA_LABEL} ({ALPHA_NOTE}). "
            f"Mismatched: {', '.join(snap.get('mismatched_files', []))} ***",
            file=sys.stderr,
        )
    return snap


def _install_scan_interrupt_signal_handlers() -> None:
    """Map SIGTERM to KeyboardInterrupt so engine finally marks ``interrupted`` (#1251)."""
    import signal

    def _raise_keyboard_interrupt(signum, frame):  # type: ignore[no-untyped-def]
        raise KeyboardInterrupt()

    if hasattr(signal, "SIGTERM"):
        try:
            signal.signal(signal.SIGTERM, _raise_keyboard_interrupt)
        except (ValueError, OSError):
            # Not the main thread / platform rejects — best-effort only.
            pass


def _finish_session_interrupted_if_running(engine: AuditEngine) -> None:
    """Mark current session interrupted when still ``running`` (idempotent vs engine finally)."""
    sid = engine.db_manager.current_session_id
    if sid:
        engine.db_manager.finish_session(sid, "interrupted")


def _emit_runtime_trust_info(
    snapshot: dict[str, Any], *, to_stdout: bool = True, to_stderr: bool = True
) -> None:
    info_line = (
        "[INFO] runtime-trust: "
        f"{snapshot['trust_level'].upper()} "
        f"(state={snapshot.get('trust_state', 'degraded')}, "
        f"license_state={snapshot['license_state']}, "
        f"mode={snapshot['license_mode']})"
    )
    if to_stdout:
        print(info_line)
    if to_stderr:
        print(info_line, file=sys.stderr)

    if not snapshot["is_unexpected"]:
        return

    attention_line = (
        "[INFO] runtime-trust attention: "
        "THERE IS SOMETHING DIFFERENT AND UNEXPECTED IN THIS RUNTIME. "
        "Review license/integrity state before trusting scan or report outputs."
    )
    if to_stdout:
        print(attention_line)
    if to_stderr:
        print(attention_line, file=sys.stderr)


_ENV_FIELDS_TARGET = (
    "pass_from_env",
    "user_from_env",
    "token_from_env",
    "api_key_from_env",
)
_ENV_FIELDS_AUTH = ("client_secret_from_env",)
_SENSITIVE_FIELDS = frozenset(
    {
        "pass_from_env",
        "token_from_env",
        "api_key_from_env",
        "client_secret_from_env",
    }
)


def _mask_env_name(field: str, env_name: str) -> str:
    """Return env var name for logs, masking credential field references."""
    if field in _SENSITIVE_FIELDS:
        return "***"
    return env_name


def _validate_config_and_exit(config: dict[str, Any], config_path: str) -> None:
    """Pre-flight: connector recognition, required keys, env hints (no network/DB)."""
    # Connector registration runs via top-level ``from core.engine import AuditEngine``.

    from core.connector_registry import connector_for_target

    errors: list[str] = []
    warnings: list[str] = []
    targets = config.get("targets", [])

    print(f"Validating config: {config_path}")

    if not targets:
        warnings.append("config: no targets defined")

    for i, target in enumerate(targets):
        name = target.get("name", f"target[{i}]")
        result = connector_for_target(target)

        if result is None:
            t = target.get("type", "?")
            d = target.get("driver", "")
            errors.append(
                f"target \"{name}\": unknown type/driver '{t}'"
                + (f" driver={d!r}" if d else "")
                + " — no connector registered"
            )
            continue

        _, required_keys = result
        for key in required_keys:
            if key not in target:
                errors.append(f'target "{name}": required key "{key}" missing')

        for field in _ENV_FIELDS_TARGET:
            env_name = target.get(field)
            if env_name and not os.environ.get(env_name):
                warnings.append(
                    f'target "{name}": {field}={_mask_env_name(field, env_name)!r} — env var not set'
                )

        auth = target.get("auth") or {}
        for field in _ENV_FIELDS_AUTH:
            env_name = auth.get(field)
            if env_name and not os.environ.get(env_name):
                warnings.append(
                    f'target "{name}": auth.{field}={_mask_env_name(field, env_name)!r} — env var not set'
                )

        # Offline optional SQL driver probe (reuse sql_driver_deps; no connect) — #1246
        kind = (target.get("type") or "").strip().lower()
        if kind == "database":
            from connectors.sql_driver_deps import ensure_sql_driver_available

            driver = target.get("driver") or "postgresql"
            try:
                ensure_sql_driver_available(driver)
            except ImportError as exc:
                warnings.append(f'target "{name}": {exc}')

        driver = target.get("driver", "")
        label = f"type={kind or '?'}" + (f" driver={driver}" if driver else "")
        print(f'  OK    target[{i}] "{name}"  {label}')

    # #1411 — Pro accelerator observability (same class of WARN as missing SQL driver).
    from core.pro_scan_path import (
        resolve_pro_scan_path,
        rust_accelerator_installed,
    )

    _, pf_status = resolve_pro_scan_path(config)
    paid_prefilter_tier = pf_status.get("tier") in (
        "pro_plus",
        "enterprise",
        "partner",
    )
    # Same class as optional SQL-driver WARN, but only when the tier could use
    # the accelerator (OPEN/Community never activate paid accel — avoid noise).
    if paid_prefilter_tier and not rust_accelerator_installed():
        warnings.append(
            "boar_fast_filter (Rust accelerator) is not installed — "
            "PyPI installs use the pure-Python regex-stage fallback; "
            "wheelhouse is the only distribution channel (see TROUBLESHOOTING.md)"
        )
    if pf_status.get("active"):
        print(
            "  OK    rust-regex-stage readiness ACTIVE "
            f"backend={pf_status.get('backend')} tier={pf_status.get('tier')}"
        )
    else:
        # Status JSON may still carry legacy reason codes from WIP routing;
        # product framing (#1414): observability only — no skip/latch narrative.
        print(
            "  OK    rust-regex-stage readiness inactive "
            f"(reason={pf_status.get('reason') or 'n/a'} tier={pf_status.get('tier')})"
        )

    from core.output_paths import OutputPathError, ensure_config_output_directories

    try:
        for msg in ensure_config_output_directories(config):
            print(f"  OK    {msg}")
    except OutputPathError as e:
        errors.append(str(e))

    for w in warnings:
        print(f"  WARN  {w}")
    for e in errors:
        print(f"  ERROR {e}")

    if errors:
        print(f"\n[INVALID] {len(errors)} error(s), {len(warnings)} warning(s).")
        sys.exit(1)
    print(f"\n[OK] {len(targets)} target(s) valid. {len(warnings)} warning(s).")
    sys.exit(0)


def _print_session_diff(result: dict[str, Any]) -> None:
    """Human-readable summary for --diff (stdout)."""
    session_a = result["session_a"]
    session_b = result["session_b"]
    print(f"\nDiff: {session_a} -> {session_b}\n")

    db = result["database"]
    fs = result["filesystem"]
    db_target_names: set[str] = set()
    for bucket in (db["new"], db["resolved"]):
        for f in bucket.values():
            db_target_names.add(f.target_name or "")
    for _k, (fa, _fb) in db["changed"].items():
        db_target_names.add(fa.target_name or "")

    fs_target_names: set[str] = set()
    for bucket in (fs["new"], fs["resolved"]):
        for f in bucket.values():
            fs_target_names.add(f.target_name or "")
    for _k, (fa, _fb) in fs["changed"].items():
        fs_target_names.add(fa.target_name or "")

    n_db_targets = len(db_target_names) or (
        1 if db["new"] or db["resolved"] or db["changed"] else 0
    )
    n_fs_targets = len(fs_target_names) or (
        1 if fs["new"] or fs["resolved"] or fs["changed"] else 0
    )

    print(f"DATABASE ({n_db_targets} target(s) with delta):")
    for f in db["new"].values():
        schema = f.schema_name or ""
        table = f.table_name or ""
        col = f.column_name or ""
        loc = ".".join(p for p in (schema, table, col) if p)
        print(
            f"  NEW    {f.target_name}  {loc}  "
            f"{f.pattern_detected} / {f.sensitivity_level}"
        )
    for f in db["resolved"].values():
        schema = f.schema_name or ""
        table = f.table_name or ""
        col = f.column_name or ""
        loc = ".".join(p for p in (schema, table, col) if p)
        print(f"  RESOLVED  {f.target_name}  {loc}  (was {f.sensitivity_level})")
    for _k, (fa, fb) in db["changed"].items():
        schema = fa.schema_name or ""
        table = fa.table_name or ""
        col = fa.column_name or ""
        loc = ".".join(p for p in (schema, table, col) if p)
        print(
            f"  CHANGED   {fa.target_name}  {loc}  "
            f"{fa.sensitivity_level} -> {fb.sensitivity_level}"
        )

    print(f"\nFILESYSTEM ({n_fs_targets} target(s) with delta):")
    for f in fs["new"].values():
        path = f.path or ""
        fname = f.file_name or ""
        label = f"{path}  {fname}".strip()
        print(
            f"  NEW    {f.target_name}  {label}  "
            f"{f.pattern_detected} / {f.sensitivity_level}"
        )
    for f in fs["resolved"].values():
        path = f.path or ""
        fname = f.file_name or ""
        label = f"{path}  {fname}".strip()
        print(f"  RESOLVED  {f.target_name}  {label}  (was {f.sensitivity_level})")
    for _k, (fa, fb) in fs["changed"].items():
        path = fa.path or ""
        fname = fa.file_name or ""
        label = f"{path}  {fname}".strip()
        print(
            f"  CHANGED   {fa.target_name}  {label}  "
            f"{fa.sensitivity_level} -> {fb.sensitivity_level}"
        )

    n_new = len(db["new"]) + len(fs["new"])
    n_resolved = len(db["resolved"]) + len(fs["resolved"])
    n_changed = len(db["changed"]) + len(fs["changed"])
    n_new_high = result["new_high_count"]
    print(
        f"\nSummary: {n_new} new ({n_new_high} HIGH), "
        f"{n_resolved} resolved, {n_changed} severity change(s)."
    )


def _run_session_diff_cli(
    config: dict[str, Any],
    session_a: str,
    session_b: str,
    *,
    fail_on_new_high: bool,
) -> None:
    from core.database import LocalDBManager

    db_path = config.get("sqlite_path", "audit_results.db")
    mgr = LocalDBManager(db_path)
    try:
        result = mgr.diff_sessions(session_a, session_b)
        _print_session_diff(result)
        if fail_on_new_high and result["new_high_count"] > 0:
            print(
                f"\n[FAIL] --fail-on-new-high: {result['new_high_count']} "
                "new HIGH finding(s). Exit 1."
            )
            sys.exit(1)
    except ValueError as e:
        print(f"Session error: {e}", file=sys.stderr)
        sys.exit(2)
    finally:
        mgr.dispose()


def _run_regenerate_report_cli(
    config: dict[str, Any], config_path: str, session_id: str
) -> None:
    """Regenerate Excel + heatmap (+ learned patterns) from SQLite without re-scan."""
    from core.engine import AuditEngine
    from core.output_paths import OutputPathError, ensure_config_output_directories

    sid = (session_id or "").strip()
    if not sid:
        print("Session error: empty session id", file=sys.stderr)
        sys.exit(2)

    try:
        ensure_config_output_directories(config)
    except OutputPathError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    engine = AuditEngine(config, config_path=config_path)
    try:
        known = {row["session_id"] for row in engine.db_manager.list_sessions()}
        if sid not in known:
            print(f"Session error: Unknown session: {sid}", file=sys.stderr)
            sys.exit(2)
        report_path = engine.generate_final_reports(sid)
        if report_path:
            print(f"Report written: {report_path}")
        else:
            print("No findings to report.")
        from core.plugins.hook import maybe_run_remediation_hook

        maybe_run_remediation_hook(config, sid, db_manager=engine.db_manager)
    finally:
        engine.db_manager.dispose()


def _display_prog(argv0: str | None = None) -> str:
    """Return the operator-facing command form for this runtime."""
    name = Path(argv0 or sys.argv[0] or "").name.lower()
    if name in {"data-boar", "data-boar.exe"}:
        return "data-boar"
    return "python main.py"


def main() -> None:
    prog = _display_prog()
    parser = argparse.ArgumentParser(
        prog=prog,
        description=(
            "Data Boar — enterprise data discovery and risk governance engine. "
            "Loads YAML/JSON config, scans configured databases/filesystems/APIs/shares, "
            "stores finding metadata in local SQLite, and generates Excel reports with heatmaps. "
            "Run once from the CLI or start a REST API dashboard (LGPD/GDPR/CCPA-aware patterns; "
            "additional frameworks via config)."
        ),
        epilog=(
            "Configuration:\n"
            "  - Main config file (YAML or JSON) defines targets (databases, filesystems, APIs, shares),\n"
            "    detection options and report settings. Default is 'config.yaml' in the current directory.\n"
            "  - See docs/USAGE.md for a full schema and examples.\n"
            "\n"
            "CLI examples:\n"
            "  # One-shot audit with the default config.yaml\n"
            f"  {prog} --config config.yaml\n"
            "\n"
            "  # One-shot audit tagging tenant/customer and technician/operator\n"
            f'  {prog} --config config.yaml --tenant "ACME Corp" --technician "Alice"\n'
            "\n"
            "  # One-shot with archive scan + content-type detection (this run only)\n"
            f"  {prog} --config config.yaml --scan-compressed --content-type-check\n"
            f"  {prog} --config config.yaml --progress\n"
            "\n"
            "  # Validate config only (loader checks; no scan or API startup)\n"
            f"  {prog} --config config.yaml --validate-config\n"
            "\n"
            "  # Show rust-regex-stage readiness (paid-tier accelerator; observability)\n"
            f"  {prog} --config config.yaml --prefilter-status\n"
            "\n"
            "  # Compare two scan sessions (CI: add --fail-on-new-high)\n"
            f"  {prog} --config config.yaml --diff <session_a> <session_b>\n"
            "\n"
            "  # DSAR-oriented JSON export for one session (stdout or --dsar-output)\n"
            f"  {prog} --config config.yaml --export-dsar <session_id>\n"
            "\n"
            "  # Remediation manifest JSON for a third-party plugin (#649)\n"
            f"  {prog} --config config.yaml --session <session_id> "
            f"--export-remediation-manifest remediation.json\n"
            "\n"
            "  # Regenerate Excel + heatmap for an existing session (SQLite only; no re-scan)\n"
            f"  {prog} --config config.yaml --regenerate-report <session_id>\n"
            "\n"
            "  # Wipe all collected data and generated reports (dangerous, see SECURITY.md)\n"
            f"  {prog} --config config.yaml --reset-data\n"
            "\n"
            "Web/API examples:\n"
            "  # HTTPS: PEM cert + key (TLS >= 1.2)\n"
            f"  {prog} --config config.yaml --web --https-cert-file server.crt --https-key-file server.key\n"
            "\n"
            "  # Plaintext HTTP (explicit risk acceptance; required when not using TLS)\n"
            f"  {prog} --config config.yaml --web --allow-insecure-http\n"
            "\n"
            "  # Explicit port or bind (same flags as before, still need TLS or --allow-insecure-http)\n"
            f"  {prog} --config config.yaml --web --allow-insecure-http --port 9090\n"
            f"  {prog} --config config.yaml --web --allow-insecure-http --host 0.0.0.0\n"
            "\n"
            "  # Zero-config demo (synthetic corpus, loopback dashboard — no config.yaml)\n"
            f"  {prog} --demo\n"
            "\n"
            "Once a one-shot scan finishes, an Excel report and heatmap PNG are written under\n"
            "the configured report.output_dir (default: current directory). When the API is\n"
            "running, you can navigate to the documented endpoints (see README.md) to trigger\n"
            "scans, list sessions and download the latest reports through the browser."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show the public product version and exit (no scan or API startup).",
    )
    parser.add_argument(
        "--check-extras",
        action="store_true",
        help=(
            "List optional extras × status × origin (image vs /extras mount) and exit. "
            "First step when a connector fails for missing dependencies "
            "(see docs/DOCKER_SETUP.md, docs/USAGE.md)."
        ),
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help=(
            "Zero-config demo: generate a synthetic filesystem corpus in a temp directory, "
            "run an initial scan, and start the dashboard on loopback (127.0.0.1) with "
            "plaintext HTTP (--allow-insecure-http). Does not require --config. "
            "Temp files are removed when the process exits."
        ),
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help=(
            "Path to the main YAML or JSON configuration file. "
            "Defines targets (databases, filesystems, APIs/shares), detection settings and report.output_dir. "
            "Default: config.yaml in the current working directory."
        ),
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help=(
            "Start the REST API/dashboard instead of running a single audit. "
            "Uses api.port from the config when present, otherwise falls back to --port (default 8088)."
        ),
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8088,
        help=(
            "API port when --web is enabled. "
            "If api.port is set in the config file it takes precedence, unless you explicitly pass --port here. "
            "Default: 8088."
        ),
    )
    parser.add_argument(
        "--host",
        default=None,
        metavar="ADDR",
        help=(
            "Bind address when --web is enabled (e.g. 127.0.0.1 or 0.0.0.0). "
            "Takes precedence over api.host in config and over the API_HOST environment variable. "
            "If omitted, resolution follows config api.host, then API_HOST, then safe default 127.0.0.1. "
            "Ignored in one-shot CLI mode."
        ),
    )
    parser.add_argument(
        "--https-cert-file",
        default=None,
        metavar="PATH",
        help=(
            "PEM certificate file for HTTPS when --web is set. "
            "Requires --https-key-file (or api.https_cert_file / api.https_key_file in config). "
            "TLS >= 1.2. Without cert+key, you must pass --allow-insecure-http for plaintext."
        ),
    )
    parser.add_argument(
        "--https-key-file",
        default=None,
        metavar="PATH",
        help=(
            "PEM private key for HTTPS when --web is set. "
            "Requires --https-cert-file (or matching api.* keys in config)."
        ),
    )
    parser.add_argument(
        "--allow-insecure-http",
        action="store_true",
        help=(
            "EXPLICIT RISK ACCEPTANCE: serve the dashboard over plaintext HTTP. "
            "Use only on trusted loopback or lab networks. "
            "For production use TLS (cert+key) or terminate TLS on a reverse proxy. "
            "Can be set via api.allow_insecure_http in config instead of this flag."
        ),
    )
    parser.add_argument(
        "--reset-data",
        action="store_true",
        help=(
            "DANGER: wipe all scan sessions, findings and failures from the SQLite database, "
            "delete generated Excel reports and heatmap PNGs under report.output_dir, "
            "and record an immutable data_wipe_log entry with the reason. "
            "Intended for lab/demo environments; review SECURITY.md before using in production."
        ),
    )
    parser.add_argument(
        "--export-audit-trail",
        metavar="PATH",
        nargs="?",
        const="-",
        default=None,
        help=(
            "Export a JSON audit trail from SQLite (data_wipe_log, session summary, "
            "maturity_assessment_integrity when applicable; future: integrity anchor). "
            "PATH optional: omit or '-' for stdout; "
            "otherwise write to PATH. Does not modify the database. "
            "Incompatible with --web and --reset-data."
        ),
    )
    parser.add_argument(
        "--validate-config",
        action="store_true",
        help=(
            "Validate config structure, connector types, and required keys per target; "
            "warn on unset *_from_env vars and missing optional SQL driver packages "
            "(offline import probe). Also reports rust-regex-stage / accelerator "
            "readiness (#1411 / #1414; observability only). No connections, scan, or --web. "
            "Exit 0 when valid, 1 on errors. Incompatible with --web, --reset-data, "
            "and --export-audit-trail."
        ),
    )
    parser.add_argument(
        "--prefilter-status",
        action="store_true",
        help=(
            "Print rust-regex-stage / prefilter readiness for this config as JSON "
            "(active, name, backend rust|python, tier, reason, engine) and exit. "
            "Observability only — does not change findings (#1411 / #1412)."
        ),
    )
    parser.add_argument(
        "--diff",
        nargs=2,
        metavar=("SESSION_A", "SESSION_B"),
        dest="diff_sessions",
        help=(
            "Compare findings between two scan sessions by UUID. "
            "Prints new, resolved, and severity-changed rows. "
            "Use --fail-on-new-high for CI exit 1 when new HIGH findings appear."
        ),
    )
    parser.add_argument(
        "--fail-on-new-high",
        action="store_true",
        dest="fail_on_new_high",
        help=(
            "With --diff: exit 1 when SESSION_B has new HIGH-sensitivity findings "
            "vs SESSION_A (CI regression gate)."
        ),
    )
    parser.add_argument(
        "--export-dsar",
        metavar="SESSION_ID",
        dest="export_dsar",
        default=None,
        help=(
            "Export findings for SESSION_ID as DSAR-ready JSON (LGPD Art. 18 / "
            "GDPR Art. 15). Metadata-first by default; use --dsar-include-samples "
            "only when stored sample fields must be included. Print to stdout or "
            "--dsar-output PATH. Incompatible with --web and --reset-data."
        ),
    )
    parser.add_argument(
        "--dsar-output",
        metavar="PATH",
        dest="dsar_output",
        default=None,
        help="Write DSAR export to PATH instead of stdout. Requires --export-dsar.",
    )
    parser.add_argument(
        "--dsar-include-samples",
        action="store_true",
        dest="dsar_include_samples",
        help=(
            "With --export-dsar: include raw sample fields from finding rows when "
            "present (increases disclosure risk; SQLite stores metadata only by default)."
        ),
    )
    parser.add_argument(
        "--session",
        metavar="SESSION_ID",
        dest="session_id",
        default=None,
        help=(
            "Scan session UUID for session-scoped exports. Required with "
            "--export-remediation-manifest."
        ),
    )
    parser.add_argument(
        "--export-remediation-manifest",
        metavar="PATH",
        dest="export_remediation_manifest",
        default=None,
        help=(
            "Write a remediation-plugin JSON manifest (schema v1) for --session to PATH. "
            "Metadata only (connection_ref, locations, pii_type) — no raw PII and no "
            "credentials. Enterprise-tier feature (open in licensing.mode off / OPEN). "
            "Incompatible with --web, --reset-data, --export-audit-trail, --export-dsar, "
            "--validate-config, --diff, and --regenerate-report."
        ),
    )
    parser.add_argument(
        "--regenerate-report",
        metavar="SESSION_ID",
        dest="regenerate_report",
        default=None,
        help=(
            "Regenerate Excel workbook and heatmap PNG for SESSION_ID from the "
            "configured SQLite database (also writes learned_patterns when enabled). "
            "No live target scan and no --web. Incompatible with --web, --reset-data, "
            "--validate-config, --diff, --export-dsar, --export-remediation-manifest, "
            "and --export-audit-trail."
        ),
    )
    parser.add_argument(
        "--tenant",
        default=None,
        help=(
            "Optional customer/tenant name for this scan. "
            "Stored in the session metadata and included in the Excel report header for traceability."
        ),
    )
    parser.add_argument(
        "--technician",
        default=None,
        help=(
            "Optional name of the technician/operator responsible for this scan. "
            "Also stored in session metadata and shown in the report header."
        ),
    )
    parser.add_argument(
        "--scan-compressed",
        action="store_true",
        help=(
            "When set, act as if file_scan.scan_compressed is true for this run: "
            "scan inside supported archives (zip, tar, 7z, etc.). May increase run time and I/O."
        ),
    )
    parser.add_argument(
        "--content-type-check",
        action="store_true",
        dest="content_type_check",
        help=(
            "When set, act as if file_scan.use_content_type is true for this run: "
            "infer file format from magic bytes (first bytes of each file), not only extension—"
            "helps find renamed or cloaked files. Adds extra I/O and CPU per file."
        ),
    )
    parser.add_argument(
        "--scan-stego",
        action="store_true",
        dest="scan_stego",
        help=(
            "When set, act as if file_scan.scan_for_stego is true for this run: "
            "append lightweight entropy hints for image/audio/video containers (heuristic only; "
            "not proof of hidden data). Increases per-file reads on rich media."
        ),
    )
    parser.add_argument(
        "--jurisdiction-hint",
        action="store_true",
        dest="jurisdiction_hint",
        help=(
            "Opt-in for this run: add heuristic jurisdiction notes (e.g. CCPA/CPRA, Colorado, Japan APPI) "
            "to the Excel Report info sheet when metadata signals suggest possible relevance. "
            "Not a legal conclusion; high false-positive rate. Same as report.jurisdiction_hints.enabled "
            "for this process and stores the opt-in on the session."
        ),
    )
    parser.add_argument(
        "--validate-crypto",
        action="store_true",
        dest="validate_crypto",
        help=(
            "Opt-in for this run: enable strong-crypto / controls validation wiring "
            "(scan.validate_crypto). Off by default. Phase 1 wires the flag only; "
            "full per-connector TLS checks and anonymisation heuristics land in later phases. "
            "CLI overrides config when this flag is set."
        ),
    )
    progress_group = parser.add_mutually_exclusive_group()
    progress_group.add_argument(
        "--progress",
        action="store_true",
        dest="scan_progress",
        default=None,
        help=(
            "Emit periodic scan progress to stderr (target X/Y, table N/M, percent, ETA). "
            "Default when omitted: scan.progress in config (true unless disabled)."
        ),
    )
    progress_group.add_argument(
        "--no-progress",
        action="store_false",
        dest="scan_progress",
        help="Disable live scan progress lines for this run.",
    )
    args = parser.parse_args()

    if args.version:
        _run_startup_integrity_check({"sqlite_path": "audit_results.db"})
        print(_cli_public_version_line())
        sys.exit(0)

    if args.check_extras:
        from core.extras_manifest import format_check_extras_table
        from core.extras_runtime import verify_extras_abi_or_exit

        verify_extras_abi_or_exit()
        print(format_check_extras_table(), end="")
        sys.exit(0)

    # Fail closed when a mounted /extras pack does not match this interpreter ABI (#1400).
    from core.extras_runtime import verify_extras_abi_or_exit

    verify_extras_abi_or_exit()

    demo_mode = bool(getattr(args, "demo", False))
    demo_dir: Path | None = None

    if demo_mode:
        demo_incompatible = (
            args.validate_config
            or args.prefilter_status
            or args.check_extras
            or args.reset_data
            or args.export_audit_trail is not None
            or args.export_dsar is not None
            or args.export_remediation_manifest is not None
            or args.diff_sessions
            or args.regenerate_report is not None
        )
        if demo_incompatible:
            print(
                "Cannot combine --demo with --validate-config, --prefilter-status, "
                "--check-extras, --reset-data, --export-audit-trail, --export-dsar, "
                "--export-remediation-manifest, --diff, or --regenerate-report.",
                file=sys.stderr,
            )
            sys.exit(2)
        from core.demo.runtime import prepare_demo_workspace, print_demo_banner

        demo_dir, config_path, _preloaded = prepare_demo_workspace(
            port=args.port,
            register_cleanup=True,
        )
        args.config = str(config_path)
        args.web = True
        args.allow_insecure_http = True
        if args.host and args.host not in ("127.0.0.1", "localhost", "::1"):
            print(
                f"[demo] Ignoring --host {args.host!r}; demo binds loopback only.",
                file=sys.stderr,
            )
        args.host = "127.0.0.1"
        print_demo_banner(args.port, demo_dir)

    if args.validate_config and (
        args.web
        or args.reset_data
        or args.export_audit_trail is not None
        or args.export_dsar is not None
        or args.export_remediation_manifest is not None
        or args.regenerate_report is not None
        or args.prefilter_status
    ):
        print(
            "Cannot combine --validate-config with --web, --reset-data, "
            "--export-audit-trail, --export-dsar, --export-remediation-manifest, "
            "--regenerate-report, or --prefilter-status.",
            file=sys.stderr,
        )
        sys.exit(2)

    if args.prefilter_status and (
        args.web
        or args.reset_data
        or args.export_audit_trail is not None
        or args.export_dsar is not None
        or args.export_remediation_manifest is not None
        or args.regenerate_report is not None
        or args.diff_sessions
    ):
        print(
            "Cannot combine --prefilter-status with --web, --reset-data, "
            "--export-audit-trail, --export-dsar, --export-remediation-manifest, "
            "--regenerate-report, or --diff.",
            file=sys.stderr,
        )
        sys.exit(2)

    if args.diff_sessions and (
        args.web
        or args.reset_data
        or args.export_audit_trail is not None
        or args.validate_config
        or args.export_dsar is not None
        or args.export_remediation_manifest is not None
        or args.regenerate_report is not None
    ):
        print(
            "Cannot combine --diff with --web, --reset-data, --export-audit-trail, "
            "--export-dsar, --export-remediation-manifest, --validate-config, "
            "or --regenerate-report.",
            file=sys.stderr,
        )
        sys.exit(2)

    if args.export_dsar is not None and (
        args.web
        or args.reset_data
        or args.export_audit_trail is not None
        or args.validate_config
        or args.diff_sessions
        or args.export_remediation_manifest is not None
        or args.regenerate_report is not None
    ):
        print(
            "Cannot combine --export-dsar with --web, --reset-data, "
            "--export-audit-trail, --validate-config, --diff, "
            "--export-remediation-manifest, or --regenerate-report.",
            file=sys.stderr,
        )
        sys.exit(2)

    if args.export_remediation_manifest is not None and (
        args.web
        or args.reset_data
        or args.export_audit_trail is not None
        or args.validate_config
        or args.diff_sessions
        or args.export_dsar is not None
        or args.prefilter_status
        or args.regenerate_report is not None
    ):
        print(
            "Cannot combine --export-remediation-manifest with --web, --reset-data, "
            "--export-audit-trail, --validate-config, --diff, --export-dsar, "
            "--prefilter-status, or --regenerate-report.",
            file=sys.stderr,
        )
        sys.exit(2)

    if args.regenerate_report is not None and (
        args.web
        or args.reset_data
        or args.export_audit_trail is not None
        or args.validate_config
        or args.diff_sessions
        or args.export_dsar is not None
        or args.export_remediation_manifest is not None
    ):
        print(
            "Cannot combine --regenerate-report with --web, --reset-data, "
            "--export-audit-trail, --validate-config, --diff, --export-dsar, "
            "or --export-remediation-manifest.",
            file=sys.stderr,
        )
        sys.exit(2)

    if args.dsar_output and args.export_dsar is None:
        print("--dsar-output requires --export-dsar.", file=sys.stderr)
        sys.exit(2)

    if args.dsar_include_samples and args.export_dsar is None:
        print("--dsar-include-samples requires --export-dsar.", file=sys.stderr)
        sys.exit(2)

    if args.export_remediation_manifest is not None and not (
        args.session_id and str(args.session_id).strip()
    ):
        print(
            "--export-remediation-manifest requires --session <session_id>.",
            file=sys.stderr,
        )
        sys.exit(2)

    if args.session_id and args.export_remediation_manifest is None:
        print(
            "--session requires --export-remediation-manifest <path.json>.",
            file=sys.stderr,
        )
        sys.exit(2)

    try:
        config = load_config(args.config)
    except FileNotFoundError as e:
        print(f"Config not found: {e}")
        if not demo_mode:
            print(
                "Tip: run `data-boar --demo` for a zero-config synthetic demo "
                "(no config.yaml required)."
            )
        print("Probable cause: The config file path is wrong or the file was moved.")
        print(
            "What to do: Check the path, use --config to point to your YAML/JSON, or create config.yaml in the current directory."
        )
        sys.exit(1)
    except Exception as e:
        print(f"Config error: {e}")
        print("Probable cause: Invalid YAML/JSON syntax or a required key is missing.")
        print(
            "What to do: Validate your config against docs/USAGE.md; check indentation and quoted strings."
        )
        sys.exit(1)

    if args.validate_config:
        _integrity = _run_startup_integrity_check(config)
        runtime_trust = get_runtime_trust_snapshot(config)
        _emit_runtime_trust_info(runtime_trust, to_stdout=True, to_stderr=True)
        _validate_config_and_exit(config, args.config)

    if args.prefilter_status:
        from core.pro_scan_path import resolve_pro_scan_path, rust_accelerator_installed

        _, pf_status = resolve_pro_scan_path(config)
        payload = {
            **pf_status,
            "rust_accelerator_installed": rust_accelerator_installed(),
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        sys.exit(0)

    if args.diff_sessions:
        session_a, session_b = args.diff_sessions
        _run_session_diff_cli(
            config,
            session_a,
            session_b,
            fail_on_new_high=args.fail_on_new_high,
        )
        sys.exit(0)

    if args.scan_compressed:
        config.setdefault("file_scan", {})["scan_compressed"] = True
    if args.content_type_check:
        config.setdefault("file_scan", {})["use_content_type"] = True
    if getattr(args, "scan_stego", False):
        config.setdefault("file_scan", {})["scan_for_stego"] = True
    if args.jurisdiction_hint:
        config.setdefault("report", {}).setdefault("jurisdiction_hints", {})
        config["report"]["jurisdiction_hints"]["enabled"] = True
    if getattr(args, "validate_crypto", False):
        # CLI overrides scan.validate_crypto when the flag is present.
        config.setdefault("scan", {})["validate_crypto"] = True
    if getattr(args, "scan_progress", None) is not None:
        config.setdefault("scan", {})["progress"] = bool(args.scan_progress)

    # #856 (Phase E): integrity anchor first-run validation / startup re-verify.
    # Runs in ANY licensing mode (including open); fail-soft (state=unknown).
    _integrity = _run_startup_integrity_check(config)

    runtime_trust = get_runtime_trust_snapshot(config)

    if args.export_dsar is not None:
        _emit_runtime_trust_info(runtime_trust, to_stdout=False, to_stderr=True)
        from core.dsar_export import build_dsar_payload

        engine = AuditEngine(config, config_path=args.config)
        try:
            payload = build_dsar_payload(
                engine.db_manager,
                session_id=args.export_dsar,
                include_samples=args.dsar_include_samples,
            )
            body = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
            dest = args.dsar_output
            if dest:
                Path(dest).write_text(body, encoding="utf-8")
                print(f"DSAR export written to {dest}", file=sys.stderr)
            else:
                sys.stdout.write(body)
        finally:
            engine.db_manager.dispose()
        return

    if args.export_remediation_manifest is not None:
        _emit_runtime_trust_info(runtime_trust, to_stdout=False, to_stderr=True)
        from core.licensing.errors import FeatureTierBlockedError
        from core.licensing.feature_gate import require_feature
        from core.remediation_manifest import build_remediation_manifest

        try:
            require_feature(config, "remediation_manifest_export")
        except FeatureTierBlockedError as e:
            print(f"Licensing: {e}", file=sys.stderr)
            sys.exit(2)

        engine = AuditEngine(config, config_path=args.config)
        try:
            try:
                payload = build_remediation_manifest(
                    engine.db_manager,
                    session_id=str(args.session_id),
                    config=config,
                )
            except ValueError as e:
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)
            body = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
            dest = Path(args.export_remediation_manifest)
            try:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(body, encoding="utf-8")
            except OSError as e:
                print(
                    f"Error: cannot write remediation manifest to {dest}: {e}",
                    file=sys.stderr,
                )
                sys.exit(1)
            print(f"Remediation manifest written to {dest}", file=sys.stderr)
        finally:
            engine.db_manager.dispose()
        return

    if args.regenerate_report is not None:
        _emit_runtime_trust_info(runtime_trust, to_stdout=False, to_stderr=True)
        _run_regenerate_report_cli(config, args.config, args.regenerate_report)
        return

    if args.export_audit_trail is not None:
        # Keep stdout clean for JSON when export destination is stdout.
        _emit_runtime_trust_info(runtime_trust, to_stdout=False, to_stderr=True)
        if args.web:
            print(
                "Cannot combine --export-audit-trail with --web.",
                file=sys.stderr,
            )
            sys.exit(2)
        if args.reset_data:
            print(
                "Cannot combine --export-audit-trail with --reset-data.",
                file=sys.stderr,
            )
            sys.exit(2)
        from core.audit_export import build_audit_trail_payload

        engine = AuditEngine(config, config_path=args.config)
        try:
            sqlite_path = config.get("sqlite_path", "audit_results.db")
            payload = build_audit_trail_payload(
                engine.db_manager,
                config=config,
                config_path=args.config,
                sqlite_path=sqlite_path,
            )
            body = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
            dest = args.export_audit_trail
            if dest in ("-", None):
                sys.stdout.write(body)
            else:
                Path(dest).write_text(body, encoding="utf-8")
                print(f"Audit trail exported to {dest}", file=sys.stderr)
        finally:
            engine.db_manager.dispose()
        return

    if args.web and not args.reset_data:
        if demo_mode:
            from core.validation import sanitize_tenant_technician

            _install_scan_interrupt_signal_handlers()
            engine = AuditEngine(config, config_path=args.config)
            try:
                _emit_runtime_trust_info(runtime_trust, to_stdout=True, to_stderr=True)
                tenant = sanitize_tenant_technician(args.tenant)
                technician = sanitize_tenant_technician(args.technician)
                session_id = engine.start_audit(
                    tenant_name=tenant,
                    technician_name=technician,
                    jurisdiction_hint=bool(args.jurisdiction_hint),
                )
                print(f"[demo] Scan session: {session_id}")
                report_path = engine.generate_final_reports(session_id)
                if report_path:
                    print(f"[demo] Report written: {report_path}")
                else:
                    print("[demo] No findings to report.")
                from core.plugins.hook import maybe_run_remediation_hook

                maybe_run_remediation_hook(
                    config, session_id, db_manager=engine.db_manager
                )
            except KeyboardInterrupt:
                _finish_session_interrupted_if_running(engine)
                print("[demo] Scan interrupted.", file=sys.stderr)
                sys.exit(130)
            finally:
                engine.db_manager.dispose()

        _emit_runtime_trust_info(runtime_trust, to_stdout=True, to_stderr=True)
        import uvicorn
        from api.routes import app
        from core.dashboard_transport import (
            configure_dashboard_transport,
            resolve_web_listen_options,
        )
        from core.host_resolution import (
            effective_api_key_configured,
            resolve_api_host,
            should_block_non_loopback_without_auth,
            should_warn_insecure_api_bind,
        )

        api_cfg = config.get("api", {})
        if demo_mode:
            api_cfg = {**api_cfg, "host": "127.0.0.1", "allow_insecure_http": True}
            config["api"] = api_cfg
        if bool(api_cfg.get("require_api_key")) and not effective_api_key_configured(
            api_cfg
        ):
            print(
                "ERROR: api.require_api_key is true but no API key is available. "
                "Set api.api_key (avoid committing secrets) or api.api_key_from_env "
                "with the named environment variable set before the process starts. "
                "See docs/ops/API_KEY_FROM_ENV_OPERATOR_STEPS.md.",
                file=sys.stderr,
            )
            sys.exit(2)
        port = api_cfg.get("port", args.port)
        workers = int(api_cfg.get("workers", 1))
        host = resolve_api_host(config, cli_host=args.host)
        if should_block_non_loopback_without_auth(config, host):
            print(
                "ERROR: Refusing startup with non-loopback API bind and unresolved auth boundary. "
                "Set host to 127.0.0.1 or configure built-in auth (api.api_key/api_key_from_env "
                "or api.webauthn with token secret).",
                file=sys.stderr,
                flush=True,
            )
            sys.exit(2)
        try:
            mode, cert_path, key_path, insecure_explicit = resolve_web_listen_options(
                allow_insecure_http_cli=args.allow_insecure_http,
                https_cert_file_cli=args.https_cert_file,
                https_key_file_cli=args.https_key_file,
                api_cfg=api_cfg,
            )
        except ValueError as e:
            print(f"Dashboard transport error: {e}", file=sys.stderr, flush=True)
            sys.exit(2)

        cert_str = str(cert_path) if cert_path else None
        key_str = str(key_path) if key_path else None
        configure_dashboard_transport(
            mode=mode,
            insecure_explicit_opt_in=insecure_explicit,
            cert_path=cert_str,
            key_path=key_str,
        )
        from core.canonical_trust import get_canonical_trust_snapshot
        from core.tls_posture import (
            clear_tls_posture_snapshot,
            expected_fingerprints_from_api_cfg,
            probe_ssl_context,
            set_tls_posture_snapshot,
        )

        ssl_ctx: ssl.SSLContext | None = None
        if mode == "https":
            info = (
                "[INFO] Dashboard transport: HTTPS (TLS >= 1.2) — "
                f"bound on {host}:{port}"
            )
            print(info)
            print(info, file=sys.stderr, flush=True)
            ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_ctx.minimum_version = ssl.TLSVersion.TLSv1_2
            ssl_ctx.load_cert_chain(certfile=cert_str, keyfile=key_str)
            # S2a wave-2a/2b: cipher/protocol + optional cert fingerprint (no bind).
            _tls_posture = probe_ssl_context(
                ssl_ctx,
                cert_path=cert_str,
                expected_fingerprints=expected_fingerprints_from_api_cfg(api_cfg),
            )
            set_tls_posture_snapshot(_tls_posture)
            print(
                f"[INFO] tls_posture ok={_tls_posture.get('ok')} "
                f"reasons={_tls_posture.get('trust_reasons')} "
                f"summary={_tls_posture.get('summary')}",
                file=sys.stderr,
                flush=True,
            )
            if not _tls_posture.get("ok"):
                print(
                    "WARNING: Dashboard TLS posture below baseline — "
                    f"{_tls_posture.get('summary')}",
                    file=sys.stderr,
                    flush=True,
                )
        else:
            clear_tls_posture_snapshot()
            banner = (
                "======================================================================\n"
                "WARNING: DASHBOARD PLAINTEXT HTTP — EXPLICIT OPT-IN\n"
                "Traffic is NOT encrypted between browsers and this process.\n"
                "Anyone on the network path may read or modify requests.\n"
                "Use --https-cert-file/--https-key-file for TLS, or terminate TLS\n"
                "on a reverse proxy. Do not use plaintext on untrusted networks.\n"
                "======================================================================"
            )
            print(banner, file=sys.stderr, flush=True)
            print(
                "[INFO] dashboard_transport=insecure_http", file=sys.stderr, flush=True
            )

        _canonical = get_canonical_trust_snapshot(config)
        _canonical_line = (
            "[INFO] trust_state="
            f"{_canonical['trust_state']} "
            f"reasons={_canonical['trust_reasons']} "
            f"output_confidence={_canonical['output_confidence']}"
        )
        print(_canonical_line, file=sys.stderr, flush=True)

        if should_warn_insecure_api_bind(config, host):
            print(
                "WARNING: API bind is non-loopback (%s) but api.require_api_key is not "
                "effectively enabled. Scan findings (including PII) are reachable without "
                "authentication (LGPD Art. 46 / adequate security measures). Set "
                "api.require_api_key: true and a strong api.api_key (or api_key_from_env), "
                "or keep host 127.0.0.1 / reverse proxy. See SECURITY.md and docs/USAGE.md."
                % (host,),
                file=sys.stderr,
                flush=True,
            )

        uvicorn_kwargs: dict[str, Any] = {
            "host": host,
            "port": port,
            "workers": workers,
        }
        if ssl_ctx is not None:
            # uvicorn>=0.52 removed run(..., ssl=ctx); keep TLS>=1.2 via factory.
            def _ssl_context_factory(config, create_default_context, _ctx=ssl_ctx):
                return _ctx

            uvicorn_kwargs["ssl_context_factory"] = _ssl_context_factory
        uvicorn.run(app, **uvicorn_kwargs)
        return

    engine = AuditEngine(config, config_path=args.config)

    if args.reset_data:
        _emit_runtime_trust_info(runtime_trust, to_stdout=True, to_stderr=True)
        # Require explicit confirmation: no undo, no going back.
        print()
        print("*** WIPE ALL GATHERED DATA ***")
        print()
        print("This will permanently:")
        print(
            "  - Remove all scan sessions, findings and failures from the SQLite database"
        )
        print(
            "  - Delete all generated Excel reports and heatmap PNGs under report.output_dir"
        )
        print()
        print("There is NO going back after this step. There is NO undo button.")
        print("Only a log entry in the database will record that a wipe was performed.")
        print()
        try:
            answer = (
                input("Type 'yes' to confirm and proceed, or anything else to abort: ")
                .strip()
                .lower()
            )
        except (EOFError, KeyboardInterrupt):
            answer = ""
        if answer != "yes":
            print("Aborted. No data was wiped.")
            return
        # Wipe DB contents and generated artifacts, but leave an immutable audit entry of the wipe itself.
        reason = f"CLI --reset-data invoked using config {args.config}"
        engine.db_manager.wipe_all_data(reason)
        out_dir = config.get("report", {}).get("output_dir", ".")
        out_path = Path(out_dir)
        # Best-effort cleanup of reports and heatmaps; ignore missing files.
        for pattern in ("Relatorio_Auditoria_*.xlsx", "heatmap_*.png"):
            for p in out_path.glob(pattern):
                try:
                    p.unlink()
                except OSError:
                    pass
        print("All scan sessions, findings and failures were wiped from SQLite.")
        print(
            "Existing Excel reports and heatmap PNGs under report.output_dir were deleted where possible."
        )
        print(
            "An audit entry was recorded in the data_wipe_log table for transparency."
        )
        return

    # Optional: warn when configured rate limits would block API scans for this config.
    rate_cfg = config.get("rate_limit") or {}
    if rate_cfg.get("enabled"):
        db_path = config.get("sqlite_path", "audit_results.db")
        dbm = LocalDBManager(db_path)
        running = dbm.get_running_sessions_count()
        last = dbm.get_last_session()
        max_concurrent = int(rate_cfg.get("max_concurrent_scans", 1))
        min_interval = int(rate_cfg.get("min_interval_seconds", 0))
        warn_lines: list[str] = []
        if running >= max_concurrent:
            warn_lines.append(
                f"rate_limit: there are already {running} running scan(s); "
                f"max_concurrent_scans={max_concurrent}. API calls would be rate-limited in this state."
            )
        if min_interval > 0 and last and last.get("started_at"):
            from datetime import datetime, timezone

            now = datetime.now(timezone.utc)
            started_at = last["started_at"]
            if isinstance(started_at, datetime):
                if started_at.tzinfo is None:
                    started_at = started_at.replace(tzinfo=timezone.utc)
                else:
                    started_at = started_at.astimezone(timezone.utc)
            else:
                started_at = None
            if started_at is not None and started_at <= now:
                delta = (now - started_at).total_seconds()
                if delta < float(min_interval):
                    warn_lines.append(
                        f"rate_limit: last scan started {int(delta)}s ago; "
                        f"min_interval_seconds={min_interval}. Back-to-back API scans would be rejected "
                        "until the interval elapses."
                    )
        if warn_lines:
            print("[rate_limit] WARNING:")
            for ln in warn_lines:
                print("  - " + ln)
            print(
                "CLI will continue, but consider adjusting rate_limit settings if this is unexpected."
            )

    from core.validation import sanitize_tenant_technician

    tenant = sanitize_tenant_technician(args.tenant)
    technician = sanitize_tenant_technician(args.technician)
    # scan_compressed / use_content_type already merged above when CLI flags were passed
    _install_scan_interrupt_signal_handlers()
    try:
        _emit_runtime_trust_info(runtime_trust, to_stdout=True, to_stderr=True)
        session_id = engine.start_audit(
            tenant_name=tenant,
            technician_name=technician,
            jurisdiction_hint=bool(args.jurisdiction_hint),
        )
        print(f"Scan session: {session_id}")
        report_path = engine.generate_final_reports(session_id)
        if report_path:
            print(f"Report written: {report_path}")
        else:
            print("No findings to report.")
        from core.plugins.hook import maybe_run_remediation_hook

        maybe_run_remediation_hook(config, session_id, db_manager=engine.db_manager)
        from utils.notify import notify_scan_complete_background

        notify_scan_complete_background(engine.config, engine.db_manager, session_id)
    except KeyboardInterrupt:
        _finish_session_interrupted_if_running(engine)
        print("Scan interrupted.", file=sys.stderr)
        sys.exit(130)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print(
            "Probable cause: A target path or file (e.g. DB, report output dir) is missing."
        )
        print(
            "What to do: Ensure paths in config exist; create report.output_dir if needed."
        )
        sys.exit(1)
    except (ConnectionError, OSError) as e:
        print(f"Error: {e}")
        print("Probable cause: Cannot access a resource (DB, disk, network target).")
        print(
            "What to do: Check permissions, disk space, and that no other process locks the DB or files."
        )
        sys.exit(1)
    except ModuleNotFoundError as e:
        print(f"Error: {e}")
        print(
            "Probable cause: An optional dependency (e.g. for 7z or a connector) is not installed."
        )
        print(
            "What to do: Install the optional extra, e.g. uv sync --extra compressed for 7z support."
        )
        sys.exit(1)
    except (ValueError, KeyError) as e:
        print(f"Error: {e}")
        print("Probable cause: Configuration or target definition is invalid.")
        print(
            "What to do: Check config against docs/USAGE.md and ensure all required keys are set."
        )
        sys.exit(1)
    except LicenseBlockedError as e:
        print(f"Licensing: scan blocked ({e.state}).", file=sys.stderr)
        print(str(e), file=sys.stderr)
        print(
            "What to do: Provide a valid license file and verify key (see docs/LICENSING_SPEC.md).",
            file=sys.stderr,
        )
        sys.exit(2)
    except Exception as e:
        from core.licensing.errors import FeatureTierBlockedError

        if isinstance(e, FeatureTierBlockedError):
            print(f"Licensing: {e}", file=sys.stderr)
            sys.exit(2)
        print(f"Error: {e}")
        print("Probable cause: Unexpected failure during scan or report generation.")
        print(
            "What to do: Check logs and config; run with a minimal config to isolate the failing target."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
