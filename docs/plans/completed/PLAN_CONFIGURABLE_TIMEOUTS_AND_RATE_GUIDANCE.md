# Plan: Configurable timeouts for data soup access (sane defaults and recommendations)

**Status:** Done (Phases 1–4 complete)
**Synced with:** [PLANS_TODO.md](../PLANS_TODO.md) (central to-do list)

## When implementing steps: update docs and tests; then update PLANS_TODO.md and this file.

This plan adds **default timeout values** for data source (data soup) accesses, **configurable in the config file**, with **sane defaults** that account for busy or slow networks (e.g. during a database backup) without waiting forever, and without being so aggressive that the scanner causes DoS or worsens slowness by scanning "too much, too fast". It also documents **recommendations** for tuning and preventing timeouts and load.

---

## Goals

- **Configurable timeouts:** Introduce global (and optionally per-target) timeout settings in config so that:
- **Connect timeout:** Time allowed to establish a connection (TCP/SSL handshake, auth). Sane default so slow or congested networks can still connect without blocking indefinitely.
- **Read timeout:** Time allowed for each read/query/response after connection. Sane default so long-running queries or slow I/O (e.g. backup in progress) can complete without hanging the scan forever.
- **Sane defaults:** Choose values that:
- Do **not** wait forever (upper bound, e.g. 60–120 seconds for read so a single target cannot stall the whole run indefinitely).
- Do **not** be so short that normal busy/slow conditions cause false timeouts (e.g. connect ≥ 15–25 s, read ≥ 60–90 s for typical DB/API).
- Can be overridden per target or globally for backup windows or high-latency links.
- **Avoid DoS and "too much, too fast":** Rely on existing **rate_limit** (max_concurrent_scans, min_interval_seconds) and **scan.max_workers**; document that **lower parallelism and intervals** reduce load on targets and avoid amplifying slowness. Add short **recommendations** section in docs (and optionally in report or failure hint) so operators know how to prevent timeouts and avoid overloading the network.

---

## Current state

- **Config:** [config/loader.py](../config/loader.py) normalizes `scan` (max_workers), `rate_limit` (max_concurrent_scans, min_interval_seconds, etc.). There is **no** global `connect_timeout` or `read_timeout` today.
- **Connectors:**
- **REST:** [connectors/rest_connector.py](../connectors/rest_connector.py) uses `timeout = float(self.config.get("timeout", 30))` (per-target) and passes it to `httpx.Client(..., timeout=timeout)` (single value for both connect and read).
- **Power BI / Dataverse:** Hardcoded 30 s (token), 60 s (client); no config.
- **SQL:** [connectors/sql_connector.py](../connectors/sql_connector.py) uses `create_engine(url, pool_pre_ping=True)` with **no** connect_timeout or statement timeout.
- **MongoDB:** `MongoClient(uri)` with no timeout parameters.
- **Redis:** `redis.Redis(host=..., port=..., ...)` with no socket timeouts.
- **SMB / WebDAV / SharePoint:** Library-dependent; may or may not expose timeouts.
- **Failure handling:** [core/database.py](../core/database.py) `failure_hint("timeout")` already suggests increasing timeout and re-running during off-peak; report shows this when a target fails with reason `timeout`.

---

## Proposed config schema

Add a **top-level `timeouts`** section (or under `scan`) with global defaults. Connectors that support timeouts will read from config; per-target overrides remain possible where already present (e.g. REST `timeout`).

## Option A – under `scan` (fewer top-level keys):

```yaml
scan:
  max_workers: 1
  connect_timeout_seconds: 25   # time to establish connection (TCP, SSL, auth)
  read_timeout_seconds: 90     # time for each read/query/response after connected
```

## Option B – top-level `timeouts` (clear grouping):

```yaml
timeouts:
  connect_seconds: 25
  read_seconds: 90
```

**Per-target override:** Allow `target.connect_timeout`, `target.read_timeout`, or `target.timeout` (single value for both) so one slow database or API can have higher values without changing defaults. Normalizer merges: target timeout overrides global if set.

## Sane defaults (recommended):

| Setting                 | Default | Rationale                                                                                            |
| ----------------------- | ------- | ---------                                                                                            |
| connect_timeout_seconds | 25      | Enough for slow DNS, congested network, or busy server; not so long that a dead host blocks the run. |
| read_timeout_seconds    | 90      | Allows one slow query or response (e.g. during backup); avoids waiting indefinitely.                 |

If the network is known to be very slow (e.g. cross-region, backup window), operators can increase (e.g. connect 45, read 180). If targets are local and fast, they can decrease to fail faster.

---

## Connector wiring (summary)

| Connector                     | Connect timeout                                | Read timeout                                                                | Notes                                                                                           |
| -----------                   | -----------------------------------            | -----------------------------------                                         | -----                                                                                           |
| **SQL**                       | SQLAlchemy `connect_args`                      | Driver-dependent (e.g. statement_timeout) or same as connect for simplicity | PostgreSQL/MySQL: `connect_args={"connect_timeout": N}`; SQLite: `connect_args={"timeout": N}`. |
| **REST**                      | httpx `Timeout(connect=..., read=...)`         | Same                                                                        | Already has per-target `timeout`; can take global default and allow connect/read split.         |
| **Power BI / Dataverse**      | httpx client                                   | Same                                                                        | Use global defaults from config.                                                                |
| **MongoDB**                   | `serverSelectionTimeoutMS`, `connectTimeoutMS` | `socketTimeoutMS`                                                           | pymongo accepts these in MongoClient options.                                                   |
| **Redis**                     | `socket_connect_timeout`                       | `socket_timeout`                                                            | redis-py accepts these.                                                                         |
| **SMB / WebDAV / SharePoint** | If library supports                            | If library supports                                                         | Wire if available; else document "use global default where supported".                          |
| **Snowflake**                 | Connector params                               | Connector params                                                            | Snowflake connector has timeout options.                                                        |

