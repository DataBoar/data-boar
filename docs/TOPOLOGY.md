# Application topology

**Português (Brasil):** [TOPOLOGY.pt_BR.md](TOPOLOGY.pt_BR.md)

Textual description of modules, classes, and main functions and how they connect.

---

## Entry points

- **main.py** — CLI: `main()` parses `--config`, `--web`, `--port`, optional `--tenant`, `--technician`; loads config via `config.loader.load_config`; if not `--web`, creates `AuditEngine(config)`, runs `start_audit(tenant_name=..., technician_name=...)`, then `generate_final_reports()`; if `--web`, runs uvicorn with `api.routes.app` on given port.
- **api/routes.py** — FastAPI app: startup loads config and creates `AuditEngine`. API routes: POST `/scan` (optional body `{ "tenant": "...", "technician": "..." }`), `/start`; GET `/status`, `/report`, `/list`; GET `/reports/{session_id}`; PATCH `/sessions/{session_id}` (body `{ "tenant": "..." }` to set/clear tenant), PATCH `/sessions/{session_id}/technician` (body `{ "technician": "..." }` to set/clear technician). POST `/scan_database` accepts optional `tenant` and `technician`. Web dashboard (Jinja2): GET `/` (dashboard with optional tenant/technician inputs and progress chart), GET `/reports` (reports list with tenant/technician columns), GET `/config`, POST `/config` (config editor). Static: `/static` → `api/static`.

---

## Config

- **config/loader.py**
- `load_config(path)` — Load YAML or JSON from path; return dict.
- `normalize_config(data)` — Normalize to unified schema: `targets[]`, `file_scan` (extensions, recursive, scan_sqlite_as_db, sample_limit), `report`, `api`, `ml_patterns_file`, `regex_overrides_file`, `sqlite_path`, `scan.max_workers`. Legacy `databases` + `file_scan.directories` converted to `targets`.

---

## Core

- **core/session.py**
- `new_session_id()` — Return UUID4 hex (12 chars) + timestamp string for scan session. **Future:** consider RFC 9562 UUID v7 for time-ordered session ids (see module docstring and `PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md`); does not replace hash/signing integrity.

- **core/database.py**
- **ScanSession** — SQLAlchemy model: id, session_id, started_at, finished_at, status, tenant_name (optional customer/tenant), technician_name (optional operator).
- **DatabaseFinding** — session_id, target_name, server_ip, engine_details, schema_name, table_name, column_name, data_type, sensitivity_level, pattern_detected, norm_tag, ml_confidence, created_at.
- **FilesystemFinding** — session_id, target_name, path, file_name, data_type, sensitivity_level, pattern_detected, norm_tag, ml_confidence, created_at.
- **ScanFailure** — session_id, target_name, reason, details, created_at.
- **LocalDBManager** — `__init__(db_path)` (migrates adding tenant_name/technician_name if missing), `set_current_session_id(sid)`, `current_session_id`, `save_finding(source_type, **kwargs)`, `save_failure(target_name, reason, details)`, `get_findings(session_id)`, `list_sessions()` (includes tenant_name, technician_name, scan_failures count), `get_previous_session(session_id)`, `get_previous_sessions(session_id, limit=3)` (for trend comparison), `create_session_record(session_id, tenant_name=None, technician_name=None)`, `update_session_tenant(session_id, tenant_name)`, `update_session_technician(session_id, technician_name)`, `finish_session(session_id, status)`, `get_current_findings_count()`.

- **core/detector.py**
- **SensitivityDetector** — `__init__(regex_overrides_path, ml_patterns_path)`; loads regex (built-in + overrides) and ML patterns; `analyze(column_name, sample_text)` → (sensitivity_level, pattern_detected, norm_tag, confidence). Uses TF-IDF + RandomForest when ML file or defaults available.
- Helpers: `_load_regex_overrides(path)`, `_load_ml_patterns(path)`.

- **core/scanner.py**
- **DataScanner** — `__init__(regex_overrides_path, ml_patterns_path)`; wraps `SensitivityDetector`. `scan_column(column_name, sample_content)` → dict (sensitivity_level, pattern_detected, norm_tag, ml_confidence); `scan_file_content(content, file_path)` → same dict or None; `analyze_data(column_name, sample_content)` → (level, pattern) for backward compatibility.

- **core/connector_registry.py**
- `register(connector_type, connector_class, required_keys)` — Register connector class.
- `get_connector(connector_type)` — Return (class, required_keys).
- `list_connector_types()` — List registered types.
- `connector_for_target(target)` — From target type/driver resolve (connector_class, required_keys).

- **core/engine.py**
- **AuditEngine** — `__init__(config, db_path)`; holds `db_manager` (LocalDBManager), `scanner` (DataScanner). `start_audit()` → session_id (creates session, runs `_run_audit_targets()`); `_run_audit_targets()` runs each target via registry (sequential or parallel); `_run_target(target)` resolves connector and calls `connector.run()`. `generate_final_reports(session_id)` → report path via `report.generator.generate_report`; if `learned_patterns.enabled`, also calls `core.learned_patterns.write_learned_patterns()`. Properties: `is_running`, `get_current_findings_count()`, `get_last_report_path()`.
- Imports connectors so they register (sql_connector, filesystem_connector, optional mongodb_connector, redis_connector).

