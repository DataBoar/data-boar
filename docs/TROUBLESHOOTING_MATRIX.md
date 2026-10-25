# Data Boar - Troubleshooting Matrix

> **Audience:** POC testers, collaborators (team members), operators.
> **Version:** 2026-04-05 | **Related:** `scripts/run_poc_error_scenarios.py`

Use this matrix when Data Boar returns an unexpected result, dashboard error, or
the scanner does not find data you expect it to find.

---

## How to collect and share findings

```ash
# 1. Start Data Boar
uv run python main.py --config deploy/config.example.yaml --web --port 8088

# 2. Run the error scenario suite
uv run python scripts/run_poc_error_scenarios.py --output reports/poc_error_metrics.json

# 3. Import Postman collection
# tests/postman/Data_Boar_POC_ErrorScenarios.postman_collection.json

# 4. Share findings: open GitHub issue with reports/poc_error_metrics.json
```

---

## Category A - API errors

### A-001: Connection refused

**Symptom:** `CONNECTION_REFUSED` in script output or `curl: (7) Failed to connect`.

**Cause:** Server not running.

**Fix (connection refused):**

```ash
uv run python main.py --config config.yaml --web --port 8088
# or Docker:
docker run -p 8088:8088 -v \C:\Users\<username>\Documents\dev\data-boar/config.yaml:/data/config.yaml fabioleitao/data_boar:latest
```

**Validation:** `curl http://localhost:8088/health` returns `{"status":"ok"}`.

---

### A-002: HTTP 401 / 403 on all endpoints

**Symptom:** Every request returns 401 or 403.

**Cause:** `api.require_api_key: true` but request has no key.

**Fix:** Add header `X-API-Key: your-key` or set `api.require_api_key: false` in config.

---

### A-003: HTTP 422 Unprocessable Entity

**Symptom:** POST to `/scan` returns 422.

**Cause:** Payload missing required fields or wrong types.

**Required fields by connector type:**

| Type | Required fields |
|---|---|
| `postgresql` | `host`, `port`, `database`, `user`, `password` |
| `mysql` | `host`, `port`, `database`, `user`, `password` |
| `sqlite` | `path` |
| `mongodb` | `host`, `port`, `database` |
| `filesystem` | `path` |
| `mssql` | `host`, `port`, `database`, `user`, `password` |

---

### A-004: HTTP 429 Too Many Requests

**Symptom:** POST to `/scan` returns 429.

**Cause:** Scan already running or rate limit hit.

**Fix:** Check `GET /status`, wait for current scan to finish.

---

## Category B - Database errors

### B-001: Connection timeout / refused on DB target

**Cause:** DB host unreachable from Data Boar container/host.

**Docker gotcha:**

```yaml
# WRONG (inside container, localhost = container itself):
targets:
  - type: postgresql
    host: localhost

# CORRECT:
targets:
  - type: postgresql
    host: host.docker.internal  # Docker Desktop
    # or actual LAN IP
```

**Diagnosis:**

```ash
telnet db-host db-port
# or: nc -zv db-host db-port
```

---

### B-002: Authentication failed

**Cause:** Wrong user/password or missing GRANT.

**Fix (PostgreSQL):**

```sql
GRANT CONNECT ON DATABASE your_db TO your_user;
GRANT USAGE ON SCHEMA public TO your_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO your_user;
```

**Fix (MySQL):**

```sql
GRANT SELECT ON your_db.* TO 'your_user'@'%';
FLUSH PRIVILEGES;
```

---

### B-003: Unknown connector type

**Supported types:** `postgresql`, `mysql`, `sqlite`, `mongodb`, `mssql`,
`redis`, `snowflake`, `filesystem`

**Fix:** Correct the `type` field.

---

## Category C - File scan errors

### C-001: Path not found

**Cause:** Path does not exist at runtime (especially in Docker without volume mount).

**Fix (path not found):**

```ash
docker run -v /your/data:/scan/data ... # then use path: /scan/data in config
```

---

### C-002: File not scanned (wrong extension)

**Cause:** Extension not in `file_scan.extensions` list.

**Fix:** Add missing extension to config:

```yaml
file_scan:
  extensions: [.txt, .csv, .pdf, .docx, .xlsx, .json, .xml, .db, .parquet, .zip, .tar.gz]
```

---

### C-003: File scanned but zero findings

**Diagnosis checklist:**

1. Is the file format supported? Run `7_extensions/` corpus.
2. Is OCR enabled for images? `ocr.enabled: true`
3. Is the PII format recognized? Run `1_happy/` corpus - CPF `123.456.789-09` should be found.
4. Is the data inside an archive? `file_scan.scan_archives: true`
5. Is encoding non-UTF-8? Check latin-1, windows-1252 handling.

---

## Category D - Dashboard / UI errors

### D-001: Blank or 500 page

**Fix (blank or 500 page):**

```ash
docker logs data_boar 2>&1 | tail -50
curl http://localhost:8088/health
```

---

### D-002: Heatmap empty (404)

**Cause:** No completed scan, or wrong session ID.

**Fix:** POST `/scan`, wait for completion (`GET /status`), then `GET /list` for session ID.

---

## Category E - Performance

### E-001: Scan very slow

**Fix (scan very slow):**

```yaml
scan:
  sample_limit: 100
  file_sample_max_chars: 5000
  max_workers: 2
```

---

### E-002: API unresponsive under load

**Fix (API unresponsive):**

```yaml
api:
  workers: 2
```

Also check: `docker stats data_boar`

---

## Metrics collection template

After `run_poc_error_scenarios.py`, share the JSON output. For manual findings:

```json
{
  "scenario": "B1",
  "observed_http_code": 422,
  "observed_body": "...",
  "latency_ms": 340,
  "expected": "202 (scan starts)",
  "finding": "Port as string accepted without error",
  "recommendation": "Add int validator for port field",
  "severity": "MEDIUM",
  "reproduced_by": "tester-1",
  "date": "2026-04-06",
  "github_issue": "#XX"
}
```

Open a GitHub issue at <https://github.com/DataBoar/data-boar/issues> with the JSON.

---

## Related documentation

- `scripts/run_poc_error_scenarios.py` -- automated runner
- `tests/postman/Data_Boar_POC_ErrorScenarios.postman_collection.json` -- Postman collection
- `scripts/generate_synthetic_poc_corpus.py` -- synthetic data
- `docs/TESTING_POC_GUIDE.md` -- full validation guide
- `docs/USAGE.md` -- config reference