"""Excel formula injection guards in report/generator.py (CWE-1236)."""

from report.generator import (
    _excel_safe_dataframe,
    _excel_sanitize_cell,
)


def test_formula_prefix_eq_is_escaped() -> None:
    assert _excel_sanitize_cell('=HYPERLINK("http://evil.example","click")') == (
        '\'=HYPERLINK("http://evil.example","click")'
    )


def test_formula_prefix_plus_is_escaped() -> None:
    assert _excel_sanitize_cell("+1+1") == "'+1+1"


def test_formula_prefix_at_is_escaped() -> None:
    assert _excel_sanitize_cell("@SUM(A1:A2)") == "'@SUM(A1:A2)"


def test_normal_string_unchanged() -> None:
    assert _excel_sanitize_cell("column_name") == "column_name"
    assert _excel_sanitize_cell("CPF 123.456.789-00") == "CPF 123.456.789-00"


def test_sample_content_with_formula_is_escaped() -> None:
    row = {"column_name": "=cmd|' /C calc'!A0", "sample_value": "+evil"}
    df = _excel_safe_dataframe([row])
    assert df.iloc[0]["column_name"].startswith("'=")
    assert df.iloc[0]["sample_value"].startswith("'+")


def test_numeric_and_none_unchanged() -> None:
    assert _excel_sanitize_cell(42) == 42
    assert _excel_sanitize_cell(None) is None
