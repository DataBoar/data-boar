# Use-case storyboard — law firm, client matters, and trust data (mid-market)

**Português (Brasil):** [LAW_FIRM_CLIENT_MATTER_AND_TRUST_DATA.pt_BR.md](LAW_FIRM_CLIENT_MATTER_AND_TRUST_DATA.pt_BR.md)

This is a **documentation storyboard** for workshops and POC narratives for **small and mid-sized** firms (boutique to regional). It is **not** legal analysis of privilege, conflicts, or professional secrecy in any jurisdiction.

## Cast (generic roles)

- **Organisation:** A partnership or professional corporation with **many concurrent matters** (civil, labour, tax, family).
- **Data subjects:** Clients, opposing parties, witnesses, minors in family-law contexts, corporate officers in M&A.
- **Systems:** Document management exports, **email PST/mbox**, shared drives named by client or matter, CRM or practice-management databases, court filing PDFs, **billing** exports.

## Storyboard (flow)

1. **Matter opens** — intake creates folders, matter numbers, and contact records across DMS + email + billing.
2. **Work product accumulates** — drafts, evidence bundles, spreadsheets with party lists; **naming conventions** leak structure (client codenames vs real company strings).
3. **Cross-matter risk** — the same person or entity may appear in **conflicting** roles; **privilege** boundaries are organisational (who may see what), not something the scanner “knows”.
4. **Boar sniffs (governance-approved scope)** — connectors surface **PII-like** patterns (phones, national IDs where regex applies, addresses) and **ambiguous** identifiers (`doc_id`, `party_ref`).
5. **Aggregation sheet** — [cross-ref risk](../SENSITIVITY_DETECTION.md) may flag **combinations** of quasi-identifiers in one export; still **metadata-only** inventory.
6. **Human moment** — **Counsel** decides lawful basis, retention, who may access matter stores; **IT** tightens shares and MFA. The tool does **not** label “privileged” vs “non-privileged” content.

## How Data Boar helps without deciding

- **Maps** where **party identifiers** and **matter metadata** concentrate (paths, column names, samples).
- **Supports** workshops on **minimisation** and **access segmentation** (which shares should exist at all).
- **Does not** replace conflicts software, e-discovery platforms, or bar-association guidance.

## Partner opportunity

Legal-tech and **IRL** consultancies attach a **bounded metadata inventory** to matter-intake or **post-merger** hygiene projects—explicitly **not** privilege labelling in the tool.

## Product alignment (maintainers)

Demand often pushes **sensitivity aggregation**, **ambiguous PII** columns, and **path-heavy** narratives. Maintainer sequencing: [docs/README.md](../README.md) *Internal and reference*.

## Related docs

- [use-cases/README.md](README.md) ([pt-BR](README.pt_BR.md)) — storyboard hub.
- [COMPLIANCE_AND_LEGAL.md](../COMPLIANCE_AND_LEGAL.md) ([pt-BR](../COMPLIANCE_AND_LEGAL.pt_BR.md))
- [SENSITIVITY_DETECTION.md](../SENSITIVITY_DETECTION.md) ([pt-BR](../SENSITIVITY_DETECTION.pt_BR.md)) — aggregated identification, `PII_AMBIGUOUS`
- [MINOR_DETECTION.md](../MINOR_DETECTION.md) ([pt-BR](../MINOR_DETECTION.pt_BR.md))
- [MAP.md](../MAP.md) ([pt-BR](../MAP.pt_BR.md))
