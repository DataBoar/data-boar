# PLAN: Pro / plugin artifact auditability

<!-- plans-hub-summary: Thin backlog for ADR-0090 G1 layers (SBOM+provenance, NDA review) + pointers to G2 sample and G3 reverse-guard child issues; docs/ADR first, no gate code in #811. -->

**Status:** Active (documentation / backlog)
**Date:** 2026-08-17
**Priority:** H1
**Issue:** [#811](https://github.com/DataBoar/data-boar/issues/811)
**ADR:** [ADR-0090](../adr/ADR-0090-open-core-plugin-boundary-pro-auditability-reference-sample.md)

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md) · [PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md](PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md) · [PLAN_YAML_PLUGIN_SYSTEM.md](PLAN_YAML_PLUGIN_SYSTEM.md)

---

## Purpose

Operational backlog for **artifact auditability** of Pro/plugin engines (ADR-0090 **G1**), distinct from scan **Audit Trail**.

Does **not** implement reverse-guard code (G3) or the public sample plugin (G2) in the #811 docs slice.

---

## Phases

| Phase | Scope | Status |
| ----- | ----- | ------ |
| 0 | ADR-0090 Proposed + this plan + cross-links (#811) | 🔄 Tracked (this PR) |
| 1 | Document operator/customer playbook for **layer A** (SBOM + signed provenance) — public ops pointers only; no secrets | ⬜ Pending |
| 2 | Private NDA / clean-room checklist under `docs/private/` for **layer B** | ⬜ Pending |
| 3 | Optional **layer C** third-party attestation vendor notes (private) | ⬜ Pending |
| G2 | Public reference sample plugin + CI contract canary (ADR-0090 G2) | ⬜ Pending (follow-up issue) |
| G3 | Reverse Pro→public leakage gate (pre-commit/CI) | ⬜ Pending ([#1624](https://github.com/DataBoar/data-boar/issues/1624)) |

---

## Related

- [#769](https://github.com/DataBoar/data-boar/issues/769) · [#784](https://github.com/DataBoar/data-boar/issues/784) · [#785](https://github.com/DataBoar/data-boar/issues/785) · [#865](https://github.com/DataBoar/data-boar/issues/865)
- [ADR 0003](../adr/ADR-0003-sbom-roadmap-cyclonedx-then-syft.md) · [ADR 0086](../adr/ADR-0086-plugin-sdk-language-neutral-contract.md)
