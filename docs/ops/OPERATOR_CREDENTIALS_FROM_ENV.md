# Operator credentials: env layer + vault-forward (English)

**Português (Brasil):** [OPERATOR_CREDENTIALS_FROM_ENV.pt_BR.md](OPERATOR_CREDENTIALS_FROM_ENV.pt_BR.md)

**Purpose:** Document the **stable** way to pass passwords, PATs, and API tokens into Data Boar — and how that stays **compatible** with Bitwarden today and with **Phase B** / enterprise vaults later.

**Not** a substitute for [OPERATOR_SECRETS_BITWARDEN.md](OPERATOR_SECRETS_BITWARDEN.md) (human vault habits) or [PLAN_SECRETS_VAULT.md](../plans/PLAN_SECRETS_VAULT.md) (in-app `@vault:` backlog).

---

## 1. Layers (what is stable vs what evolves)

| Layer | Role | Status |
| ----- | ---- | ------ |
| **A — Tracked YAML** | Names only: `pass_from_env`, `token_from_env`, `api_key_from_env`, … | **Stable product contract** (Phase A shipped) |
| **B — Process environment** | Secret **values** present when `main.py` starts | **Stable**; what connectors actually read |
| **C — Optional on-disk bridge** | `~/.config/databoar/*.env` (`chmod 0600`) + `scripts/databoar-env-load.*` | **Convenience**; not required if you inject env another way |
| **D — Operator vault** | Bitwarden (CLI/`bw`), future org vaults | **Human / enterprise SoT** → inject into **B** |
| **E — In-app / external vault refs** | `@vault:…`, HashiCorp / cloud KMS (plan Phase B+) | **Backlog**; still resolve into memory/env-equivalent at load |

**Rule:** Do not invent a second secret channel in YAML that bypasses **A→B**. New vault products should **populate environment variables** (or future `@vault:` resolution that the loader already planned) with the **same names** your `*_from_env` keys point to.

```text
  Bitwarden / HCP Vault / K8s Secret / systemd EnvironmentFile
                         │
                         ▼
              OS environment (layer B)
                         │
                         ▼
         config *_from_env  →  connector / API
```

Optional disk files sit **beside** that path as a local bridge — never as the long-term “only” story for enterprises that already run a vault.

---

## 2. Least privilege (every credential)

Whatever the source (PAT, DB password, share account):

1. **Read-only** when the connector only samples (HubSpot Private App: the six **read** scopes in [ADDING_CONNECTORS.md](../ADDING_CONNECTORS.md) §7 — no write, no webhooks).
2. **Narrow grants** on SQL (SELECT on needed schemas only).
3. **Share / FS:** least folder ACL for the scan identity.
4. **One secret per system** in the vault item (and preferably one `*.env` file per system under `~/.config/databoar/`) so rotation does not force rewriting unrelated targets.

---

## 3. Recommended layouts

### 3.1 Enterprises / vault-first (preferred when available)

1. Store the secret in Bitwarden (or corp vault).
2. At session start, inject into env — examples:

```bash
# Bitwarden CLI (operator unlocks; never commit BW_SESSION)
export BW_SESSION="$(bw unlock --raw)"
export HUBSPOT_PRIVATE_APP_TOKEN="$(bw get password 'Data Boar — HubSpot Private App')"
uv run python main.py --config /path/to/config.yaml
```

```powershell
$env:BW_SESSION = (bw unlock --raw)
$env:HUBSPOT_PRIVATE_APP_TOKEN = (bw get password "Data Boar — HubSpot Private App")
uv run python main.py --config C:\path\to\config.yaml
```

3. YAML only names the variable (`token_from_env` / default `HUBSPOT_PRIVATE_APP_TOKEN`).

Same pattern works with **systemd `EnvironmentFile=`**, **Docker/K8s secrets → env**, or a corporate vault agent that writes env before start.

### 3.1b Docker / Podman — same `KEY=value` files (degrau 2 → 3)

Prefer **orchestrator injection** (degrau **3**): Compose/K8s **Secret → environment**, or `podman run -e VAR=…`. When you already keep a host `KEY=value` file (degrau **2**), pass it without `source` inside the image:

