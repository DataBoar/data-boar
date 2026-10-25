# ADR 0033 — WebAuthn open Relying Party — JSON endpoints (Phase 1)

- **Date (UTC):** 2026-04-21
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Status

Accepted

### Status history

- 2026-04-21 — Accepted (Phase 1 WebAuthn RP on main behind `api.webauthn.enabled`, default false).
- 2026-08-13 — Narrowing note (append-only): Decision item 5 still exempts ongoing
  `/auth/webauthn/*` ceremonies from `api.require_api_key`. First-passkey
  **registration** (bootstrap / no existing credential) now requires a configured
  API key when the peer is not a trusted local operator path — see GitHub
  [#1553](https://github.com/DataBoar/data-boar/issues/1553) / PR
  [#1564](https://github.com/DataBoar/data-boar/pull/1564) and ADR-0082 Decision #6.
  Ongoing authentication and already-established trust are unchanged.

## Context

> **Note (from original Status):** — implemented on `main` behind **`api.webauthn.enabled`** (default **false**)

GitHub **#86** requires in-app identity before RBAC. Commercial passwordless SaaS (e.g. Bitwarden Passwordless.dev) is valuable as an **optional adapter** later, but the product should not depend on a single vendor for core ceremonies.

## Decision

1. Use the open-source **`webauthn`** Python library (Duo Labs) to implement the **Relying Party** in-process: registration and authentication **JSON** endpoints under **`/auth/webauthn/`**, storing credentials in SQLite (`webauthn_credentials`).

2. **No vendor SDK** in this slice: any FIDO2/WebAuthn authenticator (passkeys, security keys, common platform authenticators) can be used.

3. **Session state** for the operator is carried via a **signed cookie** (`itsdangerous`), not Starlette `SessionMiddleware`, to avoid import-order coupling and keep defaults unchanged when the feature is off.

4. **Challenge/state** for ceremonies is stored in an **in-memory** map keyed by an opaque `state` token returned with each `options` response. **Single-process** deployments only; document multi-worker limitation until a shared store exists.

5. **`api.require_api_key`** does **not** apply to `/auth/webauthn/*` so browsers can complete ceremonies without the global automation key; **`GET /health`** remains unauthenticated.

6. Enabling WebAuthn **without** resolving **`DATA_BOAR_WEBAUTHN_TOKEN_SECRET`** (or the env name in config) **fails startup** with a clear `RuntimeError`.

## Consequences

- **Positive:** Standard-aligned, testable, no lock-in; optional future adapters (Bitwarden-hosted, OIDC/Entra Phase 3) can sit beside this path.
- **Negative:** Per-route **RBAC** is **not** implemented; Phase **1b** adds an HTML session gate (after the first passkey) and CSRF on mutating dashboard forms — see `PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md`. Operators can use **`/{locale}/login`** or JSON endpoints.
- **Operational:** Operators must set **`origin`** / **`rp_id`** to match the browser URL (HTTPS recommended); `localhost` vs `127.0.0.1` matters for WebAuthn.

## Links

- Plan: `docs/plans/PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md` (Phases 1–3).
- Code: `api/webauthn_routes.py`, `core/webauthn_rp/`, `core/database.py` (`WebAuthnCredential`).
