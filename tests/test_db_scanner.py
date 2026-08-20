"""NameError / F821 fix for legacy DatabaseScanner helpers (#703).

This module is still a stub scanner (hardcoded tables/samples). Tests cover
the corrected method contracts only — not production SQL connectors.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from scanners.db_scanner import DatabaseScanner


def _scanner() -> DatabaseScanner:
    return DatabaseScanner({})


def test_check_sensitivity_id_from_table_name() -> None:
    scanner = _scanner()
    assert (
        scanner._check_sensitivity("plain text", "VARCHAR", "documents", "name") == "ID"
    )


def test_check_sensitivity_id_from_column_name() -> None:
    scanner = _scanner()
    assert (
        scanner._check_sensitivity("plain text", "VARCHAR", "users", "document_number")
        == "ID"
    )


def test_check_sensitivity_secret_from_data_type() -> None:
    scanner = _scanner()
    assert scanner._check_sensitivity("x", "PASSWORD_HASH", "users", "hash") == "Secret"


def test_check_sensitivity_pii_from_email_sample() -> None:
    scanner = _scanner()
    assert (
        scanner._check_sensitivity("user@example.com", "VARCHAR", "users", "email")
        == "PII"
    )


def test_check_sensitivity_general_when_no_signal() -> None:
    scanner = _scanner()
    assert scanner._check_sensitivity("hello", "TEXT", "notes", "body") == "General"


def test_save_audit_record_returns_dict_without_nameerror() -> None:
    scanner = _scanner()
    record = scanner._save_audit_record(
        "users", "email", "VARCHAR", "PII", "user@example.com"
    )
    assert record["table_name"] == "users"
    assert record["column_name"] == "email"
    assert record["sensitivity_level"] == "PII"
    assert "scan_date" in record["metadata"]


def test_scan_database_appends_returned_records() -> None:
    scanner = _scanner()
    scanner.logger = MagicMock()
    scanner._get_column_sample = MagicMock(return_value="plain text")
    results: list = []
    scanner._scan_database("unused", results)
    assert results
    assert all("table_name" in row and "column_name" in row for row in results)
    docs = [row for row in results if row["table_name"] == "documents"]
    assert docs
    assert all(row["sensitivity_level"] == "ID" for row in docs)
    numbered = [row for row in results if "number" in row["column_name"].lower()]
    assert numbered
    assert all(row["sensitivity_level"] == "ID" for row in numbered)
