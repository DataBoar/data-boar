# Laboratório: "completão" vs CI / pytest

**English:** [LAB_COMPLETAO_RUNBOOK.md](LAB_COMPLETAO_RUNBOOK.md)

**Objetivo:** Definir o que é **completão** neste projeto: **rodar o produto** (CLI, API, web) nos **hosts do lab**, via **SSH**, com **registro** de resultados — não é a mesma coisa que só `**pytest`** ou `**.\scripts\check-all.ps1`** no PC de desenvolvimento.

**Enquadramento (orquestração vs testes unitários):** O completão **não** substitui **`pytest`** nem o CI no GitHub — é uma camada de **orquestração e validação do ambiente de laboratório** para resultados **repetíveis e documentados** em **hosts reais**. O PC Windows de desenvolvimento corre orquestradores **PowerShell** contra destinos **Linux** por **SSH** (mais verificações HTTP opcionais a partir da LAN), exercitando **conectividade, permissões, encadeamento de runtime e caminhos de smoke** que testes unitários **sozinhos** não cobrem de ponta a ponta. Regras do Cursor (`.mdc`), **bibliotecas de prompt**, **briefs para agente novo** e **`lab_result.json`** existem para o assistente **carregar contratos**, preferir os scripts certos, classificar falhas (*timeout* vs *auth* vs *parser* — ver **`COMPLETAO_OPERATOR_PROMPT_LIBRARY.pt_BR.md`**) e deixar **evidência** em **`docs/private/homelab/reports/`** com menos ruído — **sem** sugerir revisão humana zero para mudanças de laboratório de alto impacto.

**Chat novo no Cursor / zero contexto:** Use **[LAB_COMPLETAO_FRESH_AGENT_BRIEF.pt_BR.md](LAB_COMPLETAO_FRESH_AGENT_BRIEF.pt_BR.md)** — prompts copy-paste (**só smoke** vs **estendido**), checklists opcionais, blocos de follow-up **B–E**, pré-condições e escopo honesto (o que os scripts fazem vs o que depende de config do operador).

## Contrato assistente + operador (Cursor)

- **Acesso:** O assistente executa `**ssh`**, scripts e `**curl`** no terminal integrado do Cursor no PC Windows do operador — mesma LAN e configuração SSH que o shell do operador (ver `**homelab-ssh-via-terminal.mdc**`). Não tratar o “assistente” como rede separada.
- **Orquestração por padrão:** Ao pedir **completão** ou usar o token `**completao`**, o assistente deve executar `**.\scripts\lab-completao-orchestrate.ps1 -Privileged`** na raiz do repo, salvo se optar por não usar. Registros: `**docs/private/homelab/reports/**`.
- **Probes privilegiados:** `**sudo -v`** no script de smoke exige **sudoers estreito** em cada Linux (modelo em `**LABOP_COMPLETÃO_SUDOERS*.md`** gitignored). `**sudo -v` no tmux** aquece sudo **para aquele TTY**, não automaticamente para `**ssh host 'sudo …'`** não interativo — para `**-Privileged`** fiável, **alinhe** sudoers com o modelo.
- **Em falha:** Se `**sudo -v`** ou SSH falhar, o assistente **lembra o operador** de atualizar sudoers / agente SSH / sudo interativo conforme preciso e **executa de novo** os testes — ver `**lab-completao-workflow.mdc`**.
- **Âmbito “datacenter de testes” no lab:** Para **completão**, o assistente **pode** instalar **dependências em falta**, corrigir **portas** da app/compose, acrescentar regras **estreitas** **lab-op↔lab-op** no **firewall** ou **VLAN** (via `**ufw`**, `**nftables`**, `**LAB-ROUTER-01.ps1**` quando houver credenciais), e ajustar SELinux/AppArmor/fail2ban/sshguard/USBGuard/AIDE/auditd (etc.) só com least privilege e intenção reversível — política completa: `**lab-completao-workflow.mdc**`. Registre alterações em `**docs/private/homelab/**`; **nunca** commits públicos com **segredos** ou **detalhes LAN**.
- **Wrappers + sudoers + sem perguntas ociosas:** Preferir `**lab-completao-orchestrate.ps1 -Privileged`** e os demais scripts do repo (ver `**LAB_OP_PRIVILEGED_COLLECTION.pt_BR.md`**, modelo gitignored `**LABOP_COMPLETÃO_SUDOERS*.md**`) para **sudo estreito sem senha** nos probes. **Não** voltar a pedir permissão para o fluxo acordado SSH/`**-Privileged`**. Proteger o PC Windows principal de desenvolvimento (papel L-series, `**PRIMARY_WINDOWS_WORKSTATION_PROTECTION.pt_BR.md`**) e o clone **canônico**; **outros** hosts no manifesto e imagens **Docker** podem ser **resincronizados** com `**origin`** / Hub para testes.

### Raio de explosão (contrato — não confundir alvos)

| Alvo                                                                                | Política Git / repo                                                                                                                                                                                                                       | Porquê                                                                                                            |
| ----------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| **PC dev principal** (ThinkPad **L-series**, workspace Cursor, clone **canônico**)  | **Nunca** `**git reset --hard`**, `**git clean -fdx`**, `**clean-slate**` ou reescrita de histórico na árvore principal. Fluxo normal: `**git pull**`, merge, branch, stash.                                                              | Continuidade de evidências — `**PRIMARY_WINDOWS_WORKSTATION_PROTECTION.pt_BR.md**`.                               |
| Hosts **LAB-OP** no `**lab-op-hosts.manifest.json`** (cada `**repoPaths`** por SSH) | **Seguro** alinhar com `**git fetch`**, `**git pull --ff-only`**, `**lab-op-git-align-main.ps1**`, `**lab-op-git-ensure-ref**`, `**-AlignLabClonesToLabGitRef**` — afeta **só** clones **remotos**, **não** a árvore do PC dev principal. | Clones de lab são **descartáveis** para teste; alinhar com o GitHub **não** é o mesmo risco do PC dev principal.  |
| **Imagens de contêiner** (Docker / **Swarm** / **Podman** / **Kubernetes**)         | **Puxar de novo** do **Docker Hub** (ou registry configurado); `**docker pull`**, atualizar stack/serviço, prune — **normal** no lab.                                                                                                     | Imagens são **reproduzíveis** a partir do registry — não equivalem a destruir o Git canônico no PC dev principal. |

