"""
Regression guards: entertainment / low-PII context vs ML-only HIGH.

**Why this module exists:** Clone-tree and music-folder scans used to yield many rows with
``HIGH`` + ``ML_DETECTED`` and ~99% ``ml_confidence`` on README/lyrics/cifra-like content.
The detector caps ML-only highs in that context to ``MEDIUM`` + ``ML_POTENTIAL_ENTERTAINMENT``
with reported confidence ≤ 55 (or ``MEDIUM`` + ``ML_POTENTIAL`` when post-penalty score
stays below 70). **Never** ``HIGH`` + ``ML_DETECTED`` for those paths.

**Determinism:** Two tests patch ``RandomForestClassifier.predict_proba`` to simulate ~100%
sensitive probability so we always exercise the ``>= 70`` branch after the entertainment
``-25`` penalty, without depending on TF-IDF + RF noise from tiny training sets.

**Gate:** Full pytest is run by ``scripts/check-all.ps1`` (``pre-commit-and-tests.ps1``); CI
runs the same suite. No separate registration needed.

**ReDoS / CodeQL:** ``TestChordLikeTokenizerRedosRegression`` guards the chord tokenizer
(``py/redos``, CWE-1333). It runs **without** the ML stack so CI never skips it when
``sklearn`` is absent.
"""

from __future__ import annotations

import ast
import inspect
import time
import unittest
from unittest.mock import patch

import numpy as np

from core import detector as detector_module
from core.detector import (
    _chord_like_token_count,
    _looks_like_lyrics,
    _looks_like_music_tab,
)
from core.scanner import DataScanner

# Minimal terms so a real vectorizer + RF exist; ML score comes from the patch below.
_MIN_ML_TERMS: list[dict[str, str]] = [
    {"text": "sensitive_token_xyz", "label": "sensitive"},
    {"text": "neutral_plain", "label": "non_sensitive"},
]


def _almost_certain_sensitive_proba(_X) -> np.ndarray:
    """Binary classifier: class index 1 = sensitive (~100%)."""
    return np.array([[0.001, 0.999]], dtype=float)


