# Secure dashboard: API authentication and HTTPS (technician how-to)

**Português (Brasil):** [SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.pt_BR.md](SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.pt_BR.md)

**Audience:** Technicians who will turn on **API key protection** and **TLS** for the Data Boar web dashboard (`main.py --web`). This complements (does not replace) [USAGE.md](../USAGE.md) ([pt-BR](../USAGE.pt_BR.md)), root [SECURITY.md](../../SECURITY.md) ([pt-BR](../../SECURITY.pt_BR.md)), and [deploy/DEPLOY.md](../deploy/DEPLOY.md) ([pt-BR](../deploy/DEPLOY.pt_BR.md)).

**Related runbooks:** [API_KEY_FROM_ENV_OPERATOR_STEPS.md](API_KEY_FROM_ENV_OPERATOR_STEPS.md) (env wiring detail), [SECURE_BY_DEFAULT_BLOCKERS_AND_MIGRATION.md](SECURE_BY_DEFAULT_BLOCKERS_AND_MIGRATION.md) ([pt-BR](SECURE_BY_DEFAULT_BLOCKERS_AND_MIGRATION.pt_BR.md)) (rollout order), [PLAN_DASHBOARD_HTTPS_BY_DEFAULT_AND_HTTP_EXPLICIT_RISK.md](../plans/completed/PLAN_DASHBOARD_HTTPS_BY_DEFAULT_AND_HTTP_EXPLICIT_RISK.md) (product rationale and anti-patterns).

