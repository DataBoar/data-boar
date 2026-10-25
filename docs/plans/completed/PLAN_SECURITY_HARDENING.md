# Plan: Security hardening and vulnerability closure

**Status:** Done (Tier 1 foundation). All steps 1.1–1.3, 2.1–2.4, 3.1–3.4, 5.1–5.3, 6.1–6.3, 7.1–7.3 complete.
**Synced with:** [PLANS_TODO.md](../PLANS_TODO.md) (central to-do list)

## When implementing steps: update docs and tests; then update PLANS_TODO.md and this file.

This plan recommends steps to close security gaps, reduce abuse and data-extraction risk, keep dependencies secure, and follow best practices—**without causing regressions or breaking the app**. Each step should be tested and validated before marking done.

---

## Goals

- **Vulnerabilities and gaps:** Address any remaining or newly identified vulnerabilities (input validation, output encoding, secrets, logging).
- **Abuse and data extraction:** Ensure the app cannot be abused (rate limits, auth, request bounds) and that sensitive data cannot be extracted by unauthorized callers.
- **Dependencies:** Use secure, up-to-date library versions; integrate audits into CI and release process.
- **Best practices:** Align with OWASP-style guidance, secure defaults, and deploy hardening already documented in SECURITY.md and docs/deploy.

All steps are **additive or configurable** where possible; avoid breaking existing deployments or tests.

---

## Current state (summary)

- **Already in place:** SQL injection resistance (identifier escaping, ORM), path traversal protection (session_id validation), credential encoding in URLs, `yaml.safe_load` for config, optional API key, rate limiting (concurrent + interval), security headers (CSP, X-Frame-Options, HSTS when HTTPS), config endpoint protected when API key required. See [SECURITY.md](../SECURITY.md) and [docs/SECURITY.md](SECURITY.md).
- **Gaps to consider:** Input validation/sanitization for tenant and technician (length, characters) when stored and later shown in reports/UI; request body size limits; ensuring no secrets in logs; dependency audit cadence and lockfile; optional stricter CSP; optional scan payload limits.

---

## 1. Input validation and output safety (prevent abuse and data extraction)

| #   | To-do                                                                                                                                                                                                                                                                                            | Status     | Notes                                                                                                                                        |
| --- | -------------------------------------------------------------------------------------------------------------------------------------                                                                                                                                                            | ---------- | -----                                                                                                                                        |
| 1.1 | **Tenant / technician validation:** Add optional max length (e.g. 256 chars) and allowlist of characters (printable, no control chars) for `tenant` and `technician` in ScanStartBody, SessionTenantUpdate, SessionTechnicianUpdate, and config-driven scan. Store trimmed/sanitized value only. | ✅ Done     | core/validation.sanitize_tenant_technician; api/routes + main.py; test_security.                                                             |
| 1.2 | **Request body size limit:** Ensure FastAPI/ASGI request body size is bounded (e.g. 1 MB for JSON config save and scan start body) to prevent DoS via huge payloads. Document in SECURITY.md.                                                                                                    | ✅ Done     | request_body_size_middleware; SECURITY.md; test.                                                                                             |
| 1.3 | **Logging:** Audit code paths that log request data, config, or errors; ensure API key, passwords, and connection strings are never logged. Add a regression test or checklist.                                                                                                                  | ✅ Done     | core/database.py redact_secrets_for_log; test_redact_secrets_for_log_*; CONTRIBUTING Release checklist + SECURITY.md (“do not log the key”). |

---

## 2. Dependencies (secure and up-to-date libraries)

| #   | To-do                                                                                                                                                                                                 | Status     | Notes                                                                                       |
| --- | -------------------------------------------------------------------------------------------------------------------------------------                                                                 | ---------- | -----                                                                                       |
| 2.1 | **pip-audit in CI:** Confirm `uv run pip-audit` runs on every push/PR (already in `.github/workflows/ci.yml`). Fix any new findings before release.                                                   | ✅ Done     | CI verified; CONTRIBUTING now states PRs must resolve audit failures.                       |
| 2.2 | **Dependabot:** Keep weekly pip and github-actions updates enabled; when merging, update `pyproject.toml` first, then `uv lock` and `uv export --no-emit-package pyproject.toml -o requirements.txt`. | ✅ Done     | CONTRIBUTING and SECURITY: lockfile workflow; release checklist refreshes lockfile.         |
| 2.3 | **Minimum versions:** Prefer `>=` in pyproject.toml for security patches; pin `==` only where necessary for reproducibility. Document in SECURITY.md or CONTRIBUTING.                                 | ✅ Done     | SECURITY.md and CONTRIBUTING now state prefer >=, pin == only when needed.                  |
| 2.4 | **Lockfile and audit:** Adopt `uv.lock`; run `pip-audit` against the locked environment in CI. Refresh lockfile when deps change or before a stable release; Dependabot signals when to act.          | ✅ Done     | uv.lock committed; CI uses it; CONTRIBUTING/SECURITY document workflow and release refresh. |

