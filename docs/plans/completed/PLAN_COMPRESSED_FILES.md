# Plan: Optional scan inside compressed files (archives)

**Status:** Core delivery complete (archived under `docs/plans/completed/`). Steps **1–12** ✅; optional follow-ups in **Notes to remind later** (password-protected archives test, archive bombs, nested archives, …) — see table below.
**Synced with:** [PLANS_TODO.md](../PLANS_TODO.md) (central to-do list)

## When implementing steps: update docs and tests; then update PLANS_TODO.md and this file.

This plan adds an **optional** capability to **identify, open, and scan content inside compressed files** (zip, tar, gz, 7z, etc.). Because this can require significantly more **compute, I/O, and time**, it is **off by default** and must be explicitly enabled via **config**, **CLI argument**, and/or **web dashboard checkbox**. Findings inside archives are reported so that IT, compliance, and DPOs can see possible violations in packed data (e.g. backups, exports, shared bundles) as part of the “data soup” the Data Boar roots through.

---

## Goals

1. **Optional behaviour:** Default remains “do not open archives”; user opts in via `file_scan.scan_compressed: true`, CLI `--scan-compressed`, or API/dashboard “Also scan inside compressed files” checkbox.
1. **Identify archives** by extension and, where possible, **validate by magic bytes / binary headers** before opening.
1. **Uncompress and scan** inner members with the same sensitivity detection as regular files; **report findings** with a clear path (e.g. `archive.zip|path/inside.csv`) so reports and heatmaps reflect “inside archive” locations.
1. **No regressions:** Existing scans (scan_compressed false or unset) behave exactly as today; new code is additive and guarded by the option.
1. **Tests:** New tests for archive detection, option off/on behaviour, and reporting of inner findings; existing tests remain green.
1. **Documentation and dependencies:** Config, USAGE, TECH_GUIDE, man pages, dashboard/help updated; optional dependency (e.g. py7zr) and possibly an extra like `.[compressed]` or `.[archives]` for 7z support.

---

## Compressed formats: scope and compatibility

### Tier 1 – Standard library (no extra deps)

| Extension(s)                | Format          | Python module      | Magic / validation notes                                                                  |
| -------------------         | -------------   | -------------      | ----------------------------------------------------------------------------------------- |
| `.zip`                      | ZIP             | `zipfile`          | PK\x03\x04 (or PK\x05\x06 for empty) at start                                             |
| `.tar`                      | TAR             | `tarfile`          | Optional: ustar at offset 257; or try `tarfile.open()` and catch InvalidHeader            |
| `.gz`, `.tgz`               | Gzip / tar.gz   | `gzip` + `tarfile` | Gzip: `\x1f\x8b`; .tgz is gzipped tar, open with tarfile.open(..., mode="r:gz")           |
| `.bz2`, `.tbz2`, `.tar.bz2` | Bzip2 / tar.bz2 | `bz2` + `tarfile`  | Bzip2: `BZh`; tar.bz2 open with tarfile.open(..., mode="r:bz2")                           |
| `.xz`, `.txz`, `.tar.xz`    | XZ / tar.xz     | `lzma` + `tarfile` | XZ: FD 37 7A 58 5A 00; tar.xz open with tarfile.open(..., mode="r:xz")                    |

### Tier 2 – Optional dependency (recommended extra)

| Extension(s)  | Format | Python library | Magic / validation notes                    |
| ------------- | ------ | -------------- | ------------------------------------------- |
| `.7z`         | 7-Zip  | `py7zr`        | 7z magic: `37 7A BC AF 27 1C` (bytes 0–5)   |

### Tier 3 – Legacy / exotic (investigation or future)

