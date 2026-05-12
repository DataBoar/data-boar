# ADR 0012 — OCR and Image-Based Sensitive Data Detection

- **Status:** Proposed
- **Date (UTC):** 2026-04-03
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Context

Data Boar currently detects sensitive and personal data in:

- Structured database content (rows, columns, metadata)
- Text-based files (TXT, CSV, JSON, XML, YAML, logs)
- Office documents (DOCX, XLSX via text extraction)
- PDF (text layer extraction)

**Gap:** Images -- whether as standalone files (JPG, PNG, TIFF, WebP, etc.), embedded inside PDFs/DOCX, attached in emails (EML/MSG), or stored as BLOBs or base64-encoded strings in database columns -- are entirely outside the current detection surface.

Real-world scenarios where this matters:

- A user uploads a photo of their CPF, RG, CNH, or passaporte to a system.
- A healthcare app stores prescription photos as BLOBs in MySQL.
- A compliance audit must report that an S3 bucket or NAS folder contains scanned ID images.
- A database column (foto_doc, attachment, img_data) holds base64-encoded JPEGs.
- An end user tried to bypass DLP controls by renaming a CPF-photo JPEG to .pdf or .mp3 (cloaking scenario already in the synthetic lab plan).

LGPD, GDPR, and similar norms consider the photo of an ID document to be personal data (LGPD Art. 5, X); a photo of a face is biometric data, classified as sensitive (LGPD Art. 5, II); a photo of a medical record or prescription is health data, also sensitive (Art. 5, II); photos of minors require special protection (Art. 14).

## Decision drivers

1. **No cloud dependency for raw image content** -- sending customer images to a cloud OCR API creates a secondary data processing relationship, potentially requiring additional LGPD legal basis. Local or self-hosted OCR is strongly preferred.
2. **Portuguese-language accuracy** -- OCR must handle pt-BR text well (CPF, RG formats, document headings in Portuguese).
3. **Low-overhead first tier** -- Scanning filesystem image files must not require a GPU for basic operation.
4. **Extensible tiers** -- Advanced scenarios (better accuracy, GPU, cloud with consent) must be opt-in, not breaking changes.
5. **Compliance reporting** -- Findings from image scanning must integrate with the existing finding/reporting pipeline (category, norm, location).

## Options evaluated

### A. Cloud OCR API (Google Vision / AWS Textract / Azure CV)

- **Pros:** Highest accuracy out of the box; document classification included.
- **Cons:** Images leave the local environment -- creates secondary processing; requires internet; paid per-image; unacceptable as the default for compliance-sensitive scans.
- **Decision:** Available as opt-in future tier only, with explicit operator consent and legal basis documented.

### B. Tesseract (pytesseract) -- local, open source

- **Pros:** Runs fully local; tesseract-ocr-por language pack gives good pt-BR accuracy; CPU-only; well-maintained Python bindings; MIT/Apache-compatible; zero per-image cost.
- **Cons:** Lower accuracy than DL-based approaches for low-resolution, handwritten, or distorted images; requires Tesseract binary in PATH or Docker image.
- **Decision:** PRIMARY OCR engine for tier 1 (local scanning).

### C. EasyOCR -- neural-network, local

- **Pros:** Better accuracy than Tesseract on complex layouts; GPU-optional (CPU works); pt-BR included; pure Python.
- **Cons:** Heavier dependency (~200 MB model download on first use); slower on CPU.
- **Decision:** OPTIONAL tier 2 (high-accuracy local) -- enabled via config flag `image_ocr_engine: easyocr`.

### D. PaddleOCR

- **Decision:** DEFERRED -- evaluate after EasyOCR tier is stable.

### E. Vision-language models (CLIP, LLaVA, etc.)

- **Decision:** DEFERRED to a future AI-tier feature flag -- useful for document type classification once OCR text is insufficient.

## Decision

Implement image-based sensitive data detection in three layers:

### Layer 1 -- File surface (standalone image files)

- Detect images by magic bytes (not extension) among supported file types.
- Pass images through OCR (Tesseract primary; EasyOCR optional).
- Apply existing LGPD regex patterns to OCR output.
- Tag findings with location (file path + bounding box if available), pattern matched, data category, norm.
- Supported types: JPEG, PNG, TIFF, WebP, BMP, GIF; also detect image cloaking (image magic bytes inside non-image extension).

### Layer 2 -- Database BLOB surface

- Detect columns of binary types (BLOB, BYTEA, LONGBLOB, RAW, IMAGE, VARBINARY) or text columns with base64-encoded content.
- Sample N rows per column (configurable, default 3 to 5).
- Decode and identify image magic bytes; pass to OCR tier 1.
- Report findings at column + row-sample level; never store decoded image content in reports.

### Layer 3 -- Embedded images (PDF, DOCX, EML)

- Extract embedded images from PDFs (via pdfplumber/pymupdf), DOCX (python-docx), and email attachments (existing parser).
- Pass each extracted image to OCR tier 1.
- Associate finding with parent document path + page/attachment reference.

### Compliance tagging

| Image content detected          | Category                              | Norm                    |
|---------------------------------|---------------------------------------|-------------------------|
| CPF, RG, CNH, passaporte photo  | Personal data -- ID document          | LGPD Art. 5, X          |
| Face (biometric)                | Sensitive personal data -- biometric  | LGPD Art. 5, II         |
| Medical record / prescription   | Sensitive personal data -- health     | LGPD Art. 5, II         |
| Minor (face + context)          | Children personal data                | LGPD Art. 14            |
| Bank statement / financial      | Personal data -- financial            | LGPD Art. 5             |
| Credit card number in image     | Personal data -- financial            | LGPD Art. 5; PCI DSS   |

### Architecture integration

- New module: `core/image_detector.py` (or `core/detectors/image.py`).
- Config flags: `enable_image_scanning: true`, `image_ocr_engine: tesseract|easyocr`, `image_blob_sampling_rows: 5`.
- Feature flag controls rollout; existing scanners unaffected when flag is off.
- Optional dependencies: `pytesseract`, `Pillow`, `easyocr` -- guarded with ImportError and user-friendly install instructions.

## Consequences

**Positive:**
- Closes the largest current blind spot in compliance coverage.
- No cloud dependency by default -- keeps LGPD processing on-premise.
- Layered approach allows incremental rollout without breaking existing scans.
- Cloaking detection (image disguised as another file type) improves DLP coverage.
- Enables the synthetic data lab plan to include image corpora as first-class test scenarios.

**Negative / watch items:**
- OCR adds runtime: scanning large image folders will be significantly slower. Needs worker concurrency and progress reporting.
- Tesseract must be installed system-wide (or via Docker image) -- adds to deployment docs.
- False positives on low-quality images are likely; confidence scoring must be exposed.
- BLOB sampling design must ensure no decoded image data ends up in reports or logs (privacy by design).
- Biometric/face detection requires a separate computer-vision classifier (not just OCR) -- deferred.

## References

- `docs/plans/PLAN_IMAGE_SENSITIVE_DATA_DETECTION.pt_BR.md` -- implementation plan and phasing
- `docs/plans/PLAN_SYNTHETIC_DATA_LAB.pt_BR.md` -- synthetic image corpus as test data
- `.cursor/skills/sensitive-data-detection/SKILL.md` -- detection strategy (updated to include images)
- LGPD (Lei 13.709/2018): Art. 5 (definitions), Art. 14 (children data)
- GDPR Art. 9 (special categories including biometric), Art. 4(14) (biometric data definition)