- **Mapa de inventário LAB-OP (hardware + software):** Antes de interpretar resultados do smoke, o assistente deve `**read_file`** no `**docs/private/homelab/OPERATOR_SYSTEM_MAP.md`** e na matriz `**LAB_SOFTWARE_INVENTORY.md**` quando existirem (`**docs-private-workspace-context.mdc**`). O `**lab-completao-orchestrate.ps1**` corre primeiro o `**scripts/lab-completao-inventory-preflight.ps1**` (frescura por padrão **15 dias**): se faltar arquivo ou estiver velho, corre `**lab-op-sync-and-collect.ps1`** para atualizar telemetria `**homelab-host-report`** em `**docs/private/homelab/reports/**` — depois **fundir** nos `.md` e atualizar data **as-of** (ver *Frescura do inventário* abaixo). Desligar: `**-SkipInventoryPreflight`**; ajustar dias: `**-InventoryMaxAgeDays N`**.

**Relação:**

| Camada                      | O que é                                               | Comando típico                                                                             |
| --------------------------- | ----------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| **CI / unitários e guards** | Reproduzível, GitHub, sem segredos LAN                | workflow **CI**, **pytest**                                                                |
| **Gate no PC dev**          | Pre-commit + testes antes do merge                    | `**.\scripts\check-all.ps1`**                                                              |
| **Completão no lab**        | Produto + runtime + LAN + BD opcional + HTTP opcional | `**lab-completao-host-smoke.sh`** por host; `**lab-completao-orchestrate.ps1`** no Windows |

## Evidência de lab: público vs privado (lições aprendidas)

| Camada | Local | Conteúdo |
| ------ | ----- | --------- |
| **Privado** | `docs/private/homelab/COMPLETAO_SESSION_*.md`, `docs/private/homelab/reports/` | Narrativa completa, LAN, credenciais, notas do operador — **nunca** colar literalmente no Git público. |
| **Hub público** | [`docs/ops/LAB_LESSONS_LEARNED.md`](LAB_LESSONS_LEARNED.md) | Resumo vivo + índice de arquivo + **follow-ups** para **`docs/plans/PLANS_TODO.md`**. |
| **Arquivo público datado** | [`docs/ops/lab_lessons_learned/`](lab_lessons_learned/README.pt_BR.md) | Snapshots imutáveis: **`LAB_LESSONS_LEARNED_YYYY_MM_DD.md`** (ritual no README). |

**Contrato:** [ADR 0042](../adr/ADR-0042-lab-lessons-learned-archive-contract.md). **Token de sessão:** **`lab-lessons`** carrega **`.cursor/rules/lab-lessons-learned-archive.mdc`** quando os globs não prendem — [OPERATOR_AGENT_COLD_START_LADDER.pt_BR.md](OPERATOR_AGENT_COLD_START_LADDER.pt_BR.md) § *Token → rule latch (`lab-lessons`)*.

**Checklist multi-host** (passos manuais A–M): [LAB_SMOKE_MULTI_HOST.pt_BR.md](LAB_SMOKE_MULTI_HOST.pt_BR.md).

## Frescura do inventário (antes / durante completão)

**Porquê:** Hardware muda raramente; **versões de software** (Python, Docker, pacotes) mudam com frequência e influenciam decisões (ex.: só contêiner vs `**uv`** nativo, builds de conectores). Inventários privados desatualizados aumentam interpretações erradas.

1. **Automação rastreada:** `**scripts/lab-completao-inventory-preflight.ps1`** verifica `**docs/private/homelab/LAB_SOFTWARE_INVENTORY.md`** e `**OPERATOR_SYSTEM_MAP.md**`. Por arquivo: linha `**<!-- lab-op-inventory-as-of: YYYY-MM-DD -->**` ou `****Lab inventory as-of:** YYYY-MM-DD**` (ou *Inventário … as-of* em pt-BR), senão **data de modificação** do arquivo.
2. **Limiar por padrão:** **15 dias** (`-MaxAgeDays` / `**-InventoryMaxAgeDays`** no orchestrator). Se **em falta ou velho**, `**lab-completao-orchestrate.ps1`** corre `**lab-op-sync-and-collect.ps1*`* (mesmo manifesto) salvo `**-SkipInventoryPreflight**`. `**-SkipGitPullOnInventoryRefresh**` só se quiseres relatórios **sem** `**git pull`** nos clones do lab.
3. **Depois da telemetria:** o `**lab-op-sync-and-collect`** **não** reescreve os inventários — **atualiza** as matrizes a partir do `*_labop_sync_collect.log` mais recente e define **as-of** no topo para o próximo check de idade.
4. **Preflight manual:** `.\scripts\lab-completao-inventory-preflight.ps1 -AutoRefresh` (mesmos defaults).

## Preflight de contrato de dados (opcional — falhar antes do smoke por host)

**Objetivo:** Detetar **desvio de esquema** em bases de laboratório (colunas renomeadas/removidas) **antes** do smoke SSH e dos scans do produto — espírito de **contract testing**.

1. **Manifesto (chave na raiz):** opcional **`completaoDataContractsPath`** — caminho para um YAML (normalmente em **`docs/private/homelab/`**, gitignored). Caminhos relativos resolvem a partir da raiz do repo.
2. **Formato YAML:** copiar **`docs/private.example/homelab/completao_data_contracts.example.yaml`** — lista **`checks`** com **`connection.url_from_env`** (URL SQLAlchemy na **shell do operador**, nunca no YAML), **`schema`** / **`table`** e **`require_columns`**.
3. **Executor:** **`scripts/lab_completao_data_contract_check.py`** — usa **`inspect`** do SQLAlchemy; suporta o dialecto que a URL indicar (PostgreSQL, MSSQL via **`mssql+pyodbc`**, MySQL/MariaDB, SQLite, etc.).
4. **Gancho no orquestrador:** **`lab-completao-orchestrate.ps1`** corre o checker **depois** de **`lab-op-git-ensure-ref`** e **antes** do smoke SSH por host. Se o manifesto define **`completaoDataContractsPath`** mas o arquivo **não existe**, o orquestrador **falha** (misconfiguração). Desligar: **`-SkipDataContractPreflight`**.

