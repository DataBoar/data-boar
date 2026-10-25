"""Regression guards for the Peru Ley 29733 compliance sample (#476)."""

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
PERU_SAMPLE = (
    REPO_ROOT / "docs" / "compliance-samples" / "compliance-sample-peru_ley29733.yaml"
)
_ALLOWED_PRIORITIES = frozenset({"CRÍTICA", "ALTA", "MÉDIA"})
_DOC_PATHS = (
    PERU_SAMPLE,
    REPO_ROOT / "docs" / "compliance-samples" / "README.md",
    REPO_ROOT / "docs" / "compliance-samples" / "README.pt_BR.md",
    REPO_ROOT / "docs" / "COMPLIANCE_FRAMEWORKS.md",
    REPO_ROOT / "docs" / "COMPLIANCE_FRAMEWORKS.pt_BR.md",
)


@pytest.fixture
def peru_scanner():
    from core.scanner import DataScanner

    path = str(PERU_SAMPLE.resolve())
    return DataScanner(regex_overrides_path=path, ml_patterns_path=path)


def test_peru_sample_loads():
    data = yaml.safe_load(PERU_SAMPLE.read_text(encoding="utf-8"))
    assert data["regex"]
    assert data["terms"]
    assert data["recommendation_overrides"]


def test_peru_overrides_use_pt_priorities_and_distinct_tags():
    data = yaml.safe_load(PERU_SAMPLE.read_text(encoding="utf-8"))
    patterns = [row["norm_tag_pattern"] for row in data["recommendation_overrides"]]
    assert "Ley 29733" not in patterns
    assert len(patterns) == len(set(patterns))
    for row in data["recommendation_overrides"]:
        assert row["priority"] in _ALLOWED_PRIORITIES


def test_peru_has_no_nude_id_or_qs_geo_key():
    text = PERU_SAMPLE.read_text(encoding="utf-8")
    assert r"\d{8}" not in text
    assert r"10\d{9}" not in text
    assert r"20\d{9}" not in text
    assert r"9\d{8}" not in text
    forbidden_qs = "lat" + "itude="
    assert forbidden_qs not in text


def test_peru_does_not_cite_art12_as_consent():
    """Issue spec pointed at Art. 12-13 for written consent; Art. 12 is principles."""
    text = PERU_SAMPLE.read_text(encoding="utf-8")
    assert "Art. 13.6" in text
    assert "Art. 12 = interpretive" in text or "Art. 12 is the interpretive" in text


@pytest.mark.parametrize("path", _DOC_PATHS, ids=lambda p: p.name)
def test_peru_docs_do_not_claim_oecd_membership(path: Path):
    """OECD.org: accession candidate (roadmap 2022), not a member as of 2026-08."""
    text = path.read_text(encoding="utf-8")
    lowered = text.lower()
    if "peru" in path.name or "29733" in path.name:
        assert (
            "accession" in lowered or "candidato" in lowered or "candidata" in lowered
        )
    assert "oecd member 2024" not in lowered
    assert "joined oecd in 2024" not in lowered
    assert "membro da ocde em 2024" not in lowered
    assert "ingressou na ocde em 2024" not in lowered


@pytest.mark.parametrize(
    ("column_name", "pattern_name", "art_fragment"),
    [
        ("numero_dni", "PE_FIELD_DNI_LABEL", "Art. 2.4"),
        ("numero_ruc", "PE_FIELD_RUC_LABEL", "Art. 2.4"),
        ("historia_clinica", "PE_FIELD_HEALTH_LABEL", "Art. 2.5"),
        ("ingresos_economicos", "PE_FIELD_INCOME_LABEL", "ingresos"),
        ("opinion_politica", "PE_FIELD_CONVICTION_LABEL", "convicciones"),
        ("datos_menores", "PE_FIELD_MINOR_LABEL", "Art. 13.3"),
        ("comunicacion_confidencial", "PE_FIELD_CONFIDENTIALITY_LABEL", "Art. 17"),
        ("numero_de_dni", "PE_FIELD_DNI_LABEL", "Art. 2.4"),
        ("eps_afiliacion", "PE_FIELD_HEALTH_LABEL", "Art. 2.5"),
    ],
)
def test_peru_contextual_columns(
    peru_scanner, column_name: str, pattern_name: str, art_fragment: str
):
    result = peru_scanner.scan_column(column_name, "")
    assert pattern_name in result["pattern_detected"]
    assert art_fragment in result["norm_tag"]


def test_peru_bare_digits_are_not_dni(peru_scanner):
    result = peru_scanner.scan_column("order_id", "12345678")
    detected = result.get("pattern_detected") or ""
    assert "PE_FIELD_DNI_LABEL" not in detected
    assert "DNI" not in (result.get("norm_tag") or "")
