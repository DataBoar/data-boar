# Technical guide (Data Boar)

**Português (Brasil):** [TECH_GUIDE.pt_BR.md](TECH_GUIDE.pt_BR.md)

This guide covers installation, configuration, CLI and API reference, supported connectors, and deployment. For a high-level introduction and why Data Boar exists, see the [root README](../README.md).

## Starter configuration files (copy-paste)

Do **not** start from scattered snippets: use one tracked sample and edit paths/secrets locally.

| File | Role |
| ---- | ---- |
| **[`deploy/samples/config.starter-lgpd-eval.yaml`](../deploy/samples/config.starter-lgpd-eval.yaml)** | Full **LGPD-style evaluation** starter (two FS targets + one DB, rate limit, ML/DL terms, commented optionals). |
| **[`deploy/config.example.yaml`](../deploy/config.example.yaml)** | Minimal Docker template (`targets: []`). |
| **[`docs/samples/README.md`](samples/README.md)** ([pt-BR](samples/README.pt_BR.md)) | Short index from **`docs/`** into the same paths. |
| **[`config/README.md`](../config/README.md)** | Explains **legacy JSON** only; YAML is preferred for new configs. |

**Scope import (CSV → YAML fragment):** [USAGE.md](USAGE.md#scope-import-from-csv-config-fragment) and [ops/SCOPE_IMPORT_QUICKSTART.md](ops/SCOPE_IMPORT_QUICKSTART.md) ([pt-BR](ops/SCOPE_IMPORT_QUICKSTART.pt_BR.md)).

## Features

- **Multi-target scanning**: Configure multiple databases, filesystems, APIs, remote shares, **Power BI**, and **Power Apps (Dataverse)** in a single YAML/JSON config. **Scope import (CSV):** `scripts/scope_import_csv.py` emits a YAML fragment of `targets` from a canonical CSV for operator review and merge—see [USAGE.md](USAGE.md#scope-import-from-csv-config-fragment).
- **SQL databases**: PostgreSQL, MySQL, MariaDB, SQLite, Microsoft SQL Server, Oracle (via SQLAlchemy drivers).
- **Power BI (optional)**: Discover workspaces, datasets, and tables via Power BI REST API; sample with DAX. Azure AD OAuth2 (client credentials). Findings in **Database findings** sheet; inventory metadata in **Data source inventory**.
- **Power Apps / Dataverse (optional)**: Discover entities and attributes via Dataverse Web API; sample rows. Azure AD OAuth2 (client credentials). Findings in **Database findings** sheet; inventory metadata in **Data source inventory**.
- **Remote shares (optional)**: SharePoint, WebDAV, SMB/CIFS, NFS — by FQDN or IP with credentials in config; install `.[shares]`.
- **NoSQL (optional)**: MongoDB, Redis — install optional deps: `uv pip install -e ".[nosql]"`.
- **Filesystem**: Recursive scan of local (or mounted) directories; permission check before reading. Supports many extensions: text (`.txt`, `.csv`, `.json`, `.xml`, `.html`, `.md`, `.yml`, `.log`, `.ini`, `.sql`, `.rtf`, subtitle sidecars **`.srt` / `.vtt` / `.ass` / `.ssa`**, etc.), documents (`.pdf`, `.doc`, `.docx`, `.odt`, `.ods`, `.odp`, `.xls`, `.xlsx`, `.xlsm`, `.ppt`, `.pptx`, **`.epub`**), email (`.eml`, `.msg`), and data (`.sqlite`, `.db`, **`.parquet`**, **`.feather`**, **`.orc`**, **`.avro`**, **`.dbf`** when optional **`.[dataformats]`** deps are installed). **Optional rich media:** `file_scan.scan_rich_media_metadata` and `scan_image_ocr` (default off) add EXIF/audio-tag/video-tag text and optional Tesseract OCR; install `.[richmedia]`, and for OCR/video tags ensure **tesseract** / **ffprobe** on `PATH`. **Optional stego hints:** `file_scan.scan_for_stego` (or CLI `--scan-stego` / dashboard / `POST /scan`) appends a short entropy heuristic on image/audio/video — not a stego extractor. **SQLite files** (`.sqlite`, `.sqlite3`, `.db`) found on disk are opened and scanned as databases (discover tables/columns, sample and detect); set `file_scan.scan_sqlite_as_db: false` to skip. Set `file_scan.extensions` to a list of suffixes, or `"*"` / `"all"` for all supported types.
- **Sensitivity detection**: Regex (configurable) + **ML** (TF-IDF + RandomForest) + optional **DL** (sentence embeddings + classifier) on column names and sampled content; no raw data is stored. You can set **ML and DL training terms** in the config (inline or via `ml_patterns_file` / `dl_patterns_file`). See [SENSITIVITY_DETECTION.md](SENSITIVITY_DETECTION.md) (English) or [SENSITIVITY_DETECTION.pt_BR.md](SENSITIVITY_DETECTION.pt_BR.md) (Português – Brasil) for examples. **Lyrics and music tablature** are detected via heuristics so that date-like or digit sequences in song lyrics and guitar tabs are downgraded to MEDIUM/LOW to reduce false positives; strong PII (CPF, email, etc.) still reports HIGH.
- **Multi-language, multi-encoding, and multi-regional**: Config and pattern files support **UTF-8** (recommended), UTF-8 BOM, and legacy encodings (cp1252, Latin-1); the main config is read with **auto-detection**. Compliance samples and reports support **Unicode** and terms in the language of your region (e.g. EN+FR for Canada, PT-BR+EN for Brazil). **Sample configs for UK GDPR, EU GDPR, Benelux, PIPEDA, POPIA, APPI, PCI-DSS, and other regions** are in [compliance-samples/](compliance-samples/); see [COMPLIANCE_FRAMEWORKS.md – Compliance samples](COMPLIANCE_FRAMEWORKS.md#compliance-samples) ([pt-BR](COMPLIANCE_FRAMEWORKS.pt_BR.md#amostras-de-conformidade)) for the list and how to use. Set **`pattern_files_encoding`** when using non-UTF-8 pattern files. See [USAGE – File encoding](USAGE.md#file-encoding-config-and-pattern-files) and [COMPLIANCE_FRAMEWORKS – Multi-language and regional operation](COMPLIANCE_FRAMEWORKS.md#multi-language-multi-encoding-and-multi-regional-operation).
- **Single SQLite**: All findings and failures per session (UUID + timestamp); metadata per scan includes optional **tenant_name** (customer/tenant) and **technician_name** (operator responsible). Separate tables for database findings, filesystem findings, and scan failures.
- **Reporting**: Excel with sheets **"Report info"** (Session ID, Started at, Tenant/Customer, Technician/Operator, Application, Version, Author, License, Copyright), "Database findings", "Filesystem findings", **"Data source inventory"** (best-effort source metadata by target), optional **"Suggested review (LOW)"** (ID-like columns persisted when `detection.persist_low_id_like_for_review` is true — false-negative reduction; see [SENSITIVITY_DETECTION.md](SENSITIVITY_DETECTION.md)), "Scan failures", "Recommendations", "Praise / existing controls" (indications of encryption/hashing/tokenization), **"Trends - Session comparison"** (this run vs up to 3 previous runs; aggregate notes), **"Heatmap data"** (table plus embedded heatmap image, fit-to-one-page when printed), and a standalone sensitivity/risk heatmap PNG. Report info and heatmap include optional Data Boar mascot branding; dashboard/reports pages show application and author attribution.
- **CLI and REST API**: Run one-shot audit from command line or start API (default port 8088) for `/scan`, `/start`, `/scan_database`, `/status`, `/report`, `/heatmap`, `/list`, `/reports/{session_id}`, `/logs`, and `PATCH /sessions/{session_id}` for tenant/technician metadata. **Optional WebAuthn JSON:** when `api.webauthn.enabled` is true and `DATA_BOAR_WEBAUTHN_TOKEN_SECRET` (or the env name in config) is set, JSON endpoints under `/auth/webauthn/` implement a **vendor-neutral** Relying Party (`webauthn` on PyPI) for passkey registration/authentication — see [ADR 0033](adr/ADR-0033-webauthn-open-relying-party-json-endpoints.md). **HTML session gate (Phase 1b):** when WebAuthn is on and at least one passkey exists, locale-prefixed dashboard routes require the signed session cookie (except `help`, `about`, `login` GET). **Optional RBAC (Phase 2, GitHub #86):** `api.rbac.enabled` with Pro+ `dashboard_rbac` enforces roles on API and HTML routes; set `webauthn_credentials.roles_json` (JSON array) or `api.rbac.default_roles` / `api.rbac.api_key_roles` — see [USAGE.md](USAGE.md) and the internal plan **`PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md`** (see `docs/README.md` *Internal and reference*). **HTML** pages use a **locale path prefix** (e.g. `/en/`, `/pt-br/`); JSON endpoints stay unprefixed — see [USAGE.md](USAGE.md). Both modes allow tagging scans with optional **tenant/customer** and **technician/operator** information. **Optional API key** and **rate limiting** (see [USAGE.md](USAGE.md)) protect the API when exposed. The web dashboard includes **Help**, **About** (author and license), and security headers (see [SECURITY.md](../SECURITY.md)). The application works behind NAT, load balancers, and reverse proxies (nginx, Traefik, Caddy); set `X-Forwarded-Proto: https` when TLS is terminated at the proxy.

<a id="detection-stack-vs-generative-llms"></a>

## Detection stack vs generative LLMs (product posture)

**“AI” is not one thing.** Generative **large language models** (LLMs) excel at open-ended completion from a prompt; vendors often market that as “understanding your data,” but outputs can be **non-deterministic** and may **hallucinate** plausible false claims. Data Boar deliberately keeps the **shipped engine** on a **deterministic + supervised** path: **regex** and named patterns, optional structural checks, and **ML/DL** that only **scores evidence already present** in sampled columns or files (with a **fixed `random_state`** for reproducible confidence—see [SENSITIVITY_DETECTION.md](SENSITIVITY_DETECTION.md)).

That posture supports **auditability**: the same config and inputs yield the same **finding taxonomy** and report shapes DPOs can diff across runs. Value-add inventory features stay in the same contract—**quasi-identifier** aggregation and cross-column **re-identification** risk flags, **minor** detection (see [MINOR_DETECTION.md](MINOR_DETECTION.md)), and **jurisdiction hints / tension** plus **anchor jurisdiction** workshop framing (see [JURISDICTION_COLLISION_HANDLING.md](JURISDICTION_COLLISION_HANDLING.md)) are **heuristic metadata**, not generative answers. LLMs may still appear **around** the project (IDE assistants, draft review, test ideas); treat them as **cockpit tooling** with human verification—see [docs/ops/LLM_AGENT_EDITING_CAUTION.md](ops/LLM_AGENT_EDITING_CAUTION.md) and the **Google Gemini** / **Corporate-Entity-C** glossary rows in [GLOSSARY.md](GLOSSARY.md). Compliance framing: [COMPLIANCE_FRAMEWORKS.md](COMPLIANCE_FRAMEWORKS.md#deterministic-detection-vs-generative-llm-hype).

**Historical context (no hype):** From **1950s** symbolic optimism through **AI winters**, **1980s** **expert systems** and **Lisp machines**, the **1990s–2000s** statistical ML wave, **2010s** **deep learning** on **GPUs**, to today’s **large** **transformer** **LLMs**, each wave had **different strengths and failure modes**. A short, vendor-neutral timeline and a “where it fits / limits” table live in [AI_EVOLUTION_PRIMER.md](primers/AI_EVOLUTION_PRIMER.md) ([pt-BR](primers/AI_EVOLUTION_PRIMER.pt_BR.md)); it explains why **voice-assistant** stacks (speech + intent + smaller LMs + rules) are **not** the same product category as **frontier-scale chat** models, and how that history aligns with Data Boar’s **evidence-first** mission.

## Requirements and environment preparation

- **Operating system**: Ubuntu 24.04 LTS / Debian 13 (recommended) or a recent Linux/macOS/Windows.
- **Python**: **≥3.12** supported; **3.13 recommended** for local parity with the **published Docker image** (`python:3.13-slim`).
- **Package manager**: [uv](https://github.com/astral-sh/uv) (recommended) or `pip`.

### Python minor versions (local development vs Docker image)

- **Declared:** `pyproject.toml` requires **Python ≥3.12**. **CI** runs **pytest** on **3.12 and 3.13** (see `.github/workflows/ci.yml`).
- **Recommended locally:** Use **3.13** when your OS packages it (same interpreter family as **Docker Hub** / `latest`); **3.12** remains fully supported.
- **Static analysis:** `sonar.python.version` in `sonar-project.properties` is **3.12** (single value for Sonar’s Python analyzer — not a cap on runtime).
- **Dockerfile** uses **`python:3.13-slim`** — published container images run **CPython 3.13** end-to-end; bump discipline and matrix notes: `docs/plans/PYTHON_UPGRADE_PLAYBOOK.md` (also `PYTHON_UPGRADE_PLAYBOOK.pt_BR.md`).

### Install Python and system libraries (Linux example)

On Debian/Ubuntu:

```bash
sudo apt update
sudo apt install -y python3.13 python3.13-venv python3.13-dev build-essential \
  libpq-dev libssl-dev libffi-dev unixodbc-dev default-libmysqlclient-dev
```

- On older distros without **`python3.13`**, substitute **`python3.12`** / **`python3.12-venv`** / **`python3.12-dev`** (still in CI).
- Matching `python3.*[-dev]` and `build-essential` are required to build some drivers (e.g. database clients).
- `libpq-dev`, `unixodbc-dev` and SSL/FFI headers help when using PostgreSQL, SQL Server, Oracle, or other SQLAlchemy drivers.
- `default-libmysqlclient-dev` provides headers/libs for **mysqlclient** (MySQL/MariaDB); omit it if you use **pymysql** only and wheels cover your platform.

**ThinkPad LAB-NODE-01 + LMDE 7 (Debian 13 base):** full operator checklist (updates, `ufw`, `fwupd`, optional Podman/Docker) — **[LMDE7_LAB-NODE-01_DEVELOPER_SETUP.pt_BR.md](ops/LMDE7_LAB-NODE-01_DEVELOPER_SETUP.pt_BR.md)** ([short EN summary](ops/LMDE7_LAB-NODE-01_DEVELOPER_SETUP.md)).

**Other Linux distributions:** For **RHEL/Fedora/AlmaLinux** (`dnf`), **Arch/Manjaro** (`pacman`), **Gentoo** (`emerge`), **Void** (`xbps`), **Alpine** (`apk`), and other package managers, see **[OS_COMPATIBILITY_TESTING_MATRIX.md](ops/OS_COMPATIBILITY_TESTING_MATRIX.md)** for distro-specific package names and installation notes. **illumos** (OpenIndiana, etc.) / legacy **OpenSolaris** lineage is **exploratory** only — same matrix **Tier 4**; not a supported Linux target.

On Windows:

- Install **Python 3.13** (recommended) or any **3.12+** build from `python.org` and ensure "Add Python to PATH" is checked.
- **WSL2:** Many developers run **`uv sync`** / **`pytest`** inside a **Linux** distro (Debian, Ubuntu, …) for parity with server docs; clone the repo on the **Linux filesystem** inside WSL, not only under `/mnt/c/...`. Optional **extra distros** for compatibility matrix: [WINDOWS_WSL_MULTI_DISTRO_LAB.md](ops/WINDOWS_WSL_MULTI_DISTRO_LAB.md).
- Install database client tools as needed (e.g. Oracle Instant Client, SQL Server ODBC driver) following their vendor docs.

### Install uv

`uv` is a fast Python package/dependency manager:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh          # Linux/macOS
py -m pip install uv                                    # Windows (fallback if installer not used)
```

After installation, ensure `uv` is on your `PATH`:

```bash
uv --version
```

You can always fall back to plain `pip` + virtualenv if you prefer.

## Install the application

```bash
# With uv (recommended) – creates a virtualenv and installs deps
uv sync

# Or with pip (inside an activated virtualenv)
pip install -e .
```

### Running the app with uv

`uv` can also run the application directly with all dependencies:

```bash
# One-shot CLI scan
uv run python main.py --config config.yaml

# Validate config only (same loader as scans/API; exit 0 if OK)
uv run python main.py --config config.yaml --validate-config
uv run python main.py --config config.yaml --diff <session_a_uuid> <session_b_uuid>
uv run python main.py --config config.yaml --diff <session_a_uuid> <session_b_uuid> --fail-on-new-high
uv run python main.py --config config.yaml --export-dsar <session_uuid>
uv run python main.py --config config.yaml --export-dsar <session_uuid> --dsar-output dsar_export.json

# Start the API server (plaintext opt-in; see the transport gate under "REST API")
uv run python main.py --config config.yaml --web --allow-insecure-http --port 8088
```

Optional NoSQL support (MongoDB, Redis):

```bash
uv pip install -e ".[nosql]"
# or: pip install -e ".[nosql]"
```

## Configuration

Use a single config file in **YAML** or **JSON**. The API loads it from `CONFIG_PATH` or `config.yaml` in the working directory. **First-time / evaluation:** see **[docs/samples/README.md](samples/README.md)** ([pt-BR](samples/README.pt_BR.md)) for a one-page map, then copy **[deploy/samples/config.starter-lgpd-eval.yaml](../deploy/samples/config.starter-lgpd-eval.yaml)** (full starter + commented optional blocks) or the minimal **[deploy/config.example.yaml](../deploy/config.example.yaml)** (Docker-oriented); legacy JSON shape is explained under **[config/README.md](../config/README.md)**. For detailed **targets and credentials** (databases, filesystems, APIs with basic/bearer/OAuth2, and shared content), see **[USAGE.md](USAGE.md)**. For **multi-language and multi-regional** use (encoding, compliance samples per region), see [USAGE – File encoding](USAGE.md#file-encoding-config-and-pattern-files) and [COMPLIANCE_FRAMEWORKS](COMPLIANCE_FRAMEWORKS.md#multi-language-multi-encoding-and-multi-regional-operation). Example `config.yaml`:

```yaml
targets:

- name: "Producao_Postgres"

  type: database
  driver: postgresql+psycopg2
  host: 10.0.0.50
  port: 5432
  user: audit_user
  pass: secure_password
  database: customers_db

- name: "Documentos_LGPD"

  type: filesystem
  path: /home/user/Documents/LGPD
  recursive: true

file_scan:
  extensions: [.txt, .csv, .pdf, .docx, .xlsx]
  recursive: true
  scan_sqlite_as_db: true   # open .sqlite/.db files as DBs and scan tables/columns
  sample_limit: 5
  # Optional: scan inside compressed files (zip, tar, gz, bz2, xz, 7z, …)
  # When true, candidate archives are opened and inner members with supported extensions
  # are scanned as regular files. This may significantly increase run time, disk I/O and temp usage;
  # enable only when needed and consider a smaller scope when first enabling. See PLAN_COMPRESSED_FILES.md.
  scan_compressed: false
  # max_inner_size: valid range 1 MB–500 MB (default 10 MB); members larger than this are skipped.
  # max_inner_size: 50_000_000   # optional limit for total inner bytes per archive
  # compressed_extensions: [".zip", ".tar", ".gz", ".tgz", ".bz2", ".xz", ".7z"]
  # use_content_type: false   # magic bytes: PDF slice + rich-media remapping when extension misleads
  # scan_rich_media_metadata: false   # EXIF, mutagen tags, ffprobe (optional binaries)
  # scan_image_ocr: false   # Tesseract via pytesseract + system tesseract-ocr
  # ocr_lang: eng
  # ocr_max_dimension: 2000   # clamped 256–8000

report:
  output_dir: .

api:
  port: 8088

sqlite_path: audit_results.db
scan:
  max_workers: 1   # 1 = sequential; >1 = parallel

# Optional: external pattern files (no code change)
ml_patterns_file: ml_patterns.yaml
regex_overrides_file: regex_overrides.yaml
```

Legacy `config/config.json` with `databases` and `file_scan.directories` is normalized automatically.

### ML patterns file (optional)

YAML/JSON list of `text` + `label` (sensitive / non_sensitive) to train or extend the classifier:

```yaml

- text: "cpf"

  label: sensitive

- text: "system_log"

  label: non_sensitive
```

### Learned patterns (optional)

At the end of each run (when a report is generated), the engine can write **learned patterns**: terms that were classified as sensitive in this scan, so you can merge them into `ml_patterns_file` for the next run. This improves future detection while limiting false positives (only HIGH sensitivity by default, minimum confidence, and exclusion of generic terms like `id`, `name`).

Enable in config:

```yaml
learned_patterns:
  enabled: true
  output_file: learned_patterns.yaml
  min_sensitivity: HIGH      # or MEDIUM to also capture borderline cases
  min_confidence: 70
  min_term_length: 3
  require_pattern: true      # only learn when a pattern was actually detected
  append: true               # merge with existing file
  exclude_if_in_ml_patterns: true   # skip terms already in ml_patterns_file
```

**Merge into ML patterns:** Copy or merge entries from `learned_patterns.yaml` into your `ml_patterns_file`. Each entry has `text` and `label: sensitive`; optional `pattern_detected` and `norm_tag` help you review. Use the same format as the ML patterns file (list of `text` + `label`). After merging, the next run will use the expanded set for the classifier.

### Regex overrides (optional)

YAML/JSON list of `name`, `pattern`, optional `norm_tag`:

```yaml

- name: LGPD_CPF

  pattern: "\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"
  norm_tag: "LGPD Art. 5"
```

### Rate limiting and safety (optional)

To prevent accidental overload (several scans in a row or too many in parallel when called via API/dashboard), you can enable a `rate_limit` block in the main config:

```yaml
rate_limit:
  enabled: true
  max_concurrent_scans: 1
  min_interval_seconds: 0
  grace_for_running_status: 0
```

When `enabled` is true, API endpoints that start scans (`POST /scan`, `/start`, `/scan_database`) may respond with **HTTP 429** and a JSON payload describing the reason (e.g. too many running scans or minimum interval not elapsed). The CLI only prints warnings using the same logic, so existing scripts keep working. See [USAGE.md](USAGE.md) and [data_boar.5](data_boar.5) for full configuration details and examples.

## Run

### CLI (one-shot audit)

```bash
# Minimal run with default options
python main.py --config config.yaml

# Change report/API port via config (no --web here; one-shot mode ignores --port)
python main.py --config config_prod.yaml

# Tag run with tenant/customer and technician/operator
python main.py --config config.yaml --tenant "Acme Corp" --technician "Alice V."

# Report written to report.output_dir, e.g. Relatorio_Auditoria_<session_id>.xlsx
```

### REST API (default port 8088)

```bash
# Start API with default port 8088 (plaintext is an explicit opt-in — see gate below)
python main.py --config config.yaml --web --allow-insecure-http

# Start API on a custom port
python main.py --config config.yaml --web --allow-insecure-http --port 9090

# TLS instead of plaintext (recommended off loopback)
python main.py --config config.yaml --web --https-cert-file server.crt --https-key-file server.key --port 8088
```

**Transport gate:** `main.py --web` requires **either** HTTPS (`--https-cert-file` / `--https-key-file`, or the `api` block in config) **or** an explicit `--allow-insecure-http` (loopback / lab only). Otherwise it exits with code **2** and an error on stderr — so a copy-paste `--web` **without** this flag fails before any scan. This mirrors [USAGE.md](USAGE.md#rest-api-server---web).

```bash
# Not recommended for adoption: bypasses main.py's transport gate AND
# configure_dashboard_transport, so GET /status reports mode: not_configured.
uvicorn api.routes:app --host 0.0.0.0 --port 8088
```

## CLI arguments (reference)

**The full, authoritative CLI reference (all 22 flags — `--config`, `--web`, `--host`, `--port`, `--https-cert-file` / `--https-key-file`, `--allow-insecure-http`, `--validate-config`, `--diff`, `--fail-on-new-high`, `--export-dsar` / `--dsar-output`, `--export-audit-trail`, `--scan-compressed`, `--content-type-check`, `--scan-stego`, `--jurisdiction-hint`, `--reset-data`, `--tenant`, `--technician`, …) lives in [USAGE.md §1 — Command-line interface](USAGE.md#1-command-line-interface-cli).** It is the single source of truth (kept in sync with `main.py`); this guide does not duplicate a partial copy. The live list is always `uv run python main.py --help`.

Quick orientation for the most common ones:

- `--config PATH` — YAML/JSON config (defaults to `config.yaml`). Used by CLI **and** API.
- `--web` — start the REST API / dashboard instead of a one-shot scan (needs the transport gate above: `--allow-insecure-http` or TLS).
- `--port N` / `--host HOST` — bind for `--web` (default `127.0.0.1:8088`; `--host 0.0.0.0` only with network controls).
- `--validate-config` — pre-flight targets, no scan (exit 0 if OK).
- `--reset-data` — **dangerous**: wipe sessions/findings/reports from SQLite (audited in `data_wipe_log`).

When using the API (`--web`), the server loads config from **`CONFIG_PATH`** (environment variable) or `config.yaml` in the working directory if `--config` is not provided on the CLI.

**Web dashboard:** With the server running, open <http://localhost:8088/en/> (or `/pt-br/`) for a simple dashboard: scan status, quantity/quality of discovered data (DB/FS findings, failures), **progress graph over time** (total findings and a risk score per session), optional inputs for **tenant/customer** and **technician/operator** before starting a scan, recent sessions (including tenant/technician columns), and links to **Reports** (list and download) and **Configuration** (edit YAML in the browser). Unprefixed `/` redirects to the negotiated locale (cookie, `Accept-Language`, config). Reports download both ways: the API endpoints above (`/report`, `/reports/{session_id}`) **and** the browser **Download** button on the **Reports** page — for a step-by-step non-technical walkthrough (open `/en/` → set tenant/technician → **Start scan** → **Reports** → **Download**), see [USAGE.md — Web dashboard](USAGE.md#web-dashboard).

## API routes (summary)

| Method   | Endpoint                            | Description                                                                                                                                      |
| -------- | ----------                          | -------------                                                                                                                                    |
| `GET`    | `/health`                           | Liveness/readiness JSON for orchestrators; **not** gated by `require_api_key` (see [SECURITY.md](SECURITY.md)).                                  |
| `GET`    | `/about/json`                       | Machine-readable name, version, author, and license fields for API consumers.                                                                      |
| `POST`   | `/scan` or `/start`                 | Start full audit in background; returns `session_id`. Optional JSON body: `{ "tenant": "Acme Corp", "technician": "Alice" }` to tag the session. |
| `POST`   | `/scan_database`                    | One-off scan of one database (JSON body); returns `session_id`                                                                                   |
| `GET`    | `/status`                           | `running`, `current_session_id`, `findings_count`                                                                                                |
| `GET`    | `/findings`                         | Latest session: unified JSON array of DB + filesystem findings (`source_type`, `norm_tag`, paths/columns, etc.).                                 |
| `GET`    | `/findings/csv`                     | Latest session: findings as UTF-8 CSV attachment.                                                                                               |
| `GET`    | `/findings/{session_id}`            | Same unified JSON schema for a specific session.                                                                                                 |
| `GET`    | `/findings/{session_id}/csv`        | CSV attachment for that session.                                                                                                                 |
| `GET`    | `/report`                           | Download **last generated** Excel report                                                                                                         |
| `GET`    | `/heatmap`                          | Download **last generated** heatmap PNG (sensitivity/risk heatmap for most recent session)                                                       |
| `GET`    | `/list`                             | JSON list of past sessions (`tenant_name`, `technician_name`, counts, status). Query: `sort=date_desc` (default) or `sort=date_asc`. Unprefixed `/reports` redirects to the localized dashboard HTML list (`/{locale}/reports`), not this JSON API. |
| `GET`    | `/reports/{session_id}`             | Regenerate and download report for that session                                                                                                  |
| `GET`    | `/heatmap/{session_id}`             | Regenerate report (if needed) and download heatmap PNG for that session                                                                          |
| `PATCH`  | `/sessions/{session_id}`            | Set or clear tenant/customer name for an existing session. Body: `{ "tenant": "..." }`.                                                          |
| `PATCH`  | `/sessions/{session_id}/technician` | Set or clear technician/operator name for an existing session. Body: `{ "technician": "..." }`.                                                  |
| `GET`    | `/logs`                             | Download the newest `audit_*.log` in the server working directory (plain text).                                                                  |
| `GET`    | `/logs/{session_id}`                | Download the newest `audit_*.log` whose contents mention this `session_id`.                                                                      |

For **deployment**, **using the web API** (with request/response examples), **configuration and credentials** (databases, filesystems, APIs with basic/bearer/OAuth2/custom auth, and shared content), and **downloading current and previous reports**, see **[USAGE.md](USAGE.md)**.

## Supported databases and drivers

| Engine           | Driver (config)             | Note                                                                                                                                   |
| -----------      | --------------------------- | -------------------------                                                                                                              |
| PostgreSQL       | `postgresql+psycopg2`       | psycopg2-binary                                                                                                                        |
| MySQL            | `mysql+pymysql`             | pymysql                                                                                                                                |
| MariaDB          | `mysql+pymysql`             | same as MySQL                                                                                                                          |
| SQLite           | `sqlite`                    | database = path                                                                                                                        |
| SQL Server       | `mssql+pyodbc`              | pyodbc                                                                                                                                 |
| Oracle (19+ RAC) | `oracle+oracledb`           | oracledb (thin mode; no Oracle Client). Config `database` = service name (e.g. customers_db or ORCL).                                  |
| Snowflake        | `snowflake`                 | optional: `uv pip install -e ".[bigdata]"`; config uses `account`, `user`, `pass`, `database`, `schema`, `warehouse`, optional `role`. |
| MongoDB          | `mongodb`                   | optional: pymongo                                                                                                                      |
| Redis            | `redis`                     | optional: redis                                                                                                                        |

For MongoDB/Redis, add a target with `type: database` and `driver: mongodb` or `redis` (host, port, database/password as needed). Install optional deps: `uv pip install -e ".[nosql]"`. For Snowflake, add a target with `type: database` and `driver: snowflake` and install the `.[bigdata]` extra.

## REST/API targets and authentication

You can scan remote HTTP(S) APIs for personal or sensitive data by adding targets with `type: api` or `type: rest`. The connector calls the configured endpoints (GET), parses JSON, and runs the same sensitivity detection on field names and sample values. **Authentication** is configurable so you can use static credentials, bearer tokens (e.g. negotiated or issued by an IdP), or OAuth2 client credentials.

**Required:** `name`, `base_url` (or `url`). **Optional:** `paths` or `endpoints` (list of path strings, e.g. `["/users", "/orders"]`), `discover_url` (GET returns a list of paths to scan), `timeout`, `headers`, and an `auth` block.

**SSRF guard (#832):** `base_url`, `discover_url`, and `auth.token_url` resolving to link-local (cloud metadata `169.254.0.0/16`), loopback, or private (RFC1918/ULA) hosts are **rejected by default** — the target records a failure and no request is sent. Scanning internal infrastructure is a normal Data Boar use case, so opt in per target with `allow_private_networks: true`. Non-`http(s)` schemes are always rejected. The same guard applies to SharePoint (`site_url`), WebDAV (`base_url`), and Power BI (custom `auth.token_url`).

**Default outbound User-Agent:** discovery HTTP(S) clients send **`DataBoar-Prospector/<version>`** (same resolved version as the installed `data-boar` package — `core.about.get_http_user_agent()`). Use this string in remote WAF or API-gateway logs to identify this product. If a vendor requires a different token, set **`User-Agent`** (case-insensitive key) under `headers` on the target; that value **overrides** the default for REST/API. SharePoint, Power BI, and Dataverse connectors apply the same default. See [ADR 0034](adr/ADR-0034-outbound-http-user-agent-data-boar-prospector.md).

### Auth types

| Type              | Use case                                                             | Config                                                                                                                                                          |
| ------            | ----------                                                           | --------                                                                                                                                                        |
| **basic**         | Static username and password                                         | `auth: { type: basic, username: "...", password: "..." }`                                                                                                       |
| **bearer**        | Static or negotiated token (e.g. from Kerberos/AD, or API key)       | `auth: { type: bearer, token: "..." }` or `token_from_env: "MY_TOKEN_VAR"`                                                                                      |
| **oauth2_client** | OAuth2 client credentials (machine-to-machine)                       | `auth: { type: oauth2_client, token_url: "<https://...",> client_id: "...", client_secret: "..." }` (or `client_secret: "${ENV_VAR}"` to read from environment) |
| **custom**        | Custom headers (e.g. `Authorization: Negotiate ...`, API key header) | `auth: { type: custom, headers: { "Authorization": "Bearer ...", "X-API-Key": "..." } }`                                                                        |

If you omit `auth` but set `user`/`username` and `pass`/`password` on the target, **basic** auth is used.

## Example config (YAML) — API/REST

```yaml
targets:

- name: "Internal Users API"

  type: api
  base_url: "https://api.example.com"
  paths: ["/users", "/profiles"]
  auth:
    type: oauth2_client
    token_url: "https://auth.example.com/oauth/token"
    client_id: "audit-client"
    client_secret: "${API_OAUTH_SECRET}"
    scope: "read:users"

- name: "Legacy API (basic)"

  type: rest
  base_url: "https://legacy.example.com"
  paths: ["/v1/contacts"]
  auth:
    type: basic
    username: "audit_user"
    password: "***"

- name: "API with bearer token (e.g. negotiated)"

  type: api
  base_url: "https://api.example.com"
  paths: ["/data"]
  auth:
    type: bearer
    token_from_env: "NEGOTIATED_TOKEN"   # or use "token" for static value

- name: "API with custom header"

  type: api
  base_url: "https://api.example.com"
  paths: ["/export"]
  auth:
    type: custom
    headers:
      Authorization: "Bearer ..."
      X-Requested-By: "data-boar"
```

Findings from API targets appear in the **Filesystem findings** sheet with `file_name` like `GET /users | email` (endpoint and field). The project uses **httpx** (already a dependency) for HTTP; no extra install is required for the REST connector.

## Power BI and Power Apps (Dataverse)

You can scan **Power BI** (datasets and tables) and **Power Apps / Dataverse** (entities and columns) as data sources. Both use **Azure AD OAuth2 client credentials** (app registration with a client secret). No extra install is required (httpx is already a dependency).

### Power BI

- **Type:** `powerbi`
- **Auth:** Azure AD app with Power BI permissions (`Dataset.Read.All` or `Dataset.ReadWrite.All`). Enable "Allow service principals to use Power BI APIs" in the Power BI admin portal if using a service principal.
- **Config:** `tenant_id`, `client_id`, `client_secret` (or under `auth:`). Optional: `workspace_ids` or `group_ids` to limit to specific workspaces; omit to use "My workspace" and all workspaces the app can see.

The connector lists datasets and tables (push datasets expose table schema; for others it samples via DAX), runs sensitivity detection on column names and sample values, and writes **Database findings** (schema = dataset name, table = table name, column = column).

### Example config (YAML) — Power BI

```yaml
targets:

- name: "Power BI Compliance"

  type: powerbi
  tenant_id: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
  client_id: "yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy"
  client_secret: "${POWERBI_CLIENT_SECRET}"   # or literal
  # optional: limit to specific workspaces
  # workspace_ids: ["group-guid-1", "group-guid-2"]
```

### Power Apps / Dataverse

- **Type:** `dataverse` or `powerapps`
- **Auth:** Azure AD app with application permission to Dataverse (e.g. "Common Data Service" / `user_impersonation` or env-specific application permission). Admin consent required.
- **Config:** `org_url` (or `environment_url`), e.g. `<https://myorg.crm.dynamics.co>m`, plus `tenant_id`, `client_id`, `client_secret` (or under `auth:`).

The connector lists entities (tables), their attributes, samples rows, runs sensitivity detection, and writes **Database findings** (schema = entity logical name, table = entity set, column = attribute).

### Example config (YAML) — Dataverse

```yaml
targets:

- name: "Dataverse HR"

  type: dataverse
  org_url: "https://myorg.crm.dynamics.com"
  tenant_id: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
  client_id: "yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy"
  client_secret: "${DATAVERSE_CLIENT_SECRET}"
```

Use the same `file_scan.sample_limit` (default 5) to control how many rows are sampled per table/entity for Power BI and Dataverse.

## SharePoint, WebDAV, SMB/CIFS, and NFS shares

You can scan remote file shares by **FQDN or IP** with credentials in config. Install optional deps:
`uv pip install -e ".[shares]"`
(installs `smbprotocol`, `webdavclient3`, `requests_ntlm`).

| Type               | Host / URL                                                         | Credentials                       | Notes                                                                   |
| ------             | ------------                                                       | -------------                     | --------                                                                |
| **sharepoint**     | `site_url`: `<https://host/sites/sitenam>e`                        | `user`, `pass`; NTLM or basic     | On-prem or URL; path = server-relative folder (e.g. `Shared Documents`) |
| **webdav**         | `base_url`: `<https://host/pat>h`                                  | `user`, `pass`                    | Recursive list and download                                             |
| **smb** / **cifs** | `host`: FQDN or IP, `share`: share name, `path`: path inside share | `user`, `pass`, optional `domain` | Port 445 default                                                        |
| **nfs**            | `path`: **local mount point** (NFS must be mounted first)          | —                                 | `host` / `export_path` for reporting only                               |

### Example config (YAML) — File shares

```yaml
targets:
  # SMB/CIFS (Windows or Samba)
- name: "FileServer HR"

  type: smb
  host: "fileserver.company.local"   # or 10.0.0.10
  share: "HR"
  path: "Documents"
  user: "audit_user"
  pass: "***"
  domain: "COMPANY"                 # optional
  port: 445
  recursive: true

  # WebDAV
- name: "WebDAV Storage"

  type: webdav
  base_url: "https://webdav.company.com/dav"
  user: "audit"
  pass: "***"
  path: "archive"
  recursive: true
  verify_ssl: true

  # SharePoint (on-prem or URL; NTLM or basic)
- name: "SharePoint HR"

  type: sharepoint
  site_url: "https://sharepoint.company.com/sites/hr"
  path: "Shared Documents"
  user: "audit@company.com"
  pass: "***"

  # NFS (path = local mount point; mount NFS first)
- name: "NFS Export"

  type: nfs
  host: "nfs.company.local"
  export_path: "/export/data"
  path: "/mnt/nfs_data"             # local mount point
```

All share types use the same **file_scan** settings (extensions, recursive, scan_sqlite_as_db, sample_limit) from config. Findings appear in the **Filesystem findings** sheet.

When you enable `file_scan.use_content_type: true`, the share connectors use the same helper as the filesystem connector. **Simple cloaking** here means the **filename extension** does not match the **real** container (e.g. PDF bytes behind a `.txt` or **non-text** extension such as `.mp3`). Extension-only tools route wrong; magic bytes still expose `%PDF-...` or a rich-media signature, so PDFs are treated as PDF for extraction, and **image/audio/video** with misleading extensions are remapped via the shared magic-byte table. **`scan_rich_media_metadata`** / **`scan_image_ocr`** apply to SMB, WebDAV, and SharePoint the same way (and inside **scan_compressed** archives when those members match). This remains **opt-in**; with the flag disabled, scanning stays extension-based for type choice (aside from explicit rich-media extensions when those flags add them to the effective extension set).

For a **single run** without editing the saved config, use CLI **`--content-type-check`**, or **`POST /scan`** / **`POST /start`** with **`content_type_check: true`**, or the dashboard checkbox next to **Start scan** (same semantics as **`--scan-compressed`** / **`scan_compressed`** for archives).

## Adding new connectors

To support a new data source (e.g. another database driver or API), see **[ADDING_CONNECTORS.md](ADDING_CONNECTORS.md)** (English) or **[ADDING_CONNECTORS.pt_BR.md](ADDING_CONNECTORS.pt_BR.md)** (Português – Brasil). The guide describes the connector contract, how to register a new type (or driver), optional dependencies, and includes step-by-step instructions plus examples (database-style and API-style).

## Logging and alerts

- Log file: `audit_YYYYMMDD.log` (and console).
- On each finding (possible personal/sensitive data), the app logs and prints an `[ALERT]` to the console so the operator is notified on the fly.

## Rust acceleration module (`boar_fast_filter`) and encoding boundary

The optional `boar_fast_filter` Rust extension (built with [maturin](https://github.com/PyO3/maturin) + PyO3) provides a fast pre-filter stage: it receives a **batch of Python `str` objects** and returns the indexes of rows that contain CPF-like patterns, e-mail addresses, or potential credit-card sequences. Rows without any of those patterns are skipped before the slower ML/DL pipeline.

**Encoding boundary (important for malformed-byte files):**

The Rust module operates exclusively on decoded Python strings — it never receives raw bytes. All file-reading and encoding resolution happens on the **Python side** before `filter_batch` is called:

- The filesystem connector reads text files with `errors="replace"` (default). Malformed byte sequences become the Unicode replacement character `U+FFFD` (`?`). The file is **not skipped** — it is analyzed with replacement characters in place.
- If you need stricter behavior (e.g., skip files with encoding errors instead of silently replacing bytes), set `targets[].encoding_errors: "strict"` in your config. A `ScanFailure` entry is written to the SQLite audit log for every file where a `UnicodeDecodeError` occurs in strict mode.
- The Rust pre-filter inherits whichever `str` the Python layer produces. If a CPF or e-mail straddles a replaced byte, the pattern may not match — this is a known, acceptable trade-off; the deterministic regex stage on the Python side still runs on the full replacement-substituted text.
- For binary or truly undecodable files, the connector records them as `scan_failures` rather than silently excluding them from the audit log.

**Build notes (lab environments):**

Building `boar_fast_filter` requires Rust (`rustup`), `maturin`, and a C linker. On Python 3.13 hosts built without `liblzma-dev`, the `.7z` extra may fail independently of the Rust extension. The Maestro orchestration scripts include a "Dependency Doctor" workflow that auto-detects missing C extensions, attempts OS package manager remediation (`apt install liblzma-dev`, `xbps-install lzma`, etc.), and marks the host with a `7z_UNSUPPORTED` feature flag when the OS library cannot be installed.

**Capable host (build locally) vs constrained host (prebuilt wheel):** `maturin` is a
**dev dependency** (`[dependency-groups].dev` in `pyproject.toml`; added via `uv add --dev maturin`).
Compiling the Rust extension is RAM- and CPU-intensive, so the build path is split by host class:

| Host class | Path | Command |
| ---------- | ---- | ------- |
| **Capable** (≥4 GB RAM, dev/lab/CI host) | Build in place from source | `uv sync` then `uv run maturin develop --release` |
| **Constrained** (<4 GB RAM, e.g. Raspberry Pi 3B) | Install a prebuilt **abi3** wheel — never compile | consume the wheel from the wheel-matrix (#782) |

The extension is **optional at runtime**: when `boar_fast_filter` is absent, the engine falls back to
the pure-Python pre-filter (slower, identical findings). A constrained host that cannot build and has
no matching wheel still runs correctly on the Python path. The cross-host wheel-matrix that produces the
abi3 wheels for constrained hosts is tracked in **#782**.

## Dependencies and security

- **Source of truth:** For the **uv** toolchain, **`pyproject.toml`** is the single source of truth for declared dependencies; **`uv.lock`** pins the resolved tree for reproducible installs (avoids “it worked yesterday” breakage). **pip** and **`requirements.txt`** are derivative (requirements.txt is exported from the lockfile for pip-based environments). Do not edit **`uv.lock`** or **`requirements.txt`** by hand for version changes. When you add, remove, or change a dependency, edit **`pyproject.toml`** only, then run `uv lock` and export.

- **Regenerate lockfile and requirements.txt after any dependency change:**

  ```bash
  # From project root: resolve and lock, then export for pip
  uv lock
  uv export --frozen --no-emit-project -o requirements.txt
  ```

  Commit **pyproject.toml**, **uv.lock**, and **requirements.txt**. The export uses **`--no-emit-project`** so the file is **pip-installable** for uv-less clients: `pip install -r requirements.txt` installs the **pinned, hashed dependency set** (it does **not** install Data Boar itself — add the project with `pip install .` from the repo, or run from source). Earlier exports emitted an editable `-e .` line alongside hashes, which pip rejects in one pass (`--require-hashes`); `--no-emit-project` removes it.

- **Supply-chain posture:** **`uv.lock`** pins versions (and hashes) for reproducible installs; it **does not** replace **`pip-audit`**, Dependabot, or maintainer review for **known CVEs** and supply-chain abuse. See **[SECURITY.md](../SECURITY.md)** (*Lockfile and supply-chain mitigation*).

- **Dependabot / automation:** If a PR (e.g. from Dependabot) suggests updating only `requirements.txt` or `uv.lock`, apply the change to the **source of truth** first: update the corresponding minimum version in **`pyproject.toml`**, then run `uv lock` and `uv export --frozen --no-emit-project -o requirements.txt` and commit all three files. Do not merge a dependency update that only edits `requirements.txt` or `uv.lock`.

- **Check for known CVEs:** Run `uv pip audit` (or `pip audit` if available) before deployment; fix or pin any vulnerable packages.
- See also **Security and compliance** below.

## Man pages

For systems that use the traditional `man` interface, two manual pages are provided:

- **Section 1 (command):** [data_boar.1](data_boar.1) — describes the program, its options, the web API, and curl examples. View with `man data_boar` (or `man lgpd_crawler` if you installed the compatibility symlink).
- **Section 5 (file formats):** [data_boar.5](data_boar.5) — describes the main config file topology and optional files (regex overrides, ML/DL pattern files, learned patterns), with examples. View with `man 5 data_boar` (or `man 5 lgpd_crawler` with compatibility symlink).

On Linux/BSD, section 1 is for executable commands; section 5 is for configuration and file format conventions. Install the **Data Boar** man pages and, for backward compatibility, optional symlinks so `man lgpd_crawler` also works (see below).

**Install both pages** (create the target directories first so the copy does not fail if they are missing). Right after creating the directories, run `chmod 755` on them so that all users can access the man pages; depending on your default umask, new directories may otherwise be 750 and only root could traverse them. After copying, run `chmod 644` on the installed files so that all users can read the pages (copied files may otherwise be 640).

```bash
sudo mkdir -p /usr/local/share/man/man1/
sudo mkdir -p /usr/local/share/man/man5/
sudo chmod 755 /usr/local/share/man/man1/ /usr/local/share/man/man5/
sudo cp docs/data_boar.1 /usr/local/share/man/man1/
sudo cp docs/data_boar.5 /usr/local/share/man/man5/
sudo chmod 644 /usr/local/share/man/man1/data_boar.1 /usr/local/share/man/man5/data_boar.5
# Optional: compatibility symlink for environments that still invoke `lgpd_crawler`
sudo ln -sf data_boar.1 /usr/local/share/man/man1/lgpd_crawler.1
sudo ln -sf data_boar.5 /usr/local/share/man/man5/lgpd_crawler.5
sudo mandb    # or: sudo makewhatis   # depends on distro
```

After installation, `man data_boar` and `man 5 data_boar` show the command and config formats. If you added the compatibility symlinks, `man lgpd_crawler` and `man 5 lgpd_crawler` show the same pages (legacy command alias).

```bash
man data_boar        # command and options (section 1)
man 5 data_boar      # config and file formats (section 5)
```

When adding new CLI options or API capabilities, update [data_boar.1](data_boar.1); when adding or changing config keys or pattern file formats, update [data_boar.5](data_boar.5) and the root [README](../README.md). For **version bumps** (major.minor.build convention and where to update the version number), see [VERSIONING.md](VERSIONING.md).

## Deploy with Docker

You can run the API as a **single container** (`docker run`), with **Docker Compose**, **Docker Swarm**, or **Kubernetes**. You may either **pull the pre-built image** from Docker Hub or **build from source** after cloning the repo.

### Pre-built image (Docker Hub)

Docker images are available on **Docker Hub** so you can run the application without cloning the repository:

- **Docker Hub:** [hub.docker.com/r/fabioleitao/data_boar](https://hub.docker.com/r/fabioleitao/data_boar) — `fabioleitao/data_boar:latest` and `fabioleitao/data_boar:1.7.3`

The image includes regex + ML + optional DL sensitivity detection; you can set ML/DL training terms in config (see [SENSITIVITY_DETECTION.md](SENSITIVITY_DETECTION.md) and [deploy/config.example.yaml](../deploy/config.example.yaml)).

Example: run the web API with a local config directory:

```bash
docker pull fabioleitao/data_boar:latest
docker run -d -p 8088:8088 -v /path/to/your/data:/data -e CONFIG_PATH=/data/config.yaml fabioleitao/data_boar:latest
```

Prepare `/data/config.yaml` from `deploy/config.example.yaml` (see [deploy/DEPLOY.md](deploy/DEPLOY.md) ([pt-BR](deploy/DEPLOY.pt_BR.md))). You can decide to use this image as an instanced container instead of pulling the code from Git and building locally.

> **Docker report output:** `report.output_dir` defaults to `.` (the container working directory). Inside a container that path is **ephemeral** — the Excel/heatmap files vanish when the container stops. Point `report.output_dir` at a **mounted volume** (for example `/data` in the example above) so reports land on the host, **or** retrieve them through the dashboard **Download** button / the `/report` and `/reports/{session_id}` API endpoints.

### Build from source

- **Build:** `docker build -t data_boar:latest .` (or `docker build -t fabioleitao/data_boar:latest .` to push to Docker Hub; see [deploy/DEPLOY.md](deploy/DEPLOY.md)).
- **Run:** Mount config at `/data/config.yaml` (see `deploy/config.example.yaml`). Expose port 8088.
- **Compose:** `docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.override.yml up -d` (prepare `./data/config.yaml` first).
- **Swarm:** `docker stack deploy -c deploy/docker-compose.yml -c deploy/docker-compose.override.yml data-boar-audit`.
- **Kubernetes:** `kubectl apply -f deploy/kubernetes/` (see [deploy/kubernetes/README.md](deploy/kubernetes/README.md)).

Full steps (build, push, single container, Compose, Swarm, Kubernetes): **[deploy/DEPLOY.md](deploy/DEPLOY.md)** ([pt-BR](deploy/DEPLOY.pt_BR.md)). For MCP, build and push from source: [DOCKER_SETUP.md](DOCKER_SETUP.md) ([pt-BR](DOCKER_SETUP.pt_BR.md)).

## Compliance frameworks and extensibility

The application explicitly references **LGPD**, **GDPR**, **CCPA**, **HIPAA**, and **GLBA** in built-in patterns and report labels. We provide **sample configuration and config-file examples** (e.g. [regex_overrides.example.yaml](regex_overrides.example.yaml), recommendation overrides in [USAGE.md](USAGE.md)) so you can extend to **UK GDPR**, **PIPEDA**, **POPIA**, **APPI**, **PCI-DSS**, or custom norms without code changes: set **`norm_tag`** in [regex overrides](SENSITIVITY_DETECTION.md#custom-regex-patterns-detecting-new-personalsensitive-values) or custom connectors to any framework label, and use **`report.recommendation_overrides`** in config to tailor recommendation text. We can **assist with tuning** (tailored configs or slight code changes) for further compatibility when you reach out. See **[COMPLIANCE_FRAMEWORKS.md](COMPLIANCE_FRAMEWORKS.md)** ([pt-BR](COMPLIANCE_FRAMEWORKS.pt_BR.md)) for the full list of supported regulations, sample files, and extensibility.

## Security and compliance

- No raw sampled content is persisted; only metadata (location, pattern, sensitivity, norm tag).
- The web API adds security headers by default (X-Content-Type-Options, X-Frame-Options, Content-Security-Policy, Referrer-Policy, Permissions-Policy, and HSTS when served over HTTPS). See [SECURITY.md](../SECURITY.md).
- **Optional integrity verification (design spec):** runtime hash cross-check of critical artifacts, tinted-state behavior, and audit logging — see [ops/INTEGRITY_CHECK_ALPHA_LOGIC.md](ops/INTEGRITY_CHECK_ALPHA_LOGIC.md) ([pt-BR](ops/INTEGRITY_CHECK_ALPHA_LOGIC.pt_BR.md)).
- Use recent, CVE-patched versions of the interpreter and dependencies (`uv sync` / `pip install -e .`).
- Keep credentials in config files or environment; avoid committing secrets.
- **Behind a reverse proxy (nginx, Traefik, Caddy):** Set `X-Forwarded-Proto: https` for TLS-terminated traffic so HSTS and scheme detection work correctly.
- **Reporting vulnerabilities:** See [SECURITY.md](../SECURITY.md). **Testing:** See [TESTING.md](TESTING.md). **Contributing:** See [CONTRIBUTING.md](../CONTRIBUTING.md).

## Documentation (see also)

**Topic map (minors, jurisdiction hints, child-privacy samples, bridges):** [MAP.md](MAP.md) · [MAP.pt_BR.md](MAP.pt_BR.md). **Full index (all topics, EN and pt-BR):** [README.md](README.md) · [README.pt_BR.md](README.pt_BR.md). **Root intro:** [../README.md](../README.md) · [../README.pt_BR.md](../README.pt_BR.md). **Configuration and API usage:** [USAGE.md](USAGE.md) · [USAGE.pt_BR.md](USAGE.pt_BR.md). **Sensitivity (ML/DL):** [SENSITIVITY_DETECTION.md](SENSITIVITY_DETECTION.md) · [SENSITIVITY_DETECTION.pt_BR.md](SENSITIVITY_DETECTION.pt_BR.md). **Deploy:** [deploy/DEPLOY.md](deploy/DEPLOY.md) · [deploy/DEPLOY.pt_BR.md](deploy/DEPLOY.pt_BR.md). **Connectors:** [ADDING_CONNECTORS.md](ADDING_CONNECTORS.md) · [ADDING_CONNECTORS.pt_BR.md](ADDING_CONNECTORS.pt_BR.md). **Compliance:** [COMPLIANCE_FRAMEWORKS.md](COMPLIANCE_FRAMEWORKS.md) · [COMPLIANCE_FRAMEWORKS.pt_BR.md](COMPLIANCE_FRAMEWORKS.pt_BR.md). **Testing, security, contributing:** [TESTING.md](TESTING.md) · [TESTING.pt_BR.md](TESTING.pt_BR.md), [SECURITY.md](../SECURITY.md) · [SECURITY.pt_BR.md](../SECURITY.pt_BR.md), [CONTRIBUTING.md](../CONTRIBUTING.md) · [CONTRIBUTING.pt_BR.md](../CONTRIBUTING.pt_BR.md). **Copyright/trademark:** [COPYRIGHT_AND_TRADEMARK.md](COPYRIGHT_AND_TRADEMARK.md) · [COPYRIGHT_AND_TRADEMARK.pt_BR.md](COPYRIGHT_AND_TRADEMARK.pt_BR.md).

## Topic map (peripheral guides)

For **CISO / DPO / architect** paths that tie posture to concrete config (minors, jurisdiction hints, U.S. child-privacy samples, FELCA positioning), use **[MAP.md](MAP.md)** ([pt-BR](MAP.pt_BR.md)) instead of searching folder-by-folder. It links **[MINOR_DETECTION.md](MINOR_DETECTION.md)** ([pt-BR](MINOR_DETECTION.pt_BR.md)), the **jurisdiction hints** section of **[USAGE.md](USAGE.md)** ([pt-BR](USAGE.pt_BR.md)), **[ADR 0026](adr/ADR-0026-optional-jurisdiction-hints-dpo-facing-heuristic-metadata-only.md)**, **[JURISDICTION_COLLISION_HANDLING.md](JURISDICTION_COLLISION_HANDLING.md)** ([pt-BR](JURISDICTION_COLLISION_HANDLING.pt_BR.md)), **[ADR 0038](adr/ADR-0038-jurisdictional-ambiguity-alert-dont-decide.md)**, and the relevant **COMPLIANCE_FRAMEWORKS** / **compliance-samples** rows in one place.

## License and copyright

See [LICENSE](../LICENSE). Project and copyright notice: [NOTICE](../NOTICE). For making copyright and trademark official (registration, registries): [COPYRIGHT_AND_TRADEMARK.md](COPYRIGHT_AND_TRADEMARK.md) ([pt-BR](COPYRIGHT_AND_TRADEMARK.pt_BR.md)).
