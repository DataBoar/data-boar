"""Tests for aggregated identification risk: category mapping, aggregation rule, and report sheet/recommendation."""

import unittest
from pathlib import Path

from core.aggregated_identification import (
    map_finding_to_categories,
    run_aggregation,
    QUASI_IDENTIFIER_CATEGORIES,
)
from core.database import LocalDBManager
from report.generator import generate_report


class TestCategoryMapping(unittest.TestCase):
    """Unit tests for map_finding_to_categories."""

    def test_column_name_maps_to_category(self):
        self.assertIn(
            "gender",
            map_finding_to_categories(
                {"column_name": "gender", "pattern_detected": ""}
            ),
        )
        self.assertIn(
            "job_position",
            map_finding_to_categories(
                {"column_name": "department", "pattern_detected": ""}
            ),
        )
        self.assertIn(
            "health",
            map_finding_to_categories(
                {"column_name": "health_status", "pattern_detected": ""}
            ),
        )
        self.assertIn(
            "address",
            map_finding_to_categories(
                {"column_name": "user_address", "pattern_detected": ""}
            ),
        )
        self.assertIn(
            "phone",
            map_finding_to_categories(
                {"column_name": "telefone", "pattern_detected": ""}
            ),
        )

    def test_phone_column_names_multilingual(self):
        """Phone category: multiple naming schemes and languages (home phone, mobile, celular, téléphone, etc.)."""
        phone_columns = [
            "phone",
            "telefone",
            "celular",
            "mobile",
            "fone",
            "home_phone",
            "home phone",
            "work_phone",
            "work phone",
            "cell_phone",
            "cell phone",
            "contact_number",
            "phone_number",
            "téléphone",
            "teléfono",
            "telefono",
            "móvil",
            "cel",
            "handy",
            "handynummer",
            "mobilnummer",
            "telefon",
            "contato",
            "contact",
        ]
        for col in phone_columns:
            with self.subTest(column=col):
                cats = map_finding_to_categories(
                    {"column_name": col, "pattern_detected": ""}
                )
                self.assertIn(
                    "phone", cats, f"Column '{col}' should map to category 'phone'"
                )

    def test_name_column_names_multilingual(self):
        """Name/identifier category (other): multiple naming schemes and languages (first name, surname, apellido, etc.)."""
        name_columns = [
            "first name",
            "first_name",
            "last name",
            "last_name",
            "surname",
            "full name",
            "full_name",
            "birth name",
            "nickname",
            "given name",
            "family name",
            "middle name",
            "nome",
            "sobrenome",
            "nome completo",
            "nombre",
            "apellido",
            "nombre completo",
            "prénom",
            "nom de famille",
            "nom complet",
            "vorname",
            "nachname",
            "geburtsname",
            "familienname",
            "cognome",
        ]
        for col in name_columns:
            with self.subTest(column=col):
                cats = map_finding_to_categories(
                    {"column_name": col, "pattern_detected": ""}
                )
                self.assertIn(
                    "other", cats, f"Column '{col}' should map to category 'other'"
                )

    def test_id_document_column_names_multilingual(self):
        """ID/document columns (passport, ctps, documento oficial, green card, etc.) map to category 'other'."""
        id_columns = [
            "passaporte",
            "passport",
            "ctps",
            "carteira de trabalho",
            "documento oficial",
            "official document",
            "distintivo",
            "pis",
            "cartão cidadão",
            "certidão",
            "green card",
            "registro no conselho de classe",
            "cnh",
            "driver license",
            "documento de identidade",
            "identity document",
            "id card",
            "national id",
            "document number",
            "carte d'identité",
            "cpf",
            "rg",
            "identidade",
        ]
        for col in id_columns:
            with self.subTest(column=col):
                cats = map_finding_to_categories(
                    {"column_name": col, "pattern_detected": ""}
                )
                self.assertIn(
                    "other", cats, f"Column '{col}' should map to category 'other'"
                )

    def test_pattern_detected_maps_to_category(self):
        self.assertIn(
            "phone",
            map_finding_to_categories(
                {"column_name": "x", "pattern_detected": "PHONE_BR"}
            ),
        )
        self.assertIn(
            "other",
            map_finding_to_categories(
                {"column_name": "x", "pattern_detected": "EMAIL"}
            ),
        )
        self.assertIn(
            "other",
            map_finding_to_categories(
                {"column_name": "x", "pattern_detected": "PII_AMBIGUOUS"}
            ),
        )

    def test_file_name_used_for_filesystem(self):
        cats = map_finding_to_categories(
            {"file_name": "contacts_phone.csv", "pattern_detected": ""}
        )
        self.assertIn("phone", cats)

    def test_config_mapping_override(self):
        mapping = [
            {"column_pattern": "custom_gender", "category": "gender"},
            {"pattern_detected": "CPF", "category": "other"},
        ]
        r = {"column_name": "custom_gender", "pattern_detected": "CPF"}
        cats = map_finding_to_categories(r, mapping)
        self.assertIn("gender", cats)
        self.assertIn("other", cats)

    def test_returns_subset_of_quasi_categories(self):
        for cat in QUASI_IDENTIFIER_CATEGORIES:
            self.assertIsInstance(cat, str)
        r = {"column_name": "gender", "pattern_detected": "PHONE_BR"}
        cats = map_finding_to_categories(r, None)
        self.assertTrue(cats.issubset(set(QUASI_IDENTIFIER_CATEGORIES)))


