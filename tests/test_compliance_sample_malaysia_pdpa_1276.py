"""Regression guards for the Malaysia PDPA Amendment 2024 sample (#1276)."""

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
MALAYSIA_SAMPLE = (
    REPO_ROOT / "docs" / "compliance-samples" / "compliance-sample-malaysia_pdpa.yaml"
)
_ALLOWED_PRIORITIES = frozenset({"CRÍTICA", "ALTA", "MÉDIA"})


@pytest.fixture
def malaysia_scanner():
    from core.scanner import DataScanner

    path = str(MALAYSIA_SAMPLE.resolve())
    return DataScanner(regex_overrides_path=path, ml_patterns_path=path)


def test_malaysia_sample_loads():
    data = yaml.safe_load(MALAYSIA_SAMPLE.read_text(encoding="utf-8"))
    assert data["regex"]
    assert data["terms"]
    assert data["recommendation_overrides"]


def test_malaysia_overrides_use_pt_priorities_and_distinct_tags():
    data = yaml.safe_load(MALAYSIA_SAMPLE.read_text(encoding="utf-8"))
    patterns = [row["norm_tag_pattern"] for row in data["recommendation_overrides"]]
    assert "Malaysia PDPA" not in patterns
    assert len(patterns) == len(set(patterns))
    for row in data["recommendation_overrides"]:
        assert row["priority"] in _ALLOWED_PRIORITIES


def test_malaysia_has_no_nude_twelve_digit_or_qs_geo_key():
    text = MALAYSIA_SAMPLE.read_text(encoding="utf-8")
    assert r"\d{12}" not in text
    forbidden_qs = "lat" + "itude="
    assert forbidden_qs not in text


def test_malaysia_header_cites_amendment_and_phases():
    text = MALAYSIA_SAMPLE.read_text(encoding="utf-8")
    assert "A1727" in text
    assert "1 Jan" in text or "1 January" in text
    assert "1 Jun" in text or "1 June" in text


@pytest.mark.parametrize(
    ("column_name", "pattern_name", "art_fragment"),
    [
        ("mykad", "MY_FIELD_MYKAD_LABEL", "MyKad"),
        ("nric_my", "MY_FIELD_MYKAD_LABEL", "MyKad"),
        ("malaysia_ic", "MY_FIELD_MYKAD_LABEL", "MyKad"),
        ("medical_record", "MY_FIELD_HEALTH_GENERIC_LABEL", "health"),
        ("biometric_data", "MY_FIELD_BIOMETRIC_LABEL", "biometric"),
    ],
)
def test_malaysia_contextual_columns(
    malaysia_scanner, column_name: str, pattern_name: str, art_fragment: str
):
    result = malaysia_scanner.scan_column(column_name, "")
    assert pattern_name in result["pattern_detected"]
    assert art_fragment in result["norm_tag"]


def test_malaysia_formatted_mykad_value(malaysia_scanner):
    result = malaysia_scanner.scan_column("customer_ref", "900101-14-5678")
    assert "MY_MYKAD_FORMATTED" in result["pattern_detected"]
    assert "MyKad" in result["norm_tag"]


def test_malaysia_bare_twelve_digits_are_not_mykad(malaysia_scanner):
    result = malaysia_scanner.scan_column("order_id", "900101145678")
    detected = result.get("pattern_detected") or ""
    assert "MY_MYKAD_FORMATTED" not in detected
    assert "MY_FIELD_MYKAD_LABEL" not in detected
