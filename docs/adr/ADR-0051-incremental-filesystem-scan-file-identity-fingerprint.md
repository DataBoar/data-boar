# ADR 0051 — Incremental filesystem scan: file-identity fingerprint contract

- **Status:** Accepted
- **Date (UTC):** 2026-05-14
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Context

Data Boar's `FilesystemConnector` currently treats every scan run as a full,
independent pass: it reads and detects every eligible file on each `AuditEngine`
invocation, regardless of whether the file has changed since the prior run.

For recurring audits — scheduled compliance scans, CI-gated data-residency checks,
managed-service delivery — this means wasted I/O and CPU, duplicate `FilesystemFinding`
rows across sessions with no explicit link between identical observations, and the
inability to answer the basic SRE question: *"what changed since the last scan?"*

Three design choices needed an explicit decision:

1. **What constitutes file identity** — which fields are sufficient to decide "unchanged"?
2. **Which fingerprint algorithm** to use for content-level equality?
3. **Where the skip decision lives** and what is recorded when a file is skipped.

## Decision

### D1 — File identity = (mtime_ns, size) as primary; content fingerprint as secondary

`st_mtime_ns` (nanosecond mtime) plus `st_size` covers the common case cheaply:
both are available from a single `Path.stat()` syscall before any file read.
A content fingerprint (`blake2s`, 8-byte digest) covers clock-skew edge cases and
gives auditors a stable content token independent of filesystem metadata.

The operator chooses the identity mode via `file_scan.incremental_fingerprint`:
- `mtime_size` (default): skip when both mtime_ns and size match prior state.
- `content`: skip when content_fingerprint matches (requires reading the sample).
- `both`: skip only when all three fields agree.

### D2 — blake2s (digest_size=8) for content fingerprinting; not SHA-256

`blake2s` with `digest_size=8` (64-bit) is:
- ~3× faster than SHA-256 on small inputs (CPython + OpenSSL).
- Available in Python stdlib (`hashlib.blake2s`); no new dependency.
- Sufficient for *change detection*: a 64-bit digest has collision probability
  < 10⁻¹⁸ for randomly differing files — not cryptographic evidence, but
  appropriate for skip-gating.

SHA-256 (or SHA-3) is explicitly **not** chosen for this field because:
- This is not a tamper-evidence hash (see Build identity plan for that role).
- Speed matters: this runs per-file on every scan, including large directories.
- The field is non-security-critical: a collision causes a missed finding update,
  not a security bypass.

The column is named `content_fingerprint` (not `content_hash`) to signal that it
is not a cryptographic commitment.

### D3 — Skip recording via append-only `scan_event` (Phase 3+); no silent drops

When a file is skipped, a `scan_event` row (or equivalent log entry) is written:

```
{type: unchanged, path, target_name, session_id, reference_session_id, ts}
```

This ensures:
- **Audit completeness**: a scan session record always reflects the full corpus,
  even for files with no new finding (unchanged).
- **Cross-session traceability**: `reference_session_id` links to the session
  that produced the prior finding, enabling differential reports.
- **Operator trust**: no file silently disappears from audit scope.

Silent drops (`continue` with no record) are rejected because they would make
an incremental scan indistinguishable from a partial-coverage scan.

### D4 — Feature is opt-in; default behaviour is unchanged

`file_scan.incremental: false` (default). Existing scans are unaffected.
The Phase 1 schema additions (new nullable columns on `FilesystemFinding`) are
backward-compatible: `NULL` in those columns means "not collected" — valid for
any scan run before Phase 1 was deployed.

## Consequences

**Positive:**

- Recurring scans can skip unchanged files cheaply (Phase 3); resource savings
  are proportional to the fraction of the corpus that did not change between runs.
- `FilesystemFinding` rows gain auditable file-identity fields from Phase 1 onward,
  even without the incremental feature enabled.
- Differential queries (`SELECT DISTINCT abs_path FROM scan_object_state WHERE …`)
  become possible after Phase 2 without schema churn.

**Negative / trade-offs:**

- `content_fingerprint` requires reading the file sample (same I/O as today) when
  `incremental_fingerprint: content` or `both`. No savings until `mtime_size` mode
  confirms the file is unchanged.
- `scan_object_state` grows proportionally to the number of unique file paths ever
  scanned; a `VACUUM` / retention policy may be needed for very large deployments
  (Phase 3 follow-up).
- `scan_event` table adds write volume proportional to skipped files in Phase 3;
  acceptable for expected deployment sizes (< 1 M files per scan).

**Non-goals (explicitly out of scope for this ADR):**

- Cryptographic tamper-evidence for `FilesystemFinding` rows (Build identity plan).
- Incremental scanning of database targets (separate schema concern).
- Real-time filesystem watching (inotify/FSEvents).
- Archive inner-member identity tracking (may extend Phase 3 later with
  `incremental_archives` override flag).

## Related

- [PLAN_INCREMENTAL_SCAN_IDEMPOTENCY.md](../../plans/PLAN_INCREMENTAL_SCAN_IDEMPOTENCY.md)
- [PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md](../../plans/PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md)
- [ADR-0043](ADR-0043-sql-column-sampling-non-null-and-strategy-hook.md) (SQL sampling audit evidence pattern)
- [ADR-0048](ADR-0048-operator-facing-taxonomy-and-naming-contract-preservation.md) (naming stability)
