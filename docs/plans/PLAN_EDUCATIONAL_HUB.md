# Plan: Educational hub (onboarding and anti-hype navigation)

**Status:** Active
**Date:** 2026-08-26
**Authors:** Fabio Leitao
**Priority:** H2
**Depends on:** [ADR-0004](../adr/ADR-0004-external-docs-no-markdown-links-to-plans.md), [ADR-0057](../adr/ADR-0057-lightweight-hub-index-co-located-links.md), [ADR-0070](../adr/ADR-0070-primer-taxonomy-and-home.md)

<!-- plans-hub-summary: hub de materiais educacionais, onboarding e anti-hype -->
<!-- plans-hub-related: PRIMERS_HUB.md -->

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md) · GitHub [#627](https://github.com/DataBoar/data-boar/issues/627)

## Purpose

Add a **navigation-only** hub so evaluators and CISOs can find onboarding (QUICKSTART, audience guide) and the anti-hype AI primer without hunting through `PRIMERS_HUB` related links. Do **not** duplicate primer or glossary prose.

Canonical files:

- `docs/hubs/EDUCATIONAL_HUB.md` (+ pt-BR)
- Technical primers: `docs/primers/AI_EVOLUTION_PRIMER.md` (not `docs/AI_EVOLUTION_PRIMER.md`)
- Framework primers index: `docs/plans/PRIMERS_HUB.md` (path only from the educational hub — ADR-0004)

## Sequential to-dos

| Step | Task | Status |
| ---- | ---- | ------ |
| 1 | Create EN + pt-BR educational hub (onboarding, anti-hype, frameworks path, glossary) | ✅ Done |
| 2 | Register in `docs/hubs/INDEX.md` (+ pt-BR) and `docs/ops/DOCS_AND_HUBS_INDEX.md` | ✅ Done |
| 3 | `python scripts/plans_hub_sync.py --write` and PLANS_TODO row | ✅ Done this PR |
| 4 | Optional later: video walkthrough, lab tutorial rows (no content duplication) | ⬜ Pending |

## Out of scope

- Rewriting `AGENTS.md` or moving primers between folders
- Markdown links from buyer-facing product guides into `docs/plans/`