```bash
# Lab / oneshot — file stays on the host; container only sees env
podman run --rm \
  --env-file "${HOME}/.config/databoar/hubspot.env" \
  -e CONFIG_PATH=/data/config.yaml \
  -v "${PWD}/data:/data:Z" \
  fabioleitao/data_boar:lab
```

Compose (do **not** commit real values):

```yaml
services:
  data-boar:
    env_file:
      - ./secrets/hubspot.env   # gitignored KEY=value
    # or: environment: { HUBSPOT_PRIVATE_APP_TOKEN: ${HUBSPOT_PRIVATE_APP_TOKEN} }
```

Tracked pattern for the dashboard API key: [API_KEY_FROM_ENV_OPERATOR_STEPS.md](API_KEY_FROM_ENV_OPERATOR_STEPS.md) §6. Follow-up: issue **#1611** (docs completeness + optional CLI `--env-file` evaluation).

### 3.2 Solo / lab — XDG env files (optional bridge)

```text
~/.config/databoar/          # mkdir; chmod 700
  hubspot.env                # chmod 0600 — HUBSPOT_PRIVATE_APP_TOKEN=…
  postgres-lab.env           # DEMO_DB_PASSWORD=…
  agent-sessions.env         # optional; used by primary-linux-agent-sessions.sh
```

```bash
mkdir -p ~/.config/databoar && chmod 700 ~/.config/databoar
# move or create *.env files; chmod 0600 each
. ./scripts/databoar-env-load.sh hubspot   # or omit name to load all *.env
uv run python main.py --validate-config --config /path/to/config.yaml
uv run python main.py --config /path/to/config.yaml
```

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.config\databoar"
. .\scripts\databoar-env-load.ps1 -Name hubspot
uv run python main.py --config C:\path\to\config.yaml
```

Override directory: **`DATA_BOAR_ENV_DIR`**.

**Do not** commit these files. Prefer migrating high-value secrets into Bitwarden and treating `*.env` as a disposable cache you can delete after vault injection works.

### 3.3 Nothing on disk (possible, higher toil)

Export only for the shell lifetime (`export VAR=…` / `$env:VAR=…`) or paste from the vault UI once per session. Same **A→B** contract; more typing, less filesystem residue.

---

## 4. HubSpot (example)

| Item | Value |
| ---- | ----- |
| YAML | `type: hubspot` (optional `token_from_env`) |
| Default env name | `HUBSPOT_PRIVATE_APP_TOKEN` |
| XDG file (optional) | `~/.config/databoar/hubspot.env` |
| Vault item (optional) | same env name as custom field / password field |

Full connector scopes and Forms vs CRM: [ADDING_CONNECTORS.md](../ADDING_CONNECTORS.md) §7.

---

## 5. Roadmap alignment

| Track | What lands |
| ----- | ---------- |
| **Phase A (done)** | `*_from_env` + GET `/config` redaction — [PLAN_SECRETS_VAULT.md](../plans/PLAN_SECRETS_VAULT.md) |
| **This doc + loaders** | Documented **B** + optional **C**; vault-forward wording |
| **Bitwarden operator path** | [OPERATOR_SECRETS_BITWARDEN.md](OPERATOR_SECRETS_BITWARDEN.md) — inject into **B** |
| **Phase B (backlog)** | Local encrypted store / `@vault:` / external vault resolve — still **names in YAML**, values not in Git |

When Phase B ships, existing `*_from_env` configs keep working; vault refs become an additional resolution path, not a breaking rename of HubSpot/SQL env vars.

---

## See also

- [USAGE.md](../USAGE.md) — *Credentials from environment*
- [API_KEY_FROM_ENV_OPERATOR_STEPS.md](API_KEY_FROM_ENV_OPERATOR_STEPS.md) — dashboard API key
- [SECURITY.md](../../SECURITY.md) — config file and secrets
- [TOKEN_AWARE_SCRIPTS_HUB.md](TOKEN_AWARE_SCRIPTS_HUB.md) — `databoar-env-load.*`