| Extension(s)   | Format | Notes                                                                                        |
| -------------- | ------ | -------------------------------------------------------------------------------------------- |
| `.lha`, `.lzh` | LHA    | patool relies on external `lha`; or investigate pure-Python / ctypes; add if feasible        |
| `.arj`         | ARJ    | patool + external `arj`; optional later step                                                 |
| `.zoo`         | ZOO    | Rare; patool + external tool                                                                 |
| `.pak`         | PAK    | Game/data pack; format varies; could add detection by magic if we standardise one variant    |
| `.arc`         | ARC    | Multiple variants; patool supports some                                                      |
| `.ace`         | ACE    | patool + external unace; security/maintenance concerns with some legacy unpackers            |

**Recommendation:** Implement **Tier 1** and **Tier 2** (stdlib + py7zr). Document Tier 3 as “possible future extensions” and, if we later add patool or similar, gate it behind the same `scan_compressed` option and document dependency on external tools.

---

## Extension list to treat as “compressed” (when option on)

When `scan_compressed` is true, treat files with the following suffixes as **candidate archives** (after extension check, validate with magic bytes where defined; on validation failure, skip or save_failure and continue):

- **Tier 1:** `.zip`, `.tar`, `.gz`, `.tgz`, `.bz2`, `.tbz2`, `.xz`, `.txz`

  (and combined: `.tar.gz`, `.tar.bz2`, `.tar.xz` — note: multi-suffix handling, e.g. `file.tar.gz` → both suffixes; use `tarfile.open(..., mode="r:gz")` etc.)

- **Tier 2:** `.7z`
- **Tier 3 (later):** `.lha`, `.lzh`, `.arj`, `.zoo`, `.pak`, `.arc`, `.ace` (only if we add support and document deps)

**Multi-suffix:** For `name.tar.gz`, prefer treating as single archive (gzipped tar) and open with `tarfile.open(path, mode="r:gz")`; similarly `.tar.bz2`, `.tar.xz`. So the list of “compressed extensions” for **matching** can include both single (`.gz`, `.tar`) and compound (`.tgz` = .gz with tar convention; `.tar.gz` = two suffixes). Implementation: when iterating files, consider the **full suffix** (e.g. `.tar.gz`) and then single suffix (`.gz`) so we don’t double-scan the same file.

---

## Magic bytes / binary header validation

Before opening a file as an archive:

1. Read the first **N** bytes (e.g. 8–32) into a buffer.
1. Compare against known signatures (e.g. ZIP: `PK\x03\x04` or `PK\x05\x06`; Gzip: `\x1f\x8b`; 7z: `7z\xbc\xaf\x27\x1c`; Bzip2: `BZh`; XZ: `\xfd7zXZ\0`).
1. If the extension is in our “compressed” list but magic doesn’t match, **skip** opening as archive (optionally log or save_failure with reason “invalid_archive” / “magic_mismatch”) and do not treat as a normal content file unless it’s also in the regular extensions list (e.g. we don’t scan .zip as plain text).

This avoids crashes and accidental misuse when extension is wrong or file is corrupt, and aligns with “validate content that we can figure out how to code for”.

---

## Strategy: list-first, then decompress only selected members (no full expand)

We **do not** expand the whole archive to disk or memory first. The flow is:

1. **Open** the archive (read header/directory only).
1. **List** members (names, uncompressed sizes, type) — metadata only; no decompression yet.
1. **Filter** by extension (allowed content types) and `max_inner_size`; skip directories and oversized members.
1. **Decompress only** the members that passed the filter; scan each in turn (temp or memory), then discard.

So we first **evaluate** what’s inside (names and extensions) and only **dig deeper** (decompress and ingest) for members we intend to scan. This is safer for resource use and archive bombs: we never materialise the full archive at once. Implemented in `core/archives.iter_archive_members` (ZIP: `namelist` + `getinfo` then `read(name)` per member; TAR: `getmembers` then `extractfile(member)`; 7z: `files_list` then `read(targets=[...])`).

---

## Design: config, CLI, API, dashboard

### Config

