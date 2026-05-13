# Plan: Secrets and password protection (vault and alternatives)

**Status:** Completed
**Date:** 2026-03-15
**Authors:** Fabio Leitao
**Priority:** H3
**Depends on:** ADR-0005

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md) (central to-do list)

## When implementing steps: update docs and tests; then update PLANS_TODO.md and this file.

This plan aims to **reduce risk** around passwords and other secrets used for data sources (databases, file shares, dashboards, APIs) in a **compliance and data-mapping** context: keep secrets off config files where possible, support optional import into a vault with references, and allow re-import from config via a flag (CLI and web). If a full vault is not feasible in all environments, **alternatives** are proposed to still improve protection.

---

## Goals

- **Keep secrets off files:** Prefer storing credentials in a vault or environment variables instead of plain text in `config.yaml` / `config.json`.
- **Import from YAML once, then reference:** Allow one-time (or repeated) import of secrets from the config file into a vault; after import, config can hold only references (e.g. `@vault:...`) so the file can be safely versioned or shared without secrets.
- **Optional removal from config after import:** When using a vault, optionally replace secret values in the config file with vault references (or a marker like “already imported”) so the file no longer contains plain secrets.
- **Re-import from config via flag:** Provide a way to **reload credentials from the config file** (CLI flag and web action) so operators can reconfigure access to data sources (e.g. after a password rotation) without redesigning the system.
- **No regressions:** All behaviour remains optional and backward compatible; existing configs with inline secrets continue to work.

---

## Current state: where secrets live

| Location        | What                                                                                                                                                                                                                                             |
| --------        | -----                                                                                                                                                                                                                                            |
| **Config file** | `targets[].pass` / `password`, `user`; `api.api_key`, `api.api_key_from_env`; Power BI/Dataverse/REST: `client_secret`, `token`, `token_from_env`, `auth.password`; SMB/SharePoint/WebDAV: `user`, `pass`; Redis/Snowflake: `pass` / `password`. |
| **Environment** | Already supported: `api.api_key_from_env`; Power BI/Dataverse/REST `client_secret` via `${VAR}`; REST `token_from_env`.                                                                                                                          |
| **Web UI**      | GET `/config` returns **raw file content** (including secrets) in a textarea; POST `/config` saves whatever YAML is submitted (including secrets). So the config file is the source of truth and can be edited (and leaked) via the UI.          |

Config is loaded in **config/loader.py** and **normalize_config()**; connectors read credentials from the normalized target/config dict (e.g. **connectors/sql_connector.py**, **mongodb_connector.py**, **rest_connector.py**, **powerbi_connector.py**, **dataverse_connector.py**, **smb_connector.py**, **sharepoint_connector.py**, **webdav_connector.py**, **snowflake_connector.py**, **redis_connector.py**).

**Operator password manager (Bitwarden, etc.):** Independent of Phase B, you can keep **master copies** of passwords and API keys in **Bitwarden** (free tier is usually enough for a solo operator) and **paste or inject** into env at runtime — see **[../ops/OPERATOR_SECRETS_BITWARDEN.md](../ops/OPERATOR_SECRETS_BITWARDEN.md)**. That does **not** replace `pass_from_env` or future `@vault:` resolution inside the app.

---

## Feasibility: vault with import and re-import

## Feasible, with constraints.

- **Vault backend options**
- **Local encrypted store:** A single file or SQLite DB (e.g. `secrets.vault` or under `~/.config/...`) encrypted with a key from env (e.g. `VAULT_KEY` or `VAULT_KEY_FILE`). Secrets keyed by a stable id (e.g. `targets.db1.pass`, `api.api_key`). Works for single-node, single-user or shared server where the key is in env or a mounted secret.
- **External vault (HashiCorp Vault, AWS Secrets Manager, Azure Key Vault):** Config would reference paths (e.g. `@vault:secret/data/db1`). No “import from YAML” into external vault in this plan (secrets are created in the external system by the operator). The app only **resolves** references at load time.
- **Import from YAML**
- On a dedicated action (CLI flag or web “Import secrets to vault”), the app reads the current config file, extracts known secret fields (see list above), writes them into the vault under canonical keys, then can optionally **rewrite the config file** replacing plain values with `@vault:<key>` (or leave file unchanged and only use vault in memory; see “Optional removal” below).
- **Re-import from config**
- **CLI:** e.g. `python main.py --config config.yaml --reimport-secrets-from-config`. Loads `config.yaml` (which may again contain plain secrets, e.g. after operator edits it), imports those secrets into the vault (overwriting existing entries for the same keys), then proceeds with normal run (or exits after import if we add a “dry-run” style flag).
- **Web:** A button or endpoint e.g. “Re-import secrets from current config file”. Server reads the **current config file from disk** (not the textarea), extracts secrets, writes to vault, invalidates in-memory config so next scan uses new credentials. Optionally show “Secrets re-imported” and do not expose raw secrets in the UI (see “Redaction” below).
- **Constraints**
- **Key management:** For a local vault, the encryption key must live somewhere (env or file). If the key is lost, vault contents are unrecoverable; if the key is leaked, vault is compromised. Document clearly.
- **Multi-node:** A local file vault is not shared across machines. For multi-node deployments, use env vars or an external vault.
- **Audit:** Some organisations require a specific HSM or vault product; the plan should allow “reference-only” mode (config only has `@vault:...` or env refs, no import path).

