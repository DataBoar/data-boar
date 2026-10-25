# Plan: Audit log PII self-scan gate before export (#877)

**Status:** In Progress
**Date:** 2026-09-11
**Authors:** Fabio Leitao
**Priority:** H2
**Depends on:** [ADR-0036](../adr/ADR-0036-exception-and-log-pii-redaction-pipeline.md) (first-layer log sanitization)

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md) (*Integration / active threads*), GitHub [#877](https://github.com/DataBoar/data-boar/issues/877) (milestone **v1.8.0**)

<!-- plans-hub-summary: Second-layer dogfood gate — scan audit_*.log with DEFAULT_PATTERNS before GET /logs export; block serve + Audit Trail finding (counts only). -->
<!-- plans-hub-related: PLAN_SECRETS_AND_VAULT.md, ../../SECURITY.md, ../../docs/primers/FORENSICS_AND_EVIDENCE_PRIMER.md -->

## Purpose

Data Boar claims **metadata-only, vaultless** operation: audit text logs should not carry cleartext PII even when a bug, traceback, or direct `logger` call bypasses the first-layer **`sanitize_log_text`** pipeline ([ADR-0036](../adr/ADR-0036-exception-and-log-pii-redaction-pipeline.md)).

Issue **#877** adds a **second layer**: before **`GET /logs`** / **`GET /logs/{session_id}`** serve an `audit_YYYYMMDD.log` attachment, run the same built-in regex families as **`core.detector.DEFAULT_PATTERNS`**. **Clean → serve.** **Dirty → block export**, record an **Audit Trail** taxonomy finding (category + count only — **never** matched substrings), return a structured API error without the raw log body.

This complements (does not replace) write-time redaction in **`utils/logger.py`**.

## Slices (sequencing)

| Slice | Focus | Status |
| ----- | ----- | ------ |
| **1 — Self-scan core** | `core/log_self_scan.py`: `scan_text_for_pii(text) -> dict[str, int]` reusing `DEFAULT_PATTERNS`; counts only | ✅ Shipped (this PR) |
| **2 — Export gate** | `_audit_log_file_response` in `api/routes.py`; `log_audit_trail_finding` in `utils/logger.py`; HTTP **422** with `categories` map, no raw log in error body | ✅ Shipped (this PR) |
| **3 — CI regression** | `tests/test_log_self_scan.py`: clean fixture serves; contaminated fixture blocks without cleartext in response | ✅ Shipped (this PR) |
| **4 — Write-time hardening (future)** | Optional scan-on-append or periodic scan of open audit file; CLI export paths beyond `/logs` | ⬜ Pending |

## Acceptance criteria (#877)

- PLAN + `plans_hub_sync` + PLANS_TODO row.
- Reuse patterns from `core/detector.py` — no duplicated regex table.
- Deterministic redaction policy at write time unchanged; self-scan is verification + export gate.
- **Do not log the match** — only category name + count in findings and API error payload.

## Code map

- **`core/log_self_scan.py`** — `scan_text_for_pii`, compiled `DEFAULT_PATTERNS` (excludes `DATE_DMY`, aligned with ADR-0036 log redaction).
- **`utils/logger.py`** — first-layer `sanitize_log_text`; **`log_audit_trail_finding`** for blocked exports.
- **`api/routes.py`** — `_audit_log_file_response`, `GET /logs`, `GET /logs/{session_id}`.
- **`core/detector.py`** — `DEFAULT_PATTERNS` source of truth.
- **`tests/test_log_self_scan.py`** — unit + TestClient export gate tests.

## References

- GitHub [#877](https://github.com/DataBoar/data-boar/issues/877)
- [ADR-0036](../adr/ADR-0036-exception-and-log-pii-redaction-pipeline.md)
- [TECH_GUIDE.md](../TECH_GUIDE.md) — audit log export + self-scan note
- [SECURITY.md](../SECURITY.md) — audit log protection table row
