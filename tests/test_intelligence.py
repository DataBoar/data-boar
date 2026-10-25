"""Tests for ``core.intelligence`` (PII taxonomy and risk density)."""

from __future__ import annotations

import pytest

from core.intelligence import (
    TAXONOMY_WEIGHTS,
    calculate_risk,
    classify_pii_category,
    law_hints_for_pii_findings,
    normalize_pii_type_key,
    regulatory_impact_from_findings,
)


def test_normalize_pii_type_key() -> None:
    assert normalize_pii_type_key("  brazil_cpf  ") == "BRAZIL_CPF"
    assert normalize_pii_type_key("DOB POSSIBLE MINOR") == "DOB_POSSIBLE_MINOR"


def test_calculate_risk_matches_manual_sum() -> None:
    findings = [{"type": "BRAZIL_CPF", "count": 50}]
    assert calculate_risk(findings) == pytest.approx(
        50.0 * TAXONOMY_WEIGHTS["FINANCIAL"]
    )


def test_calculate_risk_default_identifier_weight() -> None:
    findings = [{"type": "MYSTERY_TAG", "count": 3}]
    assert calculate_risk(findings) == pytest.approx(
        3.0 * TAXONOMY_WEIGHTS["IDENTIFIER"]
    )


def test_calculate_risk_skips_non_positive_and_garbage() -> None:
    assert calculate_risk([]) == pytest.approx(0.0)
    assert calculate_risk([{"type": "EMAIL", "count": 0}]) == pytest.approx(0.0)
    assert calculate_risk([{"type": "EMAIL", "count": -1}]) == pytest.approx(0.0)
    assert calculate_risk([{"type": "", "count": 5}]) == pytest.approx(0.0)
    assert calculate_risk([{"count": 5}]) == pytest.approx(0.0)


def test_classify_pii_category_exact_mapping() -> None:
    assert classify_pii_category("EMAIL") == "IDENTIFIER"
    assert classify_pii_category("CREDIT_CARD") == "FINANCIAL"
    assert classify_pii_category("HEALTH_RECORD") == "SENSITIVE"


def test_classify_composite_minor_string() -> None:
    assert classify_pii_category("DOB_POSSIBLE_MINOR, CPF") == "CHILD_DATA"


def test_classify_slice_taxonomy_keys() -> None:
    assert classify_pii_category("BRAZIL_RG") == "IDENTIFIER"
    assert classify_pii_category("PHONE_NUMBER") == "IDENTIFIER"
    assert classify_pii_category("HEALTH_DATA") == "SENSITIVE"
    assert classify_pii_category("RELIGION_INFO") == "SENSITIVE"


def test_law_hints_order_and_dedupe() -> None:
    findings = [
        {"type": "EMAIL", "count": 1},
        {"type": "BRAZIL_CPF", "count": 2},
        {"type": "EMAIL", "count": 3},
    ]
    hints = law_hints_for_pii_findings(findings)
    assert "LGPD Art. 5, I" in hints
    assert "LGPD Art. 7" in hints
    assert hints.index("LGPD Art. 5, I") < hints.index("LGPD Art. 7")
    assert regulatory_impact_from_findings(findings).startswith("LGPD Art. 5, I")