class TestChordLikeTokenizerRedosRegression(unittest.TestCase):
    """
    Prevent CodeQL ``py/redos`` regression on chord-like line heuristics.

    Do **not** fold these into ``TestDetectorEntertainmentRegression``: that class skips the
    whole case when sklearn is missing, and the tokenizer must stay covered everywhere.
    """

    def test_chord_token_count_stays_fast_on_codeql_poison_tail(self) -> None:
        """CodeQL example: input shaped like ``a`` + many ``m7`` must not blow up matching."""
        poison = "a" + ("m7" * 800)
        t0 = time.perf_counter()
        _chord_like_token_count(poison)
        elapsed = time.perf_counter() - t0
        self.assertLess(
            elapsed,
            0.2,
            f"chord token scan should stay linear (took {elapsed:.3f}s)",
        )

    def test_chord_token_count_stays_fast_on_maj_prefix_ambiguity_tail(self) -> None:
        """Extra tail: ``A`` + repeated ``maj7`` fragments (historically ambiguous with ``m``)."""
        poison = "A" + ("maj7" * 400)
        t0 = time.perf_counter()
        _chord_like_token_count(poison)
        self.assertLess(time.perf_counter() - t0, 0.2)

    def test_chord_like_token_count_golden_cifra_lines(self) -> None:
        """Stable counts for real cifra spellings (regression if lexer is tightened wrong)."""
        self.assertEqual(_chord_like_token_count("C    G    Am   F"), 4)
        self.assertEqual(_chord_like_token_count("C    D2sus9    EM7    Am"), 4)
        self.assertEqual(_chord_like_token_count("Dm7  G7   C"), 3)
        # Slash bass: lexer counts the bass letter as a second root (still chord-heavy line).
        self.assertEqual(_chord_like_token_count("G/B"), 2)
        self.assertEqual(_chord_like_token_count("F#m7  Bb"), 2)

    def test_chord_like_token_count_implementation_avoids_findall_redos_shape(
        self,
    ) -> None:
        """AST guard: no ``re.findall(...)`` in the tokenizer (docstring may mention the word)."""
        src = inspect.getsource(detector_module._chord_like_token_count)
        tree = ast.parse(src)
        bad_lines: list[int] = []

        class _FindReFindall(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> None:
                func = node.func
                if isinstance(func, ast.Attribute) and func.attr == "findall":
                    if isinstance(func.value, ast.Name) and func.value.id == "re":
                        bad_lines.append(getattr(node, "lineno", 0))
                self.generic_visit(node)

        _FindReFindall().visit(tree)
        self.assertEqual(
            bad_lines,
            [],
            f"Do not use re.findall in _chord_like_token_count (py/redos); found at lines {bad_lines}",
        )
        self.assertIn("_consume_chord_token", src)
        atoms = getattr(detector_module, "_CHORD_SUFFIX_ATOMS", None)
        self.assertIsInstance(
            atoms,
            tuple,
            "Keep module-level _CHORD_SUFFIX_ATOMS for auditable linear suffix matching.",
        )
        self.assertGreater(
            len(atoms), 5, "Suffix atom table should cover major chord families."
        )


class TestDetectorEntertainmentRegression(unittest.TestCase):
    """Contract: ML-only highs in entertainment/OSS-doc context must not be HIGH + ML_DETECTED."""

    def setUp(self) -> None:
        self.scanner = DataScanner(ml_terms_inline=_MIN_ML_TERMS)
        if not getattr(self.scanner.detector, "_model", None):
            self.skipTest("sklearn ML stack not available")

    def test_patched_high_ml_in_lyrics_is_medium_ml_potential_entertainment(
        self,
    ) -> None:
        lyrics = """Verse 1
This line has sensitive_token_xyz in it
Chorus
La la la la la"""
        with patch.object(
            self.scanner.detector._model,
            "predict_proba",
            side_effect=_almost_certain_sensitive_proba,
        ):
            result = self.scanner.scan_column("song_lyrics", lyrics)
        self.assertEqual(result["sensitivity_level"], "MEDIUM")
        self.assertEqual(result["pattern_detected"], "ML_POTENTIAL_ENTERTAINMENT")
        self.assertLessEqual(result["ml_confidence"], 55)
        self.assertNotIn("ML_DETECTED", result["pattern_detected"])

    def test_patched_high_ml_readme_short_sample_one_heading_entertainment(
        self,
    ) -> None:
        """Filesystem-sized chunks: one # line + short body must still trigger OSS Markdown context."""
        body = (
            "# Data Boar\n\n"
            "Short readme sample for scan; fewer than two headings in this chunk only.\n"
        )
        assert len(body.strip()) >= 60
        with patch.object(
            self.scanner.detector._model,
            "predict_proba",
            side_effect=_almost_certain_sensitive_proba,
        ):
            result = self.scanner.scan_file_content(body, "README.md")
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["sensitivity_level"], "MEDIUM")
        self.assertEqual(result["pattern_detected"], "ML_POTENTIAL_ENTERTAINMENT")
        self.assertLessEqual(result["ml_confidence"], 55)

    def test_patched_high_ml_subtitle_srt_path_entertainment(self) -> None:
        """Sidecar .srt path + dialogue text → ML-only HIGH capped (patched proba)."""
        body = "\n".join(
            f"Cue line {i} with sensitive_token_xyz mention" for i in range(10)
        )
        with patch.object(
            self.scanner.detector._model,
            "predict_proba",
            side_effect=_almost_certain_sensitive_proba,
        ):
            result = self.scanner.scan_file_content(body, "movie.pt_BR.srt")
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["sensitivity_level"], "MEDIUM")
        self.assertEqual(result["pattern_detected"], "ML_POTENTIAL_ENTERTAINMENT")
        self.assertLessEqual(result["ml_confidence"], 55)

    def test_patched_high_ml_interleaved_cifra_mixed_case_chords_entertainment(
        self,
    ) -> None:
        """Alternating chord rows (C, D2sus9, EM7, Am, …) and lyric lines → entertainment context."""
        body = (
            "C    D2sus9    EM7    Am\n"
            "Maria called on Tuesday saying she would wait at the station downtown\n"
            "G    C    F    dm7\n"
            "Walking down the long avenue in the summer rain again tonight\n"
            "F    G    C\n"
            "The doctor said tomorrow never knows what sensitive_token_xyz meant anyway\n"
        )
        with patch.object(
            self.scanner.detector._model,
            "predict_proba",
            side_effect=_almost_certain_sensitive_proba,
        ):
            result = self.scanner.scan_file_content(body, "Song idea.txt")
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["sensitivity_level"], "MEDIUM")
        self.assertEqual(result["pattern_detected"], "ML_POTENTIAL_ENTERTAINMENT")
        self.assertLessEqual(result["ml_confidence"], 55)

    def test_patched_high_ml_in_contributing_md_is_medium_ml_potential_entertainment(
        self,
    ) -> None:
        body = """# Contributing

## How to report
Use the issue tracker. sensitive_token_xyz is internal jargon.

## Code style
Run tests before PR.
"""
        with patch.object(
            self.scanner.detector._model,
            "predict_proba",
            side_effect=_almost_certain_sensitive_proba,
        ):
            result = self.scanner.scan_file_content(body, "CONTRIBUTING.md")
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["sensitivity_level"], "MEDIUM")
        self.assertEqual(result["pattern_detected"], "ML_POTENTIAL_ENTERTAINMENT")
        self.assertLessEqual(result["ml_confidence"], 55)
        self.assertNotEqual(result["pattern_detected"], "ML_DETECTED")

    def test_never_high_ml_detected_for_chord_grid_cifra_pattern(self) -> None:
        """Chord-only lines (cifra) must stay out of HIGH + ML_DETECTED when ML fires alone."""
        scanner = DataScanner()
        cifra = """intro
C    G    Am   F
C    G    Am   F
Dm7  G7   C
"""
        result = scanner.scan_column("partitura", cifra)
        if result["sensitivity_level"] == "HIGH" and "ML_DETECTED" in result.get(
            "pattern_detected", ""
        ):
            self.fail(
                "Regression: cifra-like grid must not yield HIGH + ML_DETECTED "
                "(entertainment heuristics should cap ML-only path)"
            )
        self.assertIn(result["sensitivity_level"], ("LOW", "MEDIUM"))


