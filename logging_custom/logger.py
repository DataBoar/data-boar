# logging_custom/logger.py – backward compatibility: re-export from utils.logger.
# Prefer: from utils.logger import get_logger, log_finding, notify_violation

from utils.logger import get_logger, notify_violation as _notify_violation


def setup_logging(log_config):
    """Delegate to unified logger; set level from log_config (e.g. log_level)."""
    logger = get_logger()
    level = (log_config or {}).get("log_level", "INFO")
    logger.setLevel(getattr(__import__("logging"), level))
    return logger


def notify_violation(data):
    """Notify operator (console + log). For email, integrate separately."""
    _notify_violation(data)
