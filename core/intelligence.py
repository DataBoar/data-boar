"""
Risk intelligence: classify PII pattern labels and aggregate density scores.

This is the scanner-facing **taxonomy brain**: map ``type`` strings (e.g. detector /
``pattern_detected`` names) to coarse risk categories, then apply per-unit weights.

**Not legal classification** — DPO / counsel validates mappings per engagement.
"""

from __future__ import annotations

from typing import Any, Literal, Mapping, Sequence

RiskCategory = Literal["IDENTIFIER", "FINANCIAL", "SENSITIVE", "CHILD_DATA"]

TAXONOMY_WEIGHTS: dict[RiskCategory, int] = {
    "IDENTIFIER": 10,
    "FINANCIAL": 30,
    "SENSITIVE": 80,
    "CHILD_DATA": 100,
}

# Exact keys after ``normalize_pii_type_key`` (uppercase, spaces -> underscores).
# Extend for new first-class pattern names; unknown labels fall back to substring rules
# then to IDENTIFIER (same default as ``PII_MAPPING.get(..., "IDENTIFIER")``).
PII_MAPPING: dict[str, RiskCategory] = {
    "BRAZIL_CPF": "FINANCIAL",
    "BRAZIL_RG": "IDENTIFIER",
    "LGPD_CPF": "FINANCIAL",
    "CPF": "FINANCIAL",
    "CNPJ": "FINANCIAL",
    "CREDIT_CARD": "FINANCIAL",
    "CREDITCARD": "FINANCIAL",
    "EMAIL": "IDENTIFIER",
    "PHONE_NUMBER": "IDENTIFIER",
    "HEALTH_RECORD": "SENSITIVE",
    "HEALTH": "SENSITIVE",
    "HEALTH_DATA": "SENSITIVE",
    "BIOMETRIC_DATA": "SENSITIVE",
    "BIOMETRIC": "SENSITIVE",
    "RELIGION_INFO": "SENSITIVE",
    "DOB_POSSIBLE_MINOR": "CHILD_DATA",
}

# Workshop-only regulatory hints keyed by coarse category (DPO validates per engagement).
LAW_MAPPING: dict[RiskCategory, tuple[str, ...]] = {
    "IDENTIFIER": ("LGPD Art. 5, I",),
    "FINANCIAL": ("LGPD Art. 7", "GDPR Art. 6"),
    "SENSITIVE": ("LGPD Art. 5, II", "LGPD Art. 11", "GDPR Art. 9"),
    "CHILD_DATA": ("LGPD Art. 14", "LGPD Art. 5, II"),
}

# Substring match on normalized label; first block wins (most specific first).
_SUBSTRING_BLOCKS: tuple[tuple[tuple[str, ...], RiskCategory], ...] = (
    (
        (
            "DOB_POSSIBLE_MINOR",
            "POSSIBLE_MINOR",
            "MINOR_DATA",
            "CHILD_DATA",
            "ADOLESCENT",
            "FELCA",
            "COPPA",
            "ART_14",
            "ART.14",
        ),
        "CHILD_DATA",
    ),
    (
        (
            "HEALTH",
            "BIOMET",
            "FINGERPRINT",
            "IRIS",
            "RETINA",
            "VOICEPRINT",
            "GENETIC",
            "DNA",
            "RELIGION",
            "POLITIC",
            "UNION",
            "SEXUAL",
            "PHILOSOPHIC",
            "RACE",
            "ETHNIC",
            "ORIGIN",
            "HIV",
            "DIAGNOS",
            "MEDICAL",
            "CLINICAL",
            "ICD",
            "CID",
            "SAUDE",
            "SAÚDE",
        ),
        "SENSITIVE",
    ),
    (
        (
            "CPF",
            "CNPJ",
            "CREDIT",
            "CARD",
            "BANK",
            "IBAN",
            "ACCOUNT",
            "AGENCIA",
            "AGÊNCIA",
            "ROUTING",
            "PIX",
            "SSN",
            "PASSPORT",
            "RG",
            "CNH",
            "DRIVER",
            "GOV_ID",
            "LGPD_CPF",
            "BRAZIL_CPF",
        ),
        "FINANCIAL",
    ),
    (
        (
            "EMAIL",
            "PHONE",
            "TEL",
            "MOBILE",
            "CELULAR",
            "FONE",
            "NAME",
            "NOME",
            "SOBRENOME",
            "USERNAME",
            "USER_ID",
            "IP_ADDRESS",
            "IPV4",
            "IPV6",
            "ADDRESS",
            "ENDERECO",
            "ENDEREÇO",
            "CEP",
            "POSTAL",
            "LOCATION",
        ),
        "IDENTIFIER",
    ),
)


