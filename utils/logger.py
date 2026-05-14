"""
Unified logger: one schema, file (audit_YYYYMMDD.log) + console; optional session_id in format.
On violation: log and print to console immediately so operator is notified on the fly.
"""

import logging
from datetime import datetime, timezone
from typing import Any

from core.validation import sanitize_log_text
from utils.audit_log_display import sanitize_target_name_for_audit_log

_LOGGER: logging.Logger | None = None
_VIOLATION_HANDLER: logging.Handler | None = None


def get_logger(session_id: str | None = None) -> logging.Logger:
    """Return the unified audit logger. Optionally include session_id in extra for formatter."""
    global _LOGGER
    if _LOGGER is None:
        _LOGGER = logging.getLogger("LGPDAudit")
        _LOGGER.setLevel(logging.INFO)
        _LOGGER.handlers.clear()
        log_file = f"audit_{datetime.now(timezone.utc).strftime('%Y%m%d')}.log"
        fh = logging.FileHandler(log_file, encoding="utf-8")
        ch = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        _LOGGER.addHandler(fh)
        _LOGGER.addHandler(ch)
    return _LOGGER


def setup_live_logger() -> logging.Logger:
    """Alias for get_logger(); used by API and existing code."""
    return get_logger()


def log_connection(target_name: str, target_type: str, location: str) -> None:
    """Log successful connection to a database or path."""
    safe_name = sanitize_target_name_for_audit_log(target_name, default="target")
    safe_loc = sanitize_log_text(location)
    get_logger().info("Connected: %s (%s) at %s", safe_name, target_type, safe_loc)


def log_finding(
    source_type: str,
    target_name: str,
    location: str,
    sensitivity: str,
    pattern: str,
) -> None:
    """Log a finding (possible violation). Also notifies operator on console."""
    logger = get_logger()
    safe_name = sanitize_target_name_for_audit_log(target_name, default="target")
    safe_loc = sanitize_log_text(location)
    logger.warning(
        "Finding: %s | %s | %s | %s | %s",
        source_type,
        safe_name,
        safe_loc,
        sensitivity,
        pattern,
    )
    notify_violation(f"{sensitivity} | {pattern} @ {safe_name} / {safe_loc}")


def notify_violation(message: str | dict[str, Any]) -> None:
    """
    Notify operator immediately on console (and log). Use when personal/sensitive data is detected.
    """
    get_logger().warning("VIOLATION: %s", message)
    if isinstance(message, dict):
        import json

        print(
            "[ALERT] Possible personal/sensitive data:",
            json.dumps(message, default=str)[:500],
        )
    else:
        print("[ALERT] Possible personal/sensitive data:", message)