- **`file_scan.scan_compressed`** (boolean, default `false`).

  When `true`, filesystem (and share connectors that use the same file-scan logic) will:

- Consider files whose extension is in the “compressed extensions” set.
- Validate by magic bytes where defined.
- Open archive and iterate members; for each member that is a supported content type (by inner extension), extract to memory (or temp file if too large), run the same sensitivity detection as for regular files, and save findings with path like `archive.zip|path/inside.txt`.

- Optional: **`file_scan.scan_compressed_max_inner_size`** (integer, default e.g. 10_000_000 bytes) to skip extracting members larger than N bytes to avoid memory spikes (configurable or documented).

- Optional: **`file_scan.scan_compressed_extensions`** (list) to restrict which archive types to open (e.g. only `[".zip", ".tar.gz", ".7z"]`). If absent, use the full Tier 1 + Tier 2 list.

- **Password-protected archives:** When opening zip, 7z, or other archives that may be password-protected, support **optional passwords** so the boar can scan locked archives when the user supplies them. Reuse or extend the existing **`file_scan.file_passwords`** mechanism (see USAGE): e.g. keys like `".zip"`, `".7z"`, or `"default"` mapping to password strings. Document how to supply archive passwords in config and in this plan’s docs so users who discover they need it can enable it without breaking the app.

### CLI

- **`--scan-compressed`** (flag).

  When present, overrides config: act as if `file_scan.scan_compressed: true` for that run. When absent, use config value (default false).
  So: no change to default behaviour; explicit opt-in.

### API and dashboard

- **POST /scan (and /start) body:** add optional **`scan_compressed`** (boolean). If `true`, merge into config for that run (e.g. engine or loader applies override for the single run). If omitted, use config.
- **Dashboard:** add a **checkbox** “Also scan inside compressed files (zip, tar, 7z, …)” next to tenant/technician. When checked, send `scan_compressed: true` in the JSON body when starting the scan. When unchecked, omit (config wins). Optional: show a short note that this may increase run time and I/O.

---

## Resource exhaustion and user warning

When implementing **scan inside compressed files**, ensure we do **not** run into resource exhaustion and that users understand the risks when they enable the option.

- **Filesystem and disk:** Extracting archives (especially large or many) can consume significant **disk space** (temp directories) and **inode / filesystem limits** on some systems. Use configurable `scan_compressed_max_inner_size` and, if extracting to temp files, consider a **max total temp usage** or cleanup policy so one run does not fill the disk.
- **Memory:** Prefer in-memory extraction only for members under a size limit; for larger members use a temp file or skip, to avoid memory spikes and OOM.
- **Time and I/O:** Scanning inside archives is more **compute- and I/O-intensive**. Document this clearly and, in the dashboard/CLI, **explain the risk** when the user enables the option: e.g. "Scanning inside compressed files may significantly increase run time, disk usage, and I/O; enable only when needed and ensure sufficient disk space and memory."
- **Documentation:** In USAGE, TECH_GUIDE, and dashboard help, state that enabling scan-inside-compressed can lead to higher resource use and that users should ensure adequate disk space and consider running during off-peak or with limited scope first.

**Reminder:** Before marking this plan complete, add guards (max inner size, optional max temp usage) and user-facing text that explains these risks so operators can make an informed choice.

---

## Implementation outline

1. **Config (loader)**
   - In `normalize_config`, add `file_scan.scan_compressed` (default False) and, if desired, `scan_compressed_max_inner_size` and/or `scan_compressed_extensions`.
   - Pass through to engine and connectors.

1. **CLI (main.py)**
   - Add `--scan-compressed` argument.
   - After loading config, if `--scan-compressed` is set, set `config["file_scan"]["scan_compressed"] = True`.

