# Plan: Governance Lens — GRC translation layer (Pro / Enterprise)

<!-- plans-hub-summary: Camada de tradução GRC: mapeia padrões detectados para controles COBIT 2019 / ISO 27001 / ISO 27014 / ISO 38500 / ITIL 4; gera Governance View no Excel e exporta MD→DOCX/PDF via pandoc; Pro tier. -->
<!-- plans-hub-related: PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md, PLAN_CLI_VALIDATE_DIFF_AND_DSAR_EXPORT.md, LICENSING_SPEC.md -->

- **Status:** In progress (Phase D — operator docs USAGE/TECH_GUIDE + pandoc quickstart)
- **Date:** 2026-08-18
- **Authors:** Fabio Leitao (operator); Cursor executor
- **Priority:** H2
- **Milestone:** [v1.8.0](https://github.com/DataBoar/data-boar/milestone/2)
- **GitHub:** [#539](https://github.com/DataBoar/data-boar/issues/539) (Phase A) · [#540](https://github.com/DataBoar/data-boar/issues/540)–[#543](https://github.com/DataBoar/data-boar/issues/543) (Phases B–E)

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md) · [ISSUE_QUEUE_SEQUENCING_MAP.md](../ops/ISSUE_QUEUE_SEQUENCING_MAP.md)

**Licensing:** [docs/LICENSING_SPEC.md](../LICENSING_SPEC.md) — Pro+ feature; curated framework maps are **not** Open Core.

---

## Problem

Data Boar findings already expose **technical** signals (`pattern_detected`, `norm_tag`, sensitivity, source metadata). DPOs, CISOs, auditors, and boards need a **third dimension**: which **governance control** the finding implies, in language they can act on — without pretending the product delivers legal advice.

Without a durable plan + schema anchor, Governance Lens becomes vaporware. **Phase A must land before Phases B–E.**

---

## Decision

Ship Governance Lens in **five phases** (A→E). Each phase is a thin, reviewable PR with explicit `Closes #N`. **Hard gate:** do **not** start [#540](https://github.com/DataBoar/data-boar/issues/540)–[#543](https://github.com/DataBoar/data-boar/issues/543) until **#539** is closed.

| Phase | Deliverable | Issue | Status |
| ----- | ----------- | ----- | ------ |
| **A** | This plan + `config/governance_framework_map.schema.yaml` (structure + illustrative examples only) | [#539](https://github.com/DataBoar/data-boar/issues/539) | ✅ Done |
| **B** | `report/governance_lens.py` — Pro-tier generator (Governance View sheet / hooks) | [#540](https://github.com/DataBoar/data-boar/issues/540) | ✅ Done |
| **C** | Pandoc-ready MD template + `pandoc` YAML + CLI `--governance-report` | [#541](https://github.com/DataBoar/data-boar/issues/541) | ✅ Done |
| **D** | Operator docs: USAGE EN + pt-BR, TECH_GUIDE, pandoc quickstart | [#542](https://github.com/DataBoar/data-boar/issues/542) | 🔄 In progress |
| **E** | Enterprise framework modules (BACEN, FEBRABAN, PCI-DSS v4.0) | [#543](https://github.com/DataBoar/data-boar/issues/543) | ⬜ Pending |

**Out of scope for Phase A:** runtime generator code, pandoc templates, USAGE prose, or Enterprise curated maps in public Git.

---

## Modelo de licenciamento

| Tier | Framework maps | Runtime behaviour |
| ---- | -------------- | ----------------- |
| **Community / Open Core** | **No** curated `governance_framework_map` bundles in OSS | Technical findings only (`pattern_detected`, `norm_tag`, recommendations sheet) |
| **Pro** | Curated **Tier 1** map (`governance_framework_map_pro.yaml` — **not** committed to public Git; distributed under commercial terms). OSS ships **`config/governance_framework_map_pro.example.yaml`** + `governance.map_file` for lab/tests. | Governance View in Excel + exports per Phases B–C |
| **Enterprise** | Adds **Tier 2** sectoral BR maps (`governance_framework_map_enterprise.yaml` — private) | Phase E modules; same generator pipeline as Pro |

The **schema** in `config/governance_framework_map.schema.yaml` is public (structure only). **Curated entries** are the commercial asset — never ship production mappings in `origin`.

JWT / `licensing.effective_tier` gating follows [LICENSING_SPEC.md](../LICENSING_SPEC.md) (`dashboard_rbac`, tier-gated exports).

---

## Frameworks Tier 1 (Pro)

| Framework | Example control IDs (illustrative) | Governance Lens use |
| --------- | ---------------------------------- | ------------------- |
| **LGPD** | Art. 6, 7, 46 (security measures) | Map PII patterns to accountability / security baselines for DPO narratives |
| **ISO/IEC 27001:2022** | A.5.34, A.8.11, A.8.12 | Information protection, data masking, DLP-style discovery evidence |
| **ISO/IEC 27014:2020** | Governance of information security | Board/CISO-facing control gap titles |
| **COBIT 2019** | APO13 (managed security), DSS05 (security services), MEA03 (monitoring) | IT governance vocabulary for findings |
| **ITIL 4** | Security management practice (SecMan) | Service-management phrasing for operational owners |
| **ISO/IEC 38500** | Evaluate / direct / monitor IT | Executive summary hooks for GRC committees |

Exact control IDs and Portuguese audit phrasing live in the **curated Pro map** (Phase B loader), not in this plan table.

---

## Frameworks Tier 2 (Enterprise)

| Framework | Scope | Notes |
| --------- | ----- | ----- |
| **BACEN Res. 4893/2021** | Financial institutions (BR) | Cybersecurity policy / incident / access themes |
| **FEBRABAN CPS 004 / Circular 3909** | Open finance / shared data (BR) | Consent and data-sharing control framing |
| **PCI-DSS v4.0** | Cardholder data environments | Req. 3 (protect stored account data), 4 (transmission), 10 (logging) |
| **ANS / ANEEL** | Regulated sectors (BR) | **Future** — placeholder in Enterprise roadmap (Phase E) |

---

## Phase A artefacts (this issue)

1. **`docs/plans/PLAN_GOVERNANCE_LENS.md`** (this file) — sequencing, licensing, framework tables.
2. **`config/governance_framework_map.schema.yaml`** — YAML shape + **three illustrative example entries** (synthetic pattern names only). Curated Pro/Enterprise files reference the same shape but stay off `origin`.

---

## Dependencies

- **Upstream:** findings pipeline, `norm_tag` / `pattern_detected`, Excel report writer (existing).
- **Related:** [completed/PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md](completed/PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md) (questionnaire POC — complementary GRC surface), [completed/PLAN_CLI_VALIDATE_DIFF_AND_DSAR_EXPORT.md](completed/PLAN_CLI_VALIDATE_DIFF_AND_DSAR_EXPORT.md) (CLI evidence exports).

---

## Acceptance (Phase A)

- [x] Plan file with hub comments, phase table A–E, licensing + framework tables
- [x] Schema YAML with structure comments + ≥3 illustrative examples
- [x] `plans_hub_sync --write` + PLANS_TODO row (same PR)
- [x] `check-all` green before merge

---

## Follow-ups (Phases B–E)

See issues [#540](https://github.com/DataBoar/data-boar/issues/540)–[#543](https://github.com/DataBoar/data-boar/issues/543). Refresh [ISSUE_QUEUE_SEQUENCING_MAP.md](../ops/ISSUE_QUEUE_SEQUENCING_MAP.md) when the chain closes.

### Acceptance (Phase C — #541)

- [x] `docs/templates/GRC_GOVERNANCE_LENS_REPORT.md.j2` + `report/governance_report.py`
- [x] `config/pandoc_governance.yaml` + `docs/templates/governance_reference.docx`
- [x] CLI `--governance-report [PATH]` (+ optional `--session`)
- [x] `tests/test_governance_report_template.py` (4 named tests + pandoc defaults guard)
- [x] `check-all` green before merge

### Acceptance (Phase D — #542)

- [x] `docs/USAGE.md` + `docs/USAGE.pt_BR.md` — Governance Lens (Pro) section + CLI `--governance-report`
- [x] `docs/TECH_GUIDE.md` + `docs/TECH_GUIDE.pt_BR.md` — architecture pipeline + schema/extension notes
- [x] `docs/ops/GOVERNANCE_LENS_QUICKSTART.md` + `.pt_BR.md` (≤2 A4 pages)
- [x] `docs/ops/README.md` quickstart table row
- [x] `plans_hub_sync --write` + plan phase table refresh
- [x] `check-all` green before merge

### Acceptance (Phase B — #540)

- [x] `report/governance_lens.py` + `config/governance_map_loader.py`
- [x] `config/governance_framework_map_pro.example.yaml` (≥10 Tier-1 entries; OSS starter — not the commercial curated file)
- [x] Excel sheet **Governance View** after Recommendations when `governance.enabled: true` + Pro license
- [x] Config keys `governance.enabled`, `governance.tier`, `governance.map_file`
- [x] `tests/test_governance_lens.py` (≥5 tests)
- [x] `check-all` green before merge
