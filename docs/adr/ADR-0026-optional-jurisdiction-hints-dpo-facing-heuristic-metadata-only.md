# ADR 0026 — Optional jurisdiction hints (DPO-facing, heuristic, metadata-only)

- **Status:** Accepted
- **Date (UTC):** 2026-04-08
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Context

Multinational and multi-framework customers often ask for **early signals** when inventory metadata (column names, paths, norm tags) might suggest **possible** relevance to **specific privacy regimes** (e.g. U.S. state consumer laws, Japan APPI), so DPOs and counsel can **prioritise review**. At the same time, [ADR 0025](ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md) requires that the product **not** present itself as determining **legal applicability**, **scope**, or **violations**.

Raw cell values are **not** persisted in SQLite for findings in the default model; hints must therefore operate on **finding metadata** only, which makes them **incomplete** and prone to **false positives and false negatives**.

## Decision

1. **Feature shape:** Implement **optional, opt-in** “jurisdiction hint” rows on the Excel **Report info** sheet, gated by `report.jurisdiction_hints` and/or per-session flags (CLI, API, dashboard). **No** change to sensitivity scoring solely because a hint fired.

2. **Content contract:** Text must state **heuristic / possible relevance**, name the **framework** in plain language where helpful (e.g. CCPA/CPRA, Colorado CPA-style framing, Japan APPI), and **require counsel review**—aligned with ADR 0025 language.

3. **Signal source:** Score from **concatenated metadata** for the session’s findings (column/table/file/path/pattern/norm_tag fields), not from stored PII payloads.

4. **Documentation anchors:** Operator detail in **[USAGE.md](../USAGE.md)**; buyer/DPO ceiling in **[COMPLIANCE_AND_LEGAL.md](../COMPLIANCE_AND_LEGAL.md)**; multinational **tension** narrative (not legal advice) in **[JURISDICTION_COLLISION_HANDLING.md](../JURISDICTION_COLLISION_HANDLING.md)** ([pt-BR](../JURISDICTION_COLLISION_HANDLING.pt_BR.md)) and **[ADR 0038](ADR-0038-jurisdictional-ambiguity-alert-dont-decide.md)**. **No** requirement for a separate **public** QA journal; optional **private** operator notes remain in gitignored `docs/private/` per **[PRIVATE_OPERATOR_NOTES.md](../PRIVATE_OPERATOR_NOTES.md)**.

5. **Roadmap / pitch:** Mention as **evidence-supporting triage** for legal/compliance readers—not as a compliance guarantee—see repository **[README.md](../../README.md)** *Roadmap* and **Compliance and legal**.

## Consequences

- Additional regions or scoring rules are **product/config** changes; extending **compliance samples** remains the path for **client-specific** vocabulary without forking core behaviour.
- Future enhancements that use **cell content** for geography would be a **separate** decision (privacy, retention, and ADR review).

## References

- [ADR 0025](ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md) — evidence and inventory, not legal-conclusion engine.
- [ADR 0038](ADR-0038-jurisdictional-ambiguity-alert-dont-decide.md) — overlapping regimes: alert, do not decide applicable law.
- [COMPLIANCE_AND_LEGAL.md](../COMPLIANCE_AND_LEGAL.md) — “What we surface”, “What we do not do”.
- [JURISDICTION_COLLISION_HANDLING.md](../JURISDICTION_COLLISION_HANDLING.md) — DPO-facing narrative for multinational “perfect storms”.
- [USAGE.md](../USAGE.md) — `report.jurisdiction_hints`, `--jurisdiction-hint`, API/dashboard opt-in.
