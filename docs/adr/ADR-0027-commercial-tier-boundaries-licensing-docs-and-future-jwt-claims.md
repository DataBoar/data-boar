# ADR 0027 — Commercial tier boundaries — licensing docs and future JWT claims

- **Status:** Accepted
- **Date (UTC):** 2026-04-17
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Status

Accepted

### Status history

- 2026-04-17 — Accepted
- 2026-06-21 — Amended: Watch condition fulfilled by [ADR 0064](ADR-0064-license-enforcement-additive-model.md) (Proposed) — GitHub #993 / #709

## Context

The product needs a **single, reviewable place** for **open core vs Pro vs Enterprise** positioning: scale (workers, targets), **deployments per license**, **federated** groups (branch silos with shared CISO but local P&L), and **JWT-shaped** controls for when enforcement ships. Without documenting this, sales and engineering drift apart; naming **real employers** in **public** docs violates repository privacy policy, so **concrete buyer examples** stay in **`docs/private/`**.

| Option | Pros | Cons |
| --- | --- | --- |
| **Extend `LICENSING_OPEN_CORE_AND_COMMERCIAL.md` + `LICENSING_SPEC.md` (chosen)** | One hub for operators and counsel; illustrative claims (`dbmax_workers`, `dbmax_deployments`, …) without implementing gates yet | Docs must stay in sync when product enforcement lands |
| Only private notes | No PII risk in public tree | Contributors and future you cannot rely on a canonical tracked policy |

## Decision

1. **Track** the working model in **`docs/LICENSING_OPEN_CORE_AND_COMMERCIAL.md`** (EN + **`.pt_BR.md`**): Pro vs Enterprise, **open-core** worker/target caps, **deployments per license**, **federated** branch pattern, **multi-Pro** at one site (e.g. cloud vs on-prem), **Enterprise** for group-wide coverage.
2. **Track** illustrative **JWT** claims and multi-site verification options in **`docs/LICENSING_SPEC.md`** (`dbmax_workers`, `dbmax_targets`, `dbmax_deployments`, `dbdeployment_pack_id`, multi-fingerprint strategies) — **not** implemented in runtime until contracts and `LicenseGuard` work are scheduled.
3. **Place concrete named examples** (specific companies, sites, terminals) only under **`docs/private/`**, not in `origin` / GitHub-facing Markdown.
4. **Defer** runtime enforcement, issuer UX, and pricing to **product + counsel**; this ADR records **documentation architecture** only.

## Consequences

- **Positive:** Sales, integrators, and future enforcement work share one **narrative**; ADR links **why** the public docs grew.
- **Negative:** Public licensing docs are longer; must be updated when tier semantics change.
- **Watch:** ~~When JWT claims go live, **revalidate** table rows and remove “illustrative” wording where behaviour is fixed.~~ **Fulfilled (2026-06-21):** runtime enforcement architecture is [ADR 0064](ADR-0064-license-enforcement-additive-model.md) (Proposed); signing algorithm [ADR 0063](ADR-0063-ed25519-license-jwt-signing.md). Public licensing docs must still track implementation drift until ADR-0064 is **Accepted** and shipped.

## Related Decisions

- [ADR 0063 — ed25519 license JWT signing](ADR-0063-ed25519-license-jwt-signing.md)
- [ADR 0064 — License enforcement additive model](ADR-0064-license-enforcement-additive-model.md) — fulfills this ADR’s deferred enforcement Watch
- [ADR 0066 — TAMPERED state behavior (fail-closed in enforced mode)](ADR-0066-tampered-state-behavior.md) — caps effective runtime tier at Community when integrity checks fail under **enforced** licensing; open mode logs CRITICAL and continues

## References

- [`docs/LICENSING_OPEN_CORE_AND_COMMERCIAL.md`](../LICENSING_OPEN_CORE_AND_COMMERCIAL.md) · [pt-BR](../LICENSING_OPEN_CORE_AND_COMMERCIAL.pt_BR.md)
- [`docs/LICENSING_SPEC.md`](../LICENSING_SPEC.md)
- [`docs/plans/PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md`](../plans/PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md) (plain-text path in licensing doc — internal planning)
- Private example note: `docs/private/commercial/LICENSING_TIER_EXAMPLE_FEDERATED_OPERATOR.pt_BR.md` (operator-only; not on `origin`)
