# Plan: Sensitive data detection in images (OCR + BLOB + embeds)

**Status:** Pending
**Date:** 2026-04-04
**Authors:** Fabio Leitao
**Priority:** H3
**Depends on:** ADR-0012

**Português (Brasil):** [PLAN_IMAGE_SENSITIVE_DATA_DETECTION.pt_BR.md](PLAN_IMAGE_SENSITIVE_DATA_DETECTION.pt_BR.md)

<!-- plans-hub-summary: OCR/BLOB/embed image scanning for personal and special-category data; optional extras; after synthetic image corpus. ADR-0012. -->

<!-- PLAN: PLAN_IMAGE_SENSITIVE_DATA_DETECTION -->
<!-- Status: Proposed | Priority: H2 (high value; depends on a stable Synthetic Data Lab) -->
<!-- Created: 2026-04-03 | Author: Fabio Leitao -->

## Motivation

Data Boar already scans structured and semi-structured text. Images — photos of national IDs, medical prescriptions, payment cards, scanned documents — remain a sensitive-data vector the scanner does not see today.

Typical scenarios:

- Object storage or NAS with photos of customer documents (onboarding, KYC).
- A `foto_documento` column storing base64 of an ID card.
- A medical-record PDF whose pages are scanned images of a health-system card.
- A user renaming a photo of a national ID to `.mp3` (cloaking) to bypass DLP.
- Email with a JPEG attachment of a bank statement.

Legal basis (LGPD):

- Art. 5, X — document numbers (national ID, registry) = personal data.
- Art. 5, II — biometric (face) and health data = sensitive personal data.
- Art. 14 — children’s data.

Legal basis (GDPR):

- Art. 4(14) — biometric data.
- Art. 9 — special categories (health, biometric).

ADR: [ADR-0012](../adr/ADR-0012-ocr-image-sensitive-data-detection.md)

---

## Recommended sequencing

Run this **after** [PLAN_SYNTHETIC_DATA_LAB.md](PLAN_SYNTHETIC_DATA_LAB.md) has produced a synthetic **image** corpus for tests.

Queue position: H2 (high value; not blocking the current release). Header **Priority** stays **H3** until `PLANS_TODO` promotes it.

---

## Phases

### Phase 0 — Foundation and dependencies (1–2 days)

**Goal:** environment ready, OCR working, first smoke test on a synthetic image.

- [ ] Add optional dependencies to `pyproject.toml`:
  - `pytesseract` (Python binding for Tesseract)
  - `Pillow` (image processing)
  - `easyocr` (optional, tier 2, separate flag)
  - Use extras or an `image` group so default installs stay light.
- [ ] Document Tesseract binary install:
  - Linux: `apt install tesseract-ocr tesseract-ocr-por`
  - macOS: `brew install tesseract tesseract-lang`
  - Windows: official installer + PATH
  - Docker: add to `Dockerfile` (optional stage `data_boar:image`)
- [ ] Create `core/image_detector.py` (stub with `ImageDetector`).
- [ ] Smoke test: JPEG with a printed synthetic national ID; OCR returns text and regex matches.
- [ ] Add `enable_image_scanning: false` to the config schema (default off).

### Phase 1 — Standalone image files (3–5 days)

**Goal:** the filesystem scanner detects images and extracts text via OCR.

- [ ] Detect by magic bytes (not extension):
  - JPEG: `FF D8 FF`
  - PNG: `89 50 4E 47`
  - GIF: `47 49 46 38`
  - TIFF: `49 49 2A 00` or `4D 4D 00 2A`
  - WebP: `52 49 46 46` + `57 45 42 50`
  - BMP: `42 4D`
- [ ] Detect **cloaking**: non-image extension with image magic bytes.
  - Example: `curriculo.mp3` with JPEG magic.
  - Report as `image_cloaked_as: mp3`.
- [ ] Pipeline:
  1. Open with Pillow.
  2. Pre-process (grayscale, resize if too small).
  3. Tesseract with `lang=por+eng`.
  4. Apply LGPD regex patterns on extracted text.
  5. Record finding with `file_path`, `ocr_engine`, `ocr_confidence`, `pattern_matched`, `category`, `norm`.
- [ ] Configure `image_ocr_engine: tesseract` (default) and `easyocr` (opt-in).
- [ ] Per-image timeout (default 30s) so corrupt files do not stall the scan.
- [ ] Unit tests against the synthetic corpus from [PLAN_SYNTHETIC_DATA_LAB.md](PLAN_SYNTHETIC_DATA_LAB.md).

### Phase 2 — BLOBs and base64 in databases (3–4 days)

**Goal:** the database scanner detects binary columns that hold images and analyses them.

- [ ] Heuristic for image columns:
  - Type: `BLOB`, `BYTEA`, `LONGBLOB`, `MEDIUMBLOB`, `RAW`, `IMAGE`, `VARBINARY`.
  - Name: `foto`, `imagem`, `photo`, `image`, `thumbnail`, `avatar`, `documento`, `attachment`, `img`, `picture`, `scan`.
  - Type + name combination raises suspicion score.
- [ ] Base64 in TEXT/VARCHAR:
  - Regex for long base64 strings (> 100 chars, charset `[A-Za-z0-9+/=]`).
  - Decode and check magic bytes.
