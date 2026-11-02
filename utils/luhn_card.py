"""Luhn validation for payment-card-shaped digit runs (shared by detector and Pro prefilter)."""

from __future__ import annotations

import re

# IIN-anchored shapes (#1984). Not a bare 13–19 digit run (that reopens #1332 FP).
# Separator class [-\s] includes hyphen, space, TAB, and NBSP.
# 16-digit 4-4-4-4 (Visa/Mastercard/Discover), Amex 15 (3[47], 4-6-5 or run-on),
# Diners 14 (300-305 / 36 / 38, 4-4-4-2 or run-on).
CREDIT_CARD_PATTERN = (
    r"\b(?:"
    r"\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}"
    r"|3[47]\d{2}[-\s]?\d{6}[-\s]?\d{5}"
    r"|3(?:0[0-5]\d|[68]\d{2})[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{2}"
    r")\b"
)
_CARD_CANDIDATE_RX = re.compile(CREDIT_CARD_PATTERN)


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
