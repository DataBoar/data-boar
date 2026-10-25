"""
Optional embedding-prototype semantic hint for FN reduction (Plan priority 5).

This module is intentionally pure/side-effect-free so behavior can be tested
without sentence-transformers installed.
"""

from __future__ import annotations

EMBEDDING_PROTOTYPE_HINT_PATTERN = "EMBEDDING_PROTOTYPE_HINT"
EMBEDDING_PROTOTYPE_HINT_NORM = (
    "Semantic embedding similarity suggests sensitive data; confirm manually"
)


def try_embedding_prototype_elevation(
    *,
    combined_confidence: int,
    found_patterns: list[tuple[str, str]],
    medium_threshold: int,
    hint_enabled: bool,
    hint_min_confidence: int,
    hint_max_confidence: int,
    hint_min_similarity: int,
    similarity_score: int | None,
) -> tuple[str, str, str, int] | None:
    """
    Optional MEDIUM elevation using similarity to a sensitive embedding prototype.

    This hint only runs in the borderline band below MEDIUM to avoid overriding
    stronger detector paths.
    """
    if not hint_enabled:
        return None
    if found_patterns:
        return None
    if similarity_score is None:
        return None

    eff_max = min(hint_max_confidence, medium_threshold - 1)
    if combined_confidence < hint_min_confidence or combined_confidence > eff_max:
        return None
    if similarity_score < hint_min_similarity:
        return None
    return (
        "MEDIUM",
        EMBEDDING_PROTOTYPE_HINT_PATTERN,
        EMBEDDING_PROTOTYPE_HINT_NORM,
        combined_confidence,
    )
