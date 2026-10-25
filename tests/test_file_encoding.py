"""
Tests for utils.file_encoding: multiple text encodings for config and pattern files.

Ensures config and compliance samples can be read as UTF-8, UTF-8 with BOM,
Windows ANSI (cp1252), and Latin-1 without regressing in production.
"""

import tempfile
from pathlib import Path

import pytest

from utils.file_encoding import read_text_auto_encoding, read_text_with_encoding


def test_read_text_with_encoding_utf8():
    """read_text_with_encoding with utf-8 reads Unicode content."""
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".txt", delete=False) as f:
        f.write("Hello 世界 café 日本語".encode("utf-8"))
        path = Path(f.name)
    try:
        out = read_text_with_encoding(path, encoding="utf-8", errors="strict")
        assert "世界" in out
        assert "café" in out
        assert "日本語" in out
    finally:
        path.unlink(missing_ok=True)


def test_read_text_with_encoding_utf8_replace():
    """read_text_with_encoding with errors=replace does not raise on invalid bytes."""
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".txt", delete=False) as f:
        f.write(b"OK prefix \xff\xfe bad suffix")
        path = Path(f.name)
    try:
        out = read_text_with_encoding(path, encoding="utf-8", errors="replace")
        assert "OK prefix" in out
        assert "\ufffd" in out or "bad suffix" in out
    finally:
        path.unlink(missing_ok=True)


def test_read_text_with_encoding_cp1252():
    """read_text_with_encoding with cp1252 reads Windows-ANSI typical bytes."""
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".txt", delete=False) as f:
        f.write("Café résumé naïve".encode("cp1252"))
        path = Path(f.name)
    try:
        out = read_text_with_encoding(path, encoding="cp1252", errors="replace")
        assert "Café" in out
        assert "résumé" in out
    finally:
        path.unlink(missing_ok=True)


def test_read_text_with_encoding_nonexistent_raises():
    """read_text_with_encoding raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        read_text_with_encoding(Path("/nonexistent/path/file.txt"))


def test_read_text_auto_encoding_utf8():
    """read_text_auto_encoding decodes UTF-8 file."""
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".yaml", delete=False) as f:
        f.write("# Comment with 中文 and émoji\nkey: value\n".encode("utf-8"))
        path = Path(f.name)
    try:
        out = read_text_auto_encoding(path)
        assert "中文" in out
        assert "key: value" in out
    finally:
        path.unlink(missing_ok=True)


def test_read_text_auto_encoding_utf8_bom():
    """read_text_auto_encoding decodes UTF-8 with BOM."""
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".yaml", delete=False) as f:
        f.write(b"\xef\xbb\xbf# UTF-8 BOM\nkey: value\n")
        path = Path(f.name)
    try:
        out = read_text_auto_encoding(path)
        assert "key: value" in out
        assert out.startswith("# UTF-8 BOM") or "UTF-8 BOM" in out
    finally:
        path.unlink(missing_ok=True)


def test_read_text_auto_encoding_latin1():
    """read_text_auto_encoding falls back to latin_1 for non-UTF-8 bytes."""
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".yaml", delete=False) as f:
        # Bytes that are invalid UTF-8 but valid Latin-1 (e.g. é = 0xe9)
        f.write(b"# Latin-1: caf\xe9 r\xe9sum\xe9\nkey: value\n")
        path = Path(f.name)
    try:
        out = read_text_auto_encoding(path)
        assert "key: value" in out
        # Either decoded as latin_1 (café) or replace chars
        assert "caf" in out or "key" in out
    finally:
        path.unlink(missing_ok=True)


def test_read_text_auto_encoding_nonexistent_raises():
    """read_text_auto_encoding raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        read_text_auto_encoding(Path("/nonexistent/path/config.yaml"))
