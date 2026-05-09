# Plan: Clojure/Lisp augmentation feasibility for Data Boar

**Português (Brasil):** [PLAN_CLOJURE_AUGMENTATION.pt_BR.md](PLAN_CLOJURE_AUGMENTATION.pt_BR.md)

<!-- plans-hub-summary: Evaluate whether a Clojure sidecar adds measurable value for policy logic and temporal evidence without regressing Rust/Python baseline. -->
<!-- plans-hub-related: PLAN_LATO_SENSU_THESIS.md, PLAN_STRICTO_SENSU_RESEARCH_PATH.md, PLAN_NEXT_WAVE_PLATFORM_AND_GTM.md -->

**Status:** Proposed (not started)
**Horizon suggestion:** `[H4][U3]` far-horizon exploration after current commercialization slices
**Primary scope:** Architecture feasibility and evidence, not immediate product migration

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
| 0.1 | Define 2-3 realistic rule cases where current Python logic is verbose or hard to audit. | ⬜ Pending |
| 0.2 | Compare candidate stacks (`datascript`, `malli`, lightweight EDN rule model) and list trade-offs. | ⬜ Pending |
| 0.3 | Write integration options (gRPC sidecar, local process, or offline rule compiler) with blast-radius notes. | ⬜ Pending |
| 0.4 | Produce a go/no-go memo (one page) and classify this track as product backlog or academic-only backlog. | ⬜ Pending |

---

## 4. Phase 1 - Minimal sidecar PoC (optional)

**Goal:** test one concrete path with a single bounded scenario.

| # | To-do | Status |
| - | ----- | ------ |
| 1.1 | Create `experimental/clojure_sidecar/` with minimal project bootstrap and README constraints. | ⬜ Pending |
| 1.2 | Implement one rule-evaluation endpoint with deterministic input/output contract. | ⬜ Pending |
| 1.3 | Add a Python adapter behind an opt-in feature flag (`off` by default). | ⬜ Pending |
| 1.4 | Add benchmark script and capture latency/memory overhead versus baseline. | ⬜ Pending |
| 1.5 | Record findings and recommendation (`continue`, `park`, or `discard`). | ⬜ Pending |

---

## 5. Phase 2 - Productization gate (only if approved)

**Goal:** define what would be needed before any production claim.

| # | To-do | Status |
| - | ----- | ------ |
| 2.1 | Define operator lifecycle workflow (install, health checks, fallback when sidecar is unavailable). | ⬜ Pending |
| 2.2 | Define security model for sidecar communication and input validation. | ⬜ Pending |
| 2.3 | Define report/audit surface fields showing when sidecar logic was active. | ⬜ Pending |
| 2.4 | Estimate maintenance cost and confirm fit with roadmap priorities. | ⬜ Pending |

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

Current recommendation: keep this track in **far-horizon backlog** until active trust/commercial slices stabilize. Re-evaluate when one of these triggers occurs:

- A customer/partner request requires richer policy reasoning.
- A thesis/research cycle needs an experimental formal-rules branch.
- Existing Python policy logic becomes too costly to maintain.
