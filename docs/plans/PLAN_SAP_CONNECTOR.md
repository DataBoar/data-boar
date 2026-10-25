# Plan: SAP connector – add SAP to the "data soup"

**Status:** Deferred
**Date:** 2026-03-15
**Authors:** Fabio Leitao
**Priority:** H3

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md) (central to-do list)

## When implementing steps: update docs and tests; then update PLANS_TODO.md and this file.

SAP is a **critical enterprise data source** for many organizations. Tables and applications in SAP systems often hold personal and sensitive data (employees, customers, health, payroll, etc.). To support compliance (LGPD, GDPR, CCPA, HIPAA, etc.) and the same violation-detection capabilities we already offer for databases, files, APIs, Power BI, and Dataverse, this plan adds a **connector** so the Data Boar can **ingest and digest** SAP data—discovering and sampling structures, then reporting findings in the same Excel/heatmap flow.

**Goal:** Operators can add SAP targets to `config.yaml`, run a scan, and get findings (e.g. table/field, sample, sensitivity) so DPOs and compliance teams can see possible violations in SAP alongside other sources.

---

## Why SAP

- **Market:** Many enterprises run SAP (ERP, S/4HANA, BW, SuccessFactors, etc.); data residency and compliance audits frequently include SAP.
- **Data soup:** Today we scan files, SQL/NoSQL DBs, APIs, Power BI, Dataverse, shares. SAP is a major gap for "one view" of where PII/sensitive data lives.
- **Same value:** Same detection (regex + ML/DL), same report format, same recommendations; only the **source type** and connection method change.

---

## Scope and approach options

SAP exposure varies by product and access method. This plan keeps **discovery and sampling** consistent with existing connectors (discover structures → sample values → `scanner.scan_column()` → `save_finding()`).

## Possible access paths (to be decided in Phase 1):

| Option               | Description                                                                    | Pros / cons                                                                |
| ------               | -----------                                                                    | ------------                                                               |
| **SAP HANA (SQL)**   | Connect to HANA as a database (ODBC/JDBC or `hdbcli`). Scan tables/views.      | Same pattern as existing SQL connector; HANA-specific types and auth.      |
| **OData / OData V2** | Call SAP OData services (e.g. S/4HANA, SuccessFactors), list entities, sample. | Covers many SAP apps; need to map entity/field to our finding shape.       |
| **RFC / BAPI**       | Call RFC/BAPI to list and read tables (e.g. via `pyrfc`).                      | Classic SAP; requires SAP NetWeaver stack and RFC libs.                    |
| **Export / file**    | Scan SAP export files (e.g. CSV/Excel from SAP exports) as filesystem.         | No live connector; already partly covered if files land in a scanned path. |

**Recommendation:** Start with **one** primary path (e.g. HANA as database, or OData for S/4HANA/cloud) so the connector is shippable; document how to add a second path (e.g. optional extra `[sap]`) later.

---

## To-dos (phased)

| #                                 | To-do                                                                                                                                                                                              | Status     |
| ----                              | -------------------------------------------------------------------------------------------------------------------------------------                                                              | ---------- |
| **Phase 1 – Research and decide** |                                                                                                                                                                                                    |            |
| 1.1                               | **Research:** Document SAP access methods (HANA SQL, OData V2/V4, RFC) and which are feasible from Python (libraries, licensing, typical operator setup).                                          | ⬜ Pending  |
| 1.2                               | **Decide:** Choose primary path (e.g. `type: sap_hana` as database, or `type: sap_odata` with base_url + auth). Document in this plan.                                                             | ⬜ Pending  |
| 1.3                               | **Config shape:** Define target schema (e.g. `name`, `type`, `host`/`base_url`, `client`, `auth`, optional `tables`/`entities` filter).                                                            | ⬜ Pending  |
| **Phase 2 – Implement**           |                                                                                                                                                                                                    |            |
| 2.1                               | **Connector module:** Add `connectors/sap_*.py` (e.g. `sap_hana_connector.py` or `sap_odata_connector.py`) with connect/run/close, discovery, sampling, `scanner.scan_column()`, `save_finding()`. | ⬜ Pending  |
| 2.2                               | **Register:** Register type in `core/connector_registry`; wire in `core/engine.py` (optional-import guard if dependency is optional).                                                              | ⬜ Pending  |
| 2.3                               | **Optional extra:** If SAP lib is heavy or licensed, add e.g. `[sap]` in `pyproject.toml` and guard import/registration.                                                                           | ⬜ Pending  |
| **Phase 3 – Docs and tests**      |                                                                                                                                                                                                    |            |
| 3.1                               | **USAGE / TECH_GUIDE:** Document SAP target in config schema and ADDING_CONNECTORS (or dedicated SAP section). EN + pt-BR.                                                                         | ⬜ Pending  |
| 3.2                               | **Tests:** Unit or integration test (e.g. mock SAP response) that connector discovers and saves findings; no regression in full suite.                                                             | ⬜ Pending  |
| 3.3                               | **Pitch:** Per [pitch-roadmap-sync](.cursor/rules/pitch-roadmap-sync.mdc), add SAP to README "data soup" list when connector is done; remove from Roadmap.                                         | ⬜ Pending  |