def normalize_pii_type_key(type_str: str) -> str:
    """Normalize a ``type`` label for ``PII_MAPPING`` lookup and substring rules."""
    return type_str.strip().upper().replace(" ", "_")


def classify_pii_category(type_str: str) -> RiskCategory:
    """
    Classify a single PII ``type`` string into a ``RiskCategory``.

    Order: exact ``PII_MAPPING`` match (after normalization), then substring blocks,
    then ``IDENTIFIER`` (LGPD common personal data bucket).
    """
    key = normalize_pii_type_key(type_str)
    if not key:
        return "IDENTIFIER"
    if key in PII_MAPPING:
        return PII_MAPPING[key]
    for keywords, category in _SUBSTRING_BLOCKS:
        if any(k in key for k in keywords):
            return category
    return "IDENTIFIER"


def taxonomy_weight(category: RiskCategory) -> int:
    """Return the configured per-unit weight for ``category``."""
    return int(TAXONOMY_WEIGHTS[category])


def law_hints_for_pii_findings(findings_list: Sequence[Mapping[str, Any]]) -> list[str]:
    """
    Collect deduplicated workshop law-hint strings implied by PII ``type`` labels.

    Order follows first occurrence of each category as encountered in ``findings_list``.
    """
    seen_cat: set[RiskCategory] = set()
    ordered_cats: list[RiskCategory] = []
    for finding in findings_list:
        if not isinstance(finding, Mapping):
            continue
        raw_type = str(finding.get("type", "")).strip()
        if not raw_type:
            continue
        cat = classify_pii_category(raw_type)
        if cat not in seen_cat:
            seen_cat.add(cat)
            ordered_cats.append(cat)
    out: list[str] = []
    seen_hint: set[str] = set()
    for cat in ordered_cats:
        for hint in LAW_MAPPING.get(cat, ()):
            if hint not in seen_hint:
                seen_hint.add(hint)
                out.append(hint)
    return out


def regulatory_impact_from_findings(findings_list: Sequence[Mapping[str, Any]]) -> str:
    """Single-line workshop note for ``GRCReporter`` ``regulatory_impact`` (not legal advice)."""
    hints = law_hints_for_pii_findings(findings_list)
    return "; ".join(hints) if hints else ""


def calculate_risk(findings_list: Sequence[Mapping[str, Any]]) -> float:
    """
    Sum ``count * weight(category(type))`` over findings.

    Parameters
    ----------
    findings_list
        Iterable of mappings with at least ``type`` and ``count`` (e.g.
        ``[{'type': 'BRAZIL_CPF', 'count': 50}, ...]``).
    """
    total_score = 0.0
    for finding in findings_list:
        if not isinstance(finding, Mapping):
            continue
        raw_type = str(finding.get("type", "")).strip()
        if not raw_type:
            continue
        try:
            count = int(finding["count"])
        except (KeyError, TypeError, ValueError):
            count = 0
        if count <= 0:
            continue
        category = classify_pii_category(raw_type)
        weight = taxonomy_weight(category)
        total_score += float(count) * float(weight)
    return float(total_score)
