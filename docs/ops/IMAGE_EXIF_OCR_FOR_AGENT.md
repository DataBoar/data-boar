# Image EXIF, OCR, and metadata for agent context (Windows + uv)

**Português (Brasil):** [IMAGE_EXIF_OCR_FOR_AGENT.pt_BR.md](IMAGE_EXIF_OCR_FOR_AGENT.pt_BR.md)

## Purpose

Assistants need **bounded** text from **photos (iPhone HEIC/JPEG)**, **audio**, and **video** without pretending the model “sees” binaries natively. This repo already implements extraction inside the **product** via **`connectors/rich_media_sample.py`** (wired by `file_scan.scan_rich_media_metadata` and `file_scan.scan_image_ocr` — see [USAGE.md](../USAGE.md)). The **operator CLI** exposes the **same stack** for ad-hoc Cursor work.

## Taxonomy (complexity vs tokens and blast radius)

| Level | What | When                                                         |
| ----- | ---- | ------------------------------------------------------------ |
| **L0** | Do not read pixels / tags                                    | Operator will paste text; file is out of scope or too sensitive. |
| **L1** | **Metadata only** (`--no-metadata` **off**, default): EXIF, mutagen, ffprobe | iPhone photos: date, camera, **optional** location strings in EXIF — still **PII-adjacent**; keep under **`docs/private/`** workflows. |
| **L2** | **L1 + OCR** (`--ocr` on images): Tesseract on a **downscaled** raster | Screenshots, scans, printed text in photos — same engine as the scanner’s optional OCR. |
| **L3** | **Full Data Boar scan** on a directory with detector **ML/DL** | Compliance / inventory: the engine scores **text samples** (including OCR output when enabled in **config**), not “visual similarity search” across a photo library. |

## What Data Boar ML / DL is (and is not)

- **Is:** classifiers and gates on **text-like** content (regex, vocabulary, optional ML tiers tied to **sensitivity** / compliance labels in the product pipeline).
- **Is not:** a general **visual embedding** or **CLIP-style** “find all photos of object X” search across tens of thousands of images. Building that requires a separate **indexing** pipeline (embeddings + vector store) and explicit privacy review.
- **Practical “find” pattern today:** run **L2** OCR (batch can be a follow-up script) and **search the extracted text** with **`repo-grep.ps1`** / `rg` on exported `.txt` — token-aware and explainable.

## Primary automation

| Tool | Role |
| ---- | ---- |
| **`scripts/image-inspect.ps1`** | Windows wrapper: **`uv run python scripts/image_inspect.py ...`** |
| **`scripts/image_inspect.py`** | One-file CLI over **`build_rich_media_text_sample`** |

**Examples (repo root):**

```powershell
.\scripts\image-inspect.ps1 -Path "docs\private\icloud_temp\IMG_1234.HEIC"
.\scripts\image-inspect.ps1 -Path ".\photo.jpg" -Ocr -OcrLang "por"
.\scripts\image-inspect.ps1 -Path ".\clip.mov"
```

```bash
uv run python scripts/image_inspect.py ./photo.heic --ocr --ocr-lang por
```

**Dependencies (honest matrix):**

| Goal | Install hint |
| ---- | ------------ |
| HEic / heif | **`uv sync --extra richmedia`** (pulls **`pillow-heif`** register opener — same as product). |
| OCR | **`uv sync --extra richmedia`** + system **`tesseract`** on `PATH` (e.g. Windows installer or `winget install --id UB-Mannheim.TesseractOCR` — pick a build your org trusts). |
| Video tags | **`ffprobe`** on `PATH` (`winget install ffmpeg`). |
| Audio tags | **`mutagen`** via **`richmedia`** extra. |

If a dependency is missing, output may be empty; the CLI prints a short stderr hint.

## iPhone / iCloud workflow (private tree)

1. Fetch or copy files into **`docs/private/icloud_temp/`** (or another **gitignored** path) with **`scripts/icloud-photos-fetch-range.ps1`** — see private **`ICLOUD_PHOTOS_SYNC_GUIDE.md`** when present.
2. Run **`image-inspect.ps1`** on the file.
3. Do **not** paste raw EXIF GPS or personal filenames into **public** issues/PRs.

## Pairing with video frames

Screen **recordings**: still use **`scripts/video-frame-samples.ps1`** + vision on PNGs — [VIDEO_FRAME_EXTRACT_FOR_AGENT.md](VIDEO_FRAME_EXTRACT_FOR_AGENT.md). **Still photos**: use **this** doc.

## References

- **`connectors/rich_media_sample.py`**, **`core/rich_media_magic.py`**
- [USAGE.md](../USAGE.md) — `scan_rich_media_metadata`, `scan_image_ocr`
- [ADR 0012](../adr/ADR-0012-ocr-image-sensitive-data-detection.md) (OCR direction)
- **`docs/ops/TOKEN_AWARE_SCRIPTS_HUB.md`**, **`.cursor/skills/image-inspect-for-agent/SKILL.md`**
