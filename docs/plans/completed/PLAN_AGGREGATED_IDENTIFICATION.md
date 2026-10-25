# Plan: Cross-referenced and aggregated data – identification risk

**Português (Brasil):** [SENSITIVITY_DETECTION.pt_BR.md](SENSITIVITY_DETECTION.pt_BR.md) (overview and configuration examples for this feature).

## Goal

Cross information from **multiple data sources or columns** (e.g. gender, job position, health information, address, phone number) that, **in aggregate**, can lead to **identifying individuals**, even when no single column is direct PII. Treat such aggregated results as **personal and/or sensitive** when the combination makes sense, and inform the DPO, security, and compliance teams as a **special case**, explaining the **cross-reference from multiple sources** so they can assess re-identification and linkage risk.

## Principles (non-destructive, no regression)

- **Additive only:** New logic is optional (config or automatic); existing findings and report layout remain valid.
- **No performance regression:** Aggregation runs after the normal scan (post-processing over existing findings); optional and configurable.
- **No raw content storage:** Only metadata (which columns/sources were combined, categories involved).
- **Tests:** New code paths covered by tests; existing tests must still pass.

---

## Approach (high level)

1. **Quasi-identifier categories**

   Define categories that, when combined, can support identification or re-identification, e.g.:

   - **Gender** (column names or patterns suggesting gender/sex)
   - **Job position** (role, department, title, occupation)
   - **Health** (health-related columns or patterns)
   - **Address** (address, city, postal code, location)
   - **Phone** (phone number, contact)
   - **Other:** age range, education, membership, etc.

   Map **column names** and **pattern_detected** to these categories via config (e.g. `detection.quasi_identifier_mapping`) or built-in heuristics (keywords in column name + pattern type).

1. **Aggregation scope**

   Group findings by **logical unit**:

   - **Database:** by (session_id, target_name, schema_name, table_name). Collect all columns (and their categories) for that table.
   - **Filesystem:** by (session_id, target_name, file_name) or by path; collect patterns/columns found in that file.
   - **Cross-target (optional):** If the same session scans multiple targets (e.g. DB + files), optionally consider “same record” across sources (e.g. same identifier in different systems). Phase 1 can be **per-table / per-file** only; cross-target in a later phase.

1. **Identification risk rule**

   For each group (e.g. one table), compute the set of **categories** present. If the set has **at least N** categories (e.g. N = 2 or 3), or contains a **sensitive combination** (e.g. health + gender + job), then:

   - Treat the **aggregate** as **personal/sensitive** for reporting.
   - Record: target, table/file, list of columns/categories involved, short **explanation** (e.g. “Gender, job position and health information present in same table – possible identification of individuals”).

1. **Storage**

   Either:

   - **Option A:** Synthetic finding row(s) in existing tables with e.g. `pattern_detected = "AGGREGATED_IDENTIFICATION"`, `norm_tag` = “Cross-referenced data – LGPD/GDPR”, and a new optional field or JSON in an existing column describing `columns_involved` / `categories`.
   - **Option B:** New table or sheet **“Aggregated identification risk”** with columns: session_id, target_name, table_name (or file_name), columns_involved, categories, explanation, sensitivity_level.

   Recommendation: **Option B** (dedicated structure) so the report can clearly separate “single-column findings” from “aggregated/cross-referenced” and explain the multi-source condition.

1. **Report**
   - Add a **recommendation** and/or **dedicated sheet/section** “Cross-referenced data – possible identification” (or “Dados agregados – possível identificação”).
   - For each aggregated case: list **target, table/file, columns (or categories) involved**, and **explanation** (e.g. “Combination of gender, job position and health information in the same table may allow identification of individuals. Consider access controls and purpose limitation.”).
   - Mark as **special case** for DPO/compliance (e.g. priority ALTA/CRÍTICA when health or other sensitive categories are in the combination).
   - Use **recommendation_overrides** (existing) where possible to add norm_tag for “AGGREGATED_IDENTIFICATION” so Base legal and Recomendação explain the cross-reference condition.

1. **Config**

   Optional settings, e.g.:

   - `detection.aggregated_identification_enabled` (default true).
   - `detection.aggregated_min_categories` (default 2): minimum number of quasi-identifier categories in a group to flag.
   - `detection.quasi_identifier_mapping`: list of { column_pattern, category } or { pattern_detected, category } to map columns/findings to gender, job_position, health, address, phone, etc.
   - Built-in defaults: map common column names (e.g. “gender”, “sex”, “cargo”, “department”, “health”, “address”, “phone”, “telefone”) and pattern_detected (e.g. PHONE_BR, DATE_*) to categories.

---

## Design decisions (implemented)

