# Plan: Post-scan remediation plugin interface (Enterprise)

<!-- plans-hub-summary: Enterprise remediation bridge — #649 manifest + #606 hook + #1443 JSONL; v1.8.0 #1057 maps anonymizer/policy classes onto existing plugin contract; Phase 2 FPE samples and Phase 3 verify still open -->
<!-- plans-hub-related: PLAN_PLUGIN_SDK.md, PLAN_PLUGIN_PARTNER_INTERFACE.md, PLAN_ACTION_PLAN_GENERATOR_POST_SCAN.md -->

**Status:** Active (bridge on `main`; v1.8.0 survey [#1057](https://github.com/DataBoar/data-boar/issues/1057) enriches this plan — do not archive)
**Date:** 2026-05-19 (v1.8.0 wave: 2026-08-27)
**Authors:** Fabio Leitao
**Priority:** H1
**Milestone:** v1.8.0

**GitHub:** [#601](https://github.com/DataBoar/data-boar/issues/601) · [#606](https://github.com/DataBoar/data-boar/issues/606) · [#649](https://github.com/DataBoar/data-boar/issues/649) · [#1057](https://github.com/DataBoar/data-boar/issues/1057) (v1.8.x anonymizer / policy enrichment)

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)

**Related:** [USE_CASE_SCAN_AND_REMEDIATE.md](../use-cases/USE_CASE_SCAN_AND_REMEDIATE.md), [USE_CASE_TOKENIZED_FINDINGS.md](../use-cases/USE_CASE_TOKENIZED_FINDINGS.md), [PLAN_G_TIER.md](PLAN_G_TIER.md), [PLAN_PLUGIN_SDK.md](PLAN_PLUGIN_SDK.md) (partner guide **#611**), [PLAN_PLUGIN_PARTNER_INTERFACE.md](PLAN_PLUGIN_PARTNER_INTERFACE.md) (L1/L2/L3 + L3 schemas — **#695**), [PLAN_ACTION_PLAN_GENERATOR_POST_SCAN.md](PLAN_ACTION_PLAN_GENERATOR_POST_SCAN.md) (suggested actions — not auto-write)

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
| **1 – Remediation manifest export** | CLI `--export-remediation-manifest` + schema v1 JSON (bridge for third-party plugins) | ✅ **#649** |
| **1b – Hook skeleton** | Minimal plugin registry + host hook (`RemediationPlugin` / ADR-0059) | ✅ **#606** |
| **2 – Export path** | Host findings JSONL before plugin (`findings_{session_id}.jsonl`, #649 taxonomy) | ✅ **#1443** (host write); ⬜ FPE / tokenized samples |
| **3 – Re-scan job** | Scoped verify after plugin run | ⬜ |

---

## Non-goals (phase 0–1)

- Shipping a proprietary HSM or vault product inside core.
- Replacing counsel on lawful basis for biometric or payment data.

---

## Acceptance (plan)

- [x] Use-case docs published under `docs/use-cases/`
- [x] Remediation manifest JSON export (`--session` + `--export-remediation-manifest`) — **#649**
- [x] Plugin interface ADR — [ADR-0059](../adr/ADR-0059-remediation-plugin-architecture.md) (revise on phases 2–3)
- [x] Code hook merged per **#606** (PR links when opened)

---

## v1.8.0 wave — anonymizer / policy enrichment ([#1057](https://github.com/DataBoar/data-boar/issues/1057))

**Driver:** Landscape survey (private competitive dossier). **Docs-first** in this PR; code slices stay on the existing Enterprise plugin path. Data Boar does **not** ship a built-in anonymizer, HSM, or in-place rewriter.

**Non-claims (align with [COMPLIANCE_AND_LEGAL.md](../COMPLIANCE_AND_LEGAL.md) and [ADR 0025](../adr/ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md)):** Scan reports, `norm_tag` values, and `report.recommendation_overrides` are **inventory and technical-mapping aids** — not legal advice, not a determination that a field must be anonymized under LGPD/GDPR, and **not** an ANPD (or other authority) seal. Partner plugins that tokenize or mask data do so under **customer policy and counsel**; the host only exports **metadata** (`pii_type`, `suggested_profile`, locations).

### What already ships (do not invent a second contract)

| Surface | Role today | Policy relevance |
| ------- | ---------- | ---------------- |
| `--export-remediation-manifest` (**#649**) | JSON map of locations + `pii_type` + `suggested_profile` (`core/remediation_manifest.py`) | Plugin chooses mask / tokenize / encrypt **from these hints** — no raw samples |
| `RemediationPlugin` hook (**#606** / ADR-0059) | In-process Enterprise callback after report | Partner IP executes; host fail-graceful |
| Host findings JSONL (**#1443**) | Same taxonomy as the manifest, written before the plugin | Input coordinates only |
| Excel / YAML `recommendation_overrides` | Wording in reports from `docs/compliance-samples/compliance-sample-*.yaml` | Suggests **direction** (restrict, mask, review) — does **not** mutate sources |
| [PLAN_ACTION_PLAN_GENERATOR_POST_SCAN.md](PLAN_ACTION_PLAN_GENERATOR_POST_SCAN.md) | Optional **suggested** action narrative | Orthogonal: APG does **not** auto-remediate |

### Policy classes (buyer language → existing plugin actions)

Competitive “anonymizer” SKUs usually bundle several **treatments**. Map them onto [PLUGIN_SDK.md](../PLUGIN_SDK.md) use cases — **partner implements**; core stays discovery + evidence.

| Policy class | Typical buyer ask | Product hook (no new engine) | Sample / override path |
| ------------ | ----------------- | ---------------------------- | ---------------------- |
| **Mask / redact** | Hide PAN, email local-part, or national ID in copies | SDK **Masking** (overwrite or staged copy) | `recommendation_overrides` bullets in PCI / LGPD samples |
| **Tokenize / FPE** | Keep format for downstream validators | SDK **FPE tokenization** via partner vault; Phase **2** still ⬜ for tokenized **samples** in host export | [USE_CASE_TOKENIZED_FINDINGS.md](../use-cases/USE_CASE_TOKENIZED_FINDINGS.md) |
| **Irreversible anonymize** | One-way transform where policy forbids reversal | Partner action log only; **not** a core hash-anonymizer | Counsel decides lawful basis; do not claim “anonymized dataset” from a scan |
| **Field encryption** | Ciphertext at rest in named columns | SDK **Field encryption** | Manifest `suggested_profile` (e.g. `TGCPF`, `TGPAN`) selects vault profile |
| **Notify / ticket** | ITSM from finding coordinates | SDK **Notification** | Operational convenience — not legal notice |

`suggested_profile` tokens already in code (`TGCPF`, `TGCNPJ`, `TGEMAIL`, `TGPAN`, …, `TGGENERIC`) are **plugin-facing hints**, not a completeness claim for every `pattern_detected` label.

### Compliance-sample methodology (mandatory for policy wording)

Same discipline as detection packs — **do not** add a second anonymizer YAML dialect:

1. Keep `regex:` / ML terms in existing `docs/compliance-samples/compliance-sample-*.yaml` files; `norm_tag` is a **framework label**, not a legal conclusion.
2. Merge `recommendation_overrides` into operator `report.recommendation_overrides` so Excel language matches internal policy (mask vs tokenize vs “review with DPO”).
3. File headers already require counsel review before production patterns.
4. Optional later stub `compliance-sample-remediation_hints.yaml` would carry **only** override bullets + disclaimers (no new detectors) — **not** in this docs PR.
5. Host never writes customer tables. Snippets and plugins are **opt-in** and operator-approved ([PLAN_ACTION_PLAN_GENERATOR_POST_SCAN.md](PLAN_ACTION_PLAN_GENERATOR_POST_SCAN.md) guardrails).

### Execution table (doc-first → later slices)

| Step | Deliverable | Status |
| ---- | ----------- | ------ |
| P1 | This plan section + hub summary + `PLANS_TODO` survey rows | ✅ Done (docs PR) |
| P2 | Optional `docs/compliance-samples/` hints pack: `recommendation_overrides` keyed by pattern → suggested plugin action id + header disclaimers | ⬜ Pending |
| P3 | [PLUGIN_SDK.md](../PLUGIN_SDK.md) (+ pt-BR): short `suggested_profile` vocabulary table (mirrors `core/remediation_manifest.py`) | ⬜ Pending |
| P4 | Phase 2 — tokenized / FPE **samples** on the host export path (still partner-executed) | ⬜ Pending (existing phase table) |
| P5 | Phase 3 — scoped re-scan verify after plugin | ⬜ Pending (existing phase table) |

### Revisit (completed / sibling plans — survey notes only)

- [PLAN_ACTION_PLAN_GENERATOR_POST_SCAN.md](PLAN_ACTION_PLAN_GENERATOR_POST_SCAN.md): keep **suggested** actions; do **not** fold auto-SQL into this plugin plan.
- [PLAN_PLUGIN_PARTNER_INTERFACE.md](PLAN_PLUGIN_PARTNER_INTERFACE.md) / epic **[#865](https://github.com/DataBoar/data-boar/issues/865)**: L2/L3 isolation remains the trust-boundary follow-up — not a substitute for policy mapping here.