## Eventos estruturados (JSONL) e preflights idempotentes

**Objetivo:** Se o orquestrador for interrompido a meio, operadores e automação mantêm **marcadores por fase** (inventário, ref Git, contrato de dados, smoke por host, resumo). Falhas trazem **`message`** e opcional **`detail`**.

1. **Orquestrador principal:** cada corrida acrescenta um objeto JSON por linha em **`docs/private/homelab/reports/completao_<timestamp>_orchestrate_events.jsonl`** (UTF-8 sem BOM). Campos incluem **`v`**, **`ts`**, **`phase`**, **`status`**, **`message`**, **`host`**, **`exitCode`** (quando aplicável), **`detail`** (hashtable quando aplicável).
2. **Fases (não exaustivo):** **`orchestrate`** (início), **`inventory_preflight`**, **`lab_git_ensure_ref`**, **`data_contract_preflight`**, **`image_preflight`**, **`host_smoke`**, **`summary`**, **`lab_result`** (resumo legível por máquina no fim da corrida), **`grc_executive_report`** (opcional: após **`lab_result.json`**, **`scripts/generate_grc_report.py`** via **`uv run python`**; grava **`GRC_EXECUTIVE_REPORT.json`** e cópia com carimbo **`completao_<stamp>_GRC_EXECUTIVE_REPORT.json`** na mesma pasta de relatórios; falha vira **aviso** e **não** altera o *exit* semântico do completão), **`grc_export_artifacts`** (quando o JSON GRC *latest* existe: **`scripts/export_reports.py`**; grava **`GRC_EXECUTIVE_REPORT_remediation.xlsx`** e **`GRC_EXECUTIVE_REPORT_executive.pdf`** mais cópias com carimbo; falha vira **aviso**).
3. **Preflight opcional de imagem de contentor (só leitura, não bloqueante):** chave na raiz do manifesto **`completaoImageRefs`** — array JSON de strings (ex.: **`fabioleitao/data_boar:lab`**). Antes do smoke por host, o script faz SSH a **`completaoImageProbeSshHost`** se existir (e **não** for host **LAB-NODE-04** passivo), senão ao **primeiro `sshHost` que não seja LAB-NODE-04**, e corre **`docker image inspect`** / **`podman image inspect`** (**sem pull**, **sem criar**). Imagem em falta ou falha de SSH no probe gera linhas JSON **`warning`** e **`Write-Warning`**; o orquestrador **continua** o smoke por host. Desligar: **`-SkipImagePreflight`**. O **LAB-NODE-04** **nunca** serve como host de probe de imagens.
4. **Caminho híbrido A/B (`-HybridLabOpHighDensity173`):** **`lab-completao-orchestrate-hybrid-v173.ps1`** escreve **`completao_hybrid_<timestamp>_events.jsonl`** com corridas **stable vs candidato**: workdirs isolados em **`/tmp/databoar_bench/stable`** e **`/tmp/databoar_bench/beta`** (nome de pasta **beta** histórico; a **tag candidata** no Docker acompanha **`pyproject.toml`**), portas publicadas **9001** (stable **v1.7.3**) e **9002** (**v1.7.4-rc** nesta revisão do doc), **tmux** destacado por passo quando não existe sessão **`completao`** do operador. O script híbrido **não depende de `docker pull` / `podman pull` nos alvos**: no **PC Windows de desenvolvimento principal** faz **`docker save` / `podman save`** das duas imagens (**`fabioleitao/data_boar:1.7.3`** e **`fabioleitao/data_boar:1.7.4-rc`**) salvo overrides, depois **`rsync`** por SSH se **`rsync`** estiver no PATH senão **`scp`**, e corre **`docker load` / `podman load` das duas arquivos antes** de gravar **`config_databoar.yaml`**. Overrides opcionais: **`DATA_BOAR_HYBRID_STABLE_TAR_GZ`** e **`DATA_BOAR_HYBRID_BETA_TAR_GZ`** (caminhos Windows; **`.tar`** ou **`.tar.gz`**). Copia **`scripts/lab-completao-host-smoke.sh`** (e **`scripts/lab_completao_data_contract_check.py`** quando existir) para **`.../stable/scripts/`** e **`.../beta/scripts/`** para execução direta por SSH a partir dos dirs de benchmark. Opcional **`DATA_BOAR_HYBRID_REMOTE_PULL_SCRIPTS=1`** mais **`DATA_BOAR_HYBRID_REMOTE_PULL_REF`** (ramo padrão **`main`** em **`origin`**, ou **`upstream/main`**, etc.) corre **`git fetch` + `git pull --ff-only`** no clone **`repoPaths[0]`** do manifesto em cada host motor. Compara o campo **`delta_ms`** em **`benchmark_compare`** no JSONL para parede de relógio vs custo **FFI/fronteira Python**.

## Resumo legível por agente (`lab_result.json`)

**Objetivo:** Permitir que um agente novo (ou automação) compare a corrida **atual** com um **`lab_result.json`** anterior sem analisar a saída de texto completa dos logs.