**Optional WebAuthn JSON (Phase 1a):** When **`api.webauthn.enabled: true`** and the token secret env (default **`DATA_BOAR_WEBAUTHN_TOKEN_SECRET`**) is set before startup, the API exposes **`/auth/webauthn/*`** for **FIDO2 / passkey** registration and authentication ([ADR 0033](../adr/ADR-0033-webauthn-open-relying-party-json-endpoints.md)). **`api.require_api_key`** does **not** apply to those paths. This does **not** require login for the HTML dashboard yet; browser session gates and RBAC are **[#86](https://github.com/FabioLeitao/data-boar/issues/86)** follow-up. Pytest subset: [SMOKE_WEBAUTHN_JSON.md](SMOKE_WEBAUTHN_JSON.md).

---

## Part A — Require API authentication (shared API key)

### A.0 What the application does (behaviour you must match)

1. When **`api.require_api_key: true`**, the process must have a **resolved** secret: either non-empty **`api.api_key`** in config, or **`api.api_key_from_env: "VAR"`** with **`VAR` set in the environment before startup**.
1. **`main.py --web`** **exits with code 2** if `require_api_key` is true but **no key** can be resolved (prevents an accidentally open dashboard).
1. **`GET /health`** is **never** authenticated (probes and load balancers stay simple). It returns JSON including `status`, a public `license` summary, and `dashboard_transport`.
1. **All other routes** (HTML pages, `GET /status`, `POST /scan`, `GET /config`, OpenAPI `/docs`, …) require a valid key when enforcement is active: send **`X-API-Key: <secret>`** or **`Authorization: Bearer <secret>`**.
1. **401** = missing or wrong key. **503** = `require_api_key` is true but the key could not be resolved at runtime (misconfiguration); fix env/YAML and restart.

**Tracked YAML:** Put **only** the **name** of the env var in config (e.g. `api_key_from_env: "AUDIT_API_KEY"`). **Never** commit the actual secret. Precedence: a non-empty literal **`api.api_key`** in YAML **overrides** the env path — for env-only operation, omit `api_key` or leave it empty.

### A.1 Generate a strong secret (one-time)

Use a password manager or a CSPRNG. Example (64 hex chars):

```bash
openssl rand -hex 32
```

Store the value in your secret store / vault / password manager; set it in the environment at deploy time (see [API_KEY_FROM_ENV_OPERATOR_STEPS.md](API_KEY_FROM_ENV_OPERATOR_STEPS.md)).

### A.2 Config fragment (safe to commit)

```yaml
api:
  port: 8088
  host: "127.0.0.1"   # or your bind; see USAGE for precedence vs CLI / API_HOST
  require_api_key: true
  api_key_from_env: "AUDIT_API_KEY"
  # Do not set api_key here when using the environment (or leave it empty).
```

### A.3 Set the environment variable and start

## Linux / macOS:

```bash
export AUDIT_API_KEY='paste-generated-secret-here'
uv run python main.py --web --config /path/to/config.yaml
```

## Windows PowerShell (session):

```powershell
$env:AUDIT_API_KEY = "paste-generated-secret-here"
uv run python main.py --web --config C:\path\to\config.yaml
```

Use **systemd `Environment=`**, **Kubernetes Secret → env**, or **Docker `environment:`** in real deployments (patterns in [API_KEY_FROM_ENV_OPERATOR_STEPS.md](API_KEY_FROM_ENV_OPERATOR_STEPS.md)).

### A.4 Verify from the shell

```bash
# Must work without a key (200)
curl -sS http://127.0.0.1:8088/health

# Must fail without a key when require_api_key is true (401)
curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8088/status

# Must succeed with header (200)
curl -sS -H "X-API-Key: paste-generated-secret-here" http://127.0.0.1:8088/status
```

For **HTTPS** listeners, use `https://` and your port; you may need `-k` only for **lab** self-signed certs (not a production habit).

### A.5 Clients (browser, scripts, CI)

- **Browser:** After enabling the key, open the dashboard only from a context that can send the header (usually you terminate TLS and add auth at a **reverse proxy**, or use an internal tool). The in-app UI does not collect an API key field for every request; **production** pattern is often **proxy auth** + app key, or **loopback bind** + proxy.
- **Scripts:** Repo helper [poll_dashboard_scan.py](../../scripts/poll_dashboard_scan.py) supports **`DATA_BOAR_API_KEY`** / **`--api-key`** when `require_api_key` is on.
- **curl / automation:** Send **`X-API-Key`** or **`Authorization: Bearer`** on every request except **`GET /health`**.

---

## Part B — HTTPS for the dashboard

### B.0 Default posture (what `main.py --web` enforces)

You must either:

1. **Serve TLS directly** from the app: provide **`--https-cert-file`** and **`--https-key-file`** (PEM), or the same paths under **`api.https_cert_file`** / **`api.https_key_file`** in config, **or**
1. **Explicitly accept plaintext HTTP:** **`--allow-insecure-http`** or **`api.allow_insecure_http: true`** (stderr warning + dashboard banner; suitable only for controlled networks).

Otherwise **`main.py --web` exits with code 2**. The default **Docker image** `CMD` includes **`--allow-insecure-http`** so the container starts without mounted certs; **override `CMD`** and mount PEM files when you want TLS in containers.

### B.1 Recommended production pattern: TLS at the reverse proxy

For internet-facing or multi-tenant LAN deployments, prefer:

1. Bind the app to **loopback** (`127.0.0.1` or a container-only interface).
1. Terminate **TLS** on **nginx**, **Traefik**, **Caddy**, or a cloud load balancer.
1. Set **`X-Forwarded-Proto: https`** from the proxy so security headers (e.g. HSTS) behave correctly.

See [deploy/DEPLOY.md](../deploy/DEPLOY.md) ([pt-BR](../deploy/DEPLOY.pt_BR.md)) and root **SECURITY.md** for hardening context.

### B.2 Native HTTPS on Data Boar (PEM paths on the host)

**1.** Obtain **`fullchain.pem`** (or server cert + **chain**) and **`privkey.pem`** (private key). Restrict key file permissions (e.g. `chmod 600` on Unix).

**2.** Start:

```bash
uv run python main.py --web --config config.yaml \
  --https-cert-file /etc/data-boar/certs/fullchain.pem \
  --https-key-file /etc/data-boar/certs/privkey.pem
```

Or in YAML:

```yaml
api:
  https_cert_file: "/etc/data-boar/certs/fullchain.pem"
  https_key_file: "/etc/data-boar/certs/privkey.pem"
```

**3.** Open **`https://<host>:<port>/`**. Use **`GET /status`** or **`GET /health`** and check **`dashboard_transport`** in JSON (`mode`, `tls_active`, `summary`).

**4.** Optional evidence: **`python main.py --export-audit-trail -`** (without `--web`) includes **`dashboard_transport`** in the exported JSON for governance snapshots.

### B.3 Let’s Encrypt (public or DNS-validated hosts)

**When it fits:** A hostname on the public Internet (HTTP-01) or DNS you can automate (DNS-01). **Internal-only** lab names with no public DNS need **internal PKI**, **self-signed for lab only**, or **`mkcert`** on dev workstations — not public CA issuance.

## Typical flow (Linux, Certbot, HTTP-01):

1. Point DNS **A/AAAA** for `dashboard.example.com` to your server (or use a validated DNS plugin).
1. Run Certbot (standalone or webroot) to obtain certs; note paths (often `/etc/letsencrypt/live/<name>/fullchain.pem` and `privkey.pem`).
1. Point Data Boar **`--https-cert-file`** / **`--https-key-file`** at those PEM files **or** configure the **reverse proxy** to use them and keep the app on loopback HTTP (often simpler renewal).
1. **Renewal:** Use **certbot renew** on a timer; if the app reads PEM files directly, restart or reload the process after renewal so new certs are loaded (or use a proxy that hot-reloads).

**Operational note:** Let’s Encrypt is a **valid production option** when automation and hostname validation match your environment; enterprise CA or internal PKI are equally valid depending on policy.

### B.4 Self-signed certificates (alternative — lab / QA / UAT only)

**Not** the default recommendation for production user trust. Browsers will warn unless you install a trust anchor (see anti-patterns in [PLAN_DASHBOARD_HTTPS_BY_DEFAULT_AND_HTTP_EXPLICIT_RISK.md](../plans/completed/PLAN_DASHBOARD_HTTPS_BY_DEFAULT_AND_HTTP_EXPLICIT_RISK.md)).

## Quick openssl example (localhost-focused, 365 days):

```bash
openssl req -x509 -newkey rsa:2048 -sha256 -days 365 -nodes \
  -keyout server-key.pem -out server-cert.pem \
  -subj "/CN=localhost"
```

Use **`server-cert.pem`** as **`--https-cert-file`** and **`server-key.pem`** as **`--https-key-file`**. For **QA/UAT** behind a corporate name, prefer **internal PKI** or **DNS-validated** certs so clients trust the **chain** without ad-hoc root installs.

**Local dev ergonomics:** Tools like **`mkcert`** install a **local dev CA** on the developer machine only — useful to avoid noisy browser warnings while testing TLS behaviour; do **not** treat that as production trust distribution.

### B.5 Docker: TLS without plaintext `CMD`

Mount PEM files and override command, for example:

- Mount certs read-only into the container.
- Run **`main.py --web`** **without** **`--allow-insecure-http`**, passing **`--https-cert-file`** / **`--https-key-file`** (or equivalent config).

Exact Compose/Kubernetes patterns live next to your orchestration files; see [deploy/DEPLOY.md](../deploy/DEPLOY.md) and [deploy/kubernetes/README.md](../../deploy/kubernetes/README.md).

### B.6 Verify and monitor

| Check            | What to look for                                                                                                                                                                                               |
| -----            | ----------------                                                                                                                                                                                               |
| **Runtime**      | `GET /status` and `GET /health` → **`dashboard_transport`** reflects **`https`** vs explicit **http** opt-in.                                                                                                  |
| **Audit export** | `python main.py --export-audit-trail -` → JSON field **`dashboard_transport`** (export runs without `--web`; values reflect env/process unless you document a workflow that sets transport env before export). |
| **Auth**         | With **`require_api_key`**, **`/health`** = no key; **`/status`** = key required.                                                                                                                              |

---

## Rollout order (staging → production)

Follow [SECURE_BY_DEFAULT_BLOCKERS_AND_MIGRATION.md](SECURE_BY_DEFAULT_BLOCKERS_AND_MIGRATION.md): inventory API clients, enable **staging** with **API key + TLS** (or proxy TLS), update callers with headers and cert trust, then production with a **short** compatibility window only if needed (`--allow-insecure-http` / plaintext behind TLS-terminating proxy), then phase out insecure modes using **`dashboard_transport`** and logs.

---

## Related documentation

| Topic                               | English                                                                  | pt-BR (when applicable)                      |
| -----                               | -------                                                                  | ------------------------                     |
| Usage (CLI, API, tables)            | [USAGE.md](../USAGE.md)                                                  | [USAGE.pt_BR.md](../USAGE.pt_BR.md)          |
| Security policy + API key semantics | [SECURITY.md](../../SECURITY.md)                                         | [SECURITY.pt_BR.md](../../SECURITY.pt_BR.md) |
| Technician security tests summary   | [SECURITY.md](../SECURITY.md) (under docs/)                              | [SECURITY.pt_BR.md](../SECURITY.pt_BR.md)    |
| Deploy / proxy / hardening          | [DEPLOY.md](../deploy/DEPLOY.md)                                         | [DEPLOY.pt_BR.md](../deploy/DEPLOY.pt_BR.md) |
| API key env wiring (detailed)       | [API_KEY_FROM_ENV_OPERATOR_STEPS.md](API_KEY_FROM_ENV_OPERATOR_STEPS.md) | — (EN-only by policy)                        |
