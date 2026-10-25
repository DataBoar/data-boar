# ADR 0039 — Retention and evidence posture in bonded / customs-adjacent contexts

- **Status:** Accepted
- **Date (UTC):** 2026-04-08
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Context

Controllers in **logistics**, **ports**, **aviation**, and other **customs-adjacent** environments often process **strong identifiers** and sometimes **biometrics** under **sector or border-control** programmes. Privacy law still demands **purpose limitation**, **minimisation**, **retention discipline**, and lawful documentation. That creates **policy tension** (security vs privacy narratives) that junior tooling often ignores or “resolves” falsely in product marketing.

Data Boar is an **inventory and evidence-support** scanner—not a **retention enforcement** platform, not a **lawful-basis** engine, and not an automatic classifier for **legal exceptions** (e.g. LGPD Art. 7 II, GDPR Art. 6(1)(c)—**counsel** maps facts to articles).

## Decision

1. **Product boundary (unchanged):** The engine produces **metadata findings**, optional **jurisdiction hints**, and **reports**; it does **not** implement **port-specific retention schedules**, **customs hold periods**, or **automatic “security exception” flags** tied to geography.

2. **Operator-owned retention:** Retention of the **SQLite** store, Excel exports, logs, and backups follows **deployment** and **organisational** policy (`report.*`, filesystem hygiene, backup tooling)—documented in [USAGE.md](../USAGE.md), [deploy/DEPLOY.md](../deploy/DEPLOY.md), and [COMPLIANCE_AND_LEGAL.md](../COMPLIANCE_AND_LEGAL.md). **Bonded-area** programmes do **not** get a special code path; operators document **why** they keep scans as long as they do.

3. **Evidence hygiene:** [ADR 0036](ADR-0036-exception-and-log-pii-redaction-pipeline.md) (redacted errors/logs) and [ADR 0037](ADR-0037-data-boar-self-audit-log-governance.md) (export audit trail, wipe log) support **professional** posture when the same teams that face **regulatory** pressure also handle **operator** diagnostics—without turning stack traces into **secondary PII leaks**.

4. **Narrative anchors (public):** Workshop framing for “why evidence matters in high-friction zones” lives in **[THE_WHY.md](../philosophy/THE_WHY.md)** and the **[port logistics storyboard](../use-cases/PORT_LOGISTICS_MULTINATIONAL_CREW.md)**—**generic** roles, no employer names, no personal dossier content.

5. **Explicit non-goal:** A future feature that tags findings with **“legal basis = customs obligation”** would require **separate** legal review, UX, and ADR; it is **out of scope** here.

## Consequences

- Sales and POC decks can say Data Boar helps teams **prepare evidence** for **retention and lawful-basis** discussions in **complex** environments—without claiming the binary **solves** customs law.
- If sector-specific **retention templates** or **config presets** are ever added, they ship as **documentation + samples** first, then optional code, each with its own ADR.

## References

- [ADR 0025](ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md), [ADR 0036](ADR-0036-exception-and-log-pii-redaction-pipeline.md), [ADR 0037](ADR-0037-data-boar-self-audit-log-governance.md), [ADR 0038](ADR-0038-jurisdictional-ambiguity-alert-dont-decide.md)
- [THE_WHY.md](../philosophy/THE_WHY.md), [JURISDICTION_COLLISION_HANDLING.md](../JURISDICTION_COLLISION_HANDLING.md)
- [use-cases/PORT_LOGISTICS_MULTINATIONAL_CREW.md](../use-cases/PORT_LOGISTICS_MULTINATIONAL_CREW.md)
