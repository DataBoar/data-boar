"""
Content-based type detection helper (magic bytes and simple heuristics).

Step 1 for PLAN_CONTENT_TYPE_AND_CLOAKING_DETECTION: provide a lightweight helper
that infers an internal content-type label (e.g. 'pdf', 'zip', 'text') from the
first bytes of a file or a bytes buffer. Wired into filesystem/share scanning when
``file_scan.use_content_type`` is true (PDF slice and rich-media remapping).
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

from core.archives import read_magic, is_zip_magic


ContentType = (
    str  # alias for clarity; values are small internal labels, not full MIME strings
)


def _infer_from_bytes(data: bytes, filename: str | None = None) -> ContentType | None:
    """
    Infer a simple content-type label from magic bytes and basic heuristics.

    Returns one of: 'pdf', 'zip', 'text', or None when unknown.
    """
    if not data:
        return None

    # PDF: starts with "%PDF-"
    if data.startswith(b"%PDF-"):
        return "pdf"

    # ZIP (including OOXML containers like .docx/.xlsx/.pptx)
    if is_zip_magic(data):
        return "zip"

    # Very simple "looks like text" heuristic: mostly printable ASCII + whitespace
    sample = data[:64]
    printable = sum(
        1
        for b in sample
        if 32 <= b <= 126 or b in (9, 10, 13)  # tab, LF, CR
    )
    if printable and printable / len(sample) > 0.9:
        return "text"

    return None


def infer_content_type(
    source: Union[Path, str, bytes, bytearray],
) -> ContentType | None:
    """
    Infer a simple content-type label from a file path or bytes buffer.

    - When a Path/str is provided, reads the first N bytes (default 64 via read_magic)
      and infers type from magic bytes and heuristics.
    - When bytes/bytearray are provided, infers directly from the buffer.

    Returns one of: 'pdf', 'zip', 'text', or None when unknown.
    """
    if isinstance(source, (bytes, bytearray)):
        return _infer_from_bytes(bytes(source))

    path = Path(source)
    data = read_magic(path, n=64)
    return _infer_from_bytes(data, filename=str(path))


def choose_effective_pdf_extension(
    ext: str,
    use_content_type: bool,
    source: Union[Path, str, bytes, bytearray],
) -> str:
    """
    Decide which extension to use for extraction for the narrow PDF-only slice.

    - When use_content_type is false or ext is already '.pdf', return ext unchanged.
    - Otherwise, call infer_content_type(source); when it yields 'pdf', return '.pdf',
      else return the original ext.

    This helper is intentionally small so connectors (filesystem and shares) can share
    the same behaviour and tests without touching network code.
    """

    if not use_content_type or ext == ".pdf":
        return ext
    try:
        label = infer_content_type(source)
    except Exception:
        return ext
    if label == "pdf":
        return ".pdf"
    return ext


def choose_effective_rich_media_extension(
    ext: str,
    use_content_type: bool,
    source: Union[Path, str, bytes, bytearray],
) -> str:
    """
    If the path's extension is not already a known image/audio/video suffix but magic bytes
    match a rich-media container, return that suffix so ``_read_text_sample`` uses the right branch.
    """
    if not use_content_type:
        return ext
    ext_l = (ext or "").lower()
    from core.rich_media_magic import (
        RICH_MEDIA_SCAN_EXTENSIONS,
        infer_rich_media_suffix_from_source,
    )

    if ext_l in RICH_MEDIA_SCAN_EXTENSIONS:
        return ext
    try:
        inferred = infer_rich_media_suffix_from_source(source)
    except Exception:
        return ext
    return inferred if inferred else ext