- [ ] Configurable sampling: `image_blob_sampling_rows: 5` (never load the whole table).
- [ ] Pipeline: decode bytes → magic bytes → if image, OCR tier 1.
- [ ] **Privacy by design:** never persist decoded image bytes in logs or reports. Findings only (path, pattern, category).
- [ ] Initial engines: MariaDB, PostgreSQL, Oracle XE (already in the synthetic lab).
- [ ] Tests: synthetic containers with BLOBs of fake ID-card images.

### Phase 3 — Images embedded in documents (2–3 days)

**Goal:** PDF, DOCX, and email with embedded images are also scanned.

**PDF:**

- [ ] Use `pymupdf` (fitz) to extract images page by page.
- [ ] Fallback: `pdfplumber` for PDFs with no native text (pure scanned image).
- [ ] Associate finding with `file_path + page_number + image_index`.

**DOCX / XLSX:**

- [ ] Use `python-docx` to extract images from inner `word/media/`.
- [ ] Associate finding with `file_path + paragraph_index`.

**EML / MSG:**

- [ ] Reuse the existing email parser for `image/*` parts.
- [ ] Pass each image attachment to OCR tier 1.

**Advanced cloaking tests:**

- [ ] PDF that is only a scanned image (no text layer).
- [ ] DOCX with images only, no text.

### Phase 4 — Compliance report integration (1–2 days)

**Goal:** image findings appear like any other finding.

- [ ] Add `source_type: image_file | image_blob | image_embedded`.
- [ ] Add `ocr_engine`, `ocr_confidence` (for audit).
- [ ] Dedicated “Images with sensitive data” section in HTML/Excel reports.
- [ ] Count images scanned, images with findings, cloaked images.
- [ ] Dashboard: scan-coverage gauge with images enabled vs disabled.

### Phase 5 — Document-type classification (deferred / H3)

**Goal:** infer document type on the image (ID card, passport, prescription, statement).

- [ ] Train or reuse a pre-trained model (CLIP zero-shot or a fine CNN).
- [ ] Input: image; output: `doc_type` (`id_card_br`, `passport`, `prescription`, `bank_statement`, `other`).
- [ ] Combine with OCR to cut false positives (e.g. report national ID only if `doc_type` = id card).
- [ ] Face detection (biometric) via `face_recognition` or `mediapipe`.
- [ ] Age estimation for possible minors — high complexity; evaluate carefully.

---

## Target detection matrix

| Image type | Primary method | LGPD category | Norm |
| ---------- | -------------- | ------------- | ---- |
| Printed national ID photo | OCR regex (CPF) | Personal data | Art. 5, X |
| Registry card (front/back) | OCR regex + doc_type | Personal data | Art. 5, X |
| Driver licence photo | OCR regex + doc_type | Personal data | Art. 5, X |
| Passport photo | OCR regex + doc_type | Personal data | Art. 5, X |
| Face photo | Face detector (Phase 5) | Sensitive biometric | Art. 5, II |
| Medical prescription photo | OCR + doc_type | Sensitive health | Art. 5, II |
| Exam / report photo | OCR + doc_type | Sensitive health | Art. 5, II |
| Payment-card photo | OCR regex PAN | Personal financial | Art. 5; PCI DSS |
| Bank-statement photo | OCR regex + doc_type | Personal financial | Art. 5 |
| Child photo | Face + age estimator | Minor’s data | Art. 14 |
| JPEG BLOB in DB with national ID | BLOB detect + OCR | Personal data | Art. 5, X |
| base64 image in TEXT column | base64 detect + OCR | Personal data | Art. 5 |
| Scanned PDF (no native text) | Embed extract + OCR | Per content | Per finding |
| JPEG cloaked as MP3 | Magic bytes + OCR | Per content | Per finding |

---

## Technical dependencies

| Package | Use | Tier | PyPI / system |
| ------- | --- | ---- | ------------- |
| `pytesseract` | OCR tier 1 | Optional | `pip install pytesseract` |
| `Pillow` | Open / pre-process | Optional | `pip install Pillow` |
| `easyocr` | OCR tier 2 (higher accuracy) | Opt-in | `pip install easyocr` |
| `pymupdf` | Extract images from PDF | Optional | `pip install pymupdf` |
| `tesseract-ocr` | System binary | System | apt / brew / msi |
| `tesseract-ocr-por` | pt-BR trained data | System | apt / traineddata |

---

## Guardrails

- Never save decoded BLOB bytes in logs, reports, or artifact files.
- Never send images to an external API without explicit operator consent and a documented legal basis.
- Per-image timeout: avoid stalling on corrupt or huge files.
- BLOB sampling: never load a whole table; sample N rows.
- OCR can false-positive — expose `ocr_confidence` on the finding for triage.

---

## Success indicators

- [ ] Scanner detects a national ID on JPEG with Tesseract at F1 > 0.85 on the synthetic corpus.
- [ ] BLOB with a fake registry-card image in synthetic MariaDB reported as a finding.
- [ ] Scanned PDF (no native text) with a national ID returns a finding.
- [ ] `.mp3` with JPEG magic reported as `image_cloaked_as: mp3`.
- [ ] No image bytes persisted in report artifacts.
- [ ] Scan of 1000 JPG/PNG finishes in under 10 min on CPU (worker=4).

---

## Open decisions

- Whether EasyOCR ships in the default Dockerfile or only `data_boar:image`.
- Whether face detection (biometric, Phase 5) is v2.0 core or a plugin.
- Which file extensions trigger image scanning by default (everything vs curated list).
- Confirm with collaborators whether typical customer segments store images in databases or only on filesystems (generic: onboarding/KYC and professional-services document stores — no named accounts in this plan).
