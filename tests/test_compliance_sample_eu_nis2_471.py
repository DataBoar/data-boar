"""Regression guards for the EU NIS2 compliance sample (#471 / #1663)."""

from pathlib import Path

import pytest
import yaml

from report.generator import _find_override_row

REPO_ROOT = Path(__file__).resolve().parent.parent
NIS2_SAMPLE = (
    REPO_ROOT / "docs" / "compliance-samples" / "compliance-sample-eu_nis2.yaml"
)
_DOC_PATHS = (
    NIS2_SAMPLE,
    REPO_ROOT / "docs" / "compliance-samples" / "README.md",
    REPO_ROOT / "docs" / "compliance-samples" / "README.pt_BR.md",
    REPO_ROOT / "docs" / "COMPLIANCE_FRAMEWORKS.md",
    REPO_ROOT / "docs" / "COMPLIANCE_FRAMEWORKS.pt_BR.md",
)
_FORBIDDEN_IN_FORCE = (
    "in force October 2024",
    "in force since October 2024",
    "vigência out 2024",
)


@pytest.fixture
def nis2_scanner():
    from core.scanner import DataScanner

    path = str(NIS2_SAMPLE.resolve())
    return DataScanner(regex_overrides_path=path, ml_patterns_path=path)


@pytest.mark.parametrize("path", _DOC_PATHS, ids=lambda p: p.name)
def test_nis2_docs_do_not_claim_in_force_october_2024(path: Path):
    """Operator factual: 17/10/2024 is the transposition deadline, not in-force."""
    text = path.read_text(encoding="utf-8")
    lowered = text.lower()
    for phrase in _FORBIDDEN_IN_FORCE:
        assert phrase not in lowered, f"{path.name} still has {phrase!r}"


@pytest.mark.parametrize(
    "column_name",
    ["csirt_contact", "cert_contact"],
)
def test_nis2_csirt_contact_is_art23_not_art3(nis2_scanner, column_name: str):
    """Bugbot #1663: CSIRT/CERT contact is incident-response metadata (Art. 23)."""
    result = nis2_scanner.scan_column(column_name, "")
    assert result["sensitivity_level"] == "HIGH"
    assert "NIS2_INCIDENT_ID_FIELD" in result["pattern_detected"]
    assert "Art. 23" in result["norm_tag"]
    assert "essential entity" not in result["norm_tag"]


def test_nis2_critical_infra_still_art3(nis2_scanner):
    result = nis2_scanner.scan_column("critical_infrastructure", "")
    assert "NIS2_CRITICAL_INFRA_FIELD" in result["pattern_detected"]
    assert "Art. 3" in result["norm_tag"]


def test_nis2_overrides_map_csirt_column_to_art23_text():
    data = yaml.safe_load(NIS2_SAMPLE.read_text(encoding="utf-8"))
    overrides = data["recommendation_overrides"]
    row = _find_override_row(
        "NIS2_INCIDENT_ID_FIELD",
        "NIS2 Art. 23 (incident notification)",
        overrides,
    )
    assert row is not None
    assert "Art. 23" in row["Base legal"]
    assert "incident-response" in row["Recomendação"]
    assert "Essential Entity classification" in row["Recomendação"]
