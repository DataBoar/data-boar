"""
Optional jurisdiction hints for Excel Report info (DPO-facing, heuristic only).

Uses only finding *metadata* (column/table/file/path/pattern/norm_tag) — no raw cell
payloads are stored in SQLite, so hints are necessarily incomplete and may false-positive.
"""

from __future__ import annotations

import re
from typing import Any

# --- US – California (CCPA / CPRA) ---
_RE_CCPA_TAG = re.compile(r"CCPA|CPRA", re.IGNORECASE)
_RE_CA_STATE = re.compile(
    r"(CALIFORNIA|,\s*CA\.?\b|\bCA\.?\s*,|\bSTATE\s*[=:]\s*CA\b|_CA_|/CA/|\bCA\b)",
    re.IGNORECASE,
)
# Rough 5-digit zips common in CA (prefix families; still overlaps other western states).
_RE_CA_ZIP_LIKE = re.compile(
    r"\b(900|901|902|903|904|905|906|907|908|909|91[0-9]{2}|92[0-9]{2}|93[0-9]{2}|94[0-9]{2}|95[0-9]{2}|96[01][0-9])\d{2}\b"
)
_RE_ADDR_CONTEXT = re.compile(
    r"(ZIP|POSTAL|ADDRESS|ADDR|PHONE|MOBILE|AREA|STATE|CITY)", re.IGNORECASE
)

# --- US – Colorado (CPA) ---
_RE_COLORADO = re.compile(r"COLORADO|COLORADO\s+CPA|\bCPA\b.*\bCOLORADO", re.IGNORECASE)
_RE_CO_ZIP = re.compile(r"\b80[0-8][0-9]{2}\b")

# --- Japan (APPI) ---
_RE_JP = re.compile(
    r"(APPI|ACT\s+ON\s+THE\s+PROTECTION\s+OF\s+PERSONAL\s+INFORMATION|個人情報|JAPAN\s+PI)",
    re.IGNORECASE,
)


def _row_blob(row: dict[str, Any]) -> str:
    parts = [
        row.get("column_name"),
        row.get("table_name"),
        row.get("schema_name"),
        row.get("file_name"),
        row.get("path"),
        row.get("pattern_detected"),
        row.get("norm_tag"),
        row.get("data_type"),
    ]
    return " ".join(str(p or "") for p in parts)


def _combined_text(db_rows: list[dict], fs_rows: list[dict]) -> str:
    return "\n".join(_row_blob(r) for r in list(db_rows) + list(fs_rows))


def _score_us_ca(text: str) -> tuple[int, list[str]]:
    reasons: list[str] = []
    score = 0
    if _RE_CCPA_TAG.search(text):
        score += 5
        reasons.append("tag/pattern mentions CCPA or CPRA")
    if re.search(r"CALIFORNIA", text, re.IGNORECASE):
        score += 3
        reasons.append("text mentions California")
    if _RE_CA_STATE.search(text):
        score += 2
        reasons.append("possible US-CA state token in names/paths")
    if _RE_CA_ZIP_LIKE.search(text):
        score += 2
        reasons.append("ZIP-like prefix consistent with western US (incl. CA)")
    if _RE_ADDR_CONTEXT.search(text) and (
        _RE_CA_ZIP_LIKE.search(text) or re.search(r"\bCA\b", text)
    ):
        score += 2
        reasons.append("address/phone/postal context near state or ZIP-like token")
    return score, reasons


def _score_us_co(text: str) -> tuple[int, list[str]]:
    reasons: list[str] = []
    score = 0
    if _RE_COLORADO.search(text):
        score += 4
        reasons.append("Colorado / Colorado CPA mentioned")
    if _RE_CO_ZIP.search(text):
        score += 2
        reasons.append("ZIP prefix often associated with Colorado")
    if re.search(r"\bDENVER\b|\bBOULDER\b", text, re.IGNORECASE):
        score += 1
        reasons.append("CO city token")
    return score, reasons


def _score_jp(text: str) -> tuple[int, list[str]]:
    reasons: list[str] = []
    score = 0
    if _RE_JP.search(text):
        score += 5
        reasons.append("Japan APPI / Japanese PI wording or script token")
    return score, reasons


def jurisdiction_hints_enabled(config: dict[str, Any] | None) -> bool:
    if not config:
        return False
    jh = (config.get("report") or {}).get("jurisdiction_hints") or {}
    return bool(jh.get("enabled"))


def jurisdiction_hints_effective(
    config: dict[str, Any] | None,
    meta: dict[str, Any] | None,
) -> bool:
    """
    True when hints should run: config enabled and/or session opted in (CLI/API/dashboard).
    """
    meta = meta or {}
    if meta.get("jurisdiction_hint"):
        return True
    return jurisdiction_hints_enabled(config)


def build_jurisdiction_hint_report_rows(
    db_rows: list[dict],
    fs_rows: list[dict],
    config: dict[str, Any] | None,
    meta: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    """
    Return extra Report info rows (Field / Value) when hints are enabled and signals fire.

    Not a legal conclusion; recommends counsel review. Does not change sensitivity levels.
    """
    if not jurisdiction_hints_effective(config, meta):
        return []
    jh = ((config or {}).get("report") or {}).get("jurisdiction_hints") or {}
    us_ca = bool(jh.get("us_ca", True))
    us_co = bool(jh.get("us_co", True))
    jp = bool(jh.get("jp", True))
    try:
        min_ca = int(jh.get("min_score_us_ca", 4))
    except (TypeError, ValueError):
        min_ca = 4
    try:
        min_co = int(jh.get("min_score_us_co", 4))
    except (TypeError, ValueError):
        min_co = 4
    try:
        min_jp = int(jh.get("min_score_jp", 3))
    except (TypeError, ValueError):
        min_jp = 3

    text = _combined_text(db_rows, fs_rows)
    if not text.strip():
        return []

    out: list[dict[str, str]] = []
    disclaimer = (
        "Heuristic only (metadata column/file/path names and norm tags — no full cell dumps). "
        "High false-positive/negative rate. Not a legal conclusion. "
        "Consult counsel before relying on jurisdiction scope."
    )

    if us_ca:
        sc, reasons = _score_us_ca(text)
        if sc >= min_ca or _RE_CCPA_TAG.search(text):
            body = (
                "Possible relevance to CCPA / CPRA (California). "
                "If consumer personal information of California residents is in scope, "
                "review disclosure, deletion, correction, and opt-out of sale/sharing obligations. "
                f"Signals: {'; '.join(reasons) or 'combined metadata match'}. "
                f"{disclaimer}"
            )
            out.append(
                {
                    "Field": "Jurisdiction hint (US-CA) — DPO / counsel",
                    "Value": body,
                }
            )

    if us_co:
        sc, reasons = _score_us_co(text)
        if sc >= min_co:
            body = (
                "Possible relevance to Colorado privacy (CPA / consumer rules). "
                "Review with counsel if Colorado residents or operations are in scope. "
                f"Signals: {'; '.join(reasons)}. {disclaimer}"
            )
            out.append(
                {
                    "Field": "Jurisdiction hint (US-CO) — DPO / counsel",
                    "Value": body,
                }
            )

    if jp:
        sc, reasons = _score_jp(text)
        if sc >= min_jp:
            body = (
                "Possible relevance to Japan APPI (Act on the Protection of Personal Information). "
                "Strong local requirements; map with counsel. "
                f"Signals: {'; '.join(reasons)}. {disclaimer}"
            )
            out.append(
                {
                    "Field": "Jurisdiction hint (JP) — DPO / counsel",
                    "Value": body,
                }
            )

    return out