1. **Local:** mesma pasta dos outros artefatos de completão: **`docs/private/homelab/reports/lab_result.json`** e **`lab_status.json`** (mesmo *payload*; ambos **sobrescritos de forma atômica** em cada corrida para o agente não ler um arquivo a meio da escrita) mais **`completao_<timestamp>_lab_result.json`** (uma cópia por carimbo, junto a **`completao_<timestamp>_orchestrate_events.jsonl`**).
2. **Campos de topo (não exaustivo):** **`schemaVersion`**, **`kind`** (`data_boar_lab_completao_orchestrate`), **`run_stamp`**, **`generated_at_utc`**, **`repo_folder_name`**, **`manifest_file_name`**, **`audit_trail`** (quem/o quê disparou a corrida — ver abaixo), **`exit_code_semantic`** (contrato de *exit* do processo + razão no caminho feliz), **`overall_status`** (`completed`, **`completed_with_skips`** ou **`degraded`** conforme conectividade e *loop* de hosts), **`phases`**, **`orchestration_checks`** (lista **`step`** / **`result`** espelhando essas fases), **`idempotency`** (o que é *overwrite* vs histórico com carimbo), **`connectivity_status`**, **`vulnerabilities_found`**, **`vulnerability_scan`**, **`performance_metrics`**, **`run_flags`**, **`artifacts`**, **`agent_readable_hint`**.
3. **Valores de `summary` em conectividade (heurística do orquestrador):** **`no_host_records`**, **`all_hosts_completed_paths_ok`**, **`degraded`** (algum registo cujo **`outcome`** coincide com padrões de inacessível / exceção / caminho de repo / falha de base).
4. **`audit_trail` (rastreabilidade):** regista **`windows_session_user`**, **`windows_computer_name`**, **`powershell_pid`**, carimbo UTC e opcional **`invoker_correlation`** a partir da variável de ambiente **`DATA_BOAR_COMPLETAO_INVOKER`** (definida pelo operador ou automação com id de ticket, rótulo de sessão Cursor ou id de agente). Apoia prestação de contas ao estilo ISO 27001 e disciplina operacional alinhada à LGPD; **por si só** não é atestado jurídico.
5. **`exit_code_semantic`:** objeto com **`contract`** = **`DATA_BOAR_COMPLETAO_EXIT_v1`**, inteiro **`value`**, texto **`reason`** e mapa **`meanings`** explicando os códigos **0–3** (ver seção seguinte). No **caminho feliz** do orquestrador, o código de saída do processo coincide com **`exit_code_semantic.value`** (`exit` do PowerShell).

## Telemetria por *exit code* (`DATA_BOAR_COMPLETAO_EXIT_v1`)

**Objetivo:** CI, prompts de release e assistentes mapeiam falhas **sem** analisar todas as linhas de log.

| Código | Classe | Fontes típicas neste repositório |
| --- | --- | --- |
| **0** | Sucesso total | Orquestrador termina com **`overall_status`** = **`completed`** (resumo de conectividade **não** **degraded**). **`lab_completao_data_contract_check.py`** devolve **0**. **`lab-completao-host-smoke.sh`** devolve **0** após emitir o pacote de diagnóstico. |
| **1** | Infra / permissão / alcance | Falha de *probe* SSH ou transporte, URL de BD em variável de ambiente vazia ou **`database error:`** de conectividade/auth em **`lab_completao_data_contract_check.py`**, orquestrador **`degraded`** ou **`completed_with_skips`**. (*Preflight* de imagem de contentor é **não bloqueante**: imagens em falta geram **`warning`** e a corrida segue.) |
| **2** | Dados, esquema ou contrato de repo | Erros de coluna em falta / forma YAML em **`lab_completao_data_contract_check.py`** (após conectar), clone remoto sem **`scripts/lab-completao-host-smoke.sh`** (guarda SSH remota usa **exit 2**), argumento CLI desconhecido em **`lab-completao-host-smoke.sh`** (**exit 2**). |
| **3** | Violação de compliance (reservado) | *Hooks* de política ou *scanner* que afirmem infração governada (scripts base **não** emitem **3** ainda; reserve para integração futura). |

**Nota:** caminhos PowerShell com **`throw`** não tratado podem terminar com código não zero padrão (**1**) **antes** de existir **`lab_result.json`** — use **`completao_*_orchestrate_events.jsonl`** para forense de corrida parcial.

## Ref Git alvo para completão reproduzível (clones LAB-OP)

O smoke no host executa `**scripts/lab-completao-host-smoke.sh`** a partir de cada checkout em `**repoPaths`**. Se esses clones estiverem em commits arbitrários, a corrida **não** é comparável ao CI, a um gate de release nem a outra sessão — estás a exercitar **o commit que estiver checked out**.

1. **Declarar uma ref:** chave opcional na raiz do manifesto privado `**completaoTargetRef`** em `**docs/private/homelab/lab-op-hosts.manifest.json`** (ver `**docs/private.example/homelab/lab-op-hosts.manifest.example.json**`) e/ou passar `**-LabGitRef**` a `**lab-completao-orchestrate.ps1**`. O CLI `**-LabGitRef**` tem prioridade quando não está vazio; senão usa-se o valor do manifesto.
2. **Verificar antes do smoke:** Quando há ref definida e **não** passas `**-SkipLabGitRefCheck`**, o orchestrator corre `**scripts/lab-op-git-ensure-ref.ps1`** em modo Check (depois do preflight de inventário, antes do smoke por SSH). Faz `**git fetch**` em cada clone (fetch de **branch** precisa concluir com sucesso; fetch de **tags** é melhor esforço para que “would clobber existing tag” **não** aborte o bash remoto antes das linhas `**LABOP_REF_*`** — ver cabeçalho do script) e **falha** se `**HEAD`** não for o commit resolvido para essa ref (`main` / `origin/main` → ponta de `**origin/main`**; tags de release, nomes de branch e SHAs completos suportados). Registos: `**docs/private/homelab/reports/lab_op_git_ensure_ref_*.log**`.
3. **Tags de release vs refresh de inventário:** `**lab-op-sync-and-collect.ps1`** (quando o markdown de inventário está velho) faz `**git pull --ff-only`** nos clones do lab, avançando-os para o `**main**` mais recente. Isso pode **quebrar** um pin em `**vX.Y.Z`**. Ao testar uma tag, passa `**-SkipGitPullOnInventoryRefresh`** em `**lab-completao-orchestrate.ps1**` para o refresh não mover os clones antes do **ensure-ref**; atualiza inventários privados manualmente se preciso.
4. **Alinhar / reset só no LAB:** `**lab-op-git-ensure-ref.ps1 -Mode Reset`**, `**lab-op-git-align-main.ps1`**, ou `**lab-completao-orchestrate.ps1 -AlignLabClonesToLabGitRef**` com `**-LabGitRef**` (ou `**completaoTargetRef**`) aplicam-se só aos `**repoPaths**` nos hosts SSH do manifesto — **nunca** ao clone **canônico** no **PC principal**. Mesma classe de risco que `**lab-op-git-align-main.ps1`** nesses clones remotos (descarta commits locais no lab / **detached HEAD** em tag).

## Pré-Big-Bang (espelho LAB + liberação de rede)