### Lockfile (uv.lock) — rationale and process

- **Why:** Reproducible installs (same tree in dev, CI, and production); protects users from “it worked yesterday” breakage when a dependency updates; pip-audit runs against what is actually installed; aligns with future self-update and stable releases.
- **Process:** (1) Declare deps in `pyproject.toml` with minimum versions (`>=`). (2) Run `uv lock` to resolve and pin the tree in `uv.lock`; run `uv export --no-emit-package pyproject.toml -o requirements.txt` for pip users. (3) Commit `pyproject.toml`, `uv.lock`, and `requirements.txt`. (4) When applying Dependabot (or any dep update): update pyproject first, then `uv lock` + export, commit all three. (5) Before a **stable release**: refresh lockfile (`uv lock`), run tests and pip-audit, then export and commit so the release is updated, compatible, and safe. Dependabot PRs help signal when to act; no need to chase every minor update between releases.

---

## 3. Application and API hardening (abuse and extraction prevention)

| #   | To-do                                                                                                                                                                                                                                                                                       | Status     | Notes                                                                                                                    |
| --- | -------------------------------------------------------------------------------------------------------------------------------------                                                                                                                                                       | ---------- | -----                                                                                                                    |
| 3.1 | **Rate limiting:** Already implemented (concurrent scans, min interval). Document recommended production values and that rate_limit is the first line of defense against scan abuse.                                                                                                        | ✅ Done     | USAGE (EN + pt_BR): production sentence added; relaxing limits increases abuse risk.                                     |
| 3.2 | **API key:** When `require_api_key` is true, /config and other sensitive endpoints are protected. Recommend in docs that production deployments set `require_api_key: true` and use a strong key from env.                                                                                  | ✅ Done     | USAGE, DEPLOY (EN + pt_BR): recommend require_api_key: true and strong key from env in production.                       |
| 3.3 | **Report/heatmap access:** Confirm that report and heatmap download endpoints only return data for validated `session_id` and that no enumeration or info leakage occurs (e.g. 404 vs 403). Current design (validate session_id, then generate or 404) is acceptable; document as intended. | ✅ Done     | docs/SECURITY.md and docs/SECURITY.pt_BR.md: table row + recommendation bullet (400/404, no enumeration).                |
| 3.4 | **Optional scan payload limits:** If the API or config ever accepts very large target lists or patterns, consider documenting or enforcing a reasonable limit (e.g. max targets per scan) to avoid resource exhaustion.                                                                     | ✅ Done     | USAGE (EN + pt_BR): no hard limit; document that very large target lists may increase duration/memory; reasonable scope. |

---

## 4. TLS, headers, and client security

| #   | To-do                                                                                                                                                                        | Status     | Notes                                                                                          |
| --- | -------------------------------------------------------------------------------------------------------------------------------------                                        | ---------- | -----                                                                                          |
| 4.1 | **SSL/TLS (S4423):** Any use of `ssl.create_default_context()` must set `minimum_version = ssl.TLSVersion.TLSv1_2`. Enforced by test in `tests/test_sonarqube_python.py`.    | ✅ Done     | Already fixed in `scripts/check_name_availability.py`; test prevents regression.               |
| 4.2 | **Security headers:** CSP, X-Frame-Options, HSTS (when HTTPS), Referrer-Policy, Permissions-Policy are set in `api/routes.py`. No change unless a new header is recommended. | ⬜ N/A      | Document in this plan that current set is sufficient; optional stricter CSP is in deploy docs. |
| 4.3 | **HTTPS in production:** Document that TLS should be terminated at reverse proxy; app respects X-Forwarded-Proto for HSTS. Already in SECURITY.md.                           | ⬜ N/A      | No code change.                                                                                |

---

## 5. Deployment and operations

| #   | To-do                                                                                                                                                                                                                           | Status     | Notes                                                                                            |
| --- | -------------------------------------------------------------------------------------------------------------------------------------                                                                                           | ---------- | -----                                                                                            |
| 5.1 | **Deploy hardening:** DEPLOY.md already includes optional securityContext, NetworkPolicy, PDB. Ensure SECURITY.md and USAGE reference “Security and hardening” in deploy docs.                                                  | ✅ Done     | SECURITY.md now references USAGE and DEPLOY for operator-facing hardening.                       |
| 5.2 | **Secrets:** Config and env may contain DB passwords and API keys. Document that config file permissions and env handling must restrict access to trusted users; never commit secrets.                                          | ✅ Done     | Reinforced in CONTRIBUTING Release checklist (secrets, config permissions).                      |
| 5.3 | **WAF / reverse proxy:** State explicitly that for internet-facing deployments, a reverse proxy with TLS and (optionally) WAF is recommended; app-level API key and rate limiting complement but do not replace proxy security. | ✅ Done     | Confirmed present in SECURITY.md (“reverse proxy with TLS… WAF… complement but do not replace”). |

