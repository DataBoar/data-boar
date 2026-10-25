"""APG Fase A — RecommendationEngine + ``core.recommendations``."""

from core.recommendations import RECOMMENDATIONS_APG_PHASE_A, apg_lookup
from report.recommendation_engine import RECOMMENDATIONS, RecommendationEngine


def test_core_recommendations_structure() -> None:
    assert RECOMMENDATIONS_APG_PHASE_A["CPF"]["risk"] == "High"
    assert "Mascaramento Dinâmico" in RECOMMENDATIONS_APG_PHASE_A["CPF"]["action"]
    assert RECOMMENDATIONS_APG_PHASE_A["EMAIL"]["risk"] == "Medium"
    assert "homologação" in RECOMMENDATIONS_APG_PHASE_A["EMAIL"]["action"]
    assert RECOMMENDATIONS_APG_PHASE_A["CREDIT_CARD"]["risk"] == "Critical"
    assert "PCI-DSS" in RECOMMENDATIONS_APG_PHASE_A["CREDIT_CARD"]["action"]
    assert RECOMMENDATIONS_APG_PHASE_A["GENERIC_PII"]["risk"] == "Low"


def test_report_recommendations_flat_compat() -> None:
    assert RECOMMENDATIONS["CPF"] == RECOMMENDATIONS_APG_PHASE_A["CPF"]["action"]


def test_apg_lookup_alias_cnpj() -> None:
    row = apg_lookup("CNPJ")
    assert row["risk"] == "High"
    assert "CNPJ" in row["action"] or "jurídica" in row["action"]


def test_row_for_pattern_maps_lgpd_cpf() -> None:
    row = RecommendationEngine.row_for_pattern("LGPD_CPF", shadow_context=False)
    assert (
        row["recommended_action"] == RECOMMENDATIONS_APG_PHASE_A["LGPD_CPF"]["action"]
    )
