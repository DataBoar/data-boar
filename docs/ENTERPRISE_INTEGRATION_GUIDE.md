# Enterprise integration guide (IT / SRE)

**Português (Brasil):** [ENTERPRISE_INTEGRATION_GUIDE.pt_BR.md](ENTERPRISE_INTEGRATION_GUIDE.pt_BR.md)

This page is for **DevOps, security engineering, and SRE** who install and operate Data Boar next to existing pipelines. It is **not** a price list, a volume/franchise quote, or a sales pitch. Capability bands: [SUBSCRIPTION_TIERS.md](SUBSCRIPTION_TIERS.md). Code gate: `FEATURE_TIER_MAP` in `core/licensing/tier_features.py`. How to run: [USAGE.md](USAGE.md). Deploy topologies: [deploy/DEPLOY.md](deploy/DEPLOY.md) ([pt-BR](deploy/DEPLOY.pt_BR.md)).

**Audience:** CLI, Python, and CI/CD familiarity. Compliance narrative lives in [COMPLIANCE_FRAMEWORKS.md](COMPLIANCE_FRAMEWORKS.md), not here.

## What this guide will not invent

- **No Data Boar prices, SKU quotes, or estate-size franchises.** The public site still says pricing is coming soon; commercial terms are under review. JWT **quantity** claims that already ship (`dbmax_workers`, `dbmax_deployments`) are documented in [SUBSCRIPTION_TIERS.md](SUBSCRIPTION_TIERS.md) and [LICENSING_SPEC.md](LICENSING_SPEC.md) — that is not a bill.
- **SSO:** the **shipped map key** is `sso_saml` (Enterprise). There is **no** implemented SAML/OIDC/LDAP login handshake in this repository as of this writing. OIDC and LDAP remain **intent** in internal plans — do not treat them as delivered IdP integration.
- **No Markdown links into `docs/plans/`** from this page ([ADR 0004](adr/ADR-0004-external-docs-no-markdown-links-to-plans.md)).
- **Config encyclopedia:** every YAML key is **not** copied here (it would rot). Canonical keys and examples: [USAGE.md](USAGE.md) (root keys, timeouts, notifications) and [deploy/samples/](../deploy/samples/).

## 1. System requirements

