"""REST connector: JSON scalar -> connector_data_type for Plan §4 format hints."""

import unittest

from connectors.rest_connector import _flatten_sample, _scalar_to_connector_data_type


class TestScalarToConnectorDataType(unittest.TestCase):
    def test_int_bigint(self):
        self.assertEqual(_scalar_to_connector_data_type(42), "BIGINT")

    def test_bool_skipped(self):
        self.assertIsNone(_scalar_to_connector_data_type(True))

    def test_float_skipped(self):
        self.assertIsNone(_scalar_to_connector_data_type(1.5))

    def test_string_varchar(self):
        self.assertEqual(_scalar_to_connector_data_type("a" * 36), "VARCHAR(36)")

    def test_string_capped(self):
        s = "x" * 5000
        self.assertEqual(
            _scalar_to_connector_data_type(s, max_varchar=4000), "VARCHAR(4000)"
        )


class TestFlattenSampleRawScalars(unittest.TestCase):
    def test_dict_preserves_raw_for_connector_hint(self):
        rows = _flatten_sample({"user_id": 99, "email": "x@y.co"}, max_len=500)
        by_key = {k: (s, r) for k, s, r in rows}
        self.assertEqual(by_key["user_id"][1], 99)
        self.assertEqual(by_key["email"][1], "x@y.co")

    def test_nested_scalar(self):
        rows = _flatten_sample({"a": {"b": 1}}, max_len=500)
        self.assertEqual(len(rows), 1)
        k, s, r = rows[0]
        self.assertEqual(k, "a.b")
        self.assertEqual(r, 1)


if __name__ == "__main__":
    unittest.main()
