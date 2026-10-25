"""Regression guards for the Pakistan PDPA Bill 2023 compliance sample (#475)."""

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
PDPA_SAMPLE = (
    REPO_ROOT / "docs" / "compliance-samples" / "compliance-sample-pakistan_pdpa.yaml"
)
_ALLOWED_PRIORITIES = frozenset({"CRÍTICA", "ALTA", "MÉDIA"})
_DOC_PATHS = (
    PDPA_SAMPLE,
    REPO_ROOT / "docs" / "compliance-samples" / "README.md",
    REPO_ROOT / "docs" / "compliance-samples" / "README.pt_BR.md",
    REPO_ROOT / "docs" / "COMPLIANCE_FRAMEWORKS.md",
    REPO_ROOT / "docs" / "COMPLIANCE_FRAMEWORKS.pt_BR.md",
)


@pytest.fixture
def pdpa_scanner():
    from core.scanner import DataScanner

    path = str(PDPA_SAMPLE.resolve())
    return DataScanner(regex_overrides_path=path, ml_patterns_path=path)


def test_pdpa_sample_loads():
    data = yaml.safe_load(PDPA_SAMPLE.read_text(encoding="utf-8"))
    assert data["regex"]
    assert data["terms"]
    assert data["recommendation_overrides"]


def test_pdpa_overrides_use_pt_priorities_and_distinct_tags():
    data = yaml.safe_load(PDPA_SAMPLE.read_text(encoding="utf-8"))
    patterns = [row["norm_tag_pattern"] for row in data["recommendation_overrides"]]
    assert "Pakistan PDPA" not in patterns
    assert len(patterns) == len(set(patterns))
    for row in data["recommendation_overrides"]:
        assert row["priority"] in _ALLOWED_PRIORITIES


def test_pdpa_has_no_nude_thirteen_digit_or_qs_geo_key():
    text = PDPA_SAMPLE.read_text(encoding="utf-8")
    assert r"\d{13}" not in text
    forbidden_qs = "lat" + "itude="
    assert forbidden_qs not in text


@pytest.mark.parametrize("path", _DOC_PATHS, ids=lambda p: p.name)
def test_pdpa_docs_do_not_claim_enacted_in_force(path: Path):
    """Operator-grade fact: 2023 text is a Bill; Chambers 2026 still lists it as draft."""
    text = path.read_text(encoding="utf-8")
    lowered = text.lower()
    if path.name.startswith("compliance-sample-pakistan"):
        assert "draft" in lowered or "bill" in lowered
    assert "in force since 2023" not in lowered
    assert "enacted and signed" not in lowered


@pytest.mark.parametrize(
    ("column_name", "pattern_name", "art_fragment"),
    [
        ("cnic", "PK_FIELD_CNIC_LABEL", "s.2(kk)"),
        ("nadra_number", "PK_FIELD_CNIC_LABEL", "s.2(kk)"),
        ("health_data", "PK_FIELD_HEALTH_LABEL", "s.2(kk)"),
        ("parental_consent", "PK_FIELD_CHILD_LABEL", "s.14"),
        ("ntn_number", "PK_FIELD_NTN_LABEL", "s.2 (personal data — NTN)"),
    ],
)
def test_pdpa_contextual_columns(
    pdpa_scanner, column_name: str, pattern_name: str, art_fragment: str
):
    result = pdpa_scanner.scan_column(column_name, "")
    assert pattern_name in result["pattern_detected"]
    assert art_fragment in result["norm_tag"]


def test_pdpa_formatted_cnic_matches(pdpa_scanner):
    result = pdpa_scanner.scan_column("customer_id", "11111-2222222-3")
    assert "PK_CNIC_FORMATTED" in result["pattern_detected"]


def test_pdpa_bare_digits_are_not_cnic(pdpa_scanner):
    result = pdpa_scanner.scan_column("order_id", "3520112345671")
    detected = result.get("pattern_detected") or ""
    assert "PK_CNIC_FORMATTED" not in detected
    assert "CNIC" not in (result.get("norm_tag") or "")
