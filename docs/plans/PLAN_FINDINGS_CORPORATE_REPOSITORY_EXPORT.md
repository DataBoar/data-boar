# Plan: Corporate findings repository — export / sync beyond local SQLite (medium-term)

**Status:** Pending
**Date:** 2026-05-02
**Authors:** Fabio Leitao
**Priority:** H2
**Depends on:** ADR-0048

**Horizon:** **[H2]** medium-term; **expedite** only when a **named prospect or contract** requires a concrete sink (MongoDB, a given SQL engine, object storage + lake ingestion, etc.).

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)

<!-- plans-hub-summary: Medium-term Pro/Ent-shaped backlog: optional export or sync of scan findings (metadata model) from local SQLite to customer-chosen corporate stores—SQL, MongoDB, object/lake paths—without changing the core scan contract. -->
<!-- plans-hub-related: PLAN_DATABRICKS_UNITY_LAKEHOUSE_SCOPE_AND_SCAN.md, PLAN_OBJECT_STORAGE_CLOUD_CONNECTORS.md, PLAN_NOTIFICATIONS_OFFBAND_AND_SCAN_COMPLETE.md, SECURITY.md, REPORTS_AND_COMPLIANCE_OUTPUTS.md -->

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

- **2026-04-28:** Initial plan — corporate **findings repository / export** beyond SQLite; **Pro/Ent-shaped**; **customer-pull** gating; links to lakehouse plan, object storage, notifications, security.
