#!/usr/bin/env python3
"""
Post a manual operator message using the configured notifications block (Part A: off-band).

Requires notifications.enabled: true and at least one operator channel in config.

By default, successful/failed sends are also recorded in ``notification_send_log`` when the
SQLite file at ``sqlite_path`` can be opened (same path semantics as the main engine:
relative paths resolve against **current working directory**). Use ``--no-audit`` to skip
the database (e.g. CI without a local DB). Respects ``notifications.notify_audit_log``.

Usage (from repo root):

  uv run python scripts/notify_webhook.py "Build green on main"
  echo "Release cut" | uv run python scripts/notify_webhook.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from config.loader import load_config  # noqa: E402
from core.database import LocalDBManager  # noqa: E402
from utils.notify import send_manual_operator_message  # noqa: E402


def _resolve_sqlite_path(cfg: dict[str, Any]) -> str:
    """
    Match :class:`core.engine.AuditEngine`: ``sqlite_path`` from config, default
    ``audit_results.db``; relative paths are relative to **process CWD** (not the config file).
    """
    raw = (
        str(cfg.get("sqlite_path") or "audit_results.db").strip() or "audit_results.db"
    )
    p = Path(raw).expanduser()
    if p.is_absolute():
        return str(p)
    return str(Path.cwd() / p)


def _try_local_db_manager(cfg: dict[str, Any]) -> LocalDBManager | None:
    """Return a manager for audit rows, or None if the DB cannot be opened."""
    try:
        return LocalDBManager(_resolve_sqlite_path(cfg))
    except OSError as e:
        print(
            f"Note: notification audit log skipped (could not open sqlite_path): {e}",
            file=sys.stderr,
        )
        return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Send a one-off message via configured operator webhook(s)."
    )
    parser.add_argument(
        "message",
        nargs="?",
        default="",
        help="Message text (default: read stdin)",
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to YAML/JSON config",
    )
    parser.add_argument(
        "--no-audit",
        action="store_true",
        help="Do not write to notification_send_log (no LocalDBManager)",
    )
    args = parser.parse_args()
    text = (args.message or "").strip()
    if not text:
        text = sys.stdin.read()
    text = text.strip()
    if not text:
        print("No message text.", file=sys.stderr)
        sys.exit(2)
    try:
        cfg = load_config(args.config)
    except Exception as e:
        print(f"Config error: {e}", file=sys.stderr)
        sys.exit(1)
    db_manager: LocalDBManager | None = None
    if not args.no_audit:
        db_manager = _try_local_db_manager(cfg)
    _ch, ok, err = send_manual_operator_message(cfg, text, db_manager=db_manager)
    if ok:
        print("Notification sent.")
        sys.exit(0)
    print(f"Not sent: {err}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
