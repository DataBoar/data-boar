"""
Optional fuzzy matching of column names to sensitive ML/DL training terms.

Requires **rapidfuzz** (install optional extra ``detection-fuzzy`` or dev dependency group).
When the extra is not installed, the detector skips this path entirely.

Used only when ``fuzzy_column_match`` is enabled in config and combined ML/DL confidence
lies in a band strictly below the MEDIUM threshold (see ``try_fuzzy_elevation``).
"""

from __future__ import annotations

from collections.abc import Sequence

from core.column_name_normalize import normalize_column_name_for_ml

FUZZY_COLUMN_MATCH_PATTERN = "FUZZY_COLUMN_MATCH"
FUZZY_COLUMN_MATCH_NORM_TAG = (
    "Possible personal data (fuzzy column name – confirm manually)"
)


def _prepare_column_key(column_name: str) -> str:
    raw = (column_name or "").strip()
    if not raw:
        return ""
    norm = normalize_column_name_for_ml(raw)
    return (norm or raw).lower().strip()


def best_fuzzy_score(column_key: str, term: str, fuzz_mod: object) -> int:
    """Return 0–100 similarity using ratio, partial_ratio, and token_set_ratio (max)."""
    if not column_key or not term:
        return 0
    t = term.strip().lower()
    if len(t) < 2:
        return 0
    ratio = getattr(fuzz_mod, "ratio", None)
    partial = getattr(fuzz_mod, "partial_ratio", None)
    token_set = getattr(fuzz_mod, "token_set_ratio", None)
    if not callable(ratio) or not callable(partial) or not callable(token_set):
        return 0
    return max(
        int(ratio(column_key, t)),
        int(partial(column_key, t)),
        int(token_set(column_key, t)),
    )


def try_fuzzy_elevation(
    *,
    column_name: str,
    combined_confidence: int,
    found_patterns: list,
    medium_threshold: int,
    fuzzy_enabled: bool,
    fuzzy_min_confidence: int,
    fuzzy_max_confidence: int,
    fuzzy_min_ratio: int,
    sensitive_terms: Sequence[str],
    fuzz_mod: object | None,
) -> tuple[str, str, str, int] | None:
    """
    If fuzzy matching should elevate this column to MEDIUM, return a full analyze() tuple;
    otherwise None.

    Runs only when there is no regex hit, ``fuzzy_enabled`` and ``fuzz_mod`` are set,
    and ``combined_confidence`` is in ``[eff_low, eff_high]`` where ``eff_high`` is at most
    ``medium_threshold - 1`` so normal MEDIUM/ML_POTENTIAL paths are unchanged.
    """
    if not fuzzy_enabled or fuzz_mod is None:
        return None
    if found_patterns:
        return None
    try:
        med_thr = int(medium_threshold)
    except (TypeError, ValueError):
        med_thr = 40
    med_thr = max(2, min(69, med_thr))
    eff_high = min(int(fuzzy_max_confidence), med_thr - 1)
    try:
        eff_low = int(fuzzy_min_confidence)
    except (TypeError, ValueError):
        eff_low = 25
    eff_low = max(0, min(100, eff_low))
    eff_high = max(0, min(100, eff_high))
    if eff_low > eff_high:
        return None
    cc = int(combined_confidence)
    if not (eff_low <= cc <= eff_high):
        return None
    col_key = _prepare_column_key(column_name)
    if len(col_key) < 3:
        return None
    try:
        min_ratio = int(fuzzy_min_ratio)
    except (TypeError, ValueError):
        min_ratio = 85
    min_ratio = max(50, min(100, min_ratio))
    best_score = 0
    seen: set[str] = set()
    for term in sensitive_terms:
        ts = (term or "").strip().lower()
        if len(ts) < 2 or ts in seen:
            continue
        seen.add(ts)
        sc = best_fuzzy_score(col_key, ts, fuzz_mod)
        if sc > best_score:
            best_score = sc
    if best_score < min_ratio:
        return None
    return (
        "MEDIUM",
        FUZZY_COLUMN_MATCH_PATTERN,
        FUZZY_COLUMN_MATCH_NORM_TAG,
        cc,
    )