class TestRunAggregation(unittest.TestCase):
    """Unit tests for run_aggregation."""

    def test_same_table_two_categories_above_threshold(self):
        db_rows = [
            {
                "target_name": "T1",
                "schema_name": "public",
                "table_name": "users",
                "column_name": "gender",
                "pattern_detected": "",
            },
            {
                "target_name": "T1",
                "schema_name": "public",
                "table_name": "users",
                "column_name": "department",
                "pattern_detected": "",
            },
        ]
        records = run_aggregation(
            db_rows,
            [],
            "sess1",
            {
                "detection": {
                    "aggregated_identification_enabled": True,
                    "aggregated_min_categories": 2,
                }
            },
        )
        self.assertEqual(len(records), 1)
        self.assertIn("gender", records[0]["categories"])
        self.assertIn("job_position", records[0]["categories"])
        self.assertEqual(records[0]["source_type"], "database")
        self.assertIn("users", records[0]["table_or_file"])

    def test_same_table_one_category_below_threshold(self):
        db_rows = [
            {
                "target_name": "T1",
                "schema_name": "",
                "table_name": "t",
                "column_name": "gender",
                "pattern_detected": "",
            },
        ]
        records = run_aggregation(
            db_rows, [], "sess1", {"detection": {"aggregated_min_categories": 2}}
        )
        self.assertEqual(len(records), 0)

    def test_disabled_returns_empty(self):
        db_rows = [
            {
                "target_name": "T1",
                "schema_name": "",
                "table_name": "t",
                "column_name": "gender",
                "pattern_detected": "",
            },
            {
                "target_name": "T1",
                "schema_name": "",
                "table_name": "t",
                "column_name": "phone",
                "pattern_detected": "PHONE_BR",
            },
        ]
        records = run_aggregation(
            db_rows,
            [],
            "sess1",
            {"detection": {"aggregated_identification_enabled": False}},
        )
        self.assertEqual(len(records), 0)

    def test_filesystem_grouping(self):
        fs_rows = [
            {
                "target_name": "FS1",
                "path": "/data",
                "file_name": "contacts.csv",
                "column_name": "",
                "pattern_detected": "PHONE_BR",
            },
            {
                "target_name": "FS1",
                "path": "/data",
                "file_name": "contacts.csv",
                "column_name": "",
                "pattern_detected": "EMAIL",
            },
        ]
        records = run_aggregation(
            [], fs_rows, "sess1", {"detection": {"aggregated_min_categories": 2}}
        )
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["source_type"], "filesystem")
        self.assertIn("contacts.csv", records[0]["table_or_file"])

    def test_medium_pii_ambiguous_counts_toward_aggregation(self):
        """
        C9: MEDIUM + PII_AMBIGUOUS should still map to category 'other' and count
        toward aggregated_min_categories with another category in the same group.
        """
        db_rows = [
            {
                "target_name": "T1",
                "schema_name": "public",
                "table_name": "users",
                "column_name": "document_id",
                "pattern_detected": "PII_AMBIGUOUS",
                "sensitivity_level": "MEDIUM",
            },
            {
                "target_name": "T1",
                "schema_name": "public",
                "table_name": "users",
                "column_name": "telefone",
                "pattern_detected": "PHONE_BR",
                "sensitivity_level": "MEDIUM",
            },
        ]
        records = run_aggregation(
            db_rows,
            [],
            "sess1",
            {
                "detection": {
                    "aggregated_identification_enabled": True,
                    "aggregated_min_categories": 2,
                }
            },
        )
        self.assertEqual(len(records), 1)
        cats = set(str(records[0]["categories"]).split(", "))
        self.assertIn("other", cats)
        self.assertIn("phone", cats)

    def test_incomplete_data_mode_lowers_threshold_by_one(self):
        db_rows = [
            {
                "target_name": "T1",
                "schema_name": "public",
                "table_name": "users",
                "column_name": "gender",
                "pattern_detected": "",
                "sensitivity_level": "MEDIUM",
            }
        ]
        # Default threshold 2 -> no row
        records_default = run_aggregation(
            db_rows, [], "sess1", {"detection": {"aggregated_min_categories": 2}}
        )
        self.assertEqual(len(records_default), 0)
        # Incomplete mode lowers effective threshold to 1 -> row appears
        records_incomplete = run_aggregation(
            db_rows,
            [],
            "sess1",
            {
                "detection": {
                    "aggregated_min_categories": 2,
                    "aggregated_incomplete_data_mode": True,
                }
            },
        )
        self.assertEqual(len(records_incomplete), 1)
        self.assertIn(
            "incomplete-data mode", records_incomplete[0]["explanation"].lower()
        )

    def test_single_high_risk_health_suggested_review_mode(self):
        db_rows = [
            {
                "target_name": "T1",
                "schema_name": "public",
                "table_name": "clinical",
                "column_name": "health_status",
                "pattern_detected": "",
                "sensitivity_level": "HIGH",
            }
        ]
        # With min_categories=2, single category would normally not be emitted.
        records = run_aggregation(
            db_rows,
            [],
            "sess1",
            {
                "detection": {
                    "aggregated_min_categories": 2,
                    "aggregated_single_high_risk_suggested_review": True,
                }
            },
        )
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["sensitivity_level"], "MEDIUM")
        self.assertIn("Single high-risk category", records[0]["explanation"])


