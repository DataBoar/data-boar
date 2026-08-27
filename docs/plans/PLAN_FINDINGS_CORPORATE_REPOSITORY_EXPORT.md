# Plan: Corporate findings repository — export / sync beyond local SQLite (medium-term)

<!-- plans-hub-summary: Optional findings export to customer stores and catalog tags; v1.8.0 #1058 OpenMetadata/DataHub/Atlas + opt-in PII-as-quality-check; discovery stays read-only (no source write-back) -->
<!-- plans-hub-related: PLAN_DATABRICKS_UNITY_LAKEHOUSE_SCOPE_AND_SCAN.md, PLAN_OBJECT_STORAGE_CLOUD_CONNECTORS.md, PLAN_NOTIFICATIONS_OFFBAND_AND_SCAN_COMPLETE.md, PLAN_FIDESLANG_EXPORT_ADAPTER.md, SECURITY.md, REPORTS_AND_COMPLIANCE_OUTPUTS.md -->

**Português (Brasil):** [PLAN_FINDINGS_CORPORATE_REPOSITORY_EXPORT.pt_BR.md](PLAN_FINDINGS_CORPORATE_REPOSITORY_EXPORT.pt_BR.md)

**Status:** Pending (no native sink on `main`; v1.8.0 survey [#1058](https://github.com/DataBoar/data-boar/issues/1058) enriches this plan — do not archive)
**Date:** 2026-05-02 (v1.8.0 wave: 2026-08-27)
**Authors:** Fabio Leitao
**Priority:** H2
**Depends on:** ADR-0048
**Milestone:** v1.8.0
**GitHub:** [#1058](https://github.com/DataBoar/data-boar/issues/1058) (v1.8.x catalog format + PII-as-quality-check)

**Horizon:** **[H2]** medium-term; **expedite** only when a **named prospect or contract** requires a concrete sink (MongoDB, a given SQL engine, object storage + lake ingestion, catalog API, etc.).

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)

---

## Problem statement

Some **corporate** prospects are **not comfortable** treating **only** the product’s **local SQLite** file (`LocalDBManager` / `audit_results.db` pattern in `core/database.py`) as the **sole** long-lived store for **scan evidence** and **session metadata**. They may require:

- **Central security / GRC** warehouses (SQL or document stores the customer already operates),
- **Data lake** landing zones (e.g. **Parquet/JSON** batches consumed by **Databricks**, **Snowflake**, **BigQuery** loaders),
- **Operational** stores (**MongoDB**, **PostgreSQL**, etc.) for dashboards owned by the customer,
- **Retention and access control** on **their** infrastructure (RBAC, encryption at rest, backup policy).

Today, the **primary** persistence path is **SQLite** plus **Excel/report** outputs from the report generator. That remains valid for many deployments; this plan adds an **optional second leg**.

---

## Feasibility (short answer)

**Yes, it is technically feasible** to **export** or **incrementally sync** the **same finding shapes** the product already persists (session-scoped rows, **metadata-oriented** fields — no bulk raw sampled payloads in the default contract) into **customer-chosen** backends. The work is mostly:

1. **Stable export schema** (versioned JSON or relational DDL) mapping `scan_sessions`, `database_findings`, `filesystem_findings`, failures, and selected inventory rows — aligned with what [REPORTS_AND_COMPLIANCE_OUTPUTS.md](../REPORTS_AND_COMPLIANCE_OUTPUTS.md) already implies for evidence discipline.
1. **Transport + idempotency** (batch after scan vs scheduled sync; `session_id` + row keys for upserts).
1. **Credential isolation** (env, vault, or secret manager — **never** committed config); see [SECURITY.md](../SECURITY.md).
1. **Per-sink modules** or a **thin “sink” interface** so Mongo vs SQL vs file-drop do not fork the core scanner.

**Non-goals (default):** Replicating **full** SQLite schema history into every sink on day one; **streaming every row sample** to a remote DB (violates metadata-minimisation story unless explicitly opted in with legal sign-off).

---

## Commercial posture (Pro / Enterprise–shaped)

- Position as **add-on / tier-gated** capability: **“corporate evidence repository connectors”** or **“post-scan export profiles”** when product is ready — align with [LICENSING_SPEC.md](../LICENSING_SPEC.md) and runtime tier flags when implemented.
- Until code ships: **documentation and ADR** only; **no** promise that **Community** tier includes multi-sink sync.

---

## Relationship to other plans

| Artifact | Relationship |
| -------- | ------------- |
| [PLAN_DATABRICKS_UNITY_LAKEHOUSE_SCOPE_AND_SCAN.md](PLAN_DATABRICKS_UNITY_LAKEHOUSE_SCOPE_AND_SCAN.md) | A **lakehouse** may be a **sink** (batch files or SQL loads) as well as a **scan source**; keep **source** vs **sink** config separate to avoid confusion. |
| [PLAN_OBJECT_STORAGE_CLOUD_CONNECTORS.md](PLAN_OBJECT_STORAGE_CLOUD_CONNECTORS.md) | **S3 / Azure Blob / GCS** are natural **staging** targets for JSONL/Parquet export batches before customer ETL. |
| [PLAN_NOTIFICATIONS_OFFBAND_AND_SCAN_COMPLETE.md](PLAN_NOTIFICATIONS_OFFBAND_AND_SCAN_COMPLETE.md) | **Complementary:** webhooks notify; **this** plan **lands** structured findings where **analytics** teams work. |
| [PLAN_FIDESLANG_EXPORT_ADAPTER.md](PLAN_FIDESLANG_EXPORT_ADAPTER.md) | Sibling **export-only** taxonomy view (`data_category`); do **not** invent a second mapping dialect — catalog tags reuse the same internal `norm_tag` / pattern leaves. |
| [OBSERVABILITY_SRE.md](../OBSERVABILITY_SRE.md) | Product **metrics** export is a **different** track; do not conflate **findings** sink with Prometheus/OpenTelemetry. |

---

## Phased outline (for later breakdown)

| Phase | Focus | Outcome |
| ----- | ----- | -------- |
| **A — Contract** | Document **canonical export JSON** (or CSV bundles) for one `session_id`: findings + failures + session header; version field; PII policy reminder (no raw samples). | Customers can **ingest today** with external ETL **without** new code (manual or their pipeline). |
| **B — Operator CLI / post-scan hook** | `scripts/` or engine hook: **after** `generate_final_reports`, push export file(s) to a **path** or **presigned URL**; exit codes and logs. | **Lowest** engineering risk; proves ops story. |
| **C — Native sinks (pick order by demand)** | **1)** PostgreSQL / SQL Server **DDL + upsert**; **2)** MongoDB **collections** with indexes on `session_id`; **3)** optional **S3 PutObject** using existing object-storage direction. | **Automated** landing in **corp DB** the customer names. |
| **D — Governance** | Retention flags, **delete-after-export** (optional, dangerous — doc-heavy), sink-side **RBAC** checklist, audit log line “exported to X”. | Enterprise **review** packet content. |

