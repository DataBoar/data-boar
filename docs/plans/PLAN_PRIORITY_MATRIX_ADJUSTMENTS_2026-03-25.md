# Plan checkpoint: priority matrix adjustments (2026-03-25)

**Status:** Pending
**Date:** 2026-03-25
**Authors:** Fabio Leitao
**Priority:** H0

**Goal context:** faster commercialization readiness without regressions, with trust-first sequencing.

## What was adjusted

### 1) `PLANS_TODO.md` sequence adjustments

- Promoted **HTTPS-by-default** earlier in "What to start next":
- moved from `6a` to `4`.
- Added explicit **trust-state accelerator** row:
- `4a` linked to [PLAN_GRC_INSPIRED_ENTERPRISE_TRUST_ACCELERATORS.md](PLAN_GRC_INSPIRED_ENTERPRISE_TRUST_ACCELERATORS.md).
- Shifted later rows accordingly:
- **Strong crypto** -> `5`
- **Data source versions** -> `6`
- **Notifications** -> `7`
- Updated "Resume next session" execution line to follow:
- `4 -> 4a -> 5 -> 6 -> 7`.

### 2) `SPRINTS_AND_MILESTONES.md` trust granularity

- Expanded the meaning of `M-TRUST` to include the runtime evidence start (`M-TRUST-01`).
- Added a dedicated subsection with trust sub-milestones:
- `M-TRUST-01` contract,
- `M-TRUST-02` confidence-gated outputs,
- `M-TRUST-03` crypto self-check,
- `M-TRUST-04` external review packet cycle.

## Why these adjustments

1. **Commercial confidence before breadth**
   - Enterprise buyers and reviewers trust deploy/runtime evidence more than roadmap prose.
1. **Risk containment**
   - Transport and trust-state controls lower the chance of "looks-good-but-risky" outputs.
1. **Workflow fit**
   - Matches token-aware one-slice cadence: each trust sub-milestone can be a narrow PR.
1. **Corporate-Entity-C timing quality**
   - Next external review is more useful after at least `M-TRUST-01` is shipped.

## Expected impact

- Better demo -> beta narrative: "secure transport + confidence semantics" before broader feature expansion.
- Clearer sequencing for daily execution under limited operator attention.
- Lower review churn by presenting concrete runtime deltas.

## Recommended next implementation slice (A activities)

1. Implement `M-TRUST-01` baseline:
   - trust-state enum/contract,
   - propagation to status/log/report/audit surfaces,
   - targeted tests.
1. Then implement `M-TRUST-02` confidence-gated output policy.

---

This checkpoint intentionally keeps scope narrow and sequence-oriented; it does not replace full plan files.
