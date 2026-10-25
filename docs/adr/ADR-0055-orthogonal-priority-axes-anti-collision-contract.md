# ADR 0055 — Orthogonal priority axes (H/U/A/P/G/S/M) anti-collision contract

- **Date (UTC):** 2026-05-19
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Status

Accepted

### Status history

- 2026-05-19 — Accepted
- 2026-06-11 — Amended: retrofit to ADR-0045 UMADR format (metadata list, Authors, Status history) — GitHub #675

## Context

Data Boar uses multiple prioritization axes (horizon **H**, urgency **U**, Priority band **A**, GitHub execution labels **P**, gravity **G**, sprints **S**, milestones **M**, plus **CodeQL** severities). Contributors and agents often collapse them into a single "priority number," which destroys intentional expressiveness (for example treating **P0** as both "execute now" and "critical harm").

ADR-0048 preserves naming contracts; it does not document **why** the axes are separate or how to combine them without collision.

## Decision

1. Adopt **orthogonal axes**, each measuring one dimension only (see [PLAN_TAXONOMY_AXES.md](../plans/PLAN_TAXONOMY_AXES.md) and [PLAN_G_TIER.md](../plans/PLAN_G_TIER.md)).
2. Publish an explicit **anti-collision contract** (below) in agent and operator docs.
3. **Collapsing** two axes into one label or retiring an axis requires a **new ADR**, not a drive-by README edit.

### Anti-collision contract

| Rule | Meaning |
| ---- | ------- |
| **G != P** | **G** = intrinsic harm if the finding stays open; **P** = when to execute work on the GitHub issue. Valid: **G3** finding with **P3** label (critical harm, defer execution). |
| **CodeQL P* != issue P*** | SAST severity bands are not GitHub **[P0]-[P3]** titles. State which world you mean. |
| **H != S** | **H** = planning horizon; **S** = thematic sprint bucket for a work window. |
| **U != P** | **U** = deadline pressure on the operator; **P** = queue ordering for issues. |
| **A vs P** | **A1-A7** = burst steps for security/IP/commercial (see PLANS_TODO); do not rename them **P0**. |

## Consequences

- **Positive:** Auditors and agents can triage without false "everything is P0" alarms; plan checkboxes stay aligned with code when combined with AGENTS.md plan discipline.
- **Negative:** Slightly more prose when stating priority; acceptable trade-off for clarity.
- **Watch:** Retro-labeling all open issues with **G-tier** is **out of scope** until a dedicated hygiene pass is requested.

## References

- [ADR-0048](ADR-0048-operator-facing-taxonomy-and-naming-contract-preservation.md)
- [PLAN_TAXONOMY_AXES.md](../plans/PLAN_TAXONOMY_AXES.md)
- [PLAN_G_TIER.md](../plans/PLAN_G_TIER.md)
- [PLANS_TODO.md](../plans/PLANS_TODO.md) (Status taxonomy)
- [THIN_SLICE_AGENT_PRIORITY_HANDOFF.md](../ops/THIN_SLICE_AGENT_PRIORITY_HANDOFF.md)
