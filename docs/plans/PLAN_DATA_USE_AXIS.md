# Plan: Optional Data-Use axis (purpose / finalidade)

<!-- plans-hub-summary: Hybrid slice 2 (#1071): optional Data-Use (purpose) axis for LGPD Art.6/7-style finalidade; internal model, default off. -->
<!-- plans-hub-related: PLAN_NORM_TAG_HIERARCHY_AND_DATA_SUBJECT.md, PLAN_TAXONOMY_AXES.md, PLAN_FIDESLANG_EXPORT_ADAPTER.md -->

**Status:** Pending
**Date:** 2026-06-30
**Authors:** Fabio Leitao
**Priority:** H2 · candidate **v1.9.x** (slice **2 of 3** — hybrid #1071)
**Tags:** taxonomy, data-use, purpose, finalidade, LGPD, DPO-facing
**GitHub evaluation:** [#1071](https://github.com/FabioLeitao/data-boar/issues/1071) (closed — hybrid approved)
**GitHub implementation:** [#1075](https://github.com/FabioLeitao/data-boar/issues/1075)
**Depends on (soft):** [PLAN_NORM_TAG_HIERARCHY_AND_DATA_SUBJECT.md](PLAN_NORM_TAG_HIERARCHY_AND_DATA_SUBJECT.md) slice 1 shipped or parallel only if shared config loader is stable

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md), [PLAN_TAXONOMY_AXES.md](PLAN_TAXONOMY_AXES.md)

---

## Motivation

**Evaluation [#1071](https://github.com/FabioLeitao/data-boar/issues/1071):** Fideslang’s **Data Use** axis models **purpose / finalidade** (GDPR lawful basis class, LGPD Art. 6 bases and Art. 7 consent where applicable). Bearer and current Data Boar **do not** classify findings by **why** data is processed — only **what** (`norm_tag`) and (after slice 1) **whose** (Data-Subject).

**Hybrid slice 2** adds an **optional**, **operator-configured** Data-Use label on findings — **heuristic**, derived from table/column naming, config overrides, or future connector metadata — **not** automated legal basis determination.

---

## Design principles

1. **Default off** — entire `data_use` config block omitted = no change to legacy output.
2. **Additive fields** — e.g. `data_use`, `data_use_rule_id`; absent = legacy consumers unaffected.
3. **Internal vocabulary first** — BR/LGPD-oriented purpose labels (e.g. `employment_admin`, `customer_contract`, `health_care`, `marketing_consent`) defined in config; not hard-coded statute text.
4. **No ethyca-fides / fideslang runtime** — naming may **align** with Fideslang Data Use ids in docs for slice 3 export mapping only.
5. **Product disclaimer** — technical mapping for inventory/RoPA **support**, not legal advice.

---

## Config sketch (draft)

```yaml
data_use:
  enabled: false
  rules:
    - id: payroll_processing
      match:
        schema_regex: "(?i)^(hr|folha|payroll)"
      use: employment_admin
    - id: crm_sales
      match:
        table_regex: "(?i)(lead|prospect|crm)"
      use: customer_relationship
  default: unspecified
```

**Future:** link rules to `norm_tag` / `data_subject` conjunction; APG suggested actions in [PLAN_ACTION_PLAN_GENERATOR_POST_SCAN.md](PLAN_ACTION_PLAN_GENERATOR_POST_SCAN.md).

---

## Phases

| Phase | Deliverable | Status |
| ----- | ----------- | ------ |
| 0 | Plan + impl issue (#1071 slice 2) | ✅ Done |
| 1 | Config + loader validation + rule-matching tests | ⬜ Pending |
| 2 | Scan pipeline attaches optional `data_use*` on findings | ⬜ Pending |
| 3 | Persistence + export surfaces (opt-in) | ⬜ Pending |
| 4 | USAGE + pt-BR; taxonomy axes doc update | ⬜ Pending |

---

## Non-goals

- Automated DPIA or consent registry integration (future connectors).
- Replacing RoPA modules in customer GRC tools.
- Slice 3 Fideslang export (separate plan).

---

## Acceptance

- [ ] Feature off → byte-identical finding JSON vs baseline fixtures
- [ ] Feature on → distinct `data_use` for payroll vs CRM fixtures
- [ ] Disclaimers in USAGE; no “legal basis guaranteed” copy

---

## Audit trail

- **2026-06-30:** #1071 hybrid approved; slice 2 plan opened.