So: a **local vault with import/re-import is feasible**; an **external vault with reference-only** is feasible; **re-import via CLI and web is feasible** by re-reading the config file and overwriting vault (or env) entries.

---

## If full vault is not adopted: alternatives to still reduce risk

These can be implemented **instead of** or **in addition to** a vault.

1. **Expand env-only for all credentials**
   - For every secret field (pass, api_key, client_secret, token, etc.), support a `*_from_env` (or existing `*_from_env` / `${VAR}`) so the config file holds **no** secrets, only references like `pass_from_env: "DB_PASS"`. Document as the recommended pattern; keep inline secrets working for backward compatibility.
   - **Pro:** No new storage; fits 12-factor and containers. **Con:** Many env vars for many targets; no “import from file” story.

1. **Redact secrets in the web UI**
   - When serving GET `/config`, do **not** send raw file content. Parse the config, replace known secret values (pass, password, api_key, client_secret, token, etc.) with a placeholder (e.g. `# REDACTED - set via env or vault` or `@env:VAR_NAME` if from env), then serialize to YAML and send that to the browser. So the UI never displays or transmits real secrets.
   - On POST `/config`, if the submitted YAML contains only placeholders for secrets (or unchanged refs), merge with in-memory or vault-resolved values so we don’t overwrite secrets with empty/placeholder. Optionally: “Save” never writes secret values to disk, only refs/placeholders.
   - **Pro:** Reduces leakage via browser, copy-paste, logs. **Con:** Editing config in the UI becomes “refs only” for secrets; operators must use env/vault or re-import flow to set secrets.

1. **Config file permissions and “do not commit”**
   - Document that `config.yaml` must have restricted permissions (e.g. chmod 600) and must **not** be committed to version control. Add `config.yaml` (and `*.vault` if we add a vault file) to `.gitignore` in examples. SECURITY.md and USAGE already mention this; reinforce and add a short “Secrets handling” section.

1. **CLI re-import without vault**
   - Even without a vault, a “reload config and apply” action can help: e.g. `--reload-config` that re-reads the config file and invalidates in-memory config so the next scan uses updated credentials. That gives “reconfigure credentials by editing the file and running with a flag” without implementing a vault.

---

## Recommended scope for this plan

- **Phase A – Low-risk, high-value (do first)**
- Expand **env-only** for all credential fields (pass_from_env, client_secret_from_env, etc.) and document “secrets in env, not in config”.
- **Redact secrets in GET /config** (and optionally on save) so the UI never shows or writes plain secrets.
- Document **config file permissions** and “do not commit”; add release checklist item.

- **Phase B – Vault (optional)**
- Introduce an optional **secrets vault**: local encrypted store (key from env) and/or external vault (reference-only). Config may use references like `pass: "@vault:targets.db1.pass"` or `pass: "@env:DB_PASS"`.
- **Import from YAML:** CLI flag and web action “Import secrets to vault” (read config file, push secrets to vault, optionally rewrite config with refs).
- **Re-import from config:** CLI `--reimport-secrets-from-config` and web “Re-import secrets from config file” (read file, overwrite vault entries, invalidate cache).
- **Optional removal from config:** After import, optionally replace secret values in the config file with `@vault:...` so the file no longer contains plain secrets; mark in docs that “already imported” is represented by the presence of vault refs.

- **Phase C – Polish**
- Release checklist: ensure no secrets in logs; SECURITY.md and USAGE updated; vault key management and multi-node limitations documented.

---

## To-dos (concise)

