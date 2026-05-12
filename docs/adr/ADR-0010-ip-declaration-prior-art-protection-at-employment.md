# ADR 0010: IP Declaration as prior-art protection for Data Boar at CLT employment

**Status:** Accepted
**Date:** 2026-03-27 (IP Declaration sent) / Recorded: 2026-04-03
**Authors:** Fabio Leitao

---

## Context

The operator accepted a CLT employment offer at **the operator's employer**. Standard Brazilian CLT employment contracts typically
include clauses assigning intellectual property created by the employee — or discovered during
the employment period — to the employer, unless explicitly excluded.

**Data Boar** had been in active development since **October 2025** as an independent open-source
project, with lab-op infrastructure, code, documentation, and commercial plans predating the
the employer's offer. The question was: how to ensure Data Boar's IP remains with the operator
and does not fall under an IP assignment clause signed at onboarding?

Options considered:

| Option | Risk | Outcome |
|---|---|---|
| Do nothing | IP assignment clause could retrospectively claim Data Boar | Unacceptable |
| Formal letter of prior invention before signing | Establishes written record of prior art | Standard legal practice |
| Open-source release before signing | Creates public prior art (timestamp) | Complementary, but not sufficient alone |
| Legal consultation | Best for certainty, costly | Deferred; prior declaration is first step |

## Decision

1. Send a **formal IP Declaration** to the designated responsible at the operator's employer **before**
   the employment contract takes effect, explicitly declaring
   Data Boar as **prior art / prior invention** — independently created before the employment
   relationship and therefore **excluded** from any IP assignment clause.
2. The declaration was sent on **2026-03-27** — before the employment start date (April 2026).
3. Record the existence and date of the declaration in private notes (`OPERATOR_RETEACH.md`,
   `OPERATOR_LIFE_JOURNEY_2022_2026.pt_BR.md`) but do **not** commit the full declaration text
   to the tracked repository (it contains identifying information and legal context that belongs
   in `docs/private/`).
4. Establish this as a **repeatable pattern** for the project: any future employment, consulting
   agreement, or partnership must trigger a review of IP clauses and, where necessary, a prior-art
   declaration before signing.

## Consequences

- **Positive:** Creates a written, timestamped record of prior invention that pre-dates the
  employment contract — the strongest protection available without formal legal counsel.
- **Positive:** The declaration was sent proactively, reducing the risk of dispute during or after
  employment.
- **Positive:** Establishes a clear precedent for how the project handles future employment / partnership
  agreements — no need to re-decide each time.
- **Negative:** A formal declaration is not a substitute for legal review. If the employer's contract
  has a specific exclusion form or process, that should also be followed. Legal counsel is deferred.
- **Watch:** If Data Boar is commercialised (client contracts, revenue), a more formal IP
  protection review (patent, copyright registration, legal entity) should be triggered.
  This ADR records the minimum viable step taken at the pre-revenue stage.

## References

- `docs/private/homelab/OPERATOR_RETEACH.md` §C (employment context — gitignored)
- `docs/private/author_info/OPERATOR_LIFE_JOURNEY_2022_2026.pt_BR.md` (IP Declaration timeline)
- `docs/private/author_info/OPERATOR_CONTEXT_FOR_AGENT.pt_BR.md` (employment context)
- `docs/private/author_info/STRATEGIC_ALIGNMENT_MASTER.pt_BR.md` (long-term IP strategy)
- [ADR 0000](ADR-0000-project-origin-and-adr-baseline.md) — project origin and Data Boar history
