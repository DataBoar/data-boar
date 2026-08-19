"""Regression guards for the Egypt PDPL Law 151/2020 compliance sample (#1277)."""

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
EGYPT_SAMPLE = (
    REPO_ROOT / "docs" / "compliance-samples" / "compliance-sample-egypt_pdpl.yaml"
)
_ALLOWED_PRIORITIES = frozenset({"CRÍTICA", "ALTA", "MÉDIA"})


@pytest.fixture
def egypt_scanner():
    from core.scanner import DataScanner

    path = str(EGYPT_SAMPLE.resolve())
    return DataScanner(regex_overrides_path=path, ml_patterns_path=path)


def test_egypt_sample_loads():
    data = yaml.safe_load(EGYPT_SAMPLE.read_text(encoding="utf-8"))
    assert data["regex"]
    assert data["terms"]
    assert data["recommendation_overrides"]


def test_egypt_overrides_use_pt_priorities_and_distinct_tags():
    data = yaml.safe_load(EGYPT_SAMPLE.read_text(encoding="utf-8"))
    patterns = [row["norm_tag_pattern"] for row in data["recommendation_overrides"]]
    assert "Egypt PDPL" not in patterns
    assert len(patterns) == len(set(patterns))
    for row in data["recommendation_overrides"]:
        assert row["priority"] in _ALLOWED_PRIORITIES


def test_egypt_has_no_nude_fourteen_digit_or_qs_geo_key():
    text = EGYPT_SAMPLE.read_text(encoding="utf-8")
    assert r"\d{14}" not in text
    forbidden_qs = "lat" + "itude="
    assert forbidden_qs not in text


def test_egypt_header_cites_decree_and_enforcement():
    text = EGYPT_SAMPLE.read_text(encoding="utf-8")
    assert "816/2025" in text
    assert "31 Oct 2026" in text
    assert "151" in text


@pytest.mark.parametrize(
    ("column_name", "pattern_name", "art_fragment"),
    [
        ("egyptian_national_id", "EG_FIELD_NATIONAL_ID_LABEL", "national ID"),
        ("raqm_qawmi", "EG_FIELD_NATIONAL_ID_LABEL", "national ID"),
        ("medical_record", "EG_FIELD_HEALTH_GENERIC_LABEL", "health"),
        ("guardian_consent", "EG_FIELD_CHILD_LABEL", "children"),
        ("electronic_direct_marketing", "EG_FIELD_EDM_LABEL", "marketing"),
    ],
)
def test_egypt_contextual_columns(
    egypt_scanner, column_name: str, pattern_name: str, art_fragment: str
):
    result = egypt_scanner.scan_column(column_name, "")
    assert pattern_name in result["pattern_detected"]
    assert art_fragment in result["norm_tag"]


def test_egypt_bare_digits_are_not_national_id(egypt_scanner):
    result = egypt_scanner.scan_column("order_id", "12345678901234")
    detected = result.get("pattern_detected") or ""
    assert "EG_FIELD_NATIONAL_ID_LABEL" not in detected
    assert "national ID" not in (result.get("norm_tag") or "")
