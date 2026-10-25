"""Tests for ``report.grc_risk_taxonomy`` (LGPD-aligned density weights)."""

from __future__ import annotations

import pytest

from report.grc_risk_taxonomy import (
    compute_asset_risk_density,
    dominant_taxonomy_from_lines,
    map_pii_type_to_taxonomy,
)


@pytest.mark.parametrize(
    ("type_str", "expected"),
    [
        ("EMAIL", "identificadores"),
        ("WORK_EMAIL", "identificadores"),
        ("CPF", "financeiros_gov"),
        ("LGPD_CPF", "financeiros_gov"),
        ("BRAZIL_CPF", "financeiros_gov"),
        ("CREDIT_CARD", "financeiros_gov"),
        ("DOB_POSSIBLE_MINOR", "infantil"),
        ("DOB_POSSIBLE_MINOR, CPF", "infantil"),
        ("HEALTH_RECORD", "sensitive"),
        ("CID_10", "sensitive"),
        ("MYSTERY", "identificadores"),
    ],
)
def test_map_pii_type_to_taxonomy(type_str: str, expected: str) -> None:
    assert map_pii_type_to_taxonomy(type_str) == expected


def test_density_raw_sum_matches_formula() -> None:
    # 2 * 10 (EMAIL) + 1 * 30 (CPF) = 50
    rows = [{"type": "EMAIL", "count": 2}, {"type": "CPF", "count": 1}]
    score, raw, breakdown, dominant = compute_asset_risk_density(rows, cap_raw=2500.0)
    assert raw == pytest.approx(50.0)
    assert score == pytest.approx(2.0)
    assert dominant == "financeiros_gov"
    assert len(breakdown) == 2
    assert breakdown[0]["line_score"] == pytest.approx(20.0)
    assert breakdown[1]["line_score"] == pytest.approx(30.0)


def test_density_caps_at_100() -> None:
    rows = [{"type": "HEALTH", "count": 100}]
    score, raw, _, dominant = compute_asset_risk_density(rows, cap_raw=2500.0)
    assert raw == pytest.approx(8000.0)
    assert score == pytest.approx(100.0)
    assert dominant == "sensitive"


def test_dominant_taxonomy_prefers_infantil_over_financeiros() -> None:
    lines = [
        {"taxonomy": "financeiros_gov", "line_score": 300.0},
        {"taxonomy": "infantil", "line_score": 100.0},
    ]
    assert dominant_taxonomy_from_lines(lines) == "infantil"


def test_dominant_ignores_zero_lines() -> None:
    lines = [
        {"taxonomy": "sensitive", "line_score": 0.0},
        {"taxonomy": "identificadores", "line_score": 10.0},
    ]
    assert dominant_taxonomy_from_lines(lines) == "identificadores"
