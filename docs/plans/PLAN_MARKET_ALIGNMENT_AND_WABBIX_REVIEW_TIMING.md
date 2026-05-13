# Plan: Market alignment checkpoint and Corporate-Entity-C review timing

**Status:** Pending
**Date:** 2026-03-25
**Authors:** Fabio Leitao
**Priority:** H1

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md), [SPRINTS_AND_MILESTONES.md](SPRINTS_AND_MILESTONES.md)

## Purpose

Assess whether current roadmap/milestones are aligned with the operator's commercial target (mid-market consulting entry -> production-ready autonomy -> larger distributed enterprises), and decide whether to request a new Corporate-Entity-C review **now** or **later**.

## Alignment assessment (current)

## What is already aligned

- **Consulting-first entry path:** docs/runbooks and operator workflows are strong for fast assisted adoption.
- **Trust trajectory:** ongoing work on release/integrity evidence and transport/auth secure-by-default direction supports "results clients can trust."
- **Operational realism:** homelab validation, check-all discipline, and phased hardening align with practical enterprise expectations.
- **Commerciability posture:** licensing and packaging discussions already exist in plans and policy docs.

## Gaps to close for "THE SOLUTION" positioning

1. **Enterprise confidence envelope not yet fully productized**
   - Need stronger runtime trust-state behavior implemented (not just planned) for auth/transport tamper scenarios.
1. **Access/governance controls**
   - Dashboard/API access model (RBAC/identity path) still tracked, not completed.
1. **Deployment trust defaults**
   - HTTPS-by-default and explicit insecure override behavior are now well planned, but implementation baseline is pending.
1. **Proof-of-value packaging**
   - Need a compact "executive evidence pack" pattern that maps findings -> actionability -> confidence boundaries for decision-makers.

## Recommended roadmap adjustments

### Priority adjustments (short-term)

1. Keep **Dependabot/Scout** as non-blocking but frequent hygiene slices.
1. Elevate first implementation slice of **HTTPS-by-default + trust/tinted state** from "planned" to an active sprint slice soon.
1. Pair one **access/governance** step (RBAC/doc-first or middleware path) with transport hardening to strengthen enterprise signal.

### Positioning adjustments (commercial narrative)

1. Keep message sequence:
   - "quick consulting value in imperfect environments,"
   - then "repeatable production-safe operation,"
   - then "distributed enterprise confidence and traceability."
1. Avoid overselling "full autonomy" before secure transport/auth trust-state baseline ships.

## Corporate-Entity-C review timing decision

## Recommendation: **wait a bit, then request**

Do **not** request the next major Corporate-Entity-C cycle immediately.

### Why wait

- Recent progress has many valuable doc/process hardening slices.
- Next Corporate-Entity-C cycle will have higher signal if we include at least one visible runtime security implementation slice (not only planning/docs).
- This avoids review fatigue and increases delta quality in external assessment.

### Suggested trigger (request when all true)

1. First implementation slice for HTTPS-by-default path is merged (flags/runtime warnings/status at minimum).
1. Trust/tinted behavior has at least baseline runtime surfacing (logs/status/report constraints linkage).
1. CI/check-all remains green and no critical regression remains open.
1. Updated evidence map is prepared (paths + concise change summary).

### Suggested window

- Reassess in **~1-2 weeks** or after one concrete secure-by-default implementation milestone.

## Prep checklist for next Corporate-Entity-C request

1. Build a compact diff narrative:
   - "what was planned,"
   - "what is now implemented,"
   - "what remains and why."
1. Include in-repo evidence paths (plans + docs + tests + workflow).
1. Ask for critical analysis focused on:
   - trustability of outputs,
   - migration safety,
   - enterprise deploy confidence.

## Next practical tasks (token-aware)

1. Implement HTTPS-by-default **Phase 1** (transport flags/config + explicit insecure override).
1. Add trust-state propagation minimum for transport insecurity in status/log surfaces.
1. Add/update targeted tests for secure/insecure modes.
1. Update operator docs only for shipped behavior (avoid doc drift).

---

This checkpoint is intentionally concise and should be revisited after the first implementation milestone lands.
