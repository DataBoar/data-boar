# Plan: Data source version and protocol detection with CVE awareness and hardening guidance

**Status:** Deferred
**Date:** 2026-03-15
**Authors:** Fabio Leitao
**Priority:** H3

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md) (central to-do list)

## When implementing steps: update docs and tests; then update PLANS_TODO.md and this file.

This plan adds a **data-source inventory** and **hardening guidance** feature: while scanning multiple targets (SQL, NoSQL, file shares, APIs, BI/dashboards), the app will **detect and record** product versions, protocol/API versions, and transport security (e.g. TLS) where possible. From that data it will **assess known CVEs** (when feasible), **protocol strength**, and **documented mitigations or upgrade paths** from public sources only, producing a **next-steps hardening guide** for IT and cybersecurity teams. All guidance is **professional, actionable, and based on public documentation and how-tos** when discovered.

---

## Goals

- **Inventory:** For each successfully connected target, record: product name (e.g. PostgreSQL, MongoDB, Redis), product version, protocol or API version (e.g. SMB 3.0, Power BI v1.0, OData 4.0), and transport security (TLS version, encryption in transit) when available.
- **Security posture:** Use version and protocol data to:
- Check against **known CVEs** (via optional NVD or local database lookup by product + version).
- Flag **deprecated or weak protocols** (e.g. SMB1, TLS &lt; 1.2) and suggest hardening.
- Surface **documented mitigation steps** and **compatibility-preserving upgrade paths** from vendor or community public docs only.
- **Report and guide:** Add report sheets (e.g. "Data source inventory", "Hardening recommendations") and a **next-steps hardening guide** (in report and/or dedicated doc) so IT and cybersecurity can prioritise upgrades and apply mitigations.
- **No regressions:** Existing scan and report behaviour unchanged; new logic is additive and optional where it involves external CVE data or extra I/O.

---

## Current state

- **Connectors** (see [TOPOLOGY.md](TOPOLOGY.md), [ADDING_CONNECTORS.md](ADDING_CONNECTORS.md)): SQL (PostgreSQL, MySQL, MariaDB, SQLite, MSSQL, Oracle), MongoDB, Redis, Snowflake, SMB/CIFS, SharePoint, WebDAV, NFS, Power BI, Dataverse, REST API, filesystem.
- **Findings:** Connectors call `save_finding(source_type, ...)` with metadata (target_name, server_ip, engine_details, schema, table, column, sensitivity, etc.). `engine_details` is a short string (e.g. `postgresql`, `redis`); **no product version or protocol version** is stored today.
- **Failures:** `save_failure(target_name, reason, details)` records unreachable/auth/permission; no version is captured for failed targets.
- **Report:** Excel sheets include Report info, Database/Filesystem findings, Scan failures (with hints), Recommendations, Trends, Aggregated identification. There is **no data-source inventory or hardening sheet**.
- **Security:** [SECURITY.md](../SECURITY.md) and [docs/SECURITY.md](SECURITY.md) describe app security; there is no feature today that assesses **scanned targets’** versions or CVEs.

---

## Scope: what can be detected per connector type

| Connector / type   | Product version                         | Protocol / API version              | Transport / TLS                       |
| ------------------ | -----------------------------------     | ----------------------------------- | ----------------------------------    |
| **SQL**            | Server version (dialect-specific query) | Driver/dialect (e.g. PostgreSQL 15) | From connection if exposed (TLS 1.2+) |
| **MongoDB**        | `buildInfo` / `serverStatus`            | Wire protocol version               | TLS from connection options           |
| **Redis**          | `INFO server` → redis_version           | Protocol (RESP)                     | TLS if connection uses it             |
| **Snowflake**      | Session/version query                   | ODBC/JDBC driver version (optional) | TLS (default)                         |
| **SMB / CIFS**     | Server name (optional)                  | SMB dialect (2.0, 2.1, 3.0, 3.1.1)  | Signing/encryption if exposed         |
| **SharePoint**     | N/A or Server header                    | REST / OData (from URL or headers)  | HTTPS                                 |
| **WebDAV**         | Server header                           | WebDAV / HTTP version               | HTTPS                                 |
| **NFS**            | N/A (limited)                           | NFSv3 / NFSv4 (from mount/config)   | Optional (Kerberos, RPCSEC_GSS)       |
| **Power BI**       | N/A                                     | API path (e.g. v1.0)                | HTTPS + Azure AD                      |
| **Dataverse**      | N/A                                     | OData 4.0 (from headers)            | HTTPS + Azure AD                      |
| **REST API**       | Optional (Server / X-API-Version)       | From target config or response      | HTTPS / TLS from client               |
| **Filesystem**     | N/A (local path)                        | —                                   | N/A                                   |

Detection should be **best-effort**: if a connector cannot obtain version or protocol (e.g. API does not expose it), record what is available and leave the rest blank; do not fail the scan.