- **Scope:** Per-table (database) and per-file (filesystem). Group DB findings by (session_id, target_name, schema_name, table_name); FS findings by (session_id, target_name, path, file_name). Cross-target linkage is out of scope for this phase.
- **Storage:** Option B – dedicated table `aggregated_identification_risk` with session_id, target_name, source_type, table_or_file, columns_involved (text), categories (text), explanation (text), sensitivity_level. Created via SQLAlchemy and `Base.metadata.create_all`; no separate migration script.
- **Categories:** gender, job_position, health, address, phone, other. Mapping from column names and pattern_detected via config (`quasi_identifier_mapping`) plus built-in defaults (e.g. gender/sex/cargo/department/health/address/phone/telefone and patterns PHONE_BR, EMAIL, etc.).
- **When aggregation runs:** At report generation time: report generator loads findings, runs aggregation when `detection.aggregated_identification_enabled` is true, writes results to the aggregated table, then adds the “Cross-referenced data – possible identification” sheet and recommendation row from those results.

---

## Sequential to-dos

Execute in order; each step should be tested and non-regressing before the next.

| #   | To-do                                                                                                                                                                                                                      | Status |
| --- | ---                                                                                                                                                                                                                        | ---    |
| 1   | **Design & doc:** Finalize quasi-identifier categories, aggregation scope (per-table/per-file first), and storage (new table vs synthetic finding); document in this file.                                                 | ✅ Done |
| 2   | **Category mapping:** Implement mapping from column_name and pattern_detected to categories (gender, job_position, health, address, phone, etc.); config + built-in defaults.                                              | ✅ Done |
| 3   | **Schema (optional):** Add table or structure for “aggregated identification risk” (session_id, target, table/file, columns_involved, categories, explanation) or reuse findings with a dedicated pattern/norm_tag.        | ✅ Done |
| 4   | **Post-scan aggregation:** After scan, for each (session, target, table) or (session, target, file), collect categories; if count >= threshold or sensitive combination, create aggregated record and store.               | ✅ Done |
| 5   | **Report – sheet/section:** Add sheet or section “Cross-referenced data – possible identification” listing each case with target, table/file, columns/categories, and explanation (cross-reference from multiple sources). | ✅ Done |
| 6   | **Report – recommendation:** Add recommendation row for aggregated identification (or use recommendation_overrides for norm_tag) with priority and text explaining the multi-source condition for DPO/compliance.          | ✅ Done |
| 7   | **Config:** Add detection.aggregated_identification_enabled, aggregated_min_categories, quasi_identifier_mapping in config loader.                                                                                         | ✅ Done |
| 8   | **Tests:** Unit tests for category mapping, aggregation rule, and report output; full test suite passes.                                                                                                                   | ✅ Done |
| 9   | **Docs:** Update sensitivity-detection and compliance docs (EN and PT-BR) to describe aggregated/cross-referenced identification and the special case for DPO/compliance.                                                  | ✅ Done |

---

## Configuration and usage (examples)

All options live under **`detection`** in your main config file (e.g. `config.yaml`).

| Key                                           | Type    | Default  | Description                                                                                                                                                                                                               |
| ---                                           | ---     | ---      | ---                                                                                                                                                                                                                       |
| `detection.aggregated_identification_enabled` | boolean | **true** | Turn aggregation and the "Cross-ref data – ident. risk" sheet on/off.                                                                                                                                                     |
| `detection.aggregated_min_categories`         | integer | **2**    | Minimum number of quasi-identifier categories in a table/file to create an aggregated record.                                                                                                                             |
| `detection.quasi_identifier_mapping`          | list    | **[]**   | Optional mappings: `{ "column_pattern": "cargo", "category": "job_position" }` or `{ "pattern_detected": "PHONE_BR", "category": "phone" }`. Categories: `gender`, `job_position`, `health`, `address`, `phone`, `other`. |

## Example: custom mapping and stricter threshold

```yaml
detection:
  aggregated_identification_enabled: true
  aggregated_min_categories: 3
  quasi_identifier_mapping:

    - column_pattern: "cargo"

      category: job_position

    - column_pattern: "departamento"

      category: job_position

    - pattern_detected: "PHONE_BR"

      category: phone
```

**How to run:** Use the same workflow as for any audit: run a scan (CLI or API), then generate/open the report. Aggregation runs **at report generation time**. If the scan found multiple columns in the same table (or file) that map to at least `aggregated_min_categories` categories, the report will include the sheet **"Cross-ref data – ident. risk"** and an **AGGREGATED_IDENTIFICATION** recommendation.

---

## References

- LGPD Art. 5 (personal data), Art. 11 (sensitive personal data); re-identification and linkage.
- GDPR Recital 26 (identifiability; single pieces vs combination of data).
- Existing: database_findings (table_name, column_name, pattern_detected, norm_tag); filesystem_findings (file_name, pattern_detected); report/generator.py (Recommendations, sheets).
- recommendation_overrides: can add norm_tag_pattern "AGGREGATED_IDENTIFICATION" (or similar) for Base legal and Recomendação text explaining cross-reference.

---

## This plan is additive and aims to avoid breaking existing behaviour or performance.
