"""
Unified sensitivity detector: regex (from config or built-in) + ML (TF-IDF + RandomForest)
+ optional DL (sentence embeddings + classifier). Returns (sensitivity, pattern_detected, norm_tag, confidence);
no storage of sample content.

Pipeline:
1. Regex: built-in + optional overrides from config.
2. ML: training terms from ml_patterns_file or sensitivity_detection.ml_terms (inline).
3. DL (hybrid): when available, training terms from dl_patterns_file or sensitivity_detection.dl_terms;
   confidence is combined with ML (e.g. max(ml_confidence, dl_confidence)).
4. Optional fuzzy column name: when sensitivity_detection.fuzzy_column_match and rapidfuzz are
   available, may elevate LOW borderline scores to MEDIUM (FUZZY_COLUMN_MATCH); default off.
5. Optional connector format hint: when sensitivity_detection.connector_format_id_hint and
   connectors pass declared SQL types/lengths, may elevate LOW to MEDIUM
   (FORMAT_LENGTH_HINT_ID including CPF/CNPJ/SSN lengths and UUID-like 32/36 with uuid/guid name tokens,
   FORMAT_TYPE_HINT_ID_INT, FORMAT_LENGTH_HINT_EMAIL for common email VARCHAR lengths); default off (Plan §4).
6. Optional embedding prototype semantic hint: when enabled and DL backend is available,
   borderline low-confidence columns may elevate to MEDIUM (EMBEDDING_PROTOTYPE_HINT); default off (Plan §5).

To reduce false positives on song lyrics and music tablature/chord sheets:
- Content heuristics detect lyrics (verse/chorus keywords, short lines), tabs (digit/pipe lines),
  and **interleaved cifra** rows (chord lines alternating with lyric lines; chords may mix cases,
  e.g. ``C``, ``Am``, ``EM7``, ``D2sus9``).
- In that context, weak patterns (DATE_DMY, PHONE_BR, CEP_BR when loaded via overrides) are
  downgraded to MEDIUM; ML/DL confidence
  is penalized so borderline cases stay MEDIUM/LOW. Strong PII (CPF, EMAIL, CREDIT_CARD, SSN)
  still reports HIGH.
- Open-source Markdown docs (README, CONTRIBUTING, …) with typical heading structure: same downgrade
  as entertainment for ML-only highs (avoids ~99% on repo boilerplate scanned as filesystem targets).
- Plain ``.txt`` files with many medium-short lines (typical lyric stanzas without ``verse`` headers)
  and filenames with chord symbols in parentheses (e.g. ``Rosa(D).txt``) also widen entertainment context.
- Known OSS Markdown stems (``README*``, ``CONTRIBUTING``, …): if the **sample is short**, **one** ``#``
  heading plus modest body length still triggers OSS-doc context so ML-only HIGH does not require two
  headings in the first chunk. Plain-text reads use ``file_scan.file_sample_max_chars`` (see config loader).
- **Subtitles / captions** (``.srt``, ``.vtt``, ``.ass``/``.ssa``): timing stripped before scan; path or
  cue-shaped text triggers the same entertainment-style ML cap as lyrics (strong PII regex unchanged).
"""

from pathlib import Path
from typing import Any

import copy
import re

from core.column_name_normalize import normalize_column_name_for_ml
from core.brazilian_cpf import text_contains_valid_cpf, text_contains_valid_cnpj
from core.dl_backend import DLClassifier, is_available as dl_available
from core.embedding_prototype_hint import try_embedding_prototype_elevation
from core.fuzzy_column_match import try_fuzzy_elevation
from core.suggested_review import column_name_suggests_identifier_review
from utils.file_encoding import read_text_with_encoding

# Pattern names that require at least one checksum-valid token in the scanned
# text before being included in found_patterns (false-positive gate).
# Identifiers from schema introspection, validated with Mod-11 (core.brazilian_cpf).
_CHECKSUM_GATED_PATTERNS: dict[str, object] = {
    "LGPD_CPF": text_contains_valid_cpf,
    "LGPD_CNPJ": text_contains_valid_cnpj,
}

# Optional ML deps (numpy/pandas/sklearn) - fail gracefully if not installed
try:
    import pandas as pd
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.ensemble import RandomForestClassifier

    _ML_AVAILABLE = True
except ImportError:
    _ML_AVAILABLE = False
    pd = None
    TfidfVectorizer = None
    RandomForestClassifier = None

