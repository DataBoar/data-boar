# CLAUDE.md — Claude Code pointer

> **Claude Code auto-loads this file; it does not auto-load `AGENTS.md`.**
> All authoritative guidance lives in [`AGENTS.md`](AGENTS.md).
> Read `AGENTS.md` first on every session.

## Sub-product landmarks (pointers into `AGENTS.md`)

| Sub-product | Where to look in `AGENTS.md` |
| ----------- | ----------------------------- |
| **Maestro / lab orchestration** | Session taxonomy keywords `completao`, `homelab`; *LAB-OP batch inventory*; *Homelab access* bullets |
| **dashBOARd (`api/`)** | *Plans* bullet; `docs/USAGE.md`; `docs/TECH_GUIDE.md` |
| **Plans hierarchy** | *Plans* bullet (active under `docs/plans/`, done under `docs/plans/completed/`); `PLANS_TODO.md`; `PLANS_HUB.md` |
| **Licensing / Maestro matrix** | Session keyword `release-ritual`; `scripts/maestro/Handle-LicensingMatrix.ps1` |
| **Private docs (`docs/private/`)** | Bullet *`docs/private/` — agent access (non-negotiable)*; `.cursor/rules/agent-docs-private-read-access.mdc` |

## Agent role for Claude Code (READ-ONLY auditor)

Full contract: `.cursor/rules/agent-roles-executor-vs-auditor.mdc`.

**TL;DR:**

- **Cursor** = executor — writes, commits, pushes, opens PRs under full governance hooks.
- **Claude Code** = auditor — reads, reasons, audits. **Does not write to the repo directly.**
  Deliver findings via `gh issue create` / comments, or as prompts handed to Cursor for execution.

## Language

Default: concise Brazilian Portuguese (pt-BR) for narrative; English for code, paths, CLI flags,
and Conventional Commits prefixes. Full rule: `AGENTS.md` *Chat language* bullet and
`.cursor/rules/operator-chat-language-pt-br.mdc`.
