# Observability, SLO/SLI, DevSecOps and SRE alignment

**Português (Brasil):** [OBSERVABILITY_SRE.pt_BR.md](OBSERVABILITY_SRE.pt_BR.md)

This document describes how the project **balances safety and security with performance and reliability**, and how it aligns with **observability**, **SLO/SLI/SLA**, **DevSecOps**, and **SRE** practices. All recommendations are **additive** and **non-breaking**; implement them incrementally and run the full test suite after any code change.

---

## 1. Balancing safety/security with performance and reliability

Today the app already balances these concerns in the following way:

| Concern         | What we do                                                                                                                                               | Where                                                                                                                 |
| --------        | ----------                                                                                                                                               | -----                                                                                                                 |
| **Security**    | API key (optional), security headers (CSP, X-Frame-Options, etc.), no secrets in responses, parameterized queries, session_id validation, YAML safe_load | [SECURITY.md](../SECURITY.md), [api/routes.py](../api/routes.py), [tests/test_security.py](../tests/test_security.py) |
| **Safety**      | Rate limiting (429), configurable timeouts (per plan), scan.max_workers, pip-audit and dependency hygiene                                                | [CONTRIBUTING.md](../CONTRIBUTING.md), [docs/USAGE.md](USAGE.md), config                                              |
| **Reliability** | Health endpoint for liveness/readiness, GET /status for scan state, SQLite + config load on startup, tests with `-W error`                               | [api/routes.py](../api/routes.py), [docs/deploy/DEPLOY.md](deploy/DEPLOY.md)                                          |
| **Performance** | Sessions list cache (TTL when no scan running), rate_limit to avoid overloading targets, configurable parallelism                                        | [api/routes.py](../api/routes.py), config                                                                             |

**Trade-offs we accept:** Health is a simple `{"status": "ok"}` (process up); it does not check DB or config reachability. For many deployments this is enough for Kubernetes/Docker liveness; for stricter readiness you can add a reverse-proxy or sidecar that checks GET /status or a future readiness endpoint. We do not log request latency or expose metrics by default, to avoid overhead and accidental leakage of sensitive data; see below for optional instrumentation.

---

## 2. Observability and SLO/SLI/SLA

### Current state

- **Liveness/readiness:** `GET /health` returns 200 when the process is up. Used by Docker, Compose, and Kubernetes for healthchecks (see [deploy/DEPLOY.md](deploy/DEPLOY.md)).
- **Scan state:** `GET /status` returns `running`, `current_session_id`, `findings_count` (useful for dashboards or runbooks).
- **No metrics endpoint yet:** There is no `/metrics` (Prometheus) or OpenTelemetry export. Adding one would be an **additive** feature (new route, optional dependency).
- **Logging:** Application logging exists but is not structured (e.g. no request_id, duration) by default; see [SECURITY.md](../SECURITY.md) for policy (no secrets in logs).

### SLI/SLO/SLA (how you can get there)

To support **SLAs** you need **SLOs** (targets), and to measure SLOs you need **SLIs** (indicators). Below is a minimal set that matches what the app can support today or with small additions.

| SLI (what to measure)      | How to measure today                                                               | Optional improvement                                                                                  |
| ----------------------     | --------------------                                                               | --------------------                                                                                  |
| **Availability** (API up)  | LB/orchestrator probes `GET /health`; count 200 vs 5xx                             | Add `/ready` that checks config + DB if you need stricter readiness                                   |
| **Scan success rate**      | Logs or DB: count sessions with status completed vs failed; or parse report output | Add a counter or label in a future `/metrics` (e.g. `scan_completed_total`, `scan_failed_total`)      |
| **API latency** (e.g. p99) | Reverse-proxy or APM (e.g. Prometheus + middleware that records duration)          | Add optional middleware that emits duration (or exports to Prometheus) without logging request bodies |
| **Error rate** (4xx/5xx)   | Access logs from reverse proxy or app logs                                         | Same: optional metrics or structured logs with status code                                            |

**Recommendation:** For now, use **GET /health** and your **reverse proxy or orchestrator** (Nginx, Traefik, Kubernetes Ingress) to measure availability and latency. Document your target SLO (e.g. “99.9% of health checks return 200”) and alert when the probe fails. When you need in-app SLIs (e.g. scan success rate, request duration), add an **optional** `/metrics` endpoint (Prometheus format) and/or structured logging with request_id and duration; keep both behind config so default behaviour stays unchanged and no secrets are logged.

---

## 3. DevSecOps alignment

DevSecOps means **security as code**, **shift-left**, and **automation**. The project already does the following:

| Practice                 | What we do                                                                                                                                |
| --------                 | ----------                                                                                                                                |
| **Shift-left**           | Tests (pytest), Ruff, SonarQube-style tests, CodeQL, pip-audit in CI; quality rule and skill so the agent avoids violations before commit |
| **Security in pipeline** | Dependency audit (pip-audit), security tests (SQL injection, path traversal, safe_load), API key and CSP tests                            |
| **Secrets**              | No secrets in logs (policy in SECURITY.md); config and env for API key; release checklist confirms no secrets in logs                     |
| **Supply chain**         | Dependabot, minimum versions in pyproject.toml, audit before release                                                                      |