1. **Archive detection helper (e.g. in connectors or a small module)**
   - `COMPRESSED_EXTENSIONS` (set of suffixes).
   - `read_magic(path, n=32)` → bytes.
   - `is_zip(path)`, `is_gzip(path)`, `is_7z(path)`, etc. using magic.
   - `open_archive(path)` → context manager or iterator that yields (member_name, readable_bytes_or_path) for each member we support scanning (by inner extension in SUPPORTED_EXTENSIONS or a subset).
   - Prefer in-memory extraction for small members; temp file or skip for members over `scan_compressed_max_inner_size` if implemented.

1. **Filesystem connector**
   - Constructor: accept `scan_compressed` (and optional max_inner_size, compressed_extensions).
   - In `run()`, when iterating files:
     - If `scan_compressed` is false, keep current behaviour (no change).
     - If true and file’s extension is in compressed set:
       - Validate magic; if not valid, skip or save_failure and continue.
       - Open archive, iterate members; for each member with a supported content extension, extract, run `_read_text_sample` (or equivalent) on the extracted buffer/path, run scanner, then `save_finding` with `path` = parent path, `file_name` = `archive.zip|member/path.csv` (or similar) so reports clearly show “inside archive”.
     - Do not double-count: a file `data.zip` should not also be scanned as a normal file; when we handle it as an archive, skip the “normal file” branch.

1. **Share connectors (SMB, WebDAV, SharePoint, NFS)**
   - They use the same `extensions` and often download a file then call similar “read content and scan” logic. When `scan_compressed` is true and the downloaded file has a compressed extension, run the same “open archive and scan members” logic (e.g. write to temp file, then use the same helper).
   - Optional for v1: only enable “scan inside archives” in the **filesystem** connector and document that share connectors may follow in a later step; or implement for all in one go if the refactor is small.

1. **Engine**
   - When building the filesystem (and share) connector(s), pass `scan_compressed` and related options from `config["file_scan"]`.
   - For API-triggered runs, accept run-time override from request body and merge into config for that run only.

1. **API (routes)**
   - Extend `ScanStartBody` with `scan_compressed: bool | None = None`.
   - In `start_scan`, if `body.scan_compressed is True`, set the engine’s config (or a run-local override) so that the next `_run_target` uses `scan_compressed=True` for file targets.

1. **Dashboard template**
   - Add checkbox “Also scan inside compressed files” and include its value in the POST /scan body when starting a scan.

1. **Report**
   - Findings already have `path` and `file_name`. Ensure `file_name` (or path) for inner content uses a clear convention (e.g. `archive.zip|folder/file.csv`). No change to Excel/heatmap schema beyond ensuring this string is shown; optionally add a column or note “Inside archive” when `file_name` contains `|`.

---

## Dependencies and extras

- **Tier 1:** No new dependencies (stdlib only).
- **Tier 2:** Add **py7zr** as optional dependency. Option A: add to main `dependencies` in pyproject.toml (small, pure Python where possible). Option B: add under optional extra, e.g. `[project.optional-dependencies] compressed = ["py7zr>=0.20.0"]`, and document that installing `.[compressed]` enables 7z support.

  Recommendation: **optional extra** so default install stays minimal; when py7zr is missing and we encounter a .7z file, skip with a clear log or save_failure reason (“7z support not installed”). **Implemented:** `pip install -e ".[compressed]"` or `uv sync --extra compressed` enables 7z; see pyproject.toml.

---

## Tests

1. **Unit: magic detection**
   - Create small binary files (zip, gz, 7z, tar) with correct magic bytes; assert `is_zip`, `is_gzip`, etc. return True.
   - Create a file with .zip extension but wrong magic; assert we do not open it as zip (or get a safe error).

1. **Unit: option off**
   - With `scan_compressed=false`, run filesystem connector on a directory that contains a .zip with PII inside; assert the .zip is **not** opened and no findings from inside the zip (existing behaviour).

1. **Unit: option on**
   - With `scan_compressed=true`, run filesystem connector on a directory containing a .zip with a .txt or .csv inside that contains PII; assert we get at least one finding with `file_name` like `test.zip|inner.txt` (or similar).

