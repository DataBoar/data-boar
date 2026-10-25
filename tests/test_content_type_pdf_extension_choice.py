from __future__ import annotations

from pathlib import Path

from core.content_type import choose_effective_pdf_extension


def test_choose_effective_pdf_extension_no_change_when_flag_disabled() -> None:
    data = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    assert (
        choose_effective_pdf_extension(".txt", use_content_type=False, source=data)
        == ".txt"
    )


def test_choose_effective_pdf_extension_no_change_when_already_pdf() -> None:
    data = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    assert (
        choose_effective_pdf_extension(".pdf", use_content_type=True, source=data)
        == ".pdf"
    )


def test_choose_effective_pdf_extension_switches_to_pdf_for_pdf_header_bytes() -> None:
    data = b"%PDF-1.7\n%mock\n"
    assert (
        choose_effective_pdf_extension(".txt", use_content_type=True, source=data)
        == ".pdf"
    )


def test_choose_effective_pdf_extension_does_not_switch_for_non_pdf_content(
    tmp_path: Path,
) -> None:
    path = tmp_path / "not_pdf.txt"
    path.write_bytes(b"\x00\x01\x02\x03")
    assert (
        choose_effective_pdf_extension(".txt", use_content_type=True, source=path)
        == ".txt"
    )
