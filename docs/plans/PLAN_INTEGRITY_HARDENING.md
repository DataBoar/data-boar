# Plan: Integrity anchor — behaviour-critical module expansion (#1298)

**Status:** In progress — Phase 1 landed in [#1298](https://github.com/DataBoar/data-boar/issues/1298) (glob allowlist + CLI surfacing).
**Date:** 2026-07-21
**Authors:** Fabio Leitao
**Priority:** P1 (field finding — MSSQL connector tamper not detected)
**GitHub:** [#1298](https://github.com/DataBoar/data-boar/issues/1298)

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md) · [PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md](PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md) · [INTEGRITY_CHECK_ALPHA_LOGIC.md](../ops/INTEGRITY_CHECK_ALPHA_LOGIC.md)

<!-- plans-hub-summary: Expand SQLite integrity anchor allowlist via globs (connectors/, core/licensing/) plus explicit spine paths; surface runtime-trust on --version and --validate-config so field tamper false-negatives are visible before scan (#1298). -->
<!-- plans-hub-related: PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md, PLAN_PII_GATE_INTEGRITY.md -->

## Problem

`CRITICAL_MODULES` in `core/integrity_anchor.py` originally hashed only **six** paths. Tamper in `connectors/` (credentials, SSRF guards, sampling caps), most of `core/licensing/` (JWT verify, tier gating), PII redaction (`core/validation.py`, `utils/logger.py`), or WebAuthn gates did **not** trigger `-alpha` — a **false-negative** integrity signal (inverse of post6 false-positive on upgrade).

## Policy — behaviour-critical criterion

A path belongs in the anchor when tamper would, without detection:

- bypass license/tier or connector gate,
- exfiltrate or redirect credentials/connections,
- remove safety caps (sampling, archive budgets, SSRF guards),
- leak PII in logs/reports,
- bypass web authentication.

**Anti-recurrence:** prefer **globs** for whole trees that share this bar (`connectors/*.py`, `core/licensing/*.py`) plus an explicit **spine** for engine/detector/API entrypoints.

## Phase 1 — Allowlist expansion (this slice)

| # | Deliverable | Status |
| - | ----------- | ------ |
| 1 | `resolve_critical_modules()` with globs + explicit extras | ✅ #1298 |
| 2 | `--version` runs integrity preflight; prints `{version}-alpha` when tampered | ✅ #1298 |
| 3 | `--validate-config` emits `runtime-trust` (informative, non-fatal) after integrity check | ✅ #1298 |
| 4 | Tests: tamper `sql_connector`, `verify`, `sql_sampling` → tampered; `--version` subprocess | ✅ #1298 |
| 5 | Update `INTEGRITY_CHECK_ALPHA_LOGIC*` module list + criterion | ✅ #1298 |

## Phase 2 — backlog (not this slice)

- Signed manifest / Sigstore (Phase C.4 of build-identity plan)
- `--reverify-integrity` operator flag
- Optional extension-module hashing (`boar_fast_filter`)

## Acceptance

- [x] `connectors/*.py` and `core/licensing/*.py` auto-included in anchor baseline
- [x] Explicit extras: `core/connector_registry.py`, `core/validation.py`, `utils/logger.py`, `api/webauthn_*.py`
- [x] CLI surfaces trust on `--version` and `--validate-config`
- [x] Regression tests for representative tamper classes
