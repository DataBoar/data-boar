# ADR 0000: Project origin and ADR baseline

**Status:** Accepted
**Date:** 2026-03-26
**Authors:** Fabio Leitao

---

## Context

The repository **`data-boar`** hosts **Data Boar** — a compliance-oriented engine to **discover and map personal and sensitive data** across files, databases, APIs, and related “data soup” sources, with reporting and dashboard surfaces for operators and compliance roles. The product positioning and feature narrative live in the canonical **[README.md](../../README.md)**; technical operation is in **[docs/TECH_GUIDE.md](../TECH_GUIDE.md)** and **[docs/USAGE.md](../USAGE.md)**.

For years before **Architecture Decision Records** existed in this tree, design choices were embedded in **code**, **plans** under **`docs/plans/`**, **release notes** under **`docs/releases/`**, and **SECURITY** / **CONTRIBUTING** text — without a numbered “why” series. That history remains valid; this ADR does **not** replace those sources.

## Decision

1. Reserve **ADR 0000** as a **short historical anchor**: what the app is for, where the canonical pitch and tech docs live, and that substantive decisions before **March 2026** were not recorded as ADRs.
1. Keep **ADR 0001+** for **explicit** decisions made after ADRs were adopted in-repo (tooling, security doc policy, SBOM roadmap, etc.).
1. Do **not** renumber existing ADRs when adding 0000; new readers see **0000** first in the index, then chronological **0001**, **0002**, …

## Consequences

- **Positive:** One place to point newcomers (“why is there no ADR for X from 2022?”) without rewriting old history.
- **Negative:** Slight overlap with README — keep 0000 **brief** and link out.

## References

- [README.md](../../README.md) · [README.pt_BR.md](../../README.pt_BR.md)
- [docs/TECH_GUIDE.md](../TECH_GUIDE.md) · [docs/NARRATIVE_AND_ARCHITECTURE_HISTORY.md](../NARRATIVE_AND_ARCHITECTURE_HISTORY.md) *(placeholder for a longer timeline if you add one)*
- [docs/ACADEMIC_USE_AND_THESIS.md](../ACADEMIC_USE_AND_THESIS.md) — thesis / dissertation guidance (EN + pt-BR)
- [docs/adr/README.md](README.md) — index and numbering rules