**Objetivo:** Antes de uma sessão de lab de alto impacto (“Big Bang”), alinhar os **clones LAB-OP** com `**origin/main`** ou uma **tag de release** (ex.: `**v1.7.3`**), evitar que o refresh de inventário faça `**git pull**` para `**main**` contra um pin de tag, e recolher **pistas só de leitura** de firewall / dependências. O script **não altera** a árvore **canônica** no **Windows/WSL2 (PC dev principal)** — apenas os `**repoPaths`** nos hosts do manifesto por SSH.

1. **No PC de desenvolvimento (terminal Cursor):** `**.\scripts\lab-op-pre-big-bang.ps1`**
  - `**-Ref origin/main**` (padrão) ou `**-Ref v1.7.3**` (ou outra ref suportada por `**lab-op-git-ensure-ref.ps1**`).
  - Com `**-ForceLabGitReset**`, corre `**lab-op-git-ensure-ref.ps1 -Mode Reset**` em cada clone do manifesto (alinhamento **destrutivo só no LAB** / checkout em tag detached). Sem este switch, só **Check** (falha se `**HEAD`** não coincidir com a ref resolvida).
  - **Tags `vX.Y.Z`:** por padrão corre primeiro `**lab-completao-inventory-preflight.ps1 -AutoRefresh -SkipGitPullOnRefresh`** (salvo `**-SkipInventoryWarmup**`) para o refresh de inventário não puxar `**main**` antes do pin da tag.
  - `**-IncludeProbes`:** SSH por host com linhas `LABOP_BB_GIT_*`, excertos de `**ufw`** / **fail2ban** / `**ss`** (melhor esforço com `**sudo -n**`), e em **LAB-NODE-03** / **LAB-NODE-04** um smoke `**python3`** (zlib/bz2/lzma) mais dicas `**xbps-query**` / `**dpkg**`.
  - `**-OrchestratorSshSourceIp`:** inclui no log uma dica concreta de **ignoreip** do fail2ban para o PC que orquestra (rajadas de SSH).
2. **Registo:** `**docs/private/homelab/reports/lab_op_pre_big_bang_<timestamp>.log`** contém `**LABOP_BB_GIT_ENSURE_REF_OK**` quando o **ensure-ref** passa, `**LABOP_BB_OPERATOR_FIREWALL_CLEAR_PENDING`** e um checklist **não executável** (UFW/nft, Postgres **5432**, MariaDB **3306**, NFS/SMB, AppArmor/SELinux / **auditd**, fail2ban / **sshguard**). **“Firewall Clear”** é **confirmação humana** depois de aplicar regras estreitas em **tmux** com `**sudo -v`** — o script **não** abre portas sozinho.
3. **Depois deste gate:** corre `**lab-completao-orchestrate.ps1`** (e caminhos híbridos se usares) com a mesma política de `**-LabGitRef**` / `**completaoTargetRef**` descrita em *Ref Git alvo* acima.

## Cobertura de capacidades (documentação + código como fonte de verdade)

**Objetivo:** Aprender o comportamento **observado** em relação ao que está **documentado** — docs em **inglês** e **código** são canônicos ([README.md](../README.md)). O completão deve **exercitar** (conforme recursos do lab): **armazenamento remoto** (NFS, SSHFS, SMB/CIFS — mounts no SO e/ou caminhos de conector segundo [TECH_GUIDE.pt_BR.md](../TECH_GUIDE.pt_BR.md)); **bases de dados** ([deploy/lab-smoke-stack](../deploy/lab-smoke-stack/), conectores em [ADDING_CONNECTORS.pt_BR.md](../ADDING_CONNECTORS.pt_BR.md)); **tipos/extensões de arquivo**, **arquivos ocultos** / nomes **dot**, **pacotes compactados**; **local vs remoto**; **“discoverables”** alinhados a LGPD como **linguagem de detecção** ([COMPLIANCE_AND_LEGAL.pt_BR.md](../COMPLIANCE_AND_LEGAL.pt_BR.md) — **não** é parecer jurídico); **sensibilidade ML/DL** ([SENSITIVITY_DETECTION.pt_BR.md](../SENSITIVITY_DETECTION.pt_BR.md), [TESTING.pt_BR.md](../TESTING.pt_BR.md)); **relatórios** e **dashboard**; **POC** — questionário de maturidade ([SMOKE_MATURITY_ASSESSMENT_POC.pt_BR.md](SMOKE_MATURITY_ASSESSMENT_POC.pt_BR.md)), **WebAuthn/FIDO2** JSON RP ([SMOKE_WEBAUTHN_JSON.pt_BR.md](SMOKE_WEBAUTHN_JSON.pt_BR.md), [SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.pt_BR.md](SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.pt_BR.md), [ADR 0033](../adr/ADR-0033-webauthn-open-relying-party-json-endpoints.md)). Afirmações **secure-by-design** devem alinhar com [SECURITY.pt_BR.md](../SECURITY.pt_BR.md) e o que **rodou na prática**. Anote **passo / lacuna / desvio** em notas **privadas** de sessão (`docs/private/homelab/`) — **política:** `**.cursor/rules/lab-completao-workflow.mdc`** (matriz de capacidades).

## Scripts (rastreados)

