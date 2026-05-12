# ADR 0028 — Lab external connectivity evaluation playbook (tracked)

- **Status:** Accepted
- **Date (UTC):** 2026-04-18
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Context

LAN-only smoke (**LAB_SMOKE_MULTI_HOST**) and CI do not cover **third-party** HTTP APIs, intermittent **internet** reachability, or operator **firewall** mistakes. Contributors and field technicians need a **sanitized**, reproducible playbook without committing LAN IPs, passwords, or strategic notes.

## Decision

Maintain **public** runbooks under **`docs/ops/LAB_EXTERNAL_CONNECTIVITY_EVAL.md`** (+ pt-BR) with:

- Taxonomy (**E2E-OK**, **E2E-FAIL-EXPECTED**, **E2E-SKIP**).
- References to well-known **public** resources (links only — no embedded secrets).
- **Intentional failure** scenarios for troubleshooting UX validation.
- Small **automation**: **`scripts/lab-external-smoke.ps1`**, optional **`docker-compose.mongo.yml`** for local MongoDB.

Operator-only detail stays in **`docs/private/homelab/`** (not GitHub). ADR **0015** (PoC / API testing) remains complementary; this ADR scopes **external** connectivity docs specifically.

## Consequences

- More files to sync (EN + pt-BR) when behaviour or scripts change.
- Session keyword **`external-eval`** documents the scope in **`.cursor/rules/session-mode-keywords.mdc`**.

## References

- [LAB_EXTERNAL_CONNECTIVITY_EVAL.md](../ops/LAB_EXTERNAL_CONNECTIVITY_EVAL.md)
- [LAB_SMOKE_MULTI_HOST.md](../ops/LAB_SMOKE_MULTI_HOST.md)
- [ADR 0015](ADR-0015-poc-test-infrastructure-synthetic-corpus-and-api-testing.md)
