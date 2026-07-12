# Regras Cursor — fase 2 situacionalização (Tier A concluído)

**English:** [CURSOR_RULES_PHASE2_SITUATIONALIZATION.md](CURSOR_RULES_PHASE2_SITUATIONALIZATION.md)

## Objetivo

Este runbook registra **por que** o repositório Data Boar moveu um lote de regras Cursor **pesadas** de **`alwaysApply: true`** para **`alwaysApply: false`** com **`globs` estreitos**, **tokens de sessão** e **presilhas `@rule.mdc`** explícitas; **o que** foi **de propósito** **não** movido nesta fase 2; e **como repetir** o ritual com segurança num próximo recorte para o trabalho continuar **token-aware** e reversível.

Complementa (não substitui) **[`OPERATOR_AGENT_COLD_START_LADDER.pt_BR.md`](OPERATOR_AGENT_COLD_START_LADDER.pt_BR.md)** ([EN](OPERATOR_AGENT_COLD_START_LADDER.md)), **[`CURSOR_AGENT_POLICY_HUB.pt_BR.md`](CURSOR_AGENT_POLICY_HUB.pt_BR.md)** ([EN](CURSOR_AGENT_POLICY_HUB.md)) e **[`AGENTS.md`](../../AGENTS.md)**.

## Vocabulário (como usamos “Tier” aqui)

| Tier | Significado neste repositório (programa fase 2) |
| ---- | ----------------------------------------------- |
| **A** | **Feito:** regras que eram ruído sempre ligado e passaram a ser **situacionais** com **token → regra** documentado e hubs alinhados. |
| **B** | **Backlog — avaliar a seguir:** regras ainda sempre ligadas que *podem* tornar-se situacionais **depois** de análise custo/benefício (risco de orientação perdida). |
| **C** | **Meta / higiene:** inventários, testes, snapshots, trabalho só de consolidação em docs — não é por si só uma troca de regra. |

Vocabulário de **mantenedor** para **planejamento**; não é um “tier” de produto Cursor.

## Tier A — regras situacionalizadas na fase 2 (inventário)

Estas regras passam a carregar por **`globs`** e/ou **`@…`** / tokens de sessão em vez de todo chat:

| Arquivo de regra | Função (resumo) | Presilha típica |
| ---------------- | --------------- | --------------- |
| **`lab-completao-workflow.mdc`** | Completão no lab, SSH, evidência | **`completao`**, `scripts/lab-completao*`, `docs/ops/LAB_COMPLETAO*` |
| **`lab-lessons-learned-archive.mdc`** | Arquivo público de lições de lab (snapshots datados + hub + planos) | **`lab-lessons`**, `docs/ops/LAB_LESSONS*`, `docs/ops/lab_lessons_learned/**`, `docs/ops/SPRINT_*POSTMORTEM*` |
| **`dossier-update-on-evidence.mdc`** | Evidência jurídica / trabalhista privada | **`legal-dossier-update`**, `docs/private/legal_dossier/**`, `raw_pastes/**` |
| **`homelab-ssh-via-terminal.mdc`** | LAN / SSH / mesmo PC que o operador | **`homelab`**, `docs/ops/HOMELAB*`, `scripts/lab-op*`, etc. |
| **`docs-private-workspace-context.mdc`** | Git privado empilhado + cadência em `docs/private/` | **`private-stack-sync`**, caminhos do ritual privado |
| **`everything-es-cli.mdc`** | Voidtools Everything / `es-find.ps1` | **`es-find`**, `EVERYTHING_ES_*`, `scripts/es-find.ps1` |
| **`release-publish-sequencing.mdc`** | Ordem tag → Release → Docker Hub | **`release-ritual`**, `VERSIONING.md`, `docs/releases/**`, scripts do Hub |
| **`plans-status-pl-sync.mdc`** | Sincronizar cabeçalho / `PLANS_TODO` / tabelas do plano | **`docs`** / **`feature`** / **`houseclean`** / **`backlog`**, `docs/plans/**` |
| **`plans-archive-on-completion.mdc`** | **`git mv`** de `PLAN_*.md` concluído para `completed/` | Caminhos de planos, `plans_hub_sync`, `plans-stats`, **`@plans-archive-on-completion.mdc`** |
| **`sonarqube_mcp_instructions.mdc`** | Etiqueta SonarQube MCP | **`sonar-mcp`**, globs do home lab Sonar / properties |
| **`study-cadence-reminders.mdc`** | Cadência de estudo / lembretes opcionais | **`study-check`**, globs de portfólio / sprints / manual do operador |

