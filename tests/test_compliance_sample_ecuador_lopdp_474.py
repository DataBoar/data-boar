"""Regression guards for the Ecuador LOPDP compliance sample (#474)."""

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
LOPDP_SAMPLE = (
    REPO_ROOT / "docs" / "compliance-samples" / "compliance-sample-ecuador_lopdp.yaml"
)
_ALLOWED_PRIORITIES = frozenset({"CRÍTICA", "ALTA", "MÉDIA"})


@pytest.fixture
def lopdp_scanner():
    from core.scanner import DataScanner

    path = str(LOPDP_SAMPLE.resolve())
    return DataScanner(regex_overrides_path=path, ml_patterns_path=path)


def test_lopdp_sample_loads():
    data = yaml.safe_load(LOPDP_SAMPLE.read_text(encoding="utf-8"))
    assert data["regex"]
    assert data["terms"]
    assert data["recommendation_overrides"]


def test_lopdp_overrides_use_pt_priorities_and_distinct_tags():
    data = yaml.safe_load(LOPDP_SAMPLE.read_text(encoding="utf-8"))
    patterns = [row["norm_tag_pattern"] for row in data["recommendation_overrides"]]
    assert "LOPDP" not in patterns
    assert len(patterns) == len(set(patterns))
    for row in data["recommendation_overrides"]:
        assert row["priority"] in _ALLOWED_PRIORITIES


def test_lopdp_has_no_nude_ten_digit_matcher():
    text = LOPDP_SAMPLE.read_text(encoding="utf-8")
    assert r"\d{10}" not in text
    assert r"\d{10}001" not in text


@pytest.mark.parametrize(
    ("column_name", "pattern_name", "art_fragment"),
    [
        ("numero_cedula", "EC_FIELD_CEDULA_LABEL", "Art. 26"),
        ("estatus_migratorio", "EC_FIELD_MIGRATION_LABEL", "Art. 23"),
        ("historia_clinica", "EC_FIELD_HEALTH_LABEL", "Art. 23"),
        ("numero_ruc", "EC_FIELD_RUC_LABEL", "Art. 26"),
        ("datos_menores", "EC_FIELD_MINOR_LABEL", "Art. 35"),
    ],
)
def test_lopdp_contextual_columns(
    lopdp_scanner, column_name: str, pattern_name: str, art_fragment: str
):
    result = lopdp_scanner.scan_column(column_name, "")
    assert pattern_name in result["pattern_detected"]
    assert art_fragment in result["norm_tag"]


def test_lopdp_bare_digits_are_not_cedula(lopdp_scanner):
    result = lopdp_scanner.scan_column("order_id", "1710031830")
    detected = result.get("pattern_detected") or ""
    assert "EC_FIELD_CEDULA_LABEL" not in detected
    assert "cédula" not in (result.get("norm_tag") or "")
