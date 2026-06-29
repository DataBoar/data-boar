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
| F | **Hotspot Rust pré-filtro** — benchmark pinado `rust_prefilter_hotspot_v1` + pytest evidence + `benchmark:` em `CLAIMS.yml` (`rust-prefilter-speedup`); spec operador em vault `docs/private/partnerships/BENCHMARK_RUST_PREFILTER_PIN.pt_BR.md` | ✅ Done |
| G | **Archive integrity** — `tests/test_plan_archive_integrity.py`: unqualified `Completed` + open `⬜` in `docs/plans/completed/` fails CI; qualified Status on tier-A drift plans (2026-06-29) | ✅ Done |

### Phase G — archived plan overclaim guard (2026-06-29)

**Problem:** Plans moved to `docs/plans/completed/` with bare **Completed** headers while
phase tables still had open `⬜` rows — readers assume 100% delivery.

**Deliverables:**

1. Qualify **Status** on tier-A archives: `PLAN_ADDITIONAL_DATA_SOUP_FORMATS`,
   `PLAN_DASHBOARD_HTTPS_BY_DEFAULT_AND_HTTP_EXPLICIT_RISK`,
   `PLAN_CNPJ_ALPHANUMERIC_FORMAT_VALIDATION` — relabel backlog as *Deferred (post-archive)*.
2. `tests/test_plan_archive_integrity.py` — fails when unqualified Completed coexists with
   open `⬜` (not Deferred/N/A/Optional).

**Not in scope:** Proving every ✅ row matches code (see phase F benchmark / future
`plan-completion-audit.py`).

### Phase F — pinned prefilter hotspot benchmark (2026-06-29)

**Problem:** `rust-prefilter-speedup` (~11–13×) is headline in `CLAIMS.yml` but CI only verified
`ProPreFilter` exists (`note:`). `official_benchmark_200k.json` pins a **different** profile
(composite Pro worker path, stale 0.574×) — must not back the Rust hotspot claim.

**Deliverables:**

1. `tests/benchmarks/run_rust_prefilter_hotspot_bench.py` — OpenCore Python vs `filter_batch` on same batch.
2. `tests/benchmarks/rust_prefilter_hotspot.json` — pinned artifact (`benchmark: rust_prefilter_hotspot_v1`).
3. `tests/test_rust_prefilter_hotspot_evidence.py` — schema + parity + speedup > 1.0 (mode A).
4. `CLAIMS.yml` — add `benchmark:` and `test:` under `rust-prefilter-speedup`.
5. `tests/benchmarks/README.md` — scope table: `official_pro_v1` vs `rust_prefilter_hotspot_v1`.

**CI posture:** `importorskip("boar_fast_filter")` — skipped without built extension; no false green.

**Pinned primary Linux reference (2026-06-29):** ~3.98× on 200k seeded rows (`linux-x86_64`). Headline ~11–13×
remains operator-calibrated on other hosts; pytest enforces direction + parity, not a tight 11.0 floor.

**Not in scope:** Maestro gate (#1021), end-to-end scan wall-clock, regenerating `official_benchmark_200k.json`.

## Acceptance criteria

- [x] `tests/test_claims_consistency.py` with invariant A (connector↔tier hard, feature↔gate
  informative), green in `check-all` (offline/deterministic).
- [x] `docs/CLAIMS.yml` seed with 8 headline claims + `backed_by`; manifest test validates backing.
- [x] Runs in `scripts/check-all.ps1` / `scripts/check-all.sh` / CI without network.
- [x] This plan created with `<!-- plans-hub-summary: ... -->`; `plans_hub_sync.py --write` run;
  entry in `docs/plans/PLANS_TODO.md`.
- [x] References the on-demand `claim-audit` (lab-op) as the HEAVY/manual counterpart; this test
  = the LIGHT/automatic one.
- [x] Phase G: `tests/test_plan_archive_integrity.py` green; tier-A completed plans use qualified Status.
- [x] Phase F: `rust_prefilter_hotspot_v1` pinned JSON + evidence test; `CLAIMS.yml` `benchmark:` + `test:`.

## Notes

- Future hardening (Phase E): replace the literal-string `is_feature_available` regex with an
  AST pass that resolves constants/variables, eliminating the 44 false-orphans, then flip
  `test_feature_gate_report` from informative to `assert not orphans`.
- Refs: #854 (fail-closed connector↔tier), #887 (Pro+/Partner gap), #892 (requirements overclaim),
  `docs/ops/inspirations/SUPPLY_CHAIN_AND_TRUST_SIGNALS.md`.
