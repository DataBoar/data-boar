# Plan: Optional subject category axis (data-subject / titular category)

<!-- plans-hub-summary: Optional configurable subject-category axis (Bearer-style subject_mapping) complementing norm_tag; audit #1069 gap; candidate v1.9.0. -->
<!-- plans-hub-related: PLAN_TAXONOMY_AXES.md, PLAN_COMPLIANCE_EXPANSION_GLOBAL_JURISDICTIONS.md, PLAN_ADDITIONAL_DETECTION_TECHNIQUES_AND_FN_REDUCTION.md -->

**Status:** Pending
**Date:** 2026-06-30
**Authors:** Fabio Leitao
**Priority:** H2 · candidate **v1.9.0**
**Tags:** detection, taxonomy, LGPD, norm_tag, subject-mapping, DPO-facing
**GitHub audit:** [#1069](https://github.com/FabioLeitao/data-boar/issues/1069) (closed — gap confirmed, no code)
**GitHub implementation:** [#1072](https://github.com/FabioLeitao/data-boar/issues/1072)
**Related evaluation:** [#1071](https://github.com/FabioLeitao/data-boar/issues/1071) (Fideslang / IAB Tech Lab taxonomy — strategic input, not a runtime dependency)

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md), [PLAN_TAXONOMY_AXES.md](PLAN_TAXONOMY_AXES.md)

---

## Motivation

External privacy-SAST tooling (Bearer-class) separates **data type** (phone, email, national ID) from **data-subject category** (employee, customer, patient, minor) via operator-configurable mapping files. Data Boar today classifies findings primarily on **type** (`norm_tag`) and **sensitivity** — not on **whose** data the column or field likely represents in context.

**Audit conclusion ([#1069](https://github.com/FabioLeitao/data-boar/issues/1069), RO-verified):** `SensitivityDetector.analyze()` returns `(sensitivity_level, pattern_detected, norm_tag, confidence)` with **no titular/subject dimension**. Table/schema/column context does not feed a subject category. The `data_subject` field in DSAR export is the **requester** of a DSAR (GDPR Art. 15 sense), not a finding-classification axis.

**Why it matters (LGPD-oriented example, not legal advice):** The same `norm_tag` (e.g. phone) in an HR table vs a customer table vs a health context can imply **different compliance narratives** (employment law, consumer relationship, health-sector rules, **Art. 14** minors). Today both phones receive **identical severity** when only type is scored — a gap a technical DPO/CISO reviewer can defend.

This plan adds an **optional**, **configurable** subject-category axis **alongside** `norm_tag`, without breaking existing finding schema or reports for operators who leave it disabled.

---

## Relationship to other plans

| Plan / issue | Relationship |
| ------------ | ------------ |
| [PLAN_TAXONOMY_AXES.md](PLAN_TAXONOMY_AXES.md) | New **orthogonal axis** (subject category vs type vs gravity **G**); document in taxonomy map when shipped. |
| [#1071](https://github.com/FabioLeitao/data-boar/issues/1071) | Strategic eval: Fideslang **Data Subject** / **Data Use** interop vs in-house hierarchy — **input before Phase 2 naming**, not a platform dependency. |
| [PLAN_ADDITIONAL_DETECTION_TECHNIQUES_AND_FN_REDUCTION.md](PLAN_ADDITIONAL_DETECTION_TECHNIQUES_AND_FN_REDUCTION.md) | Complementary; subject axis does not replace FN reduction engines. |
| [PLAN_ACTION_PLAN_GENERATOR_POST_SCAN.md](PLAN_ACTION_PLAN_GENERATOR_POST_SCAN.md) | Future APG tiers may reference subject category in suggested actions (later phase). |
| **#1069 Frente 2** (`--report=security\|privacy\|dataflow`) | **Out of scope** — Markdown-centric `data-boar-report` is an **enhancement**, not this plan; defer unless operator opens a reporter plan. |

---

## Design principles

1. **Default off:** No subject category unless `subject_mapping` (name TBD) is enabled and configured.
2. **Additive schema:** New fields are **optional** on findings / SQLite / export paths; absent fields mean legacy behaviour.
3. **Complement `norm_tag`:** Never replace or overload `norm_tag`; subject category is a **second axis**.
4. **Configurable, not hard-coded law:** Categories are **operator-defined labels** mapped from schema/table/column patterns — product does not emit legal conclusions.
5. **Evidence, not verdict:** Store **which rule matched** (pattern id, source table name redacted per policy) for audit trail; label output **heuristic**.
6. **No Bearer / Go dependency:** Inspiration only; YAML/JSON config native to Data Boar loader conventions.

---

## Proposed config sketch (draft — not validated by loader)

```yaml
# Optional root block — entire section omitted = feature disabled.
subject_mapping:
  enabled: false
  # Ordered rules: first match wins (deterministic).
  rules:
    - id: hr_employee_context
      match:
        schema_regex: "(?i)^(hr|rh|payroll|folha)"
        table_regex: "(?i)(employee|funcionario|staff)"
      subject_category: employee
    - id: crm_customer_context
      match:
        table_regex: "(?i)(customer|cliente|account)"
      subject_category: customer
    - id: health_patient_context
      match:
        schema_regex: "(?i)(clinical|paciente|ehr)"
      subject_category: patient
  default_subject_category: unknown  # or omit column when no rule matches
```

**Future:** optional `column_regex`, connector tags, or `norm_tag` conjunction — only after Phase 1 proves value.

---

## Proposed finding fields (additive)

| Field | Type | When present |
| ----- | ---- | ------------ |
| `subject_category` | string (operator label) | Rule matched and feature enabled |
| `subject_category_rule_id` | string | Same |
| `subject_category_confidence` | float 0–1 optional | If heuristic tiering is added |

Existing consumers that ignore unknown keys continue to work. Excel/Markdown report columns: **opt-in** new sheet rows or columns with disclaimer row.

---

## Phases

| Phase | Deliverable | Status |
| ----- | ----------- | ------ |
| 0 | **This plan** + PLANS_TODO row + impl issue (audit closure **#1069**) | ✅ Done |
| 1 | Config schema + loader validation; unit tests for rule matching on synthetic table names | ⬜ Pending |
| 2 | Wire `SensitivityDetector` / scan pipeline to attach optional `subject_category*` on findings when enabled | ⬜ Pending |
| 3 | SQLite persistence + backward-compatible migration (`_ensure_*` if new columns) | ⬜ Pending |
| 4 | Report / Excel / optional JSON export surfaces + USAGE disclaimer (heuristic, not legal advice) | ⬜ Pending |
| 5 | Dashboard opt-in column (if applicable) + operator-help manifest sync | ⬜ Pending |
| 6 | Reconcile naming with **#1071** eval (Fideslang interop field vs internal enum) — doc + config only unless operator chooses external ids | ⬜ Pending |

---

## Non-goals

- **Data Use / purpose** axis (finalidade LGPD Art. 6/7) — see **#1071**; separate future plan if pursued.
- **Automatic legal regime mapping** (CLT vs CFM vs Art. 14) — documentation may **cite** examples; product emits **category label** only.
- **Reporter multi-lens CLI** (`--report=privacy|security|…`) — tracked as defer from **#1069** Frente 2.
- Adopting **ethyca/fides** platform or runtime dependency.

---

## Risks

| Risk | Mitigation |
| ---- | ---------- |
| False subject assignment from weak table names | Default off; require explicit rules; `unknown` bucket; DPO review copy |
| Schema creep | Optional fields only; migration tests for legacy DBs |
| Overclaim in marketing | Same disclaimer pattern as `jurisdiction_hints` (ADR 0026 class) |

---

## Acceptance (implementation issue)

- [ ] Feature disabled by default; enabling without rules fails closed or no-ops per loader policy
- [ ] Golden-path scan on fixture DB shows distinct `subject_category` for HR vs CRM tables with same `norm_tag`
- [ ] Existing tests / exports unchanged when block omitted
- [ ] USAGE + pt-BR sync; no legal-advice wording
- [ ] Plan phase table updated in same PR as code

---

## Audit trail

- **2026-06-30:** RO audit on **#1069** confirmed Frente 1 gap; operator promoted to this plan (candidate **v1.9.0**). Frente 2 deferred (Markdown-centric reporter).
