# Security Policy

**Português (Brasil):** [SECURITY.pt_BR.md](SECURITY.pt_BR.md)

This document describes which versions of the application are supported, which dependency baseline is expected, and how to report security vulnerabilities to the maintainers. For copyright and license: [NOTICE](NOTICE); for making copyright and trademark official: [docs/COPYRIGHT_AND_TRADEMARK.md](docs/COPYRIGHT_AND_TRADEMARK.md) ([pt-BR](docs/COPYRIGHT_AND_TRADEMARK.pt_BR.md)).

## Supported versions

- **Application (brand):** **Data Boar**. PyPI distribution id: **`data-boar`** (see [CONTRIBUTING.md](CONTRIBUTING.md#repository-and-install-identity-data-boar)). Current development targets **Python 3.12+**.
- We aim to support the latest stable minor versions of Python 3.12 and 3.13 on Linux, macOS and Windows.
- Older Python versions (< 3.12) are not tested and should be considered unsupported.

## Dependencies and environment

**`pyproject.toml`** is the source of truth for the **uv** toolchain. The **`uv.lock`** file pins the exact resolved dependency tree so that installs are reproducible and users are protected from accidental breakage when a dependency updates (“it worked yesterday”). **pip** and **`requirements.txt`** are derivative (requirements.txt is exported from the lockfile for pip-based or legacy environments). Dependencies are declared in **`pyproject.toml`** and managed via **uv**:

- To install in a fresh environment (uses **uv.lock** for reproducible versions):

  ```bash
  uv sync
  ```

- To export a locked **requirements.txt** for environments that use plain **pip** (same versions as **uv.lock**):

  ```bash
  uv export --no-emit-package pyproject.toml -o requirements.txt
  ```

### Lockfile and supply-chain mitigation (`uv.lock`)

Committing **`uv.lock`** is a **supply-chain control**: it pins the **full resolved dependency tree** (direct and transitive) so `uv sync` and CI install **the same package versions** from hashes recorded in the lockfile. That **reduces** unreviewed drift from floating `>=` resolution on PyPI, “works on my machine” breakage, and mismatch between **`uv.lock`** and a pip-only **`requirements.txt`** export.

The lockfile **does not** prove that those pins are **free of known CVEs** or **non-malicious**. **Vulnerability mitigation** on the Python install path layers **on top of** the lockfile: CI **`pip-audit`**, **GitHub Dependabot** (this repo uses **`package-ecosystem: uv`** so PRs move `pyproject.toml` and **`uv.lock`** together—see [ADR 0044](docs/adr/ADR-0044-dependabot-uv-ecosystem-for-pyproject-lock-closure.md)), maintainer review, and optional **SBOM** artifacts ([below](#software-bill-of-materials-sbom)). When you triage advisories or apply updates, refresh **`uv.lock`** through the single-pass closure (**`pyproject.toml` → `uv lock` → `uv export`**) in [ADR 0030](docs/adr/ADR-0030-python-dependency-update-closure-single-pass.md)—do not hand-edit the lockfile to “fix” audits.

### Runtime prerequisites (Linux example)

On Ubuntu/Debian you should have at least:

```bash
sudo apt update
sudo apt install -y \
  python3.12 python3.12-venv python3.12-dev build-essential \
  libpq-dev libssl-dev libffi-dev unixodbc-dev
```

Additional client libraries may be required depending on which connectors you use (e.g. Oracle, SQL Server, Snowflake); see the main `README.md` for connector-specific notes.

## Software Bill of Materials (SBOM)

Formal **CycloneDX JSON** SBOMs support **supply-chain** visibility and **incident response** (see [docs/adr/0003](docs/adr/ADR-0003-sbom-roadmap-cyclonedx-then-syft.md)). They complement **`pip-audit`**; they are **not** organizational risk management under ISO 31000 (see [COMPLIANCE_FRAMEWORKS.md](docs/COMPLIANCE_FRAMEWORKS.md)).

| Artifact | Contents | How it is produced |
| -------- | -------- | ------------------ |
| **`sbom-python.cdx.json`** | Python dependencies aligned with **`uv.lock`** (via `uv export` + **`cyclonedx-py`**) | Workflow **`SBOM`**, local **`scripts/generate-sbom.ps1`** |
| **`sbom-docker-image.cdx.json`** | Packages in the **built** OCI image (OS + Python layers) | **`syft`** in **`anchore/syft:v1.28.0`** against image `data_boar:sbom` built from the **`Dockerfile`** at the same commit |

**Where to download:** GitHub Actions workflow [**SBOM**](.github/workflows/sbom.yml) uploads both files as **workflow artifacts** (runs on version tags `v*`, on **`release: published`**, on **`workflow_dispatch`**, and on path-filtered PRs to `main`). When a **GitHub Release** already exists for the tag, the same files are **attached to that release**.

**Docker Hub:** When you follow [docs/ops/DOCKER_IMAGE_RELEASE_ORDER.md](docs/ops/DOCKER_IMAGE_RELEASE_ORDER.md), the published image **`fabioleitao/data_boar:<semver>`** should match the same source tree as the tag used for the SBOM workflow; the **image** SBOM is from a **local build** in CI (equivalent layers to a clean `docker build` at that commit), not from a separate registry pull.

## Keeping dependencies up to date

- Dependencies in **`pyproject.toml`** use **minimum versions (`>=`)** so security patches are allowed; pin exact versions (`==`) only where necessary. The **lockfile (`uv.lock`)** is committed so that everyone (and CI) installs the same tree; it is refreshed when dependencies change or before a stable release so the app stays updated, compatible, and safe. **Dependabot** (see `.github/dependabot.yml`) opens weekly PRs for pip and GitHub Actions and helps signal when to act: when you apply an update (or before a release), update **`pyproject.toml`** first, then run `uv lock` and `uv export --no-emit-package pyproject.toml -o requirements.txt`, and commit **pyproject.toml**, **uv.lock**, and **requirements.txt**. Do not merge a change that only edits `requirements.txt` or `uv.lock` without updating the other. Merge dependency PRs only after CI (tests and audit) pass.

### Dependency update closure (one pass, any trigger)

The **trigger** for a change (CI, Dependabot, Docker Scout, review feedback, maintainer choice, or another signal) does not change the **workflow**. When you decide an update is **justified and safe** after tests and audit:

1. Express intent in **`pyproject.toml`**, then **`uv lock`** and **`uv export --no-emit-package pyproject.toml -o requirements.txt`**—commit all three together.
2. Run **`uv sync`** locally so **`.venv`** matches the lockfile.
3. Run **`.\scripts\check-all.ps1`** (full gate) before merge—no “half green” dependency PRs.
4. Refresh **SBOM** artifacts when your release or compliance path requires an updated bill of materials at the **same commit**—see [ADR 0003](docs/adr/ADR-0003-sbom-roadmap-cyclonedx-then-syft.md) and **`scripts/generate-sbom.ps1`** / workflow **`SBOM`**.
5. Add or update an **ADR** when the bump reflects a **policy or architecture** choice (optional extras boundaries, toolchains, recorded upstream constraints), not for every routine patch.

This is **not** permission to churn dependencies blindly; defer or reject changes that lack rationale or fail gates. Recorded decision: [ADR 0030](docs/adr/ADR-0030-python-dependency-update-closure-single-pass.md).

- Locally, install and run a dependency audit (CI does the same on every push/PR):

  ```bash
  uv sync
  uv pip install pip-audit
  uv run pip-audit
  ```

- Whenever you change dependencies (including when applying Dependabot or automation), edit **`pyproject.toml`** first, then run `uv lock` and `uv export --no-emit-package pyproject.toml -o requirements.txt` so **uv.lock** and **requirements.txt** stay in sync with the lockfile.

- **Local triage (Dependabot + image CVEs):** On Windows, from the repo root, run **`.\scripts\maintenance-check.ps1`** after `gh auth login` (lists open Dependabot PRs) and with Docker Desktop if you want **`docker scout quickview`** on the published image. It does not modify the repo. After fixing deps or the **Dockerfile**, rebuild and push the image, then re-run Scout on the new digest. The **Dockerfile** upgrades **pip** and **wheel** in both builder and runtime layers so scans do not flag stale tooling copied from old layers; **`requirements.txt`** is uv-exported and typically does not list `wheel` as an app dependency.
- **Blocked-dependency triage checkpoint (last review: 2026-05-22):** **`uv.lock`** on **`main`** carries **`pygments` 2.20.0** and **`pyopenssl` 26.2.0** (via **`snowflake-connector-python` 4.5.0** with optional **`bigdata`**). Dependabot alerts **#9** / **#10** and **CVE-2026-4539** should remain **closed** while those pins hold. Re-verify on each **Band A order –1** pass and at least **quarterly** — see **PLANS_TODO.md** *Quarterly blocked-dependency checkpoint*.
- **pyOpenSSL Dependabot alerts (#9 / #10) and Snowflake:** **Resolved** as of **2026-05-22** (connector **4.5.0+**). Historical cap and reopen steps: **[docs/ops/DEPENDABOT_PYOPENSSL_SNOWFLAKE.md](docs/ops/DEPENDABOT_PYOPENSSL_SNOWFLAKE.md)**.
- **Pygments Dependabot / pip-audit (CVE-2026-4539):** **Resolved** as of **2026-05-22** (**pygments 2.20.0** on PyPI). Historical triage and bump steps: **[docs/ops/DEPENDABOT_PYGMENTS_CVE.md](docs/ops/DEPENDABOT_PYGMENTS_CVE.md)**.
- **Code scanning baseline:** CodeQL workflow uses **`security-and-quality`** for Python and should stay enabled on push/PR/schedule. Keep this broad suite plus project-specific hardening tests/rules; if a new query is noisy, triage and document before considering suppression.
- **Semgrep (OSS):** The **Semgrep** GitHub Actions workflow runs ruleset **`p/python`** on push/PR (complements CodeQL). Exclusions and rationale: **`docs/plans/completed/PLAN_SEMGREP_CI.md`**.
- **Bandit:** **Bandit (strict)** runs as part of the **CI** workflow on push/PR (`[tool.bandit]` in **`pyproject.toml`**). Details and **low**-severity triage: **`docs/plans/completed/PLAN_BANDIT_SECURITY_LINTER.md`**.
- **CI workflow supply chain:** Workflows under **`.github/workflows/`** pin third-party GitHub Actions to **full commit SHAs** (version tag in YAML comments for humans). The **`astral-sh/setup-uv`** step pins a **specific uv CLI semver**—not **`latest`**—so installs do not float silently between runs. **Dependabot** may propose SHA bumps; review upstream release notes before merge. This **reduces** tag-moving and unexpected action updates but is **not** a guarantee against zero-day compromise of a pinned commit, supply-chain attacks that pass review, or risks outside CI (for example local developer tooling). See **`docs/adr/ADR-0005-ci-github-actions-supply-chain-pins.md`**.

This approach is part of the project’s security baseline. For the full list of hardening measures and status, see **`docs/plans/completed/PLAN_SECURITY_HARDENING.md`**.

## Resistance to common vulnerabilities

- **SQL injection:** Table and column names used in dynamic SQL (connectors) come from the database inspector (discover), not from user input. Identifiers are escaped per dialect: double-quote for SQLite/Postgres/Oracle (`"` → `""`), backtick for MySQL (`` ` `` → ` `` `). The local audit database (SQLite) uses SQLAlchemy ORM and parameterized queries only; `session_id` and other user-supplied values are never concatenated into raw SQL. See **`tests/test_security.py`** for regression tests.
- **Path traversal:** `session_id` in API paths is validated with a strict pattern (alphanumeric and underscore, 12–64 chars) before use in file paths or lookups; invalid values return HTTP 400. See **`api/routes.py`** `_validate_session_id` and **`tests/test_security.py`**.
- **Input validation (tenant/technician):** Tenant and technician values (scan start body, session PATCH, config-driven scan) are validated for length and allowed characters (printable, no control chars), then sanitized before storage so reports and the dashboard never display unsanitized input. See **`core/validation.py`** `sanitize_tenant_technician` and **`tests/test_security.py`**.
- **Credential injection in connection URLs:** User and password are URL-encoded when building database connection URLs (SQL connector, MongoDB connector) so that special characters (`@`, `:`, `/`, `#`) in credentials do not break URL parsing or be misinterpreted as host/path. See **`connectors/sql_connector.py`** `_quote_userinfo` / `_build_url`, **`connectors/mongodb_connector.py`** `connect()`, and **`tests/test_security.py`** (e.g. `test_sql_connector_build_url_encodes_password_special_chars`, `test_mongodb_connector_uri_encodes_password_special_chars`).
- **Config and serialization:** YAML config is loaded with `yaml.safe_load` (no arbitrary Python object deserialization). See **`tests/test_security.py`** for a test that unsafe YAML tags are rejected.
- **Config endpoint exposure:** When `api.require_api_key` is true, GET `/config` returns 401 without a valid API key, so raw config (which may contain secrets) is not exposed. **GET `/config` always redacts secret values** (passwords, API key, tokens, client_secret, etc.) before sending YAML to the browser, so the UI never displays or transmits plain secrets; on save, placeholders are merged with the current file so real secrets are not overwritten. See **`config/redact_config.py`** and **`tests/test_security.py`**.
- **Config file and secrets:** Restrict config file permissions (e.g. `chmod 600` on `config.yaml`) so only trusted users can read it. **Do not commit** `config.yaml` or any file containing credentials to version control; use **`config.example.yaml`** (or **`deploy/config.example.yaml`**) as a template and keep local config in **`.gitignore`** (the project ignores `config.yaml`, `config.local.yaml`, and `*.vault`). If root `config.yaml` was ever committed, run **`git rm --cached config.yaml`** so Git stops tracking it (file stays on disk); old commits may still contain the blob—rewrite history or rotate secrets if the repo was public. Prefer storing secrets in environment variables (e.g. `pass_from_env`, `api_key_from_env`) so the config file holds no plain secrets. A **password manager** (e.g. **Bitwarden**) is a good place for the **operator** to store copies of those secrets and rotate them; see **`docs/ops/OPERATOR_SECRETS_BITWARDEN.md`**. **Homelab reality** (hostnames, LAN IPs, inventory): keep under **gitignored** **`docs/private/homelab/`**—see **`docs/PRIVATE_OPERATOR_NOTES.md`**. See **`docs/USAGE.md`** (Configuration), **`CONTRIBUTING.md`** (public repo hygiene), and **`docs/plans/PLAN_SECRETS_VAULT.md`** (Phase A).
- **Operator notifications (webhooks):** Optional `notifications` can POST scan summaries to Slack, Teams, a generic URL (e.g. Signal bridge), or Telegram fields for legacy/third-party configs. The canonical maintainer policy is **not** to use Telegram for Data Boar—see **`docs/ops/OPERATOR_NOTIFICATION_CHANNELS.md`**. Treat webhook URLs and bot tokens as secrets; use `${ENV_VAR}` in YAML or env-only wiring. See **`docs/USAGE.md`** (§5.1). Sends retry on transient failures (5xx / network); they do not replace TLS or network policy.
- **API bind vs API key:** When starting **`--web`**, if the resolved bind address is **non-loopback** (e.g. `0.0.0.0`) and an API key is **not** effectively configured, the process prints a **stderr warning** (see **`main.py`** and **`core/host_resolution.py`**). Prefer loopback + reverse proxy, or `api.require_api_key` with a strong key in production.
- **Request body size limit:** The API rejects requests whose **Content-Length** exceeds **1 MB** (e.g. POST `/config`, POST `/scan`, POST `/scan_database`) with **HTTP 413 Payload Too Large** to reduce DoS via huge JSON or form bodies. See **`api/routes.py`** `request_body_size_middleware` and **`tests/test_security.py`** for regression tests.
- **Logging policy:** API key, passwords, and connection strings must not appear in audit or application logs. Failure details and exception messages use **`core.validation.sanitize_log_text`** (secrets plus detector-aligned PII shapes such as CPF, email, card runs) and **`core.validation.clean_error`** for exceptions before SQLite or log handlers; connection URLs and `password=` / `api_key=`-style values are masked. Do not log raw config, request bodies, or driver/HTTP exception text that might contain credentials or customer data. See **`core/database.py`** (`save_failure`) and **`tests/test_security.py`** (`test_redact_*`, `test_sanitize_log_text_*`, `test_clean_error_*`).
- **Report and heatmap access:** Report and heatmap endpoints validate `session_id` format before use; invalid IDs return 400, unknown or missing sessions return 404 (no session enumeration or 403/404 distinction for unknown IDs). See **`api/routes.py`** and **`docs/SECURITY.md`**.

For a **technician-oriented summary** (what to watch for, regression tests, recommendations), see **`docs/SECURITY.md`** (EN) and **`docs/SECURITY.pt_BR.md`** (pt-BR). For completed and planned hardening steps, see **`docs/plans/completed/PLAN_SECURITY_HARDENING.md`**.

## HTTP security headers (web and API)

The application adds the following headers to all web and API responses by default:

- **X-Content-Type-Options: nosniff** – prevents MIME-type sniffing.
- **X-Frame-Options: DENY** – prevents the app from being embedded in frames (clickjacking mitigation).
- **Content-Security-Policy** – restricts script, style, and resource origins to the app and the Chart.js CDN; allows inline scripts/styles required by the current dashboard.
- **Referrer-Policy: strict-origin-when-cross-origin** – limits referrer information sent on cross-origin requests.
- **Permissions-Policy** – disables browser features not needed by the app (camera, microphone, geolocation, etc.).
- **Strict-Transport-Security (HSTS)** – set only when the request is considered HTTPS (direct or via `X-Forwarded-Proto: https` from a trusted proxy), so HTTP-only deployments are not locked out. When present, it uses `max-age=31536000; includeSubDomains; preload`.

When the app is behind a reverse proxy (e.g. nginx, Caddy, load balancer), ensure the proxy sets **X-Forwarded-Proto: https** for TLS-terminated requests so HSTS is applied correctly. Do not enable HSTS at the app layer for plain HTTP; the proxy can add HSTS when serving over HTTPS.

## Optional API key (enterprise)

The API does not implement authentication by default; secure the app at the reverse proxy or network level when exposed. For enterprises that want a simple shared-secret gate without changing the “secure at proxy” model, the application supports an **optional API key**:

- In config, set `api.require_api_key: true` and either `api.api_key` (literal — avoid committing secrets) or `api.api_key_from_env: "VAR"` (read key from environment at startup). When enabled, **GET /health** stays **unauthenticated** on purpose: it returns liveness JSON (`status`, public `license` summary, `dashboard_transport`) for probes. **Every other route** must include **X-API-Key** or **Authorization: Bearer &lt;key&gt;** when a key is successfully resolved from config/env. **401** = missing or wrong key. **503** = `require_api_key` is true but no key could be resolved (misconfiguration). **`main.py --web` exits with code 2** before listening if the key is required but missing, so you do not accidentally run an open API.
- **Good practice:** Use a strong, random key and store it in an environment variable (e.g. `api_key_from_env: "AUDIT_API_KEY"`). Do not log the key or commit it to version control. This is a simple gate only; for full authentication and authorization, continue to use the reverse proxy or an identity provider.
- **Concrete operator steps** (shell, systemd, Docker/K8s patterns, `curl` checks, synthetic example key): [API_KEY_FROM_ENV_OPERATOR_STEPS.md](docs/ops/API_KEY_FROM_ENV_OPERATOR_STEPS.md). For ordering (inventory clients, staging first, monitor `dashboard_transport` and audit export), see [SECURE_BY_DEFAULT_BLOCKERS_AND_MIGRATION.md](docs/ops/SECURE_BY_DEFAULT_BLOCKERS_AND_MIGRATION.md).
- **End-to-end technician guide (API key + TLS paths, Let’s Encrypt, lab self-signed, Docker):** [SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.md](docs/ops/SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.md) ([pt-BR](docs/ops/SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.pt_BR.md)).

## Deployment hardening and reverse proxy

Security headers (including CSP) are implemented in **`api/routes.py`** (middleware applied to web and API responses). For **operator-facing hardening** (containers, reverse proxy, TLS, WAF), see **`docs/USAGE.md`** and **`docs/deploy/DEPLOY.md`** (Security and hardening). To harden container and cluster deployments:

- **Docker and Kubernetes:** See **`docs/deploy/DEPLOY.md`**, section **“Security and hardening (optional)”**, for:
- Running as non-root, resource limits, and healthchecks.
- Optional Kubernetes examples: **securityContext** (runAsNonRoot, readOnlyRootFilesystem, drop capabilities), **NetworkPolicy** (`deploy/kubernetes/network-policy.example.yaml`), and **PodDisruptionBudget** (`deploy/kubernetes/pdb.example.yaml`).

When the API or dashboard is **exposed to the internet or untrusted networks**, run it behind a **reverse proxy** with **TLS**, proper **authentication/authorization**, and consider a **WAF** (web application firewall). The app’s API key and rate limiting (see `docs/USAGE.md`) complement but do not replace proxy-level security.

## Reporting a vulnerability

If you believe you have found a security vulnerability in this project:

1. **Do not open a public issue with exploit details.**
1. Instead, please:
   - Open a new issue in the **Issues** tab with a short, high-level description (no sensitive PoC data), **or**
   - If GitHub security advisories or private reporting is available for this repo, prefer that channel.
1. Include at least:
   - Version/commit of the project you are using.
   - Python version and OS details.
   - A minimal description of the impact (e.g. information disclosure, privilege escalation, DoS).
1. The maintainers will:
   - Acknowledge receipt as soon as reasonably possible.
   - Investigate and, if confirmed, work on a fix and coordinate disclosure.

If you are unsure whether something is security-sensitive, err on the side of caution and use the private channel (or a minimal public issue) so we can triage it safely.

## Security response (optional SLAs)

These are **targets** for maintainers and reporters, not contractual obligations. Adjust to your capacity.

| Area                        | Optional target                                                                                                                                                                                                             |
| ------                      | -----------------                                                                                                                                                                                                           |
| **Vulnerability reports**   | We aim to **acknowledge** within **5 working days** and, for **high/critical** findings, to **fix or document** (e.g. advisory, mitigation, or “won’t fix” with rationale) within **30 days**.                              |
| **Dependabot security PRs** | We treat Dependabot **security** PRs as **P0**: aim to **merge or respond** (e.g. merge, close with comment, or defer with rationale) within **5 working days**. Non-security dependency PRs follow the usual review cycle. |

See **CONTRIBUTING** for how to apply dependency updates and run `pip-audit`; see **`.github/dependabot.yml`** for Dependabot configuration.

## CodeQL quick triage matrix (P0/P1/P2)

Use this matrix to prioritize CodeQL findings by impact and release risk. Map each alert to the nearest rule family and code surface, then decide fix-now vs scheduled.

| Priority                               | Rule IDs (examples)                                                                                                                                                                                                              | Typical code surface in this repo                                                                                                                                 | Action                                                                       |
| ---                                    | ---                                                                                                                                                                                                                              | ---                                                                                                                                                               | ---                                                                          |
| **P0** (fix before release)            | `py/path-injection`, `py/sql-injection`, `py/nosql-injection`, `py/code-injection`, `py/command-line-injection`, `py/template-injection`, `py/full-ssrf`, `py/unsafe-deserialization`, `py/xxe`                                  | API file serving and report paths (`api/routes.py`), connectors/query builders (`connectors/*`, `database/*`), config/load paths (`config/*`)                     | Patch immediately, add regression test, and verify with CodeQL rerun.        |
| **P1** (fix in current cycle)          | `py/weak-sensitive-data-hashing`, `py/clear-text-logging-sensitive-data`, `py/clear-text-storage-sensitive-data`, `py/insecure-protocol`, `py/insecure-default-protocol`, `py/url-redirection`, `py/regex-injection`, `py/redos` | Licensing/integrity helpers (`core/licensing/*`), logging and failure persistence (`core/database.py`, `core/validation.py`), network connectors (`connectors/*`) | Fix or document mitigation in this release cycle; add tests where practical. |
| **P2** (scheduled hardening / monitor) | `py/bind-socket-all-network-interfaces`, `py/flask-debug`, `py/client-exposed-cookie`, `py/insecure-cookie`, `py/samesite-none-cookie`, `py/stack-trace-exposure`, `py/use-of-input`                                             | Host/runtime settings (`core/host_resolution.py`, Docker defaults), web middleware/templates (`api/routes.py`, `api/templates/*`)                                 | Keep enabled, monitor trends, and batch low-risk fixes with maintenance PRs. |

Notes:

- **Do not disable broad suites by default.** Keep `security-and-quality` and use targeted code fixes + tests first.
- If you must defer a finding, record reason + compensating control in PR/issue and revisit next `-1/-1b` loop.
