# Plan: Dashboard trusted-proxy TLS posture (#1515)

**Status:** 🟢 Implementation complete (pending merge)
**Date:** 2026-08-10
**Authors:** Fabio Leitao
**Priority:** H1 · P1 · security
**Issue:** [#1515](https://github.com/DataBoar/data-boar/issues/1515)
**Related:** [PLAN_DASHBOARD_HTTPS_BY_DEFAULT_AND_HTTP_EXPLICIT_RISK.md](completed/PLAN_DASHBOARD_HTTPS_BY_DEFAULT_AND_HTTP_EXPLICIT_RISK.md) (process-level transport); `core/forwarded_headers.py`

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)

## Purpose

Recognize **client-facing HTTPS terminated at an explicitly trusted reverse proxy** so the dashboard does not show a false-positive plaintext-HTTP risk banner, while keeping the **process-level** truth that the Uvicorn upstream listener is still HTTP.

## Problem

`get_dashboard_transport_snapshot()` sets `show_insecure_banner` whenever the app was started with explicit HTTP opt-in. Production topology is often:

```text
Client ── HTTPS ──► Caddy/nginx/LB ── HTTP loopback ──► Data Boar
```

`forwarded_proto_posture()` already trusts `X-Forwarded-Proto` only when the direct peer matches `api.trusted_proxy_cidrs`, and `_is_secure_request()` uses that for HSTS — but templates still read the process snapshot alone.

## Security boundary

- Never treat forwarded headers as authoritative unless the **direct client IP** matches `api.trusted_proxy_cidrs`.
- Configuring CIDRs alone must **not** suppress the banner; only a per-request match **and** trusted `X-Forwarded-Proto: https` may suppress the plaintext risk banner.
- Forged `X-Forwarded-Proto: https` from an untrusted peer must keep the banner.

## Required behavior

| Layer | Truth |
| ----- | ----- |
| Process (`dashboard_transport`) | `mode: http`, `tls_active: false` when upstream is plaintext |
| Request (`effective_external_transport`) | `scheme: https`, `tls_termination: trusted_proxy` when edge TLS is validated |
| UI | Suppress **only** the plaintext-risk banner under trusted edge TLS; optional informative copy that TLS ended at the proxy |

Helper shape (request-scoped; do **not** make `get_dashboard_transport_snapshot()` request-dependent):

```python
effective = effective_dashboard_transport(request, config)
# show_insecure_banner = upstream.show_insecure_banner and not trusted_edge_tls
```

## Phases

| # | Item | Status |
| - | ---- | ------ |
| 1 | Plan + PLANS_TODO + `plans_hub_sync.py --write` | ✅ |
| 2 | `effective_dashboard_transport()` + wire templates / `/status` / `/health` | ✅ |
| 3 | Regression tests (#1515 list; IPv4 + IPv6 when CIDR helper allows) | ✅ |
| 4 | Locales (en + pt-BR) informative copy; CSS for info banner | ✅ |
| 5 | Docs: HOWTO + DEPLOY + SECURITY (+ pt-BR) — `trusted_proxy_cidrs` + `X-Forwarded-Proto` | ✅ |
| 6 | Startup log nuance when CIDRs configured (no claim of external HTTPS at boot) | ✅ |

## Acceptance criteria

Mirror [#1515](https://github.com/DataBoar/data-boar/issues/1515): direct HTTP / missing or `http` forwarded proto / untrusted forge keep banner; trusted peer + `https` suppresses plaintext banner only; native HTTPS unchanged; process snapshot stays honest; governance banners not silenced; no raw proxy chains in logs.

## Non-goals

- Auto-trust arbitrary reverse proxies
- Global trust of forwarded headers
- Claiming native app TLS when termination is at the proxy
- Removing `--allow-insecure-http` opt-in for the HTTP listener
- CA-bundle / auth / OAuth / WebAuthn / paid RBAC redesign

## Documentation targets

- `docs/ops/SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.md` (+ `.pt_BR.md`)
- `docs/deploy/DEPLOY.md` (+ `.pt_BR.md`)
- `SECURITY.md` (+ `.pt_BR.md`)
- `api/locales/en.json` / `pt-BR.json`
