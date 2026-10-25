"""Unit tests for magic-byte inference of image/audio/video containers (cloaking)."""

import tempfile
from pathlib import Path

import pytest

from core.content_type import choose_effective_rich_media_extension
from core.rich_media_magic import (
    IMAGE_EXTENSIONS,
    infer_rich_media_suffix,
    infer_rich_media_suffix_from_source,
)


@pytest.mark.parametrize(
    "prefix,expected",
    [
        (b"\xff\xd8\xff\xe0", ".jpg"),
        (b"\x89PNG\r\n\x1a\n\x00\x00\x00", ".png"),
        (b"GIF89a" + b"\x00" * 20, ".gif"),
        (b"BM" + b"\x00" * 30, ".bmp"),
        (b"II*\x00" + b"\x00" * 20, ".tif"),
        (b"MM\x00*" + b"\x00" * 20, ".tif"),
        (b"RIFF" + b"\x00\x00\x00\x00" + b"WEBP", ".webp"),
        (b"ID3\x04\x00\x00" + b"\x00" * 20, ".mp3"),
        (b"fLaC" + b"\x00" * 20, ".flac"),
        (b"OggS" + b"\x00" * 20, ".ogg"),
        (b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 10, ".mp4"),
    ],
)
def test_infer_rich_media_suffix(prefix: bytes, expected: str) -> None:
    assert infer_rich_media_suffix(prefix + b"\x00" * 64) == expected


def test_infer_rich_media_suffix_too_short() -> None:
    assert infer_rich_media_suffix(b"\xff\xd8") is None


def test_infer_rich_media_suffix_from_path_writes_file() -> None:
    data = b"\xff\xd8\xff\xe0" + b"\x00" * 100
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        f.write(data)
        p = Path(f.name)
    try:
        assert infer_rich_media_suffix_from_source(p) == ".jpg"
    finally:
        p.unlink(missing_ok=True)


def test_choose_effective_rich_media_extension_remaps_txt() -> None:
    data = b"\xff\xd8\xff\xe0" + b"\x00" * 100
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        f.write(data)
        p = Path(f.name)
    try:
        assert choose_effective_rich_media_extension(".txt", False, p) == ".txt"
        assert choose_effective_rich_media_extension(".txt", True, p) == ".jpg"
        assert choose_effective_rich_media_extension(".jpg", True, p) == ".jpg"
    finally:
        p.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# HEIC / HEIF - iPhone default photo format
# ---------------------------------------------------------------------------


def test_heic_in_image_extensions() -> None:
    """HEIC and HEIF must be part of IMAGE_EXTENSIONS so they enter the image pipeline."""
    assert ".heic" in IMAGE_EXTENSIONS
    assert ".heif" in IMAGE_EXTENSIONS


@pytest.mark.parametrize(
    "brand,expected",
    [
        (b"heic", ".heic"),
        (b"heis", ".heic"),
        (b"heim", ".heic"),
        (b"heix", ".heic"),
        (b"mif1", ".heic"),
        (b"msf1", ".heic"),
        (b"hevc", ".heic"),
        (b"hevx", ".heic"),
        (b"avif", ".heic"),
        (b"avis", ".heic"),
    ],
)
def test_heic_brand_detection(brand: bytes, expected: str) -> None:
    """All documented HEIC/HEIF/AVIF brands must route to .heic, not .mp4."""
    # ISO BMFF ftyp box: 4-byte size | "ftyp" | 4-byte brand | ...
    data = b"\x00\x00\x00\x18" + b"ftyp" + brand + b"\x00" * 20
    assert infer_rich_media_suffix(data) == expected


def test_mp4_brand_not_confused_with_heic() -> None:
    """Generic video brands must still route to .mp4 after the HEIC fix."""
    for brand in (b"mp42", b"isom", b"M4V ", b"M4A "):
        data = b"\x00\x00\x00\x18" + b"ftyp" + brand + b"\x00" * 20
        assert infer_rich_media_suffix(data) == ".mp4", f"brand {brand!r} mis-routed"


def test_heic_disguised_as_non_media_extension_remapped() -> None:
    """A HEIC file with a generic extension (.dat) must be remapped to .heic.

    Note: a HEIC file named .jpeg is intentionally NOT remapped at the extension layer —
    .jpeg is already a recognised image extension and goes through the image pipeline.
    pillow-heif registers a PIL opener so Image.open() handles the HEIC payload
    transparently regardless of whether the extension says .jpeg or .heic.
    """
    heic_magic = b"\x00\x00\x00\x18" + b"ftyp" + b"heic" + b"\x00" * 100
    with tempfile.NamedTemporaryFile(suffix=".dat", delete=False) as f:
        f.write(heic_magic)
        p = Path(f.name)
    try:
        # Without content-type: .dat stays .dat
        assert choose_effective_rich_media_extension(".dat", False, p) == ".dat"
        # With content-type: magic bytes reveal HEIC -> remapped to .heic
        result = choose_effective_rich_media_extension(".dat", True, p)
        assert result == ".heic", f"expected .heic, got {result!r}"
    finally:
        p.unlink(missing_ok=True)


def test_heic_disguised_as_jpeg_stays_jpeg_extension() -> None:
    """A HEIC file named .jpeg keeps its extension — .jpeg is already an image extension.

    PIL opens the HEIC payload transparently when pillow-heif is installed.
    This test documents the design decision: extension-level remapping is only for
    non-media extensions, not for same-category format mismatches.
    """
    heic_magic = b"\x00\x00\x00\x18" + b"ftyp" + b"heic" + b"\x00" * 100
    with tempfile.NamedTemporaryFile(suffix=".jpeg", delete=False) as f:
        f.write(heic_magic)
        p = Path(f.name)
    try:
        # .jpeg is already in IMAGE_EXTENSIONS, so no remapping occurs either way.
        assert choose_effective_rich_media_extension(".jpeg", False, p) == ".jpeg"
        assert choose_effective_rich_media_extension(".jpeg", True, p) == ".jpeg"
    finally:
        p.unlink(missing_ok=True)
