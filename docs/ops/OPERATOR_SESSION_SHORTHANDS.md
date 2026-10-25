# Operator session shorthands (taxonomy)

**pt-BR:** [OPERATOR_SESSION_SHORTHANDS.pt_BR.md](OPERATOR_SESSION_SHORTHANDS.pt_BR.md)

## Canonical source

The **English-only** keyword table lives in **`.cursor/rules/session-mode-keywords.mdc`**. **`AGENTS.md`** should list the **same** tokens in the **same order**; if they diverge, trust **`session-mode-keywords.mdc`** for scope and scripts.

**Script ↔ skill / keyword map (broader than keywords alone):** **[TOKEN_AWARE_SCRIPTS_HUB.md](TOKEN_AWARE_SCRIPTS_HUB.md)** ([pt-BR](TOKEN_AWARE_SCRIPTS_HUB.pt_BR.md)).

**Completão chat starters (`completao` + `tier:…`):** **[COMPLETAO_OPERATOR_PROMPT_LIBRARY.md](COMPLETAO_OPERATOR_PROMPT_LIBRARY.md)** ([pt-BR](COMPLETAO_OPERATOR_PROMPT_LIBRARY.pt_BR.md)) · **`scripts/completao-chat-starter.ps1`** (prints a minimal paste block; **`-Help`** lists tiers).

**Full public publish (semver, GitHub Release, Docker Hub):** **`release-ritual`** — situational **`release-publish-sequencing.mdc`** ( **`@release-publish-sequencing.mdc`** in fresh threads if no release doc globs are open); **`docker-local-smoke-cleanup.mdc`** stays **always-on**. See **[OPERATOR_AGENT_COLD_START_LADDER.md](OPERATOR_AGENT_COLD_START_LADDER.md)** § *Token → rule latch (`release-ritual`)*.

**Plans (`PLANS_TODO` / `PLAN_*`):** scope **`docs`** / **`feature`** / **`houseclean`** / **`backlog`** — situational **`plans-status-pl-sync.mdc`** + **`plans-archive-on-completion.mdc`**; ladder § *plans — status sync* + *plans — archive*.

**SonarQube MCP:** **`sonar-mcp`** — situational **`sonarqube_mcp_instructions.mdc`**; ladder § *`sonar-mcp`*.

**Study cadence:** **`study-check`** — situational **`study-cadence-reminders.mdc`**; ladder § *`study-check`*.

**Lab lessons (public archive):** **`lab-lessons`** — situational **`lab-lessons-learned-archive.mdc`**; hub **`LAB_LESSONS_LEARNED.md`** + dated **`lab_lessons_learned/`** per **ADR 0042**; ladder § *Token → rule latch (`lab-lessons`)*.

## LAB-OP SSH example host

Tracked examples and scripts use the SSH alias **`lab-op`** for the Linux lab server (Docker, reports). Configure **`Host lab-op`** in your dev PC’s **`~/.ssh/config`** so it resolves on your LAN (DNS or mDNS) and uses **ed25519** keys as pre-authorized on the host. Real machine names stay **only** under **`docs/private/homelab/`**. See **`docs/private.example/homelab/README.md`**.

## Related

