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

    return f"Data Boar {_package_version()}"


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

        kind = target.get("type", "?")
        driver = target.get("driver", "")
        label = f"type={kind}" + (f" driver={driver}" if driver else "")
        print(f'  OK    target[{i}] "{name}"  {label}')

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


def main() -> None:
    parser = argparse.ArgumentParser(
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
            "  python main.py --config config.yaml\n"
            "\n"
            "  # One-shot audit tagging tenant/customer and technician/operator\n"
            '  python main.py --config config.yaml --tenant "ACME Corp" --technician "Alice"\n'
            "\n"
            "  # One-shot with archive scan + content-type detection (this run only)\n"
            "  python main.py --config config.yaml --scan-compressed --content-type-check\n"
            "\n"
            "  # Validate config only (loader checks; no scan or API startup)\n"
            "  python main.py --config config.yaml --validate-config\n"
            "\n"
            "  # Compare two scan sessions (CI: add --fail-on-new-high)\n"
            "  python main.py --config config.yaml --diff <session_a> <session_b>\n"
            "\n"
            "  # DSAR-oriented JSON export for one session (stdout or --dsar-output)\n"
            "  python main.py --config config.yaml --export-dsar <session_id>\n"
            "\n"
            "  # Wipe all collected data and generated reports (dangerous, see SECURITY.md)\n"
            "  python main.py --config config.yaml --reset-data\n"
            "\n"
            "Web/API examples:\n"
            "  # HTTPS: PEM cert + key (TLS >= 1.2)\n"
            "  python main.py --config config.yaml --web --https-cert-file server.crt --https-key-file server.key\n"
            "\n"
            "  # Plaintext HTTP (explicit risk acceptance; required when not using TLS)\n"
            "  python main.py --config config.yaml --web --allow-insecure-http\n"
            "\n"
            "  # Explicit port or bind (same flags as before, still need TLS or --allow-insecure-http)\n"
            "  python main.py --config config.yaml --web --allow-insecure-http --port 9090\n"
            "  python main.py --config config.yaml --web --allow-insecure-http --host 0.0.0.0\n"
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
        action="version",
        version=_cli_public_version_line(),
        help="Show the public product version and exit (no scan or API startup).",
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
            "warn on unset *_from_env vars. No connections, scan, or --web. "
            "Exit 0 when valid, 1 on errors. Incompatible with --web, --reset-data, "
            "and --export-audit-trail."
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
    args = parser.parse_args()

    if args.validate_config and (
        args.web
        or args.reset_data
        or args.export_audit_trail is not None
        or args.export_dsar is not None
    ):
        print(
            "Cannot combine --validate-config with --web, --reset-data, "
            "--export-audit-trail, or --export-dsar.",
            file=sys.stderr,
        )
        sys.exit(2)

    if args.diff_sessions and (
        args.web
        or args.reset_data
        or args.export_audit_trail is not None
        or args.validate_config
        or args.export_dsar is not None
    ):
        print(
            "Cannot combine --diff with --web, --reset-data, --export-audit-trail, "
            "--export-dsar, or --validate-config.",
            file=sys.stderr,
        )
        sys.exit(2)

    if args.export_dsar is not None and (
        args.web
        or args.reset_data
        or args.export_audit_trail is not None
        or args.validate_config
        or args.diff_sessions
    ):
        print(
            "Cannot combine --export-dsar with --web, --reset-data, "
            "--export-audit-trail, --validate-config, or --diff.",
            file=sys.stderr,
        )
        sys.exit(2)

    if args.dsar_output and args.export_dsar is None:
        print("--dsar-output requires --export-dsar.", file=sys.stderr)
        sys.exit(2)

    if args.dsar_include_samples and args.export_dsar is None:
        print("--dsar-include-samples requires --export-dsar.", file=sys.stderr)
        sys.exit(2)

    try:
        config = load_config(args.config)
    except FileNotFoundError as e:
        print(f"Config not found: {e}")
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
        _validate_config_and_exit(config, args.config)

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

    # #856 (Phase E): integrity anchor first-run validation / startup re-verify.
    # Runs in ANY licensing mode (including open); fail-soft (state=unknown).
    from core.integrity_anchor import ALPHA_NOTE, ensure_integrity_anchor

    _integrity = ensure_integrity_anchor(config)
    if _integrity.get("integrity_state") == "tampered":
        print(
            "*** INTEGRITY: behaviour-critical modules diverge from the "
            f"validated anchor — runtime self-marked -alpha ({ALPHA_NOTE}). "
            f"Mismatched: {', '.join(_integrity.get('mismatched_files', []))} ***",
            file=sys.stderr,
        )

    runtime_trust = get_runtime_trust_snapshot(config)

    if args.export_dsar is not None:
        _emit_runtime_trust_info(runtime_trust, to_stdout=False, to_stderr=True)
        from core.dsar_export import build_dsar_payload

        engine = AuditEngine(config)
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

        engine = AuditEngine(config)
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
            should_warn_insecure_api_bind,
        )

        api_cfg = config.get("api", {})
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
        else:
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
            ssl_ctx = None

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
            uvicorn_kwargs["ssl"] = ssl_ctx
        uvicorn.run(app, **uvicorn_kwargs)
        return

    engine = AuditEngine(config)

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
        from utils.notify import notify_scan_complete_background

        notify_scan_complete_background(engine.config, engine.db_manager, session_id)
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
        print(f"Error: {e}")
        print("Probable cause: Unexpected failure during scan or report generation.")
        print(
            "What to do: Check logs and config; run with a minimal config to isolate the failing target."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
