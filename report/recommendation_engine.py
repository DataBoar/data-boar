"""
Artigo II — RecommendationEngine (APG Fase A): mapeador Achado → ação.

Fonte única: :data:`core.recommendations.RECOMMENDATIONS_APG_PHASE_A`.
"""

from __future__ import annotations

from typing import Any

from core.recommendations import (
    RECOMMENDATIONS_APG_PHASE_A,
    apg_lookup,
    apg_priority,
)

# Compat: ``pattern → texto de ação`` (derivado do dicionário core).
RECOMMENDATIONS: dict[str, str] = {
    k: v["action"] for k, v in RECOMMENDATIONS_APG_PHASE_A.items()
}


def _risk_en_to_risk_band_pt(pattern: str, risk_en: str) -> str:
    p = (pattern or "").strip().upper()
    if p == "CREDIT_CARD":
        return "Bloqueante (PCI)"
    if risk_en == "Critical":
        return "Crítico"
    if risk_en == "High":
        return "Crítico (identificador BR)"
    if risk_en == "Medium":
        if p == "DATE_DMY":
            return "Contextual"
        return "Médio"
    if risk_en == "Low":
        return "Baixo"
    return risk_en


def _business_impact_for(pattern: str, risk_en: str) -> str:
    p = (pattern or "").strip().upper()
    if p == "CREDIT_CARD":
        return "Altíssimo — PCI-DSS e fraude."
    if p in ("LGPD_CPF", "CPF"):
        return "Alto — LGPD (identificação de pessoa física)."
    if p in ("LGPD_CNPJ", "LGPD_CNPJ_ALNUM", "CNPJ") or "CNPJ" in p:
        return "Alto — LGPD e risco reputacional/fiscal."
    if p == "EMAIL":
        return "Médio — contato e vetores de phishing."
    if p in ("PHONE_BR", "PHONE", "TEL", "TELEFONE"):
        return "Médio — identificação e contato."
    if p in ("CCPA_SSN", "SSN"):
        return "Alto — identificadores governamentais."
    if p == "DATE_DMY":
        return "Variável — risco aumenta com outros identificadores."
    if risk_en == "Low":
        return "Otimização de dados e conformidade de retenção."
    return "Depende do contexto de negócio."


class RecommendationEngine:
    """Motor de recomendações APG Fase A (sem ML; só regras)."""

    @staticmethod
    def primary_action(pattern: str) -> str | None:
        return apg_lookup(pattern)["action"]

    @classmethod
    def row_for_pattern(cls, pattern: str, *, shadow_context: bool) -> dict[str, str]:
        """Uma linha APG: tipo, faixa de risco, ação, impacto (orientação operacional)."""
        p = (pattern or "").strip().upper()
        if shadow_context and p not in ("CREDIT_CARD",):
            return {
                "pii_type": p or "(unnamed)",
                "risk_band": "Baixo (shadow / naming heuristic)",
                "recommended_action": (
                    "Quarentena ou exclusão controlada do ativo; revisar se a tabela ainda é necessária."
                ),
                "business_impact": "Otimização de storage e redução de superfície de dados esquecidos.",
            }

        entry = apg_lookup(p)
        risk_en = entry["risk"]
        return {
            "pii_type": p or "(unknown)",
            "risk_band": _risk_en_to_risk_band_pt(p, risk_en),
            "recommended_action": entry["action"],
            "business_impact": _business_impact_for(p, risk_en),
        }


def apg_row_for_pattern(
    pattern: str, *, shadow_context: bool = False
) -> dict[str, str]:
    """API estável usada por relatórios e testes."""
    return RecommendationEngine.row_for_pattern(pattern, shadow_context=shadow_context)


def rank_for_poc_priority(pattern: str) -> int:
    """Menor = mais urgente para Top 3 no resumo executivo (delega a ``apg_priority``)."""
    return apg_priority(pattern)


def sort_apg_rows(apg_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Ordena por severidade APG e volume de achados (mesma regra do Top N)."""

    if not apg_rows:
        return []

    def sort_key(row: dict[str, Any]) -> tuple[int, int, str]:
        pat = str(row.get("pattern_detected", ""))
        return (
            rank_for_poc_priority(pat),
            -int(row.get("finding_count") or 0),
            pat,
        )

    return sorted(apg_rows, key=sort_key)


def top_n_recommendations(
    apg_rows: list[dict[str, Any]], n: int = 3
) -> list[dict[str, Any]]:
    """Ordena por severidade e volume de achados; devolve os N primeiros tipos."""
    sorted_rows = sort_apg_rows(apg_rows)
    return sorted_rows[:n]
