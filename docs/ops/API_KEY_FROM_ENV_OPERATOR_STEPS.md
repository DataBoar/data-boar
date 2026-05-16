# API key via environment variable — concrete operator steps (English)

**Purpose:** Remove ambiguity about `api.api_key_from_env`. This matches **`config/loader.py`** (normalized config): the YAML value is the **name** of an environment variable; the **secret** is supplied only at runtime (shell, systemd, Docker, Kubernetes Secret, etc.).

**Full technician walkthrough (API key + HTTPS, Let’s Encrypt, lab certs, Docker):** [SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.md](SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.md) ([pt-BR](SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.pt_BR.md)).

**Risk note:** A synthetic key below is **only** for learning. For any real deployment, generate a **new** strong random secret; never reuse examples from documentation.

---

## 1. What you configure vs what you never commit

| Item                       | Meaning                                                                                                                         |
| ----                       | -------                                                                                                                         |
| **`api.api_key_from_env`** | A **string**: the **name** of the OS environment variable (e.g. `AUDIT_API_KEY`). This name may appear in **git-tracked** YAML. |
| **The actual API key**     | The **value** of that variable at process start. It must **not** be committed; set it in the environment or a secret store.     |

**Precedence (important):** If `api.api_key` is set in YAML to a **non-empty** string, that literal wins and **`api_key_from_env` is ignored** for loading the key. For env-only workflow, **omit** `api_key` or leave it empty and use only `api_key_from_env`.

---

## 2. Minimal `config.yaml` fragment (example names only)

```yaml
api:
  port: 8088
  host: "127.0.0.1"
  require_api_key: true
  api_key_from_env: "AUDIT_API_KEY"
  # Do not set api_key here when using the environment (or set it to empty).
```

---

## 3. Synthetic secret (documentation / lab only)

Use **only** to verify wiring. **Do not** use this string in production.

- **Environment variable name:** `AUDIT_API_KEY`
- **Synthetic value (fake):** `SYN_EXAMPLE_k7Qm_9pL2_vN4wR8xT1`

---

## 4. Set the variable and start the app

### Linux / macOS (bash)

```bash
export AUDIT_API_KEY='SYN_EXAMPLE_k7Qm_9pL2_vN4wR8xT1'
uv run python main.py --web --config config.yaml
```

### Windows PowerShell (current session)

```powershell
$env:AUDIT_API_KEY = "SYN_EXAMPLE_k7Qm_9pL2_vN4wR8xT1"
uv run python main.py --web --config config.yaml
```

### Windows PowerShell (persistent user env — optional)

```powershell
[System.Environment]::SetEnvironmentVariable("AUDIT_API_KEY", "SYN_EXAMPLE_k7Qm_9pL2_vN4wR8xT1", "User")
```

Restart the terminal (or log off/on) so new processes see it.

### systemd (Linux service)

In the service unit, under `[Service]`:

```ini
Environment="AUDIT_API_KEY=SYN_EXAMPLE_k7Qm_9pL2_vN4wR8xT1"
```

Prefer **`EnvironmentFile=-/etc/data-boar/secrets.env`** with mode `0600` and **no** commit of that file.

---

## 5. Verify the API accepts your key

## Health (no key required):

```bash
curl -sS http://127.0.0.1:8088/health
```

Expect HTTP **200** and JSON with `"status":"ok"` (or equivalent).

## Protected route without key (should fail):

```bash
curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8088/status
```

Expect **401** when `require_api_key` is true and the key is required.

## Same request with key:

```bash
curl -sS -H "X-API-Key: SYN_EXAMPLE_k7Qm_9pL2_vN4wR8xT1" http://127.0.0.1:8088/status
```

Expect **200** (or another success), not 401.

---

## 5b. Staging before production (recommended order)

1. **Inventory** callers of the API (scripts, cron, CI, probes, internal dashboards). If the list is empty, you still run the checks so the **first** production user is not discovering 401/503 surprises cold.
1. **Staging:** set `api.require_api_key: true`, `api.api_key_from_env: "AUDIT_API_KEY"` (or your name), export the variable, and use **HTTPS** (`--https-cert-file` / `--https-key-file` or TLS at the reverse proxy) where applicable. Confirm **`GET /health`** without a key (200) vs **`GET /status`** without a key (**401**).
1. **Clients:** add **`X-API-Key`** or **`Authorization: Bearer`** to every non-health request; pin **TLS trust** (enterprise CA, `mkcert` chain in lab only, etc.).
1. **Production:** roll out with a **short** compatibility window only if needed (e.g. plaintext **`--allow-insecure-http`** or HTTP behind TLS-terminating proxy). **Phase it out** using **`GET /status` / `GET /health`** (`dashboard_transport`) and **`python main.py --export-audit-trail`** (same field in JSON) so insecure posture stays traceable.
1. Full narrative: **[SECURE_BY_DEFAULT_BLOCKERS_AND_MIGRATION.md](SECURE_BY_DEFAULT_BLOCKERS_AND_MIGRATION.md)**.

---

## 6. Docker / Compose (pattern)

Set the **same** variable name the config references; value from host env or Compose `secrets`:

```yaml
environment:

- AUDIT_API_KEY=${AUDIT_API_KEY}

```

Do **not** hard-code real secrets in `docker-compose.yml` checked into git.

---

## 7. Kubernetes (pattern)

Use a **Secret** and inject as env:

- Reference env var name **`AUDIT_API_KEY`** in the Pod spec.
- Mount or generate the Secret outside this repo; see **`deploy/kubernetes/README.md`** § Security.

---

## 8. Troubleshooting

| Symptom                                                        | Check                                                                                                                                                                                   |
| -------                                                        | -----                                                                                                                                                                                   |
| **401** on all routes except `/health`                         | Variable **name** in YAML matches exactly; variable is set **before** the process starts; no typo in `export` / systemd / container env.                                                |
| **503** on routes (not `/health`) with `require_api_key: true` | No key resolved: env var missing, wrong name, or empty value; or `api.api_key` left blank without `api_key_from_env`. **`main.py --web`** should **exit 2** before listen in this case. |
| Key seems ignored                                              | Non-empty **`api.api_key`** in YAML overrides env — remove literal or empty it.                                                                                                         |
| Works in shell, fails as service                               | Service unit does not inherit your login env — set **`Environment`** or **`EnvironmentFile`**.                                                                                          |

---

## Related

- **`SECURITY.md`** (repo root) — § Optional API key (enterprise)
- **`docs/USAGE.md`** — Configuration / Authentication
- **`config/loader.py`** — `api_key_from_env` resolution
- **`tests/test_api_key.py`** — Behaviour when `require_api_key` is true

**Português:** same steps apply; variable names are ASCII by convention.
