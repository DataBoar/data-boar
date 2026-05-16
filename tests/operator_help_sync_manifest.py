"""
Lightweight operator-help contract (drift alarm, not full documentation).

When you add a user-visible CLI flag, dashboard toggle, or in-app help callout that
operators should discover from `--help` or `/help`, add or adjust a row below and
update the surfaces listed in `docs/OPERATOR_HELP_AUDIT.md`.

Use ``None`` for a surface that intentionally does not carry that cue (e.g. `uv run`
is documented on `/help` and README, not in argparse text).

Canonical detail stays in docs/USAGE*.md, man pages, and the repo README — this
file only pins a minimal substring set so tests fail if copy disappears.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OperatorHelpMarker:
    """One feature cue checked on operator-facing surfaces (None = skip that surface)."""

    id: str
    cli_help_substring: str | None
    web_help_substring: str | None
    man1_troff_substring: str | None = None
    """
    If set, must appear in `docs/data_boar.1` (troff source).
    Use escapes as stored on disk (e.g. raw ``\\-\\-web`` in the file).
    """


# Troff hyphenated options in data_boar.1 use \- for a literal hyphen in output.
_MAN_WEB = r"\-\-web"
_MAN_HOST = r"\-\-host"
_MAN_PORT = r"\-\-port"
_MAN_CONFIG = r"\-\-config"
_MAN_SCAN_COMPRESSED = r"\-\-scan\-compressed"
_MAN_CONTENT_TYPE = r"\-\-content\-type\-check"
_MAN_SCAN_STEGO = r"\-\-scan\-stego"
_MAN_RESET = r"\-\-reset\-data"
_MAN_EXPORT_AUDIT = r"\-\-export\-audit\-trail"
_MAN_TENANT = r"\-\-tenant"
_MAN_TECH = r"\-\-technician"
_MAN_JURISDICTION_HINT = r"\-\-jurisdiction\-hint"
_MAN_HTTPS_CERT = r"\-\-https\-cert\-file"
_MAN_HTTPS_KEY = r"\-\-https\-key\-file"
_MAN_ALLOW_INSECURE_HTTP = r"\-\-allow\-insecure\-http"

OPERATOR_HELP_MARKERS: tuple[OperatorHelpMarker, ...] = (
    OperatorHelpMarker("config", "--config", "config.yaml", _MAN_CONFIG),
    OperatorHelpMarker("web", "--web", "--web", _MAN_WEB),
    OperatorHelpMarker("host", "--host", "--host", _MAN_HOST),
    OperatorHelpMarker(
        "https_cert_file",
        "--https-cert-file",
        "--https-cert-file",
        _MAN_HTTPS_CERT,
    ),
    OperatorHelpMarker(
        "https_key_file",
        "--https-key-file",
        "--https-key-file",
        _MAN_HTTPS_KEY,
    ),
    OperatorHelpMarker(
        "allow_insecure_http",
        "--allow-insecure-http",
        "--allow-insecure-http",
        _MAN_ALLOW_INSECURE_HTTP,
    ),
    OperatorHelpMarker("port", "--port", "--port", _MAN_PORT),
    OperatorHelpMarker(
        "scan_compressed",
        "--scan-compressed",
        "--scan-compressed",
        _MAN_SCAN_COMPRESSED,
    ),
    OperatorHelpMarker(
        "content_type_check",
        "--content-type-check",
        "--content-type-check",
        _MAN_CONTENT_TYPE,
    ),
    OperatorHelpMarker(
        "scan_stego",
        "--scan-stego",
        "--scan-stego",
        _MAN_SCAN_STEGO,
    ),
    OperatorHelpMarker("reset_data", "--reset-data", "--reset-data", _MAN_RESET),
    OperatorHelpMarker(
        "export_audit_trail",
        "--export-audit-trail",
        "--export-audit-trail",
        _MAN_EXPORT_AUDIT,
    ),
    OperatorHelpMarker("tenant", "--tenant", '--tenant "Acme Corp"', _MAN_TENANT),
    OperatorHelpMarker(
        "technician",
        "--technician",
        '--technician "Alice Colleague-V"',
        _MAN_TECH,
    ),
    OperatorHelpMarker(
        "jurisdiction_hint",
        "--jurisdiction-hint",
        "--jurisdiction-hint",
        _MAN_JURISDICTION_HINT,
    ),
    # Web /help recommends uv; full docs in README — not duplicated in argparse.
    OperatorHelpMarker("uv_run", None, "uv run", None),
    OperatorHelpMarker("api_host_env", "API_HOST", "API_HOST", "API_HOST"),
    OperatorHelpMarker("bind_loopback", "127.0.0.1", "127.0.0.1", "127.0.0.1"),
)


def _validate_markers() -> None:
    for m in OPERATOR_HELP_MARKERS:
        assert m.cli_help_substring or m.web_help_substring, (
            f"marker {m.id!r} must set at least one of cli_help_substring, web_help_substring"
        )


_validate_markers()
