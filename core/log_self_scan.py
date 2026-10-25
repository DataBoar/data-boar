"""
Second-layer PII self-scan for audit log export (#877).

Reuses ``core.detector.DEFAULT_PATTERNS`` (same regex families as the scanner),
except ``DATE_DMY`` (omitted per ADR-0036 log-redaction policy — too noisy).
Returns category counts only — never matched cleartext (issue #877 AC).
"""

from __future__ import annotations

import re
from functools import lru_cache

from core.detector import DEFAULT_PATTERNS


@lru_cache(maxsize=1)
def _compiled_default_patterns() -> tuple[tuple[str, re.Pattern[str]], ...]:
    # Align with ADR-0036 / core.validation redact_pii_for_log: omit DATE_DMY (too noisy).
    return tuple(
        (name, re.compile(pattern, re.IGNORECASE))
        for name, (pattern, _norm) in DEFAULT_PATTERNS.items()
        if name != "DATE_DMY"
    )


def scan_text_for_pii(text: str) -> dict[str, int]:
    """
    Scan *text* with built-in DEFAULT_PATTERNS regexes.

    Returns ``{category: match_count}`` for categories with at least one match.
    Never includes matched substrings — counts only.
    """
    if not text:
        return {}
    counts: dict[str, int] = {}
    for name, compiled in _compiled_default_patterns():
        n = len(compiled.findall(text))
        if n:
            counts[name] = n
    return counts