---

## Data model

- **New table: `data_source_inventory`** (per session, per target that was successfully connected and for which we attempted collection):
- `session_id`, `target_name`, `source_type` (database / filesystem / api / share / powerbi / dataverse / rest / etc.)
- `product` (e.g. PostgreSQL, MongoDB, Redis, SMB)
- `product_version` (e.g. 15.3, 6.0.12)
- `protocol_or_api_version` (e.g. SMB 3.0, OData 4.0, Power BI v1.0)
- `transport_security` (e.g. TLS 1.2, TLS 1.3, Encrypted, or empty)
- `raw_details` (optional JSON or text for vendor-specific build strings or extra fields)
- `created_at`

- **New table or extended model: hardening recommendations** (per inventory row, optional):
- Link to `data_source_inventory` (or session_id + target_name)
- `finding_type` (cve, deprecated_protocol, weak_transport, upgrade_available)
- `identifier` (e.g. CVE-2024-XXXXX, or "SMB1", "TLS1.0")
- `severity` (critical, high, medium, low, info)
- `summary` (short description)
- `mitigation` (text: steps or link to public doc)
- `doc_url` (optional: vendor or NVD URL)
- `created_at`

Alternatively, hardening rows can be **generated at report time** from inventory + CVE/local DB lookup, without persisting in SQLite, so that updates to CVE data are reflected on next report. The plan leaves this choice to implementation; either way, the **report** must show inventory + recommendations.

- **LocalDBManager:** New method e.g. `save_data_source_inventory(session_id, target_name, source_type, product=None, product_version=None, protocol_or_api_version=None, transport_security=None, raw_details=None)` and optionally `save_hardening_finding(...)` or a single method that writes both. Migration: add new table(s) in `core/database.py` and run migration on init.

---

## CVE and hardening logic

