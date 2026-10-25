"""
Cross-referenced / aggregated data – identification risk.

Maps findings to quasi-identifier categories (gender, job_position, health, address, phone, other),
groups by table or file, and flags when multiple categories in the same group may allow
identification (LGPD Art. 5, GDPR Recital 26). Used at report time to produce the
"Cross-referenced data – possible identification" sheet and recommendation.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

# Canonical category names used in mapping and report
QUASI_IDENTIFIER_CATEGORIES = (
    "gender",
    "job_position",
    "health",
    "address",
    "phone",
    "other",
)

# Built-in: column name tokens (lowercase) -> category. EN and PT-BR oriented.
DEFAULT_COLUMN_CATEGORY_MAP: dict[str, str] = {
    "gender": "gender",
    "sex": "gender",
    "sexo": "gender",
    "genero": "gender",
    "gênero": "gender",
    "cargo": "job_position",
    "role": "job_position",
    "department": "job_position",
    "departamento": "job_position",
    "title": "job_position",
    "titulo": "job_position",
    "occupation": "job_position",
    "occupação": "job_position",
    "job": "job_position",
    "funcao": "job_position",
    "função": "job_position",
    "health": "health",
    "saude": "health",
    "saúde": "health",
    "medical": "health",
    "medico": "health",
    "médico": "health",
    "cid": "health",
    "diagnosis": "health",
    "diagnostico": "health",
    "address": "address",
    "endereco": "address",
    "endereço": "address",
    "city": "address",
    "cidade": "address",
    "postal": "address",
    "cep": "address",
    "location": "address",
    "localizacao": "address",
    "localização": "address",
    "phone": "phone",
    "telefone": "phone",
    "celular": "phone",
    "mobile": "phone",
    "contact": "phone",
    "contato": "phone",
    "fone": "phone",
    # Additional naming schemes and languages (home/work/cell, EN/PT/ES/FR/DE)
    "home phone": "phone",
    "home_phone": "phone",
    "work phone": "phone",
    "work_phone": "phone",
    "cell phone": "phone",
    "cell_phone": "phone",
    "cell": "phone",
    "cellular": "phone",
    "tel": "phone",
    "telephone": "phone",
    "phone number": "phone",
    "phone_number": "phone",
    "contact number": "phone",
    "contact_number": "phone",
    "téléphone": "phone",
    "tél": "phone",
    "telefono": "phone",
    "teléfono": "phone",
    "móvil": "phone",
    "cel": "phone",
    "handy": "phone",
    "handynummer": "phone",
    "mobilnummer": "phone",
    "telefon": "phone",
    # Name / identifier (multiple naming schemes and languages → other for quasi-identifier aggregation)
    "first name": "other",
    "first_name": "other",
    "last name": "other",
    "last_name": "other",
    "surname": "other",
    "full name": "other",
    "full_name": "other",
    "birth name": "other",
    "birth_name": "other",
    "christian name": "other",
    "nickname": "other",
    "given name": "other",
    "given_name": "other",
    "family name": "other",
    "family_name": "other",
    "middle name": "other",
    "middle_name": "other",
    "nome": "other",
    "sobrenome": "other",
    "nome completo": "other",
    "nome_completo": "other",
    "nombre": "other",
    "apellido": "other",
    "nombre completo": "other",
    "prénom": "other",
    "nom de famille": "other",
    "nom de naissance": "other",
    "nom complet": "other",
    "vorname": "other",
    "nachname": "other",
    "geburtsname": "other",
    "familienname": "other",
    "rufname": "other",
    "cognome": "other",
    # ID / document (multiple naming schemes and languages → other for quasi-identifier aggregation)
    "cpf": "other",
    "cnpj": "other",
    "rg": "other",
    "passaporte": "other",
    "passport": "other",
    "pasaporte": "other",
    "passeport": "other",
    "ctps": "other",
    "carteira de trabalho": "other",
    "documento oficial": "other",
    "official document": "other",
    "distintivo": "other",
    "badge": "other",
    "carteira sindical": "other",
    "certificado de reservista": "other",
    "título eleitoral": "other",
    "titulo eleitoral": "other",
    "voter id": "other",
    "pis": "other",
    "cartão cidadão": "other",
    "cartao cidadao": "other",
    "identidade de estrangeiro": "other",
    "certidão": "other",
    "certidao": "other",
    "green card": "other",
    "registro no conselho de classe": "other",
    "professional registration": "other",
    "cnh": "other",
    "driver license": "other",
    "driving licence": "other",
    "documento de identidade": "other",
    "identity document": "other",
    "id card": "other",
    "carteira de identidade": "other",
    "national id": "other",
    "document number": "other",
    "identification number": "other",
    "carte d'identité": "other",
    "document d'identité": "other",
    "personalausweis": "other",
    "tax id": "other",
    "identidade": "other",
    # French document nicknames and regional (carte bleue, carte rose, carte vitale, etc.)
    "carte bleue": "other",
    "carte rose": "other",
    "carte vitale": "other",
    "titre de séjour": "other",
    "carte de séjour": "other",
    "numéro de sécurité sociale": "other",
    "numero de securite sociale": "other",
    # Further regional ID/document (PT-BR, EN, ES, DE)
    "rne": "other",
    "ric": "other",
    "certidão de nascimento": "other",
    "certidao de nascimento": "other",
    "oab": "other",
    "crm": "other",
    "registro profissional": "other",
    "employee badge number": "other",
    "membership number": "other",
    "license number": "other",
    "permit number": "other",
    "nie": "other",
    "libro de familia": "other",
    "carnet de conducir": "other",
    "titulo de residencia": "other",
    "aufenthaltserlaubnis": "other",
    "sozialversicherungsnummer": "other",
}

# Built-in: pattern_detected (substring) -> category
DEFAULT_PATTERN_CATEGORY_MAP: dict[str, str] = {
    "PHONE": "phone",
    "PHONE_BR": "phone",
    "EMAIL": "other",  # contact identifier
    "CPF": "other",
    "RG": "other",
    "SSN": "other",
    "PII_AMBIGUOUS": "other",  # generic identifier – confirm manually
    "FUZZY_COLUMN_MATCH": "other",  # typo-tolerant column name vs sensitive term
    "DATE_": "other",  # age/DOB related
    "DOB": "other",
    "ADDRESS": "address",
    "POSTAL": "address",
}


def map_finding_to_categories(
    row: dict[str, Any],
    config_mapping: list[dict[str, Any]] | None = None,
) -> set[str]:
    """
    Map a single finding (database or filesystem) to quasi-identifier categories.

    Uses config_mapping first (column_pattern or pattern_detected + category), then
    built-in column name tokens and pattern_detected substrings. Returns a set of
    category names (e.g. {"gender", "health"}).
    """
    categories: set[str] = set()
    col = (row.get("column_name") or row.get("file_name") or "").lower()
    pat = (row.get("pattern_detected") or "").upper()

    # Config overrides: list of { "column_pattern": "regex or substring", "category": "gender" } or { "pattern_detected": "PHONE", "category": "phone" }
    if config_mapping:
        for entry in config_mapping:
            if not isinstance(entry, dict):
                continue
            col_pat = entry.get("column_pattern")
            pat_det = entry.get("pattern_detected")
            cat = (entry.get("category") or "").strip().lower()
            if not cat or cat not in QUASI_IDENTIFIER_CATEGORIES:
                continue
            if col_pat and col_pat.lower() in col:
                categories.add(cat)
            if pat_det and pat_det.upper() in pat:
                categories.add(cat)

    # Built-in column tokens
    for token, category in DEFAULT_COLUMN_CATEGORY_MAP.items():
        if token in col:
            categories.add(category)

    # Built-in pattern substrings
    for pattern_sub, category in DEFAULT_PATTERN_CATEGORY_MAP.items():
        if pattern_sub in pat:
            categories.add(category)

    return categories


def run_aggregation(
    db_rows: list[dict[str, Any]],
    fs_rows: list[dict[str, Any]],
    session_id: str,
    config: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Group findings by table (DB) or file (FS); for each group with at least
    min_categories distinct categories, produce one aggregated record.

    Returns list of dicts with keys: target_name, source_type, table_or_file,
    columns_involved, categories, explanation, sensitivity_level.
    """
    detection = (config or {}).get("detection") or {}
    if not detection.get("aggregated_identification_enabled", True):
        return []
    min_cat = max(1, int(detection.get("aggregated_min_categories", 2)))
    incomplete_mode = bool(detection.get("aggregated_incomplete_data_mode", False))
    if incomplete_mode:
        # C10: when operator knows coverage is partial, lower category threshold by one (min 1).
        min_cat = max(1, min_cat - 1)
    single_high_risk_mode = bool(
        detection.get("aggregated_single_high_risk_suggested_review", False)
    )
    mapping = detection.get("quasi_identifier_mapping") or []

    out: list[dict[str, Any]] = []

    # Database: group by (target_name, schema_name, table_name)
    db_groups: dict[tuple, list[dict]] = defaultdict(list)
    for r in db_rows:
        key = (
            r.get("target_name", ""),
            r.get("schema_name", ""),
            r.get("table_name", ""),
        )
        db_groups[key].append(r)

    for (target, schema, table), rows in db_groups.items():
        all_cats: set[str] = set()
        columns_involved: list[str] = []
        for r in rows:
            cats = map_finding_to_categories(r, mapping)
            all_cats |= cats
            col = r.get("column_name") or ""
            if col and col not in columns_involved:
                columns_involved.append(col)
        should_emit = len(all_cats) >= min_cat
        single_high_risk = len(all_cats) == 1 and "health" in all_cats
        if (not should_emit) and single_high_risk_mode and single_high_risk:
            should_emit = True
        if should_emit:
            table_display = f"{schema}.{table}" if schema else table
            explanation = _build_explanation(
                all_cats,
                "table",
                incomplete_mode=incomplete_mode,
                single_high_risk=single_high_risk,
            )
            if single_high_risk_mode and single_high_risk:
                sensitivity = "MEDIUM"
            else:
                sensitivity = "CRITICAL" if "health" in all_cats else "HIGH"
            out.append(
                {
                    "session_id": session_id,
                    "target_name": target,
                    "source_type": "database",
                    "table_or_file": table_display,
                    "columns_involved": ", ".join(columns_involved[:50]) or "-",
                    "categories": ", ".join(sorted(all_cats)),
                    "explanation": explanation,
                    "sensitivity_level": sensitivity,
                }
            )

    # Filesystem: group by (target_name, path, file_name)
    fs_groups: dict[tuple, list[dict]] = defaultdict(list)
    for r in fs_rows:
        key = (
            r.get("target_name", ""),
            r.get("path", ""),
            r.get("file_name", ""),
        )
        fs_groups[key].append(r)

    for (target, path, file_name), rows in fs_groups.items():
        all_cats = set()
        columns_involved = []
        for r in rows:
            cats = map_finding_to_categories(r, mapping)
            all_cats |= cats
            fn = r.get("file_name") or ""
            if fn and fn not in columns_involved:
                columns_involved.append(fn)
        should_emit = len(all_cats) >= min_cat
        single_high_risk = len(all_cats) == 1 and "health" in all_cats
        if (not should_emit) and single_high_risk_mode and single_high_risk:
            should_emit = True
        if should_emit:
            table_display = file_name or path or "-"
            explanation = _build_explanation(
                all_cats,
                "file",
                incomplete_mode=incomplete_mode,
                single_high_risk=single_high_risk,
            )
            if single_high_risk_mode and single_high_risk:
                sensitivity = "MEDIUM"
            else:
                sensitivity = "CRITICAL" if "health" in all_cats else "HIGH"
            out.append(
                {
                    "session_id": session_id,
                    "target_name": target,
                    "source_type": "filesystem",
                    "table_or_file": table_display,
                    "columns_involved": ", ".join(columns_involved[:50]) or "-",
                    "categories": ", ".join(sorted(all_cats)),
                    "explanation": explanation,
                    "sensitivity_level": sensitivity,
                }
            )

    return out


def _build_explanation(
    categories: set[str],
    context: str,
    *,
    incomplete_mode: bool = False,
    single_high_risk: bool = False,
) -> str:
    cat_list = ", ".join(sorted(categories))
    base = (
        f"Possible identification risk: combination of {cat_list} in the same {context} may allow identification or re-identification of individuals. "
        "This inference is based on sampled/incomplete scanning coverage; treat as suggested review and confirm manually. "
        "Consider access controls, purpose limitation and anonymisation (LGPD Art. 5, GDPR Recital 26)."
    )
    if incomplete_mode:
        base += " Incomplete-data mode is enabled (lower aggregation threshold) to favor recall under partial coverage."
    if single_high_risk:
        base += " Single high-risk category (health) is surfaced as suggested review to avoid false negatives."
    return base
