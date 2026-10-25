"""Regression guards for the Germany BDSG compliance sample (#1498)."""

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
BDSG_SAMPLE = (
    REPO_ROOT / "docs" / "compliance-samples" / "compliance-sample-germany_bdsg.yaml"
)
_ALLOWED_PRIORITIES = frozenset({"CRÍTICA", "ALTA", "MÉDIA"})


@pytest.fixture
def bdsg_scanner():
    from core.scanner import DataScanner

    path = str(BDSG_SAMPLE.resolve())
    return DataScanner(regex_overrides_path=path, ml_patterns_path=path)


def test_bdsg_sample_loads():
    data = yaml.safe_load(BDSG_SAMPLE.read_text(encoding="utf-8"))
    assert data["regex"]
    assert data["terms"]
    assert data["recommendation_overrides"]


def test_bdsg_overrides_use_pt_priorities_and_distinct_tags():
    data = yaml.safe_load(BDSG_SAMPLE.read_text(encoding="utf-8"))
    patterns = [row["norm_tag_pattern"] for row in data["recommendation_overrides"]]
    assert "Germany" not in patterns
    assert "BDSG" not in patterns
    assert len(patterns) == len(set(patterns))
    for row in data["recommendation_overrides"]:
        assert row["priority"] in _ALLOWED_PRIORITIES


def test_bdsg_has_no_nude_eleven_digit_or_qs_geo_key():
    text = BDSG_SAMPLE.read_text(encoding="utf-8")
    assert r"\d{11}" not in text
    assert r"[1-9]\d{10}" not in text
    forbidden_qs = "lat" + "itude="
    assert forbidden_qs not in text


def test_bdsg_header_flags_section26_as_contested():
    text = BDSG_SAMPLE.read_text(encoding="utf-8")
    assert "C-34/21" in text
    assert "contested" in text.lower() or "CONTESTED" in text
    assert "inapplicable" in text.lower() or "not meet" in text.lower()


@pytest.mark.parametrize(
    ("column_name", "pattern_name", "art_fragment"),
    [
        ("steuer_id", "DE_FIELD_STEUER_ID_LABEL", "Steuer-ID"),
        ("mitarbeiterdaten", "DE_FIELD_EMPLOYEE_LABEL", "§26"),
        ("beschaeftigtendaten", "DE_FIELD_EMPLOYEE_LABEL", "contested"),
        ("gesichtserkennung", "DE_FIELD_BIOMETRIC_LABEL", "biometrics"),
        ("bonitaetspruefung", "DE_FIELD_SCORING_LABEL", "§31"),
    ],
)
def test_bdsg_contextual_columns(
    bdsg_scanner, column_name: str, pattern_name: str, art_fragment: str
):
    result = bdsg_scanner.scan_column(column_name, "")
    assert pattern_name in result["pattern_detected"]
    assert art_fragment in result["norm_tag"]


def test_bdsg_compound_column_fires_employee_and_biometric(bdsg_scanner):
    result = bdsg_scanner.scan_column("mitarbeiterdaten_gesichtserkennung", "")
    detected = result.get("pattern_detected") or ""
    assert "DE_FIELD_EMPLOYEE_LABEL" in detected
    assert "DE_FIELD_BIOMETRIC_LABEL" in detected


def test_bdsg_compound_employee_biometric_keeps_art9_first():
    """Joined norm_tag must not let §26 steal the Art. 9 override (list order)."""
    data = yaml.safe_load(BDSG_SAMPLE.read_text(encoding="utf-8"))
    patterns = [row["norm_tag_pattern"] for row in data["recommendation_overrides"]]
    assert patterns.index("BDSG + GDPR Art. 9 (biometrics)") < patterns.index(
        "BDSG §26 (Beschäftigtendaten — contested)"
    )


def test_bdsg_bare_digits_are_not_steuer_id(bdsg_scanner):
    result = bdsg_scanner.scan_column("order_id", "12345678901")
    detected = result.get("pattern_detected") or ""
    assert "DE_FIELD_STEUER_ID_LABEL" not in detected
    assert "Steuer-ID" not in (result.get("norm_tag") or "")
