"""
Extract text-like samples from images, audio, and video for sensitivity scanning.

Used when ``file_scan.scan_rich_media_metadata`` and/or ``file_scan.scan_image_ocr`` is enabled.
Optional dependencies: ``mutagen`` (``pip install -e ".[richmedia]"``), ``pytesseract`` + system
Tesseract for OCR, ``ffprobe`` on PATH for video container tags.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

from core.rich_media_magic import (
    AUDIO_EXTENSIONS,
    IMAGE_EXTENSIONS,
    VIDEO_EXTENSIONS,
)

# Register pillow-heif opener once at module load so PIL.Image.open() handles HEIC/HEIF
# transparently.  Idempotent; safe to call multiple times.
try:
    import pillow_heif  # type: ignore[import-untyped]

    pillow_heif.register_heif_opener()
except ImportError:
    pass


def build_rich_media_text_sample(
    path: Path,
    ext: str,
    max_chars: int,
    *,
    metadata: bool,
    image_ocr: bool,
    ocr_max_dimension: int = 2000,
    ocr_lang: str = "eng",
) -> str:
    """
    Build a bounded string for ``scan_file_content`` from EXIF/tags and optional OCR.

    *metadata* enables EXIF (images), mutagen tags (audio), ffprobe format/tags (video).
    *image_ocr* runs Tesseract on raster images when Pillow can open them.
    """
    ext_l = (ext or "").lower()
    chunks: list[str] = []
    if metadata:
        if ext_l in IMAGE_EXTENSIONS:
            chunks.append(_image_exif_text(path))
        elif ext_l in AUDIO_EXTENSIONS:
            chunks.append(_mutagen_audio_tags(path))
        elif ext_l in VIDEO_EXTENSIONS:
            chunks.append(_ffprobe_metadata_text(path))
    if image_ocr and ext_l in IMAGE_EXTENSIONS:
        chunks.append(_tesseract_ocr_text(path, ocr_max_dimension, ocr_lang))
    out = "\n".join(c for c in chunks if c and c.strip())
    return out.strip()[:max_chars]


def _image_exif_text(path: Path) -> str:
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS
    except ImportError:
        return ""
    try:
        with Image.open(path) as im:
            exif = im.getexif()
            if not exif:
                return ""
            parts: list[str] = []
            for k, v in exif.items():
                tag = TAGS.get(k, k)
                if v is None:
                    continue
                s = str(v).strip()
                if not s or len(s) > 500:
                    continue
                parts.append(f"{tag}: {s}")
            return "\n".join(parts)
    except Exception:
        return ""


def _mutagen_audio_tags(path: Path) -> str:
    try:
        from mutagen import File as MutagenFile
    except ImportError:
        return ""
    try:
        audio = MutagenFile(path, easy=True)
        if audio is None:
            return ""
        parts: list[str] = []
        for key in audio.keys():
            val = audio[key]
            if isinstance(val, list):
                text = " ".join(str(x) for x in val[:5])
            else:
                text = str(val)
            text = text.strip()
            if text and len(text) < 800:
                parts.append(f"{key}: {text}")
        return "\n".join(parts[:80])
    except Exception:
        return ""


def _ffprobe_metadata_text(path: Path) -> str:
    try:
        proc = subprocess.run(
            [
                "ffprobe",
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_format",
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=45,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return ""
    if proc.returncode != 0 or not (proc.stdout or "").strip():
        return ""
    try:
        data: dict[str, Any] = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return ""
    fmt = data.get("format") or {}
    tags = fmt.get("tags") or {}
    if not isinstance(tags, dict):
        return ""
    parts: list[str] = []
    for k, v in tags.items():
        s = str(v).strip()
        if s and len(s) < 600:
            parts.append(f"{k}: {s}")
    return "\n".join(parts[:100])


def _tesseract_ocr_text(path: Path, max_dim: int, lang: str) -> str:
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        return ""
    try:
        max_dim = max(256, min(int(max_dim), 8000))
    except (TypeError, ValueError):
        max_dim = 2000
    try:
        with Image.open(path) as im:
            im = im.convert("RGB")
            im.thumbnail((max_dim, max_dim))
            text = pytesseract.image_to_string(im, lang=lang or "eng") or ""
        text = re.sub(r"\s+", " ", text).strip()
        return text
    except Exception:
        return ""
