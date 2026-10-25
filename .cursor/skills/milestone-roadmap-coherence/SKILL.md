---
name: milestone-roadmap-coherence
description: Use when editing sprint/milestone plans, dashboard identity (#86), or production-readiness narrative—keep a single canonical map and avoid duplicating milestone tables across files.
---

# Milestone roadmap coherence

## Rule

**`.cursor/rules/plan-milestone-and-identity-coherence.mdc`** — read it first. It lists **canonical paths only** (no duplicated tables here).

## Read in this order (short)

1. `docs/plans/SPRINTS_AND_MILESTONES.md` — **§5** (M-* definitions), **Composing milestones**, **§4.1** (identity), **§4.2** (dashboard cluster).
2. `docs/plans/PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md` — phases and demo vs production-ready table (**#86**).
3. `docs/plans/PLANS_TODO.md` — queue and **Optional PM view** pointer.

## Do not

- Paste the full milestone table into README, COMPLIANCE_*, or multiple plan files—**link** instead.
- Change OIDC-vs-passwordless sequencing in one doc without checking **§4.1** and **#86** plan.