1. **Unit: nested archives (optional)**
   - Decide whether to support “zip inside zip” in v1 (can be resource-heavy). If yes, add test; if no, document “one level only” and add test that we do not recurse.

1. **Integration**
   - Run full pytest suite with `-W error`; ensure no regressions. Add a test that runs a one-shot scan with `--scan-compressed` and config that has a filesystem target with a zip in it, and assert findings or session metadata as expected.

1. **API**
   - Test POST /scan with `scan_compressed: true` in body and verify the scan runs with the option (e.g. by having a zip in the target and asserting findings or status).

---

## Documentation

- **USAGE.md / USAGE.pt_BR.md:** In “file_scan” section, add `scan_compressed`, optional `scan_compressed_max_inner_size` and `scan_compressed_extensions`; list supported archive formats (Tier 1 and 2) and note that validation uses magic bytes; mention that this can increase run time and I/O.
- **TECH_GUIDE.md / TECH_GUIDE.pt_BR.md:** Same in the configuration section; add “Compressed files (optional)” subsection.
- **Man pages (data_boar.1, data_boar.5):** Document `--scan-compressed` and config keys.
- **Dashboard Help (help.html):** Short sentence that “Also scan inside compressed files” enables scanning inside zip, tar, 7z, etc., and may increase run time.
- **README (root):** Optional one line in the “data soup” or technical overview: “Optionally scan inside compressed files (zip, tar, 7z, …) when enabled.”

---

## Possible future extensions (more “data soup” ingredients)

- **Test data (samples):** `tests/data/compressed/` holds sample archives (e.g. sample1.zip, sample2.7z, sample3.tgz, sample4.tar.bz2). Optional later: small .tar.gz for CI; RAR/ARJ only when/if support is added. Keep set small for test time/resources.
- **Password-protected archive sample:** Add at least one password-protected compressed file (or create one programmatically in tests) to validate `file_scan.file_passwords` for archives (e.g. ZIP/7z with password) in a future test.
- **Max members per archive:** Optional cap (e.g. 1000 members per archive) as an extra guard in a follow-up to tighten resource limits and mitigate archive bombs.
- **Tier 3 archives:** LHA, ARJ, ZOO, PAK, ARC, ACE — via patool + external tools or dedicated libs; document and gate behind same option.
- **Nested archives:** Zip-inside-zip (and tar inside zip, etc.) with a depth limit and size limit to avoid bombs.
- **Other data sources not yet aimed for:**
- **Cloud blob storage:** **Planned** as a dedicated connector plan — [PLAN_OBJECT_STORAGE_CLOUD_CONNECTORS.md](../PLAN_OBJECT_STORAGE_CLOUD_CONNECTORS.md) (S3-class first, then Azure Blob, GCS). Reuses the same file/archive logic after list + fetch.
- **Google Drive / OneDrive API:** List and download files (and optionally open archives).
- **Email stores:** IMAP, Exchange (already have .eml/.msg; could add “mailbox” as a target type).
- **Container images:** Scan layers or extracted rootfs for config files and DBs (advanced).

  These can be added as separate plans or “possible steps” in this plan once compressed-file support is stable.

---

## To-dos (sequential)

**Current status:** All steps 1–12 are done. Share connectors (SMB, WebDAV, SharePoint) now apply the same “scan inside compressed” logic when `scan_compressed` is true; NFS already used FilesystemConnector so it was covered. See “Notes to remind later” below for optional follow-ups.

