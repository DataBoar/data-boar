# ADR 0025 — Compliance positioning: evidence and inventory, not a legal-conclusion engine

- **Status:** Accepted
- **Date (UTC):** 2026-04-08
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Context

Data Boar discovers and labels **personal and sensitive data** across configured sources and produces **metadata-only** reports (locations, pattern types, framework-oriented recommendation text). Buyers and partners sometimes ask whether the product **eliminates legal risk**, **detects violations**, or **replaces** DPO/counsel. Over-stating capabilities would mislead regulated customers and create liability expectations the software cannot satisfy.

The product **is** configurable (**profiles**, **regex overrides**, **recommendation overrides**, **[compliance-samples/](compliance-samples/)**) and can be scoped with **professional services**—flexibility without changing this fundamental boundary.

## Decision

1. **Positioning:** Market and document the product as a **technical evidence and inventory** layer that **supports** governance, prioritisation, and specialist review—not as an **eliminator of legal risk** or an **automated legal-conclusion** system.

2. **Language:** Prefer **indicators for review**, **possible exposure**, **evidence for DPO/counsel**, and **metadata-only findings**. Avoid claiming **determination of violations**, **notifiability**, or **compliance certification** unless a future feature is explicitly designed and legally reviewed for that narrow scope (none today).

3. **Joint delivery:** Explicitly welcome a **three-way** value story—**product** (repeatable scans and artefacts) + **client legal/compliance** (judgment) + **optional consulting** (scoping and tuning)—without implying the product alone closes the loop.

4. **Documentation anchors:** Keep the public ceiling in **[COMPLIANCE_AND_LEGAL.md](../COMPLIANCE_AND_LEGAL.md)** and **[COMPLIANCE_FRAMEWORKS.md](../COMPLIANCE_FRAMEWORKS.md)**; keep deep regulator backlogs and horizon notes in **[PLAN_COMPLIANCE_EVIDENCE_MAPPING.md](../plans/PLAN_COMPLIANCE_EVIDENCE_MAPPING.md)** (internal). Do **not** require a separate **QA journal** file for this positioning; **gitignored** `docs/private/` remains available for **operator-only** commercial nuance per **[PRIVATE_OPERATOR_NOTES.md](../PRIVATE_OPERATOR_NOTES.md)**.

## Consequences

- Sales, pitch, and external docs must stay aligned with **COMPLIANCE_AND_LEGAL** wording; internal plans may explore **future** samples without becoming public **compliance promises**.
- New features that surface **legal-sounding** outputs need explicit **product** and **legal** review so outputs remain **indicators** unless scope intentionally changes (and docs update).
- Contributors can cite **this ADR** when deciding whether a proposed feature crosses from **inventory** into **legal opinion** or **regulated monitoring**.

## References

- [ADR 0026](ADR-0026-optional-jurisdiction-hints-dpo-facing-heuristic-metadata-only.md) — optional **jurisdiction hints** (same ceiling: indicators for review, not legal applicability).
- [COMPLIANCE_AND_LEGAL.md](../COMPLIANCE_AND_LEGAL.md) — “What we surface”, “What we do not do”, professional services.
- [GLOSSARY.md](../GLOSSARY.md) §**9** — short definitions of **metadata-only finding**, **counsel**, **DPIA**, **RoPA**, **TIA**/**SCC**, **PEP**/**KYC**, **compliance sample**.
- [PLAN_COMPLIANCE_EVIDENCE_MAPPING.md](../plans/PLAN_COMPLIANCE_EVIDENCE_MAPPING.md) — section 8 backlog, positioning ceiling paragraph.
- [ADR 0022](ADR-0022-public-glossary-compliance-and-platform-terms.md) — public glossary taxonomy; roles (DPO, etc.).
