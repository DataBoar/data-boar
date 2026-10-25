"""Regression guards for the Brazil EAD / ECA compliance sample (#514)."""

from pathlib import Path

import pytest
import yaml

from report.generator import _find_override_row

REPO_ROOT = Path(__file__).resolve().parent.parent
EAD_SAMPLE = (
    REPO_ROOT
    / "docs"
    / "compliance-samples"
    / "compliance-sample-br_ead_lgpd_art14.yaml"
)
_BUILTIN_MINOR_NORM = "LGPD Art. 14 – possible minor data; GDPR Art. 8"


@pytest.fixture
def ead_scanner():
    from core.scanner import DataScanner

    path = str(EAD_SAMPLE.resolve())
    return DataScanner(regex_overrides_path=path, ml_patterns_path=path)


def test_ead_overrides_do_not_hijack_builtin_minor_norm_tag():
    """
    Bugbot #1662: a catch-all ``LGPD Art. 14`` pattern substring-matches
    built-in DOB_POSSIBLE_MINOR and steals the product recommendation row.
    """
    data = yaml.safe_load(EAD_SAMPLE.read_text(encoding="utf-8"))
    overrides = data["recommendation_overrides"]
    assert all(
        "LGPD Art. 14" != (row.get("norm_tag_pattern") or "").strip()
        for row in overrides
    )
    assert (
        _find_override_row("DOB_POSSIBLE_MINOR", _BUILTIN_MINOR_NORM, overrides) is None
    )
    for sample_norm in (
        "LGPD Art. 14 – student ID (RA)",
        "LGPD Art. 14 – student enrollment ID",
        "LGPD Art. 14 – institutional edu email (BR)",
        "LGPD Art. 14 – CPF em contexto educacional",
    ):
        assert _find_override_row("EAD", sample_norm, overrides) is not None, (
            sample_norm
        )


@pytest.mark.parametrize(
    "column_name",
    [
        "cpf_aluno",
        "cpf_aluno_nome",
        "aluno_cpf_numero",
        "estudante_cpf",
    ],
)
def test_ead_cpf_student_context_matches_compound_column_headers(
    ead_scanner, column_name: str
):
    """Bugbot #1662: trailing \\b missed snake_case LMS suffixes (same class as #1288)."""
    result = ead_scanner.scan_column(column_name, "")
    assert result["sensitivity_level"] == "HIGH"
    assert "CPF_STUDENT_CONTEXT" in result["pattern_detected"]


def test_ead_cpf_student_context_does_not_match_bare_cpf_digits(ead_scanner):
    """Bare national-id digits stay on the LGPD / built-in matcher — this sample is contextual."""
    result = ead_scanner.scan_column("document_number", "000.000.000-00")
    assert "CPF_STUDENT_CONTEXT" not in result["pattern_detected"]