- **core/learned_patterns.py**
- `collect_learned_entries(db_rows, fs_rows, min_sensitivity=HIGH, min_confidence=70, ...)` — From findings build list of { text, label, pattern_detected, norm_tag, count }; filters by sensitivity rank, confidence, term length, require_pattern (skip GENERAL), exclude_generic (id, name, key, …).
- `write_learned_patterns(db_manager, session_id, config)` — If `config.learned_patterns.enabled`, get findings, collect entries, optionally merge with existing output file, write YAML (format compatible with ml_patterns_file). Returns output path or None.

---

## Connectors

- **connectors/sql_connector.py**
- **connectors/sql_sampling.py** — `SamplingManager` orchestrates dialect-specific **column** sample `SELECT`s (non-null filter before row cap); `SqlColumnSampleQueryBuilder.build` delegates to the same plan for backward compatibility. `resolve_sql_sample_limit` applies optional env **`DATA_BOAR_SQL_SAMPLE_LIMIT`** (clamp **1..10000**). **`core/sampling_policy.py`** resolves optional YAML **`sql_sampling.overrides`** (per-target / per-table / `fnmatch` patterns) before that clamp. Optional `TableSamplingMetadata` (e.g. estimated row count) adjusts **strategy labels** today and will gate `TABLESAMPLE`/prudent modes later ([ADR 0043](adr/ADR-0043-sql-column-sampling-non-null-and-strategy-hook.md); operator notes in [USAGE.md](USAGE.md)).
- **SQLConnector** — `__init__(target_config, scanner, db_manager, sample_limit)`; `connect()`, `close()`, `discover()` → list of {schema, table, columns}; `sample(schema, table, column_name)` → string (no persistence; asks **`SamplingManager`** for a `ColumnSamplePlan`, logs **strategy** once per table at INFO); `run()` — connect, discover, sample each column, run scanner, save_finding or save_failure. Registered for postgresql, mysql, mariadb, sqlite, mssql, oracle.

- **connectors/filesystem_connector.py**
- **FilesystemConnector** — `__init__(target_config, scanner, db_manager, extensions, scan_sqlite_as_db=True, sample_limit=5)`; `run()` — walk path (recursive or not), check `os.access(path, R_OK)`. For `.sqlite`/`.sqlite3`/`.db` when `scan_sqlite_as_db` is True: open as DB, discover tables/columns, sample and detect, save as filesystem_findings (file_name encodes `file.db | table.column`). Otherwise read text via `_read_text_sample()`, run scanner, save_finding or save_failure. Registered for filesystem.
- `_read_text_sample(path, ext, max_chars)` — Extract text from txt/csv/pdf/docx/odt/ods/odp/xlsx/pptx/msg/eml (pypdf, docx, pandas, odfpy, extract-msg, etc.).
- `_scan_sqlite_file_as_db(file_path, scanner, sample_limit)` — Open SQLite file, discover + sample + detect; return list of finding dicts for filesystem save_finding.

- **connectors/mongodb_connector.py** (optional)
- **MongoDBConnector** — connect, list collections, sample documents, run scanner on field names + combined sample text, save_finding. Registered for mongodb when pymongo is installed.

- **connectors/redis_connector.py** (optional)
- **RedisConnector** — connect, SCAN keys, run scanner on key names, save_finding. Registered for redis when redis package is installed.

- **connectors/rest_connector.py**
- **RESTConnector** — `__init__(target_config, scanner, db_manager, sample_limit=5)`; `connect()` builds httpx client and applies auth from `target["auth"]` (basic, bearer, oauth2_client, custom headers); `run()` GETs each path in `paths` or from `discover_url`, parses JSON, flattens keys/sample values, runs scanner, save_finding as filesystem (file_name e.g. `GET /path | field`). Registered for `api` and `rest` when httpx is available.
- Auth: **basic** (username/password), **bearer** (token or token_from_env), **oauth2_client** (token_url, client_id, client_secret, scope), **custom** (headers). Target-level `user`/`pass` used as basic when no `auth` block.

- **connectors/smb_connector.py** (optional: smbprotocol)
- **SMBConnector** — Connect to SMB/CIFS by host (FQDN or IP), share, path; credentials user, pass, optional domain. List files (smbclient.walk), download to temp, _read_text_sample + scanner; SQLite-as-DB when scan_sqlite_as_db. Registered for `smb` and `cifs`.

- **connectors/webdav_connector.py** (optional: webdavclient3)
- **WebDAVConnector** — base_url, user, pass, path; list recursively, download to temp, same scan as filesystem. Registered for `webdav`.