---

## Promotion criteria (when to expedite)

1. **Contractual** or **security questionnaire** item: “findings must land in **our** Mongo/SQL/lake.”
1. **Reference architecture** from a design partner (VPC, private link, batch window).
1. **Engineering slot** after at least **Phase A** export contract is stable (avoid building three sinks before one schema is agreed).

---

## Rearranging the to-do stack

**Explicit:** If a customer requires **Phase C** before other **[H2]** items, **PLANS_TODO.md** and sprint notes may **reorder** — this plan does **not** claim fixed priority vs [PLAN_DATABRICKS_UNITY_LAKEHOUSE_SCOPE_AND_SCAN.md](PLAN_DATABRICKS_UNITY_LAKEHOUSE_SCOPE_AND_SCAN.md) or connector backlog; **maintainer decision** per [TOKEN_AWARE_USAGE.md](TOKEN_AWARE_USAGE.md) and commercial pressure.

---

## Changelog

- **2026-08-27:** v1.8.0 survey **[#1058](https://github.com/DataBoar/data-boar/issues/1058)** — catalog tag formats (OpenMetadata / DataHub / Apache Atlas) and opt-in **PII-as-quality-check** sidecar; discovery remains read-only (no source write-back).
- **2026-04-28:** Initial plan — corporate **findings repository / export** beyond SQLite; **Pro/Ent-shaped**; **customer-pull** gating; links to lakehouse plan, object storage, notifications, security.

---

## v1.8.0 wave — catalog format + PII-as-quality-check ([#1058](https://github.com/DataBoar/data-boar/issues/1058))

**Driver:** Landscape survey (private competitive dossier). **Docs-first** in this PR; code stays on the existing **optional export / sink** outline (Phases **A–D**). This wave does **not** add a connector, REST client, or pipeline orchestrator.

**Invariant (doctrine):** Scan **discovery remains read-only**. An OpenMetadata / DataHub / Atlas **exporter is opt-in** and may **push tags or entities into the customer’s catalog**. It must **never** write back to the **scanned source** (no `UPDATE`/`ALTER`/`DELETE` on customer tables, files, or object keys). Catalog write ≠ source write. Lakehouse **scan** ([PLAN_DATABRICKS_UNITY_LAKEHOUSE_SCOPE_AND_SCAN.md](PLAN_DATABRICKS_UNITY_LAKEHOUSE_SCOPE_AND_SCAN.md)) stays a **source** track; this plan is **sink / export**.

**Non-claims (align with [COMPLIANCE_AND_LEGAL.md](../COMPLIANCE_AND_LEGAL.md) and [ADR 0025](../adr/ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md)):** Exported tags and quality-check **sidecars** are **inventory and technical-mapping aids** — not a legal determination that a column is personal data under LGPD/GDPR, and **not** an ANPD (or other authority) seal. A pipeline that quarantines a run from these hints does so under **customer policy**.

### What already ships or is already specified (do not invent a second contract)

| Surface | Role today | Catalog / DQ relevance |
| ------- | ---------- | ---------------------- |
| Local SQLite + Excel/report | Primary evidence store | Source of **metadata-oriented** finding rows (no bulk raw samples by default) |
| Phase **A** (this plan) | Versioned export JSON/CSV for one `session_id` | **Canonical** payload other tools ingest — including catalog mappers |
| [PLAN_FIDESLANG_EXPORT_ADAPTER.md](PLAN_FIDESLANG_EXPORT_ADAPTER.md) | Optional lossy `data_category` on **export only** | Same **export-only, default-off** pattern as catalog tags |
| `--export-remediation-manifest` / JSONL (**#649** / **#1443**) | Location + `pii_type` + `suggested_profile` | Coordinates for tags; **not** a catalog client |
| Object-storage / SQL / Mongo sinks (Phases **B–C**) | Customer-chosen landing | Staging **before** catalog ETL — still not source mutation |

### Catalog emission (buyer language → existing export)

Competitive “send findings to the catalog” SKUs usually mean **tags on assets the customer already registered**. Map vendor names onto **one** versioned export, then **lossy** tag ids:

| Catalog family | Typical buyer ask | Product hook (no new engine in this docs PR) | Guardrail |
| -------------- | ----------------- | -------------------------------------------- | --------- |
| **OpenMetadata** | Classification / glossary tags on tables and columns | Opt-in mapper from export JSON → OM tag/classification payload (customer or later sink module) | Opt-in; **never** PATCH the scanned warehouse |
| **DataHub** | Dataset / schema field aspects or tags | Same export JSON; DataHub aspect shape is a **view**, not a second finding model | Default off; documented field mapping |
| **Apache Atlas** | Entity classifications | Atlas type names mapped from `pattern_detected` / `norm_tag` (lossy, like Fideslang) | Customer Atlas admin applies types; Data Boar does not own Atlas |

**Output-as-governance-input:** the customer’s catalog **receives** findings without re-keying Excel. That is **interop**, not a claim that OpenMetadata (or ANPD) validated the scan.

### PII-as-quality-check (opt-in sidecar)

Expose findings as a **pipeline gate artifact** in the **style** of a data-quality rule (quarantine the **run**, or emit a **column flag for the catalog/orchestrator**):

| Idea | What to emit | What not to do |
| ---- | ------------ | -------------- |
| **Quarantine** | Sidecar JSON/YAML: `session_id`, asset ids, severity, pass/fail for the **pipeline job** | Do not pause or kill customer jobs from inside the scanner |
| **Column flag** | Suggested catalog/orchestrator flag (`pii_review`, `quarantine_column`) derived from finding coordinates | Do **not** `ALTER`/`UPDATE` the source column |
| **DQ-tool shape** | Optional later stub resembling dbt/GE **test results** the customer wires | Data Boar is **not** a DQ engine and does not replace Great Expectations / Soda |

Exact CLI/YAML keys stay **TBD** until Phase **B**. This PR only locks the **opt-in + read-only source** contract.

### Compliance-sample methodology

Same discipline as other v1.8.0 survey slices — **do not** add a catalog-vendor YAML dialect:

1. Keep `norm_tag` in existing `docs/compliance-samples/compliance-sample-*.yaml` files as a **framework label**, not a legal conclusion.
2. Catalog tag ids, when implemented, are a **lossy export view** (same principle as Fideslang).
3. Optional later `recommendation_overrides` may mention “review in catalog” — they still **do not** mutate sources.
4. No performance claims without a pinned file under `tests/benchmarks/`.

### Execution table (doc-first → later slices)

| Step | Deliverable | Status |
| ---- | ----------- | ------ |
| P1 | This plan section + hub summary + `PLANS_TODO` survey rows | ✅ Done (docs PR) |
| P2 | Mapping note: OpenMetadata / DataHub / Atlas tag fields ← Phase **A** export JSON (lossy table; no client code) | ⬜ Pending |
| P3 | Opt-in quality-check **sidecar** schema (quarantine / column flag for orchestrators; still no source write) | ⬜ Pending |
| P4 | Phase **B** CLI / post-scan hook (existing outline) can optionally emit catalog JSON + sidecar | ⬜ Pending (existing phase table) |
| P5 | Native catalog HTTP sink (customer-pull; still no source write-back) | ⬜ Pending (Phase **C**-class) |

### Revisit (sibling plans — survey notes only)

- [PLAN_FIDESLANG_EXPORT_ADAPTER.md](PLAN_FIDESLANG_EXPORT_ADAPTER.md): keep **one** lossy taxonomy adapter family; catalog vendors are additional **views**, not a fork of SQLite.
- [PLAN_DATABRICKS_UNITY_LAKEHOUSE_SCOPE_AND_SCAN.md](PLAN_DATABRICKS_UNITY_LAKEHOUSE_SCOPE_AND_SCAN.md): Unity Catalog as **scan scope** remains separate from **findings sink**.
- [PLAN_ACTION_PLAN_GENERATOR_POST_SCAN.md](PLAN_ACTION_PLAN_GENERATOR_POST_SCAN.md): suggested actions ≠ catalog exporter ≠ source write-back.
