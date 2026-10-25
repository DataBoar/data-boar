"""Plan §4: optional connector CHAR/VARCHAR length hint → MEDIUM FORMAT_LENGTH_HINT_ID."""

import unittest

from core.detector import (
    SensitivityDetector,
    _declared_type_email_length_hint,
    _declared_type_is_integer_like,
    _format_length_suggests_id_column,
    _parse_declared_char_length,
)


class TestParseDeclaredCharLength(unittest.TestCase):
    def test_variants(self):
        self.assertEqual(_parse_declared_char_length("VARCHAR(11)"), 11)
        self.assertEqual(_parse_declared_char_length("character varying(14)"), 14)
        self.assertEqual(_parse_declared_char_length("CHAR(9)"), 9)
        self.assertIsNone(_parse_declared_char_length("INT"))
        self.assertIsNone(_parse_declared_char_length(None))
        self.assertIsNone(_parse_declared_char_length(""))


class TestFormatLengthSuggestsId(unittest.TestCase):
    def test_cpf_and_id_suffix(self):
        self.assertTrue(_format_length_suggests_id_column("user_cpf", 11))
        self.assertTrue(_format_length_suggests_id_column("external_id", 11))
        self.assertFalse(_format_length_suggests_id_column("description", 11))

    def test_cnpj(self):
        self.assertTrue(_format_length_suggests_id_column("company_cnpj", 14))
        self.assertTrue(_format_length_suggests_id_column("tax_registration_id", 14))

    def test_ssn(self):
        self.assertTrue(_format_length_suggests_id_column("employee_ssn", 9))
        self.assertFalse(_format_length_suggests_id_column("status_code", 9))

    def test_uuid_lengths(self):
        self.assertTrue(_format_length_suggests_id_column("request_uuid", 36))
        self.assertTrue(_format_length_suggests_id_column("correlation_guid", 36))
        self.assertTrue(
            _format_length_suggests_id_column("external_uniqueidentifier", 36)
        )
        self.assertTrue(_format_length_suggests_id_column("row_guid", 32))
        self.assertFalse(_format_length_suggests_id_column("description", 36))
        self.assertFalse(_format_length_suggests_id_column("notes", 32))


class TestDeclaredTypeHelpers(unittest.TestCase):
    def test_integer_like(self):
        self.assertTrue(_declared_type_is_integer_like("INT"))
        self.assertTrue(_declared_type_is_integer_like("BIGINT"))
        self.assertTrue(_declared_type_is_integer_like("NUMERIC(20,0)"))
        self.assertFalse(_declared_type_is_integer_like("NUMERIC(20,2)"))
        self.assertFalse(_declared_type_is_integer_like("VARCHAR(20)"))

    def test_email_len_hint(self):
        self.assertEqual(_declared_type_email_length_hint("VARCHAR(128)"), 128)
        self.assertEqual(_declared_type_email_length_hint("VARCHAR(191)"), 191)
        self.assertEqual(_declared_type_email_length_hint("VARCHAR(254)"), 254)
        self.assertEqual(_declared_type_email_length_hint("CHAR(255)"), 255)
        self.assertEqual(_declared_type_email_length_hint("VARCHAR(256)"), 256)
        self.assertEqual(
            _declared_type_email_length_hint("character varying(320)"), 320
        )
        self.assertIsNone(_declared_type_email_length_hint("VARCHAR(200)"))
        self.assertIsNone(_declared_type_email_length_hint("INT"))


def _neutral_sample_text() -> str:
    """Push ML/DL confidence down so ID-like column names do not alone trigger HIGH."""
    return " ".join(["item_count"] * 20)


class TestDetectorFormatHintIntegration(unittest.TestCase):
    def test_disabled_no_effect(self):
        d = SensitivityDetector(detection_config={})
        level, pat, _, _ = d.analyze(
            "external_id",
            _neutral_sample_text(),
            connector_data_type="VARCHAR(11)",
        )
        self.assertEqual(level, "LOW")
        self.assertEqual(pat, "GENERAL")

    def test_enabled_low_to_medium(self):
        d = SensitivityDetector(detection_config={"connector_format_id_hint": True})
        level, pat, norm, conf = d.analyze(
            "external_id",
            _neutral_sample_text(),
            connector_data_type="VARCHAR(11)",
        )
        self.assertEqual(level, "MEDIUM")
        self.assertEqual(pat, "FORMAT_LENGTH_HINT_ID")
        self.assertIn("Schema", norm)
        self.assertGreaterEqual(conf, 40)

    def test_enabled_integer_id_hint(self):
        d = SensitivityDetector(detection_config={"connector_format_id_hint": True})
        level, pat, norm, conf = d.analyze(
            "customer_id",
            _neutral_sample_text(),
            connector_data_type="BIGINT",
        )
        self.assertEqual(level, "MEDIUM")
        self.assertEqual(pat, "FORMAT_TYPE_HINT_ID_INT")
        self.assertIn("integer", norm)
        self.assertGreaterEqual(conf, 40)

    def test_enabled_email_length_hint(self):
        d = SensitivityDetector(detection_config={"connector_format_id_hint": True})
        level, pat, norm, conf = d.analyze(
            "contact_email",
            _neutral_sample_text(),
            connector_data_type="VARCHAR(254)",
        )
        self.assertEqual(level, "MEDIUM")
        self.assertEqual(pat, "FORMAT_LENGTH_HINT_EMAIL")
        self.assertIn("email", norm.lower())
        self.assertGreaterEqual(conf, 40)

    def test_enabled_email_length_hint_191_utf8mb4_common(self):
        d = SensitivityDetector(detection_config={"connector_format_id_hint": True})
        level, pat, _, _ = d.analyze(
            "user_email",
            _neutral_sample_text(),
            connector_data_type="VARCHAR(191)",
        )
        self.assertEqual(level, "MEDIUM")
        self.assertEqual(pat, "FORMAT_LENGTH_HINT_EMAIL")

    def test_enabled_uuid_varchar_36(self):
        d = SensitivityDetector(detection_config={"connector_format_id_hint": True})
        level, pat, _, _ = d.analyze(
            "entity_uuid",
            _neutral_sample_text(),
            connector_data_type="VARCHAR(36)",
        )
        self.assertEqual(level, "MEDIUM")
        self.assertEqual(pat, "FORMAT_LENGTH_HINT_ID")


if __name__ == "__main__":
    unittest.main()