- **connectors/sharepoint_connector.py** (optional: requests_ntlm)
- **SharePointConnector** — site_url, path (server-relative folder), user, pass; NTLM or basic. REST GetFolderByServerRelativeUrl/Files, GetFileByServerRelativeUrl/$value, download to temp, scan. Registered for `sharepoint`.

- **connectors/nfs_connector.py**
- **NFSConnector** — path = local NFS mount point (user mounts first); host/export_path for reporting. Delegates to FilesystemConnector. Registered for `nfs`.

---

## Report

- **report/generator.py**
- `generate_report(db_manager, session_id, output_dir)` — Read `get_findings(session_id)` (database_findings, filesystem_findings, scan_failures); write Excel with **"Report info"** (Session ID, Started at, Tenant/Customer, Technician/Operator), "Database findings", "Filesystem findings", "Scan failures", "Recommendations", "Praise / existing controls" (if any), **"Trends - Session comparison"**, "Heatmap data"; call `_create_heatmap()` to save PNG; return Excel path.
- `_create_heatmap(db_rows, fs_rows, output_dir, session_id)` — Build pivot and seaborn heatmap, save PNG.
- `_praise_rows(db_rows, fs_rows)` — Rows where column/file name or pattern_detected suggests existing protections (encrypted, hash, tokenized, masked, etc.); written to "Praise / existing controls" sheet.
- `_trends_rows(db_manager, session_id, current_db, current_fs, current_fail, current_started_at)` — Compare this run with up to 3 previous runs (db_manager.get_previous_sessions(session_id, limit=3)); build rows: Metric, This run (count/date), Prev run 1/2/3 (count and date), Change (vs most recent previous), Note (aggregate insight: improvement, increase, or stable over last N runs). Written to "Trends - Session comparison" for DPO and security team.
- `_recommendations_rows(db_rows, fs_rows)` — Build list of recommendation dicts from unique pattern_detected/norm_tag.

---

## API

- **api/routes.py**
- FastAPI `app`; startup loads config and creates AuditEngine (singleton). Static files mounted at `/static` (api/static). Jinja2 templates from api/templates.
- **API:** `POST /scan`, `POST /start` — Create session_id, run `_run_audit_targets()` in background; return session_id. `POST /scan_database` — One-off scan of a single database (body: name, host, port, user, password, database, optional driver); starts in background, returns session_id. `GET /status` — running, current_session_id, findings_count. `GET /report` — Download last report file (or generate from last session). `GET /list` — List sessions (JSON). `GET /reports/{session_id}` — Regenerate report for session and return file.
- **Web dashboard (plan: REST + file download only, no WebSocket):** `GET /` — Dashboard page (scan status, quantity/quality stats, recent sessions, start-scan button; status polling when running). `GET /reports` — Reports list page (all sessions with download links). `GET /config` — Config editor (YAML textarea). `POST /config` — Save YAML to config file (validates, then reloads in-memory config/engine). Helpers: `_get_config_path()`, `_get_config_raw()`, `_save_config_yaml()`.

---

## Utils

- **utils/logger.py**
- `get_logger()` — Return unified logger (file audit_YYYYMMDD.log + console).
- `setup_live_logger()` — Alias for get_logger().
- `log_connection(target_name, target_type, location)` — Log successful connection.
- `log_finding(source_type, target_name, location, sensitivity, pattern)` — Log and call notify_violation.
- `notify_violation(message)` — Log and print [ALERT] to console.

---

## Data flow (summary)

1. **Config** → config/loader → normalized dict with targets, file_scan, report, api, sqlite_path.
1. **Engine** → core/engine creates LocalDBManager, DataScanner; for each target, connector_for_target → connector.run(). For filesystem targets, passes file_scan.scan_sqlite_as_db and sample_limit to FilesystemConnector.
1. **Connectors** → connect, discover (and sample for DB); for filesystem, .sqlite/.db files are optionally opened as SQLite DBs and scanned (discover + sample + detect), results saved as filesystem_findings; other files use _read_text_sample and scanner; logger.log_connection / log_finding.
1. **Report** → report/generator reads SQLite via db_manager.get_findings(session_id), writes Excel + heatmap, returns path.
1. **API** → routes use same AuditEngine; /scan starts background _run_audit_targets; /report and /reports/{id} call generate_final_reports.

---

## Dependency direction (no cycles)

- config.loader — no project imports.
- core.session — no project imports.
- core.database — no project imports.
- core.detector — optional yaml/json, sklearn, pandas.
- core.scanner — core.detector.
- core.connector_registry — none.
- connectors.* — core.connector_registry, core.database (via db_manager), core.scanner (or scanner), utils.logger.
- core.engine — core.connector_registry, core.database, core.scanner, core.session; imports connectors.
- report.generator — core.database (LocalDBManager usage), pandas, openpyxl, matplotlib/seaborn.
- api.routes — config.loader, core.engine.
- main — config.loader, core.engine, api.routes (for app), uvicorn.

**Documentation index** (all topics, both languages): [README.md](README.md) · [README.pt_BR.md](README.pt_BR.md).