- **Input:** Rows from `data_source_inventory` (product, product_version, protocol, transport).
- **CVE lookup (optional):**
- Prefer **offline or local** data (e.g. bundled JSON keyed by product+version, or optional SQLite/JSON DB updated periodically) to avoid mandatory external API and rate limits.
- If integrating **NVD API** or similar: make it **optional** (config flag, env var), rate-limited, and clearly documented; do not block reports if the service is down.
- **Protocol/transport rules:** Apply simple rules (e.g. SMB1 → recommend disable; TLS &lt; 1.2 → recommend upgrade; known EOL versions → recommend upgrade) from a small, maintainable rule set (config or code).
- **Mitigation and upgrade text:** Use **only public documentation**: vendor release notes, security advisories, NVD descriptions, and community how-tos. Do not invent steps; link to URLs when available. Tone: **professional and useful for IT and cybersecurity** (clear priority, impact, and action).
- **Output:** List of hardening recommendations (per target or per finding) with: severity, short summary, mitigation steps or doc link, and “next step” (e.g. “Upgrade to PostgreSQL 15.x; see <https://www.postgresql.org/support/versioning/>”).

---

## Report and next-steps guide

- **New Excel sheet: "Data source inventory"**

  Columns: Target name, Source type, Product, Product version, Protocol/API version, Transport security, Raw details (optional). One row per inventory record for the session.

- **New Excel sheet: "Hardening recommendations"**

  Columns: Target name, Product, Product version, Finding type, Identifier (CVE id or rule), Severity, Summary, Mitigation / next step, Doc URL. Sorted e.g. by severity then target. If no recommendations, sheet can be omitted or show a single row “No known issues identified for collected versions.”

- **Next-steps hardening guide (document):**
- Option A: A **section in the report** (e.g. “Report info” or a dedicated “Hardening summary” sheet) with a short narrative and top 5–10 actions.
- Option B: A **separate document** (e.g. `docs/hardening-guide.md` or generated `Hardening_next_steps.md` per run) that references the report and lists: (1) Data sources and versions found, (2) CVEs or protocol risks, (3) Recommended order of actions (e.g. critical first), (4) Links to public docs and how-tos.
- Recommendation: **Both** — a summary in the report (so everything is in one place) and an optional export or doc template for a standalone hardening checklist for IT/security.

---

## Implementation phases (to-dos)

### Phase 1: Data model and basic collection (SQL, MongoDB, Redis, REST/Power BI/Dataverse)

| #   | To-do                                                                                                                                                                                 | Status                                                                   |
| --- | ---------------------------------------------------------------------                                                                                                                 | ------                                                                   |
| 1.1 | Add `data_source_inventory` table and migration in `core/database.py`                                                                                                                 | ✅                                                                        |
| 1.2 | Add `LocalDBManager.save_data_source_inventory(...)` and wire to session                                                                                                              | ✅                                                                        |
| 1.3 | SQL connector: after connect, run dialect-specific version query (e.g. `SELECT version()`, `SELECT @@version`), get TLS from connection if available; call save_data_source_inventory | ✅                                                                        |
| 1.4 | MongoDB connector: run `buildInfo` or equivalent; call save_data_source_inventory                                                                                                     | ✅                                                                        |
| 1.5 | Redis connector: run `INFO server`, parse redis_version; call save_data_source_inventory                                                                                              | ✅                                                                        |
| 1.6 | Power BI / Dataverse / REST: record API version (from URL path or headers); call save_data_source_inventory                                                                           | ✅                                                                        |
| 1.7 | Report: add "Data source inventory" sheet from inventory table                                                                                                                        | ✅                                                                        |
| 1.8 | Tests: unit tests for new table and save; test that SQL/Mongo/Redis version is stored; report test for new sheet                                                                      | ✅ (unit coverage for SQL + connector inventory snapshots + report sheet) |
| 1.9 | Docs: USAGE/TECH_GUIDE and config (if any new keys) for inventory feature                                                                                                             | ✅                                                                        |

### Phase 2: Remaining connectors (SMB, Snowflake, SharePoint, WebDAV, NFS)

| #   | To-do                                                                                                       | Status |
| --- | ---------------------------------------------------------------------                                       | ------ |
| 2.1 | Snowflake connector: session/version query; save_data_source_inventory                                      | ⬜      |
| 2.2 | SMB connector: detect SMB dialect (2.0/2.1/3.0/3.1.1) if smbprotocol exposes it; save_data_source_inventory | ⬜      |
| 2.3 | SharePoint / WebDAV: Server header or API version; save_data_source_inventory                               | ⬜      |
| 2.4 | NFS: protocol version (NFSv3/NFSv4) from config or connection if available; save_data_source_inventory      | ⬜      |
| 2.5 | Tests and docs for new connectors’ inventory                                                                | ⬜      |

### Phase 3: CVE lookup and hardening recommendations

| #   | To-do                                                                                                                                          | Status |
| --- | ---------------------------------------------------------------------                                                                          | ------ |
| 3.1 | Define rule set for deprecated/weak protocol (SMB1, TLS &lt; 1.2, etc.) and optional CVE data source (local JSON/DB or optional NVD)           | ⬜      |
| 3.2 | Implement hardening engine: from inventory rows produce recommendation rows (finding_type, identifier, severity, summary, mitigation, doc_url) | ⬜      |
| 3.3 | Persist hardening findings (table or report-time only) and add "Hardening recommendations" sheet to report                                     | ⬜      |
| 3.4 | Mitigation text and doc URLs from public docs only; document data sources (NVD, vendor advisories) in SECURITY or dedicated doc                | ⬜      |
| 3.5 | Tests for rules and report sheet; optional integration test for CVE lookup (mock or small fixture)                                             | ⬜      |
| 3.6 | Docs: hardening feature in USAGE and TECH_GUIDE; operator-facing “next steps” explanation                                                      | ⬜      |

### Phase 4: Next-steps hardening guide and polish

| #   | To-do                                                                                                                                         | Status |
| --- | ---------------------------------------------------------------------                                                                         | ------ |
| 4.1 | Add "Hardening summary" section or sheet in report (top actions, links)                                                                       | ⬜      |
| 4.2 | Optional: generate or document template for standalone `Hardening_next_steps.md` (or similar) per run                                         | ⬜      |
| 4.3 | docs/hardening-guide.md (or section in SECURITY.md): how the app uses versions, CVEs, and public docs; how to interpret report and next steps | ⬜      |
| 4.4 | Final regression: full test suite passes; mark plan steps done in PLANS_TODO.md                                                               | ⬜      |

---

## Dependencies and constraints

- **No secrets in inventory:** Do not store passwords, tokens, or connection strings in `data_source_inventory` or `raw_details`; only product/version/protocol/transport and non-sensitive identifiers.
- **Optional CVE:** If CVE lookup is external (e.g. NVD), it must be **optional** and **non-blocking**; report must generate even when CVE service is unavailable.
- **Public docs only:** All mitigation and upgrade guidance must reference **public** documentation or how-tos; no internal or proprietary content.
- **Backward compatibility:** Existing config, connectors, and report layout remain valid; new sheets and tables are additive. Old sessions without inventory simply show empty or omitted inventory/hardening sheets.

---

## Conflict and placement in roadmap

- This plan is **additive** and does not conflict with Security hardening, Secrets vault, Version check & self-upgrade, Compliance samples, Compressed files, or Dashboard i18n.
- **Recommended placement:** After **Security hardening** and **Secrets vault Phase A** (so config and base security are in place), and after **Additional compliance samples** (so report structure is stable). Can run in parallel with **Compressed files** or **Secrets Phase B** if desired; sequence in PLANS_TODO.md will reflect this.

---

## Last updated with plan file. Update PLANS_TODO.md when completing or adding to-dos.
