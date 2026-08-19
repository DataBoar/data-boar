"""Regression guards for the Israel PPL Amendment 13 sample (#1273)."""

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
ISRAEL_SAMPLE = (
    REPO_ROOT / "docs" / "compliance-samples" / "compliance-sample-israel_ppl.yaml"
)
_ALLOWED_PRIORITIES = frozenset({"CRÍTICA", "ALTA", "MÉDIA"})


@pytest.fixture
def israel_scanner():
    from core.scanner import DataScanner

    path = str(ISRAEL_SAMPLE.resolve())
    return DataScanner(regex_overrides_path=path, ml_patterns_path=path)


def test_israel_sample_loads():
    data = yaml.safe_load(ISRAEL_SAMPLE.read_text(encoding="utf-8"))
    assert data["regex"]
    assert data["terms"]
    assert data["recommendation_overrides"]


def test_israel_overrides_use_pt_priorities_and_distinct_tags():
    data = yaml.safe_load(ISRAEL_SAMPLE.read_text(encoding="utf-8"))
    patterns = [row["norm_tag_pattern"] for row in data["recommendation_overrides"]]
    assert "Israel PPL" not in patterns
    assert len(patterns) == len(set(patterns))
    for row in data["recommendation_overrides"]:
        assert row["priority"] in _ALLOWED_PRIORITIES


def test_israel_has_no_nude_nine_digit_or_qs_geo_key():
    text = ISRAEL_SAMPLE.read_text(encoding="utf-8")
    assert r"\d{9}" not in text
    assert r"\d{1,2}" not in text
    forbidden_qs = "lat" + "itude="
    assert forbidden_qs not in text


def test_israel_header_cites_amendment_13_and_in_force():
    text = ISRAEL_SAMPLE.read_text(encoding="utf-8")
    assert "Amendment 13" in text
    assert "14 Aug 2025" in text
    assert "native legal review" in text.lower()


def test_israel_hebrew_inventory_terms_present():
    text = ISRAEL_SAMPLE.read_text(encoding="utf-8")
    for term in (
        "מידע אישי",
        "מידע רגיש מאוד",
        "רשות הגנת הפרטיות",
        "תעודת זהות",
        "מידע רפואי",
        "נתונים ביומטריים",
    ):
        assert term in text


@pytest.mark.parametrize(
    ("column_name", "pattern_name", "art_fragment"),
    [
        ("teudat_zehut", "IL_FIELD_TEUDAT_ZEHUT_LABEL", "identity number"),
        ("mispar_zehut", "IL_FIELD_TEUDAT_ZEHUT_LABEL", "identity number"),
        ("israeli_id", "IL_FIELD_TEUDAT_ZEHUT_LABEL", "identity number"),
        ("medical_record", "IL_FIELD_HEALTH_GENERIC_LABEL", "health"),
        ("biometric_data", "IL_FIELD_BIOMETRIC_LABEL", "biometric"),
        ("genetic_data", "IL_FIELD_GENETIC_LABEL", "genetic"),
    ],
)
def test_israel_contextual_columns(
    israel_scanner, column_name: str, pattern_name: str, art_fragment: str
):
    result = israel_scanner.scan_column(column_name, "")
    assert pattern_name in result["pattern_detected"]
    assert art_fragment in result["norm_tag"]


def test_israel_bare_digits_are_not_identity_number(israel_scanner):
    result = israel_scanner.scan_column("order_id", "123456789")
    detected = result.get("pattern_detected") or ""
    assert "IL_FIELD_TEUDAT_ZEHUT_LABEL" not in detected
    assert "identity number" not in (result.get("norm_tag") or "")
