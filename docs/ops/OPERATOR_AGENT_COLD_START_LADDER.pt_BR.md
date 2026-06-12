# Escada de arranque operador + agente (token-aware, pouco contexto)

**English:** [OPERATOR_AGENT_COLD_START_LADDER.md](OPERATOR_AGENT_COLD_START_LADDER.md)

## Objetivo

Oferecer **um caminho ordenado** para um **chat novo** (sem memória do transcript) ainda assim chegar ao **hub certo primeiro**, sem reler o [`AGENTS.md`](../../AGENTS.md) inteiro. Esta página é só **navegação + regras mínimas** — o comportamento continua no **código**, **TECH_GUIDE** e runbooks ligados.

## Ordem de leitura (profundidade conforme a tarefa)

1. **Este arquivo** — router de tarefas + sete regras inegociáveis abaixo.
2. **[`AGENTS.md`](../../AGENTS.md)** — tabela Quick index (tema → primeiro doc); os bullets longos são o contrato.
3. **[`CURSOR_AGENT_POLICY_HUB.pt_BR.md`](CURSOR_AGENT_POLICY_HUB.pt_BR.md)** — os mesmos temas com caminhos **clicáveis** para `.cursor/rules`, `.cursor/skills` e `docs/ops/`.
4. **[`TOKEN_AWARE_SCRIPTS_HUB.pt_BR.md`](TOKEN_AWARE_SCRIPTS_HUB.pt_BR.md)** — que **`scripts/*.ps1`** ligam a keywords, skills e runbooks.
5. **Só lab / completão:** **[`LAB_COMPLETAO_FRESH_AGENT_BRIEF.pt_BR.md`](LAB_COMPLETAO_FRESH_AGENT_BRIEF.pt_BR.md)** → **[`LAB_COMPLETAO_RUNBOOK.pt_BR.md`](LAB_COMPLETAO_RUNBOOK.pt_BR.md)** → **[`LAB_OP_HOST_PERSONAS.pt_BR.md`](LAB_OP_HOST_PERSONAS.pt_BR.md)** (ENT / PRO / edge / ponte + knobs Ansible).
6. **Só stack privado:** **[`PRIVATE_STACK_SYNC_RITUAL.pt_BR.md`](PRIVATE_STACK_SYNC_RITUAL.pt_BR.md)** · **`scripts/private-git-sync.ps1`** (**`-Push`** quando os espelhos têm de alinhar) · **[ADR 0040](../adr/ADR-0040-assistant-private-stack-evidence-mirrors-default.md)** (EN).
7. **Onde vivem os docs (LAB-PB vs LAB-OP):** **[`OPERATOR_LAB_DOCUMENT_MAP.pt_BR.md`](OPERATOR_LAB_DOCUMENT_MAP.pt_BR.md)**.
8. **Tokens de sessão em inglês:** [`.cursor/rules/session-mode-keywords.mdc`](../../.cursor/rules/session-mode-keywords.mdc) — escrever os tokens **exatamente** (ex.: **`homelab`**, **`completao`**, **`lab-lessons`**, **`legal-dossier-update`**, **`private-stack-sync`**, **`es-find`**, **`release-ritual`**, **`sonar-mcp`**, **`study-check`**, **`short`** / **`token-aware`**).

## Router de tarefas (um salto)

