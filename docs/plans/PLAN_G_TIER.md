# Plan: G0-G3 gravity tier (intrinsic finding severity)

<!-- plans-hub-summary: G0-G3 gravity axis for findings; orthogonal to H/U/A/P execution priority -->

**Status:** Active
**Date:** 2026-05-19
**Authors:** Fabio Leitao
**Priority:** H0

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)

**Related:** [PLAN_TAXONOMY_AXES.md](PLAN_TAXONOMY_AXES.md) (when published), [ADR-0048](../adr/ADR-0048-operator-facing-taxonomy-and-naming-contract-preservation.md), [docs/ops/THIN_SLICE_AGENT_PRIORITY_HANDOFF.md](../ops/THIN_SLICE_AGENT_PRIORITY_HANDOFF.md)

---

## Problem

The repo already uses **H0-H5** (horizon), **U0-U3** (urgency), **A1-A7** (Priority band A burst), **P0-P3** (GitHub issue execution labels), **S0-S6** (sprints), and **M-*** (milestones). None of those axes answers: **how severe is this finding if we leave it unaddressed?**

Without a **gravity** axis, a cosmetic doc typo and a **PII leak / Safe-Hold** candidate look equally "open" in triage tables.

---

## G0-G3 definition (canonical)

| Level | Name (EN) | Criterion |
| ----- | --------- | --------- |
| **G0** | Negligible | Cosmetic, typo, no functional or compliance risk |
| **G1** | Low | Improvement, documentation gap, no direct exposure |
| **G2** | Significant | Functional or compliance weakness; potential exposure |
| **G3** | Critical | Compliance breach, PII leak, IP risk, **Safe-Hold** candidate |

---

## Orthogonality (do not collapse axes)

| Axis | Measures | Example |
| ---- | -------- | ------- |
| **P0-P3** (GitHub label) | **When to execute** this issue in the queue | "Do this before H3 feature X" |
| **G0-G3** | **Intrinsic harm** if the finding stays open | "G3 finding, P3 label" = critical but not urgent this week |
| **U0-U3** | **Deadline pressure** on the operator | U0 security now vs U3 catalogue |
| **H0-H5** | **Planning horizon** | H0 must-do-now vs H4 far horizon |

**CodeQL P0/P1/P2** is a **separate** SAST severity world — never equate it to issue **P0** or **G3** without saying which axis you mean.

---

## How to use (agents and humans)

1. When opening or triaging an issue about a **finding** (not a feature), add **G-tier in prose** in the body or table when helpful: e.g. "Gravity: G2 (significant); execution: P1".
2. Do **not** retro-label every historical issue in one sweep — adopt on **new** audits and **active** triage.
3. For execution order on GitHub, keep using **[P0]-[P3]** in titles per [THIN_SLICE_AGENT_PRIORITY_HANDOFF.md](../ops/THIN_SLICE_AGENT_PRIORITY_HANDOFF.md).

---

## To-do

| # | Item | Status |
| - | ---- | ------ |
| 1 | Publish this plan + PLANS_TODO taxonomy row | ✅ Done |
| 2 | Cross-link from [PLAN_TAXONOMY_AXES.md](PLAN_TAXONOMY_AXES.md) when that hub exists | ✅ Done |
| 3 | ADR-0055 anti-collision contract (issue #573) | ✅ Done |
