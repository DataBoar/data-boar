# Plan: Web hardening and security improvements

Goal: Harden the web surface of the LGPD crawler (CSP, headers, and deploy guidance) without regressing current behaviour, keeping docs and man pages in sync and tests green.

## Goals

- Improve **web security** for the dashboard and API:
- Tighten the **Content Security Policy (CSP)** to reduce XSS and similar risks.
- Keep the UI working by using a **partial lockdown** approach (minimise `unsafe-inline`, use a narrowly-scoped inline script for now, and document a stronger CSP option).
- Keep capabilities and behaviour stable (no regressions, no broken dashboard), and ensure **all tests still pass with `-W error`**.
- Add **deployment hardening guidance** for Docker and Kubernetes (securityContext, network policies, PodDisruptionBudget, etc.) as **optional** docs, without forcing breaking changes.
- Keep **man pages, help page, and docs** in sync with the new security posture.

## Current state (high-level)

- CSP is already set in `api/routes.py` in `security_headers_middleware`, but allows `'unsafe-inline'` for scripts and styles:
- `script-src 'self' 'unsafe-inline' <https://cdn.jsdelivr.ne>t` (for Chart.js and inline dashboard scripts).
- `style-src 'self' 'unsafe-inline'`.
- Dashboard template `api/templates/dashboard.html` contains **inline script** for:
- Rendering the Chart.js line chart.
- Handling the **Start scan** button (via `fetch('/scan', ...)`).
- API already enforces optional **API key** and has good security headers and caching behaviour.
- Deploy docs describe Docker and K8s usage, but hardening (securityContext, network policies, etc.) is mostly textual and not deeply structured.

## High-level design

1. **CSP partial lockdown** (no immediate breakage):
   - Keep a single, small inline script block for the dashboard and help pages, but:
     - Reduce generic `'unsafe-inline'` where possible.
     - Split out static JS into a separate file when feasible (e.g. chart logic, poll logic) and load it from `/static/`.
   - Provide a **documented stronger CSP** profile (without `'unsafe-inline'`) as a **recommended setting behind a config/env toggle** or reverse-proxy header.
1. **Security headers refinement**:
   - Review and, if needed, tighten `Content-Security-Policy`, `Referrer-Policy`, and `Permissions-Policy` in `api/routes.py`.
   - Add a short section in SECURITY docs that explains each header and how to override/extend it at the reverse proxy.
1. **Kubernetes and Docker hardening guidance**:
   - Add/extend sections in `docs/deploy/DEPLOY.md` for:
     - Docker resource limits (CPU/memory), healthchecks (CLI vs API), and safe defaults.
     - Kubernetes examples (Deployment/StatefulSet) with **securityContext**, **read-only root filesystem**, dropping capabilities where possible, and a **NetworkPolicy** restricting access.
     - **PodDisruptionBudget** and recommendations for running more than one replica if scanning large environments.
   - Keep these as **optional, example manifests** (e.g. under `deploy/kubernetes/`) to avoid breaking existing deployments.
1. **Docs and man pages**:
   - Update README (EN/PT-BR), USAGE (EN/PT-BR), man(1)/(5), and `help.html` to:
     - Mention CSP and security headers.
     - Reference the new deployment hardening sections.
     - Explain how to flip between the current and stricter CSP profiles.

## Detailed plan by area

### 1. CSP and security headers (`api/routes.py`, `dashboard.html`, `help.html`)

1.1 **Refine `security_headers_middleware` in `api/routes.py`**

- Adjust CSP to a partial lockdown profile:
- For scripts:
    - Replace generic `'unsafe-inline'` with either:
      - A specific mention of `/static/dashboard.js` (served from `self`), or
      - Keep `'unsafe-inline'` but **document** that a stricter variant without it is available.
- For styles:
    - Consider leaving `'unsafe-inline'` for now but document that a stricter variant (no inline styles) is supported if the user removes inline style blocks from templates.
- Introduce (in code or docs) a **second CSP profile**:
- `CSP_MODE=strict` env/config toggle that removes `'unsafe-inline'` from `script-src` and `style-src`.
- When strict mode is enabled, require that all inline scripts be removed or replaced with external JS.
- Ensure **test environment** uses the default, backward-compatible CSP profile.

1.2 **Move most JS logic to static file(s)**

- Create `api/static/dashboard.js` to contain the bulk of the dashboard JS currently inline in `dashboard.html`:
- Chart.js initialisation (using `window.chartData` passed from the template).
- Polling `/status` for scan progress.
- Start-scan click handler (`fetch('/scan', ...)` with `{ tenant, technician }`).
- Update `api/templates/dashboard.html` to:
- Define small, data-only globals (e.g. `window.chartData = ...`) in the template or embed as `data-*` attributes in DOM nodes.
- Load `/static/dashboard.js` via a `<script src=\"/static/dashboard.js\" defer></script>` tag in the `scripts` block.
- Ensure `'self'` is sufficient for `script-src` in default CSP for this file; Chart.js will still be loaded from jsDelivr (already allowed).

1.3 **Help page JS (if any)**

