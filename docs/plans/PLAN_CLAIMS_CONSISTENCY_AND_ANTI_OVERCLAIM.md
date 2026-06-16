# PLAN: Claims consistency and anti-overclaim gate

**Status:** In progress
**Date:** 2026-06-16
**Authors:** Fabio Leitao
**Priority:** H1
**GitHub:** [#894](https://github.com/FabioLeitao/data-boar/issues/894)

<!-- plans-hub-summary: gate determinístico offline anti-overclaim — invariante connector↔tier (build-time do #854) + manifesto docs/CLAIMS.yml com backed_by verificável; contraparte light do auditor on-demand claim-audit (lab-op) -->
<!-- plans-hub-related: PLAN_CONNECTOR_TIER_GATING.md, PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md -->

## Context

The product narrative (README, pitch, tier table) makes **headline claims** about
capabilities. Until now nothing in CI catches **overclaim** (a capability the code does
not deliver) nor internal **consistency drift**. The manual audit of 2026-06-15/16 found
real mismatches: **#887** (Pro+/Partner present in the ladder but absent from the `Tier`
enum) and **#892** (uv-less `requirements.txt` broken = overclaim of a fallback path).

There is already an **on-demand, HEAVY** auditor — `claim-audit` (lab-op,
`~/.local/bin/claim-audit`) — that syncs, greps, and calls `gh`. It is **interactive and
heuristic**, so it cannot run in CI. This plan adds the **LIGHT/automatic** counterpart: a
**deterministic, offline, binary** pytest gate inside `check-all`.

Two levels of the same anti-overclaim axis:

| Level | Tool | Trigger | Nature |
| ----- | ---- | ------- | ------ |
| HEAVY / manual | `claim-audit` (lab-op) | operator, on-demand | sync + grep + `gh`, heuristic, interactive |
| LIGHT / automatic | `tests/test_claims_consistency.py` | every `check-all` / CI | pure AST/regex on the checkout, offline, binary pass/fail |

## Scope

### A) Internal consistency invariants (cheap, high value)

`tests/test_claims_consistency.py` — pure file reads over the current checkout (no network,
no `git reset`, no `gh`):

- **connector↔tier (hard-gate):** every registered connector (`register("x", ...)` in
  `connectors/*.py`) has an explicit entry in `FEATURE_TIER_MAP`. This raises the
  fail-closed of **#854** from runtime → **build-time**. A new connector without a tier
  ⇒ red test. Alias `powerapps → dataverse` is preserved (per `PLAN_CONNECTOR_TIER_GATING`).
- **feature↔gate (INFORMATIVE for now):** every feature in `FEATURE_TIER_MAP` is referenced
  by at least one `is_feature_available("...")`. The literal-string regex reports 44
  false-orphans because real gating uses variables/constants — kept **informative** (prints,
  does not fail) until refined with AST (constant resolution). Promoting it to a hard-gate
  before that would be flaky and the team would disable it.

### B) Headline claims manifest

- `docs/CLAIMS.yml` — only **headline** claims (what the customer reads in the central
  narrative). Each claim: `id`, `text`, `tier`, and `backed_by:` (file/symbol/test/tier_feature/
  registry/issue/note). Calibrated against paranoia: **only headline claims**, not every doc
  sentence.
- `test_claims_consistency.py` asserts each verifiable `backed_by` **exists** in the checkout.
  A new claim without backing ⇒ red. `issue:` / `note:` / `benchmark:` are informative
  (traceability only). Performance/quantity claims (e.g. "11–13x") only confirm the **code**
  exists — the **number** needs a benchmark/perf-test, marked with `note:`.

## Phases

| Phase | Item | Status |
| ----- | ---- | ------ |
| A | `test_claims_consistency.py` — connector↔tier hard-gate + feature↔gate informative | ✅ Done |
| B | `docs/CLAIMS.yml` seed (8 headline claims, verified backing) + manifest test | ✅ Done |
| C | Runs offline in `check-all` (pytest auto-discovery; no net, no `gh`) | ✅ Done |
| D | Plan + `plans_hub_sync --write` + `PLANS_TODO.md` entry | ✅ Done |
| E | (future) refine feature↔gate with AST constant resolution → promote to hard-gate | ⬜ Pending |

## Acceptance criteria

- [x] `tests/test_claims_consistency.py` with invariant A (connector↔tier hard, feature↔gate
  informative), green in `check-all` (offline/deterministic).
- [x] `docs/CLAIMS.yml` seed with 8 headline claims + `backed_by`; manifest test validates backing.
- [x] Runs in `scripts/check-all.ps1` / `scripts/check-all.sh` / CI without network.
- [x] This plan created with `<!-- plans-hub-summary: ... -->`; `plans_hub_sync.py --write` run;
  entry in `docs/plans/PLANS_TODO.md`.
- [x] References the on-demand `claim-audit` (lab-op) as the HEAVY/manual counterpart; this test
  = the LIGHT/automatic one.

## Notes

- Future hardening (Phase E): replace the literal-string `is_feature_available` regex with an
  AST pass that resolves constants/variables, eliminating the 44 false-orphans, then flip
  `test_feature_gate_report` from informative to `assert not orphans`.
- Refs: #854 (fail-closed connector↔tier), #887 (Pro+/Partner gap), #892 (requirements overclaim),
  `docs/ops/inspirations/SUPPLY_CHAIN_AND_TRUST_SIGNALS.md`.
