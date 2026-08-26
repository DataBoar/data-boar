# Plan: Public feature-by-tier page (no prices)

**Status:** Active
**Date:** 2026-08-26
**Authors:** Fabio Leitao
**Priority:** H2
**Depends on:** [PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md](PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md)

<!-- plans-hub-summary: Comparativo público de faixas — Community, Std, Pro, Pro+, Ent, Partner/WL; eixos capacidade vs quantidade -->
<!-- plans-hub-related: PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md -->

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md) · GitHub [#610](https://github.com/DataBoar/data-boar/issues/610)

## Purpose

Publish `docs/PRICING.md` (+ pt-BR) as a **feature + quantity-axis map** for the live ladder (Community, Std, Pro, Pro+, Enterprise, Partner/white-label), with a contact CTA and **no** amounts. Keep quotes in gitignored `docs/private/`. Issue #610’s three-column sketch is superseded by this page.

## Sequential to-dos

| Step | Task | Status |
| ---- | ---- | ------ |
| 1 | EN + pt-BR `docs/PRICING.md`: full ladder + quantity/franchise axis + Catalyst/Supporter as evaluation-only | ✅ Done |
| 2 | Cross-link README, AUDIENCE_GUIDE (CFO trail), SUBSCRIPTION_TIERS | ✅ Done this PR |
| 3 | Hub sync + PLANS_TODO row | ✅ Done this PR |
| 4 | When `FEATURE_TIER_MAP` changes, update PRICING in the same PR | 🔄 Ongoing |

## Out of scope

- Hardcoded prices, discounts, or partner commissions
- Inventing keys (JSONL report, OIDC) that are not in the map
