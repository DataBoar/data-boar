# Plan: Clojure/Lisp augmentation feasibility for Data Boar

**Status:** Amended (2026-10-12 — runtime in sibling bestials, not in-tree host sidecar; see §0)
**Date:** 2026-05-09
**Authors:** Fabio Leitao
**Priority:** H3

**Português (Brasil):** [PLAN_CLOJURE_AUGMENTATION.pt_BR.md](PLAN_CLOJURE_AUGMENTATION.pt_BR.md)

<!-- plans-hub-summary: Evaluate whether a Clojure sidecar adds measurable value for policy logic and temporal evidence without regressing Rust/Python baseline. -->
<!-- plans-hub-related: PLAN_LATO_SENSU_THESIS.md, PLAN_STRICTO_SENSU_RESEARCH_PATH.md, PLAN_NEXT_WAVE_PLATFORM_AND_GTM.md -->

**Horizon suggestion:** `[H4][U3]` far-horizon exploration after current commercialization slices
**Primary scope:** Architecture feasibility and evidence, not immediate product migration

---

## 0. Amendment (2026-10-12 — issue #1839)

**Conclusion:** a Clojure/Lisp **sidecar plugin** remains valid, but **not** inside the `data-boar` tree (`experimental/clojure_sidecar/`, JVM on the Community path, Python adapter in core).

- Runtime lives in **separate DataBoar org repositories** (sage-remora, faithful-ferret) orchestrated via the plugin/SDK slot — not as a sub-product of this monorepo.
- The **host** keeps only the L2 spawn/timeout/Safe-Hold contract (`PLAN_PLUGIN_PARTNER_INTERFACE` / epic #865); it does not own the Clojure engine.
- **Phases 0–2 below (host in-tree PoC):** **cancelled / do not apply** — preserved as historical hypothesis only.

This plan is **not** moved to `completed/` solely to hide hub rows; status is **Amended**, not “done on core.”

---

## 1. Why this plan exists

This plan tests one focused hypothesis: a small Clojure/Lisp sidecar may improve policy reasoning and temporal evidence generation for complex compliance scenarios.

The plan does **not** replace the current Rust/Python core:

- Rust stays the performance-first engine.
- Python stays the orchestration and connector layer.
- Clojure is only considered as an optional sidecar if objective evidence shows net benefit.

---

## 2. Value hypothesis and decision gates

### 2.1 Candidate value for Data Boar

Potential value areas:

1. **Policy expressiveness:** richer rule composition (for example, multi-condition compliance correlations) with less imperative glue code.
2. **Audit reasoning:** clearer rule explainability for operator and compliance narratives.
3. **Academic bridge:** creates a credible research line tied to formal reasoning and evidence models.

### 2.2 Hard constraints

Any sidecar experiment must preserve:

- No runtime regression in default Data Boar path.
- No forced JVM dependency for Community baseline.
- No weakening of security, observability, or operator workflow.

### 2.3 Go/no-go criteria

Proceed beyond PoC only if all are true:

- End-to-end overhead remains acceptable in a bounded benchmark scenario.
- Rule authoring and review improve measurably versus pure Python implementation.
- Integration complexity remains maintainable for one-operator execution.

---

## 3. Phase 0 - Feasibility brief (doc-first)

**Goal:** decide if a PoC is worth building.

| # | To-do | Status |
| - | ----- | ------ |
| 0.1 | Define 2-3 realistic rule cases where current Python logic is verbose or hard to audit. | ❌ Cancelled (§0 — host track) |
| 0.2 | Compare candidate stacks (`datascript`, `malli`, lightweight EDN rule model) and list trade-offs. | ❌ Cancelled (§0) |
| 0.3 | Write integration options (gRPC sidecar, local process, or offline rule compiler) with blast-radius notes. | ❌ Cancelled (§0) |
| 0.4 | Produce a go/no-go memo (one page) and classify this track as product backlog or academic-only backlog. | ❌ Cancelled (§0) |

---

## 4. Phase 1 - Minimal sidecar PoC (optional)

**Goal:** test one concrete path with a single bounded scenario.

| # | To-do | Status |
| - | ----- | ------ |
| 1.1 | Create `experimental/clojure_sidecar/` with minimal project bootstrap and README constraints. | ❌ Cancelled (§0) |
| 1.2 | Implement one rule-evaluation endpoint with deterministic input/output contract. | ❌ Cancelled (§0) |
| 1.3 | Add a Python adapter behind an opt-in feature flag (`off` by default). | ❌ Cancelled (§0) |
| 1.4 | Add benchmark script and capture latency/memory overhead versus baseline. | ❌ Cancelled (§0) |
| 1.5 | Record findings and recommendation (`continue`, `park`, or `discard`). | ❌ Cancelled (§0) |

---

## 5. Phase 2 - Productization gate (only if approved)

**Goal:** define what would be needed before any production claim.

| # | To-do | Status |
| - | ----- | ------ |
| 2.1 | Define operator lifecycle workflow (install, health checks, fallback when sidecar is unavailable). | ❌ Cancelled (§0 — host track) |
| 2.2 | Define security model for sidecar communication and input validation. | ❌ Cancelled (§0) |
| 2.3 | Define report/audit surface fields showing when sidecar logic was active. | ❌ Cancelled (§0) |
| 2.4 | Estimate maintenance cost and confirm fit with roadmap priorities. | ❌ Cancelled (§0) |

---

## 6. Academic alignment (lato/stricto sensu)

This plan also supports academic tracks without forcing near-term product scope:

- **Lato sensu:** use feasibility and audit reasoning as applied architecture material.
- **Stricto sensu:** use controlled experiments to compare rule modeling approaches and evidence quality.

Related references:

- [PLAN_LATO_SENSU_THESIS.md](PLAN_LATO_SENSU_THESIS.md)
- [PLAN_STRICTO_SENSU_RESEARCH_PATH.md](PLAN_STRICTO_SENSU_RESEARCH_PATH.md)
- [PLAN_NEXT_WAVE_PLATFORM_AND_GTM.md](PLAN_NEXT_WAVE_PLATFORM_AND_GTM.md) (N3 bridge)

---

## 7. Recommendation (current)

**After §0 (2026-10-12):** do **not** resume host in-tree phases 0–2. Any Clojure/Lisp sidecar work belongs in **sibling bestial repositories** (plugin/SDK slot) with the host keeping spawn/timeout/Safe-Hold only.

For product planning, treat this file as **amended reference** — not a near-term `main` milestone. Revisit twins + host contract when:

- A customer/partner request requires richer policy reasoning.
- A thesis/research cycle needs an experimental formal-rules branch.
- Plugin partner interface (#865) defines a concrete L2 integration test.
