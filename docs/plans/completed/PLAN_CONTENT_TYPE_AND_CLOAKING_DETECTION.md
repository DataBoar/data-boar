# Plan: Content-based type detection and cloaking resistance

**Status:** Core complete (archived under `docs/plans/completed/`). Steps 1–4 implemented (config, connectors, CLI, API/dashboard); optional man/OpenAPI polish tracked below.
**Synced with:** [PLANS_TODO.md](../PLANS_TODO.md) (central to-do list)

## When implementing steps: update docs and tests; then update PLANS_TODO.md and this file.

Today the Data Boar decides **what to scan** and **how to extract text** mainly by **file extension**. That leaves a gap: users (or bad actors) can **rename** files (e.g. `sensitive.pdf` → `notes.txt`) or use **cloaking** (e.g. misleading extension) to avoid or skew scanning. This plan adds an **optional** capability to **peek at file content**—magic bytes and, where useful, MIME-type inference—so we can **detect the real format** and **scan for violations** even when the extension is wrong or chosen to hide the true type. Optionally we can later consider **steganography** (data hidden inside images or other containers) as a separate, more compute-intensive feature.

---

## Goals

1. **Content-based type detection (opt-in):** When enabled, read the first **N** bytes (e.g. 32–64) of each file and match against **magic-byte signatures** (and optionally MIME) to infer the real format. Use that **inferred type** for extraction and sensitivity scanning, so renamed files (e.g. PDF with `.txt` extension) are still scanned as PDF.
1. **No regressions:** Default remains extension-based; new behaviour is **off by default** and gated by config/CLI/dashboard.
1. **Resource awareness:** Peeking at headers is **one small read per file** (modest extra I/O and CPU). We recommend a **new opt-in** so operators who need it can enable it without surprising others with extra I/O.
1. **Documentation:** Explain the option, the benefit (renamed-file and basic cloaking resistance), and that it is more I/O- and CPU-intensive than extension-only scanning.

---

## Recommendation: new opt-in (config, CLI, web)

Because content-based detection adds **one read of the first N bytes per file** and **magic-byte matching**, it is **more compute- and I/O-intensive** than extension-only scanning. We **recommend** adding:

- **Config:** `file_scan.use_content_type` (or `detect_content_type`) — boolean, default `false`.
- **CLI:** e.g. `--content-type-check` — when present, act as if `file_scan.use_content_type: true` for that run.
- **Web / API:** Optional field in scan-start body (e.g. `content_type_check: true`) and a **dashboard checkbox** such as “Use content type (magic bytes) to detect file format—helps find renamed or cloaked files; may increase I/O and run time.”

This keeps the default lightweight and lets operators who care about renamed files or simple cloaking opt in.

---

## Scope: magic bytes and MIME

- **Magic bytes:** For each format we support (PDF, ZIP, Office, text, etc.), define a short signature (e.g. PDF: `%PDF`, ZIP: `PK\x03\x04`, Office Open XML: `PK` + central directory). Read the first **N** bytes (e.g. 32–64) and match; if we recognize the format, use it for extraction regardless of extension.
- **MIME:** Optionally use a library (e.g. `python-magic` / libmagic) to get MIME type from content; map MIME to our internal “extractor” type. This can be a second phase or alternative to a hand-written magic table so we don’t depend on libmagic initially.
- **Fallback:** If content-based detection fails or is disabled, keep current extension-based behaviour.

---

## Renamed files and simple cloaking

- **Renamed files:** With content-type detection on, a file named `data.txt` whose header is `%PDF-1.4` will be treated as PDF and scanned with the PDF extractor. Findings are reported with the actual path and name; we can optionally note “detected as PDF (extension .txt)” in metadata or logs.
- **Simple cloaking:** Same idea: if someone renames a spreadsheet to `.log`, we still open and scan it as a spreadsheet when magic bytes indicate Office/Excel. We do **not** promise to detect **steganography** (data hidden inside images or other containers) in this phase; that is a separate, heavier concern (see below).

---

## Steganography (future / optional)

**Steganography** means hiding data inside another file (e.g. text inside an image). Detecting or extracting such content typically requires:

- Specialized tools (e.g. stegano, steghide, entropy analysis) and often **per-format** logic.
- More **compute and I/O** (decode image, analyze bits, run detection heuristics).