1. `**scripts/lab-completao-host-smoke.sh*`* (em **cada** host Linux, na raiz do clone) — `uv`, Docker/Podman, estado do compose em `deploy/lab-smoke-stack` se existir, HTTP opcional (`LAB_COMPLETAO_HEALTH_URL` / `--health-url`), import rápido do motor salvo `**--skip-engine-import`** (ou `**LAB_COMPLETAO_SKIP_ENGINE_IMPORT=1`**) — ver **Hosts só com contêiner** abaixo. `**--privileged`**: leitura com `**sudo -n`** (iptables/nft/ufw/fail2ban em modo snapshot).
2. `**scripts/lab-completao-orchestrate.ps1**` (no **PC Windows** do operador) — lê o manifest em `**docs/private/homelab/lab-op-hosts.manifest.json`**; `**completaoTargetRef`** opcional na raiz ou CLI `**-LabGitRef**` dispara `**lab-op-git-ensure-ref.ps1**` antes do smoke salvo `**-SkipLabGitRefCheck**`; SSH por host, executa o bash em cada `**repoPaths**`. Campo opcional `**completaoHealthUrl**`: depois do smoke por SSH, pedido HTTP a partir do PC dev. Campos opcionais `**completaoEngineMode`:** `**container`** ou `**completaoSkipEngineImport`:** `**true`** passam `**--skip-engine-import`** ao smoke (hosts **Docker Swarm** / **só Podman** sem `**uv`** no metal); gera em `**docs/private/homelab/reports/`** o consolidado **`completao_<timestamp>_allhosts.log`**, logs por host `*_completao_host_smoke.log` e **`lab_result.json`** / **`lab_status.json`** (mesmo JSON; mais cópia com carimbo) — ver *Resumo legível por agente* acima.
3. **Sudo sem senha (estreito)** — mesmo critério do `**homelab-host-report.sh`**: modelo em `**docs/private/homelab/LABOP_COMPLETÃO_SUDOERS.pt_BR.md`** (não commitar sudoers reais no GitHub).
4. **Template de sessão / lições** — `**docs/private/homelab/COMPLETAO_SESSION_TEMPLATE.pt_BR.md`**. Exemplos preenchidos: `**docs/private/homelab/COMPLETAO_SESSION_YYYY-MM-DD.md`** (só operador; nunca no GitHub público).
5. `**scripts/lab-op-repo-status.ps1**` — `**git fetch**` + `**git status -sb**` em cada `**repoPaths**` (sem reset). Opcional `**-PullFfOnly**` para `**git pull --ff-only**`. Use **antes** do orchestrate quando aparecer `**MISSING_SCRIPT`** (clone desatualizado vs `**main`**).
6. `**scripts/lab-op-git-ensure-ref.ps1**` — em cada host, `**git fetch**` em cada clone `**repoPaths**`, depois **Check** (falha se `**HEAD`** ≠ ref resolvida) ou **Reset** (checkout/reset destrutivo para coincidir com a ref). Usado automaticamente por `**lab-completao-orchestrate.ps1`** quando `**completaoTargetRef`** / `**-LabGitRef**` está definido — ver *Ref Git alvo para completão reproduzível* acima.
7. `**scripts/lab-op-pre-big-bang.ps1*`* — gate opcional **pré-Big-Bang**: `**lab-op-git-ensure-ref`** (Check ou `**-ForceLabGitReset**` para Reset), aquecimento de inventário consciente de tags, checklist operador (firewall / fail2ban / AppArmor) e `**-IncludeProbes**` só de leitura. Ver *Pré-Big-Bang* acima. **Não** modifica o clone canónico no PC dev.
8. `**scripts/lab-op-git-align-main.ps1*`* — `**git fetch**` + `**git reset --hard origin/main**` em cada `**repoPaths**`. **Destrutivo** (descarta commits locais no clone). Para refs que não sejam `**main`** (ex.: tags de release), preferir `**lab-op-git-ensure-ref.ps1 -Mode Reset`**.
9. **Ansible (opcional):** `**ops/automation/ansible/playbooks/lab-op-data-boar-git-sync.yml`** — alinhamento com inventário `**[lab_op_data_boar]`**.
10. **Modelos de filesystem (rastreados):** `**docs/private.example/homelab/config.lab-fs-varlog.example.yaml`**, `**config.lab-fs-home-user.example.yaml`** — executar `**main.py` no mesmo host** que os caminhos; criar pastas de relatório/SQLite antes; `**/var/log`** pode dar **permissão negada** em alguns arquivos.
11. **MongoDB:** `**driver: mongodb`**; `**pymongo`** com `**uv sync --extra nosql**`. Subir stack: `**docker compose -f docker-compose.yml -f docker-compose.mongo.yml up -d**` em `**deploy/lab-smoke-stack**` (porta típica **27018**). Se o Mongo estiver parado, o alvo falha como **unreachable**, não como **unsupported**.

## Hosts só com contêiner (Docker Swarm, stack Podman, sem `uv` no metal)

Alguns equipamentos do lab são **orquestração** ou **política**: o operador corre o Data Boar **só** via **Docker** / **Podman** / **Docker Swarm** (stack ou serviço) e **não** depende de `**uv`** no host para checks por SSH. Isso é **postura válida** de completão se estiver no manifesto privado — o assistente **não** deve tratar “`uv` não está no PATH” nesses hosts como defeito a “corrigir” instalando Python no metal.

1. Em `**docs/private/homelab/lab-op-hosts.manifest.json`**, defina `**completaoEngineMode`** como `**container**` ou `**completaoSkipEngineImport**` como `**true**` para esse `**sshHost**`. O `**lab-completao-orchestrate.ps1**` passa `**--skip-engine-import**`; o smoke registra uma linha **skipped** explícita para `**import core.engine`** em vez de falha implícita.
2. **Critérios de sucesso** nesses hosts: CLI do runtime de contêiner OK, opcional `**deploy/lab-smoke-stack`** `**compose ps`** quando usares compose aí, e/ou `**completaoHealthUrl**` (ex.: **8088** publicado) com **200** a partir do PC dev.
3. **Scans de FS / CLI** em caminhos desse host ainda precisam de **algum** runtime (ex.: `**uv run`** dentro de contêiner com bind mount, ou outro caminho documentado). O smoke do host **não** substitui isso — anotar nas notas privadas qual abordagem usaste.

Ver `**docs/private.example/homelab/lab-op-hosts.manifest.example.json`** para campos opcionais.

## Nós com hardware limitado (LAB-NODE-04, LAB-NODE-03 Void; Kubernetes adiado)

