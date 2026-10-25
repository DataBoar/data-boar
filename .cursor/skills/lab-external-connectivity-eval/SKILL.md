---
name: lab-external-connectivity-eval
description: Reproduce lab external API/DB eval using docs/ops/LAB_EXTERNAL_CONNECTIVITY_EVAL.md, scripts/lab-external-smoke.ps1, and private configs — token-aware.
---

# Lab external connectivity evaluation

## When to use

Operator wants **external** (internet or read-only public DB) connector checks alongside **LAB_SMOKE_MULTI_HOST**; or chat token **`external-eval`**.

## Steps

1. Read **`docs/ops/LAB_EXTERNAL_CONNECTIVITY_EVAL.md`** (EN) or **`.pt_BR.md`**.
2. **Do not** paste third-party credentials into tracked files or issues. Private copies: **`docs/private.example/homelab/config.external-eval.example.yaml`** → **`docs/private/`**.
3. Run **`.\scripts\lab-external-smoke.ps1`** from repo root (quick HTTPS probe). Optional **`-TcpHost`** / **`-TcpPort`** after firewall open toward hub.
4. Optional: **`deploy/lab-smoke-stack/docker-compose.mongo.yml`** for local MongoDB seeds.
5. Full Data Boar: **`uv run python main.py --config ...`** per **USAGE.md** — include at least one **E2E-OK** and one **E2E-FAIL-EXPECTED** target per session.

## Guardrails

- Respect rate limits and ToS of public APIs.
- **RNAcentral** and similar: credentials only from the provider help page; never commit.

## References

- **`docs/private/homelab/LAB_EXTERNAL_EVAL_MASTER.pt_BR.md`** (operator detail, if present).
- ADR **0028**.
