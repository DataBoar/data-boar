# ADR 0024 — Enterprise discovery — three complementary tracks (planning posture)

- **Status:** Accepted
- **Date (UTC):** 2026-04-15
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Context

Enterprise and consulting workflows need **scope** for sensitive-data scanning when:

- **File and document inventory** is incomplete (cloaked extensions, rich media, compressed innards, “forgotten” paths).
- **CMDB / ITSM / monitoring** exports exist only sometimes — or **never**.
- **Network listeners** may be missing from formal inventory, but **active probing** raises authorization, IDS, and least-privilege concerns.

A single product toggle that “discovers everything” would be **misleading**, **unsafe**, and hard to support. The work is **not** all implemented yet; the decision is how to **structure** plans and narrative until code ships.

## Decision

1. Treat **enterprise-style discovery** as **three complementary tracks**, each with its own plan, guardrails, and opt-in posture:
   - **File / data soup:** richer formats, cloaking, Tier 3b/4 heuristics, optional stego — [PLAN_ADDITIONAL_DATA_SOUP_FORMATS.md](../plans/completed/PLAN_ADDITIONAL_DATA_SOUP_FORMATS.md).
   - **Offline scope import:** exports → canonical schema → merge-safe config fragments — [PLAN_SCOPE_IMPORT_FROM_EXPORTS.md](../plans/completed/PLAN_SCOPE_IMPORT_FROM_EXPORTS.md).
   - **Opt-in network hints:** allowlisted TCP connect + short read — [PLAN_OPT_IN_NETWORK_PORT_SERVICE_HINTS.md](../plans/PLAN_OPT_IN_NETWORK_PORT_SERVICE_HINTS.md).

2. **Do not** promise one **magic** control that enables all three; **stack** explicit flags / phases as each plan defines.

3. **Marketing and hub copy** ([PLANS_TODO.md](../plans/PLANS_TODO.md) Integration / active threads, [PLANS_HUB.md](../plans/PLANS_HUB.md)) stay **product positioning** only — **not** legal, regulatory, or “completeness” guarantees.

4. **Narrative** (“hidden / legacy / forgotten ingredients”) lives in plan prose; it explains **intent**, not shipped behaviour for every bullet.

## Consequences

- **Positive:** Clear **separation of concerns** for implementers; consultants can cite **which** track applies; reduces scope creep in a single mega-feature.
- **Negative:** More cross-links to maintain; contributors must read **non-goals** in each plan before extending.
- **Neutral:** Commercial / tier packaging can align **accelerator** adapters and **opt-in** probes with [LICENSING_SPEC.md](../LICENSING_SPEC.md) later — out of scope for this ADR.

## References

- [PLAN_NEXT_WAVE_PLATFORM_AND_GTM.md](../plans/PLAN_NEXT_WAVE_PLATFORM_AND_GTM.md) (N2 — scope import called out)
- [ADR 0004](ADR-0004-external-docs-no-markdown-links-to-plans.md) (external docs do not deep-link plans; internal hub/todo may)