---

## Other data sources to consider (recommendations)

When prioritising which connectors to add after SAP, the following are strong candidates for the same "data soup" and violation-detection value:

| Source                         | Why consider                                                             | Likely effort / notes                                                          |
| ------                         | -----------                                                              | -----------------------                                                        |
| **ServiceNow**                 | CMDB, incident, user data; many enterprises; REST/API.                   | REST connector pattern; table API or scoped API.                               |
| **Salesforce**                 | CRM and marketing data (contacts, leads, custom objects); SOQL and REST. | OAuth + REST; discover objects, sample records; similar to Power BI/Dataverse. |
| **Workday**                    | HR and financial data (personal, payroll); compliance-heavy.             | REST/API; tenant-based; auth and discovery pattern.                            |
| **Google BigQuery**            | Data warehouse; many orgs store PII in BQ.                               | Already "SQL-like"; driver or dedicated connector; optional `[bigquery]`.      |
| **Elasticsearch / OpenSearch** | Logs and search indices often contain PII.                               | Index mapping + sample docs; same scan_column pattern.                         |
| **Kafka (topics)**             | Event streams; schema registry + sample from topic.                      | More operational; may fit "sample recent messages" for PII in payloads.        |
| **Confluence / Jira**          | Wikis and tickets sometimes contain personal data.                       | REST API; list spaces/projects, sample content; similar to API connector.      |
| **Splunk**                     | Log and search; PII in logs.                                             | Search API; define saved search or index + sample.                             |

**Suggested order (after SAP):** ServiceNow or Salesforce (high enterprise demand), then BigQuery or Elasticsearch (broad data-store coverage). Document each as a **future plan** in PLANS_TODO when the team is ready so the roadmap stays honest.

---

## Dependencies and placement

- **Configurable timeouts:** Helpful for SAP (long-running queries or OData calls); not blocking.
- **Secrets vault (Phase A):** SAP credentials (e.g. OAuth, RFC user) benefit from env expansion or vault; not blocking for a first version (config with env vars is enough).
- **Placement in sequence:** Can run in parallel with other "scan and report" plans (Compliance samples, Compressed files, Data source versions). See [PLANS_TODO.md](PLANS_TODO.md) for the full sequence.

---

## See also

- **[PLAN_ENTERPRISE_HR_SST_ERP_CONNECTORS.md](PLAN_ENTERPRISE_HR_SST_ERP_CONNECTORS.md)** — Umbrella backlog for Brazilian SST (e.g. SOC), HR/folha suites, ERP/CRM beyond SAP, helpdesk, and URM-class tools; research-first and data-minimisation for health data.

---

## Reference

- **Connector guide:** [ADDING_CONNECTORS.md](../ADDING_CONNECTORS.md).
- **Central to-do list:** [PLANS_TODO.md](PLANS_TODO.md).
- **Pitch–roadmap sync:** When this plan is completed, update README/README.pt_BR so SAP appears in the "data soup" list and is removed from the Roadmap sentence (see `.cursor/rules/pitch-roadmap-sync.mdc`).
