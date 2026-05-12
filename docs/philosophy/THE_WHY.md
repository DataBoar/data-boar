# The why — evidence over theatre

**Português (Brasil):** [THE_WHY.pt_BR.md](THE_WHY.pt_BR.md)

This page states **public, product-level philosophy** only: why Data Boar emphasises **technical evidence**, **metadata-first** reporting, and **honest limits**. It does **not** replace [COMPLIANCE_AND_LEGAL.md](../COMPLIANCE_AND_LEGAL.md), [ADR 0025](../adr/ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md), or counsel.

## What we optimise for

- **Inventory you can defend:** connectors, sampling, findings, and reports that help **CISO**, **DPO**, and **operators** see where personal and sensitive data live—not a slide deck pretending coverage.
- **Operational truth:** the same rigour you expect from **SRE** culture (timeouts, rate limits, health signals, log hygiene) applied to **discovery** work—bounded scans, clear failure modes, redacted operator logs where errors could leak context ([ADR 0036](../adr/ADR-0036-exception-and-log-pii-redaction-pipeline.md)).
- **Field-grade complexity:** high-friction environments—**logistics**, **customs-adjacent** flows, multinational crews—where one dataset carries **many** jurisdictional **signals**. The product **surfaces tension** for humans to resolve ([JURISDICTION_COLLISION_HANDLING.md](../JURISDICTION_COLLISION_HANDLING.md), [ADR 0038](../adr/ADR-0038-jurisdictional-ambiguity-alert-dont-decide.md)); it does **not** pick applicable law.

## What we refuse to be

- A **paper-compliance** substitute: no substitute for **counsel**, **RoPA/DPIA** ownership, or **retention** decisions.
- A **black box** that invents legal outcomes: jurisdiction hints are **heuristic**; sensitivity is **technical** classification, not a statutory verdict.

## Where the storyboard lives

For a **generic** port-style multinational flow (workshops, POC decks), see [use-cases/PORT_LOGISTICS_MULTINATIONAL_CREW.md](../use-cases/PORT_LOGISTICS_MULTINATIONAL_CREW.md) ([pt-BR](../use-cases/PORT_LOGISTICS_MULTINATIONAL_CREW.pt_BR.md)).

## Related

- [ADR 0039](../adr/ADR-0039-retention-evidence-posture-bonded-customs-adjacent-contexts.md) — retention/evidence boundary in customs-adjacent contexts (no automated lawful-basis tags).
- [MAP.md](../MAP.md) — concern-first index ([pt-BR](../MAP.pt_BR.md))
- [README.md](../../README.md) — **The Architect's Vault** (ADRs, briefs, narrative placeholders)
