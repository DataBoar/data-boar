# Plan: Public feature-by-tier page (no prices)

**Status:** Active
**Date:** 2026-08-26
**Authors:** Fabio Leitao
**Priority:** H2
**Depends on:** [PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md](PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md)

<!-- plans-hub-summary: Comparativo público de tiers — o que está em community, pro e enterprise -->
<!-- plans-hub-related: PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md -->

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md) · GitHub [#610](https://github.com/DataBoar/data-boar/issues/610)

## Purpose

Publish `docs/PRICING.md` (+ pt-BR) as a **feature map** grounded in `FEATURE_TIER_MAP`, with a contact CTA and **no** amounts. Keep numbers in gitignored `docs/private/`.

## Sequential to-dos

| Step | Task | Status |
| ---- | ---- | ------ |
| 1 | EN + pt-BR `docs/PRICING.md` from `FEATURE_TIER_MAP` (Community / Pro / Enterprise columns; other bands footnoted) | ✅ Done |
| 2 | Cross-link README, AUDIENCE_GUIDE (CFO trail), SUBSCRIPTION_TIERS | ✅ Done this PR |
| 3 | Hub sync + PLANS_TODO row | ✅ Done this PR |
| 4 | When `FEATURE_TIER_MAP` changes, update PRICING in the same PR | 🔄 Ongoing |

## Out of scope

- Hardcoded prices, discounts, or partner commissions
- Inventing keys (JSONL report, OIDC) that are not in the map
