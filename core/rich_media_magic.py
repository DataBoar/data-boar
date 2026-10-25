"""
Magic-byte sniffing for common image, audio, and video containers.

Used with ``file_scan.use_content_type`` to treat renamed files (e.g. ``.txt`` hiding a ``.jpg``)
as rich media when scanning metadata or OCR is enabled.
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

from core.archives import read_magic

# All suffixes we might remap toward (must match connectors/rich_media_sample.py usage).
IMAGE_EXTENSIONS = frozenset(
    {
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".tif",
        ".tiff",
        ".webp",
        # Apple HEIF/HEIC - iPhone default photo format; needs pillow-heif for decoding.
        ".heic",
        ".heif",
    }
)
AUDIO_EXTENSIONS = frozenset(
    {
        ".mp3",
        ".flac",
        ".ogg",
        ".oga",
        ".opus",
        ".m4a",
        ".aac",
        ".wav",
        ".wma",
    }
)
VIDEO_EXTENSIONS = frozenset(
    {
        ".mp4",
        ".mkv",
        ".avi",
        ".mov",
        ".wmv",
        ".webm",
        ".mpeg",
        ".mpg",
        ".m4v",
    }
)
RICH_MEDIA_SCAN_EXTENSIONS = IMAGE_EXTENSIONS | AUDIO_EXTENSIONS | VIDEO_EXTENSIONS


def infer_rich_media_suffix(data: bytes) -> str | None:
    """
    Return a canonical suffix (including dot) such as ``.jpg``, or ``None``.
    """
    if not data or len(data) < 4:
        return None
    if data[:3] == b"\xff\xd8\xff":
        return ".jpg"
    if len(data) >= 8 and data[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    if len(data) >= 6 and data[:6] in (b"GIF87a", b"GIF89a"):
        return ".gif"
    if data[:2] == b"BM":
        return ".bmp"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    if data[:4] in (b"II*\x00", b"MM\x00*"):
        return ".tif"
    if data[:3] == b"ID3":
        return ".mp3"
    if len(data) >= 4 and data[:4] == b"fLaC":
        return ".flac"
    if len(data) >= 4 and data[:4] == b"OggS":
        return ".ogg"
    if len(data) >= 12 and data[4:8] == b"ftyp":
        # ISO Base Media File Format: brand in bytes 8-11 distinguishes HEIC from video.
        # HEIC/HEIF brands: heic heis heim heix mif1 msf1 hevc hevx avif avis
        brand = data[8:12]
        _HEIC_BRANDS = frozenset(
            b"heic heis heim heix mif1 msf1 hevc hevx avif avis".split()
        )
        if brand in _HEIC_BRANDS:
            return ".heic"
        return ".mp4"
    return None


def infer_rich_media_suffix_from_source(
    source: Union[Path, str, bytes, bytearray],
) -> str | None:
    if isinstance(source, (bytes, bytearray)):
        return infer_rich_media_suffix(bytes(source[:64]))
    data = read_magic(Path(source), n=32)
    return infer_rich_media_suffix(data)
