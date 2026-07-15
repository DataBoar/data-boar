# Plan: Aggregate archive decompression budgets (anti zip-bomb / DoS)

<!-- plans-hub-summary: Aggregate archive budgets — max_members, max_total_uncompressed, max_expansion_ratio; fail-closed archive_budget_exceeded (#1233) -->

**Status:** Done
**Date:** 2026-07-15
**Authors:** Fabio Leitao
**Priority:** H1 / P2 security
**GitHub:** [#1233](https://github.com/FabioLeitao/data-boar/issues/1233)
**Promotes:** Notes #2/#3 in [PLAN_COMPRESSED_FILES.md](completed/PLAN_COMPRESSED_FILES.md) (*Notes to remind later*)
**Related:** #828 `scan_failures` taxonomy; per-member `max_inner_size` (unchanged)

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)

---

## Context

`file_scan.scan_compressed` already caps **per-member** uncompressed size (`max_inner_size`). That does not stop an archive with thousands of small members or a high **declared** expansion ratio (classic zip-bomb shape). Aggregate budgets close that gap at the single choke-point `core/archives.py::iter_archive_members`.

## Decision (shipped)

| Knob | Default (connector) | Config key | Role |
| ---- | ------------------- | ---------- | ---- |
| Member count | 1000 | `file_scan.max_members` | Bound enumeration + extraction |
| Declared uncompressed sum | 1 GiB | `file_scan.max_total_uncompressed` | Bound total declared sizes |
| Expansion ratio | 200 | `file_scan.max_expansion_ratio` | `total_uncompressed / archive_bytes` |

Checks use **declared** sizes **before** `z.read` / `extractfile` / `archive.read`. Exceeding any limit calls `on_member_read_failure` with reason **`archive_budget_exceeded`** and **stops** the generator (fail-closed, never silent). One-level archives only (no nested recursion) — unchanged from v1 compressed-files scope.

Invalid or missing YAML → `None` in loader; `scan_archive_at_path` always applies connector defaults (covers SMB / WebDAV / SharePoint when kwargs omitted).

## Out of scope

- Nested archive recursion
- Changing per-member `max_inner_size`
- Tier-3 formats

## Docs / tests

- Operator: [USAGE.md](../USAGE.md), [data_boar.5](../data_boar.5)
- Tests: `tests/test_archives_scan_failures.py`, `tests/test_filesystem_scan_compressed_wiring.py`, `tests/test_config_encoding.py`
