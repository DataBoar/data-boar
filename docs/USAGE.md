# Data Boar: Enterprise Data Discovery & Risk Governance Engine

This page is the **operator usage guide**: **CLI**, **web API and dashboard**, **configuration** (targets, sampling, detection, credentials), and **deliverables** (Excel, heatmap, executive Markdown, evidence manifest — current and previous sessions). It complements the [technical guide](TECH_GUIDE.md) and the [root README](../README.md). Install identity and PyPI **`data-boar`**: [CONTRIBUTING.md](../CONTRIBUTING.md#repository-and-install-identity-data-boar).

**Data Boar** is **compliance-aware discovery and mapping** of personal and sensitive data across databases, files, APIs, and shares (**LGPD**, **GDPR**, **CCPA**, **GLBA**, and configurable frameworks — not LGPD-only). Deliverables are **GRC-adjacent** (executive narrative, APG-style priorities, evidence manifests): they support **risk assessment** and **compliance discovery** workflows; they do **not** replace legal counsel or a full enterprise GRC platform. The repository still ships the historical **`lgpd_crawler`** Python package for imports — implementation detail, not the product name.

**Warehouse and enterprise SQL:** The same engine covers **SQLAlchemy** database targets (**Microsoft SQL Server**, **PostgreSQL**, **MySQL/MariaDB**, **Oracle**, …) and optional **Snowflake** (install with ``uv sync --extra bigdata`` — [Snowflake (optional)](#snowflake-optional-bigdata)). Sampling uses **per-engine timeouts** and documented hints (e.g. MySQL **`/*+ MAX_EXECUTION_TIME(N) */`** and PostgreSQL **`SET LOCAL statement_timeout`** — see **SRE sampling** under global options). If **your** DBA policy uses **read-uncommitted** reads (for example **`NOLOCK`** hints in connector SQL), record that in **runbooks** and in **`scan_manifest_*.yaml`** / evidence text so stakeholders see **attributed posture**, not silent isolation semantics.

**Português (Brasil):** [USAGE.pt_BR.md](USAGE.pt_BR.md)

---

## 1. Command-line interface (CLI)

The main entry point is `main.py`.

### Arguments

<!-- markdownlint-disable MD060 -->
| Argument                | Default           | Description                                                                                                                                                                                                                                                                         |
| ---                     | ---               | ---                                                                                                                                                                                                                                                                                 |
| `--demo`                | *(flag)*          | **Zero-config demo:** creates a temp workspace under `/tmp/data_boar_demo/` (or the OS temp dir) with `demo.config.yaml`, a synthetic filesystem corpus, reports, and SQLite DB; runs an initial scan and starts the dashboard on loopback. **Ignores `config.yaml` in the current working directory.** Implies `--web` and `--allow-insecure-http`. Temp files are removed on exit. Incompatible with `--validate-config`, `--reset-data`, `--export-audit-trail`, `--export-dsar`, and `--diff`. |
| `--config`              | `config.yaml`     | Path to the configuration file (YAML or JSON). Used for both one-shot audit and to resolve `api.port` / `api.host` when starting the web server.                                                                                                                                    |
| `--web`                 | *(flag)*          | Start the REST API server instead of running a one-shot audit.                                                                                                                                                                                                                      |
| `--port`                | `8088`            | Port for the API when `--web` is set. Can be overridden by `api.port` in config unless you pass `--port` explicitly. Ignored in one-shot mode.                                                                                                                                      |
| `--host`                | *(resolved)*      | Bind address when `--web` is set (e.g. `127.0.0.1`, `0.0.0.0`). **Overrides** `api.host` and `API_HOST`. If omitted: `api.host` → `API_HOST` → default **`127.0.0.1`**. Ignored in one-shot mode. See §2.                                                                           |
| `--https-cert-file`     | *(none)*          | PEM certificate path for TLS when `--web` is set; requires `--https-key-file` (or `api.https_cert_file` / `api.https_key_file`). TLS **≥ 1.2**. Without both files, startup **fails** unless you pass `--allow-insecure-http`.                                                      |
| `--https-key-file`      | *(none)*          | PEM private key path for TLS when `--web` is set; paired with `--https-cert-file` or config keys above.                                                                                                                                                                             |
| `--allow-insecure-http` | *(flag)*          | **Explicit risk acceptance:** serve the dashboard over **plaintext HTTP** (sniffing/tampering risk). Prefer TLS or a reverse proxy in production. Same effect as `api.allow_insecure_http: true`. The default **Docker** `CMD` passes this so the image runs without mounted certs. |
| `--validate-config`     | *(flag)*          | Pre-flight: parse config, check each target’s connector type/driver and required keys; **WARN** on unset `*_from_env` vars (not errors). No network or DB. Exit **0** with `[OK]` or **1** with `[INVALID]`. Incompatible with `--web`, `--reset-data`, and `--export-audit-trail`. |
| `--diff`                | `SESSION_A SESSION_B` | Compare findings between two scan session UUIDs in SQLite; prints new, resolved, and severity-changed rows. Exit **0** unless `--fail-on-new-high` and new **HIGH** findings exist (exit **1**). Unknown session UUID → exit **2**. Incompatible with `--web`, `--reset-data`, `--export-audit-trail`, and `--validate-config`. |
| `--fail-on-new-high`    | *(flag)*          | With `--diff`: exit **1** when `SESSION_B` has any new **HIGH** finding vs `SESSION_A` (CI regression gate). |
| `--export-dsar`         | `SESSION_ID`      | Export findings for one scan session as DSAR-oriented JSON (metadata-first; LGPD Art. 18 / GDPR Art. 15 framing). Print to **stdout** or use `--dsar-output PATH`. Unknown or empty session → empty `findings_by_source`, exit **0**. Incompatible with `--web`, `--reset-data`, `--export-audit-trail`, `--validate-config`, and `--diff`. |
| `--dsar-output`         | `PATH`            | Write DSAR JSON to `PATH` instead of stdout. Requires `--export-dsar`. |
| `--dsar-include-samples`| *(flag)*          | With `--export-dsar`: include raw sample fields from stored finding rows when present (SQLite stores metadata only by default). |
| `--reset-data`          | *(flag)*          | Dangerous maintenance operation: wipe all scan sessions, findings and failures from SQLite, delete generated reports/heatmaps under `report.output_dir`, and record the wipe in `data_wipe_log`. Does not start a scan.                                                             |
| `--export-audit-trail`  | *(optional path)* | Export a JSON audit trail from SQLite (`data_wipe_log`, session summary, `dashboard_transport`, **`maturity_assessment_integrity`** when the maturity POC has stored rows — same counts as **`GET /status`**). Omit path or use `-` for **stdout**; otherwise write to the given file. Does **not** modify the DB. Cannot be combined with `--web` or `--reset-data`.                             |
| `--tenant`              | *(none)*          | Optional customer/tenant name for the scan in CLI mode. Stored on the session and surfaced on dashboard and reports.                                                                                                                                                                |
| `--technician`          | *(none)*          | Optional technician/operator responsible for the scan in CLI mode. Stored on the session and surfaced on dashboard and reports.                                                                                                                                                     |
| `--scan-compressed`     | *(flag)*          | One-shot override: enable archive scanning as if `file_scan.scan_compressed` were true (zip, tar, 7z, …).                                                                                                                                                                           |
| `--content-type-check`  | *(flag)*          | One-shot override: enable magic-byte / content-type inference as if `file_scan.use_content_type` were true (extension vs true format — simple cloaking).                                                                                                                                                 |
| `--scan-stego`          | *(flag)*          | One-shot override: enable rich-media stego **hints** as if `file_scan.scan_for_stego` were true (byte-entropy heuristic on image/audio/video — not proof of hidden data). May increase reads on those files.                                                                                                |
| `--jurisdiction-hint`   | *(flag)*          | Opt-in for this run: enable heuristic jurisdiction notes on the Excel **Report info** sheet (e.g. US-CA CCPA/CPRA, Colorado, Japan APPI) when metadata signals suggest possible relevance. Not a legal conclusion. Same effect as `report.jurisdiction_hints.enabled: true` for this process; stores the opt-in on the session. |
<!-- markdownlint-enable MD060 -->

### Optional licensing tamper-evidence (enforced installs)

Some enterprise deployments require explicit **tamper-evidence hooks** beside `licensing.mode: enforced`:

- **`DATA_BOAR_EXPECTED_BUILD_DIGEST`** — compares to the embedded line in **`core/licensing/_build_digest.txt`** (generated at build time via **`scripts/generate_build_digest.py`** — see **`docs/RELEASE_INTEGRITY.md`**). Mismatch ⇒ **TAMPERED** (blocks scans when enforcement is active).
- **`DATA_BOAR_RELEASE_MANIFEST_PATH`** or **`licensing.manifest_path`** — optional SHA-256 manifest JSON verified at startup when provided (**same doc**).

**Roadmap:** **SQLite anchor**, **startup re-verify**, and **trust-level downgrade** unrelated to licensing-only checks remain **planned** (**`docs/plans/PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md`** — Phase **E.11** JSON export ✅; anchors ⬜).

### Outcomes

## Zero-config demo (`--demo`)

```bash
data-boar --demo
# or from a clone:
uv run python main.py --demo
```

- **Not** a config-driven one-shot audit: `--demo` **does not** read `config.yaml` from the current working directory.
- Prepares `/tmp/data_boar_demo/` (platform temp dir + `data_boar_demo/`) with `demo.config.yaml`, synthetic corpus, `reports/`, and `audit_results.db`, then runs an initial scan and keeps the dashboard on **`127.0.0.1`** with plaintext HTTP.
- **Output:** Console banner with workspace path and dashboard URL (default port **8088**). Temp tree is removed when the process exits.
- See also [QUICKSTART.md](../QUICKSTART.md) (*Caminho 0*) and `man 1 data-boar` (`--demo`).

## One-shot audit (no `--web`)

```bash
# Minimal run
python main.py --config config.yaml

# Tag scan with tenant and technician metadata
python main.py --config config.yaml --tenant "Acme Corp" --technician "Alice V."
```

- Loads config, runs a full audit of all targets (databases, filesystems, APIs, shares as configured).
- Creates a new session (UUID + timestamp), writes findings to the local SQLite DB (including optional `tenant_name` and `technician_name`), then generates the Excel report (and heatmap) for that session.
- **Output:** Console prints runtime trust `INFO` lines (stdout + stderr), then `Scan session: <session_id>` and `Report written: <path>` (or "No findings to report."). If trust is unexpected, the CLI explicitly warns: **THERE IS SOMETHING DIFFERENT AND UNEXPECTED IN THIS RUNTIME**.
- Report path is under `report.output_dir` from config (default: current directory). File name: `Relatorio_Auditoria_<session_id>.xlsx` (and `heatmap_<session_id>.png`).
- Report now includes a **Data source inventory** sheet with best-effort source metadata (target, source type, product/version, API/protocol hint, transport security hint, raw details).

## REST API server (`--web`)

**Transport:** you must either use **HTTPS** (PEM cert + key on the CLI or under `api` in config) or **explicitly** accept plaintext with **`--allow-insecure-http`** (or `api.allow_insecure_http: true`). Otherwise `main.py --web` exits with code **2** and an error on stderr. **`GET /status`** and **`GET /health`** include a `dashboard_transport` object (`mode`, `tls_active`, `summary`, etc.) and an **`enterprise_surface`** object (transport + license trust + global API-key posture; optional per-route RBAC is summarized under **`enterprise_surface.access_surface.rbac`** — **`enabled`** when `api.rbac` is on and the tier allows **`dashboard_rbac`**, otherwise **`not_implemented`**); plaintext mode shows a **banner** on dashboard pages.

```bash
# TLS (example paths; keep keys out of git)
python main.py --config config.yaml --web --https-cert-file server.crt --https-key-file server.key --port 8088

# Plaintext — lab / loopback only (explicit opt-in)
python main.py --config config.yaml --web --allow-insecure-http --port 8088

# Listen on all interfaces (overrides config / API_HOST; use only with network controls):
python main.py --config config.yaml --web --allow-insecure-http --host 0.0.0.0 --port 8088
```

- Loads config and starts the FastAPI server on **`<bind>:<port>`**. Default bind is **`127.0.0.1`** unless you set `api.host`, `API_HOST`, or **`--host`** (CLI wins). The official Docker image sets `API_HOST=0.0.0.0` and passes **`--allow-insecure-http`** in `CMD` so the container starts without mounted certificates; mount cert/key and override `CMD` for HTTPS.
- **Outcome:** Server runs until interrupted. No scan runs automatically; you trigger scans and download reports via the API (see below).
- **Note:** The API process loads its own config at startup from the **`CONFIG_PATH`** environment variable, or `config.yaml` in the current working directory. To use a different file when running the server, set `CONFIG_PATH`:

  ```bash
  set CONFIG_PATH=production.yaml   # Windows
  export CONFIG_PATH=production.yaml   # Linux/macOS
  python main.py --web --port 8088
  ```

### Configuration file (first run)

**Prefer YAML** (`.yaml` / `.yml`) for new projects: you can add comments, review diffs, and merge changes safely. **`--config`** defaults to **`config.yaml`** in the current working directory; that file name is **gitignored** at the repo root so you do not accidentally commit LAN paths or secrets — use a **copy** of a tracked sample in a private path or set **`CONFIG_PATH`**.

| What to copy | Use when |
| ------------ | -------- |
| **[`deploy/samples/config.starter-lgpd-eval.yaml`](../deploy/samples/config.starter-lgpd-eval.yaml)** | **Recommended** first lab or evaluation: two fictional filesystem folders, one PostgreSQL-style target with `pass_from_env`, `scan.max_workers`, timeouts, **`rate_limit`**, minimal ML/DL terms, and **commented** optional blocks (compressed archives, `file_passwords`, `learned_patterns`, pattern files, `detection.cnpj_alphanumeric`, `connector_format_id_hint`, API key, jurisdiction hints). Replace paths and set env vars — values use **RFC 5737** documentation IPs and placeholder paths only. |
| **[`deploy/config.example.yaml`](../deploy/config.example.yaml)** | **Smallest** valid file for Docker (`targets: []`, `/data` paths). |
| **Legacy JSON** in [`config/config.json`](../config/README.md) | Loader still accepts the old **`databases`** + **`file_scan.directories`** shape; **new work should use YAML** — see [`config/README.md`](../config/README.md). |

**Hub (same links from `docs/`):** [samples/README.md](samples/README.md) ([pt-BR](samples/README.pt_BR.md)). **Build targets from a spreadsheet:** [deploy/scope_import.example.csv](../deploy/scope_import.example.csv) and [ops/SCOPE_IMPORT_QUICKSTART.md](ops/SCOPE_IMPORT_QUICKSTART.md) ([pt-BR](ops/SCOPE_IMPORT_QUICKSTART.pt_BR.md)) — written for counsel, DPOs, and programme leads who are **not** full-time infra staff.

---

## 2. Deploying and accessing the web API

### Deploying the server

### Automated deployment with Ansible (two paths)

For reproducible, one-command deployments on Debian/Ubuntu servers, Data Boar ships
Ansible playbooks under `deploy/ansible/`. Two paths are available:

**Path A — Simple (Docker Compose, existing Docker install):**

```bash
# 1. Install Ansible on your control machine
sudo apt install ansible
ansible-galaxy collection install community.docker

# 2. Clone the repo
git clone https://github.com/DataBoar/data-boar.git
cd data-boar/deploy/ansible

# 3. Configure your inventory
cp inventory/hosts.ini.example inventory/hosts.ini
# Edit hosts.ini: add your server IP and SSH user

# 4. Dry-run, then apply
ansible-playbook site.yml --check
ansible-playbook site.yml
```

**Path B — Full stack (Docker CE + Swarm + ctop + Data Boar service, fresh server):**

```bash
# Steps 1-3 same as Path A, then:
ansible-playbook site-full.yml --check
ansible-playbook site-full.yml
```

This installs Docker CE from the official repository, initialises a single-node Swarm,
installs `ctop` for container monitoring, and deploys Data Boar as a Swarm service.

After either path, Data Boar is reachable at `http://<server>:8088`.
See `deploy/ansible/README.md` for variables, multi-node Swarm, and troubleshooting.

## Option: run from Docker (no Git clone)

Pre-built images are on Docker Hub: `fabioleitao/data_boar:latest` ([hub.docker.com/r/fabioleitao/data_boar](https://hub.docker.com/r/fabioleitao/data_boar)). Pull and run with a mounted config at `/data/config.yaml` (see README “Deploy with Docker” and [docs/deploy/DEPLOY.md](deploy/DEPLOY.md) ([pt-BR](deploy/DEPLOY.pt_BR.md))). You can use this instanced container instead of installing from source.

1. **Install** the application and optional dependencies (e.g. `.[postgres]`, `.[sql-all]`, `.[nosql]`, `.[shares]`) as in the README and [TECH_GUIDE.md](TECH_GUIDE.md) (*Supported databases*).
1. **Cross-distro `pipx` reality check (Linux):** before rollout on RHEL/Void/musl/no-AVX fleets, read [TROUBLESHOOTING.md](TROUBLESHOOTING.md) and the matrix in [ops/OS_COMPATIBILITY_TESTING_MATRIX.md](ops/OS_COMPATIBILITY_TESTING_MATRIX.md) (RHEL 8/9 explicit Python 3.12 step; Void-musl/no-AVX wheelhouse path; RHEL/CentOS 7 Docker-only). Docker remains a fallback deployment option, not the primary wheelhouse route.
1. **Prepare** a config file (e.g. `config.yaml`) with `targets`, `file_scan`, `report`, and optionally `api.port`.
1. **Set config path** (optional):

   `CONFIG_PATH=/etc/data-boar/config.yaml` (or your path) so the API loads that file regardless of working directory.

1. **Run the server:**

   ```bash
   python main.py --config config.yaml --web --port 8088
   ```

   Or with uvicorn directly (config is still read from `CONFIG_PATH` or `config.yaml` in the process working directory):

   ```bash
   uvicorn api.routes:app --host 0.0.0.0 --port 8088
   ```

1. **Binding:** `python main.py --web` uses the same resolution as above (`--host`, then `api.host`, then `API_HOST`, then **`127.0.0.1`**). Direct **uvicorn** defaults differ by version; pass **`--host`** explicitly if you need a specific interface.
1. **Production:** Run behind a reverse proxy (nginx, Traefik, Caddy, or similar), use a process manager (systemd, supervisord), or a container; ensure `CONFIG_PATH` and `report.output_dir` are set appropriately and that the process can write to the output directory and the SQLite path. The application behaves correctly behind NAT, load balancers, and reverse proxies: when TLS is terminated at the proxy, set **X-Forwarded-Proto: https** so security headers (e.g. HSTS) and scheme detection work. See [SECURITY.md](../SECURITY.md) for HTTP security headers.

### Base URL and accessing the API

- **Base URL:** `http://<host>:<port>/`

  Example: `<http://localhost:8088>/` or `<http://your-server:8088>/`

- **OpenAPI docs (interactive):**
- Swagger UI: `<http://localhost:8088/doc>s`
- ReDoc: `<http://localhost:8088/redo>c`
- **Authentication:** By default the API does not require authentication; secure it at the reverse proxy or network level if exposed. You can optionally enable a shared API key: set `api.require_api_key: true` and either `api.api_key` (avoid committing secrets) or `api.api_key_from_env: "VAR"` with the variable set **before** process start — see **[API_KEY_FROM_ENV_OPERATOR_STEPS.md](ops/API_KEY_FROM_ENV_OPERATOR_STEPS.md)**. **Step-by-step (key + HTTPS, Let’s Encrypt, lab certs):** **[SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.md](ops/SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.md)** ([pt-BR](ops/SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.pt_BR.md)). **For production we recommend `require_api_key: true` plus `api_key_from_env`** so the secret never lives in tracked YAML.
- **WebAuthn (optional — Phase 1 JSON API + Phase 1b HTML session):** When **`api.webauthn.enabled: true`**, set the environment variable named by **`api.webauthn.token_secret_from_env`** (default **`DATA_BOAR_WEBAUTHN_TOKEN_SECRET`**) **before** starting the process; startup fails if the secret is missing. This enables **vendor-neutral** passkey registration/authentication JSON endpoints under **`/auth/webauthn/`** (open-source **`webauthn`** library on PyPI — not Bitwarden- or Microsoft-specific). **`api.require_api_key` does not apply** to these paths or to **`GET /{locale}/login`** (so you can open the sign-in page when a global API key is on). Align **`api.webauthn.origin`** and **`api.webauthn.rp_id`** with the browser URL (HTTPS recommended). Credentials persist in SQLite (`webauthn_credentials`); **`--reset-data` / wipe** clears them. **After at least one passkey is registered**, locale-prefixed dashboard pages (**`/`, `/config`, `/reports`, `/assessment`, …**) require a valid WebAuthn session cookie unless you only visit **`help`**, **`about`**, or **`login`** (GET). Use **`/{locale}/login`** in the browser ( **`/static/webauthn-login.js`** ) to register or sign in; mutating HTML forms (**`POST …/config`**, **`POST …/assessment`**) **always** require a signed **CSRF** synchronizer token (**#1231** — independent of whether the WebAuthn gate is active; optional stable key via **`DATA_BOAR_HTML_CSRF_SECRET`**, else the WebAuthn token secret when set, else a process-ephemeral secret). Optional **per-route RBAC** (next bullet; **#86** Phase **2**) layers on top when enabled. See **[ADR 0033](adr/ADR-0033-webauthn-open-relying-party-json-endpoints.md)**.
- **RBAC (optional — Phase 2, Pro+ `dashboard_rbac`):** When **`api.rbac.enabled: true`** and the effective tier allows **`dashboard_rbac`** (`licensing.effective_tier` in YAML, or JWT **`dbtier`** when enforcement is on — same as other tier-gated features), protected routes require **named roles**: `admin` (all), `dashboard`, `scanner`, `reports_reader`, `config_admin`. The **global API key** (when present and matching) receives **`api.rbac.api_key_roles`**; WebAuthn sessions use the **`roles_json`** column on the matching `webauthn_credentials` row (JSON array of role names), or **`api.rbac.default_roles`** when **`roles_json`** is unset. **401** if no principal; **403** if roles are insufficient. **`GET /status`** and **`GET /health`** include **`enterprise_surface.access_surface.rbac`** (`enabled` vs `not_implemented`). **Community** tier cannot enable in-product RBAC; use reverse-proxy or network controls. See the internal plan file **`PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md`** (listed under **Internal and reference** in `docs/README.md`; GitHub **#86**); enterprise **SSO/OIDC** remains Phase **3**.
- **`GET /health` (always public):** Intended for load balancers and orchestrators. Returns JSON with at least `status`, a **public** `license` summary, `dashboard_transport`, and `enterprise_surface`. **No** `X-API-Key` / Bearer header is required or checked.
- **All other HTTP routes** (HTML pages, `GET /status`, `POST /scan`, locale-prefixed dashboard paths such as `GET /en/config`, OpenAPI `/docs`, etc.): when `require_api_key` is true and a key is configured, send **X-API-Key** or **Authorization: Bearer &lt;key&gt;**. **401** = missing or invalid key. **503** = `require_api_key` is true but no key could be resolved (fix config/env). **`main.py --web` refuses to start (exit code 2)** in that misconfiguration so you do not accidentally expose an open dashboard.
- **Rollout:** Inventory API clients (scripts, cron, CI, probes), enable **staging** first with TLS + API key where applicable, then production with a short compatibility window if needed — **[SECURE_BY_DEFAULT_BLOCKERS_AND_MIGRATION.md](ops/SECURE_BY_DEFAULT_BLOCKERS_AND_MIGRATION.md)**. After enabling HTTPS or plaintext HTTP explicitly, use **`GET /status` / `GET /health`** and **`--export-audit-trail`** (`dashboard_transport` in the JSON) to verify posture.
- See also [SECURITY.md](../SECURITY.md#optional-api-key-enterprise) and the Configuration section below.

### Web dashboard {#web-dashboard}

When the API server is running, a **simple web dashboard** is available in the browser. **HTML pages use a locale prefix** (`/en/…`, `/pt-br/…` by default). Visiting `/`, `/config`, `/reports`, `/help`, or `/about` without a prefix **redirects** to the best match: **`db_locale` cookie** (if valid), then **`Accept-Language`**, then **`locale.default_locale`** in config (see `locale` block below). **JSON API routes** (`/status`, `/scan`, `/reports/{session_id}`, …) stay **without** a locale prefix.

**Walkthrough (non-technical, first run):**

1. **Open** the dashboard in a browser: `http://127.0.0.1:8088/en/` (or `/pt-br/`). It must be running first — see [REST API server (`--web`)](#rest-api-server---web) (plaintext needs `--allow-insecure-http`; off-loopback use TLS).

   ![Dashboard home — scan form](img/dashboard/en/scan-start.png)

2. **(Optional) Tag the run:** type a **tenant/customer** and **technician/operator** in the form fields — these appear on the report's **Report info** sheet.
3. **Check targets (optional):** open **Configuration** and confirm databases, filesystems, or other targets are listed — the next scan uses exactly that file.

   ![Configuration page — YAML targets](img/dashboard/en/config.png)

4. **Start scan:** click **Start scan**. The page polls status while the audit runs (`POST /scan` under the hood).
5. **Open Reports:** when the scan finishes, go to the **Reports** page (`/en/reports` or `/pt-br/reports`).
6. **Download:** click **Download** on the session row to get the Excel report (and heatmap). No shell or API call needed.

   ![Reports — Download button per session](img/dashboard/en/reports-download.png)

| Page              | URL (examples)                            | Description                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| ---               | ---                                       | ---                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| **Dashboard**     | `http://<host>:<port>/en/`               | Scan status (running/idle, current session, findings count), quantity/quality summary (DB findings, FS findings, failures, total), **“Progress over time” chart** (total findings + risk score per session), form inputs for **tenant/customer** and **technician/operator** before starting a scan, and a “Start scan” button. Recent sessions table shows session ID, started date, tenant, technician, findings, failures, and a download link. |
| **Reports**       | `http://<host>:<port>/en/reports`         | List of all scan sessions (session ID, started/finished, status, tenant, technician, DB/FS/failures counts) with a “Download” link per session (regenerates and downloads the Excel report).                                                                                                                                                                                                                                                       |
| **Configuration** | `http://<host>:<port>/en/config`         | Edit the scan configuration (YAML) in the browser. “Save configuration” writes to the config file (see `CONFIG_PATH` or `config.yaml`). Changes apply to the next scan.                                                                                                                                                                                                                                                                            |
| **Help**          | `http://<host>:<port>/en/help`           | Quickstart, config examples, and links to README/USAGE.                                                                                                                                                                                                                                                                                                                                                                                             |
| **Sign in (WebAuthn)** | `http://<host>:<port>/en/login`     | Browser passkey registration and sign-in when **`api.webauthn.enabled`**; static **`webauthn-login.js`**. If WebAuthn is off, the page explains that fact. When **no** passkey is registered yet, the HTML dashboard stays reachable without this page (bootstrap). After **one or more** passkeys exist, unauthenticated visitors are redirected here from other dashboard URLs.                                                                  |
| **About**         | `http://<host>:<port>/en/about`          | Application name, version, author, and license (same as repository LICENSE).                                                                                                                                                                                                                                                                                                                                                                        |
| **Self-assessment (POC)** | `http://<host>:<port>/en/assessment` | Optional placeholder when **`api.maturity_self_assessment_poc_enabled`** is on; **404** when off. **Tier:** `licensing.effective_tier` in YAML for lab, or **`dbtier`** in the JWT when `licensing.mode: enforced` (**Pro+** needed for this feature). When enforcement is on and the license JWT is valid, **`dbtier` overrides YAML `effective_tier`** for this gate (same rule as other tier-gated dashboard features). Optional **`api.maturity_assessment_pack_path`** points to a YAML questionnaire pack (`core/maturity_assessment/pack.py`); optional per-answer **`scores`** in YAML drive a **rubric total** on the post-submit summary. Optional **`DATA_BOAR_MATURITY_INTEGRITY_SECRET`** (or **`api.maturity_integrity_secret_from_env`**) enables **HMAC-SHA256 per row** (tamper-evident; not encryption). **`GET /status`** includes **`maturity_assessment_integrity`** when you need to demo integrity. After **POST** submit, the redirect includes **`saved=1`** and **`batch=`** (submit id); the HTML shows a **submission summary** (rows stored, rubric score when configured, HMAC counts) and, when any answers exist in SQLite, a **recent submissions** table grouped by **batch** (newest first). **Export:** `GET /{locale}/assessment/export?batch=<id>&format=csv` or `format=md` returns an **attachment** (download); there is no separate on-disk export path—save via browser or redirect `curl` to a file. When **`api.require_api_key`** is on, send **`X-API-Key`** or **`Authorization: Bearer`** like other dashboard routes. No proprietary questionnaire text in the public repo. |

**Locale configuration (optional):** under top-level `locale`: `default_locale` (e.g. `en`), `supported_locales` (e.g. `[en, pt-BR]`), `cookie_name` (default `db_locale`), `cookie_max_age_seconds`. UI strings are loaded from `api/locales/<tag>.json` (no gettext in v1). Maintainer-facing architecture notes: ``docs/plans/completed/PLAN_DASHBOARD_I18N.md`` (not linked from product-only reading paths per ADR 0004).

The **Start scan** button sends `POST /scan` and triggers a **full audit of all targets** in the current configuration (the same databases, filesystems, APIs, and options defined in your config file). Saving the Configuration page updates the config used for the next scan. The dashboard uses the same API under the hood (`/status`, `/scan`, `/list`, `/reports/{session_id}`). Status polls automatically when a scan is running. No separate frontend build (Python + Jinja2 + minimal CSS/JS).

### API endpoints (summary)

| Method  | Endpoint                            | Purpose                                                                                                                                                |
| ---     | ---                                 | ---                                                                                                                                                    |
| `POST`  | `/scan` or `/start`                 | Start a full audit in the background. Returns `session_id`. Optional JSON body: `tenant`, `technician`, `scan_compressed`, `content_type_check`, `scan_for_stego`, `jurisdiction_hint` (booleans for run-local toggles). |
| `POST`  | `/scan_database`                    | One-off scan of a single database (body: name, host, port, user, password, database, driver, optional tenant/technician, optional `jurisdiction_hint`). Returns `session_id`.        |
| `GET`   | `/status`                           | Current run state: `running`, `current_session_id`, `findings_count`, plus `runtime_trust`, `dashboard_transport`, `enterprise_surface`, and **`maturity_assessment_integrity`** (HMAC summary for POC questionnaire rows when configured). |
| `GET`   | `/report`                           | Download the **last generated** Excel report (or generate from last session if none).                                                                  |
| `GET`   | `/heatmap`                          | Download the **last generated** heatmap PNG (sensitivity/risk heatmap for the most recent session).                                                    |
| `GET`   | `/logs`                             | Download the most recent `audit_YYYYMMDD.log` file with connection/finding entries.                                                                    |
| `GET`   | `/list`                             | List past sessions (JSON). For the HTML list, use `/en/reports` or `/pt-br/reports` (locale prefix). Each entry includes tenant/technician when set.   |
| `GET`   | `/reports/{session_id}`             | **Regenerate** and download the Excel report for that session.                                                                                         |
| `GET`   | `/heatmap/{session_id}`             | **Regenerate** the report (if needed) and download the heatmap PNG for that session.                                                                   |
| `GET`   | `/logs/{session_id}`                | Download the audit log for that `session_id` (content match first; UTC-day fallback to `audit_YYYYMMDD.log` when needed), for session-level trace analysis. |
| `POST`  | `/auth/webauthn/registration/options` | **Optional.** When **`api.webauthn.enabled`**, returns WebAuthn creation options JSON plus opaque `state` (see ADR 0033). |
| `POST`  | `/auth/webauthn/registration/verify` | **Optional.** Verify registration response; stores passkey in SQLite; sets session cookie. |
| `POST`  | `/auth/webauthn/authentication/options` | **Optional.** Authentication options JSON + `state`. |
| `POST`  | `/auth/webauthn/authentication/verify` | **Optional.** Verify authentication; refreshes cookie. |
| `GET`   | `/auth/webauthn/status`             | **Optional.** `{ enabled, registered_credentials, session_authenticated }` when WebAuthn is enabled. |
| `POST`  | `/auth/webauthn/logout`             | **Optional.** Clear WebAuthn session cookie. |
| `PATCH` | `/sessions/{session_id}`            | Set or clear tenant/customer name for an existing session. Body: `{ "tenant": "..." }`.                                                                |
| `PATCH` | `/sessions/{session_id}/technician` | Set or clear technician/operator name for an existing session. Body: `{ "technician": "..." }`.                                                        |
| `GET`   | `/about`                            | About page (HTML): application name, version, author, license.                                                                                         |
| `GET`   | `/about/json`                       | Machine-readable about info (name, version, author, license, copyright).                                                                               |
| `GET`   | `/health`                           | Liveness/readiness for Docker and Kubernetes.                                                                                                          |

---

## 3. Using the API (examples)

**For automation / scripting** — use the `curl` examples below when you need CI, cron jobs, or integrations. For DPO, legal, and other non-technical users, prefer the [web dashboard walkthrough](#web-dashboard) and [Downloading reports (web)](#downloading-reports-web) first.

### Start a full audit

```bash
# Minimal: start a scan with default metadata
curl -X POST http://localhost:8088/scan

# Start a scan tagged with tenant/customer and technician/operator
curl -X POST http://localhost:8088/scan \
  -H "Content-Type: application/json" \
  -d '{ "tenant": "Acme Corp", "technician": "Alice V." }'
```

## Response (200)

```json
{
  "status": "started",
  "session_id": "a1b2c3d4-20250301_143022"
}
```

- Use `session_id` to download that session’s report later (see “Download reports” below).

### Check status

```bash
curl http://localhost:8088/status
```

## Response (200) — GET /status

```json
{
  "running": true,
  "current_session_id": "a1b2c3d4-20250301_143022",
  "findings_count": 42
}
```

- When `running` is `false`, the audit for `current_session_id` has finished.

### One-off database scan

```bash
curl -X POST http://localhost:8088/scan_database \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Ad-hoc Postgres",
    "host": "db.example.com",
    "port": 5432,
    "user": "audit",
    "password": "secret",
    "database": "mydb",
    "driver": "postgresql+psycopg2",
    "tenant": "Acme Corp",
    "technician": "Alice V."
  }'
```

**Response (200):** Same as `/scan`: `{"status": "started", "session_id": "..."}`.

### List past sessions (to choose a report)

```bash
curl http://localhost:8088/list
```

## Response (200) — GET /list

```json
{
  "sessions": [
    {
      "session_id": "a1b2c3d4-20250301_143022",
      "started_at": "2025-03-01LAB-NODE-01:30:22",
      "finished_at": "2025-03-01LAB-NODE-01:35:10",
      "status": "completed",
      "tenant_name": "Acme Corp",
      "technician_name": "Alice V.",
      "database_findings": 12,
      "filesystem_findings": 30,
      "scan_failures": 0
    }
  ]
}
```

Use any `session_id` to download that session’s report (see below).

### Download current (last) report

```bash
curl -o report.xlsx http://localhost:8088/report
```

- Returns the **last generated** Excel file.
- If no report exists, the server may try to generate one from the current or most recent session; if none exists, you get **404** with body like: `{"detail": "Report not available. Run a scan first."}`.

### Download current (last) audit log

```bash
curl -o audit.log http://localhost:8088/logs
```

- Returns the most recent `audit_YYYYMMDD.log` file written by the application.
- If no log file is found, you get **404** with `{"detail": "No log files found."}`.

**Audit log line format (read this before interpreting paths):** Lines look like `Finding: source | target_label | location | sensitivity | pattern` and `Connected: target_label (type) at location`. The **`target_label`** is a **sanitized, unique** per-target name derived from config (`audit_log_name`), not necessarily identical to the raw `name` string. For **filesystem** targets, **`location`** is usually a **POSIX path relative to the resolved scan root** (no drive letter or home directory). The scan root itself is logged as `folder_name?8_hex` (not a full absolute path). If a file **resolves outside** the scan root (e.g. symlink), **`location`** becomes `target_label?12_hex` instead of leaking an absolute path—use the SQLite/Excel row for the authoritative path. Remote share connectors that scan archives via a temp file keep archive-style locations like `archive.zip|inner/path.txt` in the log.

### Download current (last) heatmap PNG

```bash
curl -o heatmap.png http://localhost:8088/heatmap
```

- Returns the **last generated** heatmap PNG for the most recent session (creating it along with the report if needed).
- If no suitable session exists, you get **404** with a message like `{"detail": "Heatmap not available. Run a scan first."}`.

### Download report for a specific (previous) session

```bash
curl -o report_20250301.xlsx "http://localhost:8088/reports/a1b2c3d4-20250301_143022"
```

- **Regenerates** the Excel (and heatmap) for that `session_id` and returns the file.
- If the session has no data or generation fails, you get **404** with `{"detail": "No data for session ... or report generation failed."}`.

### Download heatmap for a specific (previous) session

```bash
curl -o heatmap_20250301.png "http://localhost:8088/heatmap/a1b2c3d4-20250301_143022"
```

- Regenerates the report (and heatmap) for that `session_id` if needed and returns the PNG.
- If no heatmap is available for that session (e.g. no findings), you get **404** with `{"detail": "Heatmap not available for session ..."`}.

### Download audit log that contains a specific session

```bash
curl -o audit_20250301.log "http://localhost:8088/logs/a1b2c3d4-20250301_143022"
```

- Scans available `audit_YYYYMMDD.log` files (newest first) and returns the first one whose content contains that `session_id`.
- If no such log file is found, you get **404** with `{"detail": "No log file contains session_id ..."`}.

## Typical workflow

1. `POST /scan` → get `session_id`.
1. Poll `GET /status` until `running` is `false`.
1. Download last report: `GET /report` → save as Excel.
1. Or list sessions: `GET /list`, then download a specific one: `GET /reports/<session_id>`.

---

## 4. Configuration: targets and credentials

The application uses a **single** config file (YAML or JSON). The API loads it from:

- Environment variable **`CONFIG_PATH`**, or
- **`config.yaml`** in the process working directory.

CLI uses the path you pass with `--config` (e.g. `config.yaml`). For the **web server**, ensure the process either has `CONFIG_PATH` set or is started in a directory that contains `config.yaml` (or the path you use).

### Config file location and shape

- **Location:** Any path; typical names: `config.yaml`, `config/config.json`. Legacy `config/config.json` with `databases` and `file_scan.directories` is normalized automatically.
- **Root keys:** `targets`, `file_scan`, `report`, `api`, `sqlite_path`, `scan`, **`rate_limit`**, **`timeouts`**, optional **`sql_sampling`** (hierarchical row caps for SQL/Snowflake targets), optional `ml_patterns_file`, `dl_patterns_file`, `regex_overrides_file`, `sensitivity_detection`, `learned_patterns`, **`pattern_files_encoding`**.

### Starter config (copy-paste) and where to look first {#starter-config-samples}

If you are **new to the product** (counsel, DPO, audit lead, or anyone validating what the scanner can do) and need **one file** to align with IT without reading every guide first:

1. Open the **hub** **[docs/samples/README.md](samples/README.md)** ([pt-BR](samples/README.pt_BR.md)) — it links the starter YAML, the minimal Docker template, the scope CSV, and explains **`config/config.json`** (legacy JSON only).
1. Copy **[deploy/samples/config.starter-lgpd-eval.yaml](../deploy/samples/config.starter-lgpd-eval.yaml)** to your machine as **`config.yaml`** (any writable folder). The file is **Runnable defaults** (two folders + one database + rate limit + ML/DL terms) plus **commented optional** sections (e.g. `scan_compressed`, `file_passwords`, `learned_patterns`, external pattern files) so you can enable features gradually.
1. Replace the **fictitious** paths (`/opt/lgpd-demo/...`) and the database host **`192.0.2.10`** (documentation-only TEST-NET) with your lab paths and hostname.
1. Set the environment variable referenced by **`pass_from_env`** (example: `DEMO_DB_PASSWORD`) **before** starting the process — do not paste real passwords into YAML for production.
1. Run a one-shot scan: `uv run python main.py --config config.yaml` or start the dashboard with the same `--config` path.

The starter is **not** as exhaustive as **`docs/compliance-samples/`** (those are for **framework-specific** tuning).

For **Docker**, start from **[deploy/config.example.yaml](../deploy/config.example.yaml)** (`targets: []`, `/data` paths) and merge sections from the starter if you need a fuller lab profile.

**Legacy JSON:** The repo’s **`config/config.json`** illustrates the old `databases` + `file_scan.directories` layout only — see **[config/README.md](../config/README.md)**. **YAML is preferred** for new projects.

By default the web API binds to **`127.0.0.1` (loopback)** when started via the CLI (`python main.py --web ...`). When you run the official Docker image, the container sets `API_HOST=0.0.0.0` so the published port works from outside Docker Desktop/WSL.

If you run behind a reverse proxy or have special network constraints, you can still override with `api.host` in the config (e.g. `0.0.0.0` / `127.0.0.1`)—but keep the safe loopback default unless the runtime is explicitly fenced.

### Scope import from CSV (config fragment) {#scope-import-from-csv-config-fragment}

You can **bootstrap `targets`** from a **canonical CSV** (for example an export from a spreadsheet) and emit a **YAML fragment** to paste under `targets:` or save as a separate file for review. This does **not** live-merge into an existing config file; operators merge manually or with their own tooling.

- **Script:** `uv run python scripts/scope_import_csv.py <file.csv>` writes YAML to stdout; `-o out.yaml` writes a file. `--no-merge-hint` omits the leading comment block.
- **Required column:** `type` (e.g. `filesystem`, `postgresql`, `mysql`, `database`, `smb`, `nfs`). Header names are matched case-insensitively; spaces become underscores.
- **Common columns:** `name`, `path`, `host`, `port`, `database`, `driver`, `user`, `pass_from_env`, `user_from_env`, `share`, `domain`, `export_path`, `recursive`, plus optional breadcrumbs: `asset_id`, `hostname`, `ip`, `tags` (use `|` or `;` to separate multiple values), `path_hints`, `port_hints`, `source_system`, `source_export_type`, `confidence`. Optional metadata is stored under each target’s `scope_import` key.
- **Secrets:** Prefer `pass_from_env` / `user_from_env` in the CSV; **do not** put live passwords in the CSV file.
- **Privacy:** Exports may contain sensitive infrastructure metadata—handle like config (permissions, no accidental commits). See [SECURITY.md](../SECURITY.md).
- **Example:** [`deploy/scope_import.example.csv`](../deploy/scope_import.example.csv).
- **Non-technical path:** [docs/ops/SCOPE_IMPORT_QUICKSTART.md](ops/SCOPE_IMPORT_QUICKSTART.md) ([pt-BR](ops/SCOPE_IMPORT_QUICKSTART.pt_BR.md)) — build the CSV from a spreadsheet or memory when no CMDB export exists yet.

Full behaviour is implemented in `config/scope_import_csv.py` (v1 focuses on `filesystem`, `database` / SQL aliases, `smb`, `nfs`).

### File encoding (config and pattern files)

Config and compliance sample files can use different character sets. The application supports this so multilingual terms (e.g. Japanese, Arabic, French) and legacy environments do not break in production.

- **Config file:** Read with **auto-detection**: UTF-8, UTF-8 with BOM, Windows ANSI (cp1252), and Latin-1 are tried in order. No need to set encoding for the main config file.
- **Pattern files** (`regex_overrides_file`, `ml_patterns_file`, `dl_patterns_file`): Read with the encoding set by **`pattern_files_encoding`** (default **`utf-8`**). Use this when your YAML/JSON is saved in another encoding (e.g. `cp1252`, `latin_1`, `utf-8-sig`). Invalid bytes are replaced so a single bad character does not crash the scan.
- **Recommendation:** Save all config and sample files in **UTF-8** for best compatibility with multilingual content (compliance samples for APAC, EMEA, etc.). The Excel report and heatmap output support Unicode.

Example in config:

```yaml
pattern_files_encoding: utf-8   # default; or cp1252, latin_1, utf-8-sig for legacy
regex_overrides_file: docs/compliance-samples/compliance-sample-uk_gdpr.yaml
ml_patterns_file: docs/compliance-samples/compliance-sample-pipeda.yaml
```

> **Optional (opt-in) toggle:** The `file_scan` block also accepts a boolean `use_content_type` key. When enabled, the scanner consults a small content-type helper (**magic bytes**) so **simple cloaking** does not win by default: the **filename extension** may suggest one kind of file (e.g. `.txt` or a non-text extension such as `.mp3`) while the **first bytes** reveal another (e.g. `%PDF-...`). That mismatch only fools **extension-only** routing; with this flag on, filesystem and share targets (SMB/WebDAV/SharePoint) apply a **narrow PDF slice** (treat as PDF when the header is PDF) plus **rich-media remapping** where implemented—see [TECH_GUIDE.md](TECH_GUIDE.md). The default remains extension-based; leave this off if you prefer the original behaviour and lowest I/O.
>
> **One-shot overrides (same run only):** CLI **`--content-type-check`** sets `use_content_type: true` for that process (like **`--scan-compressed`** for archives). The dashboard **Start scan** checkbox and **`POST /scan`** / **`POST /start`** JSON field **`content_type_check: true`** do the same for that API-triggered run only; the on-disk config is unchanged after the scan finishes.
>
> **Rich media (opt-in):** With **`file_scan.scan_rich_media_metadata: true`**, the scanner reads **bounded** text samples from image EXIF (Pillow), audio tags (**mutagen** — install `uv pip install -e ".[richmedia]"`), and video container/format tags via **ffprobe** when the `ffprobe` binary is on `PATH`. With **`file_scan.scan_image_ocr: true`**, it also runs **Tesseract** on a downscaled image (`pytesseract` in `.[richmedia]` plus system **`tesseract-ocr`**). **Privacy:** OCR processes **visible pixels**; only enable on paths you are allowed to read at that depth. Defaults for both flags are **false** to avoid surprise I/O and CPU.
>
> **`ocr_lang`** (default `eng`) and **`ocr_max_dimension`** (default `2000`, clamped 256–8000) tune OCR. When **`use_content_type`** is on, magic bytes can remap a **misleading extension** to image/audio/video (in addition to the PDF slice) so metadata/OCR runs on files whose **name** does not match the **real** container.
>
> **Subtitles (default):** Sidecar **`.srt`**, **`.vtt`**, **`.ass`**, **`.ssa`** are in the default `file_scan.extensions` list and are read as UTF-8 text (timing cues normalized) like other text files—no extra flag.
>
> **Additional formats (Tier 1 “data soup”):** The scanner can sample text from **`.epub`** (ZIP/XHTML), and—when optional dependencies are installed (`uv pip install -e ".[dataformats]"`)—from **`.parquet`**, **`.feather`**, **`.orc`** (PyArrow), **`.avro`** (fastavro), and **`.dbf`** (dbfread). Without those extras, extraction returns empty content for the binary columnar/legacy types (path/name analysis still applies). Add these extensions to `file_scan.extensions` if you use an explicit allow-list.
>
> **Steganography hints (opt-in):** **`file_scan.scan_for_stego: true`**, CLI **`--scan-stego`**, dashboard checkbox, or **`scan_for_stego: true`** on **`POST /scan`** appends a short **byte-entropy** line for image/audio/video paths to help spot unusually high-entropy payloads. This is a **weak heuristic**, not stego extraction. Same run-local restore pattern as `scan_compressed` / `use_content_type`.

### Credentials from environment (secrets not in config)

To keep secrets **out of the config file**, use **`*_from_env`** keys so the application reads values from environment variables at load time. This is the recommended pattern for production and for config files that may be shared or versioned.

**Requesting access from IT:** When you need to ask the IT team for permissions (e.g. shared folders, database accounts, API tokens), use the **minimal** access required. See [OPERATOR_IT_REQUIREMENTS.md](ops/OPERATOR_IT_REQUIREMENTS.md) for a per-source checklist of what to ask for (read-only, no admin), what we do *not* need, and a short justification so the request aligns with zero-trust or strict IAM. ([pt-BR](ops/OPERATOR_IT_REQUIREMENTS.pt_BR.md))

- **API key:** `api.api_key_from_env: "AUDIT_API_KEY"` (see Authentication above).
- **Targets (databases, REST, Power BI, etc.):**
- **Password:** `pass_from_env: "DB_PASS"` or `password_from_env: "DB_PASS"` — the app reads the password from the named env var.
- **User:** `user_from_env: "DB_USER"` — username from env.
- **REST / OAuth:** In the target’s `auth` block: `token_from_env: "REST_TOKEN"`, `client_secret_from_env: "CLIENT_SECRET"`.
- **Power BI / Dataverse:** At target level: `client_secret_from_env: "PBI_SECRET"`, or in `auth`: `client_secret_from_env: "PBI_SECRET"`.

When a `*_from_env` key is set, the resolved value is used for the connection; the config file can omit the literal secret. Restrict config file permissions and **do not commit** config files that contain credentials; see [SECURITY.md](../SECURITY.md) (Config file and secrets).

### Sensitivity detection: ML and DL training terms

You can set the **training words for ML and DL** in the main config (inline) or in separate YAML/JSON files. The pipeline is **hybrid**: regex → ML (TF-IDF + RandomForest) → optional DL (sentence embeddings + classifier). ML/DL terms use the same format: a list of `{ text, label }` with `label` = `sensitive` or `non_sensitive`.

- **Files:** `ml_patterns_file`, `dl_patterns_file` – paths to YAML/JSON with a list of `{ text, label }`.
- **Inline:** `sensitivity_detection.ml_terms`, `sensitivity_detection.dl_terms` – same structure; when non-empty they override the corresponding file.
- **DL backend:** Optional; install with `uv pip install -e ".[dl]"`. When installed and DL terms are provided, confidence is combined with ML for better semantic detection.
- **FN reduction (optional):** `sensitivity_detection.medium_confidence_threshold` (default 40, range 1–69) tunes how aggressively ML/DL borderline scores map to **MEDIUM**; `detection.persist_low_id_like_for_review` (default false) makes the SQL connector persist identifier-like **LOW** columns for the Excel sheet **Suggested review (LOW)**. See [SENSITIVITY_DETECTION.md](SENSITIVITY_DETECTION.md#suggested-review-low-and-medium-threshold-fn-reduction).

**Full description and examples:** [SENSITIVITY_DETECTION.md](SENSITIVITY_DETECTION.md) (English) · [SENSITIVITY_DETECTION.pt_BR.md](SENSITIVITY_DETECTION.pt_BR.md) (Português – Brasil).

#### CNPJ formats (legacy numeric and alphanumeric)

For Brazilian **CNPJ**, the detector ships with two built-in regex patterns:

- `LGPD_CNPJ` – legacy **numeric-only** format (14 digits, optional `./-/` punctuation: `XX.XXX.XXX/XXXX-XX`).
- `LGPD_CNPJ_ALNUM` – an **alphanumeric** format where the first 12 positions may contain `A–Z` or `0–9`, and the last two positions remain numeric digits; punctuation is optional in the same places.

Both patterns share the same `norm_tag` (`LGPD Art. 5`). At this stage detection is **format-based only** (no checksum); see [SENSITIVITY_DETECTION.md](SENSITIVITY_DETECTION.md#cnpj-formats-brazil-legacy-numeric-and-alphanumeric) for details.

By default only the legacy numeric pattern (`LGPD_CNPJ`) is active; to enable the alphanumeric pattern at runtime set:

```yaml
detection:
  cnpj_alphanumeric: true
```

in your config. To **enable alphanumeric CNPJ via overrides only** (for example, on older installs or for experimentation), you can copy the `LGPD_CNPJ_ALNUM` example from `config/regex_overrides.example.yaml` or from [SENSITIVITY_DETECTION.md](SENSITIVITY_DETECTION.md#yaml-example-regex-overrides) into your own `regex_overrides_file`.

### Custom regex patterns (new personal/sensitive values)

To detect **new possibly personal or sensitive values** (e.g. RG, vehicle plate, health plan ID), add custom regex patterns. In the main config set **`regex_overrides_file`** to the path of a YAML or JSON file with a list of `{ name, pattern, norm_tag }`. The detector matches each pattern against the column name and sample text; any match is reported with HIGH sensitivity. Your file adds to or overrides built-in patterns (CPF, CNPJ, email, phone, SSN, credit card, dates). **Format and examples:** [SENSITIVITY_DETECTION.md](SENSITIVITY_DETECTION.md#custom-regex-patterns-detecting-new-personalsensitive-values) (EN) · [SENSITIVITY_DETECTION.pt_BR.md](SENSITIVITY_DETECTION.pt_BR.md#padrões-regex-customizados-detectar-novos-dados-pessoaissensíveis) (pt-BR). For **multiple regulations and sample configuration** (built-in: LGPD, GDPR, CCPA, HIPAA, GLBA; extensibility for UK GDPR, PIPEDA, POPIA, APPI, PCI-DSS, or custom), and for assistance with tuning, see [COMPLIANCE_FRAMEWORKS.md](COMPLIANCE_FRAMEWORKS.md) ([pt-BR](COMPLIANCE_FRAMEWORKS.pt_BR.md)).

**Other regulations and compliance samples:** Ready-to-use sample configs for **UK GDPR**, **EU GDPR**, **Benelux**, **PIPEDA**, **POPIA**, **APPI**, **PCI-DSS**, and other regions are in [compliance-samples/](compliance-samples/). Set `regex_overrides_file` and `ml_patterns_file` to the sample file and merge its `recommendation_overrides` into `report.recommendation_overrides`. Full list, what goes where, and how to use: [COMPLIANCE_FRAMEWORKS.md – Compliance samples](COMPLIANCE_FRAMEWORKS.md#compliance-samples) ([pt-BR](COMPLIANCE_FRAMEWORKS.pt_BR.md#amostras-de-conformidade)).

**Checklist when using a compliance sample file:**

1. **Merge** the sample’s `recommendation_overrides` into `report.recommendation_overrides` in your main config — otherwise the **Recommendations** sheet falls back to built-in generic text only.
1. **Review** optional `regex` entries; regional digit patterns can be noisy on unconstrained text (see [SENSITIVITY_DETECTION.md](SENSITIVITY_DETECTION.md#generic-digit-patterns-and-false-positive-scope)).
1. **Order** `recommendation_overrides` so **more specific** `norm_tag_pattern` strings appear **before** broader substrings (e.g. **UK GDPR** before **GDPR**). The matcher uses **first match** (substring semantics).

### Rate limiting and safe concurrency

To avoid accidental DoS or overload when the tool is misused (for example, many scans in a row or too many workers), you can configure a dedicated `rate_limit` block:

```yaml
rate_limit:
  enabled: true               # default true when block is present
  max_concurrent_scans: 1     # maximum running scans at the same time (API)
  min_interval_seconds: 0     # minimum seconds between scan starts
  grace_for_running_status: 0 # optional extra grace when status still reports running
```

- When `rate_limit.enabled` is true, the API endpoints that start scans (`POST /scan`, `POST /start`, `POST /scan_database`) may return **HTTP 429** with a JSON body like:

  ```json
  {
    "detail": {
      "error": "rate_limited",
      "reason": "too_many_running_scans",
      "running_scans": 2,
      "max_concurrent_scans": 1,
      "source": "scan"
    }
  }
  ```

- The CLI uses the same logic only to print **warnings** (it never exits with 429). This lets you keep existing scripts working while seeing when your policies would reject extra scans if called via API or dashboard.
- Settings can also be overridden with environment variables: `RATE_LIMIT_ENABLED`, `RATE_LIMIT_MAX_CONCURRENT_SCANS`, `RATE_LIMIT_MIN_INTERVAL_SECONDS`, `RATE_LIMIT_GRACE_FOR_RUNNING_STATUS`.
- **Production:** Rate limiting is the first line of defense against scan abuse and overload. Disabling or relaxing rate limits (e.g. high `max_concurrent_scans` or zero `min_interval_seconds`) increases the risk of abuse and resource exhaustion; keep limits enabled with conservative values in production.

### Timeouts for data source connections

You can configure connection and read timeouts (in seconds) used when opening and reading from databases, APIs, or other targets. Global defaults apply to all targets; individual targets can override them.

```yaml
timeouts:
  connect_seconds: 25   # default: 25 — max time to establish a connection
  read_seconds: 90      # default: 90 — max time to wait for read/response
```

- **Per-target overrides:** On any target you can set `connect_timeout`, `read_timeout`, or a single `timeout` (used for both connect and read when the other is not set). Target values override the global timeouts when present. Values are in seconds and are clamped to at least 1.

Example (global defaults plus one slower target):

```yaml
timeouts:
  connect_seconds: 25
  read_seconds: 90

targets:

- name: fast-db

    type: database
    # uses 25 / 90
- name: slow-api

    type: api
    connect_timeout: 60
    read_timeout: 120

- name: legacy

    type: database
    timeout: 45   # 45 for both connect and read
```

Connectors use the merged values (global or per-target) when opening connections and performing I/O; see the config schema and connector documentation for details.

### Timeouts and load

Recommendations so scans stay robust without overloading targets or waiting forever:

1. **Don’t wait forever:** Set connect and read timeouts so one stuck target does not block the whole scan. Use report failure hints to spot timeout failures and which target failed.
1. **Don’t be too aggressive:** Too-low timeouts cause false timeouts on busy or slow networks (e.g. during backup). If you see many timeouts, **increase** `connect_seconds` and `read_seconds` (or per-target `connect_timeout` / `read_timeout`) and consider re-running during off-peak.
1. **Avoid DoS and "too much, too fast":** Use **rate_limit** (e.g. `max_concurrent_scans: 1`, `min_interval_seconds: 5`) and **scan.max_workers: 1** (or 2) so the scanner does not open many connections at once. This reduces load on targets and avoids amplifying slowness or causing DoS.
1. **Backup or maintenance windows:** If scans run during backup or maintenance, increase timeouts and keep parallelism low; or schedule scans outside those windows.
1. **Per-target overrides:** For one slow database or API, set `connect_timeout` / `read_timeout` (or `timeout`) on that target instead of raising global defaults for everyone.

### API and security (CSP, headers)

The web API and dashboard send **security headers** on every response (see [SECURITY.md](../SECURITY.md)): X-Content-Type-Options, X-Frame-Options, **Content-Security-Policy (CSP)**, Referrer-Policy, Permissions-Policy, and HSTS when the request is considered HTTPS.

- **CSP defaults:** Scripts and styles are allowed from the app origin (`'self'`). The dashboard loads Chart.js from the **jsDelivr CDN** (`<https://cdn.jsdelivr.ne>t`), which is allowed by default so the "Progress over time" chart works without extra config. A minimal amount of inline script is used for data passed to the chart; the rest of the dashboard logic lives in `/static/dashboard.js`.
- **Stricter CSP:** To remove `'unsafe-inline'` (e.g. for a high-security profile), you can set a stricter CSP at the **reverse proxy** (override the app's header) or use an env/config toggle if the application adds one in a future version. With a stricter CSP, all script and style must be from allowed origins (e.g. `'self'` and the CDN); any remaining inline script in templates would need to be refactored into external files. See [SECURITY.md](../SECURITY.md) and [docs/deploy/DEPLOY.md](deploy/DEPLOY.md) ([pt-BR](deploy/DEPLOY.pt_BR.md)) (Security and hardening) for deployment hardening (Docker, Kubernetes, reverse proxy).

### Targets: databases

Each target is an object in `targets` with at least `name` and `type`. For SQL databases use `type: database` and the appropriate `driver`. **Scan payload:** There is no hard limit on the number of targets per scan; very large lists (e.g. hundreds of databases or APIs) may increase scan duration and memory use. Consider a reasonable scope per scan for your environment to avoid resource exhaustion.

```yaml
targets:

- name: "Produção_Postgres"

    type: database
    driver: postgresql+psycopg2
    host: 10.0.0.50
    port: 5432
    user: audit_user
    pass: secure_password
    database: customers_db
```

Credentials: `user`, `pass` (or `password`). Optional: `url` to pass a full SQLAlchemy URL instead of host/port/user/database.

## Snowflake (optional, .[bigdata])

```yaml
targets:

- name: "Warehouse_LGPD"

    type: database
    driver: snowflake
    account: "xy12345.us-east-1"
    user: "AUDIT_USER"
    pass: "secret"
    database: "COMPLIANCE_DB"
    schema: "PUBLIC"
    warehouse: "AUDIT_WH"
    role: "ANALYST"   # optional
```

Install the optional dependency with:

```bash
uv pip install -e ".[bigdata]"
```

The Snowflake connector uses the same pattern as other SQL engines: discover tables/columns, sample rows (no raw storage), run sensitivity detection, and save findings as database metadata (schema, table, column, data type, sensitivity, pattern, norm tag, confidence).

### Targets: filesystem

```yaml

- name: "Documentos_LGPD"

    type: filesystem
    path: /home/user/Documents/LGPD
    recursive: true
```

No credentials. Uses `file_scan` settings (extensions, recursive, scan_sqlite_as_db, `sample_limit`, `file_sample_max_chars`) from config.

### Targets: APIs (REST) – Basic, Bearer, OAuth2, custom

Use `type: api` or `type: rest`. Required: `name`, `base_url` (or `url`). Optional: `paths` or `endpoints`, `discover_url`, `timeout`, `headers`, and an `auth` block.

**SSRF guard:** `base_url`, `discover_url`, and `auth.token_url` pointing at link-local (cloud metadata `169.254.0.0/16`), loopback, or private (RFC1918/ULA) hosts are rejected by default. To scan internal infrastructure, add `allow_private_networks: true` to the target. The same guard applies to SharePoint (`site_url`), WebDAV (`base_url`), and Power BI (`auth.token_url`) targets.

```yaml

- name: "Internal API"

    type: api
    base_url: "http://10.0.0.5:8080"
    paths: ["/users"]
    allow_private_networks: true  # explicit opt-in for private/loopback hosts
```

## Basic auth

```yaml

- name: "Legacy API"

    type: api
    base_url: "https://api.example.com"
    paths: ["/users", "/contacts"]
    auth:
      type: basic
      username: "audit_user"
      password: "your_password"
```

## Bearer token (static or from environment)

```yaml

- name: "API with bearer"

    type: api
    base_url: "https://api.example.com"
    paths: ["/data"]
    auth:
      type: bearer
      token: "eyJhbGc..."   # or use token_from_env: "API_TOKEN" to read from env
```

## OAuth2 client credentials (machine-to-machine)

```yaml

- name: "Internal Users API"

    type: api
    base_url: "https://api.example.com"
    paths: ["/users", "/profiles"]
    auth:
      type: oauth2_client
      token_url: "https://auth.example.com/oauth/token"
      client_id: "audit-client"
      client_secret: "${API_OAUTH_SECRET}"   # or literal secret
      scope: "read:users"
```

Set the env var (e.g. `API_OAUTH_SECRET`) in the environment where the app runs.

## Custom headers (e.g. API key or Negotiate)

```yaml

- name: "API with custom header"

    type: api
    base_url: "https://api.example.com"
    paths: ["/export"]
    auth:
      type: custom
      headers:
        Authorization: "Bearer ..."
        X-API-Key: "your-api-key"
```

If you omit `auth` but set `user`/`username` and `pass`/`password` on the target, **basic** auth is applied.

### Targets: Power BI and Power Apps (Dataverse)

**Power BI** and **Dataverse (Power Apps)** use Azure AD OAuth2 client credentials. No extra package is required (httpx is already a dependency).

## Power BI (`type: powerbi`)

- Required: `name`, `tenant_id`, `client_id`, `client_secret` (or under `auth:`).
- Optional: `workspace_ids` or `group_ids` (list of workspace GUIDs) to limit scan; omit to use “My workspace” and all workspaces.
- Azure AD app must have Power BI permission `Dataset.Read.All` or `Dataset.ReadWrite.All`. If using a service principal, enable “Allow service principals to use Power BI APIs” in the Power BI admin portal.

```yaml

- name: "Power BI Compliance"

    type: powerbi
    tenant_id: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    client_id: "yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy"
    client_secret: "${POWERBI_CLIENT_SECRET}"
    # workspace_ids: ["group-guid-1"]
```

## Dataverse / Power Apps (`type: dataverse` or `type: powerapps`)

- Required: `name`, `org_url` (or `environment_url`, e.g. `<https://myorg.crm.dynamics.co>m`), `tenant_id`, `client_id`, `client_secret` (or under `auth:`).
- Azure AD app needs application permission to Dataverse (admin consent). Scope is derived from `org_url`.

```yaml

- name: "Dataverse HR"

    type: dataverse
    org_url: "https://myorg.crm.dynamics.com"
    tenant_id: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    client_id: "yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy"
    client_secret: "${DATAVERSE_CLIENT_SECRET}"
```

Findings from Power BI and Dataverse appear in the **Database findings** sheet. Sampling uses `file_scan.sample_limit` (default 5). Inventory metadata for these connectors (API version hints and transport) appears in the **Data source inventory** sheet.

### Targets: shared content (SMB, WebDAV, SharePoint, NFS)

Install optional deps: `uv pip install -e ".[shares]"`.

## SMB/CIFS

```yaml

- name: "FileServer HR"

    type: smb
    host: "fileserver.company.local"
    share: "HR"
    path: "Documents"
    user: "audit_user"
    pass: "***"
    domain: "COMPANY"   # optional
    port: 445
    recursive: true
```

## WebDAV

```yaml

- name: "WebDAV Storage"

    type: webdav
    base_url: "https://webdav.company.com/dav"
    user: "audit"
    pass: "***"
    path: "archive"
    recursive: true
    verify_ssl: true
```

## SharePoint

```yaml

- name: "SharePoint HR"

    type: sharepoint
    site_url: "https://sharepoint.company.com/sites/hr"
    path: "Shared Documents"
    user: "audit@company.com"
    pass: "***"
```

## NFS (path = local mount point; mount NFS before scanning)

```yaml

- name: "NFS Export"

    type: nfs
    host: "nfs.company.local"
    export_path: "/export/data"
    path: "/mnt/nfs_data"   # local mount point
```

All share types use the same `file_scan` settings (extensions, recursive, scan_sqlite_as_db, `sample_limit`, `file_sample_max_chars`, file_passwords). Findings appear in the **Filesystem findings** sheet.

### Global options (excerpt)

```yaml
file_scan:
  extensions: [.txt, .csv, .pdf, .docx, .xlsx]
  recursive: true
  scan_sqlite_as_db: true
  sample_limit: 5   # row-style caps (e.g. SQLite-as-DB per column, Power BI / Dataverse TOPN)
  file_sample_max_chars: 12000   # UTF-8 chars read per plain-text file (.txt, .md, …) on FS/shares
  # Optional: scan inside compressed files (off by default)
  # When true, candidate archives (zip, tar, gz, bz2, xz, 7z, etc.) are opened and inner members
  # with supported extensions are scanned as if they were regular files. Inner paths appear in
  # findings as e.g. "backup.zip|inner/path/file.csv". This may significantly increase run time,
  # disk I/O and temporary space usage; enable only when needed.
  scan_compressed: false
  # Optional: max uncompressed size per archive member (bytes). Valid range 1 MB–500 MB; default 10 MB if omitted.
  # Members larger than this are skipped to reduce memory and I/O. Alias: scan_compressed_max_inner_size.
  # max_inner_size: 50_000_000   # e.g. 50 MB
  # Aggregate budgets (#1233): stop opening further members when exceeded (fail-closed → scan_failures
  # reason archive_budget_exceeded). Checked from declared sizes before materializing member bytes.
  # max_members: 1000                  # default 1000; clamped 1–100000
  # max_total_uncompressed: 1000000000 # default 1 GiB; sum of declared member sizes
  # max_expansion_ratio: 200           # default 200; total_uncompressed / archive file size
  # Optional: restrict which archive types to open; if omitted, a sensible default list is used.
  # compressed_extensions: [".zip", ".tar", ".gz", ".tgz", ".bz2", ".xz", ".7z"]
  # For .7z support install the optional extra: pip install -e ".[compressed]" (or uv sync --extra compressed).
  # Optional: passwords for password-protected files (PDF, ZIP-based e.g. .docx/.pptx)
  # Keys: extension with leading dot (e.g. ".pdf", ".pptx") or "default"; values: password string.
  # Without a matching password, encrypted files are skipped (no content extracted).
  # file_passwords:
  #   ".pdf": "my-pdf-secret"
  #   ".pptx": "presentation-pass"
  #   default: "fallback-for-any-encrypted"

```

**Relational database sampling (SQLAlchemy SQL targets + Snowflake connector):** Per-column reads apply `WHERE <column> IS NOT NULL` before the row cap so sparse columns still yield non-empty samples for the detector when non-null values exist. Optional process environment variable **`DATA_BOAR_SQL_SAMPLE_LIMIT`** (integer, clamped to **1** through **10000**) **replaces** `file_scan.sample_limit` for those connectors when set—useful for production break-glass without editing YAML. Optional YAML **`sql_sampling.overrides`** tightens or loosens the default **per target name** (must match `targets[].name`), **per table** under that target (`schema.table` or bare `table`), then **per table name pattern** (`fnmatch`, e.g. `*_audit`) before falling back to `file_scan.sample_limit`. You may split overrides into a separate file (same schema as the `sql_sampling` block or bare `overrides:`) and reference it with root keys **`sql_sampling_file`** (single path) and/or **`sql_sampling_files`** (list, merged in order; later files override earlier ones). Inline `sql_sampling` in the main config **wins** over fragments when the same key is set. Paths are relative to the main config file’s directory; relative paths must not escape that directory (`..` is rejected). **`load_config`** and **`normalize_config(..., config_path=...)`** expand fragments; calling **`normalize_config(dict)`** without `config_path` does **not** read external files. Implementation: `core/sampling.py` / `core/sampling_policy.py` + `connectors/sql_sampling.py` — `SamplingManager` picks a **strategy label** per dialect (and optional table metadata); `SQLConnector` / Snowflake / embedded SQLite-as-DB log that label **once per table** at INFO for a short audit trail. Legacy entry point: `SqlColumnSampleQueryBuilder.build` → same SQL.

**SRE sampling knobs (database targets):** Generated sampling statements start with the line comment **`-- Data Boar Compliance Scan`** so operators can attribute activity in engine views. On each **database** target you may set **`sample_statement_timeout_ms`** or **`sample_statement_timeout_seconds`** (use **`0`** to disable); when unset the connector defaults to **5000 ms** for short reads. That budget drives a MySQL **`/*+ MAX_EXECUTION_TIME(N) */`** optimizer hint and a per-sample PostgreSQL **`SET LOCAL statement_timeout`** (wrapped in a short transaction). **SQL Server has no equivalent query-level time hint** (T-SQL does *not* accept `OPTION (MAX_EXECUTION_TIME = …)`), so the budget is recorded in the audit log only; tighten MSSQL reads via the connection-level **`connect_timeout`** and DBA-side resource governor. **`DATA_BOAR_SAMPLE_STATEMENT_TIMEOUT_MS`** overrides the budget from the process environment. Optional **`inter_query_delay_ms`** adds a sleep between column samples to reduce burst load. Approximate table sizes for “large table” sampling strategies come from **catalog statistics** (`connectors/sql_table_row_estimate.py`), never **`COUNT(*)`** on the heap.

```yaml
# Optional: convention-over-config row caps for SQL + Snowflake (still clamped by DATA_BOAR_SQL_SAMPLE_LIMIT when set).
# sql_sampling_file: configs/sampling_overrides.yaml   # optional fragment (YAML) merged before inline block below
# sql_sampling_files: [configs/team_a.yaml, configs/team_b.yaml]
sql_sampling:
  overrides:
    targets:
      legacy_oracle_db:
        sample_limit: 5
        tables:
          "HR.PAYROLL": 2
    patterns:
      "*_audit": 100
      "*_logs": 50
```

**Scan inside compressed files (`scan_compressed`, `max_inner_size`, aggregate budgets):** Enabling **`scan_compressed: true`** may **significantly increase run time, disk I/O and temporary space**. Use it only when you need to inspect contents of archives; when first enabling it, consider a smaller target scope (e.g. one directory or a limited set of paths). The **`max_inner_size`** value is validated and clamped to 1 MB–500 MB; if invalid or omitted, a safe default (10 MB) is used so that very large inner members are skipped. **Aggregate budgets** (anti zip-bomb / DoS) always apply when scanning archives: **`max_members`** (default **1000**), **`max_total_uncompressed`** (default **1 GiB** of declared sizes), and **`max_expansion_ratio`** (default **200** = declared uncompressed total ÷ archive file size). Exceeding any limit records **`scan_failures`** with reason **`archive_budget_exceeded`** and stops further members in that archive (fail-closed; no silent skip). Nested archives remain one level only for v1.

**Password-protected files (`file_passwords`):** Some PDFs and ZIP-based documents (e.g. `.docx`, `.pptx`) can be encrypted with a password. If you need to scan such files, set **`file_scan.file_passwords`** to a dict mapping extension keys (e.g. `".pdf"`, `".pptx"`) or `"default"` to the password string. Keys are normalized to lowercase with a leading dot. Without a matching password, encrypted files are skipped (no content is extracted). **Limitations:** Workbook-level encrypted Excel (`.xlsx`/`.xlsm`) is not supported; the standard library `zipfile` only supports ZipCrypto for ZIP-based formats (AES-encrypted ZIP may require additional support). Use environment variables or a secrets manager for production so passwords are not stored in the config file.

**Extension `.doc` (optional `legacy-doc` extra):** Body sampling uses **`mammoth`** when you install **`pip install -e ".[legacy-doc]"`** (or `uv sync --extra legacy-doc`). Mammoth targets **ZIP-based OOXML** (same family as `.docx`); classic **Word 97-2003 binary** `.doc` often still yields an **empty** content sample — only path/filename analysis applies. See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) (*Legacy `.doc` files*).

**Jurisdiction hints (`report.jurisdiction_hints`, `--jurisdiction-hint`):** Optional **DPO / counsel**-oriented notes on the **Report info** sheet when **finding metadata** (column/table/file/path names, norm tags — not raw cell dumps) suggests possible relevance to **US-CA (CCPA/CPRA)**, **Colorado**-style privacy expectations, or **Japan (APPI)**. This is **heuristic only** (high false-positive/negative rate) and **not** a legal conclusion; prefer **counsel review** before relying on scope. Enable with **`report.jurisdiction_hints.enabled: true`**, CLI **`--jurisdiction-hint`**, dashboard checkbox, or **`POST /scan`** with **`"jurisdiction_hint": true`**. Sub-keys: **`us_ca`**, **`us_co`**, **`jp`** (booleans), and optional **`min_score_us_ca`**, **`min_score_us_co`**, **`min_score_jp`** (integers, defaults in code). Does **not** change sensitivity levels or findings.

```yaml
report:
  output_dir: .    # directory for Excel and heatmap PNG
  # Optional: custom recommendation text per norm/framework (UK GDPR, PIPEDA, or sensitive categories)
  recommendation_overrides:

    - norm_tag_pattern: "UK GDPR"

      base_legal: "UK GDPR Art. 4(1)"
      risk: "Identification of data subject."
      recommendation: "Apply UK GDPR safeguards and DPA registration if required."
      priority: "ALTA"
      relevant_for: "DPO, UK Representative"

    - norm_tag_pattern: "PIPEDA"

      base_legal: "PIPEDA s. 2 (personal information)"
      risk: "Personal information as defined under Canadian law."
      recommendation: "Review PIPEDA consent and limitation purposes."
      priority: "MÉDIA"
      relevant_for: "DPO, Privacy Officer"
    # Sensitive categories (LGPD Art. 5 II, 11; GDPR Art. 9) – see SENSITIVITY_DETECTION.md
    - norm_tag_pattern: "health"

      base_legal: "LGPD Art. 5 II, 11 – dado de saúde; GDPR Art. 9"
      risk: "Health or medical condition data; special treatment and legal basis required."
      recommendation: "Ensure legal basis and consent; restrict access; consider anonymisation."
      priority: "CRÍTICA"
      relevant_for: "DPO, Compliance, Health area"

    - norm_tag_pattern: "religious"

      base_legal: "LGPD Art. 5 II, 11 – convicção religiosa; GDPR Art. 9"
      risk: "Sensitive data; discrimination and differential treatment."
      recommendation: "Minimisation; explicit legal basis and consent; restricted access."
      priority: "CRÍTICA"
      relevant_for: "DPO, Compliance, HR"

    - norm_tag_pattern: "political"

      base_legal: "LGPD Art. 5 II, 11 – filiação política; GDPR Art. 9"
      risk: "Political affiliation or opinion; sensitive under both regimes."
      recommendation: "Minimise; explicit consent and purpose limitation; restrict access."
      priority: "CRÍTICA"
      relevant_for: "DPO, Compliance, Legal"

    - norm_tag_pattern: "PEP"

      base_legal: "LGPD Art. 5 II; GDPR Art. 9 – PEP lists and enhanced due diligence"
      risk: "Politically exposed person data; enhanced scrutiny and retention limits."
      recommendation: "Apply PEP policies; limit retention; document legal basis."
      priority: "ALTA"
      relevant_for: "DPO, Compliance, AML/KYC"

    - norm_tag_pattern: "race"

      base_legal: "LGPD Art. 5 II, 11 – raça/origem; GDPR Art. 9"
      risk: "Race, skin color or ethnic origin; discrimination risk."
      recommendation: "Minimise; explicit consent; restrict access and purpose."
      priority: "CRÍTICA"
      relevant_for: "DPO, Compliance, HR"

    - norm_tag_pattern: "union"

      base_legal: "LGPD Art. 5 II, 11 – filiação sindical; GDPR Art. 9"
      risk: "Trade union membership; sensitive in both regimes."
      recommendation: "Minimise; legal basis and consent; restricted access."
      priority: "ALTA"
      relevant_for: "DPO, Compliance, HR"

    - norm_tag_pattern: "genetic"

      base_legal: "LGPD Art. 5 II, 11 – dados genéticos; GDPR Art. 9"
      risk: "Genetic data; special category; high re-identification risk."
      recommendation: "Strict minimisation; explicit consent; consider separate storage and access controls."
      priority: "CRÍTICA"
      relevant_for: "DPO, Compliance, Health area"

    - norm_tag_pattern: "biometric"

      base_legal: "LGPD Art. 5 II, 11 – biometria; GDPR Art. 9"
      risk: "Biometric data for identification; irreversible if compromised."
      recommendation: "Purpose limitation; secure storage; legal basis and consent."
      priority: "CRÍTICA"
      relevant_for: "DPO, Compliance, Security"

    - norm_tag_pattern: "sex life"

      base_legal: "LGPD Art. 5 II, 11 – vida sexual; GDPR Art. 9"
      risk: "Sex life or sexual orientation; highly sensitive."
      recommendation: "Strict minimisation; explicit consent; highest access restrictions."
      priority: "CRÍTICA"
      relevant_for: "DPO, Compliance, Legal"

api:
  port: 8088
  workers: 1       # uvicorn workers; 1 = minimal, 2+ for concurrent API traffic
  # Optional: require API key for all endpoints except GET /health (X-API-Key or Authorization: Bearer)
  # require_api_key: true
  # api_key: "your-secret-key"              # or use api_key_from_env to read from environment
  # api_key_from_env: "AUDIT_API_KEY"
  # Optional POC: dashboard GET /{locale}/assessment (see Web dashboard table). Default off.
  # maturity_self_assessment_poc_enabled: true
  # maturity_assessment_pack_path: /path/to/maturity_pack.yaml
  # Optional: HMAC per stored answer (set env before process start). Not encryption; deters casual DB edits.
  # maturity_integrity_secret_from_env: "DATA_BOAR_MATURITY_INTEGRITY_SECRET"
  # (or rely on default env name DATA_BOAR_MATURITY_INTEGRITY_SECRET without this key)

# Optional: simulate commercial tier in lab (community | pro | enterprise). Omits OPEN dev behaviour for feature gates.
# licensing:
#   effective_tier: pro

# Optional: possible minor data detection (LGPD Art. 14, GDPR Art. 8). See MINOR_DETECTION.md.
# detection:
#   minor_age_threshold: 18        # age below this flags DOB/age columns as possible minor (default 18)
#   minor_full_scan: false         # when true (databases only), re-sample columns that look like DOB/age for minors using minor_full_scan_limit
#   minor_full_scan_limit: 100     # max rows for the full-scan pass (databases only; ignored when minor_full_scan is false)
#   minor_cross_reference: true    # when true, report cross-references DOB_POSSIBLE_MINOR with identifier/health in same table/path and adds "Minor confidence"

sqlite_path: audit_results.db
scan:
  max_workers: 1   # 1 = sequential; >1 = parallel targets (I/O-bound)
```

---

## 5. Downloading reports (summary)

### Downloading reports (web) {#downloading-reports-web}

For **DPO, legal, and other non-technical readers** (see [AUDIENCE_GUIDE.md](AUDIENCE_GUIDE.md)), use the browser — screenshots show the path before any `curl` commands.

1. Open **Reports** from the top menu (`/en/reports` or `/pt-br/reports`).
2. Click **Download** on the session row you need.

![Reports page — click Download on a session row](img/dashboard/en/reports-download.png)

The Excel workbook is saved to your browser downloads folder; the heatmap PNG is generated alongside the workbook when the report is built.

### For automation / scripting

| Goal                                   | How                                                                                                                                                    |
| ---                                    | ---                                                                                                                                                    |
| **Last generated report**              | `GET /report` → save response as `.xlsx`.                                                                                                              |
| **Report for a specific past session** | `GET /list` to get `session_id`s, then `GET /reports/<session_id>` → save as `.xlsx`.                                                                  |
| **One-shot run (CLI)**                 | After `python main.py --config config.yaml`, the report path is printed; file is under `report.output_dir` as `Relatorio_Auditoria_<session_id>.xlsx`. |
| **Executive Markdown + manifest**      | Written next to the Excel when the workbook is generated: `POC_SUMMARY_<session_prefix>.md` and `scan_manifest_<session_prefix>.yaml` (same directory). If this step fails, the Excel path is still returned — see subsection below. |
| **Executive Markdown only (CLI)**    | `data-boar-report` — reads **local SQLite** from `sqlite_path` in config; no live database connector required. See subsection below.                    |

- Reports are generated on demand for a given session (from SQLite findings). The heatmap PNG is written next to the Excel file when the report is generated.
- No built-in retention policy; reports are files on disk. Clean up or archive them as needed.

### Executive evidence, APG priorities, and `data-boar-report`

When **`generate_report`** runs (CLI one-shot, **`GET /reports/{session_id}`**, **`GET /report`**, or dashboard **Download**), the product can emit:

- **`POC_SUMMARY_<first_16_chars_of_session_id>.md`** — stakeholder-oriented Markdown: status, findings **aggregated by sensitivity** (pattern names and counts only), top **three** APG Phase A mitigation priorities, and a short DBA/SRE posture summary. It does **not** list column names, table names, file paths, or sampled cell content — share safely with audiences that should not see operational detail.
- **`scan_manifest_<prefix>.yaml`** — evidence manifest (sampling caps, timeouts, audit trail bullets, scope snapshot, optional `apg_phase_a` block).

Failing to write these files is **non-fatal**: Excel and heatmap generation still succeed; check logs if the Markdown or YAML is missing.

**Console entry point** (installed with the `data-boar` package from `[project.scripts]`):

```bash
uv run data-boar-report --config config.yaml --session-id <session_id>
```

When **`-o` / `--output` is omitted**, the CLI writes **`executive_report_<safe_prefix>.md`** next to the config file (avoids streaming the full report to stdout in CI logs). Use **`-o`** for an explicit path:

```bash
uv run data-boar-report --config config.yaml --session-id <session_id> -o Executive_summary.md
```

**Useful flags:**

| Flag | Meaning |
| --- | --- |
| `--sqlite <path>` | Override `sqlite_path` from the config (e.g. homelab copy of the audit DB). |
| `--trial-rows-capped` | Adds the same “trial license may cap Excel rows” note as the bundled `POC_SUMMARY` when you regenerate from SQLite. |

**Requirements:** Same **`config.yaml`** you use for scans (so sampling/timeout metadata in the manifest matches policy). **`session_id`** must exist in `scan_sessions` / findings tables.

#### Local processing and privacy (`data-boar-report`)

`data-boar-report` reads **only** the **local SQLite** artefact from your scan (`sqlite_path`, overridable with **`--sqlite`**). It **re-aggregates** session metadata into Markdown/YAML **without opening live connectors**. By design, the default executive Markdown (**`POC_SUMMARY_*.md`**) carries **pattern names, counts, APG Phase A priorities**, and posture narrative — **not** raw sampled values or free-text PII excerpts. Sensitive literals stay in the secured database tier (or in **redacted** exports **you** control).

**Structure (PoC “desk” contract):** the Markdown uses a clear heading ladder (**H1–H4**): session status, sensitivity roll-up, **`## 3. Metodologia e segurança`** (sampling caps, statement timeouts, traceability comment, **SQL Server `WITH (NOLOCK)`** when that engine appears in the session, plus manifest **SRE/DBA** bullets), then **`## 4. Plano de ação (APG)`** with **Top 3** priorities and a **full per-pattern inventory** (finding → risk → technical recommendation).

**Related:** [REPORTS_AND_COMPLIANCE_OUTPUTS.md](REPORTS_AND_COMPLIANCE_OUTPUTS.md) (output map).

### 5.1 Operator notifications (optional)

After a scan finishes (CLI one-shot or `POST /scan` / `POST /start` background run), the app can **POST a short pt-BR brief** to **Slack**, **Microsoft Teams**, a **generic JSON webhook** (e.g. automation tools or a **Signal** REST bridge), or **Telegram** (optional fields for legacy/third-party installs only). Default is **off** (`notifications.enabled: false`).

- **Maintainer policy (canonical repo):** The maintainer does **not** use **Telegram** for Data Boar operator notifications; prefer **Slack**, **Teams**, or **generic webhook** for **Signal**. See [OPERATOR_NOTIFICATION_CHANNELS.md](ops/OPERATOR_NOTIFICATION_CHANNELS.md).
- **Config (legacy single path):** `notifications.operator` with `slack_webhook_url`, `teams_webhook_url`, `telegram_bot_token` + `telegram_chat_id`, or `generic_webhook_url` — first configured type wins (Slack → Teams → Telegram → generic).
- **Config (multiple operator channels):** `notifications.operator.channels` as a **list** of objects; each object is **one** channel (e.g. one Slack webhook and one generic webhook). All configured channels receive the same message (scan-complete or manual script).
- **Tenant copy (optional):** `notifications.tenant.by_tenant` maps a **lowercased** tenant name to a webhook block (or string URL for generic POST). `default_slack_webhook_url` / `default_generic_webhook_url` apply when `tenant_name` is set but there is no per-tenant entry. Requires a non-empty `tenant_name` on the session.
- **Dedupe:** `notifications.dedupe_scan_complete_per_session` (default `true`) avoids a second POST for the same `session_id` after **at least one** outbound send succeeded (process-local; use `false` only if you need retries on every completion hook).
- **Audit log (optional):** `notifications.notify_audit_log` (default `true`) appends one row per channel attempt to SQLite table **`notification_send_log`** (session id, trigger, recipient `operator`/`tenant`, channel, success, redacted error text, timestamp). No message body stored. Set to `false` to disable writes.
- **Secrets:** URLs may use `${ENV_VAR}`. Outbound webhook POSTs retry a few times on HTTP 5xx or transient network errors.
- **Manual / CI:** `python scripts/notify_webhook.py "message"` (same config file; requires `notifications.enabled: true` and a channel URL). By default the script opens ``sqlite_path`` and appends audit rows for each channel (same as scan-complete); use ``--no-audit`` when no local DB exists (e.g. some CI jobs).
- **Details:** [TECH_GUIDE.md](TECH_GUIDE.md) (notifications and webhooks) and [ops/OPERATOR_NOTIFICATION_CHANNELS.md](ops/OPERATOR_NOTIFICATION_CHANNELS.md).

---

## 6. Infrastructure as Code — OpenTofu / Terraform

For corporate and enterprise environments that manage infrastructure via OpenTofu or Terraform,
Data Boar ships a minimal HCL module under `deploy/opentofu/`.

**The recommended workflow for IaC-first teams:**

```bash
# Step 1 — Provision infrastructure (Docker container, ports, volumes)
cd deploy/opentofu
tofu init
tofu apply                       # or: terraform apply

# Step 2 — Configure and deploy the application
cd ../..
ansible-playbook -i deploy/opentofu/generated_inventory.ini deploy/ansible/site.yml
```

**With a POC database (PostgreSQL) for testing:**

```bash
tofu apply -var="db_enabled=true" -var="db_password=poc-test-123"
uv run python scripts/populate_poc_database.py --db-type postgres --host localhost --write-config
```

Key variables: `data_boar_image`, `data_boar_port` (default `8088`), `data_boar_config_path`,
`data_boar_output_dir`, `db_enabled`, `db_password`.

Full module docs: `deploy/opentofu/README.md` — design rationale: `docs/adr/ADR-0016-opentofu-corporate-iac-path-alongside-ansible.md`.

> OpenTofu >= 1.6 and Terraform >= 1.5 are both compatible with this module (HCL-identical).
> For remote Docker hosts, set `DOCKER_HOST` or configure an SSH tunnel before `tofu apply`.

---

## 7. Quick reference

- **CLI one-shot:** `python main.py --config config.yaml`
- **CLI start API:** `python main.py --config config.yaml --web --port 8088`
- **Config for API:** Set `CONFIG_PATH` or place `config.yaml` in working directory.
- **Start scan:** `POST /scan` or `POST /start`
- **Status:** `GET /status`
- **List sessions:** `GET /list` (JSON). For the HTML session list, open `/{locale}/reports` (e.g. `/en/reports`); bare `/reports` redirects there (no JSON list at `GET /reports`).
- **Download last report:** `GET /report`
- **Download report by session:** `GET /reports/{session_id}`
- **Executive Markdown (local SQLite):** `uv run data-boar-report --config config.yaml --session-id <session_id>` (see section 5)
- **Interactive API docs:** `http://<host>:<port>/docs`

**Related documentation:** Full documentation index (all topics, both languages): [README](README.md) · [README.pt_BR.md](README.pt_BR.md). Technical guide: [TECH_GUIDE.md](TECH_GUIDE.md) · [TECH_GUIDE.pt_BR.md](TECH_GUIDE.pt_BR.md). [SENSITIVITY_DETECTION.md](SENSITIVITY_DETECTION.md) (ML/DL training terms; [pt-BR](SENSITIVITY_DETECTION.pt_BR.md)). For `recommendation_overrides` covering sensitive categories (health, religion, political, PEP, race, union, genetic, biometric, sex life), see the example above (Global options) and [SENSITIVITY_DETECTION.md](SENSITIVITY_DETECTION.md). To add a new data-source connector (database, API, share), see [ADDING_CONNECTORS.md](ADDING_CONNECTORS.md) ([pt-BR](ADDING_CONNECTORS.pt_BR.md)). Deploy: [deploy/DEPLOY.md](deploy/DEPLOY.md) · [deploy/DEPLOY.pt_BR.md](deploy/DEPLOY.pt_BR.md). Further: [TESTING](TESTING.md) ([pt-BR](TESTING.pt_BR.md)), [TOPOLOGY](TOPOLOGY.md) ([pt-BR](TOPOLOGY.pt_BR.md)), [COMMIT_AND_PR](ops/COMMIT_AND_PR.md) ([pt-BR](ops/COMMIT_AND_PR.pt_BR.md)), [compliance-frameworks](COMPLIANCE_FRAMEWORKS.md) ([pt-BR](COMPLIANCE_FRAMEWORKS.pt_BR.md)).
