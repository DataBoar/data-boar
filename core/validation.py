"""
Input validation helpers for security hardening.

Used for tenant/technician and other operator-supplied values that are stored
or displayed in reports/UI. Keeps values within length limits and strips
control characters to reduce abuse and injection risk.

Log / audit hygiene: ``sanitize_log_text`` and ``clean_error`` mask secrets and
common PII shapes (aligned with ``core.detector.DEFAULT_PATTERNS``) so driver or
HTTP client exceptions cannot leak request bodies, SQL fragments, or customer data
into SQLite or log files.
"""

from __future__ import annotations

import re
from typing import Pattern

# Match DB column size (core.database.ScanSession.tenant_name / technician_name)
MAX_TENANT_TECHNICIAN_LENGTH = 255

# Compiled once: same strong-PII regex families as core.detector.DEFAULT_PATTERNS
# (omit DATE_DMY here — too noisy in generic error text). Keep list in sync when
# adding new built-in high-confidence patterns intended for log redaction.
_PII_LOG_PATTERNS: tuple[Pattern[str], ...] | None = None


def _pii_regexes_for_log() -> tuple[Pattern[str], ...]:
    global _PII_LOG_PATTERNS
    if _PII_LOG_PATTERNS is not None:
        return _PII_LOG_PATTERNS
    raw = (
        r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b",  # LGPD_CPF
        r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b",  # LGPD_CNPJ
        r"\b[A-Z0-9]{2}\.?[A-Z0-9]{3}\.?[A-Z0-9]{3}/?[A-Z0-9]{4}-?\d{2}\b",  # LGPD_CNPJ_ALNUM
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",  # EMAIL
        r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",  # CREDIT_CARD
        r"\b(?:\+55\s?)?(?:\(?\d{2}\)?\s?)?\d{4,5}-?\d{4}\b",  # PHONE_BR
        r"\b\d{3}-\d{2}-\d{4}\b",  # CCPA_SSN
    )
    _PII_LOG_PATTERNS = tuple(re.compile(p, re.IGNORECASE) for p in raw)
    return _PII_LOG_PATTERNS


def sanitize_tenant_technician(
    value: str | None, max_length: int = MAX_TENANT_TECHNICIAN_LENGTH
) -> str | None:
    """
    Sanitize an optional tenant or technician string for storage and display.

    - Strips leading/trailing whitespace.
    - Removes ASCII control characters (ord < 32 and DEL 0x7f) to avoid
      injection or broken rendering in Excel/HTML.
    - Truncates to max_length (default 255, matching DB column) so we never
      overflow the database.

    Returns None if the result is empty after sanitization.
    """
    if value is None:
        return None
    s = value.strip()
    if not s:
        return None
    # Allow only printable / safe chars: drop control chars (0x00-0x1f, 0x7f)
    sanitized = "".join(c for c in s if ord(c) >= 32 and ord(c) != 127)
    sanitized = sanitized.strip()
    if not sanitized:
        return None
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    return sanitized


def redact_secrets_for_log(text: str | None) -> str:
    """
    Return a copy of text safe for logging: mask passwords, API keys, connection URLs
    with credentials, and similar secrets. Used for failure details and any log message
    that might contain config or exception content.
    """
    if not text:
        return ""

    out = text
    # Connection URL with user:password@ (e.g. postgresql://u:secret@host/db)
    out = re.sub(
        r"([a-z][a-z0-9+.-]*://)([^@\s]+)(@[^\s]+)",
        r"\1***REDACTED***\3",
        out,
        flags=re.IGNORECASE,
    )
    # password=, pass=, api_key=, client_secret=, token= (key=value)
    out = re.sub(
        r"(password|pass|api_key|client_secret|token)(\s*=\s*)([^\s&]+)",
        r"\1\2***REDACTED***",
        out,
        flags=re.IGNORECASE,
    )
    return out


def redact_pii_for_log(text: str | None) -> str:
    """
    Mask common personal-data shapes that may appear inside exception strings
    (SQL drivers, httpx response text, etc.). Patterns mirror the built-in
    detector regexes in ``core.detector.DEFAULT_PATTERNS`` (strong PII only).
    """
    if not text:
        return ""
    out = text
    for rx in _pii_regexes_for_log():
        out = rx.sub("***REDACTED***", out)
    return out


def sanitize_log_text(text: str | None) -> str:
    """
    Full pipeline for text persisted to audit SQLite or written to logs:
    secrets/URLs first, then PII-shaped substrings. Prefer this (or
    ``clean_error`` for exceptions) over raw ``str(e)``.
    """
    return redact_pii_for_log(redact_secrets_for_log(text))


def clean_error(exc: BaseException | None, *, max_length: int = 8192) -> str:
    """
    Serialize an exception for logs or ``save_failure`` details: ``str(exc)``
    plus a short ``__cause__`` chain (httpx/SQLAlchemy often wrap the original
    error), then ``sanitize_log_text``. Never pass raw ``str(e)`` to SQLite or
    user-visible error banners if the string may contain response bodies or SQL.
    """
    if exc is None:
        return ""
    parts: list[str] = []
    seen: set[int] = set()
    cur: BaseException | None = exc
    depth = 0
    while cur is not None and depth < 6:
        oid = id(cur)
        if oid in seen:
            break
        seen.add(oid)
        parts.append(str(cur))
        cur = cur.__cause__
        depth += 1
    merged = " | ".join(parts)
    return sanitize_log_text(merged)[: max(1, max_length)]
