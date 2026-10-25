# Atalhos de sessão do operador (taxonomia)

**English:** [OPERATOR_SESSION_SHORTHANDS.md](OPERATOR_SESSION_SHORTHANDS.md)

## Fonte canônica

A tabela de palavras-chave **só em inglês** está em **`.cursor/rules/session-mode-keywords.mdc`**. O **`AGENTS.md`** deve listar os **mesmos** tokens na **mesma ordem**; se divergirem, use **`session-mode-keywords.mdc`** como referência de escopo e scripts.

**Mapa script ↔ skill / palavra-chave (mais amplo que só keywords):** **[TOKEN_AWARE_SCRIPTS_HUB.pt_BR.md](TOKEN_AWARE_SCRIPTS_HUB.pt_BR.md)** · [EN](TOKEN_AWARE_SCRIPTS_HUB.md).

**Arranques de chat para completão (`completao` + `tier:…`):** **[COMPLETAO_OPERATOR_PROMPT_LIBRARY.pt_BR.md](COMPLETAO_OPERATOR_PROMPT_LIBRARY.pt_BR.md)** ([EN](COMPLETAO_OPERATOR_PROMPT_LIBRARY.md)) · **`scripts/completao-chat-starter.ps1`** (imprime bloco mínimo para colar; **`-Help`** lista os *tiers*).

**Publicação pública completa (semver, GitHub Release, Docker Hub):** **`release-ritual`** — **`release-publish-sequencing.mdc`** **situacional** ( **`@release-publish-sequencing.mdc`** em chat novo se nenhum caminho coberto pelos **globs** de release estiver aberto no editor); **`docker-local-smoke-cleanup.mdc`** continua **sempre ligada**. Ver **[OPERATOR_AGENT_COLD_START_LADDER.pt_BR.md](OPERATOR_AGENT_COLD_START_LADDER.pt_BR.md)** § *Presilha token → regra (`release-ritual`)*.

**Planos (`PLANS_TODO` / `PLAN_*`):** âmbito **`docs`** / **`feature`** / **`houseclean`** / **`backlog`** — **`plans-status-pl-sync.mdc`** + **`plans-archive-on-completion.mdc`** **situacionais**; escada § *planos — sincronização de status* + *planos — arquivo*.

**SonarQube MCP:** **`sonar-mcp`** — **`sonarqube_mcp_instructions.mdc`** **situacional**; escada § *`sonar-mcp`*.

**Cadência de estudo:** **`study-check`** — **`study-cadence-reminders.mdc`** **situacional**; escada § *`study-check`*.

**Lições de lab (arquivo público):** **`lab-lessons`** — **`lab-lessons-learned-archive.mdc`** **situacional**; hub **`LAB_LESSONS_LEARNED.md`** + **`lab_lessons_learned/`** datados conforme **ADR 0042**; escada § *Presilha token → regra (`lab-lessons`)*.

## Exemplo de host SSH no LAB-OP

Exemplos versionados e scripts usam o alias SSH **`lab-op`** para o servidor Linux do lab (Docker, reports). Configure **`Host lab-op`** no **`~/.ssh/config`** do PC de desenvolvimento para resolver na LAN (DNS ou mDNS) e usar chaves **ed25519** já autorizadas no host. Nomes reais de máquina ficam **só** em **`docs/private/homelab/`**. Ver **`docs/private.example/homelab/README.md`**.

## Relacionado