**Recommendation:** Treat steganography as a **possible future extension** or a **separate opt-in** (e.g. “Scan for hidden content in images”), not part of the initial content-type plan. In docs and this plan, we can state that “content-based type detection helps with renamed files and extension cloaking; detection of data hidden via steganography may be considered in a later phase and would be more resource-intensive.”

---

## Implementation outline

1. **Magic-byte table:** Define a small module or mapping: format → (signature bytes, offset). For formats we already support (PDF, DOCX/XLSX/PPTX as ZIP, plain text, etc.), add entries. Reuse or align with the magic used in [PLAN_COMPRESSED_FILES.md](PLAN_COMPRESSED_FILES.md) for archives. (Step 1 helper implemented with coarse labels: `pdf`, `zip`, `text`.)
1. **Content-type resolver:** Use `read_magic(path, n=64)` + `infer_content_type(path_or_bytes)` to infer a coarse internal label or `None`. When suggested type is in our supported set, use it to decide which existing extraction path to take; otherwise fall back to file extension or skip.
1. **Optional libmagic / `file`-style backend (future, optional):** Consider wiring an **optional** backend based on libmagic (e.g. `python-magic` / `python-magic-bin`) as a second pass when the built-in helper returns `None`. Map only a **small, whitelisted set of MIME types** (e.g. `application/pdf`, Office OOXML, `text/*`) to our coarse labels and ignore everything else. This should be **dependency-optional** (best-effort; if the library is absent, we keep current behaviour).
1. **Config / engine / connector:** Add and normalize `file_scan.use_content_type` (default false) and propagate it into filesystem/share connectors as `self.use_content_type`. When true, connectors **may** consult the resolver before choosing extraction strategy; when false, behaviour remains extension-only.
1. **CLI:** Add `--content-type-check`; override config for that run when set.
1. **API and dashboard:** Add optional `content_type_check` to scan-start body and a checkbox in the dashboard with short help text (benefit + “may increase I/O and run time”).
1. **Tests:** Extension-only (default) unchanged; with option on, a renamed PDF (e.g. `file.txt` with PDF magic) is scanned and yields findings. No regressions.
1. **Docs:** USAGE, TECH_GUIDE, dashboard help—explain the option, that it helps with renamed files and simple cloaking, and that it is more I/O- and CPU-intensive, plus that an optional libmagic backend (when installed) may improve coverage.

---

## To-dos (sequential)

| #   | To-do                                                                                                                                                                                                 | Status                                                                                                                                                                  |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------                                                                                                                                                                  |
| 1   | Define magic-byte table for supported formats (PDF, ZIP, Office OOXML, plain text, etc.); implement `read_magic` and `infer_content_type`.                                                            | ✅ Done (helper `infer_content_type(path_or_bytes)` in `core/content_type.py`; basic PDF/ZIP/text coverage; uses existing `read_magic` and archive magic)                |
| 2   | Config: `file_scan.use_content_type` (default false); normalize in loader and pass to engine/connectors.                                                                                              | ✅ Done (loader normalizes; engine injects file_scan into target; connectors read use_content_type; test in test_config_encoding + test_file_scan_use_content_type_flag) |
| 3   | FilesystemConnector: when `use_content_type` true, infer type from header and use it for extraction (fallback to extension). Share connectors: same when they use file-scan logic.                    | ✅ Done (choose_effective_pdf_extension used in filesystem, SMB, WebDAV, SharePoint when use_content_type true)                                                          |
| 4   | CLI: `--content-type-check`; API/dashboard: optional `content_type_check` and checkbox with user warning (may increase I/O and run time).                                                             | ✅ Done                                                                                                                                                                  |
| 5   | Tests: default behaviour unchanged; with option on, renamed PDF (or other) is scanned by content; no regressions.                                                                                     | ✅ Done (`tests/test_api_scan_content_type_check.py` + existing connector tests)                                                                                         |
| 6   | Docs: USAGE, TECH_GUIDE, help—content-type option, benefit (renamed/cloaking), and resource impact. Note: steganography out of scope for v1; possible future phase.                                   | ✅ Done (USAGE, USAGE.pt_BR, TECH_GUIDE EN/pt_BR; optional: man pages / OpenAPI examples later)                                                                          |

**Sync:** When a step is done, mark **✅ Done** in this table and in [PLANS_TODO.md](../PLANS_TODO.md).

---

## Last updated

Plan updated for Step 1 helper implementation. Update this doc when completing further steps or when design decisions change.
