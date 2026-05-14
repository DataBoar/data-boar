# Plan: Incremental scan idempotency — file fingerprinting and skip-unchanged

**Status:** Active
**Date:** 2026-05-14
**Authors:** Fabio Leitao
**Priority:** H2
**Depends on:** ADR-0051 (this plan's own decision record)
**Related:** [PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md](PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md) (SQLite anchor, startup re-verify), [PLAN_SQL_SAMPLING_SRE_AND_AUDIT_EVIDENCE.md](PLAN_SQL_SAMPLING_SRE_AND_AUDIT_EVIDENCE.md) (audit evidence pattern)

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)

---

## Context and motivation

Each `AuditEngine.start_audit()` call treats every target as a fresh corpus: the
`FilesystemConnector` walks the tree, reads a sample of every eligible file, runs
the detector, and inserts a new `FilesystemFinding` row — regardless of whether
the file changed since the last run.

For recurring scans (scheduled audits, CI integration, managed-service delivery)
this means:

- **Wasted resources**: identical files are sampled and detected again on every run.
- **Audit noise**: findings accumulate per-session with no link to prior identical
  findings, making diff-based review harder.
- **Non-SRE posture**: an SRE-grade tool must be able to answer "what changed since
  the last scan?" — not just "what exists now".

This plan introduces a **three-phase** incremental scan capability:

- **Phase 1 (schema + state capture):** record file identity (`mtime_ns`, `size`,
  `content_fingerprint`) on each `FilesystemFinding` row; zero behavioural change.
- **Phase 2 (state index):** add a `scan_object_state` auxiliary table; upserted
  after every finding or clean-pass; enables cross-session diff queries.
- **Phase 3 (short-circuit):** add `file_scan.incremental: true` config flag;
  connector skips files whose identity matches the last completed session for the
  same target, optionally re-emitting prior findings or recording a `scan_event`
  (type=unchanged).

Phases are **additive and backward-compatible**. Existing behaviour is unchanged
unless the operator opts in (`incremental: true` in Phase 3).

---

## Phase 1 — File identity on FilesystemFinding (schema + collect)

### 1.1 Schema additions (additive)

Extend `FilesystemFinding` in `core/database.py` with three nullable columns:

```python
source_mtime_ns     = Column(BigInteger, nullable=True)
# Path.stat().st_mtime_ns at scan time (nanoseconds since epoch, platform int)

source_size         = Column(BigInteger, nullable=True)
# Path.stat().st_size at scan time (bytes)

content_fingerprint = Column(String(16), nullable=True)
# blake2s(sampled_bytes, digest_size=8).hexdigest()  — fast, non-crypto, 16 hex chars
# computed on the same byte slice used for detection (file_sample_max_chars)
```

**Migration:** SQLite `ALTER TABLE … ADD COLUMN` (nullable, no default) — safe on
existing databases; new installs get all three columns via `Base.metadata.create_all`.

**Why `blake2s` over sha256:** 8-byte blake2s is ~3× faster, outputs 16 hex chars,
and is sufficient for *change detection* (not cryptographic integrity). Operator may
override digest algorithm in Phase 2+ if needed.

### 1.2 Stat collection in FilesystemConnector

Before calling `_read_text_sample`, call `file_path.stat()` and store the result.
After detection, pass `source_mtime_ns`, `source_size`, and `content_fingerprint`
to `save_finding`.

The fingerprint is computed from the same raw bytes returned by `_read_text_sample`
(before text decoding), truncated to `file_sample_max_chars * 4` bytes (worst-case
UTF-8 expansion). If stat or fingerprint computation fails, fields are stored as
`None` — no scan abort.

### 1.3 Done criteria (Phase 1)

- [ ] `FilesystemFinding` has three new nullable columns; Alembic-free migration works.
- [ ] `FilesystemConnector._scan_path` passes stat+fingerprint to `save_finding`.
- [ ] `save_finding` accepts and persists the three new kwargs.
- [ ] `tests/test_filesystem_connector.py` (and/or dedicated test) verifies the
      fields are populated on a real scan of a temp directory.
