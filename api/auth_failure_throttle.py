"""In-memory throttle for API-key authentication failures (#2078)."""

from __future__ import annotations

import hmac
import threading
import time
from collections import deque

DEFAULT_MAX_FAILURES = 5
DEFAULT_WINDOW_SECONDS = 60

_lock = threading.Lock()
_failures: dict[str, deque[float]] = {}


def reset_auth_failure_throttle() -> None:
    """Drop counters. Tests call this so one case cannot fill the window."""
    with _lock:
        _failures.clear()


def auth_failure_limits(api_cfg: dict) -> tuple[int, int] | None:
    """Return ``(max_failures, window_seconds)``, or None when disabled."""
    raw = api_cfg.get("auth_failure_throttle")
    block = raw if isinstance(raw, dict) else {}
    if block.get("enabled") is False:
        return None
    try:
        limit = int(block.get("max_failures", DEFAULT_MAX_FAILURES))
        window = int(block.get("window_seconds", DEFAULT_WINDOW_SECONDS))
    except (TypeError, ValueError):
        limit, window = DEFAULT_MAX_FAILURES, DEFAULT_WINDOW_SECONDS
    return max(1, limit), max(1, window)


def _prune_bucket(source: str, now: float, window_seconds: int) -> deque[float]:
    """Drop expired failures and remove an empty bucket so the dict cannot grow."""
    bucket = _failures.get(source)
    if bucket is None:
        return deque()
    cutoff = now - window_seconds
    while bucket and bucket[0] <= cutoff:
        bucket.popleft()
    if not bucket:
        _failures.pop(source, None)
        return deque()
    return bucket


def _compare_key(provided: str, expected: str) -> bool:
    """True when both values match. A non-text value is a mismatch, not an error."""
    try:
        return bool(provided) and hmac.compare_digest(
            provided.encode("utf-8"), expected.encode("utf-8")
        )
    except (TypeError, UnicodeError):
        return False


def _record_failure(source: str, now: float) -> None:
    """Remember one failed attempt for this source."""
    _failures.setdefault(source, deque()).append(now)


def decide_auth_attempt(
    source: str,
    limit: int,
    window_seconds: int,
    *,
    provided: str,
    expected: str,
    cookie_ok: bool,
) -> tuple[str, int]:
    """Compare under the lock. Return outcome and Retry-After seconds."""
    now = time.monotonic()
    with _lock:
        bucket = _prune_bucket(source, now, window_seconds)
        if cookie_ok and not provided:
            return "cookie", 0
        if len(bucket) >= limit:
            retry = max(1, int(window_seconds - (now - bucket[0])))
            return "limited", retry
        if _compare_key(provided, expected):
            return "ok", 0
        if cookie_ok:
            return "cookie", 0
        _record_failure(source, now)
        return "invalid", 0