- Confirm whether `api/templates/help.html` has inline scripts.
- If so, apply the same pattern: move non-trivial logic into `/static/help.js` and load it as an external script.
- If not, no change needed beyond CSP.

1.4 **Tests for CSP behaviour (high-level)**

- Optionally add a small test (e.g. in a new `tests/test_csp_headers.py`) that:
- Spins up the app and inspects `GET /` or `GET /help` headers for the expected CSP string in default mode.
- Asserts no syntax regressions.

### 2. SecurityContext, network policies, and PDB guidance (Docker/K8s) – docs only

2.1 **Docker hardening in `docs/deploy/DEPLOY.md`**

- Add a “Security and resource tuning” subsection that:
- Recommends running the container as a **non-root user** (the Dockerfile already creates `appuser`; show `--user` example for `docker run` if helpful).
- Recommends CPU/memory limits (for Compose: `deploy.resources.limits`, for plain Docker: `--cpus`, `--memory`).
- Reiterates usage of API key, rate limiting, and CSP as part of **devsecops** practice.

2.2 **Kubernetes hardening examples (mixed environments)**

- Under `deploy/kubernetes/` (or in `docs/deploy/DEPLOY.md` as inline YAML), add example snippets:
- **Deployment** with `securityContext`:
    - `runAsNonRoot: true`, `runAsUser: 1000` (align with `appuser`), `readOnlyRootFilesystem: true` (if writable paths are correctly mounted).
    - Drop unnecessary Linux capabilities.
- **NetworkPolicy** that:
    - Allows ingress only from specific namespaces or pods (e.g. from ingress-controller namespace or a monitoring namespace).
    - Optionally restricts egress to allowed DB/FS endpoints.
- **PodDisruptionBudget** (PDB):
    - Optional example ensuring at least one replica remains available during node maintenance when running multiple replicas.
- **Resource requests/limits**: Document recommended baseline (I/O-bound app, moderate CPU, enough memory for ML/DL).
- Keep these examples **commented out or separate** so existing users are not forced into a specific K8s deployment pattern.

2.3 **SECURITY.md updates**

- Add a short section referencing:
- CSP and security headers as in `api/routes.py`.
- The Docker/K8s hardening examples in `docs/deploy/DEPLOY.md`.
- Encouragement to run the app behind a reverse proxy with TLS, proper auth, and WAF when exposed externally.

### 3. Docs, man pages, and help page

3.1 **USAGE docs (EN/PT-BR)**

- Add a subsection in **Configuration → API / Security** that:
- Explains the CSP defaults (what is allowed, why Chart.js CDN is included).
- Describes how to enable the stricter CSP profile (if we introduce an env toggle), and warns that inline scripts must be refactored.

3.2 **Man pages**

- `docs/lgpd_crawler.1`:
- Under DESCRIPTION or a new “Security” subsection, mention:
    - Security headers (CSP, HSTS, Referrer-Policy, Permissions-Policy).
    - That CSP may be tightened via env/config and/or reverse proxy.
    - Pointer to `SECURITY.md` and `docs/deploy/DEPLOY.md`.
- `docs/lgpd_crawler.5`:
- If we add a CSP/headers toggle in config, document it alongside `api` and `rate_limit` sections.

3.3 **Help page (`api/templates/help.html`)**

- Add a brief bullet in the Help page that:
- Mentions security headers and CSP.
- Points users to `SECURITY.md` and `docs/deploy/DEPLOY.md` for hardening guidance.

### 4. Non-regression and testing strategy

- Ensure that default CSP and header changes do **not** break:
- Dashboard chart rendering.
- Start scan button functionality (`POST /scan` from GUI, including tenant/technician fields).
- Help and About pages.
- Tests to run and/or add:
- Existing suite: `uv run pytest tests/ -v -W error`.
- New small tests for CSP header presence and syntax.
- Optional TestClient-based check that `POST /scan` from the API still behaves as expected.

## Todos and status

1. Refine CSP and security headers in `api/routes.py` (partial lockdown profile, optional stricter mode) and move dashboard JS into `/static/dashboard.js` to reduce inline code. **Status:** ✅ Done.
1. Confirm and, if needed, adjust Help page JS so it works under the refined CSP. **Status:** ✅ Done (no inline JS present; Help works with updated CSP).
1. Extend `docs/deploy/DEPLOY.md` with Docker and Kubernetes hardening guidance (securityContext, NetworkPolicy, PDB, resource tuning) as **optional** examples. **Status:** ✅ Done.
1. Update `SECURITY.md` with a short section covering CSP, security headers, and the new hardening examples. **Status:** ✅ Done.
1. Update docs (`docs/USAGE.md`, `docs/USAGE.pt_BR.md`) to mention CSP behaviour and how to enable stricter profiles, and update man(1)/(5) plus `help.html` to stay in sync. **Status:** ✅ Done.
1. Add/adjust tests (e.g. `tests/test_rate_limit_api.py`-style) to assert CSP header presence and default semantics, and re-run the full test suite (`uv run pytest tests/ -v -W error`). **Status:** ✅ Done (see `tests/test_csp_headers.py`; full suite passes).
