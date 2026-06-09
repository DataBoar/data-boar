# GRC executive report — JSON contract and risk matrix (design)

**Português (Brasil):** [GRC_EXECUTIVE_REPORT_SCHEMA.pt_BR.md](GRC_EXECUTIVE_REPORT_SCHEMA.pt_BR.md)

**Audience:** CISO, DPO, integrators building **dashboards** (React, Streamlit, etc.) or **PDF** generators (ReportLab, fpdf2, etc.) that must turn **Data Boar scan metadata** into **business-risk language** without pretending the product is a full enterprise GRC suite.

**See also:** [REPORTS_AND_COMPLIANCE_OUTPUTS.md](REPORTS_AND_COMPLIANCE_OUTPUTS.md) (what ships today), [COMPLIANCE_METHODOLOGY.md](COMPLIANCE_METHODOLOGY.md) (norm tags and triage), [COMPLIANCE_AND_LEGAL.md](COMPLIANCE_AND_LEGAL.md) (legal posture — not advice), [GLOSSARY.md](GLOSSARY.md) (**GRC**).

**Example file (placeholders only):** [../schemas/grc_executive_report.v1.example.json](../schemas/grc_executive_report.v1.example.json)

**Reference viewer (optional):** after ``uv sync --extra grc-dashboard``, run ``streamlit run app/dashboard.py`` from the repository root (override path with env ``DATA_BOAR_GRC_JSON``). Logic helpers live in ``app/grc_dashboard_model.py`` for tests and reuse without Streamlit.

---

## 1. Design goals

1. **Risk matrix, not only an error list:** each **detailed finding** row must carry **asset context**, **severity or risk score**, **PII categories** (counts, **never** raw values in this JSON), and **remediation priority** so executives see **exposure × asset criticality**.
2. **Audit-ready metadata:** stable **`report_id`**, UTC **`scan_date`**, **`scanner_version`**, and **scope** text that matches what was configured (targets, limits, jurisdiction hint when used).
3. **Dual consumer:** the same payload should feed **interactive UI** (drill-down) and **print/PDF** (fixed ordering, executive summary first).
4. **Non-authoritative compliance mapping:** `compliance_mapping` lists **candidate** articles or controls for **workshop** use; **counsel / DPO** decides applicability. The product does **not** auto-determine lawful basis.

---

## 2. Top-level JSON shape (contract `data_boar_grc_executive_report_v1`)

| Block | Purpose |
| ----- | ------- |
| **`schema_version`** | String, e.g. **`data_boar_grc_executive_report_v1`**. Bump only on breaking field renames or semantic changes. |
| **`report_metadata`** | Identity of the run: **`report_id`**, optional **`client_display_name`** (operator-supplied label; may be redacted in exports), **`scan_date`** (ISO-8601 UTC), **`scanner_version`** (app semver + optional build label), **`scope`** (human-readable summary of targets: DBs, paths, limits), optional **`session_id`** linking back to SQLite session rows. |
| **`executive_summary`** | Aggregates: **`total_records_scanned`** (or “cells inspected” / file count — define unit per implementation), **`pii_instances_found`** (metadata hits, not assumed unique persons), **`critical_assets_at_risk`** (count of assets above a configured threshold), **`compliance_score`** (0–100 **heuristic** — formula is product-defined and must be documented; **not** a legal adequacy score), **`risk_level`** enum such as `LOW` / `MEDIUM` / `HIGH` / `CRITICAL` derived from policy. |
| **`compliance_mapping`** | Lists such as **`lgpd_articles_hint`** / **`gdpr_articles_hint`** — short codes (e.g. `"LGPD:Art.46"`) derived from **norm tags** and methodology tables, with **`mapping_confidence`** optional per family. |
| **`detailed_findings`** | Array of **risk-matrix rows** (see §3). |
| **`recommendations`** | Prioritised actions: **`id`**, **`priority`** (e.g. P0–P3), **`action`**, **`estimated_effort`**, **`regulatory_impact_note`** (worded as **hypothesis** for DPO workshop, not a sanction prediction). |

