#!/usr/bin/env python3
"""Bounded rich-media metadata + optional OCR for one file (operator / assistant CLI).

Reuses :func:`connectors.rich_media_sample.build_rich_media_text_sample` — the same stack as
``file_scan.scan_rich_media_metadata`` / ``scan_image_ocr`` in the product filesystem connector.

- **Images:** EXIF (Pillow) + optional Tesseract OCR on a downscaled raster (``pytesseract`` +
  system ``tesseract``). **HEIC/HEIF** needs optional ``pillow-heif`` (``uv sync --extra richmedia``).
- **Audio:** ID3/simple tags via **mutagen** when installed.
- **Video:** container/format tags via **ffprobe** on PATH.

This CLI is for **token-aware** inspection in Cursor sessions — not a substitute for a full
Data Boar scan (detector ML runs on configured targets, not on ad-hoc “find my photo” search).

Usage (repo root)::

  uv run python scripts/image_inspect.py path.mov --metadata
  uv run python scripts/image_inspect.py path.heic --metadata --ocr
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from connectors.rich_media_sample import build_rich_media_text_sample
from core.rich_media_magic import RICH_MEDIA_SCAN_EXTENSIONS


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Print bounded rich-media metadata and/or OCR text "
            "(same stack as Data Boar file_scan rich media options)."
        )
    )
    parser.add_argument(
        "path",
        type=Path,
        help="Path to an image, audio, or video file.",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=16000,
        metavar="N",
        help="Cap output size (default 16000).",
    )
    parser.add_argument(
        "--no-metadata",
        dest="metadata",
        action="store_false",
        default=True,
        help="Skip EXIF / mutagen / ffprobe (use with --ocr for OCR-only on images).",
    )
    parser.add_argument(
        "--ocr",
        action="store_true",
        help="Run Tesseract on images (ignored for audio/video).",
    )
    parser.add_argument(
        "--ocr-lang",
        default="eng",
        help="Tesseract language code (default eng). For Portuguese try por or eng+por.",
    )
    parser.add_argument(
        "--ocr-max-dimension",
        type=int,
        default=2000,
        metavar="PX",
        help="Max width/height before OCR (default 2000, clamped 256-8000).",
    )
    args = parser.parse_args()

    path = args.path.expanduser().resolve()
    if not path.is_file():
        print(f"image_inspect: not a file: {path}", file=sys.stderr)
        return 2

    ext = path.suffix.lower()
    if ext not in RICH_MEDIA_SCAN_EXTENSIONS:
        print(
            f"image_inspect: extension {ext!r} not in rich-media set; trying anyway",
            file=sys.stderr,
        )

    cap = max(1, min(int(args.max_chars), 500_000))
    sample = build_rich_media_text_sample(
        path,
        ext,
        cap,
        metadata=bool(args.metadata),
        image_ocr=bool(args.ocr),
        ocr_max_dimension=args.ocr_max_dimension,
        ocr_lang=args.ocr_lang or "eng",
    )
    if not sample:
        print(
            "(no sample extracted: check --metadata/--ocr, install .[richmedia], "
            "tesseract on PATH for OCR, ffprobe for video, mutagen for audio)",
            file=sys.stderr,
        )
        return 0

    print(sample)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