**Recommendation:** Keep integrating security into the same pipeline (tests + lint + audit). When you add new features (e.g. webhooks, new connectors), add tests and update [SECURITY.md](../SECURITY.md) and [docs/SECURITY.md](SECURITY.md) so behaviour stays documented.

---

## 4. SRE alignment

SRE focuses on **reliability**, **toil reduction**, **error budgets**, and **operability**.

| Practice           | What we do                                                                                                                                                                                                                                              |
| --------           | ----------                                                                                                                                                                                                                                              |
| **Healthchecks**   | GET /health for liveness/readiness; used in Docker and K8s examples                                                                                                                                                                                     |
| **Runbooks**       | [TROUBLESHOOTING.md](TROUBLESHOOTING.md), [TROUBLESHOOTING_CONNECTIVITY.md](TROUBLESHOOTING_CONNECTIVITY.md), [TROUBLESHOOTING_CREDENTIALS_AND_AUTH.md](TROUBLESHOOTING_CREDENTIALS_AND_AUTH.md); deploy docs describe resource limits and healthchecks |
| **Toil reduction** | CI (tests, lint, audit), scripts (fix_markdown_sonar, commit-or-pr), pre-commit optional; quality rules reduce rework                                                                                                                                   |
| **Operability**    | Config file (no code change for many scenarios), rate_limit and timeouts to avoid overload, single binary/container                                                                                                                                     |

**Error budgets:** If you define an SLO (e.g. 99.9% availability), the “error budget” is the allowed fraction of failures (e.g. 0.1%). Use health probe success rate and, if you add it, scan success rate to stay within the budget; prioritize reliability work when the budget is consumed.

**Recommendation:** Document your chosen SLO and how you measure it (e.g. “Health check 99.9% over 30 days”). Add a short “Operations” or “Runbooks” section to [docs/deploy/DEPLOY.md](deploy/DEPLOY.md) or keep pointers here so operators know where to look when something fails.

### Governance of the auditor

SRE framing: **who watches the watcher** — the scanner must be **audit-defensible**, not only the data it inspects. **[ADR 0037](adr/ADR-0037-data-boar-self-audit-log-governance.md)** records the **2026 baseline** (session attribution in SQLite, export audit trail, wipe log, notification send log, host logs with redaction) and **explicit gaps** (no immutable per-report download log or per-config POST row by default). Use it for honest **CISO / procurement** narratives and for [MAP.md](MAP.md) navigation.

---

## 5. What to add next (additive only)

Without breaking the app or introducing regressions, you can:

1. **Keep current behaviour:** Rely on GET /health and GET /status plus your reverse proxy/orchestrator for availability and latency. Document your SLO and where you measure it.
1. **Optional /metrics (later):** Add a route (e.g. GET /metrics) that returns Prometheus text format: e.g. `http_requests_total`, `http_request_duration_seconds`, `scan_completed_total`, `scan_failed_total`. Guard it with a config flag (e.g. `api.metrics_enabled: false` by default) so it is off unless explicitly enabled. Do not expose secrets or PII.
1. **Optional structured logging (later):** Add request_id and duration to logs (e.g. middleware that logs method, path, status, duration_ms). Ensure logs never contain API keys, session_ids that could be sensitive, or target credentials; see [SECURITY.md](../SECURITY.md).
1. **Readiness (optional):** If you need “ready” to mean “config loaded and DB reachable”, add GET /ready that performs a minimal DB check (e.g. list_sessions limit 1) and returns 200/503. Leave GET /health as a simple liveness check so orchestrators do not need to change.

Run the full test suite (`uv run pytest -v -W error`) and the lint job (`uv run ruff check .`) after any code change; update this doc and [TESTING.md](TESTING.md) when you add new endpoints or behaviour.

---

## 6. Summary

| Question                                                  | Answer                                                                                                                                                                                                            |
| --------                                                  | ------                                                                                                                                                                                                            |
| **Balance safety/security with performance/reliability?** | Yes: security (headers, API key, validation, audit) and reliability (health, status, rate limit, timeouts) are in place; trade-offs (simple health, no default metrics) are documented.                           |
| **Instrumentation for observability and SLOs?**           | Health and status exist; SLIs can be measured today via health probes and proxy logs. Optional /metrics and structured logging can be added later without breaking the app.                                       |
| **DevSecOps and SRE?**                                    | DevSecOps: shift-left (tests, lint, audit, CodeQL), security in pipeline, no secrets in logs. SRE: healthchecks, runbooks (troubleshooting docs), toil reduction (CI, scripts), operability (config, rate limit). |
| **Without breaking or regressions?**                      | This doc and the suggested next steps are additive and config-optional; any new code should be tested and documented so the app keeps passing the full suite and follows SECURITY.md.                             |

For deployment details (Docker, Kubernetes, healthchecks), see [deploy/DEPLOY.md](deploy/DEPLOY.md). For security policy and API key, see [SECURITY.md](../SECURITY.md). For **sprints**, milestone **M-OBS**, and **error-budget** style guardrails, see **SPRINTS_AND_MILESTONES** under **Internal and reference** in [README.md](README.md) (`docs/plans/` in the checkout).
