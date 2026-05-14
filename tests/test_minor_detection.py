"""
Tests for possible minor data detection (DOB/age heuristic).
Covers EN and PT-BR column names, acronyms (DOB, DDN, NASC, idade), date formats (DMY, YMD),
and numeric age; ensures DOB_POSSIBLE_MINOR and LGPD Art. 14 / GDPR Art. 8 appear when appropriate
and are not set for adults or non-DOB/age columns.
"""

import tempfile
import unittest
from pathlib import Path

from config.loader import load_config
from core.detector import SensitivityDetector, _detect_possible_minor
from core.engine import AuditEngine
from core.scanner import DataScanner


class TestMinorDetectionHeuristic(unittest.TestCase):
    """Unit tests for _detect_possible_minor (column name + sample → possible minor)."""

    def test_age_like_column_with_minor_age_returns_true(self):
        self.assertTrue(_detect_possible_minor("idade", "17", 18))
        self.assertTrue(_detect_possible_minor("age", "0", 18))
        self.assertTrue(_detect_possible_minor("idade_atual", "15", 18))

    def test_age_like_column_with_adult_age_returns_false(self):
        self.assertFalse(_detect_possible_minor("idade", "25", 18))
        self.assertFalse(_detect_possible_minor("age", "18", 18))
        self.assertFalse(_detect_possible_minor("idade", "30", 18))

    def test_dob_like_column_with_minor_birth_date_returns_true(self):
        # Use a recent birth date so age is always < 18 regardless of test run year
        self.assertTrue(_detect_possible_minor("data de nascimento", "01/01/2022", 18))
        self.assertTrue(_detect_possible_minor("dob", "2015-06-15", 18))
        self.assertTrue(_detect_possible_minor("ddn", "15/03/2012", 18))
        self.assertTrue(_detect_possible_minor("nascimento", "01/01/2020", 18))

    def test_dob_like_column_with_adult_birth_date_returns_false(self):
        self.assertFalse(_detect_possible_minor("data de nascimento", "01/01/1990", 18))
        self.assertFalse(_detect_possible_minor("dob", "1985-01-01", 18))
        self.assertFalse(_detect_possible_minor("birth date", "15/03/1995", 18))

    def test_non_dob_age_column_ignores_minor_value(self):
        # "17" in sample but column name does not suggest age/DOB → not minor
        self.assertFalse(_detect_possible_minor("item_count", "17", 18))
        self.assertFalse(_detect_possible_minor("quantity", "5", 18))
        self.assertFalse(_detect_possible_minor("other_column", "01/01/2022", 18))

    def test_custom_threshold(self):
        self.assertTrue(_detect_possible_minor("idade", "20", 21))
        self.assertFalse(_detect_possible_minor("idade", "20", 18))


class TestMinorDetectionViaScanner(unittest.TestCase):
    """Integration tests: DataScanner returns HIGH + DOB_POSSIBLE_MINOR and LGPD Art. 14 when appropriate."""

    def test_idade_with_17_returns_high_and_possible_minor_marker(self):
        scanner = DataScanner()
        result = scanner.scan_column("idade", "17")
        self.assertEqual(result["sensitivity_level"], "HIGH")
        self.assertIn("DOB_POSSIBLE_MINOR", result["pattern_detected"])
        self.assertIn("LGPD Art. 14", result["norm_tag"])
        self.assertIn("GDPR Art. 8", result["norm_tag"])

    def test_data_de_nascimento_with_minor_date_returns_high_and_possible_minor(self):
        scanner = DataScanner()
        # Birth date that yields age < 18 regardless of current year
        result = scanner.scan_column("data de nascimento", "01/01/2022")
        self.assertEqual(result["sensitivity_level"], "HIGH")
        self.assertIn("DOB_POSSIBLE_MINOR", result["pattern_detected"])
        self.assertIn("LGPD Art. 14", result["norm_tag"])

    def test_dob_acronym_with_minor_date_returns_possible_minor(self):
        scanner = DataScanner()
        result = scanner.scan_column("dob", "2015-01-01")
        self.assertEqual(result["sensitivity_level"], "HIGH")
        self.assertIn("DOB_POSSIBLE_MINOR", result["pattern_detected"])

    def test_age_with_adult_value_no_possible_minor_marker(self):
        scanner = DataScanner()
        result = scanner.scan_column("age", "25")
        # Should not be tagged as possible minor (adult age)
        self.assertNotIn("DOB_POSSIBLE_MINOR", result.get("pattern_detected", ""))

    def test_dob_with_adult_birth_date_no_possible_minor_marker(self):
        scanner = DataScanner()
        result = scanner.scan_column("dob", "01/01/1990")
        self.assertNotIn("DOB_POSSIBLE_MINOR", result.get("pattern_detected", ""))

    def test_unrelated_column_with_number_no_minor_marker(self):
        scanner = DataScanner()
        result = scanner.scan_column("quantity", "17")
        self.assertNotIn("DOB_POSSIBLE_MINOR", result.get("pattern_detected", ""))