def test_report_contains_aggregated_sheet_and_recommendation(tmp_path):
    """Generate report with DB findings that trigger aggregation; sheet and recommendation must exist."""
    db_path = str(tmp_path / "agg.db")
    out_dir = str(tmp_path / "out")
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    mgr = LocalDBManager(db_path)
    try:
        mgr.set_current_session_id("agg-sess")
        mgr.create_session_record("agg-sess")
        mgr.save_finding(
            "database",
            target_name="DB1",
            schema_name="public",
            table_name="staff",
            column_name="gender",
            sensitivity_level="MEDIUM",
            pattern_detected="TEXT",
            norm_tag="",
            ml_confidence=0,
        )
        mgr.save_finding(
            "database",
            target_name="DB1",
            schema_name="public",
            table_name="staff",
            column_name="department",
            sensitivity_level="MEDIUM",
            pattern_detected="TEXT",
            norm_tag="",
            ml_confidence=0,
        )
        mgr.save_finding(
            "database",
            target_name="DB1",
            schema_name="public",
            table_name="staff",
            column_name="health",
            sensitivity_level="HIGH",
            pattern_detected="TEXT",
            norm_tag="",
            ml_confidence=0,
        )
        mgr.finish_session("agg-sess")
        config = {
            "detection": {
                "aggregated_identification_enabled": True,
                "aggregated_min_categories": 2,
            }
        }
        path = generate_report(mgr, "agg-sess", output_dir=out_dir, config=config)
        assert path is not None
        import pandas as pd

        with pd.ExcelFile(path) as xl:
            assert "Cross-ref data – ident. risk" in xl.sheet_names
            df_agg = pd.read_excel(xl, sheet_name="Cross-ref data – ident. risk")
            # First row is the sample/coverage disclaimer; at least one aggregated data row follows.
            assert len(df_agg) >= 2
            assert (
                "Sample / coverage note" in str(df_agg.iloc[0].get("Target", ""))
                or "sampled scanning"
                in str(df_agg.iloc[0].get("Explanation", "")).lower()
            )
            assert (
                "Target" in df_agg.columns
                and "Categories" in df_agg.columns
                and "Explanation" in df_agg.columns
            )
            recs = pd.read_excel(xl, sheet_name="Recommendations")
        agg_rec = recs[
            recs["Data / Pattern"]
            .astype(str)
            .str.contains("AGGREGATED_IDENTIFICATION", na=False)
        ]
        assert len(agg_rec) >= 1
        assert "LGPD" in str(agg_rec.iloc[0]["Base legal"]) or "GDPR" in str(
            agg_rec.iloc[0]["Base legal"]
        )
    finally:
        mgr.dispose()
