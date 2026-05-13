# Plan: Extended sensitive discovery positioning (clinical adjacency, IP, security artifacts)

**Status:** Active
**Date:** 2026-04-13
**Authors:** Fabio Leitao
**Priority:** H2

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

## References

- [SENSITIVITY_DETECTION.md](../SENSITIVITY_DETECTION.md) · [COMPLIANCE_FRAMEWORKS.md](../COMPLIANCE_FRAMEWORKS.md)
- [PLAN_SENSITIVE_CATEGORIES_ML_DL.md](completed/PLAN_SENSITIVE_CATEGORIES_ML_DL.md) (historical; examples live under `docs/`)