| #           | To-do                                                                                                                                                                                                                                  | Status    |
| ---         | -----                                                                                                                                                                                                                                  | ------    |
| **Phase A** |                                                                                                                                                                                                                                        |           |
| A1          | Add `pass_from_env` / `password_from_env` (and equivalent for every connector secret) in config schema and loader; resolve from env when present. Document in USAGE and SECURITY.                                                      | ✅ Done    |
| A2          | Redact secret values when serving GET /config (parse → replace secrets with placeholder → serialize). Ensure POST /config does not overwrite secrets with placeholder when user saves; merge or keep refs.                             | ✅ Done    |
| A3          | Document config file permissions, .gitignore for config.yaml and vault file, and "do not commit secrets"; add to SECURITY.md and release checklist.                                                                                    | ✅ Done    |
| **Phase B** |                                                                                                                                                                                                                                        |           |
| B1          | Design vault key schema (e.g. `targets.<name>.pass`, `api.api_key`, `targets.<name>.client_secret`) and reference format in config (`@vault:key` or `@env:VAR`).                                                                       | ⬜ Pending |
| B2          | Implement local encrypted vault (single file or SQLite, key from VAULT_KEY or VAULT_KEY_FILE); encrypt at rest.                                                                                                                        | ⬜ Pending |
| B3          | In config loader: when a value is `@vault:...`, resolve from vault; when `@env:...`, resolve from env. Keep inline and existing env behaviour.                                                                                         | ⬜ Pending |
| B4          | CLI: add `--reimport-secrets-from-config` (and optionally `--import-secrets-to-vault` once) to read config file and write secrets to vault; optionally rewrite config with vault refs.                                                 | ⬜ Pending |
| B5          | Web: add "Re-import secrets from config file" action (and "Import secrets to vault" if not yet imported); read file from disk, update vault, invalidate in-memory config. Do not expose raw secrets in UI (redaction already from A2). | ⬜ Pending |
| B6          | Optional: "Remove secrets from config after import" – when importing, rewrite config file replacing plain secrets with `@vault:...` so file is safe to store/share.                                                                    | ⬜ Pending |
| **Phase C** |                                                                                                                                                                                                                                        |           |
| C1          | Document vault key management, multi-node limitation (local vault), and external-vault option (reference-only); add to SECURITY.md and USAGE.                                                                                          | ⬜ Pending |
| C2          | Release checklist: no secrets in logs; vault and env usage documented.                                                                                                                                                                 | ⬜ Pending |

---

## Why a full vault might be "not feasible" in some cases

- **Key management:** The local vault needs an encryption key; storing it in env or a file shifts but does not eliminate the secret-management problem. Acceptable for many single-node deployments; not enough for strict HSM/compliance without an external vault.
- **Multi-node / high availability:** A local file vault is not shared across processes or nodes. For multi-instance deployments, env vars or an external vault (HashiCorp Vault, cloud secret manager) is required.
- **Operational overhead:** Teams that already use a corporate vault may prefer to keep secrets only there and have the app reference them (reference-only mode), without an "import from YAML" step.

So the plan keeps **vault optional** and emphasises **env expansion** and **UI redaction** as always-useful improvements even if the full vault is not adopted.

---

## Order of execution

1. **Phase A** (no vault): A1 → A2 → A3. Delivers immediate risk reduction (env-only, no secrets in UI, documentation).
1. **Phase B** (vault): B1 → B2 → B3 → B4 → B5 → B6. Enables "secrets off file" and re-import via CLI and web.
1. **Phase C**: C1, C2 after B is usable.

---

---

## Execution log (progress and history)

| Date       | Step | Action                                                                                                                                                                |
| ---------- | ---- | ------                                                                                                                                                                |
| 2026-03    | A1   | pass_from_env, password_from_env, user_from_env, auth.token_from_env, auth.client_secret_from_env, client_secret_from_env in config/loader.py; USAGE + SECURITY docs. |
| 2026-03    | A2   | config/redact_config.py: redact_config_for_display, merge_config_on_save; GET /config redacts, POST merges; tests in test_security.py.                                |
| 2026-03    | A3   | .gitignore: config.yaml, *.vault; SECURITY.md + docs/SECURITY.pt_BR.md config file and redaction; CONTRIBUTING release checklist.                                     |

## Update this table when completing each step; keep Status cells in the tables above in sync.

---

*Last updated: plan created. Update this doc when completing steps or when new security recommendations are adopted.*
