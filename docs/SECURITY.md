# Security: fixes, tests, and technician guidance

**Português (Brasil):** [security.pt_BR.md](security.pt_BR.md)

This document summarizes **critical and high-severity security measures** implemented in the application, the **regression tests** that guard them, and **recommendations for technicians** so you know what to keep an eye out for when configuring and operating the audit tool.

For full policy, supported versions, dependency audit, and how to report vulnerabilities, see **[SECURITY.md](../SECURITY.md)** ([pt-BR](../SECURITY.pt_BR.md)).

---

## What is protected (and how)

| Area                                        | Protection                                                                                                                                                                                                                                                                                                                                                                                       | Regression tests                                                                                                                                                                |
| ------                                      | ------------                                                                                                                                                                                                                                                                                                                                                                                     | ------------------                                                                                                                                                              |
| **Credential injection in connection URLs** | Database user and password are **URL-encoded** when building connection strings (SQL connector, MongoDB connector). Passwords containing `@`, `:`, `/`, or `#` no longer break URL parsing or get misinterpreted as host/path.                                                                                                                                                                   | `test_sql_connector_build_url_encodes_password_special_chars`, `test_sql_connector_build_url_encodes_user_with_at`, `test_mongodb_connector_uri_encodes_password_special_chars` |
| **SQL injection**                           | Table/column names in dynamic SQL come from the database inspector (discover), not from user input. Identifiers are escaped per dialect (double-quote or backtick). `session_id` is only used via ORM/parameterized queries.                                                                                                                                                                     | `test_sqlite_identifier_escaping_prevents_second_statement`, `test_sql_connector_sample_uses_escaped_identifiers_sqlite`, `test_database_filters_use_orm_not_raw_sql`           |
| **Path traversal**                          | `session_id` in API paths is validated with a strict pattern (alphanumeric and underscore, 12–64 characters) before use in file paths. Invalid values return HTTP 400.                                                                                                                                                                                                                           | `test_session_id_validation_rejects_dangerous_patterns`                                                                                                                         |
| **Config / YAML**                           | Config is loaded with `yaml.safe_load` only (no arbitrary Python object deserialization). Malicious YAML tags (e.g. code execution) are rejected.                                                                                                                                                                                                                                                | `test_config_save_uses_safe_load`, `test_config_loader_uses_safe_load_not_load`                                                                                                 |
| **Config endpoint exposure**                | When `api.require_api_key` is true, GET `/config` returns **401** without a valid API key, so the raw config file (which may contain database passwords and secrets) is not exposed to unauthenticated users.                                                                                                                                                                                    | `test_config_endpoint_requires_api_key_when_required`                                                                                                                           |
| **Report and heatmap access**               | Endpoints that return reports or heatmaps (`/report`, `/heatmap`, `/reports/{session_id}`, `/heatmap/{session_id}`) validate `session_id` format first (strict pattern, 12–64 chars). Invalid IDs return **400**; unknown or missing sessions return **404**. No distinction is made between “invalid ID” and “session not found” for unknown IDs, avoiding enumeration and information leakage. | Same as path traversal (`_validate_session_id`); report/heatmap handlers return 404 when no data.                                                                               |
| **Audit text logs (`audit_*.log`)**         | After config normalization, each target gets a unique **`audit_log_name`** (sanitized from `name`) so log lines never collide. Filesystem **Connected** and **Finding** lines avoid raw absolute host paths: scan roots use `folder?8-hex`, file paths use POSIX paths **relative to the resolved scan root**, or `audit_log_name?12-hex` when a file resolves **outside** that root (e.g. symlink). The SQLite/Excel report remains the authoritative evidence; see **docs/USAGE.md** (audit log format). | `tests/test_audit_log_display.py`, `tests/test_database.py` (`test_normalize_config_sets_unique_audit_log_names`) |

All of the above tests live in **`tests/test_security.py`** (plus the audit-log tests above). Running `pytest tests/test_security.py tests/test_audit_log_display.py -v` regularly (e.g. in CI) helps ensure these protections are not accidentally removed.

---

## Recommendations for technicians

