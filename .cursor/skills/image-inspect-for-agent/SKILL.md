---
name: image-inspect-for-agent
description: Bounded EXIF/metadata and optional Tesseract OCR for one media file via scripts/image-inspect.ps1 and scripts/image_inspect.py (same stack as connectors/rich_media_sample).
---

# Image / media inspect for agent context

## When to use

- Operator points to a **photo (HEIC/JPEG)**, **audio**, or **video** and the assistant needs **tags or OCR text** in the chat.
- Prefer this over inventing Pillow/Tesseract one-offs.

## Ritual

1. Read **`docs/ops/IMAGE_EXIF_OCR_FOR_AGENT.md`** for **L0-L3** and ML limits.
2. From repo root: **`.\scripts\image-inspect.ps1 -Path <file>`**; add **`-Ocr`** for images with visible text.
3. Keep paths under **`docs/private/`** when handling iPhone / personal media.
4. If output is empty: check **`uv sync --extra richmedia`**, **tesseract** / **ffprobe** on PATH — report the matrix from the doc, not vague “cannot”.

## Pairing

- **Video screen recordings:** **`video-frame-samples.ps1`** + [VIDEO_FRAME_EXTRACT_FOR_AGENT.md](../../docs/ops/VIDEO_FRAME_EXTRACT_FOR_AGENT.md).
- **iCloud staging:** **`icloud-photos-fetch-range.ps1`** then inspect.

## Anti-patterns

- Claiming **CLIP-style** visual search using the product ML stack — it is **text-sample** detection, not photo embedding search.
- Pasting **GPS EXIF** or personal paths into **public** GitHub text.