| Se o operador quer… | Abrir primeiro (depois seguir links lá dentro) |
| ------------------- | ----------------------------------------------- |
| **Entregar código / corrigir CI** | **`TOKEN_AWARE_SCRIPTS_HUB`** §1 → **`check-all.ps1`**; bullets de merge/PR no **`AGENTS.md`** |
| **Semver público / Docker Hub / GitHub Release (publicação completa)** | Sessão **`release-ritual`** · **`.cursor/rules/release-publish-sequencing.mdc`** (**situacional** — **globs** ou **`@release-publish-sequencing.mdc`**) · **`docs/VERSIONING.md`** · **`docker-local-smoke-cleanup.mdc`** (**sempre ligada**) · § *Presilha token → regra (`release-ritual`)* abaixo |
| **Eixos de prioridade (H/U/A/P/G/S/M) — o que cada eixo mede** | **[`PLAN_TAXONOMY_AXES.md`](../plans/PLAN_TAXONOMY_AXES.md)** ([pt-BR](../plans/PLAN_TAXONOMY_AXES.pt_BR.md)) · [ADR-0055](../adr/ADR-0055-orthogonal-priority-axes-anti-collision-contract.md) (contrato anti-colisao) |
| **`PLANS_TODO` vs `PLANS_HUB` vs `PLAN_*.md` (modelo em três camadas)** | **`PLANS_DOCUMENTATION_HIERARCHY.md`** ([pt-BR](PLANS_DOCUMENTATION_HIERARCHY.pt_BR.md)) · **`plans-status-pl-sync.mdc`** ao editar tabelas de status de planos |
| **Deriva em `PLANS_TODO` / `PLAN_*`** (cabeçalhos, painel, tabelas no corpo) | **`docs`** / **`feature`** / **`houseclean`** / **`backlog`** (âmbito) · **`plans-status-pl-sync.mdc`** (**situacional** — **globs** de planos ou **`@plans-status-pl-sync.mdc`**) · § *Presilha token → regra (planos — sincronização de status)* abaixo |
| **Arquivar um `PLAN_*.md` concluído** | **`plans-archive-on-completion.mdc`** (**situacional** — caminhos de planos, **`plans_hub_sync`**, **`plans-stats`**, ou **`@plans-archive-on-completion.mdc`**) · **`docs-plans.mdc`** · § *Presilha token → regra (planos — arquivo)* abaixo |
| **SonarQube MCP no Cursor** | **`sonar-mcp`** · **`sonarqube_mcp_instructions.mdc`** (**situacional** — **globs** Sonar ou **`@sonarqube_mcp_instructions.mdc`**) · **`SONARQUBE_HOME_LAB.md`** · **`quality-sonarqube-codeql.mdc`** (barra de qualidade no repo) · § *Presilha token → regra (`sonar-mcp`)* abaixo |
| **Cadência de estudo / lembretes** | **`study-check`** · **`study-cadence-reminders.mdc`** (**situacional** — **globs** de portfólio/sprints/manual do operador ou **`@study-cadence-reminders.mdc`**) · § *Presilha token → regra (`study-check`)* abaixo |
| **Qual script / wrapper usar?** (evitar reinventar shell longo) | **`repo-scripts-wrapper-ritual.mdc`** · **`TOKEN_AWARE_SCRIPTS_HUB`** · **`check-all-gate.mdc`** · skill **`token-aware-automation`** |
| **LLM de chat web do fornecedor vs orquestração de lab validada / scripts *as-is*** | **`LLM_AGENT_EDITING_CAUTION.pt_BR.md`** ([EN](LLM_AGENT_EDITING_CAUTION.md)) — hype vs limites de sessão; índice completo de evidência em **`docs/private/ops/`** (gitignored) |
| **Docs / hubs / MAP** | skill **`doc-hubs-plans-sync`** · **`docs/README.md`** *Interno e referência* · par **`*.pt_BR.md`** |
| **Smoke de lab / completão** | **`COMPLETAO_OPERATOR_PROMPT_LIBRARY`** (**`completao`** + **`tier:…`**) · **`LAB_COMPLETAO_FRESH_AGENT_BRIEF`** · **`lab-completao-workflow.mdc`** · **`LAB_COMPLETAO_RUNBOOK`** · **`scripts/completao-chat-starter.ps1`** |
| **Arquivo de lições de lab (público)** | **`lab-lessons`** · **`lab-lessons-learned-archive.mdc`** · **`docs/ops/LAB_LESSONS_LEARNED.md`** · **`docs/ops/lab_lessons_learned/`** · [ADR 0042](../adr/ADR-0042-lab-lessons-learned-archive-contract.md) |
| **Ansible / Podman / personas** | **`LAB_OP_HOST_PERSONAS`** · **`ops/automation/ansible/README.md`** |
| **Inventário homelab / lote SSH** | Token de sessão **`homelab`** · **`homelab-ssh-via-terminal.mdc`** · **`lab-op-hosts.manifest.json`** em `docs/private/` (se existir) · **`LAB_OP_PRIVILEGED_COLLECTION.md`** · **`OPERATOR_LAB_DOCUMENT_MAP`** · § *Presilha token → regra (`homelab`)* abaixo |
| **Fecho do Git empilhado em `docs/private/`** | Sessão **`private-stack-sync`** · **`docs-private-workspace-context.mdc`** · **`PRIVATE_STACK_SYNC_RITUAL`** · **`private-git-sync.ps1`** · § *Presilha token → regra (`private-stack-sync`)* abaixo |
| **Evidência jurídica / trabalhista privada** (importação, atualizações tipo CAT/INSS, novo paste) | Token de sessão **`legal-dossier-update`** · **`dossier-update-on-evidence.mdc`** · **`legal_dossier/`** + **`raw_pastes/`** em `docs/private/` · § *Presilha token → regra (dossiê jurídico)* abaixo |
| **Recuperação / “descobre aí”** | **`operator-investigation-before-blocking.mdc`** · skill **`operator-recovery-investigation`** |
| **Busca de nome/caminho no Windows (Everything, árvores enormes, `P:\`)** | Sessão **`es-find`** · **`.cursor/rules/everything-es-cli.mdc`** (**situacional** — **globs** ou **`@everything-es-cli.mdc`**) · **`.cursor/rules/windows-pcloud-drive-search-discipline.mdc`** (**sempre ligada** para disciplina em **`P:`**) · **`EVERYTHING_ES_PRIMARY_WINDOWS_DEV_LAB.md`** · § *Presilha token → regra (`es-find`)* abaixo |
| **Gmail / webmail / redes / caixa ou anexo** (mesmo PC que **SSH**; sessão quente ou fria + **SSO Google** quando o site oferecer) | **`cursor-browser-social-sso-hygiene.mdc`** (*Contrato único* + *Gmail e webmail*) · **`operator-browser-warm-session.mdc`** · **`operator-direct-execution.mdc`** §5 — **tentar** MCP e clique **SSO** antes de negar; **só depois** pedir interação humana uma vez; PDFs → **`docs/private/`** + **`read_file`** |

### Presilha token → regra → wrapper (**`completao`**)

Use este **formato da primeira mensagem** para que um **`lab-completao-workflow.mdc`** **situacional** ainda “pegue” (via **globs** ou **`@`** explícito), sem recarregar a regra em todo chat irrelevante:

1. Linha 1: token em inglês **`completao`** (opcional na mesma mensagem: **`short`** / **`token-aware`** para narrativa curta).
2. Linha 2: **`tier:…`** exatamente como em **`COMPLETAO_OPERATOR_PROMPT_LIBRARY.md`**. Bloco para colar: **`.\scripts\completao-chat-starter.ps1 -Help`** ou correr com **`-Tier …`** para imprimir linhas copiáveis.
3. Se o fio **não** estiver a mexer em **`scripts/lab-completao*`** nem **`docs/ops/LAB_COMPLETAO*`**, **anexar** **`.cursor/rules/lab-completao-workflow.mdc`** com **`@`** para trazer a regra completa para o contexto.
3a. Quando o bloqueio for **`ssh` / LAN / `sudo -n` vs tmux`** e não só flags do orquestrador, **`read_file`** em **`.cursor/rules/homelab-ssh-via-terminal.mdc`** (ou **`@homelab-ssh-via-terminal.mdc`**) mesmo que **`lab-completao-workflow.mdc`** já esteja aberto.
4. **Automação por omissão (operador corre, assistente interpreta logs):** na raiz do repo **`.\scripts\lab-completao-orchestrate.ps1 -Privileged`** — depois **`read_file`** / resumir em **`docs/private/homelab/reports/`** conforme **`LAB_COMPLETAO_RUNBOOK.md`**. **Não** substituir o orquestrador por **`ssh`** ad hoc salvo se o operador optar explicitamente por isso.

### Presilha token → regra (**`lab-lessons`**)

Para **higiene de evidência** de QA/SRE de lab no **Git público** (snapshots datados + hub + ligação a planos), manter **`lab-lessons-learned-archive.mdc`** **situacional**, mas **obrigatório** quando fechas um bloco de lab:

1. Linha 1: token em inglês **`lab-lessons`** (opcional **`short`** / **`token-aware`**).
2. **`read_file`** em **`.cursor/rules/lab-lessons-learned-archive.mdc`** — usar **`@lab-lessons-learned-archive.mdc`** se o editor ainda não tiver anexado.
3. Seguir o **ADR 0042** + **`docs/ops/lab_lessons_learned/README.md`**: copiar o hub para **`lab_lessons_learned/LAB_LESSONS_LEARNED_YYYY_MM_DD.md`** antes de reescrever **`docs/ops/LAB_LESSONS_LEARNED.md`** para uma sessão nova; promover trabalho real para **`docs/plans/PLANS_TODO.md`** e correr **`python scripts/plans-stats.py --write`** quando linhas mudarem.
4. Emparelhar **`docs/private/homelab/COMPLETAO_SESSION_*.md`** (privado) com **números públicos** só — nunca colar segredos de LAN em arquivo rastreado.

### Presilha token → regra (**`homelab`**)

Manter **`homelab-ssh-via-terminal.mdc`** **situacional**, mas **vinculante** para semântica de **LAN / `ssh` / mesmo PC que o operador**:

1. Linha 1: token em inglês **`homelab`** (opcional **`short`** / **`token-aware`**).
2. **`read_file`** em **`.cursor/rules/homelab-ssh-via-terminal.mdc`** — usar **`@homelab-ssh-via-terminal.mdc`** se o editor ainda não anexou a regra (caminhos fora dos **globs** não carregam sozinhos).
3. Depois **`docs/ops/HOMELAB_VALIDATION.md`** (+ **`.pt_BR.md`** quando preciso) e **`docs/private/homelab/AGENT_LAB_ACCESS.md`** em privado quando existir — **nunca** colar hostnames reais ou identificadores de LAN em arquivos **versionados** ou PRs públicos.

### Presilha token → regra (**`legal-dossier-update`**)

Para **evidência jurídica / trabalhista** em **`docs/private/legal_dossier/`** ou **`docs/private/raw_pastes/`**, mantém a regra pesada **situacional**, mas **vinculante** quando precisas dela:

1. Linha 1: token em inglês **`legal-dossier-update`** (opcional **`short`** / **`token-aware`**).
2. **`read_file`** em **`.cursor/rules/dossier-update-on-evidence.mdc`** — usar **`@dossier-update-on-evidence.mdc`** se o editor ainda não anexou a regra (caminhos fora dos **globs** não carregam sozinhos).
3. Executar a **checklist ordenada** dentro dessa regra (índice → sumário executivo → risco se aplicável → **`OPERATOR_RETEACH.md`** → Git empilhado em **`docs/private/`** + **`private-git-sync.ps1`** quando a política pedir).
4. **Nunca** colocar nomes de partes, números de autos ou identificadores de LAN em **docs versionados**, issues ou PRs públicos.

### Presilha token → regra (**`private-stack-sync`** + cadência de leitura em **`docs/private/`**)

Para **Git privado empilhado** e higiene em **`docs/private/`**, mantém **`docs-private-workspace-context.mdc`** **situacional**, mas **vinculante** no ritual de fecho:

1. Linha 1: token em inglês **`private-stack-sync`** (opcional **`short`** / **`token-aware`**).
2. **`read_file`** em **`.cursor/rules/docs-private-workspace-context.mdc`** — usar **`@docs-private-workspace-context.mdc`** se os **globs** não carregaram a regra (**`agent-docs-private-read-access.mdc`** continua **sempre ligada** para **nunca auto-bloquear**).
3. **`read_file`** em **`docs/ops/PRIVATE_STACK_SYNC_RITUAL.md`** (+ **`.pt_BR.md`** se usares), depois **`.\scripts\private-git-sync.ps1`** (**`-Push`** quando os espelhos têm de alinhar) conforme **ADR 0040** / **`operator-evidence-backup-no-rhetorical-asks.mdc`**.
4. **Nunca** colar passphrases, keyfiles ou caminhos privados em arquivos **versionados** ou PRs públicos.

### Presilha token → regra (**`es-find`**)

Para semântica de **Voidtools Everything** / **`es-find.ps1`** no **PC dev Windows principal**, mantém **`everything-es-cli.mdc`** **situacional**, mas **vinculante** quando precisas do texto completo (fallbacks, **lab-op** = sem **`es`**, higiene):

1. Linha 1: token em inglês **`es-find`** (opcional **`short`** / **`token-aware`**).
2. **`read_file`** em **`.cursor/rules/everything-es-cli.mdc`** — usar **`@everything-es-cli.mdc`** se os **globs** não anexaram a regra (caminhos fora dos **globs** não carregam sozinhos).
3. Na raiz do repo correr **`.\scripts\es-find.ps1`** conforme essa regra (**`-MaxCount`** baixo salvo precisares de lista exaustiva). **`windows-pcloud-drive-search-discipline.mdc`** continua **sempre ligada** para **`P:`** / evitar **`Get-ChildItem`** **sem limite**.

### Presilha token → regra (**`release-ritual`**)

Para **tag → GitHub Release → Docker (smoke antes do push no Hub) → prune → descrição no Hub → `PUBLISHED_SYNC`**, mantém **`release-publish-sequencing.mdc`** **situacional**, mas **vinculante** quando estás a **publicar** ou a aconselhar publicação **completa**:

1. Linha 1: token em inglês **`release-ritual`** (opcional **`short`** / **`token-aware`**).
2. **`read_file`** em **`.cursor/rules/release-publish-sequencing.mdc`** — usar **`@release-publish-sequencing.mdc`** se os **globs** não anexaram a regra (ex.: só **`pyproject.toml`** aberto). **`docker-local-smoke-cleanup.mdc`** continua **sempre ligada** para **smoke / prune / disco** no PC de dev.
3. **`read_file`** em **`docs/VERSIONING.md`** (*Assistant / automação*) e seguir a **checklist ordenada** na regra — **não** colocar **`-beta`** no **`main`** antes de tag + Release + passos no Hub que o operador pediu estarem **feitos**, salvo fluxo explícito com **SHA** a taguear.

### Presilha token → regra (planos — **sincronização de status**)

Para **anti-deriva** em **`PLAN_*.md`** / **`PLANS_TODO.md`** (linha **Status**, tabelas de fase, narrativa de integração), mantém **`plans-status-pl-sync.mdc`** **situacional**, mas **vinculante** quando o trabalho de planos está no âmbito:

1. Abrir quase qualquer caminho em **`docs/plans/**`** costuma anexar a regra via **globs**. Num fio **novo** sobre deriva **sem** arquivo de plano aberto, usar em inglês **`docs`**, **`feature`**, **`houseclean`** ou **`backlog`** (âmbito) e **`read_file`** em **`.cursor/rules/plans-status-pl-sync.mdc`** — ou **`@plans-status-pl-sync.mdc`**.
2. Correr **`plans-stats.py --write`** / **`plans_hub_sync.py --write`** quando a regra pedir.

### Presilha token → regra (planos — **arquivo**)

Ao fazer **`git mv`** de um **`PLAN_*.md`** **concluído** para **`docs/plans/completed/`**, mantém **`plans-archive-on-completion.mdc`** **situacional**, mas **vinculante**:

1. **`read_file`** em **`.cursor/rules/plans-archive-on-completion.mdc`** — usar **`@plans-archive-on-completion.mdc`** se os **globs** não anexaram (ex.: só a discutir arquivo no chat).
2. Seguir **`.cursor/rules/docs-plans.mdc`** para sincronizar o hub e corrigir links; reconciliar **`plans-status-pl-sync`** se **`PLANS_TODO`** mudou.

### Presilha token → regra (**`sonar-mcp`**)

Para chamadas **SonarQube MCP** (toggles de análise, chaves de projeto, tokens **USER**), mantém **`sonarqube_mcp_instructions.mdc`** **situacional**, mas **vinculante**:

1. Linha 1: token em inglês **`sonar-mcp`** (opcional **`short`** / **`token-aware`**).
2. **`read_file`** em **`.cursor/rules/sonarqube_mcp_instructions.mdc`** — usar **`@sonarqube_mcp_instructions.mdc`** se os **globs** não anexaram.
3. **`read_file`** em **`docs/ops/SONARQUBE_HOME_LAB.md`** (+ **`.pt_BR.md`** quando preciso) para **alcance** e política de tokens. **`quality-sonarqube-codeql.mdc`** = testes de qualidade **no repo** — não substitui a etiqueta do MCP.

### Presilha token → regra (**`study-check`**)

Para recapitular **cadência de estudo** e **lembretes opcionais** em pontos de paragem, mantém **`study-cadence-reminders.mdc`** **situacional**:

1. A pedido: token em inglês **`study-check`** — depois **`read_file`** em **`.cursor/rules/study-cadence-reminders.mdc`** (ou **`@study-cadence-reminders.mdc`** se os **globs** falharem).
2. **Proativo** sem **`study-check`**: só quando esta regra **já** está no contexto (**globs** de portfólio / sprints / manual do operador ou **`@`** anterior). **Não** inventar parágrafos longos de estudo em fios não relacionados.

## Sete coisas inegociáveis (não “esquecer” em chat novo)

1. **`docs/private/`** existe no workspace → **`read_file` / `list_dir` é permitido**; **nunca** colar segredos ou identificadores de LAN em arquivos **versionados** ou PRs públicos (**`PRIVATE_OPERATOR_NOTES.md`**). Cadência de leitura + **`.cursorignore`**: situacional **`docs-private-workspace-context.mdc`** — usar **`private-stack-sync`** ou **`@docs-private-workspace-context.mdc`** em chats **novos**; **nunca auto-bloquear** continua em **`agent-docs-private-read-access.mdc`** (**sempre ligada**).
2. **Clone canônico no PC dev Windows principal** — **sem** **`clean-slate`**, **`git filter-repo`** ou **`git reset --hard`** de rotina na árvore do produto (**`PRIMARY_WINDOWS_WORKSTATION_PROTECTION.md`**).
3. **`completao`** — quando couber no âmbito, usar **`lab-completao-orchestrate.ps1 -Privileged`** na raiz do repo; o **manifest** define **`completaoEngineMode` / `completaoSkipEngineImport`** para hosts só contêiner (**`LAB_COMPLETAO_RUNBOOK`**).
4. **Conselho sobre merge / PR / “o que segue”** — **`git fetch`** primeiro (**`git-pr-sync-before-advice.mdc`**).
5. **Espelhos privados** — quando o sync é óbvio, correr **`private-git-sync.ps1 -Push`** e **reportar** erros concretos de SSH/mount (**ADR 0040**, **`operator-evidence-backup-no-rhetorical-asks.mdc`**).
6. **Prosa em português = pt-BR por padrão** — **`*.pt_BR.md`**, Markdown em PT em **`docs/private/`** e parágrafos que o assistente escreve **não** podem ir para **pt-PT** “sem querer.” Exceções só conforme **`.cursor/rules/docs-locale-pt-br-contract.mdc`**. Depois de edições grandes em pt-BR, rodar **`uv run pytest tests/test_docs_pt_br_locale.py -v`**.
7. **Alcance homelab / LAB-OP a partir do terminal integrado** — no **PC de dev**, o terminal integrado do Cursor é a **mesma máquina e LAN** que o teu shell habitual para **`ssh`**, **`scp`**, **`curl` HTTP no lab**, etc. (**`homelab-ssh-via-terminal.mdc`**). Antes de dizer **“sem acesso remoto”** ou **“não consigo chegar nos hosts do lab”**, usar **`read_file`** em **`docs/private/homelab/AGENT_LAB_ACCESS.md`** (se existir) e seguir **aliases `Host` do SSH / caminhos do manifest** nos docs privados — **não** inventar hostnames reais, IPs nem caminhos de `$HOME` em arquivos **versionados**. Um prompt de notebook tipo **`usuario@LAB-NODE-02-…` no chat** **não** prova que o assistente **não** possa usar **`ssh`** para hosts do manifest a partir deste workspace.

## Produto vs operador (por preocupação)

Perguntas de compliance e capacidade para **compradores / DPO / CISO** começam no **[`MAP.pt_BR.md`](../MAP.pt_BR.md)** ([EN](../MAP.md)), não em `docs/plans/` (regra de tier externo: **ADR 0004**).

## Relacionados (mapa mental, não duplicar)

| Artefato | Função |
| -------- | ------ |
| **`AGENTS.md`** | Contrato longo canônico do assistente |
| **`CURSOR_AGENT_POLICY_HUB`** | Fase B — mesmo índice, clicável |
| **`CURSOR_RULES_PHASE2_SITUATIONALIZATION`** | Fase 2 — narrativa Tier A/B/C + ritual reproduzível |
| **`TOKEN_AWARE_SCRIPTS_HUB`** | Mapa script ↔ keyword ↔ skill |
| **`OPERATOR_LAB_DOCUMENT_MAP`** | Índice LAB-PB vs LAB-OP |
| **`LAB_OP_HOST_PERSONAS`** | Intenção LAB-NODE-01 / LAB-NODE-02 / pi / LAB-NODE-03 vs automação |
| **`COMPLETAO_OPERATOR_PROMPT_LIBRARY.md`** | Taxonomia de chat **`completao`** + **`tier:`** + **`completao-chat-starter.ps1`** |

Ao acrescentar um **tema recorrente novo**, incluir **uma linha** no Quick index do **`AGENTS.md`** e no **`CURSOR_AGENT_POLICY_HUB`** na **mesma alteração**.
