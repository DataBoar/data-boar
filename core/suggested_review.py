"""
False-negative reduction: ID-like column names that scored LOW.

When ``detection.persist_low_id_like_for_review`` is true, database/API-style connectors may persist
these columns with pattern ``SUGGESTED_REVIEW_ID_LIKE`` so the Excel report can list them
on the **Suggested review (LOW)** sheet without upgrading sensitivity (still LOW).

See docs/SENSITIVITY_DETECTION.md and PLAN_ADDITIONAL_DETECTION_TECHNIQUES_AND_FN_REDUCTION.md.
"""

from __future__ import annotations

import re

# Persisted / reported pattern name (stable for filters and tests).
SUGGESTED_REVIEW_PATTERN = "SUGGESTED_REVIEW_ID_LIKE"

# Keep <= 100 chars (database_findings.norm_tag column).
SUGGESTED_REVIEW_NORM_TAG = (
    "ID-like column name; confirm manually (suggested review / FN reduction)."
)

# Suffix-style hints on normalized column names (spaces → underscores).
_ID_LIKE_SUFFIX = re.compile(
    r"(?:_id|_uuid|_guid|_num|_number|_nr|_no)$",
    re.IGNORECASE,
)


def column_name_suggests_identifier_review(column_name: str) -> bool:
    """
    Return True if the column name looks like a generic identifier column worth human review.

    Heuristic: name ends with _id, _uuid, _guid, _num, _number, _nr, or _no (after
    normalizing spaces to underscores). Minimum length avoids trivial matches.
    """
    raw = (column_name or "").strip()
    if len(raw) < 4:
        return False
    normalized = raw.replace(" ", "_")
    return bool(_ID_LIKE_SUFFIX.search(normalized))


def augment_low_id_like_for_persist(
    result: dict,
    column_name: str,
    detection_config: dict | None,
) -> dict:
    """
    If result is LOW, ``detection.persist_low_id_like_for_review`` is true, and the column
    name looks ID-like, tag the finding for the **Suggested review (LOW)** sheet.

    Returns a new dict (or the same reference if unchanged). Sensitivity stays **LOW**;
    only ``pattern_detected`` / ``norm_tag`` are set so connectors can persist and the
    report can route rows to the dedicated sheet.
    """
    det = detection_config or {}
    if (result or {}).get("sensitivity_level") != "LOW":
        return result
    if not bool(det.get("persist_low_id_like_for_review", False)):
        return result
    if not column_name_suggests_identifier_review(column_name):
        return result
    return {
        **result,
        "pattern_detected": SUGGESTED_REVIEW_PATTERN,
        "norm_tag": SUGGESTED_REVIEW_NORM_TAG,
    }


def is_persisted_low_finding(result: dict) -> bool:
    """True if this row should be written to the DB (non-LOW or LOW suggested-review)."""
    if (result or {}).get("sensitivity_level") != "LOW":
        return True
    return (result or {}).get("pattern_detected") == SUGGESTED_REVIEW_PATTERN