# Built-in regex patterns (LGPD/GDPR/CCPA/HIPAA/GLBA relevant)
# Notes on Brazilian identifiers:
# - LGPD_CNPJ matches the legacy numeric-only format (14 digits, optional ./-/ punctuation).
# - LGPD_CNPJ_ALNUM matches the newer alphanumeric format where the first 12 positions may
#   contain A–Z or 0–9 and the last two positions remain numeric check digits.
# - LGPD_CPF and LGPD_CNPJ are checksum-gated in the detect() loop via _CHECKSUM_GATED_PATTERNS
#   (Mod-11 validation from core.brazilian_cpf); LGPD_CNPJ_ALNUM is not gated (different
#   encoding; RFB IN 2.229/2024 format validation is out of scope for now).
#   LGPD_CNPJ_ALNUM uses a lookahead to require ≥1 letter so it does not fire on pure-numeric
#   values already handled (with checksum) by LGPD_CNPJ — prevents double-hit and FP noise.
DEFAULT_PATTERNS = {
    "LGPD_CPF": (r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b", "LGPD Art. 5"),
    "LGPD_CNPJ": (r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b", "LGPD Art. 5"),
    # LGPD_CNPJ_ALNUM targets the new alphanumeric CNPJ (IN RFB 2.229/2024).
    # The lookahead (?=[A-Z0-9./-]*[A-Z]) requires at least one uppercase letter in
    # the first 12 positions so this pattern does NOT overlap with pure-numeric CNPJs
    # already handled (with Mod-11 checksum) by LGPD_CNPJ. Without this guard every
    # legacy numeric CNPJ would double-fire here, generating redundant findings and
    # polluting the report when cnpj_alphanumeric is enabled (ADR-0052 / Phase 5.1).
    "LGPD_CNPJ_ALNUM": (
        r"\b(?=[A-Z0-9./-]*[A-Z])[A-Z0-9]{2}\.?[A-Z0-9]{3}\.?[A-Z0-9]{3}/?[A-Z0-9]{4}-?\d{2}\b",
        "LGPD Art. 5",
    ),
    "EMAIL": (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "GDPR Art. 4(1)"),
    "CREDIT_CARD": (r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", "PCI/GLBA"),
    "PHONE_BR": (r"\b(?:\+55\s?)?(?:\(?\d{2}\)?\s?)?\d{4,5}-?\d{4}\b", "LGPD Art. 5"),
    "CCPA_SSN": (r"\b\d{3}-\d{2}-\d{4}\b", "CCPA"),
    "DATE_DMY": (r"\b\d{1,2}/\d{1,2}/\d{2,4}\b", "Personal data context"),
}

# Default ML training terms (sensitive=1, non_sensitive=0).
# Includes LGPD/GDPR-relevant PII plus a subset of sensitive categories (health, religion, political,
# gender, biometric, genetic, race, union, PEP, sex life) for out-of-the-box detection.
# See docs/plans/completed/PLAN_SENSITIVE_CATEGORIES_ML_DL.md and docs/sensitivity_terms_sensitive_categories.example.yaml
# for the full list; override via ml_patterns_file or sensitivity_detection.ml_terms to customize.
DEFAULT_ML_TERMS = [
    ("cpf", 1),
    ("email", 1),
    ("credit card", 1),
    ("password", 1),
    ("senha", 1),
    ("health record", 1),
    ("saude", 1),
    ("data de nascimento", 1),
    ("birth date", 1),
    ("ethnic origin", 1),
    ("political opinion", 1),
    ("religion", 1),
    ("gender", 1),
    ("rg", 1),
    ("ssn", 1),
    ("salary", 1),
    ("salário", 1),
    # Phone / contact (multiple naming schemes and languages for column-name detection)
    ("phone", 1),
    ("telefone", 1),
    ("celular", 1),
    ("mobile", 1),
    ("fone", 1),
    ("home phone", 1),
    ("work phone", 1),
    ("cell phone", 1),
    ("contact number", 1),
    ("phone number", 1),
    ("téléphone", 1),
    ("tél", 1),
    ("teléfono", 1),
    ("telefono", 1),
    ("móvil", 1),
    ("cel", 1),
    ("handy", 1),
    ("handynummer", 1),
    ("mobilnummer", 1),
    ("telefon", 1),
    ("número de telefone", 1),
    # Name / identifier (multiple naming schemes and languages for column-name detection)
    ("first name", 1),
    ("last name", 1),
    ("surname", 1),
    ("full name", 1),
    ("birth name", 1),
    ("christian name", 1),
    ("nickname", 1),
    ("given name", 1),
    ("family name", 1),
    ("middle name", 1),
    ("nome", 1),
    ("sobrenome", 1),
    ("nome do meio", 1),
    ("nome completo", 1),
    ("nombre", 1),
    ("apellido", 1),
    ("nombre completo", 1),
    ("segundo nombre", 1),
    ("prénom", 1),
    ("nom de famille", 1),
    ("nom de naissance", 1),
    ("nom complet", 1),
    ("vorname", 1),
    ("nachname", 1),
    ("geburtsname", 1),
    ("familienname", 1),
    ("rufname", 1),
    ("cognome", 1),
    ("nome di battesimo", 1),
    # ID / document (multiple naming schemes and languages for column-name detection)
    ("cnpj", 1),
    ("passaporte", 1),
    ("passport", 1),
    ("pasaporte", 1),
    ("passeport", 1),
    ("Reisepass", 1),
    ("ctps", 1),
    ("carteira de trabalho", 1),
    ("work permit", 1),
    ("residence permit", 1),
    ("distintivo", 1),
    ("badge", 1),
    ("documento oficial", 1),
    ("official document", 1),
    ("carteira sindical", 1),
    ("union card", 1),
    ("certificado de reservista", 1),
    ("reservist certificate", 1),
    ("título eleitoral", 1),
    ("titulo eleitoral", 1),
    ("voter id", 1),
    ("voter registration", 1),
    ("pis", 1),
    ("pasep", 1),
    ("cartão cidadão", 1),
    ("cartao cidadao", 1),
    ("citizen card", 1),
    ("identidade de estrangeiro", 1),
    ("foreigner id", 1),
    ("certidão", 1),
    ("certidao", 1),
    ("birth certificate", 1),
    ("green card", 1),
    ("registro no conselho de classe", 1),
    ("professional registration", 1),
    ("conselho de classe", 1),
    ("cnh", 1),
    ("carteira de motorista", 1),
    ("driver license", 1),
    ("driving licence", 1),
    ("documento de identidade", 1),
    ("documento de identidad", 1),
    ("identity document", 1),
    ("id card", 1),
    ("carteira de identidade", 1),
    ("cédula", 1),
    ("cedula", 1),
    ("national id", 1),
    ("national id number", 1),
    ("número do documento", 1),
    ("document number", 1),
    ("identification number", 1),
    ("carte d'identité", 1),
    ("document d'identité", 1),
    ("Personalausweis", 1),
    ("Ausweisnummer", 1),
    ("tax id", 1),
    ("tax identification number", 1),
    ("cadastro de pessoa física", 1),
    # French document nicknames and regional variants (carte bleue, carte rose, etc.)
    ("carte bleue", 1),
    ("carte rose", 1),
    ("carte vitale", 1),
    ("titre de séjour", 1),
    ("carte de séjour", 1),
    ("numéro de sécurité sociale", 1),
    ("numero de securite sociale", 1),
    ("n° sécu", 1),
    # Further regional ID/document variations (PT-BR, EN, ES, FR, DE)
    ("rne", 1),
    ("ric", 1),
    ("certidão de nascimento", 1),
    ("certidão de casamento", 1),
    ("certidão de óbito", 1),
    ("certidao de nascimento", 1),
    ("oab", 1),
    ("crm", 1),
    ("crc", 1),
    ("crea", 1),
    ("crq", 1),
    ("registro profissional", 1),
    ("employee badge number", 1),
    ("membership number", 1),
    ("license number", 1),
    ("permit number", 1),
    ("alien registration number", 1),
    ("visa number", 1),
    ("nie", 1),
    ("libro de familia", 1),
    ("carnet de conducir", 1),
    ("titulo de residencia", 1),
    ("Aufenthaltserlaubnis", 1),
    ("Sozialversicherungsnummer", 1),
    # Generic/ambiguous identifiers → flagged but treated as MEDIUM + "confirm manually" (see AMBIGUOUS_COLUMN_TOKENS)
    ("doc_id", 1),
    ("document_id", 1),
    ("id_number", 1),
    ("doc_number", 1),
    ("doc_ref", 1),
    ("document_ref", 1),
    ("identifier", 1),
    # Sensitive categories (LGPD Art. 5 II, 11; GDPR Art. 9) – additive subset for out-of-the-box
    ("religious affiliation", 1),
    ("religiao", 1),
    ("political affiliation", 1),
    ("filiacao politica", 1),
    ("biometric data", 1),
    ("genetic data", 1),
    ("union affiliation", 1),
    ("sindicato", 1),
    ("politically exposed person", 1),
    ("PEP", 1),
    ("race", 1),
    ("skin color", 1),
    ("sexual orientation", 1),
    ("disability", 1),
    ("deficiencia", 1),
    ("condicao de saude", 1),
    ("health condition", 1),
    ("system_log", 0),
    ("item_count", 0),
    ("config_file", 0),
    ("temp_data", 0),
    ("id_interno", 0),
    ("quantidade_estoque", 0),
    # Lyrics and music notation context → reduce false positives
    ("lyrics", 0),
    ("verse", 0),
    ("chorus", 0),
    ("bridge", 0),
    ("refrão", 0),
    ("estrofe", 0),
    ("letra", 0),
    ("cifra", 0),
    ("tab", 0),
    ("tablature", 0),
    ("chord", 0),
    ("guitar", 0),
    ("intro", 0),
    ("outro", 0),
    ("riff", 0),
    ("bass", 0),
    ("capo", 0),
    ("tuning", 0),
]

# Regex patterns that often match in lyrics/tabs without real PII (dates in lyrics, digits in tabs).
# CEP_BR is optional (compliance sample / overrides only): same 8-digit shape as many SKUs/part IDs.
WEAK_PATTERNS_IN_ENTERTAINMENT = frozenset({"DATE_DMY", "PHONE_BR", "CEP_BR"})

# Column-name tokens that are ambiguous (may be PII or internal ID). When the only signal is ML match
# and column name matches one of these, we return MEDIUM and PII_AMBIGUOUS so the report recommends manual confirmation.
AMBIGUOUS_COLUMN_TOKENS = (
    "doc_id",
    "document_id",
    "id_number",
    "doc_number",
    "doc_ref",
    "document_ref",
    "identifier",
)
PII_AMBIGUOUS_NORM_TAG = (
    "Generic identifier – confirm manually (doc_id, document_id, etc.)"
)


def _join_pattern_hits(found_patterns: list[tuple[str, str]]) -> tuple[str, str]:
    """Return joined pattern names and norm tags from regex hits."""
    names = ", ".join(p[0] for p in found_patterns)
    norms = ", ".join(p[1] for p in found_patterns)
    return names, norms


def _attach_possible_minor_context(
    names: str, norms: str, possible_minor: bool
) -> tuple[str, str]:
    """Prefix minor marker and legal context when minor heuristics trigger."""
    if not possible_minor:
        return names, norms
    names = f"DOB_POSSIBLE_MINOR, {names}"
    norms = "LGPD Art. 14 – possible minor data; GDPR Art. 8" + (
        ", " + norms if norms else ""
    )
    return names, norms


def _looks_like_lyrics(sample: str) -> bool:
    """
    Heuristic: content resembles song lyrics (short lines, verse/chorus keywords).
    Used to downgrade false positives from dates/numbers in lyrics.
    """
    if not sample or len(sample.strip()) < 30:
        return False
    lower = sample.lower()
    keywords = (
        "verse",
        "chorus",
        "bridge",
        "refrão",
        "estrofe",
        "letra",
        "lyrics",
        "intro",
        "outro",
        "la la",
        "na na",
        "oh oh",
        "yeah yeah",
        "repeat",
    )
    if any(k in lower for k in keywords):
        return True
    lines = [ln.strip() for ln in sample.splitlines() if ln.strip()]
    if len(lines) >= 5:
        avg_len = sum(len(ln) for ln in lines) / len(lines)
        if avg_len < 55:
            return True
    return False


# Chord suffix atoms: longest-first, matched with .match(); each pattern is linear (no nested
# ambiguous quantifiers) to avoid ReDoS (CodeQL py/redos) from the old ``(?:...)*`` chord regex.
_CHORD_SUFFIX_ATOMS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.I)
    for p in (
        r"maj9",
        r"maj7",
        r"maj\d{1,2}",  # maj13, etc.
        r"maj",
        r"min7",
        r"min",
        r"dim7",
        r"dim",
        r"aug",
        r"sus\d*",
        r"add\d*",
        r"m7",
        r"m(?!aj)",  # minor triad; not start of "maj"
        r"\d",
    )
)
_CHORD_TOKEN_END_OK = re.compile(r"(?=\s|\||/|$)")
_SLASH_BASS = re.compile(r"/[A-Ga-g](?:#|b|♭)?(?:m|min)?", re.I)
_CHORD_ROOT_START = re.compile(r"(?<![A-Za-z0-9])(?=[A-Ga-g])", re.I)


def _consume_chord_token(s: str, start: int) -> int | None:
    """
    If a chord-like token starts at ``start``, return the index just past it; else ``None``.

    Linear time in line length: bounded suffix steps, each step picks the longest matching atom.
    """
    n = len(s)
    if start >= n or s[start] not in "ABCDEFGabcdefg":
        return None
    j = start + 1
    if j < n and s[j] in "#b♭":
        j += 1
    if j < n and s[j].isdigit():
        j += 1
        if j < n and s[j].isdigit():
            j += 1
    for _ in range(48):
        if j >= n:
            break
        best = 0
        rest = s[j:]
        for rx in _CHORD_SUFFIX_ATOMS:
            m = rx.match(rest)
            if m:
                elen = m.end()
                if elen > best:
                    best = elen
        if best == 0:
            break
        j += best
    sb = _SLASH_BASS.match(s, j)
    if sb:
        j = sb.end()
    if j < n and not _CHORD_TOKEN_END_OK.match(s, j):
        return None
    return j


def _chord_like_token_count(line: str) -> int:
    """
    Count tokens that look like chord symbols on one line (EN + PT-BR cifras).

    Covers typical spellings: ``C  G  Am  F``, ``dm7``, ``EM7``, ``D2sus9``, slash bass
    (``G/B``). Mixed case is common in handwritten-style exports (major roots uppercase,
    ``m``/``sus``/extensions lower or upper).

    Implementation avoids a single big ``re.findall`` with a repeated ambiguous alternation
    (CodeQL py/redos); see ``_CHORD_SUFFIX_ATOMS`` / ``_consume_chord_token``.
    """
    if not (line or "").strip():
        return 0
    s = line.strip()
    count = 0
    for m in _CHORD_ROOT_START.finditer(s):
        i = m.start()
        end = _consume_chord_token(s, i)
        if end is not None:
            count += 1
    return count


def _is_prose_lyric_line(line: str) -> bool:
    """Non-empty line that reads like words, not a chord row (allows one stray chord token)."""
    s = (line or "").strip()
    if len(s) < 12:
        return False
    if _chord_like_token_count(s) >= 2:
        return False
    vowels = sum(1 for c in s.lower() if c in "aeiouáéíóúãõâêôàèìòùü")
    if vowels < 2:
        return False
    alpha = sum(1 for c in s if c.isalpha())
    if alpha < 8:
        return False
    return True


def _is_mostly_chord_line(line: str) -> bool:
    """Line dominated by chord symbols (traditional cifra row)."""
    s = (line or "").strip()
    if not s:
        return False
    ntok = _chord_like_token_count(s)
    words = s.split()
    if not words:
        return False
    if ntok >= 2:
        return True
    if len(words) == 1 and ntok == 1:
        return True
    if ntok >= 1 and len(s) <= 48 and all(len(w) <= 10 for w in words):
        if ntok >= max(1, (len(words) + 1) // 2):
            return True
    return False


def _looks_like_interleaved_chord_lyric_sheet(sample: str) -> bool:
    """
    Layout: chord row, lyric row, chord row, … Common in BR cifras; lyrics mention names/dates
    and can spuriously trigger regex + ML unless this context is detected.
    """
    stripped = (sample or "").strip()
    if len(stripped) < 50:
        return False
    lines = [ln.strip() for ln in sample.splitlines() if ln.strip()][:72]
    if len(lines) < 5:
        return False
    transitions = 0
    chord_rows = 0
    n = len(lines)
    for i in range(n - 1):
        a, b = lines[i], lines[i + 1]
        if (_is_mostly_chord_line(a) and _is_prose_lyric_line(b)) or (
            _is_prose_lyric_line(a) and _is_mostly_chord_line(b)
        ):
            transitions += 1
    for i in range(n):
        if _is_mostly_chord_line(lines[i]):
            chord_rows += 1
    if chord_rows < 2:
        return False
    if transitions >= 2:
        return True
    if transitions >= 1 and chord_rows >= 4:
        return True
    return False


def _looks_like_music_tab(sample: str) -> bool:
    """
    Heuristic: content resembles guitar/bass tablature or chord sheets.
    Used to downgrade false positives from digit sequences (tabs) or chord names.
    """
    if not sample or len(sample.strip()) < 20:
        return False
    lines = [ln.strip() for ln in sample.splitlines() if ln.strip()]
    tab_score = 0
    chord_score = 0
    chord_token_lines = 0
    total_chord_tokens = 0
    for ln in lines[:40]:
        if len(ln) > 2:
            # Tab: digits, |, -, [, ], h, p, b, /, \
            tab_chars = sum(1 for c in ln if c in "0123456789|-[ ]hp/b\\")
            if tab_chars >= min(4, len(ln) // 2):
                tab_score += 1
            # Legacy: single-token chord line (capital root only)
            if re.match(r"^[\sA-G][mM0-9#b\s/dim]*$", ln) and len(ln) >= 2:
                chord_score += 1
            ntok = _chord_like_token_count(ln)
            total_chord_tokens += ntok
            if ntok >= 2:
                chord_token_lines += 1
    if tab_score >= 2 or chord_score >= 2:
        return True
    # Typical Brazilian / pop chord sheets: several lines with 2+ chords each
    if chord_token_lines >= 2 or total_chord_tokens >= 6:
        return True
    lower = sample.lower()
    if any(
        k in lower
        for k in (
            "tab",
            "tablature",
            "cifra",
            "chord",
            "acordes",
            "violão",
            "violao",
            "afinação",
            "afinacao",
            "capo",
            "tuning",
            "e|---",
            "a|---",
            "b|---",
        )
    ):
        return True
    return False


# Basenames (without extension) that usually indicate OSS / project docs, not PII stores.
_OSS_MARKDOWN_DOC_STEMS = frozenset(
    {
        "contributing",
        "code_of_conduct",
        "changelog",
        "license",
        "licence",
        "copying",
        "security",
        "authors",
        "governance",
        "codeowners",
        "support",
        "maintaining",
        "readme",
        "history",
    }
)


def _markdown_doc_basename_stem(file_name: str) -> str:
    """Lowercase stem of final path component (``README.pt_BR.md`` → ``readme.pt_br``)."""
    base = Path(file_name).name.lower()
    for suf in (".md", ".markdown"):
        if base.endswith(suf):
            return base[: -len(suf)]
    return base


def _looks_like_open_source_markdown_doc(file_name: str, sample: str) -> bool:
    """
    Heuristic: file looks like a standard repository Markdown document (README, CONTRIBUTING, …)
    with typical ``#`` headings. Used to downgrade ML-only false HIGH on scanned clone trees.
    """
    stem_full = _markdown_doc_basename_stem(file_name)
    if not stem_full:
        return False
    # readme, readme.pt_br, contributing, etc.
    first_part = stem_full.split(".")[0]
    if first_part not in _OSS_MARKDOWN_DOC_STEMS and not first_part.startswith(
        "readme"
    ):
        return False
    if not (file_name.lower().endswith((".md", ".markdown"))):
        return False
    if not (sample or "").strip():
        return False
    heading_hits = len(re.findall(r"(?m)^#+\s+\S", sample))
    if heading_hits >= 2:
        return True
    if heading_hits >= 1 and len(sample.strip()) > 400:
        return True
    # Short samples: scanners often pass only the first N lines. One H1 + a bit of body is enough
    # for known OSS doc names (README*, CONTRIBUTING.md, …) to match entertainment / low-PII doc context.
    stripped = (sample or "").strip()
    if (
        heading_hits >= 1
        and len(stripped) >= 60
        and (first_part.startswith("readme") or first_part in _OSS_MARKDOWN_DOC_STEMS)
    ):
        return True
    return False


def _looks_like_plain_lyrics_txt_file(file_name: str, sample: str) -> bool:
    """
    Heuristic: ``.txt`` with several non-empty lines of moderate length (song lyrics without
    explicit ``verse``/``chorus`` headers). Catches cases where average line length exceeded
    ``_looks_like_lyrics``'s stricter prose threshold.
    """
    if not file_name.lower().endswith(".txt"):
        return False
    lines = [ln.strip() for ln in sample.splitlines() if ln.strip()]
    if len(lines) < 5:
        return False
    lengths = sorted(len(ln) for ln in lines)
    med = lengths[len(lengths) // 2]
    longest = lengths[-1]
    if med > 78 or longest > 200:
        return False
    return True


_FILENAME_CHORD_IN_PARENS = re.compile(
    r"\([A-G](?:#|b|♭)?(?:m(?:aj|in)?|dim|aug|sus|add\d+|maj7?|m7|7)?\)",
    re.IGNORECASE,
)


def _filename_suggests_chord_sheet(file_name: str) -> bool:
    """``Rosa(D).txt``, ``Song(Am).txt`` — filename hints at chord chart / cifra."""
    return bool(_FILENAME_CHORD_IN_PARENS.search(Path(file_name).name))


def _looks_like_subtitle_or_transcript(column_name: str, sample: str) -> bool:
    """
    Sidecar subtitles, pasted cue text, or OCR'd image text: dialogue-like content often
    triggers ML false positives. FN-first: strong regex matches still yield HIGH elsewhere.
    """
    from core.rich_media_magic import IMAGE_EXTENSIONS
    from utils.subtitle_text import SUBTITLE_EXTENSIONS, looks_like_subtitle_markup

    suf = Path(column_name).suffix.lower()
    if suf in SUBTITLE_EXTENSIONS:
        return True
    if suf in IMAGE_EXTENSIONS and looks_like_subtitle_markup(sample or ""):
        return True
    return looks_like_subtitle_markup(sample or "")


def _load_regex_overrides(
    path: str | None,
    encoding: str = "utf-8",
    errors: str = "replace",
) -> dict[str, tuple[str, str]]:
    """Load name -> (pattern, norm_tag) from YAML/JSON file. Uses given encoding (default utf-8)."""
    if not path or not Path(path).exists():
        return {}
    # Validate against canonical plugin schema (ADR-0052); emit warnings for bad items.
    import warnings

    from config.plugin_validator import PluginValidationWarning, validate_plugin_file

    result = validate_plugin_file(path, plugin_type="regex_patterns")
    for issue in result.issues:
        warnings.warn(
            f"Plugin file '{path}': {issue}",
            PluginValidationWarning,
            stacklevel=2,
        )
    raw = read_text_with_encoding(path, encoding=encoding, errors=errors)
    if Path(path).suffix.lower() in (".yaml", ".yml"):
        import yaml

        data = yaml.safe_load(raw)
    else:
        import json

        data = json.loads(raw)
    if not isinstance(data, (list, dict)):
        return {}
    out = {}
    items = (
        data if isinstance(data, list) else data.get("patterns", data.get("regex", []))
    )
    from config.plugin_validator import _has_nested_quantifier

    for item in items:
        if isinstance(item, dict):
            name = item.get("name", "")
            pattern = item.get("pattern", "")
            norm = item.get("norm_tag", "Custom")
            if not (name and pattern):
                continue
            # ReDoS guard (#829) — enforcement at the trust boundary: third-party
            # override patterns only. Built-in DEFAULT_PATTERNS are curated and
            # exempt (calibration test: tests/test_redos_guard.py).
            if _has_nested_quantifier(pattern):
                warnings.warn(
                    f"Plugin file '{path}': pattern '{name}' skipped — nested "
                    f"quantifiers detected (potential ReDoS). Simplify the "
                    f"pattern. (#829)",
                    PluginValidationWarning,
                    stacklevel=2,
                )
                continue
            try:
                re.compile(pattern)
            except re.error as exc:
                warnings.warn(
                    f"Plugin file '{path}': pattern '{name}' skipped — invalid "
                    f"regex: {exc}. (#829)",
                    PluginValidationWarning,
                    stacklevel=2,
                )
                continue
            out[name] = (pattern, norm)
    return out


def _load_ml_patterns(
    path: str | None,
    encoding: str = "utf-8",
    errors: str = "replace",
    *,
    plugin_type: str = "ml_patterns",
) -> list[tuple[str, int]]:
    """Load (text, label) from YAML/JSON; label 1=sensitive, 0=non_sensitive. Uses given encoding."""
    if not path or not Path(path).exists():
        return []
    import warnings

    from config.plugin_validator import PluginValidationWarning, validate_plugin_file

    result = validate_plugin_file(path, plugin_type=plugin_type)
    for issue in result.issues:
        warnings.warn(
            f"Plugin file '{path}': {issue}",
            PluginValidationWarning,
            stacklevel=2,
        )
    raw = read_text_with_encoding(path, encoding=encoding, errors=errors)
    if Path(path).suffix.lower() in (".yaml", ".yml"):
        import yaml

        data = yaml.safe_load(raw)
    else:
        import json

        data = json.loads(raw)
    if not isinstance(data, (list, dict)):
        return []
    items = (
        data if isinstance(data, list) else data.get("patterns", data.get("terms", []))
    )
    out = []
    for item in items:
        if isinstance(item, dict):
            text = item.get("text", "").strip()
            label = 1 if item.get("label", "sensitive") in ("sensitive", 1, "1") else 0
            if text:
                out.append((text.lower(), label))
    return out


def _ml_terms_from_inline_or_file(
    inline: list[dict[str, Any]] | list[tuple[str, int]] | None,
    path: str | None,
    encoding: str = "utf-8",
    errors: str = "replace",
) -> list[tuple[str, int]]:
    """ML training terms: prefer inline when non-empty; else file; else DEFAULT_ML_TERMS."""
    if inline:
        out = []
        for t in inline:
            if isinstance(t, dict):
                text = (t.get("text") or "").strip().lower()
                label = 1 if t.get("label", "sensitive") in ("sensitive", 1, "1") else 0
                if text:
                    out.append((text, label))
            elif isinstance(t, (list, tuple)) and len(t) >= 2:
                text = str(t[0]).strip().lower()
                label = 1 if t[1] in (1, "1", "sensitive") else 0
                if text:
                    out.append((text, label))
        if out:
            return out
    return _load_ml_patterns(path, encoding=encoding, errors=errors) or DEFAULT_ML_TERMS


def _load_dl_terms(
    path: str | None,
    inline: list[dict[str, Any]] | list[tuple[str, int]] | None,
    encoding: str = "utf-8",
    errors: str = "replace",
) -> list[tuple[str, int]]:
    """DL training terms: prefer inline (list of {text, label}); else load from path (same format as ML)."""
    if inline:
        out = []
        for t in inline:
            if isinstance(t, dict):
                text = (t.get("text") or "").strip().lower()
                label = 1 if t.get("label", "sensitive") in ("sensitive", 1, "1") else 0
                if text:
                    out.append((text, label))
            elif isinstance(t, (list, tuple)) and len(t) >= 2:
                text = str(t[0]).strip().lower()
                label = 1 if t[1] in (1, "1", "sensitive") else 0
                if text:
                    out.append((text, label))
        if out:
            return out
    return _load_ml_patterns(
        path, encoding=encoding, errors=errors, plugin_type="dl_patterns"
    )


def _detect_possible_minor(
    column_name: str, sample_text: str, minor_age_threshold: int
) -> bool:
    """
    Heuristic detection of possible minor data based on column name (including PT-BR variants/acronyms)
    and sample values (dates of birth or numeric ages).
    """
    col = (column_name or "").lower()
    sample = sample_text or ""

    # DOB-like column name tokens (EN + PT-BR, including acronyms)
    dob_tokens = (
        "date of birth",
        "birth date",
        "birthdate",
        "data de nascimento",
        "data nascimento",
        "data de nasc",
        "dt_nasc",
        "dt_nascimento",
        "dtnasc",
        "nascimento",
        "menor_de_idade",
        "dob",
        "ddn",
        "dn",
        "nasc",
        "dtn",
    )
    # Age-like column name tokens (EN + PT-BR, including acronyms)
    age_tokens = (
        "age",
        "person age",
        "idade",
        "idade_atual",
        "idade_pessoa",
        "idade_anos",
        "anos",
        "faixa etaria",
        "faixa etária",
        "faixa_etaria",
        "idd",
        "menores",
        "crianca",
        "criança",
        "adolescente",
    )

    is_dob_like = any(tok in col for tok in dob_tokens)
    is_age_like = any(tok in col for tok in age_tokens)
    if not is_dob_like and not is_age_like:
        return False

    from datetime import date

    # Helper: compute age from year, month, day (rough, but enough for < threshold vs >= threshold)
    def _age_from_ymd(y: int, m: int, d: int) -> int | None:
        try:
            today = date.today()
            dob = date(y, m, d)
            years = (
                today.year
                - dob.year
                - ((today.month, today.day) < (dob.month, dob.day))
            )
            return years
        except Exception:
            return None

    # If age-like and we see numeric ages, use them directly
    if is_age_like:
        for match in re.findall(r"\b\d{1,3}\b", sample):
            try:
                val = int(match)
            except ValueError:
                continue
            if 0 <= val < minor_age_threshold:
                return True

    # If DOB-like, try parsing common date formats in the sample text
    if is_dob_like:
        # DMY (e.g. 15/03/2010 or 1/5/12)
        for m in re.findall(r"\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b", sample):
            d_s, m_s, y_s = m
            try:
                d_i = int(d_s)
                m_i = int(m_s)
                y_i = int(y_s)
            except ValueError:
                continue
            if y_i < 100:
                # Simple century heuristic: 00–30 => 2000–2030, else 1900–1999
                y_i = 2000 + y_i if y_i <= 30 else 1900 + y_i
            years = _age_from_ymd(y_i, m_i, d_i)
            if years is not None and 0 <= years < minor_age_threshold:
                return True

        # YMD (e.g. 2010-03-15 or 2010/03/15)
        for m in re.findall(r"\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b", sample):
            y_s, m_s, d_s = m
            try:
                y_i = int(y_s)
                m_i = int(m_s)
                d_i = int(d_s)
            except ValueError:
                continue
            years = _age_from_ymd(y_i, m_i, d_i)
            if years is not None and 0 <= years < minor_age_threshold:
                return True

        # MDY (e.g. 03-15-2010)
        for m in re.findall(r"\b(\d{1,2})[-](\d{1,2})[-](\d{4})\b", sample):
            m_s, d_s, y_s = m
            try:
                m_i = int(m_s)
                d_i = int(d_s)
                y_i = int(y_s)
            except ValueError:
                continue
            years = _age_from_ymd(y_i, m_i, d_i)
            if years is not None and 0 <= years < minor_age_threshold:
                return True

    return False


# Declared length in SQL-style type strings, e.g. VARCHAR(11), CHARACTER(14), character varying(9).
_DECLARED_CHAR_LEN = re.compile(
    r"(?i)(?:var)?char(?:acter)?(?:\s+varying)?\s*\(\s*(\d+)\s*\)"
)


def _parse_declared_char_length(data_type: str | None) -> int | None:
    """Return N from VARCHAR(N) / CHAR(N) / CHARACTER VARYING(N) if present; else None."""
    if not data_type or not str(data_type).strip():
        return None
    m = _DECLARED_CHAR_LEN.search(str(data_type).strip())
    if not m:
        return None
    try:
        n = int(m.group(1))
    except ValueError:
        return None
    return n if n > 0 else None


def _declared_type_is_integer_like(data_type: str | None) -> bool:
    """True when declared SQL type is integer-ish and suitable for ID hints."""
    if not data_type or not str(data_type).strip():
        return False
    t = str(data_type).strip().lower()
    if re.search(r"\b(bigint|integer|int2|int4|int8|int|smallint)\b", t):
        return True
    # DECIMAL(p,0) / NUMERIC(p,0) used as IDs in some schemas.
    if re.search(r"\b(?:decimal|numeric)\s*\(\s*\d+\s*,\s*0\s*\)", t):
        return True
    return False


def _declared_type_email_length_hint(data_type: str | None) -> int | None:
    """
    Return declared character length when it strongly suggests an email-storage column.
    Conservative lengths seen in schemas: 128/191/254/255/256/320 (RFC-ish max, MySQL utf8mb4
    index-friendly 191, common VARCHAR buckets); still gated by email-like column name tokens.
    """
    char_len = _parse_declared_char_length(data_type)
    if char_len in (128, 191, 254, 255, 256, 320):
        return char_len
    return None


def _uuid_declared_length_matches_name(column_name: str, char_len: int) -> bool:
    """True when CHAR/VARCHAR length matches UUID storage and name tokens reduce FPs."""
    col = (column_name or "").lower()
    if char_len == 36 and ("uuid" in col or "guid" in col or "uniqueidentifier" in col):
        return True
    return char_len == 32 and ("uuid" in col or "guid" in col)


def _format_length_suggests_id_column(column_name: str, char_len: int) -> bool:
    """
    True if declared string length matches common ID sizes and the column name is ID-like.

    Conservative: 9 (SSN-style), 11 (CPF digits), 14 (CNPJ digits) with name hints to limit FPs;
    32/36 for UUID-like columns when name contains uuid/guid/uniqueidentifier.
    """
    col = (column_name or "").lower()
    if char_len == 9 and (
        "ssn" in col or "social_sec" in col or "social security" in col
    ):
        return True
    if char_len == 11 and (
        "cpf" in col or column_name_suggests_identifier_review(column_name)
    ):
        return True
    if char_len == 14 and (
        "cnpj" in col or column_name_suggests_identifier_review(column_name)
    ):
        return True
    return _uuid_declared_length_matches_name(column_name, char_len)


def _format_hint_suggests_sensitive_column(
    column_name: str, data_type: str | None
) -> tuple[str, str] | None:
    """
    Optional schema-based hints for columns that look sensitive despite low sample signal.
    Returns (pattern_detected, norm_tag) when a conservative hint applies.
    """
    col = (column_name or "").lower()

    decl_len = _parse_declared_char_length(data_type)
    if decl_len is not None and _format_length_suggests_id_column(
        column_name, decl_len
    ):
        return (
            "FORMAT_LENGTH_HINT_ID",
            "Schema type/length suggests identifier; confirm against sample values",
        )

    if _declared_type_is_integer_like(
        data_type
    ) and column_name_suggests_identifier_review(column_name):
        return (
            "FORMAT_TYPE_HINT_ID_INT",
            "Schema integer type with ID-like column name; confirm against sample values",
        )

    email_len = _declared_type_email_length_hint(data_type)
    email_name_tokens = ("email", "e_mail", "mail")
    if email_len is not None and any(tok in col for tok in email_name_tokens):
        return (
            "FORMAT_LENGTH_HINT_EMAIL",
            "Schema type/length suggests email field; confirm against sample values",
        )
    return None


class SensitivityDetector:
    """
    Hybrid detector: regex first, then ML (TF-IDF + RandomForest), then optional DL (sentence embeddings + classifier).
    analyze(column_name, sample_text, connector_data_type=...) -> (sensitivity_level, pattern_detected, norm_tag, confidence).
    ML/DL training terms can come from config files (ml_patterns_file, dl_patterns_file) or inline (sensitivity_detection.ml_terms / dl_terms).
    """

    def __init__(
        self,
        regex_overrides_path: str | None = None,
        ml_patterns_path: str | None = None,
        ml_terms_inline: list[dict[str, Any]] | list[tuple[str, int]] | None = None,
        dl_patterns_path: str | None = None,
        dl_terms_inline: list[dict[str, Any]] | list[tuple[str, int]] | None = None,
        detection_config: dict[str, Any] | None = None,
        file_encoding: str = "utf-8",
    ):
        enc = file_encoding or "utf-8"
        err = "replace"
        det = detection_config or {}
        # Start from built-in patterns and optionally gate LGPD_CNPJ_ALNUM behind config.
        patterns = copy.deepcopy(DEFAULT_PATTERNS)
        if not bool(det.get("cnpj_alphanumeric", False)):
            patterns.pop("LGPD_CNPJ_ALNUM", None)
        over = _load_regex_overrides(regex_overrides_path, encoding=enc, errors=err)
        for k, v in over.items():
            patterns[k] = v
        self.patterns = patterns
        # Built-in DEFAULT_PATTERNS are curated (trusted); third-party overrides
        # were already filtered by _load_regex_overrides (ReDoS + re.error guard,
        # #829), so every pattern reaching this point compiles safely.
        self._compiled = {
            name: re.compile(pat) for name, (pat, _) in self.patterns.items()
        }

        # ML terms: inline overrides file; file overrides default
        ml_terms = _ml_terms_from_inline_or_file(
            ml_terms_inline, ml_patterns_path, encoding=enc, errors=err
        )
        self._ml_available = False
        self._vectorizer = None
        self._model = None
        if _ML_AVAILABLE and ml_terms:
            texts = [t[0] for t in ml_terms]
            labels = [t[1] for t in ml_terms]
            self._vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
            X = self._vectorizer.fit_transform(texts)
            self._model = RandomForestClassifier(n_estimators=100, random_state=42)
            self._model.fit(X, labels)
            self._ml_available = True

        # DL terms: inline or from dl_patterns_path (same file format as ML)
        dl_terms = _load_dl_terms(
            dl_patterns_path, dl_terms_inline, encoding=enc, errors=err
        )
        self._dl_classifier: DLClassifier | None = None
        if dl_terms and dl_available():
            self._dl_classifier = DLClassifier(dl_terms)
            if not self._dl_classifier.is_ready:
                self._dl_classifier = None

        # Sensitive term strings for optional fuzzy column match (ML + DL training labels).
        sens_for_fuzzy: list[str] = []
        seen_fz: set[str] = set()
        for text, label in ml_terms:
            if label == 1 and text and text not in seen_fz:
                seen_fz.add(text)
                sens_for_fuzzy.append(text)
        for text, label in dl_terms:
            if label == 1 and text and text not in seen_fz:
                seen_fz.add(text)
                sens_for_fuzzy.append(text)
        self._fuzzy_sensitive_terms: tuple[str, ...] = tuple(sens_for_fuzzy)

        try:
            from rapidfuzz import fuzz as _rapidfuzz_fuzz
        except ImportError:
            _rapidfuzz_fuzz = None
        self._rapidfuzz_fuzz = _rapidfuzz_fuzz
        self._fuzzy_requested = bool(det.get("fuzzy_column_match", False))
        self._fuzzy_enabled = self._fuzzy_requested and self._rapidfuzz_fuzz is not None
        try:
            self._fuzzy_min_confidence = int(
                det.get("fuzzy_column_match_min_confidence", 25)
            )
        except (TypeError, ValueError):
            self._fuzzy_min_confidence = 25
        try:
            self._fuzzy_max_confidence = int(
                det.get("fuzzy_column_match_max_confidence", 45)
            )
        except (TypeError, ValueError):
            self._fuzzy_max_confidence = 45
        try:
            self._fuzzy_min_ratio = int(det.get("fuzzy_column_match_min_ratio", 85))
        except (TypeError, ValueError):
            self._fuzzy_min_ratio = 85
        self._fuzzy_min_confidence = max(0, min(100, self._fuzzy_min_confidence))
        self._fuzzy_max_confidence = max(0, min(100, self._fuzzy_max_confidence))
        self._fuzzy_min_ratio = max(50, min(100, self._fuzzy_min_ratio))

        # Minor detection: threshold from config (default 18); other options (e.g. full_scan, cross_reference) are used by connectors/report
        try:
            self._minor_age_threshold = int(det.get("minor_age_threshold", 18))
        except (TypeError, ValueError):
            self._minor_age_threshold = 18
        # ML/DL combined confidence floor for MEDIUM (default 40). HIGH remains at 70. Clamped 1–69.
        try:
            self._medium_confidence_threshold = int(
                det.get("medium_confidence_threshold", 40)
            )
        except (TypeError, ValueError):
            self._medium_confidence_threshold = 40
        self._medium_confidence_threshold = max(
            1, min(69, self._medium_confidence_threshold)
        )
        # Optional: normalize column name (accents/separators) for ML/DL input only; default off.
        self._normalize_column_name_for_ml = bool(
            det.get("column_name_normalize_for_ml", False)
        )
        # Optional: use SQL VARCHAR/CHAR length from connector metadata (Plan §4).
        self._connector_format_id_hint = bool(
            det.get("connector_format_id_hint", False)
        )
        # Optional semantic hint from DL embedding similarity to sensitive-term prototype (Plan §5).
        self._embedding_prototype_hint = bool(
            det.get("embedding_prototype_hint", False)
        )
        try:
            self._embedding_prototype_hint_min_confidence = int(
                det.get("embedding_prototype_hint_min_confidence", 20)
            )
        except (TypeError, ValueError):
            self._embedding_prototype_hint_min_confidence = 20
        try:
            self._embedding_prototype_hint_max_confidence = int(
                det.get("embedding_prototype_hint_max_confidence", 39)
            )
        except (TypeError, ValueError):
            self._embedding_prototype_hint_max_confidence = 39
        try:
            self._embedding_prototype_hint_min_similarity = int(
                det.get("embedding_prototype_hint_min_similarity", 80)
            )
        except (TypeError, ValueError):
            self._embedding_prototype_hint_min_similarity = 80
        self._embedding_prototype_hint_min_confidence = max(
            0, min(100, self._embedding_prototype_hint_min_confidence)
        )
        self._embedding_prototype_hint_max_confidence = max(
            0, min(100, self._embedding_prototype_hint_max_confidence)
        )
        self._embedding_prototype_hint_min_similarity = max(
            50, min(100, self._embedding_prototype_hint_min_similarity)
        )

    def analyze(
        self,
        column_name: str,
        sample_text: str,
        *,
        connector_data_type: str | None = None,
    ) -> tuple[str, str, str, int]:
        """
        Returns (sensitivity_level, pattern_detected, norm_tag, ml_confidence 0-100).
        Does not store sample_text. Downgrades classification when content looks like
        song lyrics or music tabs to reduce false positives.
        """
        combined = f"{column_name} {sample_text}"
        sample_only = sample_text or ""
        if self._normalize_column_name_for_ml:
            nc = normalize_column_name_for_ml(column_name)
            col_for_ml = nc if nc else (column_name or "").strip()
            ml_dl_text = f"{col_for_ml} {sample_only}".strip()
        else:
            ml_dl_text = combined
        entertainment_context = (
            _looks_like_lyrics(sample_only)
            or _looks_like_music_tab(sample_only)
            or _looks_like_interleaved_chord_lyric_sheet(sample_only)
            or _looks_like_open_source_markdown_doc(column_name, sample_only)
            or _looks_like_plain_lyrics_txt_file(column_name, sample_only)
            or _filename_suggests_chord_sheet(column_name)
            or _looks_like_subtitle_or_transcript(column_name, sample_only)
        )

        # Heuristic: possible minor data based on DOB/age (EN + PT-BR)
        possible_minor = _detect_possible_minor(
            column_name, sample_only, self._minor_age_threshold
        )

        found_patterns: list[tuple[str, str]] = []
        for name, (_, norm_tag) in self.patterns.items():
            rex = self._compiled.get(name)
            if not (rex and rex.search(combined)):
                continue
            # Checksum gate: for CPF and CNPJ (numeric), require at least one
            # match with a valid Mod-11 check digit.  This eliminates false
            # positives from sequential IDs, counters, and test data that
            # happen to match the 11/14-digit shape but fail the algorithm.
            gate_fn = _CHECKSUM_GATED_PATTERNS.get(name)
            if gate_fn is not None and not gate_fn(combined):  # type: ignore[operator]
                continue
            found_patterns.append((name, norm_tag))

        ml_confidence = 0
        if self._ml_available and self._model and self._vectorizer:
            try:
                X = self._vectorizer.transform([ml_dl_text.lower()])
                prob = self._model.predict_proba(X)[0][1]
                ml_confidence = int(round(prob * 100))
            except Exception:
                pass

        # Hybrid DL step: when available, combine with ML (take max to avoid missing semantic matches)
        dl_confidence = 0
        if self._dl_classifier and self._dl_classifier.is_ready:
            prob = self._dl_classifier.predict_proba(ml_dl_text)
            if prob is not None:
                dl_confidence = int(round(prob * 100))
        combined_confidence = max(ml_confidence, dl_confidence)

        if entertainment_context:
            combined_confidence = max(0, combined_confidence - 25)
            if found_patterns:
                matched_names = {p[0] for p in found_patterns}
                only_weak = matched_names <= WEAK_PATTERNS_IN_ENTERTAINMENT
                if only_weak and not possible_minor:
                    names, norms = _join_pattern_hits(found_patterns)
                    return (
                        "MEDIUM",
                        names + " (lyrics/tabs context)",
                        norms,
                        min(combined_confidence, 55),
                    )
                names, norms = _join_pattern_hits(found_patterns)
                names, norms = _attach_possible_minor_context(
                    names, norms, possible_minor
                )
                return "HIGH", names, norms, max(combined_confidence, 70)
        else:
            if found_patterns:
                names, norms = _join_pattern_hits(found_patterns)
                names, norms = _attach_possible_minor_context(
                    names, norms, possible_minor
                )
                return "HIGH", names, norms, max(combined_confidence, 80)
        if possible_minor:
            # Minor indication even without strong ML/regex confidence → treat as HIGH with dedicated norm_tag.
            return (
                "HIGH",
                "DOB_POSSIBLE_MINOR",
                "LGPD Art. 14 – possible minor data; GDPR Art. 8",
                max(combined_confidence, 80),
            )
        # Ambiguous column names (doc_id, document_id, etc.): flag for review but MEDIUM priority and ask operator to confirm.
        col_lower = (column_name or "").lower().strip()
        med_thr = self._medium_confidence_threshold
        if not found_patterns and combined_confidence >= med_thr:
            for token in AMBIGUOUS_COLUMN_TOKENS:
                if token in col_lower or col_lower == token:
                    return (
                        "MEDIUM",
                        "PII_AMBIGUOUS",
                        PII_AMBIGUOUS_NORM_TAG,
                        combined_confidence,
                    )
        if not found_patterns:
            fz = try_fuzzy_elevation(
                column_name=column_name,
                combined_confidence=combined_confidence,
                found_patterns=found_patterns,
                medium_threshold=med_thr,
                fuzzy_enabled=self._fuzzy_enabled,
                fuzzy_min_confidence=self._fuzzy_min_confidence,
                fuzzy_max_confidence=self._fuzzy_max_confidence,
                fuzzy_min_ratio=self._fuzzy_min_ratio,
                sensitive_terms=self._fuzzy_sensitive_terms,
                fuzz_mod=self._rapidfuzz_fuzz,
            )
            if fz is not None:
                return fz
            sim_score = None
            if self._dl_classifier and self._dl_classifier.is_ready:
                sim_score = self._dl_classifier.sensitive_prototype_similarity(
                    ml_dl_text
                )
            proto = try_embedding_prototype_elevation(
                combined_confidence=combined_confidence,
                found_patterns=found_patterns,
                medium_threshold=med_thr,
                hint_enabled=self._embedding_prototype_hint,
                hint_min_confidence=self._embedding_prototype_hint_min_confidence,
                hint_max_confidence=self._embedding_prototype_hint_max_confidence,
                hint_min_similarity=self._embedding_prototype_hint_min_similarity,
                similarity_score=sim_score,
            )
            if proto is not None:
                return proto
        if combined_confidence >= 70:
            if entertainment_context:
                # ML-only confidence in entertainment context (lyrics/tabs/cifras) → cap at MEDIUM
                # and cap the *reported* score (same band as weak-regex entertainment path) so the
                # Excel column does not show ~99% for chord sheets that are not PII.
                return (
                    "MEDIUM",
                    "ML_POTENTIAL_ENTERTAINMENT",
                    "Potential personal data in entertainment context",
                    min(combined_confidence, 55),
                )
            return "HIGH", "ML_DETECTED", "LGPD/GDPR/CCPA context", combined_confidence
        if combined_confidence >= med_thr:
            return (
                "MEDIUM",
                "ML_POTENTIAL",
                "Potential personal data",
                combined_confidence,
            )
        # Optional schema hints (declared SQL type/length + conservative column-name heuristics)
        # can elevate LOW to MEDIUM for manual confirmation. This is FN-first and opt-in.
        if self._connector_format_id_hint and not found_patterns:
            fmt_hint = _format_hint_suggests_sensitive_column(
                column_name, connector_data_type
            )
            if fmt_hint is not None:
                pat, norm = fmt_hint
                return (
                    "MEDIUM",
                    pat,
                    norm,
                    max(combined_confidence, med_thr),
                )
        return "LOW", "GENERAL", "Non-personal", combined_confidence
