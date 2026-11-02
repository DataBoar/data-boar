"""Detector #1984 — IIN-anchored Amex/Diners plus existing 16-digit CREDIT_CARD."""

from __future__ import annotations

from core.scanner import DataScanner
from utils.luhn_card import CREDIT_CARD_PATTERN, text_contains_luhn_valid_card

# Public test PANs (Luhn-valid).
_AMEX = "378282246310005"
_AMEX_SPACED = "3782 822463 10005"
_DINERS = "30569309025904"
_DINERS_SPACED = "3056 9309 0259 04"
_VISA = "4111111111111111"
_AMEX_BAD_LUHN = "378282246310006"


def _credit_card_in_pattern(pattern_detected: str | None) -> bool:
    return "CREDIT_CARD" in (pattern_detected or "")


def test_amex_pan_free_text_detects_credit_card() -> None:
    scanner = DataScanner()
    result = scanner.scan_column("notes", _AMEX_SPACED)
    assert _credit_card_in_pattern(result.get("pattern_detected"))


def test_amex_pan_run_on_detects_credit_card() -> None:
    scanner = DataScanner()
    result = scanner.scan_column("notes", _AMEX)
    assert _credit_card_in_pattern(result.get("pattern_detected"))


def test_diners_pan_free_text_detects_credit_card() -> None:
    scanner = DataScanner()
    result = scanner.scan_column("notes", _DINERS_SPACED)
    assert _credit_card_in_pattern(result.get("pattern_detected"))


def test_diners_pan_run_on_detects_credit_card() -> None:
    scanner = DataScanner()
    result = scanner.scan_column("notes", _DINERS)
    assert _credit_card_in_pattern(result.get("pattern_detected"))


def test_visa_tab_nbsp_still_detected() -> None:
    scanner = DataScanner()
    tab = scanner.scan_column("card_number", "4111\t1111\t1111\t1111")
    nbsp = scanner.scan_column("card_number", "4111\u00a01111\u00a01111\u00a01111")
    assert _credit_card_in_pattern(tab.get("pattern_detected"))
    assert _credit_card_in_pattern(nbsp.get("pattern_detected"))


def test_luhn_invalid_amex_rejected() -> None:
    scanner = DataScanner()
    result = scanner.scan_column("notes", _AMEX_BAD_LUHN)
    assert not _credit_card_in_pattern(result.get("pattern_detected"))
    assert not text_contains_luhn_valid_card(_AMEX_BAD_LUHN)


def test_long_non_card_digit_run_not_credit_card() -> None:
    scanner = DataScanner()
    result = scanner.scan_column("notes", "id 12345678901234567890")
    assert not _credit_card_in_pattern(result.get("pattern_detected"))


def test_timestamp_digits_not_credit_card() -> None:
    scanner = DataScanner()
    result = scanner.scan_column("notes", "ts 20231102153000")
    assert not _credit_card_in_pattern(result.get("pattern_detected"))


def test_builtin_pattern_is_iin_ssot() -> None:
    from core.detector import DEFAULT_PATTERNS

    assert DEFAULT_PATTERNS["CREDIT_CARD"][0] == CREDIT_CARD_PATTERN
    assert r"{13,19}" not in CREDIT_CARD_PATTERN