- **Tenant and technician validation:** Values for tenant and technician (scan start body, session PATCH, config-driven scan) are validated for maximum length and allowed characters (printable, no control characters), then trimmed and sanitized before storage; invalid or oversized input is rejected or truncated so reports and the dashboard never display unsanitized values.
- **Request body size limit:** The API rejects requests whose body exceeds **1 MB** (e.g. POST `/config`, POST `/scan`, POST `/scan_database`) with **HTTP 413 Payload Too Large** to reduce DoS via huge payloads.
- **Logging policy:** API keys, passwords, and connection strings are never written to logs; failure details and exception messages are redacted (e.g. connection URLs and `password=` / `api_key=`-style values masked) before being logged.
- **Audit log vs report:** Text logs (`audit_YYYYMMDD.log`) use **sanitized, unique** per-target labels (`audit_log_name`) and **redacted** filesystem locations as described in **docs/USAGE.md**. Do not treat the log’s third column as a verbatim OS path when it shows `name?hex`; use the database/report row for the exact stored path. If the `target?hash` form for out-of-root files is too opaque in your environment, a future option could switch to **filename-only** plus hash—file an issue if you need that operational toggle.
- **Passwords with special characters:** You can safely use database or MongoDB passwords that contain `@`, `:`, `/`, or `#`. The application encodes them when building connection URLs. No extra configuration is required.
- **Protecting the config in the UI:** The **Configuration** page (GET `/config`) shows and allows editing the main config file, which may contain credentials. If the API is exposed to untrusted users or networks, set **`api.require_api_key: true`** and provide a strong API key (or `api.api_key_from_env`). Then only requests that send a valid **X-API-Key** or **Authorization: Bearer** can access `/config`.
- **API key vs /health:** **`GET /health`** stays **unauthenticated** (liveness for orchestrators). Other routes require the key when enabled. **401** = wrong/missing key; **503** = `require_api_key` true but no key resolved; **`main.py --web` exits 2** before listen in that case. See root **[SECURITY.md](../SECURITY.md)** § Optional API key, **[USAGE.md](USAGE.md)** (Authentication), and **[SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.md](ops/SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.md)** ([pt-BR](ops/SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.pt_BR.md)).
- **Where config is stored:** The config file path is set at startup (default `config.yaml` or `CONFIG_PATH`). Ensure the file and directory permissions restrict read/write to trusted users only.
- **Session IDs in URLs:** The API uses `session_id` in paths (e.g. `/reports/{session_id}`). Only values that match the allowed pattern (alphanumeric and underscore, 12–64 chars) are accepted; anything else returns 400. This prevents path traversal via crafted session IDs.
- **Operator notifications (webhooks):** Optional `notifications` POSTs scan summaries to Slack, Teams, Telegram, or a generic URL. Treat webhook URLs and bot tokens as secrets; prefer `${ENV_VAR}` in YAML or env-only wiring. See **`docs/USAGE.md`** (§5.1) and the policy note in root **`SECURITY.md`**. Outbound sends retry on transient failures; they do not replace TLS or network policy.
- **Deployment:** When the dashboard or API is exposed to the internet or untrusted networks, run behind a **reverse proxy** with **TLS** and proper authentication. Use the optional API key and rate limiting as an extra layer; see **SECURITY.md** and **docs/deploy/DEPLOY.md** (Security and hardening).
- **Report and heatmap downloads:** Report and heatmap endpoints only return data for a **validated** `session_id` (format check first). Invalid format returns 400; valid format but unknown or missing session returns 404. This design avoids session enumeration and information leakage (no 403 vs 404 distinction for unknown sessions).

---

## Incident Response Philosophy

Data Boar is a tool for detecting personal and sensitive data. The standard for how it handles its own repository must be at least as rigorous as what it recommends to customers.

We do not claim a perfect record; we claim a deterministic response.

When a hygiene incident occurred in the project's history, the response was:

1. **Find:** full-history audit via `scripts/pii_history_guard.py --full-history` and a fresh-clone check via `scripts/pii-fresh-clone-audit.ps1` (Windows) or an empty-folder `git clone` per [docs/ops/PII_PUBLIC_TREE_OPERATOR_GUIDE.md](ops/PII_PUBLIC_TREE_OPERATOR_GUIDE.md).
2. **Fix:** history remediation via `git filter-repo`; prior Docker Hub tags deprecated; Golden Clean Slate published as **`v1.7.2-safe`** (verifiable on GitHub).
3. **Build:** layered deterministic guardrails:
   - `tests/test_pii_guard.py` — tracked-file patterns
   - `scripts/gatekeeper-audit.ps1` — staged-file gate against private operator seeds (Python port: issue #560)
   - `.pre-commit-config.yaml` — hooks on every commit
   - `scripts/pii_history_guard.py` — branch anti-recurrence gate (`origin/main..HEAD`)
4. **Verify:** tiered cadence (weekly / monthly / quarterly) with mandatory manual review before marking SAFE — [docs/ops/PII_PUBLIC_TREE_OPERATOR_GUIDE.md](ops/PII_PUBLIC_TREE_OPERATOR_GUIDE.md).
5. **Govern:** [ADR-0018](adr/ADR-0018-pii-anti-recurrence-guardrails-for-tracked-files-and-branch-history.md) and [ADR-0019](adr/ADR-0019-pii-verification-cadence-and-manual-review-gate.md) are permanent architectural decisions.

The public **`v1.7.2-safe`** tag exists so due-diligence readers can verify the narrative independently. Finding a sensitivity incident and responding with durable, test-backed controls is a stronger trust signal than claiming the incident never happened.

**For customers:** the same discipline governs how the tool handles your data during a scan — **metadata-only findings**, no exfiltration, **Audit Trail** per session, configurable sampling bounds. See [COMPLIANCE_FRAMEWORKS.md](COMPLIANCE_FRAMEWORKS.md) and [USAGE.md](USAGE.md) (Privacy and data handling).

---

## Related documentation

- **Documentation index** (all topics, both languages): [README.md](README.md) · [README.pt_BR.md](README.pt_BR.md).
- **SECURITY.md** ([pt-BR](../SECURITY.pt_BR.md)) — Security policy, headers, optional API key, reporting vulnerabilities.
- **docs/deploy/DEPLOY.md** ([pt-BR](deploy/DEPLOY.pt_BR.md)) — Deployment and hardening (Docker, Kubernetes, reverse proxy).
- **docs/USAGE.md** ([pt-BR](USAGE.pt_BR.md)) — CLI, API, and configuration (including `api.require_api_key`).
- **Man pages:** `man data_boar` or `man lgpd_crawler` (section 1), `man 5 data_boar` or `man 5 lgpd_crawler` (section 5) — include brief security and credential notes.