- **LAB-NODE-04 (sem Docker no hardware):** `**completaoHardwareProfile`** começando por `**LAB-NODE-04**` ou `**sshHost**` com `**LAB-NODE-04**` — o `**lab-completao-orchestrate.ps1**` usa só o caminho **passivo** (`**.venv/bin/python3`** ou `**python3 -m databoar --help**` + logs do sistema), **sem** smoke de contêiner. **Kubernetes** fica **fora** desta fase até haver capacidade dedicada.
- **LAB-NODE-03 (Void, compilação `mysqlclient`):** alias `**LAB-NODE-03`** / `**minibt**` ou perfil `**LAB-NODE-03-void**` força `**--skip-engine-import**` e registra dicas `**xbps-install**` (`**libmariadbclient-devel**`, `**pkg-config**`); scans pesados de **MariaDB/MySQL** e **Swarm** no **LAB-NODE-02** e **LAB-NODE-01**. Se `**uv sync`** continuar falhando, usar **branch privada** ou **overlay** `**pyproject`** **gitignored** **só nesse host** — **não** retirar extras de BD do `**pyproject.toml`** canônico no Git.
- **Skip-on-failure:** falhas de **SSH**, de **saúde do diretório** do primeiro `**repoPaths`**, ou base passiva LAB-NODE-04 inválida fazem `**continue**` com aviso e linhas `**skip-on-failure**` nos relatórios em `**docs/private/homelab/reports/**`.

## Ordem de fatias recomendada (um host de cada vez)

1. **Ref alvo (recomendado para corridas comparáveis):** definir `**completaoTargetRef`** (ex.: `**origin/main`** ou `**vX.Y.Z**`) e/ou `**-LabGitRef**` em `**lab-completao-orchestrate.ps1**`; usar `**-SkipGitPullOnInventoryRefresh**` ao fixar uma **tag**. Opcional: `**lab-op-pre-big-bang.ps1`** (gate pré-Big-Bang), `**lab-op-repo-status.ps1**` (inspecionar), depois `**lab-op-git-align-main.ps1**`, `**lab-op-git-ensure-ref.ps1**` ou `**git pull --ff-only**` quando aceitares reset **destrutivo** ou fast-forward nos clones LAB.
2. **Smoke no host:** `**lab-completao-orchestrate.ps1`** até desaparecer `**MISSING_SCRIPT`** e, em hosts **nativos**, o import do motor funcionar. Hosts **só contêiner** (manifest `**completaoEngineMode`:** `**container`** ou `**completaoSkipEngineImport`:** `**true`**) saltam o import no metal; validar Docker/Podman/Swarm + `**completaoHealthUrl`**.
3. **FS `/var/log`:** copiar o modelo, executar `**main.py`** **naquele Linux**.
4. **FS home:** idem com `**config.lab-fs-home-user.example.yaml`** (ajustar o caminho `/home/user/...` ao usuário de lab se preciso).
5. **Completão CLI no PC dev** com YAML privado (BD no hub + FS sintético no repo) — ver `**docs/ops/LAB_EXTERNAL_CONNECTIVITY_EVAL.md`**.
6. **API / web:** subir `**main.py --web`**; `**curl`** em `**/health**`; browser; opcional `**completaoHealthUrl**` no manifesto.

## Limite de automação vs remediação assistida

- Os **scripts** (`lab-completao-orchestrate`, host-smoke) **por si** **não** abrem **firewalls** nem relaxam **LSM**/ferramentas de integridade — **só** **inspecionam** e **registram**.
- Quando o operador pede **completão** e **quer** **desbloquear** testes, o assistente **pode aplicar** correções **estreitas**, no **escopo lab-op**, com **least privilege** (pacotes, portas, `**ufw`**/nft, UniFi via `**LAB-ROUTER-01.ps1`** se existir, contêineres, mounts **NFS**/**SMB**/**SSHFS** conforme o produto) segundo `**lab-completao-workflow.mdc`**. **Pergunte ao operador** antes de mudanças **amplas** ou **irreversíveis** de hardening.
- **Prontidão para produção** continua **iterativa**: repetir completão, issues, patches, executar de novo.

## Reutilização de automação e registro de aprendizados

- **Codificar o que repetir:** Quando um passo do completão for **repetível**, acrescentar ou alargar `**scripts/`**, Ansible em `**ops/automation/ansible/`**, ou campos no **manifesto** — hub: **[TOKEN_AWARE_SCRIPTS_HUB.md](TOKEN_AWARE_SCRIPTS_HUB.md)**; política: `**lab-completao-workflow.mdc`** (*Automation reuse + documented learnings*).
- **A/B com Git no clone Windows (cronometrado):** o **`scripts/benchmark-ab.ps1`** cria **`benchmark_runs/`**, exige árvore limpa (**`-AutoStash`** / **`-AllowDirty`**), faz checkout da **tag** legada e volta ao **branch/HEAD** guardado, corre **`lab-completao-orchestrate.ps1`** duas vezes com **`Measure-Command`**, copia arquivos recentes de **`docs/private/homelab/reports/`** por rodada e grava **`benchmark_runs/times.txt`**. *Harness* mais leve só com ref no LAB (sem checkout local): **`scripts/run-benchmark.ps1`**.
- **Registrar sinais** em notas **privadas** (`docs/private/homelab/`, modelo `**COMPLETAO_SESSION_TEMPLATE.pt_BR.md*`*): **timeouts**, duração **de relógio**, **lentidão** inesperada, **FP/FN** face a **sintéticos** com verdade conhecida (relatório vs esperado), **confiança** em caminhos **reais** (ex.: árvores de log do sistema, amostras em diretório de usuário), **latência** em **APIs públicas** / **SSH** / hosts **com poucos recursos** vs máquinas mais rápidas, e desvios **docs/defaults**. Isto alimenta `**PLANS_TODO.md*`* / **issues** — **sem** PII cru no Git público.

## Arranque rápido

1. Em hosts onde você roda o produto **no metal**, garantir clone + `**uv`** (muitas vezes `**~/.local/bin/uv`** — o smoke antecede isso ao `**PATH**`); `**uv sync**` e `**uv sync --extra nosql**` se houver alvos Mongo; outros extras conforme [TECH_GUIDE.pt_BR.md](../TECH_GUIDE.pt_BR.md). Em hosts **só contêiner** (gerenciador Swarm, só Podman, etc.), definir `**completaoEngineMode`:** `**container`** (ou `**completaoSkipEngineImport`:** `**true`**) e basear-se em HTTP / compose / stack — não assumir `**uv`** no host.
2. No manifest, opcionalmente `**completaoTargetRef**`, `**completaoHealthUrl**`, `**completaoEngineMode**`, `**completaoSkipEngineImport**` — ver exemplo em `**docs/private.example/homelab/lab-op-hosts.manifest.example.json**`.
3. Na raiz do repo no Windows: `**.\scripts\lab-completao-orchestrate.ps1 -Privileged**` (padrão para completão orientado pelo assistente; omite `**-Privileged**` só se precisar evitar probes privilegiados).
4. Preencher o template privado (**timeouts**, **FP/FN**, **latência**, **confiança**); abrir issues / planos quando houver lacunas de produto.