### Pareamento sempre ligado (não situacionalizado na fase 2)

- **`docker-local-smoke-cleanup.mdc`** — continua **sempre ligada** para smoke, prune e higiene de disco em **alta frequência** ao lado de **`release-publish-sequencing.mdc`** situacional (ver [Por que manter docker-local-smoke-cleanup sempre ligada?](#por-que-manter-docker-local-smoke-cleanup-sempre-ligada)).
- **`windows-pcloud-drive-search-discipline.mdc`** — continua **sempre ligada** para disciplina em **`P:\`** / árvores enormes enquanto **`everything-es-cli.mdc`** é situacional.
- **`agent-docs-private-read-access.mdc`** — continua **sempre ligada** para o assistente **nunca auto-bloquear** em `docs/private/`.

Histórico canônico: **[`CHANGELOG.md`](../../CHANGELOG.md)** (*Unreleased* / entradas fase 2).

## Linha de base sempre ligada (exceções a não situacionalizar)

Tratar como **padrão** salvo revisão explícita de política:

- **`agent-docs-private-read-access.mdc`** — nunca auto-bloquear em `docs/private/`.
- **`docs-locale-pt-br-contract.mdc`** — saída em português do assistente permanece **pt-BR**, não pt-PT.
- **`docker-local-smoke-cleanup.mdc`** — curta; higiene transversal de smoke / prune / disco com Docker.
- **`windows-pcloud-drive-search-discipline.mdc`** — disciplina em **`P:\`** e árvores sem limite (pareada com **`everything-es-cli.mdc`** situacional).
- **`session-mode-keywords.mdc`** — tabela canônica de tokens em inglês para o repositório.

## Por que fizemos a fase 2 (objetivos)

1. **Orçamento de contexto:** Regras longas sempre ligadas competem pelo mesmo “espaço” no prompt que código e texto do usuário. Regras situacionais **só entram no contexto** quando arquivos ou tokens indicam necessidade real.
2. **Sinal vs ruído:** Completão no lab, dossiê jurídico, Sonar MCP e coreografia de release são **poderosas mas raras** face a um typo rápido num doc. Não devem dominar todo o fio.
3. **Controle explícito do operador:** Tokens de sessão em inglês (**`homelab`**, **`release-ritual`**, **`sonar-mcp`**, …) e **`@rule.mdc`** dão ganchos **reproduzíveis** para **chats novos** sem memória de transcript.
4. **Lotes reversíveis:** Cada onda é um **`git commit`** coerente; rollback é **`git revert`** ou `git show <parent>:caminho`.

## Trade-offs (prós e contras)

| Prós | Contras / riscos |
| ---- | ---------------- |
| Menos ruído de base; mais espaço para contexto da tarefa | Assistentes podem **omitir** regra situacional se o operador não abre arquivo correspondente e esquece **`@`** / token |
| Chats “tarefa simples” mais rápidos | **`globs`** podem ficar desatualizados quando arquivos mudam — requer auditoria ocasional |
| Mapa claro intenção → token → regra (escada de arranque) | Mais **superfície de documentação** para manter alinhada (este runbook, escada, hubs) |
| Raciocínio mais claro sobre “o que é vinculante agora” | **`globs`** excessivamente estreitos ou largos errados — **sobre**-anexar por arquivo aberto acidental |

Mitigação: manter **[`session-mode-keywords.mdc`](../../.cursor/rules/session-mode-keywords.mdc)** com **`alwaysApply: true`** como **tabela canônica de tokens**, e seguir o [Ritual reproduzível](#ritual-reproduzível-passos-concretos) para hubs e testes mudarem em conjunto.

## Por que as regras de locale não entraram na “viragem” da fase 2

**Objetivo da fase 2 aqui:** reduzir volume de **fluxos de domínio**, não tornar **conformidade de idioma** condicional.

- **`docs-locale-pt-br-contract.mdc`** permanece **`alwaysApply: true`** para **toda** resposta do assistente em português ser **pt-BR por omissão** (não pt-PT). É uma restrição **transversal**, não um fluxo “às vezes”.
- **`docs-pt-br-locale.mdc`** já é **`alwaysApply: false`** com **`globs`** focados no editor — é ajuda em **tempo de edição / lint**, não a mesma classe que completão no lab.
- **Testes reforçam a pilha:** **`tests/test_docs_pt_br_locale.py`** falha com marcadores de português europeu em **`*.pt_BR.md`**. Tornar o contrato situacional convidaria a **regressões** de locale e **retrabalho** (tokens + testes) com pouca poupança de contexto.

Em resumo: **locale = comportamento contextual forte** no sentido de **disciplina de prosa não negociável**, não “carregar isto só ao editar pt-BR”.

## Por que manter `docker-local-smoke-cleanup` sempre ligada?

1. **Regra curta, alta frequência:** Qualquer build Docker, smoke ou prune no PC de dev beneficia da mesma higiene (tags de imagem, número de contêineres, disco). O custo em tokens é **pequeno** face à orientação perdida e smoke lixo repetido.
2. **A sequência de release já é situacional:** **`release-publish-sequencing.mdc`** liga com **`release-ritual`** / **globs** de release. A regra **sempre ligada** cobre a camada transversal “limpar depois de si” que também vale **fora** de publicação completa (experiências locais, depuração de CI).
3. **Modo de falha:** Se fosse situacional, assistentes muitas vezes **saltam** prune/higiene de smoke em fios onde só `main.py` está aberto — precisamente quando disco e tags ainda importam.

## Tier B — situacionalizadas (issue #1154, 2026-07)

Inventário completo (EN): [Tier B situationalized](CURSOR_RULES_PHASE2_SITUATIONALIZATION.md#tier-b--situationalized-issue-1154-2026-07). **Meta:** reduzir ruído; rollback = `git revert`. **Always-on:** 36 → 18 (não meta mágica ~13).

## Tier B — backlog de avaliação (histórico pré-#1154)

| Regra (exemplos) | Por que poderia ser Tier B depois | Por que esperar / cuidado |
| ---------------- | ----------------------------------- | -------------------------- |
| **`operator-direct-execution.mdc`** | Longa; sobretudo quando o operador diz para fechar | Risco de pedir confirmações a mais em fluxos urgentes |
| **`operator-investigation-before-blocking.mdc`** | Narrativa de recuperação | Fácil sub-aplicar quando o usuário está bloqueado |
| **`git-pr-sync-before-advice.mdc`** | Conselho de merge | Perder `git fetch` primeiro mina confiança |
| **`execution-priority-and-pr-batching.mdc`** | PMO pesado | Ainda útil em muitos fios “o que segue” |
| **`check-all-gate.mdc`**, **`repo-scripts-wrapper-ritual.mdc`** | Disciplina de scripts | Barreiras centrais para higiene de CI |
| **`cursor-browser-social-sso-hygiene.mdc`** | Grande; só browser/MCP | Fluxos SSO ficam frágeis sem a regra |
| **`agent-autonomous-merge-and-lab-ops.mdc`** | Automação LAB-OP / merge | Alto impacto se faltar |
| **`cursor-markdown-preview-guardrail.mdc`** | UX do editor | Pequena mas evita confusão de preview |

**Fluxo Tier B:** Para cada regra: (1) Que fração de chats precisa dela? (2) Os **`globs`** expressam isso com **confiabilidade**? (3) Existe **token** ou **`@`** já? (4) Que teste ou linha da escada prova a presilha?

## Tier C — meta e higiene

- **Automação de inventário (ideia):** Teste ou script que afirma que a lista de regras **`alwaysApply: true`** coincide com um allowlist em docs (opcional; custo de manutenção).
- **Snapshots:** Zips privados em **`docs/private/ops/cursor-config-snapshots/`** (se usados) para frontmatter antes/depois.
- **Fase “B” do hub:** **[`CURSOR_AGENT_POLICY_HUB.pt_BR.md`](CURSOR_AGENT_POLICY_HUB.pt_BR.md)** é o mapa **clicável** — manter alinhado com **`AGENTS.md`** ao acrescentar presilha.

## Ritual reproduzível (passos concretos)

Use esta checklist **por ordem** ao situacionalizar a **próxima** regra ou lote. Está escrita para uma sessão futura gastar **menos tokens** a redescobrir passos e evitar pares EN/pt-BR **a meio**.

1. **Escolher o candidato** — Preferir regras **grandes** e **de domínio** que raramente se aplicam a edições genéricas. Confirmar que não pertence à [linha de base sempre ligada](#linha-de-base-sempre-ligada-exceções-a-não-situacionalizar).
2. **Ler a regra completa** — Notar secções que devem permanecer **vinculantes** quando anexada; identificar ligações a skills e runbooks.
3. **Desenhar `globs`** — Listar caminhos que preveem honestamente “este fio precisa desta regra” (ripgrep / layout). Evitar `**/*` (anula a situacionalização).
4. **Editar frontmatter** — **`alwaysApply: false`**; colar **`globs`**; acrescentar bloco **“When this rule attaches”** / contexto se faltar.
5. **Tokens de sessão** — Se um **chat novo** precisaria da regra sem esses arquivos abertos, acrescentar ou estender token em inglês em **[`session-mode-keywords.mdc`](../../.cursor/rules/session-mode-keywords.mdc)** (e na linha YAML **`description`** se existir). **Nunca** inventar grafias em português para tokens em docs versionados.
6. **Escada de arranque (EN + pt-BR)** — Linha no router de tarefas e subsecção **Presilha token → regra** em **[`OPERATOR_AGENT_COLD_START_LADDER.md`](OPERATOR_AGENT_COLD_START_LADDER.md)** e **[`.pt_BR.md`](OPERATOR_AGENT_COLD_START_LADDER.pt_BR.md)**. No espelho pt-BR usar vocabulário **do Brasil** (**arquivo**, não *ficheiro*).
7. **`AGENTS.md`** — Linha(s) no Quick index e linha de taxonomia de sessão se houver token **novo**.
8. **Hub de políticas (EN + pt-BR)** — Linhas correspondentes em **[`CURSOR_AGENT_POLICY_HUB.md`](CURSOR_AGENT_POLICY_HUB.md)** e **[`.pt_BR.md`](CURSOR_AGENT_POLICY_HUB.pt_BR.md)**.
9. **Atalhos de sessão (EN + pt-BR)** — Bullets em **[`OPERATOR_SESSION_SHORTHANDS.md`](OPERATOR_SESSION_SHORTHANDS.md)** e **[`.pt_BR.md`](OPERATOR_SESSION_SHORTHANDS.pt_BR.md)** quando o operador precisar de lembrete num salto.
10. **Outras ligações** — p.ex. **`VERSIONING.md`**, skills ou regras companheiras que mencionavam sempre ligado.
11. **`CHANGELOG.md`** — Bullet **`Unreleased`**: o que mudou, o que ficou sempre ligado, **rollback** (`git revert` / `git show <parent>:caminho`).
12. **Validar** — No mínimo: `uv run pytest tests/test_docs_pt_br_locale.py tests/test_markdown_lint.py tests/test_pii_guard.py -q` — para edições grandes de docs, correr **`.\scripts\check-all.ps1`** (ou **`./scripts/check-all.sh`**) antes do merge.
13. **Um commit** — Um commit coerente por lote para rollback trivial; depois push.

**Por que reproduzível?** A fase 2 tocou **muitos arquivos por regra** (regra + keywords + escada EN/pt-BR + hubs + atalhos + changelog). Uma checklist fixa evita cablagem **parcial** que confunde a próxima sessão **token-aware**.

## Relacionados

- **[`OPERATOR_AGENT_COLD_START_LADDER.pt_BR.md`](OPERATOR_AGENT_COLD_START_LADDER.pt_BR.md)** ([EN](OPERATOR_AGENT_COLD_START_LADDER.md)) — Router + presilhas.
- **[`CURSOR_AGENT_POLICY_HUB.pt_BR.md`](CURSOR_AGENT_POLICY_HUB.pt_BR.md)** ([EN](CURSOR_AGENT_POLICY_HUB.md)) — Tema → primeiro doc.
- **[`TOKEN_AWARE_SCRIPTS_HUB.pt_BR.md`](TOKEN_AWARE_SCRIPTS_HUB.pt_BR.md)** ([EN](TOKEN_AWARE_SCRIPTS_HUB.md)) — Scripts ↔ tokens ↔ skills.
- **[`AGENTS.md`](../../AGENTS.md)** — Contrato longo do assistente.
- **Skill:** [`.cursor/skills/token-aware-automation/SKILL.md`](../../.cursor/skills/token-aware-automation/SKILL.md).
