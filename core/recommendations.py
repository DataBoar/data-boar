"""
APG Fase A — dicionário pragmático Achado → ação (PoC).

``risk`` usa rótulos em inglês estáveis para integrações; textos de ``action`` em pt-BR.
"""

from __future__ import annotations

# Mapeamento pragmático para o PoC (chave = nome do achado / pattern canônico).
RECOMMENDATIONS_APG_PHASE_A: dict[str, dict[str, str]] = {
    "CPF": {
        "risk": "High",
        "action": "Implementar Mascaramento Dinâmico ou Criptografia.",
    },
    "LGPD_CPF": {
        "risk": "High",
        "action": "Implementar Mascaramento Dinâmico ou Criptografia.",
    },
    "EMAIL": {
        "risk": "Medium",
        "action": "Pseudonimização em ambientes de homologação.",
    },
    "CREDIT_CARD": {
        "risk": "Critical",
        "action": "Tokenização e isolamento de logs (PCI-DSS).",
    },
    "GENERIC_PII": {
        "risk": "Low",
        "action": "Revisar necessidade de retenção desse dado.",
    },
    "LGPD_CNPJ": {
        "risk": "High",
        "action": (
            "Mascaramento em não-produção; em produção: controles de acesso, mínima exposição "
            "e trilha de uso (CNPJ identifica pessoa jurídica)."
        ),
    },
    "LGPD_CNPJ_ALNUM": {
        "risk": "High",
        "action": (
            "Mascaramento em não-produção; em produção: controles de acesso e rastreabilidade."
        ),
    },
    "PHONE_BR": {
        "risk": "Medium",
        "action": "Pseudonimização; mascarar em interfaces não essenciais.",
    },
    "CCPA_SSN": {
        "risk": "Critical",
        "action": "Eliminar cópias não autorizadas; criptografia forte e segregação de ambientes.",
    },
    "DATE_DMY": {
        "risk": "Medium",
        "action": (
            "Avaliar em conjunto com outros identificadores; políticas de retenção e base legal explícitas."
        ),
    },
}

# Pattern detectado (uppercase) → chave em RECOMMENDATIONS_APG_PHASE_A.
APG_PATTERN_ALIASES: dict[str, str] = {
    "CNPJ": "LGPD_CNPJ",
    "PHONE": "PHONE_BR",
    "TEL": "PHONE_BR",
    "TELEFONE": "PHONE_BR",
    "SSN": "CCPA_SSN",
}


def apg_lookup(pattern: str) -> dict[str, str]:
    """
    Resolve ``pattern_detected`` para ``{"risk": str, "action": str}``.

    Desconhecidos caem em ``GENERIC_PII`` (APG Fase A).
    """
    p = (pattern or "").strip().upper()
    if p in RECOMMENDATIONS_APG_PHASE_A:
        return dict(RECOMMENDATIONS_APG_PHASE_A[p])
    key = APG_PATTERN_ALIASES.get(p)
    if key and key in RECOMMENDATIONS_APG_PHASE_A:
        return dict(RECOMMENDATIONS_APG_PHASE_A[key])
    return dict(RECOMMENDATIONS_APG_PHASE_A["GENERIC_PII"])


def apg_priority(pattern: str) -> int:
    """Menor valor = maior urgência (Top N executivo / ordenação)."""
    p = (pattern or "").strip().upper()
    if p == "CREDIT_CARD":
        return 0
    if p in ("LGPD_CPF", "CPF", "CCPA_SSN", "SSN"):
        return 1
    if "CNPJ" in p or p in ("LGPD_CNPJ", "LGPD_CNPJ_ALNUM"):
        return 2
    if p == "EMAIL":
        return 3
    if p in ("PHONE_BR", "PHONE", "TEL", "TELEFONE"):
        return 4
    return 9


__all__ = [
    "APG_PATTERN_ALIASES",
    "RECOMMENDATIONS_APG_PHASE_A",
    "apg_lookup",
    "apg_priority",
]
