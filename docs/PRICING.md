# Feature and quantity map by commercial band

**Português (Brasil):** [PRICING.pt_BR.md](PRICING.pt_BR.md)

This page is **not** a price list. Amounts, discounts, partner commissions, and franchise quotes stay off the public tree (`docs/private/`). Contact **contact@databoar.com.br**.

The GitHub issue that asked for **only** Community / Pro / Enterprise is **out of date**. The live product ladder is Community → Std → Pro → Pro+ → Enterprise → Partner / white-label (SKU), plus lab Open (enforcement off). **Trial** JWT strings currently map to **Pro** in code.

## Two axes (do not collapse)

| Axis | Question | Public sources |
| ---- | -------- | -------------- |
| **Capability (tier)** | What can this deployment do? | `Tier` + `FEATURE_TIER_MAP` in `core/licensing/tier_features.py`; JWT `dbtier` mapped in `core/licensing/runtime_feature_tier.py` |
| **Quantity (franchise)** | How much concurrency, how many sites, how large a governed estate? | Implemented: `dbmax_workers`, `dbmax_deployments` ([LICENSING_SPEC.md](LICENSING_SPEC.md), [SUBSCRIPTION_TIERS.md](SUBSCRIPTION_TIERS.md)). **Estate-size franchises** (logical active scope, not bytes-read-per-scan) are **under commercial evaluation** and are **not** `FEATURE_TIER_MAP` keys. Raising volume **must not** silently promote Pro → Pro+ / Enterprise. |

GTM narrative (RBAC story, SIEM/RoPA packs, worker table): [SUBSCRIPTION_TIERS.md](SUBSCRIPTION_TIERS.md). Policy draft: [LICENSING_OPEN_CORE_AND_COMMERCIAL.md](LICENSING_OPEN_CORE_AND_COMMERCIAL.md). How to run: [USAGE.md](USAGE.md).

Default CI/dev is `licensing.mode: open` (all capability keys on). Gates apply in `enforced` mode. Additive compare uses `_TIER_ORDER` in `tier_features.py`.

## JWT / lab aliases (code)

| Band | Typical `dbtier` / `effective_tier` strings |
| ---- | ------------------------------------------- |
| Community | `community`, `oss`, `open_core` |
| Std (Boar-Std — not Oracle Database Standard Edition) | `std`, `standard`, `boar_std`, `boar-std` |
| Pro | `pro`, `professional`, `consultant`; **`trial` maps here** |
| Pro+ | `pro_plus`, `pro+`, `proplus` |
| Enterprise | `enterprise`, `ent` |
| Partner / white-label SKU | `partner`, `partner_custom`, `whitelabel`, `white_label` → enum **`partner`** |
| Open (lab) | empty / open mode — not a paid SKU |

Unknown strings fail closed to **Community** when mapped.

## Capability groups

A cell is **Yes** when that band’s enum is **≥** the feature’s minimum in `_TIER_ORDER`. **Std** has **no extra feature keys** (same Community capability set; commercial right is licence/claims, not a map key). **Partner** sits **above Enterprise** in that order, so a Partner token currently receives **all** mapped keys (including Enterprise). White-label is an **alias of Partner**, not a seventh enum.

| Capability group | Community | Std | Pro | Pro+ | Ent | Partner / WL |
| ---------------- | :-------: | :-: | :-: | :--: | :-: | :----------: |
| Filesystem; self-hosted SQL/NoSQL; generic REST/API; core detectors; compressed files; content-type; synthetic testing; XLSX/HTML; REST API; dashBOARd; Docker/Ansible keys | Yes | Yes | Yes | Yes | Yes | Yes |
| OCR; PDF report; compliance-grade report; scheduled scans; dashboard RBAC; API-key UI; maturity POC; notifications; SBOM; build-integrity; SQL findings sink; Pro governance lens; managed/corporate connectors | — | — | Yes | Yes | Yes | Yes |
| `pro_prefilter_accel`; `rust_regex_stage` | — | — | — | Yes | Yes | Yes |
| Custom PDF branding; Ent scheduler UI; Ent governance lens; multi-tenant; **SSO SAML**; PDF digital signature; scheduled PDF email; historical comparison; audit-log export; custom detectors; VCS connector; plugin/partner interface; partner provider driver; remediation plugin/manifest | — | — | — | — | Yes | Yes |

**Not in `FEATURE_TIER_MAP`:** JSONL report key; OIDC/LDAP SSO (named in SUBSCRIPTION_TIERS as **intent**); dedicated-support SLAs.

## Quantity franchises (evaluation vs shipped)

Shipped quantity claims (not prices): Community workers **2** · Pro **4** · Pro+ **8** (claim) · Enterprise **unlimited** entitlement; Pro default **2** licensed production sites — see [SUBSCRIPTION_TIERS.md](SUBSCRIPTION_TIERS.md). `dbmax_targets` remains a planned claim.

**Volume / data-estate franchises** (included base allotment + add-on packs, true-up rather than kill-switch) are being **priced privately**. Public docs will not list amounts or pack SKUs until product+legal freeze them. Inventory of estate **size** can still be a product feature without being a bill.

## Catalyst / Supporter (evaluation)

**Catalyst** and **Supporter** are **commercial program names under evaluation**. They are **not** values in `map_dbtier_string_to_tier` today. Do not treat them as extra `FEATURE_TIER_MAP` bands until issuance and docs are updated together.

## Contact

**contact@databoar.com.br** or a GitHub issue. This page is not a quote.

## Drift

When `FEATURE_TIER_MAP`, `_TIER_ORDER`, or `map_dbtier_string_to_tier` change, update this page in the same PR.
