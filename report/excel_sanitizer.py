"""Shared XLSX sanitization helpers to prevent Excel formula injection (CWE-1236)."""

from __future__ import annotations

from typing import Any

import pandas as pd

FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def excel_sanitize_cell(value: object) -> object:
    """Prefix formula-like string values so Excel/openpyxl treat them as literal text."""
    if isinstance(value, str) and value.startswith(FORMULA_PREFIXES):
        return "'" + value
    return value


def excel_safe_dataframe(data: Any) -> pd.DataFrame:
    """Build DataFrame with every cell sanitized against formula execution."""
    df = pd.DataFrame(data)
    return df.map(excel_sanitize_cell)
