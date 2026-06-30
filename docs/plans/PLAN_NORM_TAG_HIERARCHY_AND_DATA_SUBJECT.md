# Plan: Hierarchical norm_tag + configurable Data-Subject axis

<!-- plans-hub-summary: Hybrid slice 1 (#1071): parent→child norm_tag inheritance preserving BR/LGPD vocabulary + optional Data-Subject axis; closes #1069 titular gap. -->
<!-- plans-hub-related: PLAN_TAXONOMY_AXES.md, PLAN_SUBJECT_CATEGORY_AXIS.md, PLAN_DATA_USE_AXIS.md, PLAN_FIDESLANG_EXPORT_ADAPTER.md -->

**Status:** Pending
**Date:** 2026-06-30
**Authors:** Fabio Leitao
**Priority:** H2 · candidate **v1.9.0** (slice **1 of 3** — hybrid #1071)
**Tags:** detection, taxonomy, norm_tag, hierarchy, data-subject, LGPD, BR-vocabulary
**GitHub evaluation:** [#1071](https://github.com/FabioLeitao/data-boar/issues/1071) (closed — hybrid approved)
**GitHub audit (titular gap):** [#1069](https://github.com/FabioLeitao/data-boar/issues/1069) (closed)
**GitHub implementation:** [#1074](https://github.com/FabioLeitao/data-boar/issues/1074)
**Supersedes narrow track:** [#1072](https://github.com/FabioLeitao/data-boar/issues/1072) + [PLAN_SUBJECT_CATEGORY_AXIS.md](PLAN_SUBJECT_CATEGORY_AXIS.md) (Bearer-only subject mapping absorbed here)

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md), [PLAN_TAXONOMY_AXES.md](PLAN_TAXONOMY_AXES.md)

---

## Motivation

**Evaluation [#1071](https://github.com/FabioLeitao/data-boar/issues/1071)** (RO-verified, not re-done here): Data Boar’s **BR/LGPD vocabulary** (CPF, CNPJ, NIS/PIS, PEP, Mod-11 checks) **exceeds** generic industry taxonomies. **Hybrid decision:** internal model (**Direction B**) preserves depth; Fideslang interop stays **export-only** (slice 3).

**Slice 1** delivers the **highest-value** gap closure from **#1069**: optional **Data-Subject** axis (employee / customer / patient / minor / …) **plus** **hierarchical `norm_tag`** (parent category → subcategory with inheritance), without lossy collapse of BR-specific tags.

---

## Design principles

1. **Default off** — no hierarchy or subject axis unless config enables it.
2. **Backward compatible** — flat `norm_tag` strings and legacy findings unchanged when disabled; optional additive fields only when enabled.
3. **Preserve BR moat** — internal tags stay granular (`LGPD_CPF`, `LGPD_CNPJ`, …); hierarchy is **composition**, not replacement by generic `user.government_id`.
4. **Orthogonal axes** — Data-Subject complements type (`norm_tag`); does not overload sensitivity or gravity **G**.
5. **Heuristic only** — no legal conclusions; DPO-facing disclaimers like `jurisdiction_hints` (ADR 0026 class).

---

## Hierarchical norm_tag (internal)

**Concept:** `norm_tag` may encode `parent.child` or explicit `parent` + `norm_tag_leaf` fields (implementation choice in Phase 1 design).

| Parent (example) | Child examples (BR-preserved) |
| ---------------- | ----------------------------- |
| `government_id` | `LGPD_CPF`, `LGPD_CNPJ`, `NIS_PIS` |
| `contact` | `phone`, `email` |
| `financial` | `account_number`, `card_number` |

**Inheritance rules (draft):**

- Child inherits parent’s compliance-sample hooks and recommendation templates unless overridden.
- Reports may **roll up** to parent for executive view while retaining leaf in detail export.
- Existing flat tags remain valid leaf nodes (no forced migration).

---

## Data-Subject axis (configurable)

Same intent as Bearer `subject_mapping` and Fideslang **Data Subject** concept — **internal labels**, config-driven:

```yaml
data_subject:
  enabled: false
  rules:
    - id: hr_employee
      match:
        schema_regex: "(?i)^(hr|rh|payroll)"
      subject: employee
    - id: crm_customer
      match:
        table_regex: "(?i)(customer|cliente)"
      subject: customer
  default: unknown
```

**Additive finding fields (when enabled):** `data_subject`, `data_subject_rule_id` (names TBD in impl).

---

## Phases

| Phase | Deliverable | Status |
| ----- | ----------- | ------ |
| 0 | Plan + impl issue; supersede #1072 narrow track | ✅ Done |
| 1 | Config schema + loader; hierarchy resolution + subject rules unit tests | ⬜ Pending |
| 2 | Detector/scan pipeline: optional hierarchy fields + `data_subject*` on findings | ⬜ Pending |
| 3 | SQLite + `_ensure_*` migration; legacy DB bootstrap tests | ⬜ Pending |
| 4 | Report/Excel/JSON export (opt-in columns; rollup + leaf) | ⬜ Pending |
| 5 | USAGE + pt-BR; update [PLAN_TAXONOMY_AXES.md](PLAN_TAXONOMY_AXES.md) | ⬜ Pending |

---

## Non-goals (this slice)

- **Data-Use / purpose** — [PLAN_DATA_USE_AXIS.md](PLAN_DATA_USE_AXIS.md) (slice 2).
- **Fideslang `data_category` export** — [PLAN_FIDESLANG_EXPORT_ADAPTER.md](PLAN_FIDESLANG_EXPORT_ADAPTER.md) (slice 3).
- **ethyca-fides** platform or **`fideslang`** PyPI dependency.

---

## Acceptance

- [ ] Disabled config → identical behaviour to pre-change scans
- [ ] Enabled: HR vs CRM fixture shows same leaf `norm_tag`, different `data_subject`
- [ ] CPF/CNPJ remain distinct leaf tags under hierarchy (no lossy merge)
- [ ] Plan checkboxes updated in implementation PR

---

## Audit trail

- **2026-06-30:** #1071 hybrid approved; slice 1 plan opened; supersedes Bearer-only [PLAN_SUBJECT_CATEGORY_AXIS.md](PLAN_SUBJECT_CATEGORY_AXIS.md) / #1072.
