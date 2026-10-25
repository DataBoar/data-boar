"""Regression guards for the Ethiopia PDPP 1321/2024 sample (#1274)."""

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
ETHIOPIA_SAMPLE = (
    REPO_ROOT / "docs" / "compliance-samples" / "compliance-sample-ethiopia_pdpp.yaml"
)
_ALLOWED_PRIORITIES = frozenset({"CRÍTICA", "ALTA", "MÉDIA"})


@pytest.fixture
def ethiopia_scanner():
    from core.scanner import DataScanner

    path = str(ETHIOPIA_SAMPLE.resolve())
    return DataScanner(regex_overrides_path=path, ml_patterns_path=path)


def test_ethiopia_sample_loads():
    data = yaml.safe_load(ETHIOPIA_SAMPLE.read_text(encoding="utf-8"))
    assert data["regex"]
    assert data["terms"]
    assert data["recommendation_overrides"]


def test_ethiopia_overrides_use_pt_priorities_and_distinct_tags():
    data = yaml.safe_load(ETHIOPIA_SAMPLE.read_text(encoding="utf-8"))
    patterns = [row["norm_tag_pattern"] for row in data["recommendation_overrides"]]
    assert "Ethiopia PDPP" not in patterns
    assert len(patterns) == len(set(patterns))
    for row in data["recommendation_overrides"]:
        assert row["priority"] in _ALLOWED_PRIORITIES


def test_ethiopia_has_no_nude_twelve_digit_or_qs_geo_key():
    text = ETHIOPIA_SAMPLE.read_text(encoding="utf-8")
    assert r"\d{12}" not in text
    forbidden_qs = "lat" + "itude="
    assert forbidden_qs not in text


def test_ethiopia_header_cites_proclamation_and_native_review():
    text = ETHIOPIA_SAMPLE.read_text(encoding="utf-8")
    assert "1321/2024" in text
    assert "24 Jul 2024" in text
    assert "native review" in text.lower()


def test_ethiopia_amharic_draft_terms_present():
    text = ETHIOPIA_SAMPLE.read_text(encoding="utf-8")
    for term in ("የግል መረጃ", "ግላዊነት", "ስምምነት"):
        assert term in text


@pytest.mark.parametrize(
    ("column_name", "pattern_name", "art_fragment"),
    [
        ("fayda_id", "ET_FIELD_FAYDA_LABEL", "Fayda FIN"),
        ("fayda_number", "ET_FIELD_FAYDA_LABEL", "Fayda FIN"),
        ("fin_ethiopia", "ET_FIELD_FAYDA_LABEL", "Fayda FIN"),
        ("biometric_data", "ET_FIELD_BIOMETRIC_LABEL", "biometric"),
        ("medical_record", "ET_FIELD_HEALTH_GENERIC_LABEL", "health"),
    ],
)
def test_ethiopia_contextual_columns(
    ethiopia_scanner, column_name: str, pattern_name: str, art_fragment: str
):
    result = ethiopia_scanner.scan_column(column_name, "")
    assert pattern_name in result["pattern_detected"]
    assert art_fragment in result["norm_tag"]


def test_ethiopia_bare_twelve_digits_are_not_fayda(ethiopia_scanner):
    result = ethiopia_scanner.scan_column("order_id", "123456789012")
    detected = result.get("pattern_detected") or ""
    assert "ET_FIELD_FAYDA_LABEL" not in detected
    assert "Fayda FIN" not in (result.get("norm_tag") or "")
