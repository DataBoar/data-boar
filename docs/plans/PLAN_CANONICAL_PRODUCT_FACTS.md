# Plan: Canonical product facts (anti-AI invention)

<!-- plans-hub-summary: Canonical product facts anti-AI-invention source — identity, Windows non-tech path, config/CLI truths, overclaim-safe agent block + light pytest guard on FACTS; enriches #1470 -->
<!-- plans-hub-related: PLAN_CLAIMS_CONSISTENCY_AND_ANTI_OVERCLAIM.md, PLAN_WEBSITE_AND_DOCS_I18N_FUTURE.md -->

- **Status:** In progress (slice 1: FACTS + FACTS-anchored guard)
- **Date:** 2026-08-06
- **Authors:** Fabio Leitao (operator); Cursor executor
- **Priority:** H1 (docs / discoverability / agent grounding)
- **GitHub:** [#1470](https://github.com/DataBoar/data-boar/issues/1470) (enrich; do not open a parallel issue)

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)

---

## Problem

Business and AI surfaces invent install paths, YAML keys, and repo identity (`pastas_para_varrer`, `databoarscan`, stale GitHub personal-namespace paths, Docker-as-required for non-tech). [#1470](https://github.com/DataBoar/data-boar/issues/1470) covers discoverability; this plan is the **anti-invention source of truth** so agents and docs stay overclaim-safe.

## Decision

1. Ship **`docs/CANONICAL_PRODUCT_FACTS.md`** + **`.pt_BR.md`** — terse, factual, link-oriented (site = business; repo = how to run).
2. Anchor a **light offline pytest** on those FACTS files only in slice 1.
3. **Do not** edit root README / QUICKSTART in this slice — coordinate with [#1473](https://github.com/DataBoar/data-boar/issues/1473) (identity links) and later #1470 de-Docker / non-tech README work.
4. Pre-check MUST-NOT strings with `git grep` before denylisting (avoid false positives on legitimate historical evidence). Note: [ADR-0045](../adr/ADR-0045-adr-metadata-and-format-standardization.md) is ADR metadata format — string-sweep discipline here follows that pre-check habit + [PLAN_CLAIMS_CONSISTENCY_AND_ANTI_OVERCLAIM.md](PLAN_CLAIMS_CONSISTENCY_AND_ANTI_OVERCLAIM.md).

## Execution checklist

| Step | Scope | Status |
| ---- | ----- | ------ |
| 1 | FACTS EN + pt-BR (identity, Windows path, contract, hallucinations, agent block) | ✅ |
| 2 | `tests/test_canonical_product_facts.py` (MUST / MUST-NOT on FACTS only) | ✅ |
| 3 | This plan + `plans_hub_sync.py --write` + `PLANS_TODO.md` entry | ✅ |
| 4 | Comment on #1470 (Refs; not Closes) | ⬜ with PR |
| 5 | Expand guard to README / QUICKSTART after #1473 + de-Docker slice | ⬜ |

## Acceptance (slice 1)

- [x] FACTS pair documents `pipx install data-boar`, `data-boar --demo`, `DataBoar/data-boar`, `databoar.com.br`, Docker optional, Docker Hub image `fabioleitao/data_boar` labeled distinct from GitHub.
- [x] FACTS MUST-NOT invented keys / CLI / stale GitHub path substring / Docker-as-required-for-non-tech.
- [x] Guard green offline in pytest.
- [ ] README/QUICKSTART alignment — **out of slice 1**.

## Out of scope

- Root README “Não é de TI?” block (#1470 later slice).
- QUICKSTART Docker wording (#1470 later).
- MSI / winget packaging ([#1467](https://github.com/DataBoar/data-boar/issues/1467)).
- Closing #1470 entirely.
