"""Detector gap #1984 — Amex/Diners Luhn-valid PANs not matched by CREDIT_CARD regex."""

from __future__ import annotations

import pytest

from core.scanner import DataScanner


def _credit_card_in_pattern(pattern_detected: str | None) -> bool:
    return "CREDIT_CARD" in (pattern_detected or "")


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="1984 — Amex 15-digit PAN not matched by CREDIT_CARD regex yet",
)
def test_amex_pan_free_text_should_detect_credit_card() -> None:
    scanner = DataScanner()
    result = scanner.scan_column("notes", "3782 822463 10005")
    assert _credit_card_in_pattern(result.get("pattern_detected"))


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="1984 — Diners 14-digit PAN not matched by CREDIT_CARD regex yet",
)
def test_diners_pan_free_text_should_detect_credit_card() -> None:
    scanner = DataScanner()
    result = scanner.scan_column("notes", "3056 9309 0259 04")
    assert _credit_card_in_pattern(result.get("pattern_detected"))
