# PLAN: CMMC / CUI discovery sample (US defense supply chain)

<!-- plans-hub-summary: Config-only CMMC/CUI inventory sample — markings, dissemination controls, ITAR/EAR triage signals; overclaim-safe evidence posture; NIS2/DORA/AI-Act positioned as evidence not samples. -->
<!-- plans-hub-related: PLAN_COMPLIANCE_EXPANSION_GLOBAL_JURISDICTIONS.md, PLAN_FERPA_AND_EDTECH_COMPLIANCE.md, PLAN_YAML_PLUGIN_SYSTEM.md -->

Status: Active
Date: 2026-08-05
Authors: Fabio Leitao
Priority: H1
Tags: compliance, cmmc, cui, itar, ear, defense, usa, inventory, overclaim-safe
Depends on: —
GitHub: [#1453](https://github.com/DataBoar/data-boar/issues/1453)

---

## Motivation

US defense industrial base buyers need **Controlled Unclassified Information (CUI)** discovery as data discovery. **CMMC** programmes depend on correct CUI handling; Data Boar can supply **inventory and triage signals** (markings, categories, dissemination controls, export-control vocabulary) without becoming an assessment engine.

**NIS2**, **DORA**, and the **EU AI Act** are cybersecurity / ICT resilience / AI-governance frameworks — **evidence-supported**, not `compliance-sample-*.yaml` packs (category mismatch / overclaim risk).

---

## Goals

- Ship `docs/compliance-samples/compliance-sample-us_cmmc_cui.yaml` (regex + terms + recommendation_overrides).
- Link from `COMPLIANCE_FRAMEWORKS` (+ pt-BR), compliance-samples README (+ pt-BR), and a short `COMPLIANCE_AND_LEGAL` (+ pt-BR) paragraph.
- Document NIS2 / DORA / EU AI Act as **evidence, not samples**.
- Keep wording overclaim-safe: **supports CMMC evidence / CUI discovery**; does **not** certify CMMC, assess a CMMC level, or determine ITAR/EAR applicability.
- Do **not** add a certification claim to `docs/CLAIMS.yml`.

---

## Phase 1 — YAML + docs (this issue)

| Step | Deliverable | Status |
| ---- | ----------- | ------ |
| 1 | `compliance-sample-us_cmmc_cui.yaml` with contextual regex (no bare `\bCUI\b`), ~40–80 terms, norm_tags `CMMC CUI` + `ITAR/EAR` | ✅ |
| 2 | `COMPLIANCE_FRAMEWORKS.md` (+ pt-BR) table row + cyber/AI evidence subsection | ✅ |
| 3 | `compliance-samples/README.md` (+ pt-BR) table row | ✅ |
| 4 | `COMPLIANCE_AND_LEGAL.md` (+ pt-BR) short US CMMC/CUI paragraph | ✅ |
| 5 | This plan + `plans_hub_sync.py --write` + `PLANS_TODO` entry | ✅ |
| 6 | Local gates (`test_compliance_samples`, locale, lint/check-all) + signed PR `Closes #1453` | ✅ |

---

## Out of scope

- CMMC level scoring, C3PAO assessment automation, ITAR/EAR legal classification.
- YAML samples for NIS2, DORA, or EU AI Act.
- Changes to `docs/CLAIMS.yml` headline claims.

---

## References

- Issue [#1453](https://github.com/DataBoar/data-boar/issues/1453)
- [ADR 0025](../adr/ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md) — evidence and inventory, not a legal-conclusion engine
- [COMPLIANCE_FRAMEWORKS.md](../COMPLIANCE_FRAMEWORKS.md#cyber-ai-governance-evidence-not-samples)
