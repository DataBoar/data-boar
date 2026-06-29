# Plan: Extended sensitive discovery positioning (clinical adjacency, IP, security artifacts)

**Status:** Active (wave 1 shipped; **v1.8.0 wave 2** [#1056](https://github.com/FabioLeitao/data-boar/issues/1056))
**Date:** 2026-04-13 (wave 2: 2026-06-21)
**Authors:** Fabio Leitao
**Priority:** H2
**Milestone:** v1.8.0
**GitHub:** [#1056](https://github.com/FabioLeitao/data-boar/issues/1056)

<!-- plans-hub-summary: Buyer/DPO positioning for clinical adjacency, IP, and security artifacts; wave 2 adds explicit entity taxonomy (SWIFT, IBAN, VIN, MAC, CVV, AWS keys, PIN) tied to #1056. -->
<!-- plans-hub-related: PLAN_ADDITIONAL_DETECTION_TECHNIQUES_AND_FN_REDUCTION.md, PLAN_YAML_PLUGIN_SYSTEM.md -->

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)

## Purpose

Position how Data Boar can support **discovery and mapping** of additional classes of sensitive “ingredients” that buyers ask about in conversation:

- **Clinical / health-record semantics** (national health systems, longitudinal records, forms—often discussed alongside HIPAA-style health data).
- **Intellectual property** indicators (trade names, patents, marks—column names and content hints, not legal title determination).
- **Security artifacts** (credentials, API keys, tokens, PEM material—distinct from **log redaction** in the application, which only masks secrets in operational logs).

This plan describes **technical capability** (config + optional consulting). It does **not** assert compliance with a specific statute named by acronym in chat (e.g. a particular “DRS” rule set); **legal classification remains with the organisation, DPO, and counsel.**

## How the product already supports this

| Need | Mechanism | Notes |
| --- | --- | --- |
| Broader health/clinical lexicon | `ml_patterns_file` / `dl_patterns_file`, inline `sensitivity_detection.*_terms`, [sensitivity_terms_sensitive_categories.example.yaml](../sensitivity_terms_sensitive_categories.example.yaml) | Additive; tune per tenant. |
| PCI-style card data | Built-in patterns + [compliance-sample-pci_dss.yaml](../compliance-samples/compliance-sample-pci_dss.yaml) | Already documented. |
| IP-ish column/content hints | ML/DL terms + optional narrow `regex` overrides | Expect false positives; scope with consulting. |
| Secrets / tokens in **scanned data** | `regex_overrides` (e.g. JWT, AWS key shapes, PEM headers) + ML terms (“api_key”, “client_secret”) | Distinct from `sanitize_log_text` / `redact_secrets_for_log` in `core/validation.py` (logging and SQLite failure-row hygiene only). |
| Report language | `report.recommendation_overrides` | Align wording to internal policy without forking code. |

## Professional services fit

Scoping **targets**, prioritising **pattern sets**, and reducing **noise** for IP and SEC-style findings usually benefits from **joint work** (same framing as [COMPLIANCE_AND_LEGAL.md](../COMPLIANCE_AND_LEGAL.md) — Professional services). Deliverables are **configuration artefacts** and runbooks, not a legal opinion.

## Scope

| Track | In scope | Out of scope |
| --- | --- | --- |
| **This wave** | Subsection in COMPLIANCE_AND_LEGAL (EN + pt-BR); light cross-reference in COMPLIANCE_FRAMEWORKS; this plan; PLANS_TODO row | Code changes, new connectors |
| **Optional later** | Curated `compliance-sample-*` profiles for “secrets-heavy” or “IP lexicon” starter packs | Exhaustive secret scanning parity with dedicated SAST/DAST tools |

## v1.8.0 wave 2 — entity taxonomy and secrets alignment ([#1056](https://github.com/FabioLeitao/data-boar/issues/1056))

**Driver:** Competitive landscape survey (private dossier). Complements detection implementation in [PLAN_ADDITIONAL_DETECTION_TECHNIQUES_AND_FN_REDUCTION.md](PLAN_ADDITIONAL_DETECTION_TECHNIQUES_AND_FN_REDUCTION.md) — this wave stays **positioning + sample sketch**, not a claim to replace dedicated secret scanners or SAST tools.

**Disclaimer (same bar as [COMPLIANCE_AND_LEGAL.md](../COMPLIANCE_AND_LEGAL.md)):** Findings are **heuristic inventory** for DPO and engineering review. `norm_tag` labels framework **context** for reports; they are **not** legal advice and do not prove that a matched token is regulated personal data in your jurisdiction.

### Entity-types table (buyer language → product hook)

| Buyer asks about | Product hook (wave 2) | Sample / override path |
| ---------------- | --------------------- | ---------------------- |
| Bank routing / SWIFT | `SWIFT_BIC` pattern name | `compliance-sample-global_identifiers.yaml` (planned) or financial sector pack |
| IBAN | `IBAN_*` + mod-97 gate when implemented | EU/GDPR samples + global identifiers pack |
| Vehicle VIN | `VIN` pattern | Motor/insurance lexicon in ML terms + regex |
| Device MAC | `MAC_ADDRESS` | Security-artifact section; high FP — document in SENSITIVITY_DETECTION |
| Card CVV / expiry (not PAN) | `CARD_CVV`, `CARD_EXPIRY` | [compliance-sample-pci_dss.yaml](../compliance-samples/compliance-sample-pci_dss.yaml) — keep **separate** from PAN/Luhn |
| Cloud keys (AWS AKIA / secret shapes) | Extend secrets row in table below | Built-in PII guard tests already cover AKIA shapes; detector parity in #1056 code slice |
| PIN / short auth codes | `PIN` with strict context | PCI sample + checksum/context gate — expect FP without gate |

### Security artifacts row (unchanged intent, richer taxonomy)

| Artifact class | Example pattern names | Scanned-data vs logs |
| -------------- | --------------------- | -------------------- |
| Cloud API keys | `AWS_ACCESS_KEY`, `AWS_SECRET_KEY` shape | Scanned content via regex overrides; **not** `sanitize_log_text` |
| Tokens | JWT, Bearer, OAuth client secrets | ML terms + regex; recommend rotation in `recommendation_overrides` |
| PEM / private key material | `PEM_PRIVATE_KEY` header | High severity in report; operator merge overrides |
| Network | MAC, optional internal host placeholders | Asset inventory framing — no real hostnames in public samples |

### Wave 2 execution (doc-first)

| # | To-do | Status |
| - | ----- | ------ |
| W2.1 | This section + cross-link #1056 execution table in PLAN_ADDITIONAL | ✅ Done (docs PR) |
| W2.2 | Optional `compliance-sample-global_identifiers.yaml` stub (regex + disclaimers + recommendation_overrides) | ⬜ Pending |
| W2.3 | COMPLIANCE_FRAMEWORKS one-line pointer (no overclaim) when sample lands | ⬜ Pending |
| W2.4 | Code: built-in/override patterns + checksum validators per PLAN_ADDITIONAL D3–D7 | ⬜ Pending |

### ML/DL taxonomy enrichment (revisit — no reopen by default)

When #1056 code ships, consider additive terms in [sensitivity_terms_sensitive_categories.example.yaml](../sensitivity_terms_sensitive_categories.example.yaml) for categories such as `FINANCIAL_ID`, `VEHICLE_ID`, `NETWORK_ID`. Historical plan: [PLAN_SENSITIVE_CATEGORIES_ML_DL.md](completed/PLAN_SENSITIVE_CATEGORIES_ML_DL.md). Promote only if FN metrics from [PLAN_SYNTHETIC_DATA_AND_CONFIDENCE_VALIDATION.md](PLAN_SYNTHETIC_DATA_AND_CONFIDENCE_VALIDATION.md) justify.

---

## References

- [SENSITIVITY_DETECTION.md](../SENSITIVITY_DETECTION.md) · [COMPLIANCE_FRAMEWORKS.md](../COMPLIANCE_FRAMEWORKS.md)
- [PLAN_SENSITIVE_CATEGORIES_ML_DL.md](completed/PLAN_SENSITIVE_CATEGORIES_ML_DL.md) (historical; examples live under `docs/`)
- [PLAN_ADDITIONAL_DETECTION_TECHNIQUES_AND_FN_REDUCTION.md](PLAN_ADDITIONAL_DETECTION_TECHNIQUES_AND_FN_REDUCTION.md) — v1.8.0 #1056 implementation table
