# Gordon (Docker AI) — how we use it without regressions

**Português (Brasil):** [GORDON_DOCKER_AI_USAGE.pt_BR.md](GORDON_DOCKER_AI_USAGE.pt_BR.md)

Purpose: use Docker’s “Gordon” assistant to accelerate Docker/Compose/Dockerfile work **without** leaking secrets, copying homelab details into tracked docs, or introducing regressions.

This is a workflow guide: Gordon’s output is treated as an **input**, not a policy mandate.

## What Gordon is best for (high ROI)

- **Troubleshooting** Docker Desktop / BuildKit / Compose errors with repeatable steps.
- **Dockerfile** caching and hardening suggestions (multi-stage, non-root).
- **Compose** overrides for dev/lab (profiles, volumes, healthchecks).
- **Pre-push / post-push** validation commands for Docker Hub tags (no UI).

## Red lines (never paste to Gordon)

- Tokens, PATs, passwords, private keys.
- Real homelab hostnames, RFC1918 subnets, inventory details (belongs in `docs/private/`).
- Anything you wouldn’t paste into a public issue.

## Token-aware prompting pattern

Ask **one** narrow question at a time. Prefer outputs that we can turn into repo-owned artifacts:

- “Give a minimal reproduction checklist.”
- “Give a small Dockerfile diff and explain cache impact.”
- “Give a compose override for `/data` + healthcheck.”
- “Give post-push validation commands.”

Avoid “everything about Docker” prompts.

## Converting Gordon output into repo work (the accepted shape)

1. Extract a **concrete artifact** we can own:
   - a script under `scripts/`,
   - a doc change under `docs/`,
   - or a regression test under `tests/`.
1. Prefer existing repo wrappers to keep transcripts short:
   - Quality gates: `.\scripts\check-all.ps1`, `.\scripts\lint-only.ps1`, `.\scripts\quick-test.ps1`
   - Docker hygiene/build: `.\scripts\docker-lab-build.ps1`, `.\scripts\docker-hub-pull.ps1`, `.\scripts\docker-prune-local.ps1`
1. Validate **no regression**:
   - docs-only: `.\scripts\lint-only.ps1`
   - otherwise: `.\scripts\check-all.ps1`

## Related

- [Docker setup (MCP, build, push)](../DOCKER_SETUP.md) ([pt-BR](../DOCKER_SETUP.pt_BR.md))
- [Branch and Docker cleanup](BRANCH_AND_DOCKER_CLEANUP.md) ([pt-BR](BRANCH_AND_DOCKER_CLEANUP.pt_BR.md))
- Cursor guardrail: `.cursor/rules/gordon-docker-ai-token-aware.mdc`
