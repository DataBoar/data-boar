"""
Tests for optional fuzzy column name matching (rapidfuzz).

Default config must match explicit fuzzy_column_match: false (no behaviour change).
Pure elevation logic is tested via try_fuzzy_elevation.
"""

from __future__ import annotations

import pytest

from core.detector import SensitivityDetector
from core.fuzzy_column_match import (
    FUZZY_COLUMN_MATCH_PATTERN,
    try_fuzzy_elevation,
)


@pytest.fixture(scope="module")
def rfuzz():
    pytest.importorskip("rapidfuzz")
    from rapidfuzz import fuzz

    return fuzz


def test_try_fuzzy_elevation_typo_column_similar_to_term(rfuzz):
    """Misspelled column name vs sensitive term 'email' in the confidence band."""
    mod = rfuzz
    r = try_fuzzy_elevation(
        column_name="emial_adres",
        combined_confidence=30,
        found_patterns=[],
        medium_threshold=40,
        fuzzy_enabled=True,
        fuzzy_min_confidence=25,
        fuzzy_max_confidence=45,
        fuzzy_min_ratio=78,
        sensitive_terms=["email", "telefone"],
        fuzz_mod=mod,
    )
    assert r is not None
    assert r[0] == "MEDIUM"
    assert r[1] == FUZZY_COLUMN_MATCH_PATTERN
    assert r[3] == 30


def test_try_fuzzy_elevation_no_match_below_ratio(rfuzz):
    mod = rfuzz
    r = try_fuzzy_elevation(
        column_name="xyz_random_q",
        combined_confidence=30,
        found_patterns=[],
        medium_threshold=40,
        fuzzy_enabled=True,
        fuzzy_min_confidence=25,
        fuzzy_max_confidence=45,
        fuzzy_min_ratio=95,
        sensitive_terms=["email"],
        fuzz_mod=mod,
    )
    assert r is None


def test_try_fuzzy_elevation_disabled():
    r = try_fuzzy_elevation(
        column_name="emial",
        combined_confidence=30,
        found_patterns=[],
        medium_threshold=40,
        fuzzy_enabled=False,
        fuzzy_min_confidence=25,
        fuzzy_max_confidence=45,
        fuzzy_min_ratio=70,
        sensitive_terms=["email"],
        fuzz_mod=None,
    )
    assert r is None


def test_try_fuzzy_elevation_skips_when_regex_hits(rfuzz):
    mod = rfuzz
    r = try_fuzzy_elevation(
        column_name="emial",
        combined_confidence=30,
        found_patterns=[("EMAIL", "tag")],
        medium_threshold=40,
        fuzzy_enabled=True,
        fuzzy_min_confidence=25,
        fuzzy_max_confidence=45,
        fuzzy_min_ratio=70,
        sensitive_terms=["email"],
        fuzz_mod=mod,
    )
    assert r is None


def test_try_fuzzy_elevation_band_respects_medium_threshold(rfuzz):
    """When ML would already be MEDIUM (>= med_thr), effective fuzzy max is med_thr - 1."""
    mod = rfuzz
    r = try_fuzzy_elevation(
        column_name="emial",
        combined_confidence=40,
        found_patterns=[],
        medium_threshold=40,
        fuzzy_enabled=True,
        fuzzy_min_confidence=25,
        fuzzy_max_confidence=45,
        fuzzy_min_ratio=70,
        sensitive_terms=["email"],
        fuzz_mod=mod,
    )
    assert r is None


def test_analyze_default_matches_explicit_fuzzy_false():
    """
    Off by default: identical results to explicitly disabling fuzzy_column_match.
    Covers a spread of column/sample pairs (regex, ML, LOW, ambiguous).
    """
    cases = [
        ("email_addr", "contact@test.invalid"),
        ("cpf", "000.000.000-00"),
        ("item_count", "42"),
        ("telefone", "user data"),
        ("document_id", "internal-ref-1"),
        ("lyrics", "verse one\nchorus line\n" * 8),
        ("full_name", "John Doe"),
    ]
    d0 = SensitivityDetector(detection_config={})
    d1 = SensitivityDetector(detection_config={"fuzzy_column_match": False})
    for col, sample in cases:
        assert d0.analyze(col, sample) == d1.analyze(col, sample), (
            f"mismatch for {col!r}"
        )


def test_analyze_fuzzy_true_without_rapidfuzz_same_as_false_when_library_missing(
    monkeypatch,
):
    """
    If rapidfuzz import fails, fuzzy_column_match: true must not change outcomes vs false.
    """
    import builtins

    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "rapidfuzz":
            raise ImportError("no rapidfuzz")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    col, sample = "emial_field", "nothing"
    d_on = SensitivityDetector(
        detection_config={"fuzzy_column_match": True, "medium_confidence_threshold": 40}
    )
    d_off = SensitivityDetector(
        detection_config={
            "fuzzy_column_match": False,
            "medium_confidence_threshold": 40,
        }
    )
    assert d_on.analyze(col, sample) == d_off.analyze(col, sample)


def test_recommendation_row_for_fuzzy_pattern():
    from report.generator import (
        _REC_DATA_PATTERN,
        _REC_PRIORIDADE,
        _recommendation_row_for_pattern,
    )

    row = _recommendation_row_for_pattern(
        "FUZZY_COLUMN_MATCH",
        "Possible personal data (fuzzy column name – confirm manually)",
    )
    assert row[_REC_DATA_PATTERN] == "FUZZY_COLUMN_MATCH"
    assert "MÉDIA" in str(row[_REC_PRIORIDADE])