- **Deriva + arquivo de planos** — **`docs`** / **`feature`** / **`houseclean`** / **`backlog`** + **`plans-status-pl-sync.mdc`** / **`plans-archive-on-completion.mdc`** **situacionais** + [OPERATOR_AGENT_COLD_START_LADDER.pt_BR.md](OPERATOR_AGENT_COLD_START_LADDER.pt_BR.md) § *planos — sincronização de status* / *planos — arquivo* ([EN](OPERATOR_AGENT_COLD_START_LADDER.md))
- **SonarQube MCP** — **`sonar-mcp`** + **`sonarqube_mcp_instructions.mdc`** **situacional** + escada § *`sonar-mcp`* ([EN](OPERATOR_AGENT_COLD_START_LADDER.md))
- **Cadência de estudo** — **`study-check`** + **`study-cadence-reminders.mdc`** **situacional** + escada § *`study-check`* ([EN](OPERATOR_AGENT_COLD_START_LADDER.md))
- [LAB_OP_SHORTHANDS.pt_BR.md](LAB_OP_SHORTHANDS.pt_BR.md) · [EN](LAB_OP_SHORTHANDS.md) — ações do `lab-op.ps1`
- **Homelab / SSH / LAN** — sessão **`homelab`** + **`.cursor/rules/homelab-ssh-via-terminal.mdc`** (situacional) + [OPERATOR_AGENT_COLD_START_LADDER.pt_BR.md](OPERATOR_AGENT_COLD_START_LADDER.pt_BR.md) § *Presilha token → regra (`homelab`)* ([EN](OPERATOR_AGENT_COLD_START_LADDER.md))
- **Git privado empilhado (`docs/private/.git`)** — **`private-stack-sync`** + situacional **`docs-private-workspace-context.mdc`** (**`agent-docs-private-read-access.mdc`** sempre ligada) + [OPERATOR_AGENT_COLD_START_LADDER.pt_BR.md](OPERATOR_AGENT_COLD_START_LADDER.pt_BR.md) § *Presilha token → regra (`private-stack-sync`)* ([EN](OPERATOR_AGENT_COLD_START_LADDER.md))
- [LAB_EXTERNAL_CONNECTIVITY_EVAL.pt_BR.md](LAB_EXTERNAL_CONNECTIVITY_EVAL.pt_BR.md) · [EN](LAB_EXTERNAL_CONNECTIVITY_EVAL.md) — **`external-eval`** + `lab-external-smoke.ps1` + playbook de APIs/datasets públicos (sem segredos no GitHub)
- [PII_FRESH_CLONE_AUDIT.pt_BR.md](PII_FRESH_CLONE_AUDIT.pt_BR.md) · [EN](PII_FRESH_CLONE_AUDIT.md) — **`pii-fresh-audit`** + `pii-fresh-clone-audit.ps1`
- **Dossiê jurídico / trabalhista privado** — **`legal-dossier-update`** (token de sessão) + **`.cursor/rules/dossier-update-on-evidence.mdc`** + [OPERATOR_AGENT_COLD_START_LADDER.pt_BR.md](OPERATOR_AGENT_COLD_START_LADDER.pt_BR.md) § *Presilha token → regra (dossiê jurídico)* ([EN](OPERATOR_AGENT_COLD_START_LADDER.md)); caminhos **`docs/private/legal_dossier/`**, **`docs/private/raw_pastes/`**
- [EVERYTHING_ES_PRIMARY_WINDOWS_DEV_LAB.pt_BR.md](EVERYTHING_ES_PRIMARY_WINDOWS_DEV_LAB.pt_BR.md) · [EN](EVERYTHING_ES_PRIMARY_WINDOWS_DEV_LAB.md) — **`es-find`** + `es-find.ps1` (Windows (PC principal de desenvolvimento); nao Linux **lab-op**); **presilha em chat novo:** **`es-find`** ou **`@everything-es-cli.mdc`** (**`everything-es-cli.mdc`** é situacional; **`windows-pcloud-drive-search-discipline.mdc`** continua **sempre ligada** para **`P:`**)
- [PRIMARY_WINDOWS_WORKSTATION_PROTECTION.pt_BR.md](PRIMARY_WINDOWS_WORKSTATION_PROTECTION.pt_BR.md) · [EN](PRIMARY_WINDOWS_WORKSTATION_PROTECTION.md) — sem operações destrutivas no repo no PC principal; `es-find` / auditorias PII em temp só leitura ou só em `%TEMP%`
- [TOKEN_AWARE_USAGE.md](../plans/TOKEN_AWARE_USAGE.md) — ritmo token-aware
- [COMPLETAO_OPERATOR_PROMPT_LIBRARY.pt_BR.md](COMPLETAO_OPERATOR_PROMPT_LIBRARY.pt_BR.md) ([EN](COMPLETAO_OPERATOR_PROMPT_LIBRARY.md)) — taxonomia **`completao`** + **`tier:`** · **`completao-chat-starter.ps1`**
