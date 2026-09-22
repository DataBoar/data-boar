"""Regression tests for #1332 — sample join false positives and optional Luhn validator."""

from __future__ import annotations

from pathlib import Path

import yaml

from connectors.sample_value_dedup import join_distinct_sample
from core.detector import SensitivityDetector
from core.scanner import DataScanner

_PAN_OVERRIDE_PATTERN = r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"
_LUHN_VALID_TEST_PAN = "4111111111111111"


def _write_pan_override(tmp_path: Path, *, validator: str | None) -> str:
    item: dict[str, str] = {
        "name": "PAN",
        "pattern": _PAN_OVERRIDE_PATTERN,
        "norm_tag": "PCI-DSS",
    }
    if validator:
        item["validator"] = validator
    path = tmp_path / "pan_override.yaml"
    path.write_text(yaml.safe_dump([item]), encoding="utf-8")
    return str(path)


def _has_credit_or_pan(pattern_detected: str | None) -> bool:
    p = pattern_detected or ""
    return "CREDIT_CARD" in p or "PAN" in p


def test_joined_years_ids_last4_not_credit_card_with_pan_override(tmp_path) -> None:
    override = _write_pan_override(tmp_path, validator=None)
    scanner = DataScanner(regex_overrides_path=override)
    fixtures = {
        "Ano": [2020, 2021, 2022, 2023, 2024],
        "id": [1001, 1002, 1003, 1004, 1005],
        "last_four_digits": [1234, 5678, 9012, 3456, 7890],
    }
    for column, values in fixtures.items():
        sample = join_distinct_sample(values, distinct_cap=5)
        result = scanner.scan_column(column, sample)
        assert not _has_credit_or_pan(result.get("pattern_detected")), (
            f"column {column!r} must not look like PAN/CARD after #1332 join fix"
        )


def test_luhn_valid_pan_still_detected_with_validator_override(tmp_path) -> None:
    override = _write_pan_override(tmp_path, validator="luhn")
    scanner = DataScanner(regex_overrides_path=override)
    result = scanner.scan_column("card_number", _LUHN_VALID_TEST_PAN)
    assert "PAN" in (result.get("pattern_detected") or "")


def test_luhn_validator_rejects_form_only_match_on_override(tmp_path) -> None:
    override = _write_pan_override(tmp_path, validator="luhn")
    det = SensitivityDetector(regex_overrides_path=override)
    combined = "2020 2021 2022 2023"
    hits = det._match_regex_patterns(combined)
    assert hits == []


def test_builtin_credit_card_detects_luhn_valid_single_value() -> None:
    scanner = DataScanner()
    result = scanner.scan_column("pan", _LUHN_VALID_TEST_PAN)
    assert "CREDIT_CARD" in (result.get("pattern_detected") or "")
