# Plan: Rate limiting and concurrency safeguards

<!-- plans-hub-summary: Rate limits and concurrency caps so discovery scans cannot overwhelm customer networks; behaviour and docs stay aligned. -->

Goal: Add configurable rate limiting and concurrency safeguards so the Data Boar scan engine cannot accidentally DoS customer networks while keeping existing behaviour and docs in sync.

## Goals

- Add **configurable rate limiting** for scan-triggering operations so the app cannot easily DoS customer networks/servers (even if a technician mis-clicks or scripts repeated scans).
- Add **safe bounds on parallelism** (workers/max concurrent scans) without removing existing capabilities.
- Keep **current behaviour as the default** (or very close), with rate limiting as an **opt-in or gentle default** to avoid regressions.
- Keep **CLI, API, docs, man pages, and help page** in sync; all existing and future tests must pass with `-W error`.

## High-level design (implemented)

- Introduce a small **rate-limiting layer** in the API/engine that:
- Tracks **recent scan sessions** (start times, status) via the existing session DB (`core/database.py`).
- Enforces a **global maximum number of concurrent scans** (config: `rate_limit.max_concurrent_scans`).
- Enforces a **minimum interval between scan starts** (`rate_limit.min_interval_seconds`) to prevent rapid-fire restarts.
- Keep CLI one-shot behaviour essentially unchanged, but reuse the same safeguards when reasonable (e.g. warnings when limits would be exceeded).
- Expose rate-limiting and safety configs in the main config file (YAML/JSON) under a `rate_limit` section, with environment-variable overrides.

## Key changes by area

### 1. Configuration model (`config/loader.py`, docs)

- **New `rate_limit` section in config schema**:
- `rate_limit.enabled: bool` (default `true`, with sane defaults).
- `rate_limit.max_concurrent_scans: int` (default `1`, clamped to `≥ 1`).
- `rate_limit.min_interval_seconds: int` (default `0`, clamped to `≥ 0`).
- `rate_limit.grace_for_running_status: int` (optional, seconds; treated as an upper bound for the effective interval, clamped to `≥ 0`).
- Support **env overrides** in the loader:
- `RATE_LIMIT_ENABLED`
- `RATE_LIMIT_MAX_CONCURRENT_SCANS`
- `RATE_LIMIT_MIN_INTERVAL_SECONDS`
- `RATE_LIMIT_GRACE_FOR_RUNNING_STATUS`
- Normalize and validate this block (similar pattern to `detection` config).

### 2. Persistence and state for rate limiting (`core/database.py`)

- Reuse existing `scan_sessions` table in SQLite.
- Add helpers on the DB manager:
- `get_running_sessions_count()` – number of sessions with `status == "running"`.
- `get_last_session()` – most recent session, returning `session_id`, `started_at`, `status`.

### 3. Enforcement on API endpoints (`api/routes.py`)

- Rate limiting applies to **scan-triggering endpoints**:
- `POST /scan` and `/start` (same handler).
- `POST /scan_database`.
- For each incoming request:
- Look up normalized `rate_limit` from config.
- Check **current count of running scans**; if `≥ max_concurrent_scans`, return HTTP 429 with a structured JSON payload (`error: "rate_limited"`, `reason`, `running_scans`, `max_concurrent_scans`, `source`).
- Check **time since last scan started**; if `< min_interval_seconds` (or effective interval when `grace_for_running_status` is higher), return HTTP 429 with details and `retry_after_seconds`.
- GET endpoints (`/reports`, `/heatmap`, `/logs`, `/status`, `/about`, `/health`) remain **unlimited** to avoid impacting read-only operations.

### 4. CLI behaviour (`main.py`, `core/engine.py`)

- CLI **one-shot scan** remains primary use; it is not blocked by rate limits.
- When `rate_limit.enabled` is true, the CLI issues **warnings** based on the same logic used by the API:
- Warns when running scans `≥ max_concurrent_scans`.
- Warns when the last scan started less than `min_interval_seconds` ago.
- The CLI still proceeds with the scan (no exit code change), preserving existing behaviour.

### 5. Worker and parallelism safeguards

- `scan.max_workers` in `config/loader.py` is now clamped:
- Minimum `1`.
- Maximum `32` (hard cap to avoid accidental huge parallelism).
- Docs recommend keeping `max_workers` small in highly sensitive or resource-limited environments and explain its relationship with `rate_limit.max_concurrent_scans`.

### 6. Tests

- **DB helpers:** new tests in `tests/test_database.py` to cover:
- `test_running_sessions_count_and_last_session`
- `test_normalize_config_rate_limit_and_scan_max_workers`
- **API behaviour:** `tests/test_rate_limit_api.py` covers:
- `test_rate_limit_blocks_when_max_concurrent_reached`
- `test_rate_limit_blocks_when_min_interval_not_elapsed`
- `test_rate_limit_disabled_by_default_for_legacy_configs`
- Existing tests (e.g. `test_post_scan_triggers_audit_using_config` and API key tests) remain valid with defaults.

### 7. Documentation and man/help pages

- **README.md / README.pt_BR.md**: mention rate limiting and link to usage docs and VERSIONING docs for where the version lives.
- **USAGE docs (EN/PT-BR)**: extended configuration section to describe:
- `rate_limit.enabled`
- `rate_limit.max_concurrent_scans`
- `rate_limit.min_interval_seconds`
- `rate_limit.grace_for_running_status`
- Env overrides for these keys.
- **Man pages**:
- `docs/lgpd_crawler.1`: references configuration-driven rate limiting and points at USAGE/SECURITY.
- `docs/lgpd_crawler.5`: documents the `rate_limit` section in the config topology.
- **Help page** (`api/templates/help.html`): mentions sensitivity detection, recommendations, and points to USAGE/README; may be extended further for rate-limit details if desired.

## Todos and status

1. Add `rate_limit` configuration support in `config/loader.py` (with env overrides) and document it. **Status:** ✅ Done.
1. Implement DB-level helpers to query running/last sessions for rate limiting. **Status:** ✅ Done.
1. Enforce rate limiting in `api/routes.py` for `/scan`, `/start`, `/scan_database` (no impact on read-only endpoints). **Status:** ✅ Done.
1. Decide and implement CLI interaction with rate limits (reject vs warn) and document the decision. **Status:** ✅ Done (implemented as warnings only).
1. Add bounds and documentation for `scan.max_workers` to avoid extreme values when rate limiting is on. **Status:** ✅ Done.
1. Write unit tests for the new rate-limit behaviour and ensure all existing tests still pass. **Status:** ✅ Done (full suite passes with `uv run pytest tests/ -v -W error`).
1. Update README (EN/PT-BR), USAGE (EN/PT-BR), man pages (1 and 5), and `help.html` to describe rate limiting and keep docs in sync. **Status:** ✅ Done (can be refined further over time as needed).
