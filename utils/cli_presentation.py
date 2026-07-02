"""Runtime CLI / help presentation for installed (pipx) vs dev entry points."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# dashBOARd /help always shows the packaged command name (not dev ``python main.py``).
DASHBOARD_CLI_PROG = "data-boar"


def _basename_for_argv0(raw: str) -> str:
    """Basename that tolerates Windows-style paths on POSIX runners."""
    if "\\" in raw:
        from pathlib import PureWindowsPath

        return PureWindowsPath(raw).name
    return os.path.basename(raw)


def cli_prog_name(argv0: str | None = None) -> str:
    """
    Command prefix shown in argparse ``prog`` and ``--help``.

    Installed users see ``data-boar``; repo/dev runs see ``python main.py``.
    """
    if argv0 is not None:
        raw = argv0
    elif len(sys.argv) >= 2:
        script = _basename_for_argv0(sys.argv[1])
        interpreter = _basename_for_argv0(sys.argv[0]).lower()
        if script == "main.py" and (
            interpreter.startswith("python") or interpreter in {"py", "py.exe"}
        ):
            return "python main.py"
        raw = sys.argv[0]
    else:
        raw = sys.argv[0] if sys.argv else "main.py"

    stem, _ext = os.path.splitext(_basename_for_argv0(raw))
    if stem.lower() == "data-boar":
        return "data-boar"
    if stem == "main":
        return "python main.py"
    return "python main.py"


def cli_home_example() -> str:
    """Concrete home directory for help copy (not ``~``)."""
    return str(Path.home())


def cli_filesystem_lgpd_example() -> str:
    """Concrete filesystem target path for help/config illustrations."""
    return str(Path.home() / "Documents" / "LGPD")


def cli_help_context(_argv0: str | None = None) -> dict[str, str]:
    """Template context for dashBOARd ``/help`` (installed-user paths only)."""
    return {
        "home_example": cli_home_example(),
        "filesystem_lgpd_example": cli_filesystem_lgpd_example(),
    }


def build_cli_epilog() -> str:
    """Argparse epilog; ``%(prog)s`` is substituted by argparse from ``prog=``."""
    return (
        "Configuration:\n"
        "  - Main config file (YAML or JSON) defines targets (databases, filesystems, APIs, shares),\n"
        "    detection options and report settings. Default is 'config.yaml' in the current directory.\n"
        "  - See docs/USAGE.md for a full schema and examples.\n"
        "\n"
        "CLI examples:\n"
        "  # One-shot audit with the default config.yaml\n"
        "  %(prog)s --config config.yaml\n"
        "\n"
        "  # One-shot audit tagging tenant/customer and technician/operator\n"
        '  %(prog)s --config config.yaml --tenant "ACME Corp" --technician "Alice"\n'
        "\n"
        "  # One-shot with archive scan + content-type detection (this run only)\n"
        "  %(prog)s --config config.yaml --scan-compressed --content-type-check\n"
        "\n"
        "  # Validate config only (loader checks; no scan or API startup)\n"
        "  %(prog)s --config config.yaml --validate-config\n"
        "\n"
        "  # Compare two scan sessions (CI: add --fail-on-new-high)\n"
        "  %(prog)s --config config.yaml --diff <session_a> <session_b>\n"
        "\n"
        "  # DSAR-oriented JSON export for one session (stdout or --dsar-output)\n"
        "  %(prog)s --config config.yaml --export-dsar <session_id>\n"
        "\n"
        "  # Wipe all collected data and generated reports (dangerous, see SECURITY.md)\n"
        "  %(prog)s --config config.yaml --reset-data\n"
        "\n"
        "Web/API examples:\n"
        "  # HTTPS: PEM cert + key (TLS >= 1.2)\n"
        "  %(prog)s --config config.yaml --web --https-cert-file server.crt --https-key-file server.key\n"
        "\n"
        "  # Plaintext HTTP (explicit risk acceptance; required when not using TLS)\n"
        "  %(prog)s --config config.yaml --web --allow-insecure-http\n"
        "\n"
        "  # Explicit port or bind (same flags as before, still need TLS or --allow-insecure-http)\n"
        "  %(prog)s --config config.yaml --web --allow-insecure-http --port 9090\n"
        "  %(prog)s --config config.yaml --web --allow-insecure-http --host 0.0.0.0\n"
        "\n"
        "  # Zero-config demo (synthetic corpus, loopback dashboard — no config.yaml)\n"
        "  %(prog)s --demo\n"
        "\n"
        "Once a one-shot scan finishes, an Excel report and heatmap PNG are written under\n"
        "the configured report.output_dir (default: current directory). When the API is\n"
        "running, you can navigate to the documented endpoints (see README.md) to trigger\n"
        "scans, list sessions and download the latest reports through the browser."
    )