Engine or connector factory must receive the normalized config (with default timeouts) so each connector can read `config.get("timeouts", {}).get("connect_seconds", 25)` (or from `scan`) and, for per-target, `target.get("connect_timeout") or global_connect`.

---

## Recommendations to document

Add a short **"Timeouts and load"** (or "Scan behaviour and timeouts") section in USAGE and, if useful, in the report or failure-hint text. Content:

1. **Don’t wait forever:** Set read (and connect) timeouts so one stuck target does not block the whole scan. Use report failure hints to spot timeout failures.
1. **Don’t be too aggressive:** Too-low timeouts cause false timeouts on busy or slow networks (e.g. during backup). If you see many timeouts, **increase** `connect_timeout_seconds` and `read_timeout_seconds` (or per-target overrides) and consider re-running during off-peak.
1. **Avoid DoS and "too much, too fast":** Use **rate_limit** (e.g. `max_concurrent_scans: 1`, `min_interval_seconds: 5`) and **scan.max_workers: 1** (or 2) so the scanner does not open many connections at once. This reduces load on targets and avoids amplifying slowness or causing DoS.
1. **Backup or maintenance windows:** If scans run during backup or maintenance, increase timeouts and keep parallelism low; or schedule scans outside those windows.
1. **Per-target overrides:** For one slow database or API, set `connect_timeout` / `read_timeout` (or `timeout`) on that target instead of raising global defaults for everyone.

Optionally extend `failure_hint("timeout")` with one line: "You can set timeouts in config (timeouts.connect_seconds, timeouts.read_seconds) or per target; see USAGE.md."

---

## Implementation phases (to-dos)

### Phase 1: Config and defaults

| #   | To-do                                                                                                                                                | Status |
| --- | ---------------------------------------------------------------------                                                                                | ------ |
| 1.1 | Add `timeouts` (or `scan.connect_timeout_seconds` / `scan.read_timeout_seconds`) to config loader with sane defaults (e.g. connect 25, read 90).     | ✅      |
| 1.2 | Normalize per-target overrides: `target.connect_timeout`, `target.read_timeout`, `target.timeout`; merge with global when building connector config. | ✅      |
| 1.3 | Document new keys in USAGE (config schema) and in example config.yaml or docs.                                                                       | ✅      |

### Phase 2: Wire connectors

| #   | To-do                                                                                                                                        | Status |
| --- | ---------------------------------------------------------------------                                                                        | ------ |
| 2.1 | SQL connector: pass connect_timeout (and optionally read/statement timeout) via create_engine connect_args from config/target.               | ✅      |
| 2.2 | REST connector: use global default when target.timeout not set; optionally split into connect/read via httpx.Timeout(connect=..., read=...). | ✅      |
| 2.3 | Power BI / Dataverse: create httpx client with timeout from config (connect + read).                                                         | ✅      |
| 2.4 | MongoDB: pass serverSelectionTimeoutMS, connectTimeoutMS, socketTimeoutMS from config.                                                       | ✅      |
| 2.5 | Redis: pass socket_connect_timeout and socket_timeout from config.                                                                           | ✅      |
| 2.6 | Other connectors (SMB, WebDAV, SharePoint, Snowflake): wire timeouts where the library supports; otherwise no change.                        | ✅      |

### Phase 3: Pass config to connectors

| #   | To-do                                                                                                                                                                                                                       | Status                                                    |
| --- | ---------------------------------------------------------------------                                                                                                                                                       | ------                                                    |
| 3.1 | Ensure engine or connector instantiation receives global config (or merged timeout values) so connectors can read defaults. (Today some connectors only get target_config; may need to pass config or pre-merged timeouts.) | ✅ (loader merges onto each target; engine passes target.) |
| 3.2 | Use consistent source: e.g. target.timeout or target.read_timeout override config.timeouts.read_seconds.                                                                                                                    | ✅                                                         |

### Phase 4: Recommendations and failure hint

| #   | To-do                                                                                                                                                                                                         | Status |
| --- | ---------------------------------------------------------------------                                                                                                                                         | ------ |
| 4.1 | Add "Timeouts and load" (or "Scan behaviour and timeouts") to USAGE.md with: don't wait forever, don't be too aggressive, avoid DoS/too-fast (rate_limit, max_workers), backup windows, per-target overrides. | ✅      |
| 4.2 | Optional: extend failure_hint("timeout") with a line pointing to config timeouts and USAGE.                                                                                                                   | ✅      |
| 4.3 | Optional: add same recommendations to docs in pt_BR.                                                                                                                                                          | ✅      |
| 4.4 | Tests: unit test that normalized config contains default timeouts; optional integration test that a connector receives and uses timeout (e.g. REST with short timeout fails or times out).                    | ✅      |

---

## Dependencies and constraints

- **Backward compatible:** If `timeouts` (or scan timeouts) are absent, use the same sane defaults in code so existing configs keep working.
- **Per-target wins:** Target-level `timeout` or `connect_timeout`/`read_timeout` override global values for that target only.
- **No change to rate_limit or max_workers logic:** Only add timeout handling; recommendations document how to use existing rate_limit and max_workers to avoid DoS and slowness.

---

## Conflict and placement in roadmap

- **No conflicts** with other plans. Additive (config keys, connector wiring, docs).
- **Placement:** Can be done early (improves robustness of all scans). See [PLANS_TODO.md](../PLANS_TODO.md).

---

## Last updated with plan file. Update PLANS_TODO.md when completing or adding to-dos.
