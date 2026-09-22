"""Luhn validation for payment-card-shaped digit runs (shared by detector and Pro prefilter)."""

from __future__ import annotations

import re

# Fallback scan when no detector match span is available (e.g. Pro prefilter).
# Align separator class with CREDIT_CARD detection: optional whitespace or hyphen.
_CARD_CANDIDATE_RX = re.compile(r"\b(?:\d[-\s]?){13,19}\b")


def check_luhn(card_number: str) -> bool:
    digits = [int(ch) for ch in card_number if ch.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    total = 0
    for idx, digit in enumerate(reversed(digits)):
        if idx % 2 == 1:
            doubled = digit * 2
            total += doubled - 9 if doubled > 9 else doubled
        else:
            total += digit
    return total % 10 == 0


def luhn_check_matched_card_span(matched_span: str) -> bool:
    """Run Luhn on digits extracted from a regex match span (no re-scan with a narrower pattern)."""
    return check_luhn(matched_span)


def text_contains_luhn_valid_card(value: str) -> bool:
    return any(
        luhn_check_matched_card_span(m.group(0))
        for m in _CARD_CANDIDATE_RX.finditer(value)
    )