Optional future blocks (non-breaking additions): **`data_lineage_notes`**, **`tooling_limits`**, **`operator_attestation`**, **`integrity_reference`** (hash of config + session). A shipped, **non-breaking** per-finding **`nist_csf_function_hint`** (plus the matching `compliance_mapping` disclaimer keys) is described in **§3.3**.

---

## 3. `detailed_findings[]` — risk matrix row

Each element should be sufficient for a **CISO one-pager row** and a **DPO triage queue**.

| Field | Type | Notes |
| ----- | ---- | ----- |
| **`asset_id`** | string | Stable slug: e.g. `db:<target>:<schema>.<table>`, `fs:<target>:<path-prefix>`, `api:<target>:<route-class>`. No secrets. |
| **`asset_class`** | string | e.g. `database_table`, `filesystem_tree`, `api_surface`. |
| **`data_category`** | string | `personal` (ordinary personal data), `sensitive` (LGPD Art. 11-style special categories when the pipeline classifies them), or `unknown`. Drives **stricter** `risk_score` weighting for `sensitive` in the reference consolidator (`report/grc_reporter.py`). |
| **`risk_score`** | number | 0–100: **final** score after category weighting (and any future tunables). Used for **`executive_summary`** aggregates (`compliance_score`, `risk_level`, critical-asset counts). |
| **`risk_score_input`** | number | Optional **transparency** field: raw numeric input before `data_category` adjustment (same as `risk_score` when no bump applies). Omit in minimal exporters if you need a slimmer payload; the Python `GRCReporter` currently **always** emits it. |
| **`impact_score`** | number | 0–100, **Impact** axis for board heatmaps. When not supplied by the engagement, `GRCReporter` derives a default from `risk_score` (see §3.1). |
| **`likelihood_score`** | number | 0–100, **Likelihood** axis. Same default derivation when absent. |
| **`heatmap_quadrant`** | string | One of `impact_high_likelihood_high`, `impact_high_likelihood_low`, `impact_low_likelihood_high`, `impact_low_likelihood_low` — threshold at **50** on each axis in the reference implementation (tune per engagement). |
| **`pii_types`** | array of objects | Each: **`type`** (CPF, EMAIL, …), **`count`**, **`exposure`** enum such as `Cleartext`, `Hashed`, `Unknown` — from detector + storage hints only. |
| **`location_summary`** | string | Column, file path pattern, or API field class — **metadata**. |
| **`violation_desc`** | string | **Technical** description (e.g. “high-density CPF-like tokens without field-level encryption signal in this scan configuration”). Avoid stating legal breach as fact. |
| **`norm_tags`** | array of strings | Pass-through from findings / config (see [COMPLIANCE_METHODOLOGY.md](COMPLIANCE_METHODOLOGY.md)). |
| **`nist_csf_function_hint`** | array of strings | **Optional, non-breaking.** Short **NIST CSF 2.0** codes (e.g. `"GV"`, `"ID.AM"`, `"PR.DS"`) derived from `norm_tags` via a **versioned shipped table** (`report/nist_csf_mapping.yaml`). **Heuristic hint, not a compliance determination** (see §3.3 and [ADR 0025](adr/ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md)). **Omitted** when no `norm_tag` maps — never an empty array. |
| **`remediation_priority`** | string | e.g. `CRITICAL` / `HIGH` / `MEDIUM` / `LOW` — mapped from **adjusted** `risk_score` and operator overrides. |
| **`regulatory_impact`** | string | **Business / legal workshop wording** for this row (e.g. candidate articles, administrative-risk framing). **Not** an automated legal conclusion; **counsel / DPO** must validate. Empty string is allowed when the integrator has no vetted sentence yet. |

**Context-sensitive severity (interpretation):** the same **`pii_types`** profile may imply **different** `risk_score` when **`asset_class`** is an append-only log versus an identity store — align with operator prompt guidance in [COMPLETAO_OPERATOR_PROMPT_LIBRARY.md](ops/COMPLETAO_OPERATOR_PROMPT_LIBRARY.md) (*Interpretation taxonomy*). Product implementers encode weights; analysts validate.

### 3.1 Heatmap (Impact × Likelihood) — default derivation

