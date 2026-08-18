"""Tests for dialect-safe encoding_stress rows in populate_poc_database (#1007)."""

from __future__ import annotations

from scripts.populate_poc_database import DBConfig, _encoding_stress_null_term_row


def test_null_term_row_postgres_uses_visible_escape_not_literal_nul() -> None:
    cfg = DBConfig("postgres", "localhost", 5432, "poc", "u", "p")
    content, note = _encoding_stress_null_term_row(cfg)
    assert "\x00" not in content
    assert "\\x00" in content
    assert "postgres" in note.lower()


def test_null_term_row_mariadb_keeps_literal_nul() -> None:
    cfg = DBConfig("mariadb", "localhost", 3306, "poc", "u", "p")
    content, note = _encoding_stress_null_term_row(cfg)
    assert "\x00" in content
    assert "CPF\x00" in content
    assert note == "null-terminated C-style string"
