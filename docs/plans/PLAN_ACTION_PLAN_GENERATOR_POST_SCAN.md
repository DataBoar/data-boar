# Plan: Action Plan Generator (APG) — post-scan accountability and remediation hints

**Status:** Deferred
**Date:** 2026-04-26
**Authors:** Fabio Leitao
**Priority:** H1

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md) (*Integration / active threads*), [ADR 0025](../adr/ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md) (evidence positioning), [PLAN_SQL_SAMPLING_SRE_AND_AUDIT_EVIDENCE.md](completed/PLAN_SQL_SAMPLING_SRE_AND_AUDIT_EVIDENCE.md) (Slice 4 — coverage / confidence metadata), [PLAN_PDF_GRC_REPORT.md](PLAN_PDF_GRC_REPORT.md) (executive PDF narrative), [PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md](PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md) (audit trail / tamper posture)

<!-- plans-hub-summary: Post-scan Action Plan Generator: triage tiers, suggested mitigations, optional JSON/SQL snippets and evidence log—evidence for diligence, not legal conclusions. -->
<!-- plans-hub-related: PLAN_SYNTHETIC_DATA_AND_CONFIDENCE_VALIDATION.md, completed/PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md, ../REPORTS_AND_COMPLIANCE_OUTPUTS.md -->

## Purpose

Mid-market buyers need **accountability**: moving from “we did not know” to **documented discovery + proportionate next steps**. The APG turns technical findings into a **structured remediation narrative** the DPO/CISO can attach to internal risk registers—while the product stays an **inventory and evidence** tool, not a legal conclusion engine ([ADR 0025](../adr/ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md)).

## PoC framing — “semáforo” + suggested actions (illustrative)

| Band | Example signal (heuristic) | Example suggested direction (non-binding) |
| ---- | ---------------------------- | ---------------------------------------- |
| **Critical (red)** | High-sensitivity categories (e.g. national ID, payment card, health-adjacent labels) in log-like tables or wide unscoped samples | Prioritise **purge / anonymisation / access restriction** with counsel; cite finding location and sampling depth |
| **Alert (amber)** | Sensitive hints in non-prod paths (naming heuristics, connector labels) | **Masking / obfuscation** in CI/CD and test data lifecycle; separate prod from lower environments |
| **Monitor (green)** | Production-scoped findings with strong controls narrative missing | **Access logging / audit trail** on named objects; periodic re-scan policy |

Copy is always **suggested**; operators choose actions under their own legal and IT governance.

## Deliverables (phased)

| Phase | Deliverable | Notes |
| ----- | ----------- | ----- |
| **A — Schema + report hooks** | Machine-readable **action rows** linked to finding keys (target, table, column, category, band, suggested_action_id, disclaimer_version) | Extends Excel / JSON export paths; reuses recommendation patterns where they exist (`report/` / `utils/report_gen.py` mitigation helpers) |
| **B — “Exposure diagnosis” narrative** | One-page **human summary** + optional **PDF executive stub** | Align vocabulary with [PLAN_PDF_GRC_REPORT.md](PLAN_PDF_GRC_REPORT.md); no new legal claims—**evidence + proportionality** language only |
| **C — Remediation snippets** | Optional **`remediation_snippets.json`** (or sheet) with **parameterised** SQL / masking examples (e.g. email mask pattern) | Snippets are **templates**; DBAs must review dialect, locks, and change windows—tagged as such |
| **D — Audit evidence log** | Immutable-enough **scan manifest**: who ran, config hash, time window, recommendation set version | Bridges to **`--export-audit-trail`**, `/status`, and [PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md](PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md) SQLite anchor work—single story for “we ran Data Boar on date X” |

## Product guardrails (non-negotiable)

1. **No fine math** — the product does not predict regulatory penalties or “pedagogical vs breaking” fines.
2. **No auto-remediation** — no destructive SQL or writes from the scanner; snippets are **export-only** until a separate operator-approved workflow exists.
3. **Confidence honesty** — tie “95% / 90%” style claims to **measurable coverage** (targets scanned, sample depth vs estimates, skipped columns)—see SQL sampling plan **Slice 4** and synthetic-data confidence plan for shared vocabulary.

## Open questions (before coding)

- Which **finding taxonomy** keys are stable enough to map to `suggested_action_id` (norm_tag, sensitivity, connector type)?
- **Locale**: EN-first strings in code; pt-BR in paired docs per [docs-policy](../README.md).
- **Tier**: open-core vs Pro packaging for PDF / JSON bundle (align with [PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md](PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md) when scoped).
