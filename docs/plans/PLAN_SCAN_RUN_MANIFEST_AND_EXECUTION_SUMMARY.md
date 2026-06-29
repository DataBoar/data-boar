# Plan: Scan run manifest and execution summary

**Status:** Pending
**Date:** 2026-05-12
**Authors:** Fabio Leitao
**Priority:** H2
**Depends on:** ADR-0037, ADR-0048, ADR-0049

<!-- plans-hub-summary: Customer-facing run manifest: structured execution summary (connectors, counts, skips, errors, version) emitted per scan as an Excel sheet and optional JSON file. Closes the gap between host-bound audit log and customer-visible evidence. -->
<!-- plans-hub-related: completed/PLAN_SQL_SAMPLING_SRE_AND_AUDIT_EVIDENCE.md, PLAN_ADDITIONAL_DETECTION_TECHNIQUES_AND_FN_REDUCTION.md -->

## Purpose

A Data Boar scan today produces a findings report (Excel) and a host-bound audit log
(`audit_YYYYMMDD.log`). An operator or DPO who receives the Excel file cannot answer
from the file alone:

- Which connectors and targets were configured for this run?
- How many columns were sampled vs. skipped, and why?
- What version of Data Boar produced this evidence?
- How long did the scan take? Were there errors?

The audit log answers some of these, but it is **host-bound** — customers and their legal
or compliance teams cannot read it. ADR-0049 Decision 1 requires that skips appear in
report output, not only in the log. ADR-0048 requires deterministic, stable output schema.
This plan creates the artefact that satisfies both contracts in a customer-facing form.

## Problem framing

A DPO presenting a Data Boar report to an auditor or a regulatory body must be able to
attest to the **completeness and provenance** of the scan:

> "This report was produced by Data Boar v1.4.2 on 2026-05-10, scanning 3 SQL targets
> and 1 filesystem. 340 columns were sampled; 3 were skipped due to permission errors.
> No errors occurred. Config hash: abc123."

Without a structured manifest, that attestation requires reconstructing context from logs,
config files, and memory. With a manifest, it is a one-line read from the report itself.

## Slices

| Slice | Focus | Delivers |
| ----- | ----- | -------- |
| **1 — Core manifest (proposed)** | Structured run summary in report | New `_Run Summary` sheet in every Excel output (always emitted, never skipped). Fixed schema: `run_id` (UUID), `data_boar_version`, `started_at` (ISO 8601 UTC), `duration_s`, `config_hash` (SHA-256 of resolved config), `connectors_used` (list), `targets_scanned` (count), `columns_sampled` (count), `columns_skipped` (count + reason list), `findings_total`, `errors` (count + brief list). Empty fields use explicit `0` or `[]`, never absent. |
| **2 — JSON sidecar (proposed)** | Machine-readable parallel output | Emit `run_manifest_YYYYMMDD_HHMMSS.json` alongside the Excel when `--manifest-json` flag is set (or `report.emit_json_manifest: true` in config). Schema mirrors the Excel sheet. Enables downstream automation (BI tools, SIEM ingestion, CI assertions). |
| **3 — CLI summary (proposed)** | Operator-facing terminal output | Print a compact run summary to stdout on scan completion — same fields as Slice 1, condensed. Satisfies operators who consume CLI output in CI pipelines without opening the Excel file. |
| **4 — Manifest schema contract (future)** | ADR + versioned schema | Once Slice 1 schema stabilises across 2+ releases, create ADR for the manifest schema as a versioned, breaking-change contract (aligned with ADR-0048 deterministic-output-ordering bullet). |

## Schema (Slice 1 — `_Run Summary` sheet)

| Field | Type | Example | Notes |
| ----- | ---- | ------- | ----- |
| `run_id` | string (UUID4) | `a1b2c3d4-...` | Generated at scan start |
| `data_boar_version` | string | `1.4.2` | From `core/about.py` |
| `started_at` | string (ISO 8601 UTC) | `2026-05-10T14:32:00Z` | Scan start wall clock |
| `duration_s` | float | `47.3` | Wall time, not CPU time |
| `config_hash` | string (SHA-256, 8 chars) | `abc12345` | Hash of resolved config dict |
| `connectors_used` | string (comma list) | `sql, filesystem` | Active connector types |
| `targets_scanned` | int | `4` | Connectors with ≥1 result or attempt |
| `columns_sampled` | int | `340` | Columns with ≥1 row returned |
| `columns_skipped` | int | `3` | Columns skipped for any reason |
| `skip_reasons` | string (list) | `col_x: permission denied; ...` | One entry per skip; max 50 shown |
| `findings_total` | int | `47` | Total findings across all targets |
| `errors` | int | `0` | Connector-level errors (not skips) |
| `error_details` | string | `` | Brief description; empty if 0 |

## Implementation notes

- `_Run Summary` uses leading underscore so Excel sorts it before findings sheets.
- `run_id` is generated once per `AuditEngine.run()` call and passed to the report generator.
- `config_hash` hashes the **resolved** config dict (after normalization), not the raw YAML
  bytes — so whitespace-only changes do not alter the hash.
- Skip counter increments in connector `sample()` / `scan()` paths where ADR-0049 Decision 1
  already requires a log line; the manifest collects from the same counter.
- The sheet is always emitted even when `findings_total == 0` — an empty findings report
  with a manifest is more useful than an ambiguous empty file.

## Acceptance criteria (Slice 1)

- [ ] `_Run Summary` sheet present in every Excel output regardless of finding count.
- [ ] `columns_skipped` count matches the number of explicit skip log lines for that run.
- [ ] `data_boar_version` matches `core/about.py` (guarded by `tests/test_about_version_matches_pyproject.py`).
- [ ] Schema fields are stable (column names do not change between runs on the same config).
- [ ] Tests cover: zero-findings run, run with skips, multi-connector run.

## Related ADRs

- [ADR-0037 — Data Boar self-audit log governance](../adr/ADR-0037-data-boar-self-audit-log-governance.md)
- [ADR-0048 — Operator-facing taxonomy and naming contract preservation](../adr/ADR-0048-operator-facing-taxonomy-and-naming-contract-preservation.md)
- [ADR-0049 — No brittle mitigations — robust input handling](../adr/ADR-0049-no-brittle-mitigations-robust-input-handling.md)