class TestMinorDetectionConfigWiring(unittest.TestCase):
    """Config detection.minor_age_threshold is passed to the detector and affects minor detection."""

    def test_custom_threshold_via_scanner_marks_20_as_minor_when_threshold_21(self):
        scanner = DataScanner(detection_config={"minor_age_threshold": 21})
        result = scanner.scan_column("idade", "20")
        self.assertEqual(result["sensitivity_level"], "HIGH")
        self.assertIn("DOB_POSSIBLE_MINOR", result["pattern_detected"])

    def test_default_threshold_does_not_mark_20_as_minor(self):
        scanner = DataScanner()
        result = scanner.scan_column("idade", "20")
        self.assertNotIn("DOB_POSSIBLE_MINOR", result.get("pattern_detected", ""))

    def test_custom_threshold_passed_to_detector(self):
        detector = SensitivityDetector(detection_config={"minor_age_threshold": 25})
        level, pattern, norm, _ = detector.analyze("age", "24")
        self.assertEqual(level, "HIGH")
        self.assertIn("DOB_POSSIBLE_MINOR", pattern)


class TestMinorThresholdFromExternalConfigFile(unittest.TestCase):
    """Threshold is configurable via external config file (YAML); default 18 when section missing."""

    def test_threshold_from_config_file_applied_to_engine(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config_path = tmp_path / "config_minor.yaml"
            config_path.write_text(
                "targets: []\n"
                "report:\n  output_dir: .\n"
                "sqlite_path: audit_minor_test.db\n"
                "detection:\n  minor_age_threshold: 21\n",
                encoding="utf-8",
            )
            config = load_config(config_path)
            self.assertEqual(config.get("detection", {}).get("minor_age_threshold"), 21)
            engine = AuditEngine(config, db_path=str(tmp_path / "audit_minor_test.db"))
            self.assertEqual(engine.scanner.detector._minor_age_threshold, 21)

    def test_default_threshold_18_when_detection_section_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config_path = tmp_path / "config_no_detection.yaml"
            config_path.write_text(
                "targets: []\nreport:\n  output_dir: .\nsqlite_path: audit_default.db\n",
                encoding="utf-8",
            )
            config = load_config(config_path)
            self.assertEqual(config.get("detection", {}).get("minor_age_threshold"), 18)
            engine = AuditEngine(config, db_path=str(tmp_path / "audit_default.db"))
            self.assertEqual(engine.scanner.detector._minor_age_threshold, 18)


class TestMinorDetectionDoesNotBreakExisting(unittest.TestCase):
    """Ensure minor detection is additive: existing behaviour for non-minor data unchanged."""

    def test_cpf_still_high(self):
        # Placeholder updated to a checksum-valid CPF (G-13-11 strict mode).
        # Goal of the test is unchanged: a CPF still scored HIGH and labeled
        # with "CPF" in pattern_detected (regex branch, not ML fallback).
        scanner = DataScanner()
        result = scanner.scan_column("documento", "123.456.789-09")
        self.assertEqual(result["sensitivity_level"], "HIGH")
        self.assertIn("CPF", result.get("pattern_detected", ""))

    def test_low_sensitivity_unchanged(self):
        scanner = DataScanner()
        result = scanner.scan_column("item_count", "42")
        # With many sensitive ML terms (ID, document, etc.), model may occasionally return MEDIUM; must not be HIGH.
        self.assertIn(result["sensitivity_level"], ("LOW", "MEDIUM"))
        self.assertNotEqual(result["sensitivity_level"], "HIGH")

    def test_scan_column_shape_unchanged(self):
        scanner = DataScanner()
        result = scanner.scan_column("idade", "17")
        self.assertIn("sensitivity_level", result)
        self.assertIn("pattern_detected", result)
        self.assertIn("norm_tag", result)
        self.assertIn("ml_confidence", result)


if __name__ == "__main__":
    unittest.main()
