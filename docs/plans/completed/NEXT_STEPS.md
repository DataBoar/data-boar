# Next Steps (archived implementation checklist)

*This document is archived in [plans/completed/](.) as the implementation-plan checklist; all items are Done. For current plan status and open to-dos, see [../PLANS_TODO.md](../PLANS_TODO.md).*

*Historical note: the original working title referred to an “LGPD audit solution” era; the product scope is now multi-framework discovery and mapping (see root README and USAGE).*

Plan of next steps based on the [implementation plan](../../.cursor/plans/lgpd_audit_solution_full_implementation_4a673b9e.plan.md) and current codebase.

---

## 1. Status vs plan

| Plan item                          | Status   | Notes                                                                                                 |
| ---                                | ---      | ---                                                                                                   |
| config/loader.py                   | Done     | Unified YAML/JSON, normalized schema                                                                  |
| core/session.py                    | Done     | UUID + timestamp                                                                                      |
| core/database.py                   | Done     | Single SQLite, 4 tables, LocalDBManager                                                               |
| core/detector.py                   | Done     | Regex + ML from config                                                                                |
| core/scanner.py                    | Done     | Uses detector only                                                                                    |
| core/connector_registry.py         | Done     | Registry + connector_for_target                                                                       |
| core/engine.py                     | Done     | start_audit, generate_final_reports, parallel/sequential                                              |
| connectors/sql_connector.py        | Done     | Discover + sample, Oracle/MSSQL/MySQL/Postgres/etc.                                                   |
| connectors/filesystem_connector.py | Done     | Permission check, recursive, many extensions                                                          |
| connectors/mongodb_connector.py    | Done     | Optional, pymongo                                                                                     |
| connectors/redis_connector.py      | Done     | Optional, redis                                                                                       |
| report/generator.py                | Done     | Excel + heatmap, DB/FS/failures/recommendations                                                       |
| api/routes.py                      | Done     | /scan, /start, /status, /report, /list, /reports/{id}; GET /, /reports, /config (dashboard)           |
| Web dashboard (frontend)           | Done     | GET / dashboard, GET /reports list, GET/POST /config editor; Jinja2 + static; no WebSocket (per plan) |
| main.py                            | Done     | --config, --web, --port 8088                                                                          |
| utils/logger.py                    | Done     | Unified logger, log_finding, notify_violation                                                         |
| README.md                          | Done     | Install, config, run, DBs, file types                                                                 |
| TOPOLOGY.md                        | Done     | Module/class/function topology                                                                        |
| config.yaml                        | Done     | Unified shape, DB targets (commented), file_scan                                                      |
| pyproject.toml                     | Done     | requires-python 3.12+, optional nosql/bigdata                                                         |
| requirements.txt                   | In place | Keep in sync with pyproject.toml                                                                      |

---

## 2. Recommended next steps (in order)

### 2.1 Consolidate legacy code and tests — Done