- [ ] `tests/test_db_schema.py` (or equivalent) asserts the columns exist.
- [ ] No behaviour change in existing integration tests (fields are nullable/additive).

---

## Phase 2 — Object state index (cross-session diff enablement)

### 2.1 New table `scan_object_state`

```python
class ScanObjectState(Base):
    __tablename__ = "scan_object_state"
    id               = Column(Integer, primary_key=True, autoincrement=True)
    target_name      = Column(String(100), nullable=False, index=True)
    abs_path         = Column(String(512), nullable=False, index=True)
    last_session_id  = Column(String(64), nullable=False)
    mtime_ns         = Column(BigInteger, nullable=True)
    size             = Column(BigInteger, nullable=True)
    content_fingerprint = Column(String(16), nullable=True)
    last_sensitivity = Column(String(20), nullable=True)
    updated_at       = Column(DateTime, default=_utc_now, onupdate=_utc_now)
    __table_args__   = (UniqueConstraint("target_name", "abs_path"),)
```

### 2.2 Upsert after each finding

`LocalDBManager.upsert_object_state(target_name, abs_path, session_id, mtime_ns,
size, fingerprint, sensitivity_level)` — SQLite `INSERT OR REPLACE` or
`INSERT … ON CONFLICT DO UPDATE`.

### 2.3 Done criteria (Phase 2)

- [ ] Table created and migrated.
- [ ] `upsert_object_state` called from `FilesystemConnector` after each finding.
- [ ] `GET /status` or `--export-audit-trail` optionally includes `scan_object_state`
      summary (object count, distinct sessions).
- [ ] Test: two scans of the same dir; `scan_object_state` rows updated, not doubled.

---

## Phase 3 — Short-circuit / skip-unchanged (opt-in)

### 3.1 Config flag

```yaml
file_scan:
  incremental: false        # default; set true to skip unchanged files
  incremental_fingerprint: mtime_size   # mtime_size | content | both
```

`mtime_size`: skip when `mtime_ns` and `size` match prior state (fast, no read).
`content`: skip when `content_fingerprint` matches (requires read; catches clock-skew).
`both`: skip only when all three fields match.

### 3.2 Connector short-circuit

```python
if incremental_enabled:
    prior = db_manager.get_object_state(target_name, str(file_path))
    stat  = file_path.stat()
    if prior and _identity_matches(prior, stat, mode):
        metrics["skipped_unchanged"] += 1
        continue
```

When skipped, the connector records a `scan_event` row (new table or JSON log):
`{type: unchanged, path, session_id, reference_session_id, ts}`.

### 3.3 Done criteria (Phase 3)

- [ ] `file_scan.incremental` parsed and validated in config loader.
- [ ] Connector respects the flag; `skipped_unchanged` counter in session metrics.
- [ ] `scan_event` table or equivalent records skip events (append-only, reference_session_id).
- [ ] `GET /status` exposes `skipped_unchanged` count for the last session.
- [ ] Full regression: all existing tests green with `incremental: false` (default).
- [ ] Smoke test: incremental scan on an unchanged dir produces 0 new findings and
      correct `skipped_unchanged` count.

---

## Non-goals

- **Cryptographic tamper-evidence** for findings (see Build identity plan).
- **Database connector** incremental (schema is more complex; separate plan if needed).
- **Forced re-scan** of archive inner members when outer archive is unchanged (Phase 3
  may add `incremental_archives: false` flag to override).
- **Real-time filesystem watching** (inotify/FSEvents) — out of scope.

---

## ADR pointer

Decision recorded in **ADR-0051** — fingerprint algorithm choice, skip policy,
config flag contract, and non-goals re: cryptographic integrity.

---

## Gemini / triage notes

Not yet reviewed externally. Promote external review findings to this plan's
to-do table when received.
