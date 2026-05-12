# ADR 0038 — Jurisdictional ambiguity: alert and inventory, do not decide law

**Status:** Accepted
**Date:** 2026-04-08

## Context

Operators described **multinational “perfect storms”**: one operational dataset (e.g. crew access logs, manifests, ID scans) where **metadata** can simultaneously suggest attention to **several** privacy regimes (host state, employer state, document-issuing state, sector security rules). That is common in **logistics, ports, aviation, and critical infrastructure**—not an exotic edge case.

[ADR 0025](ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md) already positions the product as **evidence and inventory**, not a legal-conclusion engine. [ADR 0026](ADR-0026-optional-jurisdiction-hints-dpo-facing-heuristic-metadata-only.md) added **optional** Excel **Report info** rows scored from **finding metadata** only (today: US-CA, US-CO, JP heuristics in `report/jurisdiction_hints.py`).

Stakeholders asked for clearer **narrative** and **career-safe positioning**: show the **tangle**, help DPO/CISO **prioritise counsel**, and avoid implying the scanner picks **applicable law**, **lawful basis**, or **“most restrictive jurisdiction”** automatically—including LGPD Art. 7 II or customs/security exceptions.

## Decision

1. **Product posture:** When metadata suggests **overlapping** regimes, the product **surfaces tension** (multiple hint rows today; optional future **summary** band) and **never** outputs a machine **legal verdict** on which statute controls processing.

2. **Organisational principle (documentation only):** Teams may adopt **stricter interim safeguards** pending counsel; that is a **human** programme choice—**not** encoded as an automatic “apply strictest law” flag in core detection.

3. **Documentation anchors:** Long-form DPO narrative lives in **[JURISDICTION_COLLISION_HANDLING.md](../JURISDICTION_COLLISION_HANDLING.md)** ([pt-BR](../JURISDICTION_COLLISION_HANDLING.pt_BR.md)); a **use-case storyboard** for port-style multinational crew flows lives under **[use-cases/](../use-cases/)**. Glossary adds **scent origin**, **anchor jurisdiction (operational framing)**, **drifted data persona**, **jurisdiction hint**, **jurisdiction tension**—see [ADR 0022](ADR-0022-public-glossary-compliance-and-platform-terms.md) maintenance habit.

4. **Implementation scope:** Any **numeric “collision score”**, **per-finding hint table**, or **automatic lawful-basis tagging** (e.g. LGPD Art. 7 II) requires a **future** ADR and privacy/UX review—**out of scope** for this decision record.

## Consequences

- Marketing and POC decks can honestly claim **“visualise jurisdictional ambiguity”** at the **metadata / triage** layer without over-selling **legal automation**.
- Extending regions in `jurisdiction_hints.py` remains **incremental engineering**; collision **aggregation** is a separate product slice when prioritised.

## References

- [ADR 0025](ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md), [ADR 0026](ADR-0026-optional-jurisdiction-hints-dpo-facing-heuristic-metadata-only.md)
- [JURISDICTION_COLLISION_HANDLING.md](../JURISDICTION_COLLISION_HANDLING.md)
- [report/jurisdiction_hints.py](../../report/jurisdiction_hints.py)
