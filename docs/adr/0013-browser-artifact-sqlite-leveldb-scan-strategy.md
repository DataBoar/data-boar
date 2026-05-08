# ADR 0013: Browser artifact scanning — SQLite (default) + LevelDB (opt-in) strategy

**Status:** Accepted
**Date:** 2026-04-03
**Authors:** Fabio Leitao

## Context

Modern browsers (Chrome, Edge, Firefox, Safari) store a significant amount of user data in
structured local databases on disk. These files are relevant to LGPD/GDPR compliance scanning
because they can contain:

- Browsing history, search terms, and download paths (History)
- Cookie names and domains, revealing tracking patterns (Cookies)
- Autofill form data including names, addresses, phone numbers (Web Data / formhistory)
- Saved plaintext usernames (Login Data)
- Cached API responses and session tokens in localStorage (LevelDB / IndexedDB)

Two storage technologies are in play:

1. **SQLite** — Chrome (`History`, `Cookies`, `Web Data`, `Login Data`), Firefox
   (`places.sqlite`, `cookies.sqlite`, `formhistory.sqlite`), and most Electron/browser-based apps.
   Files use the standard `.sqlite` / `.sqlite3` / `.db` extension or sometimes **no extension**
   (Chrome uses bare filenames like `History`, `Cookies`).

2. **LevelDB** — Chrome's localStorage and IndexedDB storage engine. These are **directories**
   containing `.ldb` log files, a `MANIFEST-*` file, and a `CURRENT` pointer — not a single file.
   Requires the `plyvel` (or `leveldb`) Python library for reading.

Three decisions are needed: **how to handle locked files**, **how to handle encrypted values**,
and **whether to support LevelDB** (and at what priority).

---

## Decision

### 1. SQLite browser artifacts — default, already implemented

The filesystem connector's `scan_sqlite_as_db: true` (default) already opens any
`.sqlite` / `.sqlite3` / `.db` file via SQLAlchemy and runs sensitivity detection on column
names and sampled row values. Chrome/Firefox SQLite databases fit this path transparently.

**Locked file handling:** Chrome and Firefox use WAL (Write-Ahead Log) mode. Reading a WAL-mode
SQLite while the browser is running may either:

- Succeed (SQLite allows concurrent readers in WAL mode), or
- Fail with `SQLITE_BUSY` / `database is locked` if the write lock is held.

**Decision:** Treat locked SQLite files as a **graceful-skip with WARNING** — the connector
already catches exceptions per-file and logs them. Document in USAGE that browser artifact scans
should be run with the browser closed or against backup copies (Time Machine, VSS, iTunes/Finder
backup). Do **not** implement automatic copy-on-scan as that doubles I/O and complicates audit
trails; leave copy-before-scan to the operator.

**Encrypted values (Chrome cookies, Login Data):** Chrome encrypts cookie *values* and saved
passwords with OS key stores (DPAPI on Windows, KeyColleague-Nn on macOS/Linux Gnome Keyring). The
scanner will see:

- Column **names** (`host_key`, `name`, `path`, `is_secure`, `creation_utc`, ...) — still useful
  for compliance (reveal tracker domains and session cookie names).
- Encrypted **blobs** as binary values — reported as non-text and not matched by regex patterns.

**Decision:** Accept this limitation. Document that column-name sensitivity detection works;
value decryption is **out of scope** (requires OS-level secret access, user consent, and is
outside the stated threat model of filesystem scanning). Flag the limitation in USAGE and in
scan output via the existing `reason: encrypted or binary` path.

**Files without extension:** Chrome's `History`, `Cookies`, `Web Data`, `Login Data` have no
`.sqlite` extension. They are only scanned if `file_scan.use_content_type: true` is set and
magic-byte detection identifies them as SQLite (`SQLite format 3\x00` at offset 0).

**Decision:** Rely on `use_content_type` for extension-less Chrome files; document this in USAGE
under the browser-artifacts section. No special-casing of bare Chrome filenames.

### 2. LevelDB — opt-in, future

LevelDB storage is **directory-based** (not a single file), requires the `plyvel` library
(native C extension, heavier than SQLite), and the data model (key-value with binary keys and
serialised JavaScript values) requires bespoke parsing for each Chrome subsystem.

**Decision:** Implement LevelDB scanning as **opt-in** (`file_scan.scan_leveldb: true`, default
`false`), behind an optional extra `[browserartifacts]` in `pyproject.toml`. A dedicated
`_scan_leveldb_dir` helper (similar to `_scan_sqlite_file_as_db`) will detect LevelDB
directories by the presence of a `CURRENT` file and at least one `.ldb` file, enumerate keys,
decode values where possible (UTF-8 string fallback), and sample for sensitivity detection.

This ADR records the decision and reserves the `file_scan.scan_leveldb` config key and
`[browserartifacts]` extra name for when the feature is implemented.

### 3. HAR, vCard, iCalendar, plist — see data soup plan (Tier 5)

These are Tier 5 format additions documented in
[PLAN_ADDITIONAL_DATA_SOUP_FORMATS.md](../plans/PLAN_ADDITIONAL_DATA_SOUP_FORMATS.md) Sec 5B-5C.
They do not require a separate ADR; they follow the same pattern as existing Tier 1 format
additions (add extension, add extractor, run sensitivity detection).

---

## Consequences

**Positive:**

- Chrome/Firefox history, autofill, and cookie metadata are immediately scannable with zero
  additional code (operators who already use Data Boar get this "for free" via `scan_sqlite_as_db`).
- Locked-file graceful-skip means scans do not crash on active browser sessions.
- LevelDB reserved for a clean opt-in path without forcing a C extension dependency on all users.
- Encrypted-value limitation is documented rather than silently ignored.

**Negative / trade-offs:**

- Extension-less Chrome files require `use_content_type: true` — a second flag operators must
  know about; mitigate with USAGE documentation.
- WAL-locked scans may produce incomplete results without a clear error unless the operator checks
  the scan log; mitigate with explicit WARNING log entries per skipped file.
- LevelDB deferred — operators who need IndexedDB / localStorage scanning must wait for a
  future release.

---

## References

- [PLAN_ADDITIONAL_DATA_SOUP_FORMATS.md](../plans/PLAN_ADDITIONAL_DATA_SOUP_FORMATS.md) Tier 5
- [PLAN_HEIC_APPLE_IMAGE_SUPPORT.md](../plans/PLAN_HEIC_APPLE_IMAGE_SUPPORT.md) — analogous
  opt-in pattern for `pillow-heif`
- [PLAN_COMPRESSED_FILES.md](../plans/PLAN_COMPRESSED_FILES.md) — opt-in pattern for archives
- [docs/USAGE.md](../USAGE.md) — browser artifacts guidance (to be added when Tier 5 ships)
