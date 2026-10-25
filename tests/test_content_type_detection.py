from __future__ import annotations

from pathlib import Path

from core.content_type import infer_content_type


def test_infer_pdf_from_bytes_literal() -> None:
    header = b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n"
    assert infer_content_type(header) == "pdf"


def test_infer_zip_from_bytes_literal() -> None:
    # Minimal ZIP local file header magic; payload does not need to be valid.
    header = b"PK\x03\x04" + b"\x00" * 28
    assert infer_content_type(header) == "zip"


def test_infer_text_from_bytes_literal() -> None:
    header = b"Hello, world!\nThis looks like plain text.\n"
    assert infer_content_type(header) == "text"


def test_infer_unknown_from_bytes_literal() -> None:
    header = b"\x00\x01\x02\x03\x04\x05\x06\x07"
    assert infer_content_type(header) is None


def test_infer_from_temporary_pdf_file(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample_renamed_as_txt.txt"
    pdf_path.write_bytes(b"%PDF-1.4\n%mock\n")
    assert infer_content_type(pdf_path) == "pdf"
