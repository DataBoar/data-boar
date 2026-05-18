# Plan: CLI — config validation, session diff, DSAR-oriented export

**Status:** Pending
**Date:** 2026-05-14
**Authors:** Fabio Leitao
**Priority:** H1 U1
**Depends on:** Stable config loader and CLI entry (`main.py`); optional alignment with scan run manifest / execution summary output

<!-- plans-hub-summary: Operator CLI: validate YAML/config before scans, diff two scan sessions for regressions, and export DSAR-oriented evidence bundles (metadata-first) with documented limits—not legal advice. -->
<!-- plans-hub-related: PLAN_SCAN_RUN_MANIFEST_AND_EXECUTION_SUMMARY.md, PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md -->

## Purpose

GitHub tracks three related operator-facing capabilities:

- **[#520](https://github.com/FabioLeitao/data-boar/issues/520)** — **`--validate-config`** (or equivalent): fail fast on invalid YAML, unknown keys where the product defines strictness, broken connector prerequisites, and other **pre-flight** checks **without** running a full scan.
- **[#521](https://github.com/FabioLeitao/data-boar/issues/521)** — **`--diff`** (or equivalent): compare **two** saved scan sessions (SQLite paths or export bundles) and emit a **structured delta** (e.g. new/removed/changed findings counts, per-target drift) for regression triage and audit narration.
- **[#522](https://github.com/FabioLeitao/data-boar/issues/522)** — **`--export-dsar`** (or equivalent): produce a **bounded** export package suitable for **data-subject / DSAR-style** handoff—**metadata and findings summaries** by default, with **explicit** opt-in for any raw samples, and clear documentation that the tool assists **technical inventory**, not legal determination of rights or exemptions.

Together they close the gap between “I changed config / upgraded / rescoped targets” and “I can prove what changed in outcomes” for operators, DPOs, and security teams.

## Relationship to other plans

- **[PLAN_SCAN_RUN_MANIFEST_AND_EXECUTION_SUMMARY.md](PLAN_SCAN_RUN_MANIFEST_AND_EXECUTION_SUMMARY.md)** — When a per-run manifest or `_Run Summary` sheet exists, **`--diff`** and **`--export-dsar`** should **reuse** the same stable field names and versioning rules where feasible (ADR-0048 / ADR-0049 alignment).
- **[PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md](PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md)** — Audit export and integrity signals on **`--export-audit-trail`** should remain consistent; DSAR export must **not** weaken tamper-evidence narrative.

## Non-goals

- Replacing **eDiscovery** platforms or **legal** review workflows end-to-end.
- **Automatic** redaction of every file in scope for DSAR—scope stays **metadata-first** unless the operator explicitly opts into broader behavior documented in USAGE / TECH_GUIDE.

## Slices and acceptance criteria

### Slice A — Config validation (`#520`)

- [ ] CLI flag (name per `docs/OPERATOR_HELP_AUDIT.md` / `operator_help_sync_manifest.py`) parses config and exits **0** with a concise **OK** path; non-zero on invalid config with **actionable** messages (no secret values in stderr).
- [ ] **Tests:** at least one **positive** and one **negative** fixture; warnings policy matches project norm (`-W error` in CI).
- [ ] **Docs:** USAGE (EN + pt-BR) and man page stub if applicable; cross-link from TECH_GUIDE deploy/ops where config is edited.

### Slice B — Session diff (`#521`)

- [ ] Accepts two session references (paths / identifiers documented in USAGE); outputs **stable** JSON or text format suitable for scripting.
- [ ] Defines **ordering** and **identity keys** for findings (file path, column, rule id, etc.) so “same finding” is deterministic; document limitations when schema evolves.
- [ ] **Tests:** synthetic two-session fixture with known delta.

### Slice C — DSAR-oriented export (`#522`)

- [ ] Default export is **metadata-heavy**; any inclusion of **raw cell samples** requires **explicit** flags documented next to risk (retention, legal review).
- [ ] **README / SECURITY** posture: export does **not** become an exfiltration default; logs/audit trail mention export events where the product already logs scan lifecycle.
- [ ] **Tests:** golden export structure (redacted paths); PII guards in tests use placeholders only.

## Rollout

Ship as **thin PRs** (one slice or one sub-slice per PR when large), **`check-all` green**, then close the corresponding issue with evidence links.

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)