- **run.py** – *(removed from repo; historical)* was a thin wrapper; **`main.py`** is the only supported CLI entry point.
- **api/app.py** – Re-exports app from `api.routes` (single FastAPI app).
- **scanners/** – Deprecation README added; use `core.engine` + `connectors` + `report.generator`.
- **database/** – Deprecation README added; use `core.database` and `connectors`.
- **file_scan/**, **db/**, **report/sqlite_reporter.py**, **logging_custom/** – Legacy notes in place; tests use `config.loader`, `core.*`, `connectors`.
- **Tests** – Use `core.scanner`, `core.detector`, `config.loader`, `core.database`, `core.connector_registry`; no legacy imports.

---

### 2.2 Learned patterns (optional) — Done

- **Implemented:** Optional `learned_patterns` config; when report is generated, terms from HIGH (or MEDIUM) findings are collected (min_confidence, min_term_length, require_pattern, exclude_generic). Output YAML compatible with ml_patterns_file; README documents merge.
- (e.g. column names that scored HIGH). Document in README: "Merge entries from `learned_patterns.yaml` into `ml_patterns_file` for the next run."

---

### 2.3 Report "praise" for existing protections — Done

- **Implemented:** `report/generator.py` adds sheet "Praise / existing controls" when any finding has column name or pattern_detected containing protection keywords (encrypted, hash, tokenized, masked, pseudonym, anon, redact, hmac, cipher). Rows list target, source, column/file, pattern, and indication.

---

### 2.4 Dependencies and security — Done

- **Done:** README has "Dependencies and security" with `uv pip compile pyproject.toml -o requirements.txt` and `uv pip audit`. `requirements.txt` regenerated from pyproject.toml.

---

### 2.5 Optional connectors (BigData / APIs) — Done

- **Implemented:** REST/API connector (`connectors/rest_connector.py`) with auth: basic, bearer (token or token_from_env), oauth2_client, custom headers. Targets `type: api` or `type: rest`; README documents auth table and YAML examples. (Legacy plan: "Snowflake, REST/SOAP, SharePoint, Datalake, Graylog/Grafana as optional connectors; document config and install."
- **Next step:** Add optional connector modules (e.g. `connectors/snowflake_connector.py`, `connectors/rest_connector.py`) behind optional deps (`bigdata`, `api`), or at least document in README:
- How to add a target (type, driver, URL/credentials).
- Which packages to install (e.g. snowflake-connector-python, httpx/requests).
- Example config snippets for Snowflake, a REST API, etc.

**Deliverable:** Docs and, if desired, one or two optional connector stubs (e.g. Snowflake, generic REST).

---

### 2.6 SQLite / .db files in filesystem scan — Done

- **Implemented:** When `file_scan.scan_sqlite_as_db` is true (default), files with extension `.sqlite`, `.sqlite3`, or `.db` are opened with SQLAlchemy; discover tables/columns, sample rows, run detector; results saved as filesystem_findings with `file_name` encoding `path.db | table.column`. Config: `file_scan.scan_sqlite_as_db`, `file_scan.sample_limit`. "from filesystem" vs "from database" but content is analyzed.

**Deliverable:** Design (config flag or auto-detect) and implementation for "scan SQLite files as DBs" in the file connector.

---

### 2.7 TOPOLOGY and README upkeep — Done

- **Updated:** TOPOLOGY.md documents file_scan.scan_sqlite_as_db/sample_limit, FilesystemConnector SQLite-as-DB flow and `_scan_sqlite_file_as_db`, and API route `POST /scan_database`. README documents SQLite-as-DB behavior, `scan_sqlite_as_db`/`sample_limit`, and `/scan_database` route.

---

### 2.8 Web dashboard (frontend) — Done

- **Per plan:** "No WebSocket/streaming UI; REST API and file download only." The frontend is encoded accordingly: server-rendered HTML (Jinja2), no SPA, no separate build.
- **Implemented:**
- **Dashboard (GET /):** Scan status (running/idle, current session, findings count), quantity/quality summary (DB findings, FS findings, failures, total for last run), "Start scan" button, recent sessions table with download links. Status polls every 2s while a scan is running.
- **Reports (GET /reports):** List of all sessions (session ID, started/finished, status, DB/FS/failures) with "Download" link per session (uses existing `GET /reports/{session_id}`).
- **Configuration (GET /config, POST /config):** Edit scan configuration (YAML) in browser; save writes to config file (CONFIG_PATH or config.yaml) and reloads in-memory config/engine for next scan.
- **Artifacts:** `api/templates/` (base.html, dashboard.html, reports.html, config.html), `api/static/` (style.css, app.js), routes in `api/routes.py` (dashboard, config get/post, reports page, static mount). Documented in README and docs/USAGE.md.

---

## 3. File-level checklist (from plan)

| Path                                         | Action                                                | Status                         |
| ---                                          | ---                                                   | ---                            |
| pyproject.toml                               | Optional deps, CVE-safe pins                          | Done; refresh pins (2.4)       |
| requirements.txt                             | Sync with pyproject                                   | In place; formalize sync (2.4) |
| config/loader.py                             | Unified load                                          | Done                           |
| core/session.py                              | UUID + timestamp                                      | Done                           |
| core/database.py                             | Single schema                                         | Done                           |
| core/detector.py                             | Regex + ML from config                                | Done                           |
| core/scanner.py                              | Use detector only                                     | Done                           |
| core/connector_registry.py                   | Registry                                              | Done                           |
| core/engine.py                               | Full engine + reports                                 | Done                           |
| connectors/sql_connector.py                  | Discover + sample                                     | Done                           |
| connectors/filesystem_connector.py           | Permission, recursive, extensions, SQLite-as-DB (2.6) | Done                           |
| connectors/mongodb_connector.py              | Optional                                              | Done                           |
| connectors/redis_connector.py                | Optional                                              | Done                           |
| report/generator.py                          | Single Excel + heatmap + Praise sheet                 | Done (2.3)                     |
| api/routes.py                                | All routes + dashboard, config, reports pages         | Done                           |
| api/templates/*.html                         | Dashboard, reports list, config editor (Jinja2)       | Done (2.8)                     |
| api/static/*                                 | CSS, JS for dashboard                                 | Done (2.8)                     |
| main.py                                      | CLI + API                                             | Done                           |
| utils/logger.py                              | Unified logger                                        | Done                           |
| README.md                                    | Install, config, DBs, files                           | Done; keep updated (2.7)       |
| TOPOLOGY.md                                  | Full topology                                         | Done; keep updated (2.7)       |
| config.yaml                                  | Unified shape                                         | Done                           |
| run.py                                       | Removed — use `main.py` only                          | N/A (retired)                  |
| api/app.py                                   | Re-export routes                                      | Done (2.1)                     |
| scanners/*                                   | Deprecated                                            | README (2.1)                   |
| database/*                                   | Deprecated                                            | README (2.1)                   |
| file_scan/*, db/*, report/sqlite_reporter.py | Legacy                                                | Notes in place (2.1)           |
| logging_custom/*                             | Alias utils.logger                                    | Done (2.1)                     |
| tests/*                                      | Use core/config/connectors                            | Done (2.1)                     |

---

## 4. Out of scope (per plan)

- No storage of raw DB/file content; only metadata (and optional anonymized example).
- **SMB/NFS/WebDAV/SharePoint:** Now supported via optional connectors (type smb, cifs, nfs, webdav, sharepoint; install `.[shares]`). NFS requires a pre-mounted path.
- Deep learning is optional later; default remains regex + TF-IDF classifier.
- No WebSocket/streaming UI; REST API and file download only. The web dashboard (2.8) follows this: server-rendered pages (Jinja2) consuming the same REST API; no separate frontend stack or build.

---

## 5. Suggested order of work

1. **2.1** – Consolidate legacy code and fix tests (removes confusion and prevents regressions).
1. **2.4** – Dependencies and security (low risk, high value).
1. **2.7** – TOPOLOGY + README after 2.1 and 2.4.
1. **2.3** – Report "praise" (small, visible improvement).
1. **2.2** – Learned patterns (optional, when ML tuning is a priority).
1. **2.6** – SQLite-as-DB in file scan (optional, when .sqlite/.db scanning is required).
1. **2.5** – Optional BigData/API connectors (when a specific integration is needed).
1. **2.8** – Web dashboard (frontend): dashboard, reports list, config editor; server-rendered, REST + file download only — Done.
