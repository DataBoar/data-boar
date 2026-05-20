# Plan: Post-scan remediation plugin interface (Enterprise)

<!-- plans-hub-summary: Enterprise hook for third-party tokenization, masking, and field crypto after discovery -->

**Status:** Active
**Date:** 2026-05-19
**Authors:** Fabio Leitao
**Priority:** H1

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md) · GitHub **#601** · **#606**

**Related:** [USE_CASE_SCAN_AND_REMEDIATE.md](../use-cases/USE_CASE_SCAN_AND_REMEDIATE.md), [USE_CASE_TOKENIZED_FINDINGS.md](../use-cases/USE_CASE_TOKENIZED_FINDINGS.md), [PLAN_G_TIER.md](PLAN_G_TIER.md)

---

## Problem

Open-core **discovery** and **reporting** ship today; **remediation** (tokenize, mask, encrypt in place) is partner-specific. Without a **stable plugin contract**, every integration forks core paths and breaks audit narrative.

---

## Goal

Define an **Enterprise-tier** post-scan hook that:

1. Receives a **structured findings map** (location + `pii_type` + stable finding id).
1. Invokes a **registered third-party plugin** (tokenization, masking, pseudonymization, field encryption).
1. Supports **re-scan verification** and **audit trail** fields documented in use cases.

**IP model:** tokenizer/remediator stays **third-party**; Data Boar owns discovery, orchestration, and evidence export.

---

## Phases

| Phase | Deliverable | Status |
| ----- | ----------- | ------ |
| **0 – Docs** | Use cases + this plan | 🔄 In progress (**#602–605**, **#601**) |
| **1 – Hook skeleton** | Minimal plugin registry + no-op driver | ⬜ **#606** |
| **2 – Export path** | Tokenized findings JSONL option | ⬜ |
| **3 – Re-scan job** | Scoped verify after plugin run | ⬜ |

---

## Non-goals (phase 0–1)

- Shipping a proprietary HSM or vault product inside core.
- Replacing counsel on lawful basis for biometric or payment data.

---

## Acceptance (plan)

- [x] Use-case docs published under `docs/use-cases/`
- [ ] Plugin interface ADR when shape stabilises
- [ ] Code hook merged per **#606**
