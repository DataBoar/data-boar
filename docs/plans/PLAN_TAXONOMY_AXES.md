# Plan: Taxonomy axes (single map of orthogonal priorities)

<!-- plans-hub-summary: Canonical map of H/U/A/P/G/S/M and CodeQL axes; links to operational sources -->

**Status:** Active
**Date:** 2026-05-19
**Authors:** Fabio Leitao
**Priority:** H1

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)

**Related:** [ADR-0055](../adr/ADR-0055-orthogonal-priority-axes-anti-collision-contract.md), [PLAN_G_TIER.md](PLAN_G_TIER.md), [SPRINTS_AND_MILESTONES.md](SPRINTS_AND_MILESTONES.md)

This document **does not replace** the operational definitions in linked files — it answers **what each axis measures**, **when to use it**, and **how not to confuse axes**.

---

## How to read a priority statement

Good: "Gravity **G2**; execute as GitHub **P1** this sprint (**S2a**); horizon **H1**."

Bad: "This is P0" (ambiguous: CodeQL? GitHub? gravity?).

---

### Axis: Horizon (H0-H5)

| Field | Content |
| ----- | ------- |
| **Measures** | When in the product roadmap the work belongs |
| **Range** | H0 must-do-now through H5 dream/PhD horizon |
| **Rationale** | Prevents H3 research from blocking H0 safety |
| **Objective** | Stable sequencing in PLANS_TODO and plans-stats |
| **Applicability** | Plan rows, dashboard in PLANS_TODO |
| **Canonical source** | [PLANS_TODO.md](PLANS_TODO.md) (Status taxonomy) |
| **Orthogonality** | Not urgency (**U**), not sprint theme (**S**) |

---

### Axis: Urgency (U0-U3)

| Field | Content |
| ----- | ------- |
| **Measures** | Time pressure on the operator or deployment |
| **Range** | U0 security now to U3 backlog/catalogue |
| **Rationale** | Separates "important eventually" from "now" |
| **Objective** | Token-aware batching without hiding U0 |
| **Applicability** | Plan tags, operator today-mode |
| **Canonical source** | [PLANS_TODO.md](PLANS_TODO.md), [TOKEN_AWARE_USAGE.md](TOKEN_AWARE_USAGE.md) |
| **Orthogonality** | A **G3** finding can still be **U3** if execution waits |

---

### Axis: Priority band A (A1-A7)

| Field | Content |
| ----- | ------- |
| **Measures** | Burst steps for security, IP, commercial exposure |
| **Range** | A1-A7 ordered checklist (not GitHub P0) |
| **Rationale** | Protects revenue and public tree without renaming issues |
| **Objective** | Clear "stop feature work" windows |
| **Applicability** | When operator invokes band A or security incident |
| **Canonical source** | [PLANS_TODO.md](PLANS_TODO.md) (Priority band A section) |
| **Orthogonality** | Do not label band-A steps as **[P0]** in issue titles |

---

### Axis: GitHub execution labels (P0-P3)

| Field | Content |
| ----- | ------- |
| **Measures** | Order of execution for GitHub issues and thin PRs |
| **Range** | P0 (critical path) to P3 (housekeeping) |
| **Rationale** | Agents and humans share one queue language |
| **Objective** | Predictable burn-down per [THIN_SLICE_AGENT_PRIORITY_HANDOFF.md](../ops/THIN_SLICE_AGENT_PRIORITY_HANDOFF.md) |
| **Applicability** | Issue titles `[P0]`-`[P3]`, assistant handoff |
| **Canonical source** | [docs/ops/THIN_SLICE_AGENT_PRIORITY_HANDOFF.md](../ops/THIN_SLICE_AGENT_PRIORITY_HANDOFF.md) |
| **Orthogonality** | See **G** and **CodeQL** rows below |

---

### Axis: Gravity (G0-G3)

| Field | Content |
| ----- | ------- |
| **Measures** | Intrinsic severity of a **finding** if left open |
| **Range** | G0 negligible to G3 critical (PII, Safe-Hold) |
| **Rationale** | Distinguishes cosmetic drift from breach-class issues |
| **Objective** | Better audit triage without re-scoring every issue |
| **Applicability** | Findings, compliance audits, plan drift |
| **Canonical source** | [PLAN_G_TIER.md](PLAN_G_TIER.md) |
| **Orthogonality** | **G3** with **P3** is valid (critical, defer execution) |

---

### Axis: Sprints (S0-S6)

| Field | Content |
| ----- | ------- |
| **Measures** | Thematic work bucket for a calendar window |
| **Range** | S0 trust burst through S6 (see sprint doc) |
| **Rationale** | Kanban "Selected / In progress" without replacing H-tags |
| **Objective** | Align sessions to one narrative |
| **Applicability** | [SPRINTS_AND_MILESTONES.md](SPRINTS_AND_MILESTONES.md) |
| **Canonical source** | Same |
| **Orthogonality** | **S2a** can contain mixed **P1** and **P2** issues |

---

### Axis: Milestones (M-*)

| Field | Content |
| ----- | ------- |
| **Measures** | Deliverable with an explicit "done" criterion |
| **Range** | M-OBS, M-MOBILE-V1, M-MATURITY-POC, etc. |
| **Rationale** | Stakeholder language distinct from plan rows |
| **Objective** | Release and demo checkpoints |
| **Applicability** | Sprint doc, PLANS_TODO integration bullets |
| **Canonical source** | [SPRINTS_AND_MILESTONES.md](SPRINTS_AND_MILESTONES.md) |
| **Orthogonality** | Milestones span multiple **H** horizons |

---

### Axis: CodeQL severity (P0/P1/P2 in SAST)

| Field | Content |
| ----- | ------- |
| **Measures** | Static analysis finding severity in CodeQL world |
| **Range** | P0/P1/P2 per codeql-priority-matrix rule |
| **Rationale** | Security scanner vocabulary != GitHub issue labels |
| **Objective** | Avoid false "everything is P0" in chat |
| **Applicability** | CI CodeQL, SECURITY.md |
| **Canonical source** | `.cursor/rules/codeql-priority-matrix.mdc`, [SECURITY.md](../SECURITY.md) |
| **Orthogonality** | Always say "CodeQL P1" vs "issue P1" |

---

## To-do

| # | Item | Status |
| - | ---- | ------ |
| 1 | Publish this hub + pt-BR mirror | ⬜ Pending |
| 2 | Link from [OPERATOR_AGENT_COLD_START_LADDER.md](../ops/OPERATOR_AGENT_COLD_START_LADDER.md) | ⬜ Pending |
| 3 | DOCS_AND_HUBS_INDEX (#571) cross-link when available | ⬜ Pending |
