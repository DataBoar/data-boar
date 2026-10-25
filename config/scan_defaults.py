"""
Scan-related defaults shared by the config loader and engine.

``file_scan.sample_limit`` is still used for **row-style** sampling (SQLite-as-DB per column,
Power BI / Dataverse TOPN, etc.). Plain-text file reads use ``file_sample_max_chars`` so
cifra/lyric/Markdown heuristics see enough bytes without fetching thousands of SQL rows.
"""

from __future__ import annotations

# UTF-8 characters read for .txt/.md/… via ``_read_text_sample`` (filesystem and shares).
DEFAULT_FILE_SAMPLE_MAX_CHARS = 12_000
MIN_FILE_SAMPLE_MAX_CHARS = 256
MAX_FILE_SAMPLE_MAX_CHARS = 500_000


def clamp_file_sample_max_chars(
    raw: object, *, default: int = DEFAULT_FILE_SAMPLE_MAX_CHARS
) -> int:
    """Clamp ``file_sample_max_chars`` to a safe range; invalid values → *default*."""
    try:
        n = int(raw)
    except (TypeError, ValueError):
        n = int(default)
    return max(MIN_FILE_SAMPLE_MAX_CHARS, min(MAX_FILE_SAMPLE_MAX_CHARS, n))
