# Secure-by-default blockers and safe migration (API key + transport)

**Português (Brasil):** [SECURE_BY_DEFAULT_BLOCKERS_AND_MIGRATION.pt_BR.md](SECURE_BY_DEFAULT_BLOCKERS_AND_MIGRATION.pt_BR.md)

## Purpose

Explain why some "secure-by-default" changes are currently treated as a **product decision with migration risk** (not as a simple patch), and how to get there without breaking real deployments.

## Short answer

The blocked path is usually **not technical impossibility**. It is mainly a **compatibility and rollout risk**:

- Forcing auth or transport defaults abruptly can break existing automations, probes, dashboards, and scripts.
- "Security default on" is good, but if introduced without migration controls it can cause outages and lock-outs.

## Main blocker map

| Theme                            | Why it can break app/deploy                                                                           | Typical regression                                    |
| ---                              | ---                                                                                                   | ---                                                   |
| **API key enforced by default**  | Existing operators/tools may call protected routes without `X-API-Key`                                | 401s in scripts, dashboards, scheduled jobs           |
| **`api_key_from_env` migration** | Misconfigured env var name/value, or YAML precedence confusion (`api_key` literal overrides env path) | App starts but auth behavior differs from expectation |
| **HTTP -> HTTPS default**        | Cert/key setup missing or invalid in environments that previously used plain HTTP                     | startup failure or inaccessible dashboard             |
| **Health/status assumptions**    | Some callers assume all routes are open like `/health`                                                | monitoring noise and false negatives                  |

## Why this appears in plans as "product decision"

In `PLANS_TODO` and Corporate-Entity-C follow-ups, "secure-by-default" for API auth and transport is tracked as a product-level change because it can be **breaking-by-default** for current users if switched instantly.

This is why the repo has incremental hardening first:

- clear warnings on risky runtime modes,
- env-based API key patterns documented,
- explicit migration steps,
- tests for both secure and compatibility modes.

## Workarounds that avoid breakage

1. **Dual-mode rollout**
   - Keep secure mode available now.
   - Keep compatibility mode only with explicit opt-in and warnings.
1. **Warn -> enforce transition**
   - Phase A: warning + telemetry/audit.
   - Phase B: secure default for new installs, compatibility flag for legacy.
   - Phase C: deprecate unsafe mode with clear timeline.
1. **Operator-safe key handling**
   - Use `api_key_from_env` pattern (see [API_KEY_FROM_ENV_OPERATOR_STEPS.md](API_KEY_FROM_ENV_OPERATOR_STEPS.md)).
   - Avoid literal key in tracked YAML.
1. **Status/health clarity**
   - Keep `/health` semantics explicit.
   - Document which routes require key and what failures mean.

## Practical migration checklist

1. Inventory clients calling API/dashboard (scripts, cron, CI, mobile checks, probes).
1. Enable secure path in staging first (API key + HTTPS where applicable).
1. Update clients with auth headers and cert expectations.
1. Roll to production with explicit fallback flag available (short window).
1. Monitor logs/status/audit for insecure mode usage and phase it out.

## Operator context (early deployments)

For **this product**, the maintainer-controlled install base is currently **effectively empty**: there are **no known external production API/dashboard clients** yet. That **reduces rollout risk** when turning on `require_api_key`, HTTPS-first listeners, and richer audit signals — but it does **not** remove the need for **documented migration paths**, **regression tests** (secure + compatibility modes), and **operator-safe secrets** (`api_key_from_env`, no literal keys in tracked YAML). The first real customer environment should not be the first time those paths are exercised.

## Related docs and plans

- [SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.md](SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.md) ([pt-BR](SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.pt_BR.md)) — concrete API key + TLS setup for technicians
- [API_KEY_FROM_ENV_OPERATOR_STEPS.md](API_KEY_FROM_ENV_OPERATOR_STEPS.md)
- [SECURITY.md](../SECURITY.md)
- [PLAN_DASHBOARD_HTTPS_BY_DEFAULT_AND_HTTP_EXPLICIT_RISK.md](../plans/completed/PLAN_DASHBOARD_HTTPS_BY_DEFAULT_AND_HTTP_EXPLICIT_RISK.md)
- [Corporate-Entity-C_ANALISE_2026-03-23_EVOLUTIVA.md](../plans/Corporate-Entity-C_ANALISE_2026-03-23_EVOLUTIVA.md)
