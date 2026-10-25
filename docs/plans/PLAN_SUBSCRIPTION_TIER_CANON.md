# Plan: Canonical subscription-band doc (no public prices)

**Status:** Active
**Date:** 2026-08-26
**Authors:** Fabio Leitao
**Priority:** H2
**Depends on:** [PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md](PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md)

<!-- plans-hub-summary: Escada canônica de 6 faixas em SUBSCRIPTION_TIERS — sem página pública de preços -->
<!-- plans-hub-related: PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md -->

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md) · GitHub [#610](https://github.com/DataBoar/data-boar/issues/610)

## Purpose

Keep **one** public/internal-facing ladder in `docs/SUBSCRIPTION_TIERS.md` (+ pt-BR) matching `FEATURE_TIER_MAP` / `_TIER_ORDER` (Community → Std → Pro → Pro+ → Enterprise → Partner). This is **not** a public pricing page: no `PRICING.md`, no site promise, no amounts. Quotes and estate-franchise evaluation stay in gitignored `docs/private/`. Issue #610’s Community/Pro/Enterprise-only sketch is **closed as rescoped delivered** (six-band ladder in `docs/SUBSCRIPTION_TIERS.md`; no public pricing page).

`Tier.OPEN` is enforcement-off (dev/CI), never a seventh SKU.

## Sequential to-dos

| Step | Task | Status |
| ---- | ---- | ------ |
| 1 | Delete public `docs/PRICING.md` (+ pt-BR); no README/AUDIENCE links to a pricing filename | ✅ Done |
| 2 | Fold JWT aliases + FEATURE_TIER_MAP groups into `SUBSCRIPTION_TIERS.md`; other licensing docs **point**, do not restate the ladder | ✅ Done |
| 3 | Hub sync + PLANS_TODO row (plan renamed away from PRICING) | ✅ Done |
| 4 | When `FEATURE_TIER_MAP` / `_TIER_ORDER` / `map_dbtier_string_to_tier` change, update **SUBSCRIPTION_TIERS** in the same PR | 🔄 Ongoing |

## Out of scope

- Hardcoded prices, discounts, partner commissions, volume/franchise SKUs
- Inventing keys (JSONL report, OIDC) that are not in the map
- Advertising evaluation-only commercial program names on a public pricing surface