---

## 6. Testing and regression

| #   | To-do                                                                                                                                                                                                                   | Status     | Notes                                                                                                                   |
| --- | -------------------------------------------------------------------------------------------------------------------------------------                                                                                   | ---------- | -----                                                                                                                   |
| 6.1 | **Security tests:** `tests/test_security.py` covers SQL injection, path traversal, credential encoding, safe_load, config endpoint. Keep these green; add tests for any new validation (e.g. tenant/technician length). | ✅ Done     | test_sanitize_tenant_technician_* (4 tests), test_request_body_size_limit_returns_413_*, test_redact_secrets_for_log_*. |
| 6.2 | **S4423 regression:** `test_ssl_create_default_context_uses_minimum_tls_version` in test_sonarqube_python.py ensures no new use of default context without minimum TLS.                                                 | ✅ Done     | Already in place.                                                                                                       |
| 6.3 | **No regressions:** Before marking any step done, run `uv run pytest -v -W error` and relevant security tests.                                                                                                          | ✅ Done     | Process: run full suite; CI enforces it.                                                                                |

---

## 7. Documentation and checklist

| #   | To-do                                                                                                                                                                                 | Status     | Notes                                                                                                       |
| --- | -------------------------------------------------------------------------------------------------------------------------------------                                                 | ---------- | -----                                                                                                       |
| 7.1 | **Release checklist:** Add a “Security” section: run `pip-audit`, fix any high/critical findings, ensure SECURITY.md and docs/security.md are up to date, confirm no secrets in logs. | ✅ Done     | Added in CONTRIBUTING.md and CONTRIBUTING.pt_BR.md ("Release checklist (Security)").                        |
| 7.2 | **docs/security.md:** After implementing 1.1–1.3, add one line each for tenant/technician validation, body size, and logging policy so technicians know what is enforced.             | ✅ Done     | docs/SECURITY.md and docs/SECURITY.pt_BR.md: three bullets added in Recommendations.                        |
| 7.3 | **SECURITY.md:** Ensure “Resistance to common vulnerabilities” and “Keeping dependencies up to date” reflect current state and reference this plan where appropriate.                 | ✅ Done     | Root SECURITY.md and SECURITY.pt_BR.md: added tenant/technician, report/heatmap; plan ref in both sections. |

---

## Order of execution (recommended)

1. **Low-risk, high-value:** 2.1, 2.2, 2.3 (audit and dependency policy); 5.1, 5.2, 5.3 (docs only).
1. **Input and request safety:** 1.1 (tenant/technician validation + test 6.1), then 1.2 (body size), then 1.3 (logging audit).
1. **Documentation:** 3.1, 3.2, 3.3, 3.4; then 7.1, 7.2, 7.3.

---

## Out of scope (by design)

- **Authentication beyond API key:** Full OAuth2/OIDC or per-user auth is out of scope; proxy or IdP remains the recommended place for that.
- **Code signing / SBOM:** Not in this plan; can be a separate improvement.
- **Penetration testing:** Recommended for production deployments but not part of this implementation plan.

---

---

## Execution log (progress and history)

| Date       | Step | Action                                                                                                               |
| ---------- | ---- | ------                                                                                                               |
| 2026-03    | 2.1  | Verified pip-audit in CI (`.github/workflows/ci.yml`); added CONTRIBUTING sentence: PRs must resolve audit failures. |
| 2026-03    | 2.2  | Added CONTRIBUTING “Release checklist (Security)”: audit, docs, no secrets in logs.                                  |
| 2026-03    | 2.3  | Documented min versions (>=) in SECURITY.md and CONTRIBUTING.                                                        |
| 2026-03    | 5.1  | SECURITY.md now references USAGE and DEPLOY for operator hardening.                                                  |
| 2026-03    | 5.2  | Secrets/config reinforced in Release checklist.                                                                      |
| 2026-03    | 5.3  | Confirmed WAF/reverse proxy text in SECURITY.md; no change.                                                          |
| 2026-03    | 7.1  | Release checklist (Security) added in CONTRIBUTING.md and CONTRIBUTING.pt_BR.md.                                     |

## Update this table when completing each step; keep Status cells in the tables above in sync.

---

*Last updated: plan created. Update this doc when completing steps or when new security recommendations are adopted.*
