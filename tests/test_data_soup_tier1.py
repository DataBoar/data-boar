"""Tier-1 data soup extractors and optional stego hints (filesystem connector helpers)."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest

from connectors.data_soup_formats import sample_epub_text
from connectors.filesystem_connector import _read_text_sample
from connectors.stego_hint import build_stego_hint_text


def test_sample_epub_text_extracts_from_xhtml(tmp_path: Path) -> None:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(
            "OEBPS/chapter1.xhtml",
            '<?xml version="1.0"?><html xmlns="http://www.w3.org/1999/xhtml">'
            "<body><p>SecretProjectCode ALPHA-7749</p></body></html>",
        )
    epub_path = tmp_path / "book.epub"
    epub_path.write_bytes(buf.getvalue())
    text = sample_epub_text(epub_path, 5000)
    assert "SecretProjectCode" in text
    assert "ALPHA-7749" in text


def test_read_text_sample_epub_via_connector(tmp_path: Path) -> None:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(
            "OEBPS/chap.xhtml",
            '<?xml version="1.0"?><html xmlns="http://www.w3.org/1999/xhtml">'
            "<body><p>PII-TEST-EMAIL test@example.com</p></body></html>",
        )
    p = tmp_path / "sample.epub"
    p.write_bytes(buf.getvalue())
    out = _read_text_sample(p, ".epub", 8000, {})
    assert "test@example.com" in out


def test_stego_hint_on_png(tmp_path: Path) -> None:
    # Minimal 1x1 PNG (89 bytes standard)
    png = (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
        b"\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    p = tmp_path / "x.png"
    p.write_bytes(png)
    hint = build_stego_hint_text(p, ".png")
    assert "stego_hint" in hint
    assert "sample_entropy" in hint


def test_read_text_sample_stego_appends_for_png(tmp_path: Path) -> None:
    png = (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
        b"\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    p = tmp_path / "y.png"
    p.write_bytes(png)
    out = _read_text_sample(p, ".png", 8000, {}, scan_for_stego=True)
    assert "stego_hint" in out


def test_sample_parquet_when_pyarrow_available(tmp_path: Path) -> None:
    pa = pytest.importorskip("pyarrow")
    import pyarrow.parquet as pq  # type: ignore[import-untyped]

    table = pa.table({"col_a": [1, 2], "name": ["alice", "bob"]})
    path = tmp_path / "t.parquet"
    pq.write_table(table, path)
    from connectors.data_soup_formats import sample_parquet_text

    text = sample_parquet_text(path, 4000)
    assert "col_a" in text or "alice" in text