class TestLooksLikeLyricsShortFieldCsv(unittest.TestCase):
    """CSV/TSV with short fields must not trip the lyrics short-line heuristic (#395)."""

    _CSV_SAMPLE = (
        "id,name,amount\n"
        "1,user_a,100\n"
        "2,user_b,200\n"
        "3,user_c,300\n"
        "4,user_d,150\n"
        "5,user_e,250"
    )

    def test_short_field_csv_is_not_lyrics(self) -> None:
        self.assertFalse(_looks_like_lyrics(self._CSV_SAMPLE))
        self.assertFalse(_looks_like_music_tab(self._CSV_SAMPLE))

    def test_short_field_semicolon_and_tsv_are_not_lyrics(self) -> None:
        semi = self._CSV_SAMPLE.replace(",", ";")
        tsv = self._CSV_SAMPLE.replace(",", "\t")
        self.assertFalse(_looks_like_lyrics(semi))
        self.assertFalse(_looks_like_lyrics(tsv))

    def test_short_lyric_lines_without_delimiters_still_match(self) -> None:
        lyrics = "\n".join(
            (
                "walking home at night",
                "the rain begins again",
                "wait for me downtown",
                "lights along the river",
                "nobody on the platform",
            )
        )
        self.assertTrue(_looks_like_lyrics(lyrics))

    def test_csv_with_weak_date_pattern_stays_high_not_lyrics_context(self) -> None:
        csv_dates = (
            "id,event_date,amount\n"
            "1,31/12/2024,100\n"
            "2,01/01/2025,200\n"
            "3,15/06/2024,300\n"
            "4,20/07/2024,150\n"
            "5,08/08/2024,250"
        )
        result = DataScanner().scan_column("events.csv", csv_dates)
        self.assertEqual(result["sensitivity_level"], "HIGH")
        self.assertIn("DATE_DMY", result.get("pattern_detected") or "")
        self.assertNotIn("lyrics/tabs context", result.get("pattern_detected") or "")


if __name__ == "__main__":
    unittest.main()