| Need | Truth in tree |
| ---- | ------------- |
| **Python** | `requires-python = ">=3.12"` in `pyproject.toml`. |
| **Installer** | [uv](https://docs.astral.sh/uv/) is the maintainer path (`uv sync`); pip/pipx also work for published wheels. |
| **OS** | CPython on **Linux** and **Windows** (native or WSL2). Distro flavour (Debian family, RHEL family, Void, …) is a **host** concern: NFS/SMB clients, `tesseract`, `ffprobe` live on `PATH`, not inside the wheel. |
| **PowerShell** | Optional. Repo wrappers under `scripts/*.ps1` help **operators**; the product entrypoint is `python main.py` (see [USAGE.md](USAGE.md)). |
| **`py7zr` / 7z** | Optional extra **`compressed`**: `py7zr` in `pyproject.toml`. Without it, ZIP/tar still work via the stdlib; **`.7z` members are skipped** (graceful), not a hard crash. Install with `uv sync --extra compressed` or `pip install 'data-boar[compressed]'`. Distro packages are optional; do not treat a single package manager command as the only supported path. |
| **NFS / SMB** | Product extras: `.[shares]`. The **kernel/userland** NFS or Samba **client** is an OS package (`nfs-utils`, `cifs-utils`, etc. — names vary). Mounting is usually IT’s job; Data Boar needs **read + list** on the mounted path ([ops/OPERATOR_IT_REQUIREMENTS.md](ops/OPERATOR_IT_REQUIREMENTS.md)). |
| **`boar_fast_filter` (Rust / PyO3)** | **Optional accelerator.** The PyPI `data-boar` wheel is `py3-none-any` with **no** compiled extension — regex matching falls back to **pure Python**. On paid tiers, `--validate-config` **WARN**s if the wheel is missing. The wheelhouse is the **documented** channel for the Rust stage ([TROUBLESHOOTING.md](TROUBLESHOOTING.md)). It is **not** required to produce findings. |

## 2. Deployment patterns

Canonical Docker/Compose/Swarm/Kubernetes: [deploy/DEPLOY.md](deploy/DEPLOY.md). Image vs CLI override is spelled there (default **web** on **8088**; one-shot CLI must **not** pass `--web`).

| Pattern | Pointer |
| ------- | ------- |
| **Standalone CLI** | `python main.py --config /path/config.yaml` (optional `--tenant` / `--technician`). Persist `sqlite_path` and `report.output_dir` on a volume. |
| **CI/CD step** | Pre-flight `--validate-config` ([#532](https://github.com/DataBoar/data-boar/issues/532)); scan; optional `--diff` + `--fail-on-new-high` ([#565](https://github.com/DataBoar/data-boar/issues/565)). Keep secrets in CI secret stores, not YAML. |
| **Scheduled scan** | Host **cron** / **systemd timer** / orchestrator CronJob calling the same CLI. Product key `scheduled_scans` is **Pro**; `scan_scheduler_ui_enterprise` is an **Enterprise map key** (UI), not a substitute for a working timer. |
| **Air-gapped / no internet** | Mirror the application wheel (and optional extras / `boar_fast_filter` wheelhouse) into an internal index; `pip install --no-index --find-links …` as in [TROUBLESHOOTING.md](TROUBLESHOOTING.md). Load Docker images from an **internal registry**. There is no separate “air-gap SKU”. |

## 3. Configuration

1. Copy a **tracked sample**, do not assemble YAML from memory: [deploy/samples/config.starter-lgpd-eval.yaml](../deploy/samples/config.starter-lgpd-eval.yaml) and [docs/samples/README.md](samples/README.md).
1. Put credentials in the **environment** (`*_from_env` keys). `--validate-config` **WARN**s on unset env vars without scanning.
1. **Connectors:** types and required keys are validated on `--validate-config`. Which connectors exist and which **band** they need: [SUBSCRIPTION_TIERS.md](SUBSCRIPTION_TIERS.md) + `FEATURE_TIER_MAP` (example: generic REST / self-hosted SQL-NoSQL are Community; Power BI, SharePoint, Snowflake, SAP, object storage, SMB/NFS/WebDAV, MSSQL, Oracle are **Pro** unless the map says otherwise). Authoring a new connector: [ADDING_CONNECTORS.md](ADDING_CONNECTORS.md). Pattern plugins: [PLUGIN_AUTHOR_GUIDE.md](PLUGIN_AUTHOR_GUIDE.md).
1. Timeouts and retries: global `timeouts:` and per-target `connect_timeout` / `read_timeout` in [USAGE.md](USAGE.md); connectivity failures: [TROUBLESHOOTING_CONNECTIVITY.md](TROUBLESHOOTING_CONNECTIVITY.md).

```bash
python main.py --config /path/config.yaml --validate-config
# exit 0 → [OK]; exit 1 → [INVALID] (unknown connector, missing keys, …)
```

## 4. CI/CD features (shipped CLI)

| Flag | Role | Origin |
| ---- | ---- | ------ |
| `--validate-config` | Parse + connector/driver/key check; no scan on `[INVALID]` | [#532](https://github.com/DataBoar/data-boar/issues/532) |
| `--diff SESSION_A SESSION_B` | New / resolved / severity-changed findings | [#565](https://github.com/DataBoar/data-boar/issues/565) |
| `--fail-on-new-high` | With `--diff`: exit **1** if `SESSION_B` has new **HIGH** rows | same |
| `--export-dsar SESSION_ID` | DSAR-oriented JSON (metadata-first); `--dsar-output PATH` | [#522](https://github.com/DataBoar/data-boar/issues/522) |
| `--export-audit-trail [PATH]` | JSON trail from SQLite (session summary, trust fields, …) | [USAGE.md](USAGE.md) |

Unknown `--diff` session UUID → exit **2**. Do **not** combine `--web` with these export/diff flags.

## 5. Existing stack (SIEM, GRC, notifications, API)

| Integration | What exists |
| ----------- | ----------- |
| **SIEM / audit** | Ingest `--export-audit-trail` JSON (fields documented in [USAGE.md](USAGE.md)). **SARIF / SIEM push** is a **Pro+** band capability in [SUBSCRIPTION_TIERS.md](SUBSCRIPTION_TIERS.md) — not an open-core webhook to Splunk. |
| **GRC / CSV-JSONL** | Excel reports, DSAR JSON, audit JSON, GRC executive schema: [REPORTS_AND_COMPLIANCE_OUTPUTS.md](REPORTS_AND_COMPLIANCE_OUTPUTS.md), [GRC_EXECUTIVE_REPORT_SCHEMA.md](GRC_EXECUTIVE_REPORT_SCHEMA.md). |
| **Slack / Teams / generic webhook** | `notifications.enabled` (default **off**). Operator Slack webhook + kill-switch / channel policy: [ops/OPERATOR_NOTIFICATION_CHANNELS.md](ops/OPERATOR_NOTIFICATION_CHANNELS.md). Manual: `python scripts/notify_webhook.py`. |
| **HTTP API** | Default port **8088**. Endpoints: [USAGE.md](USAGE.md) / [TECH_GUIDE.md](TECH_GUIDE.md) (`/scan`, `/status`, `/health`, `/docs`, …). **Auth:** optional API key (`X-API-Key` or `Authorization: Bearer`). Optional WebAuthn JSON when enabled. **`GET /health` stays unauthenticated** on purpose. |

## 6. Troubleshooting

| Symptom | What to do |
| ------- | ---------- |
| **`boar_fast_filter` missing / does not build** | Expected on PyPI-only installs. Findings still run in Python. See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) (`boar_fast_filter` is not on PyPI). Optional: inject from a matching wheelhouse. `--prefilter-status` prints readiness JSON. |
| **Connector timeout** | Raise `timeouts.connect_seconds` / `read_seconds` or per-target overrides; reduce `scan.max_workers`; see [TROUBLESHOOTING_CONNECTIVITY.md](TROUBLESHOOTING_CONNECTIVITY.md). |
| **`$HOME` is root / empty under systemd or `sudo`** | Do **not** store scan corpora or reports under an implicit home. Set **absolute** `sqlite_path`, `report.output_dir`, and credential env vars on the **service user**. Privileged helper scripts in this repo resolve the invoking user via `SUDO_USER` / `getent` when they must — production units should still use explicit paths. |
| **`.7z` not scanned** | Install the **`compressed`** extra (`py7zr`). Without it, skip is expected. |

Auth and credentials: [TROUBLESHOOTING_CREDENTIALS_AND_AUTH.md](TROUBLESHOOTING_CREDENTIALS_AND_AUTH.md).

## 7. Deployment security

### API key default is open ([#549](https://github.com/DataBoar/data-boar/issues/549))

Tracked samples keep **`api.require_api_key` false** so a laptop lab can start. That is **not** a production posture.

**Workaround (required on non-loopback binds):**

1. Set `api.require_api_key: true`.
1. Set a strong key via `api.api_key_from_env` (preferred) or `api.api_key` (do not commit).
1. Prefer loopback + reverse proxy with TLS. `main.py --web` **warns** on stderr if bind is non-loopback and no effective key is configured; it **exits 2** if the key is required but missing.
1. Full behaviour: root [SECURITY.md](../SECURITY.md), [docs/SECURITY.md](SECURITY.md), [ops/SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.md](ops/SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.md).

### Filesystem permissions

Least privilege for **scan targets**: [ops/OPERATOR_IT_REQUIREMENTS.md](ops/OPERATOR_IT_REQUIREMENTS.md). The **process** needs write only where **it** persists SQLite and reports — not on customer data stores.

### Signing keys (do not mix two worlds)

- **Product license JWT:** [LICENSING_SPEC.md](LICENSING_SPEC.md) — rotate **issuer** material according to your agreement; this guide does not publish procedures that belong in private commercial packs.
- **[ADR 0056](adr/ADR-0056-cryptographic-adr-inventory-inv-adr-ssh-attestation.md)** (`inv-adr.ps1`, `docs/adr/INVENTORY.txt`, SSH ed25519): that is **repository G0-S attestation** for Architecture Decision Records. It is **not** the dashboard SSO key and **not** a customer “rotate SAML certs” runbook. Fork maintainers follow the ADR; IT deploying the scanner does not need that ritual to scan.

## Related product docs

| Doc | Why |
| --- | --- |
| [SUBSCRIPTION_TIERS.md](SUBSCRIPTION_TIERS.md) | Six public bands; no `docs/PRICING.md` |
| [USAGE.md](USAGE.md) | CLI/API/config |
| [TECH_GUIDE.md](TECH_GUIDE.md) | Install, connectors, notifications |
| [PLUGIN_SDK.md](PLUGIN_SDK.md) | Enterprise remediation plugin host (L1) |
| [AUDIENCE_GUIDE.md](AUDIENCE_GUIDE.md) | Who reads what |
| [hubs/INDEX.md](hubs/INDEX.md) | Map of maps |
