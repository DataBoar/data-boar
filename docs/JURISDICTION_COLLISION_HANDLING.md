# Jurisdiction collision handling (DPO-facing)

**Português (Brasil):** [JURISDICTION_COLLISION_HANDLING.pt_BR.md](JURISDICTION_COLLISION_HANDLING.pt_BR.md)

This guide explains how to **read** optional **jurisdiction hints** when metadata suggests **more than one** privacy regime might be in play—without treating the product as a legal engine.

## What Data Boar does and does not do

- **Does:** Surface **heuristic** “possible relevance” text on the Excel **Report info** sheet (when hints are enabled), using **only finding metadata** (column/table/file/path names, `pattern_detected`, `norm_tag`, etc.)—see [ADR 0026](adr/ADR-0026-optional-jurisdiction-hints-dpo-facing-heuristic-metadata-only.md) and [ADR 0038](adr/ADR-0038-jurisdictional-ambiguity-alert-dont-decide.md).
- **Does not:** Determine **which law applies**, **which form to file first**, **most restrictive jurisdiction** as an automated legal outcome, or **lawful basis** (including LGPD Art. 7 II or customs/security exceptions). **Counsel** and the **DPO** own those calls.

## The “perfect storm” (why this doc exists)

Multinational operations—logistics, ports, aviation, payroll shared services—often hold **one profile** of data where **signals point in different directions**: document types or phone prefixes suggest one country, employer or host another, audit or customs regime another. That is **operational paralysis risk** for privacy teams, not only a regex problem.

**Customs-adjacent / bonded-area note:** border and **recinto**-style programmes may **require** collection that looks “heavy” from a pure privacy-minimisation lens. Data Boar still only delivers **inventory evidence** and **hints**; it does **not** label rows as “legal obligation satisfied” or choose retention periods—see [ADR 0039](adr/ADR-0039-retention-evidence-posture-bonded-customs-adjacent-contexts.md) and [THE_WHY.md](philosophy/THE_WHY.md).

Data Boar’s opportunity is to **visualise the tangle** (inventory and triage language) so the **DPO** and **CISO** can prioritise **counsel review**—not to untie the knot in software.

## Scent origin (metaphor)

**Scent origin** is a narrative label in this repo (see [GLOSSARY.md](GLOSSARY.md#glossary-stakeholder-jargon)): jurisdiction hints are **probabilistic incidence signals** inferred from **incomplete** metadata—like picking up **several** scents at once. A strong scent is **not** legal certainty.

## Hint layers (analytical lens)

Use this lens when reading reports and planning playbooks:

| Layer | Meaning (documentation) | Typical inputs (examples) |
| ----- | ------------------------ | --------------------------- |
| **Primary (anchor)** | **Operational anchor**: where the **scanner runs** and where the **controller’s systems under scan** live (contract, SOX/RoPA scope, host country). Often dominates **internal policy** and retention. | Deployment region, target labels in config, organisation’s chosen governing policy (outside the product). |
| **Secondary (data nature)** | **Data-shape signals**: identifiers and norm tags that **suggest** which regimes teams should **consider** (e.g. CPF → Brazil vocabulary, SSN → US vocabulary). | `norm_tag`, `pattern_detected`, compliance sample hooks. |
| **Contextual (metadata drift)** | **Weak geographic tokens** in names/paths (area codes, state tokens, ZIP-like prefixes) that may **overlap** regions or **false-positive**. | Column/path strings scored in `report/jurisdiction_hints.py` (US-CA, US-CO, JP today). |

**Anchor vs drift:** **Anchor** is your operational/legal home base for the inventory run; **drift** is data that “passed through” or belongs to **other** contexts (crew manifests, foreign ID formats, multinational HR). The product does **not** automatically classify anchor vs drift; teams apply that frame in workshops.

## “Jurisdiction collision” today vs roadmap

**Today (shipped):** When multiple regional heuristics fire, the Report info sheet can show **more than one** jurisdiction hint row (e.g. US-CA and US-CO both above threshold). That is a **human-visible overlap signal**—still **not** a numeric “collision score” and **not** per-finding row tables.

**Roadmap / product intelligence (not promised in this release):** A consolidated **collision summary** (counts, severity band, optional per-session flag) would be a **separate** design: privacy review, UX in Excel/API, and an ADR update. See [ADR 0038](adr/ADR-0038-jurisdictional-ambiguity-alert-dont-decide.md).

## Suggested counsel-facing sentence

Use verbatim in slide decks if useful:

> **Data Boar does not issue legal opinions.** It may surface **overlapping jurisdiction hints** from **metadata** so teams see **where tension exists**. When multiple hints apply, organisations often apply the **strictest practical safeguards** pending counsel—but that **choice** is **not** encoded as an automatic verdict in the product.

## Related documentation

- [USAGE.md](USAGE.md) — `report.jurisdiction_hints`, `--jurisdiction-hint`, API/dashboard ([pt-BR](USAGE.pt_BR.md))
- [COMPLIANCE_AND_LEGAL.md](COMPLIANCE_AND_LEGAL.md) — ceiling language ([pt-BR](COMPLIANCE_AND_LEGAL.pt_BR.md))
- [MAP.md](MAP.md) — concern-first index ([pt-BR](MAP.pt_BR.md))
- [use-cases/PORT_LOGISTICS_MULTINATIONAL_CREW.md](use-cases/PORT_LOGISTICS_MULTINATIONAL_CREW.md) — storyboard (non-exhaustive scenario)
- [ADR 0025](adr/ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md), [ADR 0026](adr/ADR-0026-optional-jurisdiction-hints-dpo-facing-heuristic-metadata-only.md), [ADR 0038](adr/ADR-0038-jurisdictional-ambiguity-alert-dont-decide.md), [ADR 0039](adr/ADR-0039-retention-evidence-posture-bonded-customs-adjacent-contexts.md)
- [THE_WHY.md](philosophy/THE_WHY.md) ([pt-BR](philosophy/THE_WHY.pt_BR.md))
