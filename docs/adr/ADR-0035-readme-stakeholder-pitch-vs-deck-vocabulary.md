# ADR 0035 — README stakeholder pitch vs optional deck vocabulary

## Context

The root **README** has two audiences in one file: an executive **“For decision-makers”** block (plain language, metaphor-led) and a **“Technical overview”** table that points integrators to **USAGE**, **TECH_GUIDE**, **SENSITIVITY_DETECTION**, etc.

Separately, compliance slide banks and structured technical docs use optional paired labels **Data Sniffing** (discovery/sampling pass) and **Deep Boring** (structured report depth), defined in **GLOSSARY** and scoped in **COMPLIANCE_FRAMEWORKS** — useful for procurement/DPO workshops, **not** as mandatory wording in the README executive paragraph.

External review (including Gemini-suggested hygiene) flagged a regression risk: internal POC vocabulary could drift into the **stakeholder pitch**, confusing non-technical readers and contradicting the **information architecture** split between pitch and deep docs ([ADR 0004](ADR-0004-external-docs-no-markdown-links-to-plans.md), [ADR 0022](ADR-0022-public-glossary-compliance-and-platform-terms.md)).

## Decision

1. Treat the README section from **“For decision-makers…”** through the line **before** **“Technical overview”** / **“Visão técnica”** as **stakeholder copy**: keep headings such as **Sniffing with judgment** / **Farejando com critério** and everyday phrasing; **do not** require or insert **Data Sniffing** / **Deep Boring** there.
2. Keep **Data Sniffing** / **Deep Boring** as **optional** labels in **COMPLIANCE_FRAMEWORKS**, **COMPLIANCE_TECHNICAL_REFERENCE**, **GLOSSARY**, and related plans — explicitly documented as deck/technical scope, not README pitch scope.
3. Encode the boundary in **CI**: a narrow pytest module asserts the stakeholder slice contains the judgment headings and does **not** contain the deck-only product labels, so edits cannot silently “enterprise-wash” the pitch.

## Consequences

- **Positive:** Contributors and agents have a **machine-checked** guardrail; glossary and compliance docs can evolve deck language without rewriting the README opening.
- **Negative:** Changing the README pitch structure (heading text) requires updating the pytest contract in the same PR.
- **Related:** Outbound HTTP identity on the wire remains **ADR 0034** (`DataBoar-Prospector/<version>`) — orthogonal to README prose; both ADRs are linked from **AGENTS.md** for assistant routing.

## References

- [ADR 0034 — Outbound HTTP User-Agent](ADR-0034-outbound-http-user-agent-data-boar-prospector.md)
- [COMPLIANCE_FRAMEWORKS.md](../COMPLIANCE_FRAMEWORKS.md) (Engine vocabulary section)
- [GLOSSARY.md](../GLOSSARY.md) (Product identity rows)
- `tests/test_readme_stakeholder_pitch_contract.py`
