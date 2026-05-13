# Plan: Databricks SQL, Unity Catalog, and lakehouse scope (medium-term)

**Status:** Pending
**Date:** 2026-05-02
**Authors:** Fabio Leitao
**Priority:** H2

**Horizon:** **[H2]** medium-term (post core connector hardening and scope-import maturity), unless promoted earlier by demand.

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)

<!-- plans-hub-summary: Medium-term Pro/Ent-shaped backlog: (1) lakehouse tables as scan targets via Databricks SQL; (2) UC or curated tables as source of target list / scope metadata—aligned with CSV scope import and data soup formats. -->
<!-- plans-hub-related: PLAN_SCOPE_IMPORT_FROM_EXPORTS.md, PLAN_ADDITIONAL_DATA_SOUP_FORMATS.md, PLAN_ENTERPRISE_HR_SST_ERP_CONNECTORS.md, PLAN_OBJECT_STORAGE_CLOUD_CONNECTORS.md, PLAN_FINDINGS_CORPORATE_REPOSITORY_EXPORT.md, ADDING_CONNECTORS.md -->

---

## Agreement (maintainer stance)

**Yes — defer detail until a customer requires it.** Shipping a **thin, validated** slice (e.g. SQL warehouse read + one lab config) beats a large speculative build. This plan stays **documentation-first** until promotion.

---

## Two tracks (same product metaphor)

| Track | Metaphor | What it means for Data Boar | Primary dependency today |
| ----- | -------- | ---------------------------- | ------------------------- |
| **A — Soup ingredient** | Data you **scan** | Managed / external **tables** (often **Delta / Parquet** behind UC), **views**, and (later) **volumes** paths—same **discover → sample → detect → finding** loop as other SQL sources. | First-class **Databricks SQL** path (driver, auth, SQLAlchemy `inspect` behaviour for **catalog.schema.table**), timeouts, least-privilege docs. See [ADDING_CONNECTORS.md](../ADDING_CONNECTORS.md), `connectors/sql_connector.py` patterns (incl. Snowflake-style schema skipping). |
| **B — Recipe / inventory** | Where to **point** the scanner | **Curated catalog**: UC metadata, **inventory tables** in the lakehouse, or ETL outputs that list hosts, paths, DB endpoints, `source_system`, confidence—**normalized into** the same **target list** model as [PLAN_SCOPE_IMPORT_FROM_EXPORTS.md](PLAN_SCOPE_IMPORT_FROM_EXPORTS.md) (CSV → YAML fragments today). | **No** automatic equivalence to “GLPI export” unless the customer **lands** ITAM/ITSM exports (or integrations) **into** UC or tables; then we **import** via CSV pipeline, SQL-driven code generation, or a **future** UC REST adapter. |

**Key message:** Unity Catalog is **governance + discovery metadata**, not a replacement for **GLPI / ManageEngine / Snipe-IT / Contributor-Ati / Service Management** exports. It becomes the **same slot as “inventory”** when the organisation **chooses the lakehouse as the system of record** for normalized scope.

---

## Relationship to existing plans

| Plan | Relationship |
| ---- | ------------- |
| [PLAN_SCOPE_IMPORT_FROM_EXPORTS.md](PLAN_SCOPE_IMPORT_FROM_EXPORTS.md) | **Track B** extends the same **bootstrap scope** story: catalog or warehouse tables **feed** canonical targets + `scope_import` breadcrumbs; CSV remains the **v1** operator path. |
| [PLAN_ADDITIONAL_DATA_SOUP_FORMATS.md](PLAN_ADDITIONAL_DATA_SOUP_FORMATS.md) | **Track A** aligns with **Parquet / ORC / columnar** “soup” already in the format roadmap; lakehouse tables are often those formats under SQL. |
| [PLAN_ENTERPRISE_HR_SST_ERP_CONNECTORS.md](PLAN_ENTERPRISE_HR_SST_ERP_CONNECTORS.md) | **Distinct:** live HR/ERP/helpdesk **sampling** vs **this** plan’s focus on **Databricks as a technical substrate** (SQL + metadata). Overlap only if a customer stores CMDB exports **in** UC-managed tables. |
| [PLAN_OBJECT_STORAGE_CLOUD_CONNECTORS.md](PLAN_OBJECT_STORAGE_CLOUD_CONNECTORS.md) | **Complementary:** UC **external locations** / cloud paths may eventually need **object-store** connectors for file-shaped soup, not SQL alone. |
| [PLAN_FINDINGS_CORPORATE_REPOSITORY_EXPORT.md](PLAN_FINDINGS_CORPORATE_REPOSITORY_EXPORT.md) | **Orthogonal sink:** customers may want **findings** in a **lakehouse** or **warehouse** they operate — **export/sync** track is separate from using Databricks **only** as a scan **source**. |

---

## Commercial posture (Pro / Enterprise–shaped)

- **Positioning:** Treat **Databricks SQL warehouse connectivity** and **catalog-driven scope generation** as **add-on / tier-gated** capabilities when product marketing is ready — same discipline as other **advanced connector** work ([LICENSING_SPEC.md](../LICENSING_SPEC.md) “future extensions”; runtime flags in `core/licensing/` when implemented).
- **Until code ships:** This plan is **spec + sequencing only**; no promise of **Community** vs **Pro** split until validated with at least one design partner.

---

## Non-goals (until explicitly in scope)

- **Replacing** UC, ITSM, or CMDB products.
- **Bulk exfiltration** of lakehouse data — scanner stays **metadata + bounded samples** per existing connector contract.
- **OAuth-only** enterprise auth without a documented operator story (PAT vs OAuth vs service principal — pick per customer segment when implementing).

---

## Phased outline (for later breakdown)

| Phase | Focus | Outcome |
| ----- | ----- | -------- |
| **A — Discovery** | Lab repro: warehouse URL, token/PAT, `SELECT` on `information_schema` or small known table; document **inspector** behaviour (catalog vs schema names). | Go / no-go on SQLAlchemy path; risks listed. |
| **B — Ingredient (MVP)** | Supported `type: database` **driver + config docs** + skip lists for system catalogs; optional `url:` override patterns. | Customer can point Data Boar at **Databricks SQL** for **table/column sampling** like other warehouses. |
| **C — Recipe** | **Option 1:** Scheduled job exports inventory table → **CSV** → existing `scope_import_csv.py`. **Option 2:** Read-only SQL over an **inventory** schema to emit YAML fragment (script or productized). | Same **merge-safe targets** story as exports from GLPI-class tools. |
| **D — Optional** | UC **REST** metadata (owners, tags, external locations) for **report enrichment** or **scope hints** — not required for MVP. | `data_source_inventory` / report narrative alignment with [PLAN_DATA_SOURCE_VERSIONS_AND_HARDENING.md](PLAN_DATA_SOURCE_VERSIONS_AND_HARDENING.md) when that work advances. |

---

## Promotion criteria (when to break down tasks for real)

1. **Named** prospect or customer with **Databricks + UC** in production and **written** scope for read-only access.
1. **Security review** of auth (secrets in env/vault, not config files in repo) and **Databricks** ToS / workspace policy alignment.
1. **Engineering capacity** after higher-priority connector and **scope import Phase E** decisions (vendor adapters) are stable enough not to starve.

---

## Changelog

- **2026-04-28:** Initial plan — captures **soup ingredient** + **recipe / inventory** dual track, **Pro/Ent-shaped** backlog, **customer-pull** gating; links to scope import, data soup formats, enterprise connector umbrella, object storage plan.