Dashboards can plot **`impact_score`** vs **`likelihood_score`** as a scatter or matrix. When the scan pipeline does not yet supply real control-maturity or exposure-window likelihood, **`GRCReporter.default_heatmap_axes_from_risk`** maps the consolidated **`risk_score`** to two 0–100 coordinates so every row is plottable. **Replace** these defaults with engagement-specific models when you have them (e.g. control tests, incident history).

**Quadrants:** the reference **`heatmap_quadrant`** uses a **50 / 50** split on each axis so CISOs can label “high–high” clusters quickly; adjust thresholds in code or config if your risk register uses different cut-offs.

### 3.2 LGPD-aligned **risk density** (optional row fields)

When the Python consolidator is called with **`lgpd_density=LgpdDensityRiskConfig(...)`** on `GRCReporter.add_finding` / `add_detailed_finding`, **`risk_score`** is derived from **`report.grc_risk_taxonomy`** instead of the caller-supplied scalar.

| Tier (taxonomy) | Typical `pii_types[].type` hints (substring match) | Per-unit weight | Workshop framing (non-binding) |
| ----- | ----- | -----: | ----- |
| **`identificadores`** | Name, e-mail, phone-like labels | **10** | Ordinary personal data (LGPD Art. 5, I — high-level framing). |
| **`financeiros_gov`** | CPF, CNH, bank/credit-card-like labels | **30** | Fraud / financial integrity and strong identifier signals. |
| **`sensitive`** | Health, biometrics, religion, politics, race/ethnicity-like labels | **80** | Special-category style rigour (LGPD Art. 5, II / Art. 11 — **verify** with counsel). |
| **`infantil`** | Minor / DOB-possible-minor / child-protection sample tags | **100** | Heightened protection narrative (e.g. child/adolescent data — **verify** classification). |

**Formula (raw density):** \(\textit{density\_raw} = \sum_i (\textit{count}_i \times \textit{weight}_i)\).

**Dashboard scale (0–100):** `risk_score = min(100, (density_raw / cap_raw) * 100)` with default **`cap_raw = 2500`** in code (tunable per engagement). **Disclose** the cap in the report footer when this mode is used so scores remain comparable across runs.

**Extra JSON fields (density mode only):** **`risk_density_raw`**, **`risk_density_scaled_cap`**, **`risk_density_breakdown`** (per-type lines: `pii_type`, `count`, **`risk_category`** (`IDENTIFIER` / `FINANCIAL` / `SENSITIVE` / `CHILD_DATA` — from ``core.intelligence``), `taxonomy`, `weight`, `line_score`), **`risk_density_taxonomy_version`**, **`dominant_risk_taxonomy`**. These fields justify *why* an asset scores high without embedding raw values.

**Not legal classification:** substring mapping from detector labels is a **starting taxonomy**; operators may override weights or caps per engagement in future versions.

### 3.3 Optional **NIST CSF 2.0** function hint (non-breaking)

CISOs often reason in **NIST CSF 2.0** *Functions* (Govern, Identify, Protect, Detect, Respond, Recover). To let a dashboard or PDF **filter findings by CSF function** without bumping the contract, each `detailed_findings[]` row **may** carry an **optional** array of short CSF codes:

| Field | Type | Notes |
| ----- | ---- | ----- |
| **`nist_csf_function_hint`** | array of strings | Short CSF 2.0 codes — **Function** (`"GV"`, `"ID"`, …) or **Function.Category** (`"ID.AM"`, `"PR.DS"`). Sorted in canonical order **GV, ID, PR, DE, RS, RC**. Present only when at least one `norm_tag` maps. |

**Where the mapping lives (versioned, shipped — not hard-coded):** `report/nist_csf_mapping.yaml` (`mapping_version`, e.g. `nist_csf_2_0_hint_v1`). It maps `norm_tag` substrings to CSF codes — same model as the **article hints** (§4) and the [compliance-samples/](compliance-samples/) profiles. The reference consolidator `report/grc_reporter.py` derives the hint from `norm_tags`; the loader is `report/nist_csf_hints.py`.

**Disclaimer location (ADR-0025):** so each row stays a plain array of codes, the heuristic disclaimer and mapping version are surfaced **once** in `compliance_mapping` (emitted only when at least one finding carries the hint):

