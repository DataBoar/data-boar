# ADR 0070 — Primer taxonomy and home: technical/onboarding (docs/primers/) vs deliverable (docs/plans/)

- **Date (UTC):** 2026-06-17
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao
- **Consulted:** Cursor (executor agent); Claude Code (read-only auditor — origin of #744)

## Status

Accepted

### Status history

- 2026-06-17 — Proposed
- 2026-06-17 — Accepted: ratified to proceed with the #744 migration now (Maestro gate decoupled)

## Context

The repository carries one implicit primer split across two tiers with no written
decision:

- **Technical / onboarding** primer: `docs/AI_EVOLUTION_PRIMER.md` (+ pt-BR) in the
  product-docs tier.
- **Deliverable / framework / compliance** primers: `docs/plans/*_PRIMER.md`, indexed by
  `docs/plans/PRIMERS_HUB.md`, governed by [ADR 0058](ADR-0058-primer-hub-registration-ritual.md)
  (registration ritual) and [ADR 0057](ADR-0057-lightweight-hub-index-co-located-links.md)
  (lightweight hub index).

The backlog already drifted: newer primer issues target `docs/primers/` (e.g. #744, #742,
#685) while older ones target `docs/plans/` (e.g. #629, #630, #637, #598, #590–#592, #600).
ADR-0058 pins primers and the hub to `docs/plans/`; #744 (Claude read-only audit) proposes a
dedicated `docs/primers/` home with a local INDEX. Distinct **training material** that is
neither a primer nor a TECH_GUIDE (labs, KT runbooks, onboarding tracks) is also coming and
has no home today.

A guardrail constrains the design: `tests/test_docs_external_no_plan_links.py`
([ADR 0004](ADR-0004-external-docs-no-markdown-links-to-plans.md)) scans external-tier
Markdown (which includes `docs/primers/`) and forbids links into `docs/plans/`. Technical
primers therefore must not link down into the plan-tier hub; the central hub (in
`docs/plans/`, excluded from the scan) links down to them, and primers link up to
`docs/hubs/INDEX.md` plus a local INDEX.

## Decision

1. **Two primer tiers, explicit:**
   - **Technical / onboarding / KT** primers (conceptual; audience = integrators, new
     maintainers, technical clients) live under **`docs/primers/`**.
   - **Deliverable / framework / compliance / governance** primers (external-standard
     explainers, issue-tracked) **stay under `docs/plans/`** for now; a future
     `docs/plans/primers/` subfolder is allowed in a later revision.
2. **Create `docs/primers/`** with a local mini-hub (`INDEX.md` + `INDEX.pt_BR.md`), migrate
   `docs/AI_EVOLUTION_PRIMER.md` (+ pt-BR) there, and host new technical primers (e.g. a
   `DECISION_RECORDS_PRIMER` for ADR/MADR/UMADR). This executes **#744**.
3. **One central hub:** `docs/plans/PRIMERS_HUB.md` remains the single index of all primers
   across both tiers, hung under the hub-of-hubs `docs/hubs/INDEX.md`. The `docs/primers/`
   local INDEX is a navigation aid registered/linked from the central hub
   (hub → primers direction only).
4. **Navigation rule** (enforced by the ADR-0004 test): `docs/primers/` files link **up** to
   `docs/hubs/INDEX.md` and the local INDEX, **never** into `docs/plans/`. The central hub
   and plan-tier primers (excluded from the external scan) may link **down** into
   `docs/primers/`.
5. **Hybrid promotion path:** when training material beyond primers arrives, promote
   `docs/primers/` under a `docs/training/` umbrella (`docs/training/primers/`) via a
   follow-up amendment — **not now** (avoid over-engineering).
6. **Amend, do not supersede, ADR-0058:** its registration ritual broadens to cover primers
   in `docs/primers/` as well as `docs/plans/`; the home/tier vocabulary is clarified, the
   ritual and the queued deliverable-primer issues are preserved. ADR-0057 is unaffected.

## Rationale

- Primers are **onboarding/training** material, not execution/PMO artifacts; `docs/plans/`
  conflates the two. A dedicated home matches existing `docs/hubs/INDEX.md` patterns and the
  backlog's newer convention.
- **Amend over supersede** keeps ADR-0058's ritual and the queued deliverable-primer issues
  intact; only the home/tier vocabulary changes.
- **One central hub** satisfies single-index navigation; the local INDEX aids in-folder
  discovery.
- **Deferring `docs/training/`** avoids over-engineering until non-primer training exists.

## Consequences

- **Positive:** clear tier taxonomy; stops backlog drift; cleaner `docs/`; #744 closes;
  future training material has a defined promotion path.
- **Cost:** one-time migration of `AI_EVOLUTION_PRIMER` touches ~12 cross-referencing files;
  a future amendment is needed when `docs/training/` or `docs/plans/primers/` is adopted.
- **Enforcement:** `tests/test_docs_external_no_plan_links.py` (no primer → plans links);
  `scripts/check_hubs.py` (hub link integrity); review convention from amended ADR-0058.
- **Governance:** this ADR is **Accepted**; the physical migration (#744) executes in the same
  slice. Later refinements (the `docs/training/` umbrella, a `docs/plans/primers/` subfolder)
  land via amendment or a successor ADR.

## Alternatives Considered

- **Supersede ADR-0058 + move the hub out of `docs/plans/`:** rejected — heavier blast
  radius, breaks the registration ritual and the queued issues; operator chose amend.
- **Keep everything in `docs/plans/` (status quo):** rejected — conflates training with PMO;
  backlog already drifting.
- **Create `docs/training/primers/` now:** rejected for now — over-engineering before
  non-primer training exists; kept as the hybrid promotion path.

## Related Decisions

- [ADR 0004](ADR-0004-external-docs-no-markdown-links-to-plans.md) — external docs must not
  link into plans (constrains navigation direction).
- [ADR 0057](ADR-0057-lightweight-hub-index-co-located-links.md) — lightweight hub index.
- [ADR 0058](ADR-0058-primer-hub-registration-ritual.md) — primer hub registration ritual
  (**amended by this ADR**).
- [ADR 0045](ADR-0045-adr-metadata-and-format-standardization.md) — UMADR metadata/format.
- GitHub #744 (create `docs/primers/` + migrate AI_EVOLUTION) and related primer issues.

## References

- `docs/plans/PRIMERS_HUB.md`
- `docs/hubs/INDEX.md`
- `tests/test_docs_external_no_plan_links.py`
