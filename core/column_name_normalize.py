"""
Optional normalization of **column names** before ML/DL scoring only.

Regex and minor-detection heuristics still use the **original** column name so behaviour
for pattern matching stays predictable. When enabled via config, ML/DL see a folded,
separator-normalized form (accents removed, `_`/`-`/`.` → space) to reduce false negatives
on inflected or accented names (e.g. ``téléphone`` vs training term ``telefone``).

See PLAN_ADDITIONAL_DETECTION_TECHNIQUES_AND_FN_REDUCTION.md (priority 2).
"""

from __future__ import annotations

import re
import unicodedata

# Collapse repeated separators/spaces after fold.
_SPACE_RE = re.compile(r"\s+")
_SEP_RE = re.compile(r"[\s_\-\.]+")


def fold_accents(text: str) -> str:
    """Decompose Unicode (NFKD) and strip combining characters (e.g. é → e)."""
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def normalize_column_name_for_ml(column_name: str) -> str:
    """
    Normalize column name for TF-IDF / embedding input only.

    - Accent folding (NFKD + strip marks)
    - Lowercase
    - Underscores, hyphens, dots → space; collapse whitespace
    """
    raw = (column_name or "").strip()
    if not raw:
        return ""
    folded = fold_accents(raw)
    spaced = _SEP_RE.sub(" ", folded.lower())
    return _SPACE_RE.sub(" ", spaced).strip()
