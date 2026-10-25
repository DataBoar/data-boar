"""
Plan §5: optional embedding-prototype semantic hint (borderline -> MEDIUM).
"""

from core.embedding_prototype_hint import (
    EMBEDDING_PROTOTYPE_HINT_PATTERN,
    try_embedding_prototype_elevation,
)


def test_embedding_hint_elevates_in_band_with_similarity():
    r = try_embedding_prototype_elevation(
        combined_confidence=30,
        found_patterns=[],
        medium_threshold=40,
        hint_enabled=True,
        hint_min_confidence=20,
        hint_max_confidence=39,
        hint_min_similarity=80,
        similarity_score=86,
    )
    assert r is not None
    assert r[0] == "MEDIUM"
    assert r[1] == EMBEDDING_PROTOTYPE_HINT_PATTERN
    assert r[3] == 30


def test_embedding_hint_skips_when_disabled():
    r = try_embedding_prototype_elevation(
        combined_confidence=30,
        found_patterns=[],
        medium_threshold=40,
        hint_enabled=False,
        hint_min_confidence=20,
        hint_max_confidence=39,
        hint_min_similarity=80,
        similarity_score=99,
    )
    assert r is None


def test_embedding_hint_skips_when_similarity_too_low():
    r = try_embedding_prototype_elevation(
        combined_confidence=30,
        found_patterns=[],
        medium_threshold=40,
        hint_enabled=True,
        hint_min_confidence=20,
        hint_max_confidence=39,
        hint_min_similarity=80,
        similarity_score=70,
    )
    assert r is None


def test_embedding_hint_respects_medium_threshold_band():
    # At MEDIUM threshold or higher, normal MEDIUM path should win; hint must skip.
    r = try_embedding_prototype_elevation(
        combined_confidence=40,
        found_patterns=[],
        medium_threshold=40,
        hint_enabled=True,
        hint_min_confidence=20,
        hint_max_confidence=45,
        hint_min_similarity=80,
        similarity_score=95,
    )
    assert r is None
