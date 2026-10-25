"""
Unified logger: one schema, file (audit_YYYYMMDD.log) + console; optional session_id in format.
On violation: log and print to console immediately so operator is notified on the fly.
"""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.validation import clean_error, sanitize_log_text
from utils.audit_log_display import sanitize_target_name_for_audit_log

_LOGGER: logging.Logger | None = None
_VIOLATION_HANDLER: logging.Handler | None = None
_AUDIT_LOG_DIR: Path | None = None

# Choke-point filter name (#1722 / ADR-0036). Must stay on the logger, not only
# on individual handlers, so every sink (file, console, pytest caplog) is covered.
SANITIZE_LOG_FILTER_NAME = "data_boar_sanitize_log_text"


class SanitizeLogFilter(logging.Filter):
    """Redact secrets/PII in log records before any handler emits them (#1722)."""

    def __init__(self) -> None:
        super().__init__(name=SANITIZE_LOG_FILTER_NAME)

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = _sanitize_log_arg(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: _sanitize_log_arg(v) for k, v in record.args.items()}
            else:
                record.args = tuple(_sanitize_log_arg(a) for a in record.args)
        _sanitize_record_traceback(record)
        return True


_PASSTHROUGH_LOG_ARGS = (int, float, bool, type(None))


def _sanitize_log_arg(value: Any) -> Any:
    """Redact secrets in any log operand, not only ``str`` (#1722 HIGH)."""
    if isinstance(value, BaseException):
        return clean_error(value)
    if isinstance(value, memoryview):
        value = value.tobytes()
    if isinstance(value, (bytes, bytearray)):
        return sanitize_log_text(bytes(value).decode("utf-8", errors="replace"))
    if isinstance(value, str):
        return sanitize_log_text(value)
    if isinstance(value, _PASSTHROUGH_LOG_ARGS):
        return value
    return sanitize_log_text(str(value))


def _sanitize_record_traceback(record: logging.LogRecord) -> None:
    """Sanitize ``exc_info`` / ``exc_text`` / ``stack_info`` before formatters run."""
    if record.exc_info:
        if not record.exc_text:
            record.exc_text = logging.Formatter().formatException(record.exc_info)
        # Drop unsanitized tuple so a later formatException cannot replay secrets.
        record.exc_info = None
    if record.exc_text:
        record.exc_text = sanitize_log_text(record.exc_text)
    stack_info = getattr(record, "stack_info", None)
    if isinstance(stack_info, str) and stack_info:
        record.stack_info = sanitize_log_text(stack_info)


def _ensure_sanitize_filter(logger: logging.Logger) -> None:
    if any(
        getattr(f, "name", None) == SANITIZE_LOG_FILTER_NAME for f in logger.filters
    ):
        return
    logger.addFilter(SanitizeLogFilter())


def configure_audit_log_directory(log_dir: str | Path | None) -> None:
    """
    Configure the directory used by the unified audit logger.

    Passing ``None`` restores default behaviour (current working directory).
    Reconfiguring resets handlers so subsequent writes use the new destination.
    """
    global _LOGGER, _AUDIT_LOG_DIR
    resolved: Path | None = None
    if log_dir is not None:
        raw = Path(str(log_dir).strip())
        if str(raw):
            resolved = raw.resolve()
    if resolved == _AUDIT_LOG_DIR:
        return
    _AUDIT_LOG_DIR = resolved
    if _LOGGER is not None:
        for handler in list(_LOGGER.handlers):
            try:
                handler.close()
            finally:
                _LOGGER.removeHandler(handler)
        _LOGGER = None


def get_logger(session_id: str | None = None) -> logging.Logger:
    """Return the unified audit logger. ``SanitizeLogFilter`` is always attached (#1722)."""
    global _LOGGER
    if _LOGGER is None:
        _LOGGER = logging.getLogger("LGPDAudit")
        _LOGGER.setLevel(logging.INFO)
        _LOGGER.handlers.clear()
        log_name = f"audit_{datetime.now(timezone.utc).strftime('%Y%m%d')}.log"
        log_file = (
            _AUDIT_LOG_DIR / log_name if _AUDIT_LOG_DIR is not None else Path(log_name)
        )
        if _AUDIT_LOG_DIR is not None:
            _AUDIT_LOG_DIR.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file, encoding="utf-8")
        ch = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        _LOGGER.addHandler(fh)
        _LOGGER.addHandler(ch)
        _ensure_sanitize_filter(_LOGGER)
    else:
        _ensure_sanitize_filter(_LOGGER)
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


def log_audit_trail_finding(categories: dict[str, int]) -> None:
    """
    Record an Audit Trail taxonomy finding from audit-log PII self-scan (#877).

    Logs category names and counts only — never matched cleartext or log excerpts.
    """
    if not categories:
        return
    parts = ",".join(f"{name}:{count}" for name, count in sorted(categories.items()))
    get_logger().warning(
        "AuditTrailFinding: taxonomy=Audit Trail | log_self_scan_pii | categories=%s",
        parts,
    )


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