| `compliance_mapping` key | Meaning |
| ----- | ----- |
| **`nist_csf_function_hint_method`** | e.g. `heuristic_norm_tag_to_csf_v1`. |
| **`nist_csf_mapping_version`** | Version string from the shipped table. |
| **`nist_csf_function_hint_disclaimer`** | Plain-language **hint, not a compliance determination or control attestation** ([ADR 0025](adr/ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md)); CISO/DPO validates. |

**Non-breaking:** this is an **additive optional** field — `schema_version` stays `data_boar_grc_executive_report_v1`; consumers that ignore unknown keys are unaffected. **Scope:** NIST CSF 2.0 **only** (no COBIT/SOC 2/ISO mapping here). For the **prose** tri-level positioning (NIST CSF / SANS / ISO 27035) see the related documentation discussion; this field is the **structured** complement that makes the artefact *carry* the CSF tag.

---

## 4. Mapping logic — from Data Boar artefacts to this JSON

This section is the **contract for implementers**. A first-party consolidator lives at **`report/grc_reporter.py`** (`GRCReporter`); English **risk categories** and ``calculate_risk`` live in **`core/intelligence.py`**; GRC tier labels and 0–100 scaling live in **`report/grc_risk_taxonomy.py`**. Full SQLite row ingest and PDF wiring remain future work.

| Source | Maps to |
| ------ | ------- |
| SQLite **session** row (`session_id`, timestamps, optional tenant/technician labels) | **`report_metadata`**, optional executive narrative context (labels are **operator-supplied**, not verified identity). |
| **`database_findings` / `filesystem_findings`** rows (target, location, pattern, sensitivity, `norm_tag`, recommendation text) | **`detailed_findings`** (+ aggregation into **`executive_summary`** counts). |
| **`report.recommendation_overrides`** in config ([USAGE.md](USAGE.md)) | **`recommendations`** priority and wording where configured. |
| Heatmap / density sheets (if present for session) | Optional **`executive_summary`** visual refs or embedded chart ids for PDF. |
| **`--export-audit-trail`** payload ([ADR 0037](adr/ADR-0037-data-boar-self-audit-log-governance.md), `core/audit_export.py`) | **`report_metadata.scanner_version`**, integrity / runtime trust **annex** object (either merged or referenced by `report_id`). |
| Lab orchestration **`lab_result.json`** (`DATA_BOAR_COMPLETAO_EXIT_v1`) | **Not** merged into customer GRC JSON by default; use for **internal** assurance of the scan environment when documenting methodology. |

**`compliance_score` (illustrative formula, to be fixed in code when implemented):** example: start from 100, subtract weighted sums of `risk_score` above threshold per `asset_class`, apply caps, never below 0. Document the formula next to the field in the generator’s README. **Disclose** in the PDF/dashboard footer that the score is **heuristic**.

**Article hints:** map `norm_tag` and methodology tables to `lgpd_articles_hint` / `gdpr_articles_hint` using a **versioned CSV or YAML** shipped with the product (like compliance samples), never hard-code counsel conclusions in code comments as “truth”.

---

## 5. Consumer checklist (CISO / DPO handoff)

1. Confirm **`scope`** matches the **engagement letter** (systems in/out).
2. Treat **`compliance_mapping`**, per-row **`regulatory_impact`**, and recommendation **`regulatory_impact_note`** as **starting points** for workshop, not filings. Do **not** treat template language about fines or articles as **verified** sanctions advice without counsel review.
3. Keep **raw PII** out of this JSON; link to **redacted** annexes or on-prem dashboards with access control.
4. Version **`schema_version`** in change logs when fields move.
5. Validate **`data_category`** (`personal` vs `sensitive`) against your **data inventory** and legal analysis; the product’s classifier is a **hint**, not a definitive LGPD Art. 11 determination.

---

## 6. Evolution

Implementations should write **`schema_version`**: **`data_boar_grc_executive_report_v1`** and publish migration notes in release docs when the shape changes. A reference builder is **`report.grc_reporter.GRCReporter`**. Plain-text planning filenames for PDF implementation remain under the repository’s internal planning tree (see [docs/README.md](README.md) — *Internal and reference*); this specification stays the **stable contract** for integrators.