### 🚀 Estratégia do Lab Completão (v1.7.3+)

Focos de **resiliência** para completão com selo de qualidade de release (dados sintéticos nos exemplos rastreados; caminhos reais só em `**docs/private/`**).

#### A. Higiene de camadas (pre-flight)

- **Check:** Confirmar que não há metadados Git embutidos na raiz de runtime onde o produto deve ir como artefato (ex.: contêiner `**/app`** sem repositório aninhado).
- **Comando:** `[ ! -d /app/.git ]` — código de saída **0** significa **ausência de `.git`** (esperado em árvores estilo imagem). Ajuste `**/app**` se o mount do compose usar outra raiz.

#### B. Matriz de dados de teste

1. **Óbvios positivos:** arquivos `.csv` e `.sql` com **CPFs e padrões de cartão sintéticos** (sem PANs reais).
2. **Falsos positivos (ruído):** logs de sistema (ex. `**/var/log/syslog`**) e blobs binários para exercitar ruído.
3. **Latência de rede:** volume NFS via `**LAB-NODE-03`** para o `**LAB-NODE-04**`, com simulação de atraso via `**tc qdisc**` (documentar a receita exacta de `**tc**` nas notas privadas de sessão).

#### C. Monitoramento de performance

Durante o scan, o agente deve acompanhar:

- **PC dev principal (Win11):** consumo de **RAM** do processo Docker na estação que orquestra.
- **LAB-NODE-04:** **temperatura do SoC** e **I/O wait** (crítico em hardware com pouca margem para não confundir atrasos térmicos ou do cartão SD com defeito do produto).

### 🌐 Matriz de Infraestrutura Heterogênea

**Personas** canônicas (ENT / PRO / edge / bridge), entrypoints Ansible e evidências estão em **[LAB_OP_HOST_PERSONAS.pt_BR.md](LAB_OP_HOST_PERSONAS.pt_BR.md)** ([EN](LAB_OP_HOST_PERSONAS.md)) — atualize essa página quando os papéis do lab mudarem; esta matriz é só **visão rápida**.

| Host                 | SO                  | Runtime (intenção padrão) | Papel no teste |
| -------------------- | ------------------- | ------------------------- | -------------- |
| **PC dev principal** | Win11/WSL2 (Deb 13) | Docker Desktop            | Orquestrador central e scan Windows (`C:\Users\fabio`). |
| **LAB-NODE-02**         | Zorin OS 18 Pro     | **Docker Swarm + Git**    | **PRO/parceiro:** **`uv`** no host, scan de cifras/PII (`/home/leitao/documents`), DBs sintéticas no Swarm. |
| **LAB-NODE-01**              | LMDE 7              | **Podman**                | **Tipo ENT:** validação centrada em contêiner **sem** depender de **`uv`** no metal para “verdade” do produto; shares. |
| **LAB-NODE-03**          | Void Linux          | Podman **opcional** (muitas vezes **`.labop-skip-lab-node-01-podman`**) | **Ponte:** **`curl`** / **`completaoHealthUrl`** / **`--web`** leve para latência; não é segundo gerente Swarm por padrão. |
| **LAB-NODE-04**             | Debian Trixie       | **Nenhum** no metal (NFS/caminhos como **alvo**) | **Edge / sumidouro de sopas:** resiliência e I/O; CLI mínimo **`databoar`** opcional para medir “quão ruim” — ver doc de personas. |

### 🛠️ Geração de configurações dinâmicas (agente)

O agente deve gerar `**config.yaml` temporários** (ou fragmentos a fundir) com base em **[TECH_GUIDE.pt_BR.md](../TECH_GUIDE.pt_BR.md)** e **[USAGE.pt_BR.md](../USAGE.pt_BR.md)** — **nunca** commitar credenciais ou caminhos LAN reais no Git público; manter cópias em `**docs/private/`** ou anexar só excertos sintéticos na transcrição da sessão.

1. **Cenário LAB-NODE-01 (Podman / só contêiner):** montar `config.yaml` para escanear `**/data`** (volume a partir do *share* no LAB-NODE-02 ou mount acordado); injecção típica `podman run … -v /tmp/config.yaml:/app/config.yaml …` (ver [DOCKER_SETUP.pt_BR.md](../DOCKER_SETUP.pt_BR.md)).
2. **Cenário LAB-NODE-02 (Git / Swarm):** modo DB com **nomes de serviço** na overlay; modo ingestão com sopas **sintéticas** apenas.

#### Cenários de teste avançados

1. **Cross-share scan:** LAB-NODE-01 monta *share* do LAB-NODE-02; scan SMB/NFS conforme suportado (notas privadas).
2. **Container soup:** volumes em serviços Swarm (dados sintéticos).
3. **Podman vs Docker:** paridade rootless (LAB-NODE-01) vs Docker/Swarm nos outros hosts, mesma imagem ou `uv` alinhada ao ref de completão.

### 🧠 Cenários de Stress e Heurística

1. **Desafio das Cifras (Falsos Positivos):** O scan em `/home/leitao/documents` no LAB-NODE-02 contém arquivos de música. A heurística deve ser validada para NÃO gerar alertas aqui.
2. **Dados do Mundo Real:** Scan profundo em `/home/leitao` (Linux) e `C:\Users\fabio` (Windows) em busca de PIIs históricas.
3. **Scan de Container Rootless:** No LAB-NODE-01, validar o comportamento do binário dentro do Podman sem dependências locais.

**Verificação de integridade (caminhos):** `/home/leitao` e `C:\Users\fabio` são **perfis de operador** documentados no completão e **exceptuados** no `tests/test_pii_guard.py` para paths públicos; `**/var/log*`* alinha-se ao modelo rastreado [config.lab-fs-varlog.example.yaml](../private.example/homelab/config.lab-fs-varlog.example.yaml) e à seção **Matriz de dados de teste** (logs) acima neste runbook.