- [LAB_EXTERNAL_CONNECTIVITY_EVAL.md](LAB_EXTERNAL_CONNECTIVITY_EVAL.md) ([pt-BR](LAB_EXTERNAL_CONNECTIVITY_EVAL.pt_BR.md)) — **`external-eval`**, `lab-external-smoke.ps1`, public API / read-only DB lab (no secrets in git)
- [LAB_OP_SHORTHANDS.md](LAB_OP_SHORTHANDS.md) ([pt-BR](LAB_OP_SHORTHANDS.pt_BR.md)) — `lab-op.ps1` actions
- **Homelab / SSH / LAN** — session **`homelab`** + **`.cursor/rules/homelab-ssh-via-terminal.mdc`** (situational) + [OPERATOR_AGENT_COLD_START_LADDER.md](OPERATOR_AGENT_COLD_START_LADDER.md) § *Token → rule latch (`homelab`)* ([pt-BR](OPERATOR_AGENT_COLD_START_LADDER.pt_BR.md))
- **Stacked private Git (`docs/private/.git`)** — **`private-stack-sync`** + situational **`docs-private-workspace-context.mdc`** ( **`agent-docs-private-read-access.mdc`** always-on) + [OPERATOR_AGENT_COLD_START_LADDER.md](OPERATOR_AGENT_COLD_START_LADDER.md) § *Token → rule latch (`private-stack-sync`)* ([pt-BR](OPERATOR_AGENT_COLD_START_LADDER.pt_BR.md))
- [PII_FRESH_CLONE_AUDIT.md](PII_FRESH_CLONE_AUDIT.md) ([pt-BR](PII_FRESH_CLONE_AUDIT.pt_BR.md)) — **`pii-fresh-audit`** + `pii-fresh-clone-audit.ps1`
- **Private legal / labour dossier** — **`legal-dossier-update`** (session token) + **`.cursor/rules/dossier-update-on-evidence.mdc`** + [OPERATOR_AGENT_COLD_START_LADDER.md](OPERATOR_AGENT_COLD_START_LADDER.md) § *Token → rule latch (legal dossier)* ([pt-BR](OPERATOR_AGENT_COLD_START_LADDER.pt_BR.md)); paths **`docs/private/legal_dossier/`**, **`docs/private/raw_pastes/`**
- **Plans drift + archive** — **`docs`** / **`feature`** / **`houseclean`** / **`backlog`** + situational **`plans-status-pl-sync.mdc`** / **`plans-archive-on-completion.mdc`** + [OPERATOR_AGENT_COLD_START_LADDER.md](OPERATOR_AGENT_COLD_START_LADDER.md) § *plans — status sync* / *plans — archive* ([pt-BR](OPERATOR_AGENT_COLD_START_LADDER.pt_BR.md))
- **SonarQube MCP** — **`sonar-mcp`** + situational **`sonarqube_mcp_instructions.mdc`** + ladder § *`sonar-mcp`* ([pt-BR](OPERATOR_AGENT_COLD_START_LADDER.pt_BR.md))
- **Study cadence** — **`study-check`** + situational **`study-cadence-reminders.mdc`** + ladder § *`study-check`* ([pt-BR](OPERATOR_AGENT_COLD_START_LADDER.pt_BR.md))
- [EVERYTHING_ES_PRIMARY_WINDOWS_DEV_LAB.md](EVERYTHING_ES_PRIMARY_WINDOWS_DEV_LAB.md) ([pt-BR](EVERYTHING_ES_PRIMARY_WINDOWS_DEV_LAB.pt_BR.md)) — **`es-find`** + `es-find.ps1` (Windows primary dev PC; not Linux **lab-op**); **token latch (fresh chat):** **`es-find`** or **`@everything-es-cli.mdc`** (**`everything-es-cli.mdc`** is situational; **`windows-pcloud-drive-search-discipline.mdc`** stays **always-on** for **`P:`**)
- [PRIMARY_WINDOWS_WORKSTATION_PROTECTION.md](PRIMARY_WINDOWS_WORKSTATION_PROTECTION.md) ([pt-BR](PRIMARY_WINDOWS_WORKSTATION_PROTECTION.pt_BR.md)) — no destructive repo ops on primary dev PC; `es-find` / temp PII audits are read-only or temp-only
- [TOKEN_AWARE_USAGE.md](../plans/TOKEN_AWARE_USAGE.md) — token-aware pacing
- [COMPLETAO_OPERATOR_PROMPT_LIBRARY.md](COMPLETAO_OPERATOR_PROMPT_LIBRARY.md) ([pt-BR](COMPLETAO_OPERATOR_PROMPT_LIBRARY.pt_BR.md)) — **`completao`** + **`tier:`** taxonomy; **`completao-chat-starter.ps1`**