| #   | To-do                                                                                                                                                                                                                         | Status     |        |
| --- | -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------                         | ------     |        |
| 1   | Add config keys: `file_scan.scan_compressed` (default false), optional `scan_compressed_max_inner_size`, optional `scan_compressed_extensions`; normalize in config/loader.py and pass to engine/connectors                   | ✅ Done     |        |
| 2   | Add CLI argument `--scan-compressed` in main.py; override config for that run when present                                                                                                                                    | ✅ Done     |        |
| 3   | Implement archive detection: COMPRESSED_EXTENSIONS set, read_magic(), is_zip/is_gzip/is_7z/… by magic bytes; add small module or section in connectors                                                                        | ✅ Done     |        |
| 4   | Implement “open archive and iterate members” helper: ZIP (zipfile), TAR/GZ/BZ2/XZ (tarfile), 7z (py7zr, optional); yield (member_name, content_or_path) for members with supported content extensions; respect max_inner_size | ✅ Done     |        |
| 5   | In FilesystemConnector: accept scan_compressed (and options); when true, for files with compressed extension validate magic, open archive, scan inner members, save_finding with path like archive.zip\                       | inner path | ✅ Done |
| 6   | Add py7zr to optional extra `[compressed]` in pyproject.toml; handle missing py7zr when .7z is encountered (skip with reason or save_failure)                                                                                 | ✅ Done     |        |
| 7   | Engine: pass scan_compressed (and options) from config to filesystem/share connectors; support run-time override from API body for that run                                                                                   | ✅ Done     |        |
| 8   | API: extend ScanStartBody with scan_compressed; in start_scan apply override to config for that run; dashboard: add checkbox and send scan_compressed in POST body                                                            | ✅ Done     |        |
| 9   | Share connectors (SMB, WebDAV, SharePoint, NFS): when scan_compressed true, apply same “open archive and scan members” logic for downloaded files with compressed extension (or document “filesystem only” for v1)            | ✅ Done     |        |
| 10  | Tests: magic detection; scan_compressed=false no archive opening; scan_compressed=true findings from inside zip/tar; no regression in full suite                                                                              | ✅ Done     |        |
| 11  | Docs: USAGE, TECH_GUIDE, man pages, help.html, README (EN and pt-BR) for scan_compressed and --scan-compressed                                                                                                                | ✅ Done     |        |
| 12  | Resource exhaustion: enforce max_inner_size and optional temp caps; document and show user warning (dashboard + docs) when enabling scan-inside-compressed (disk, I/O, run time risks)                                        | ✅ Done     |        |

**Sync:** When a step is done, mark **✅ Done** in this table and in [PLANS_TODO.md](../PLANS_TODO.md) so both stay in sync.

---

## Notes to remind later

Follow-ups or optional improvements, **ordered by recommended execution** under typical token/session constraints (smallest-scope, high-value first):

1. **Password-protected archives:** Add a test (and optionally sample data) that uses `file_scan.file_passwords` for ZIP/7z so we validate the config path end-to-end. (Focused change; existing config.)
1. **Max members per archive:** **Done** in [#1233](https://github.com/FabioLeitao/data-boar/issues/1233) / [PLAN_ARCHIVE_BUDGET.md](../PLAN_ARCHIVE_BUDGET.md) (`file_scan.max_members`, default 1000).
1. **Optional max temp / total uncompressed:** Aggregate **declared** uncompressed sum + expansion ratio shipped with #1233 (`max_total_uncompressed`, `max_expansion_ratio`). Optional disk/temp cleanup policy remains follow-up.
1. **Nested archives:** Zip-inside-zip (and tar inside zip) with a depth limit and size limit; document “one level only” for v1 or add recursion with a cap. (Larger design/code scope.)
1. **Tier 3 archives:** LHA, ARJ, ZOO, PAK, ARC, ACE — via patool + external tools or dedicated libs; document and gate behind the same `scan_compressed` option. (New deps/formats.)
1. **Test data:** RAR/ARJ samples only when/if support is added; keep test set small for CI. (Do when touching those formats.)

---

## Last updated

- **2026-04-20:** Header **Status** aligned with completed steps 1–12 and [PLANS_TODO.md](../PLANS_TODO.md) (drift fix).
