"""Test for Rust stage pattern order determinism (#2246).

The Rust regex stage returns hits in arbitrary set order, but the Python branch
iterates patterns in definition order. This test verifies that the Rust branch
emits hits in the same order as the detector's definition order.
"""

from __future__ import annotations

import unittest
from core.detector import SensitivityDetector


class ReverseOrderSet(set[str]):
    """A set whose iterator yields items in reverse order of insertion.

    Used to simulate that Rust hits come back in reverse definition order.
    """

    def __init__(self, items: list[str], definition_order: list[str]) -> None:
        super().__init__(items)
        self._definition_order = definition_order

    def __iter__(self):
        # Yields items in the order they appear in definition_order, filtered
        # to only those in the set (simulating Rust returning them in reverse)
        return (name for name in reversed(self._definition_order) if name in self)


class FakeRustStage:
    """A fake rust stage for testing order behavior."""

    def __init__(
        self,
        rust_pattern_names: set[str],
        python_fallback_names: set[str],
        match_result: tuple[set[str], bool],
    ) -> None:
        self.rust_pattern_names = rust_pattern_names
        self.python_fallback_names = python_fallback_names
        self._match_result = match_result

    def match_names(self, text: str) -> tuple[set[str], bool]:
        return self._match_result


class TestRustStageOrder(unittest.TestCase):
    """Verify pattern order matches definition order in Rust stage."""

    def setUp(self) -> None:
        # Create a detector with known patterns in specific order
        # Using a subset of DEFAULT_PATTERNS for clean test
        self.test_patterns = {
            "PATTERN_ALPHA": (r"\balpha\b", "NormAlpha"),
            "PATTERN_BETA": (r"\bbeta\b", "NormBeta"),
            "PATTERN_GAMMA": (r"\bgamma\b", "NormGamma"),
            "PATTERN_DELTA": (r"\bdelta\b", "NormDelta"),
            "PATTERN_EPSILON": (r"\bepsilon\b", "NormEpsilon"),
        }

        # Text that matches patterns alpha, gamma, and epsilon
        self.test_text = "alpha gamma epsilon"

        # Expected order based on definition order (alpha, gamma, epsilon)
        self.expected_names = ["PATTERN_ALPHA", "PATTERN_GAMMA", "PATTERN_EPSILON"]

    def _create_detector_with_patterns(
        self, patterns: dict[str, tuple[str, str]]
    ) -> SensitivityDetector:
        """Create a detector with the given patterns and no Rust stage."""
        detector = object.__new__(SensitivityDetector)
        detector.patterns = patterns
        detector._compiled = {
            name: __import__("re", fromlist=["re"]).compile(pat)
            for name, (pat, _) in patterns.items()
        }
        detector._rust_stage = None
        detector._rust_ok = True
        # Initialize other required attributes
        detector._pattern_validators = {}
        detector._rust_ok = True
        return detector

    def test_rust_stage_order_matches_definition_order(self) -> None:
        """Rust stage must return hits in definition order, not arbitrary set order.

        This test FAILS before the fix because Rust returns hits as a set
        with arbitrary iteration order.
        """
        # Create detector with test patterns
        detector = self._create_detector_with_patterns(self.test_patterns)

        # Create a fake rust stage that returns hits in reverse order
        # (simulating the bug where set iteration is arbitrary)
        reverse_hits = ReverseOrderSet(
            self.expected_names, list(self.test_patterns.keys())
        )
        fake_rust_stage = FakeRustStage(
            rust_pattern_names=set(self.test_patterns.keys()),
            python_fallback_names=set(),
            match_result=(reverse_hits, True),  # rust_ok = True
        )
        detector._rust_stage = fake_rust_stage

        # Call the method under test
        result = detector._match_regex_patterns(self.test_text)

        # Extract just the names from the result
        result_names = [name for name, _ in result]

        # The order must match the definition order of patterns
        self.assertEqual(
            result_names,
            self.expected_names,
            f"Pattern order mismatch: got {result_names}, expected {self.expected_names}. "
            "Rust stage must iterate in definition order.",
        )

    def test_python_only_path_in_definition_order(self) -> None:
        """When rust_ok is False, python_only path must also be in definition order."""
        detector = self._create_detector_with_patterns(self.test_patterns)

        # Create a fake rust stage where rust_ok is False
        # In this case, all patterns go through python_only path
        all_names = set(self.test_patterns.keys())
        fake_rust_stage = FakeRustStage(
            rust_pattern_names=set(),  # empty since rust_ok is False
            python_fallback_names=all_names,
            match_result=(all_names, False),  # rust_ok = False
        )
        detector._rust_stage = fake_rust_stage

        # Call the method under test
        result = detector._match_regex_patterns(self.test_text)

        # Extract just the names from the result
        result_names = [name for name, _ in result]

        # Filter to only the patterns that actually match
        matching_names = [n for n in self.expected_names if n in all_names]

        self.assertEqual(
            result_names,
            matching_names,
            f"Python-only path order mismatch: got {result_names}, expected {matching_names}. "
            "Must iterate in definition order.",
        )

    def test_pure_python_path_matches_detection_order(self) -> None:
        """Pure Python path (no rust stage) should iterate in definition order."""
        detector = self._create_detector_with_patterns(self.test_patterns)
        detector._rust_stage = None  # Pure Python path

        result = detector._match_regex_patterns(self.test_text)
        result_names = [name for name, _ in result]

        self.assertEqual(
            result_names,
            self.expected_names,
            f"Python path order mismatch: got {result_names}, expected {self.expected_names}.",
        )


if __name__ == "__main__":
    unittest.main()
