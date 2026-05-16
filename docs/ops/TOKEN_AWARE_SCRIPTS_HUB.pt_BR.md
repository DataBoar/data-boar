# Hub de scripts token-aware (mapa + cobertura)

**English:** [TOKEN_AWARE_SCRIPTS_HUB.md](TOKEN_AWARE_SCRIPTS_HUB.md)

**Objetivo:** Um índice da **automação do repositório** em **`scripts/`** (sobretudo **`.ps1`** no Windows; **`.sh` em par** para *gates* no Linux/macOS — ver **[`SCRIPTS_CROSS_PLATFORM_PAIRING.pt_BR.md`](SCRIPTS_CROSS_PLATFORM_PAIRING.pt_BR.md)**) e como cada área liga a **skills**, **regras**, **palavras-chave de sessão** e **runbooks** — para reutilizar trabalho anterior em vez de redescobrir scripts a cada sessão.

**Não substitui:** **`.cursor/skills/token-aware-automation/SKILL.md`** (comandos do dia a dia) nem **`.cursor/rules/session-mode-keywords.mdc`** (tokens de chat). Este arquivo responde: *“o que mais existe, e onde está documentado?”*

**Ritual do assistente:** **`.cursor/rules/repo-scripts-wrapper-ritual.mdc`** (`alwaysApply: true`) — folhear este hub antes de reinventar shell longo; usar **`scripts/*.ps1`** acordados; se um wrapper falhar, **avisar o operador** (instalação/montagem/PATH) em vez de “esquecer” a automação em silêncio.

**Chat novo / pouco contexto:** leia primeiro **[OPERATOR_AGENT_COLD_START_LADDER.pt_BR.md](OPERATOR_AGENT_COLD_START_LADDER.pt_BR.md)** ([EN](OPERATOR_AGENT_COLD_START_LADDER.md)) — escada ordenada + router de tarefas para abrir *este* hub depois de saber qual família de scripts importa.

---

## 1. Caminho de ouro (quase toda sessao)

| Script | Função | Ligado a |
| ------ | ---- | -------- |
| `check-all.ps1` | Gate completo (Windows) | SKILL **`token-aware-automation`**, **`.cursor/rules/check-all-gate.mdc`**, `CONTRIBUTING.md`, **[`SCRIPTS_CROSS_PLATFORM_PAIRING.pt_BR.md`](SCRIPTS_CROSS_PLATFORM_PAIRING.pt_BR.md)** |
| `check-all.sh` | Gate completo (Linux / macOS; bash) — mesmos passos de **`check-all.ps1`**; **`pwsh`** opcional para `gatekeeper-audit.ps1` | Igual a **`check-all.ps1`** |
| `lint-only.ps1` | So lint/format | Igual + doc de pares |
| `lint-only.sh` | Igual (Linux / macOS) | Igual |
| `quick-test.ps1` | Pytest focado | Igual + doc de pares |
| `quick-test.sh` | Igual (Linux / macOS) | Igual |
| `pre-commit-and-tests.ps1` | *Pre-commit* + *pytest* completo (fino; sem *gatekeeper*) | **`check-all.ps1`** delega aqui |
| `pre-commit-and-tests.sh` | Igual (Linux / macOS) | Doc de pares |
| `preview-commit.ps1`, `commit-or-pr.ps1`, `create-pr.ps1` | Commit / PR | Igual + **`docs/ops/COMMIT_AND_PR.md`** |
| `pr-merge-when-green.ps1` | Merge com CI verde | **`.cursor/rules/agent-autonomous-merge-and-lab-ops.mdc`**, SKILL **`autonomous-merge-and-lab`** |
| `safe-workspace-snapshot.ps1` | Snapshot pre-commit | Palavra-chave **`safe-commit`** |
| `smoke-maturity-assessment-poc.ps1` | Subconjunto pytest rapido (gate 1 do POC de maturidade) | [PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md](../plans/PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md), [SMOKE_MATURITY_ASSESSMENT_POC.md](SMOKE_MATURITY_ASSESSMENT_POC.md) |

### 1b. Contrato YAML do GitHub Actions (pytest — não fica em `scripts/`)

| Artefato | Como rodar | Ligado a |
| -------- | ---------- | -------- |
| **[`tests/test_github_workflows.py`](../../tests/test_github_workflows.py)** | **`.\scripts\quick-test.ps1 -Path tests/test_github_workflows.py`** (ou **`check-all`**) · **`./scripts/quick-test.sh --path tests/test_github_workflows.py`** | **[`.github/workflows/ci.yml`](../../.github/workflows/ci.yml)** roda **`uv run pytest`** na **suíte completa** (este módulo entra sempre); **[ADR 0005](../adr/ADR-0005-ci-github-actions-supply-chain-pins.md)**; **[`OPERATOR_NOTIFICATION_CHANNELS.pt_BR.md`](OPERATOR_NOTIFICATION_CHANNELS.pt_BR.md)** §4.1 / §4.1.1; **[`TESTING.pt_BR.md`](../TESTING.pt_BR.md)** |

**Use depois de:** mudanças em **`.github/workflows/*.yml`** (Slack, pins / job de lint do `ci.yml`, Semgrep, Gitleaks, SBOM, Dependabot sync, zizmor) — feedback rápido sem rodar toda a matriz de testes do produto.

### 1a. CLI rápida no Windows (conteúdo / tail / preview)

| Script | Função | Ligado a |
| ------ | ---- | -------- |
| `repo-grep.ps1` | Busca em conteúdo: **`rg`**, opcional **`baregrep`** (`-PreferBareGrep`; também **`Downloads`**) | **`docs/ops/WINDOWS_FAST_CLI_WRAPPERS.pt_BR.md`**, **`.cursor/rules/repo-scripts-wrapper-ritual.mdc`** |
| `repo-tail.ps1` | Ultimas **N** linhas: **`tail.exe`** do Git, senão **`Get-Content -Tail`** | Igual |
| `repo-view.ps1` | Preview com teto: **`bat`** / **`batcat`**, senão **`Get-Content`** | Igual |

---

## 2. PII / árvore pública / estação principal de desenvolvimento

| Script | Função | Ligado a |
| ------ | ---- | -------- |
| `pii-fresh-clone-audit.ps1` | Clone fresco + guards (Windows) | SKILL **`pii-fresh-clone-audit`**, **`docs/ops/PII_FRESH_CLONE_AUDIT.md`**, **`pii-fresh-audit`**, **`PRIMARY_WINDOWS_WORKSTATION_PROTECTION.md`** |
| `new-b2-verify.ps1` | Auditoria de segmento de path de usuario | **`docs/ops/PII_PUBLIC_TREE_OPERATOR_GUIDE.md`** |
| `run-pii-local-seeds-pickaxe.ps1` | Pickaxe sobre seeds locais | **`docs/private.example/scripts/README.md`**, guia PII |
| `run-pii-history-rewrite.ps1` | Reescrita de histórico (perigoso) | Guia PII Parte II — **não** rotina no PC Windows principal de desenvolvimento; **`PRIMARY_WINDOWS_WORKSTATION_PROTECTION.md`** |
| `es-find.ps1` | Busca por nome (**`es.exe`**, opcional **`-FallbackPowerShell`**) | SKILL **`everything-es-search`**, **`docs/ops/EVERYTHING_ES_PRIMARY_WINDOWS_DEV_LAB.md`**, **`es-find`** |
| `social-x-pace-remind.ps1` | Linhas X em atraso vs `SOCIAL_HUB.md` (privado); Slack opcional | **`x-pace-check`**, **`x-posted`**; **`OPERATOR_NOTIFICATION_CHANNELS.md`** §6; privado **`OPERATOR_X_PACE_AND_VALIDATION.pt_BR.md`** |
| `social_x_thread_lengths.py` | Valida blocos em crases sob `## Thread pronta` em `2026*_x_*.md` (máx. 279 por padrão) | Privado **`SOCIAL_HUB.md`**, **`X_PLATFORM_LIMITS_AND_PREMIUM.pt_BR.md`**; `uv run python scripts/social_x_thread_lengths.py` |

---

## 3. Homelab, lab-op, energia, rede

| Script | Função | Ligado a |
| ------ | ---- | -------- |
| `lab-op.ps1` | SSH report / sync-collect | **`docs/ops/LAB_OP_SHORTHANDS.md`**, **`lab-op-systems-context.mdc`** |
| `lab-op-sync-and-collect.ps1` | Batch multi-host | SKILL **`autonomous-merge-and-lab`**, manifest privado |
| `lab-completao-inventory-preflight.ps1` | Verificação de idade dos privados **`LAB_SOFTWARE_INVENTORY.md`** / **`OPERATOR_SYSTEM_MAP.md`**; opcional **`lab-op-sync-and-collect.ps1`** | **`LAB_COMPLETAO_RUNBOOK.pt_BR.md`** (*Frescura do inventário*); o **`lab-completao-orchestrate.ps1`** chama por padrão |
| `lab-completao-orchestrate.ps1` | Completão no lab (preflight + opcional **`lab-op-git-ensure-ref`** quando **`completaoTargetRef`** / **`-LabGitRef`** + YAML opcional de **contrato de dados** quando **`completaoDataContractsPath`** + preflight só de leitura **`docker`/`podman` `image inspect`** quando **`completaoImageRefs`** + smoke SSH por host + HTTP opcional; gera **`completao_*_orchestrate_events.jsonl`**, **`lab_result.json`** com **`audit_trail`** + **`exit_code_semantic`**, opcional **`GRC_EXECUTIVE_REPORT.json`** via **`scripts/generate_grc_report.py`**, **`exit`** semântico **0**/**1** no caminho feliz) | **`LAB_COMPLETAO_RUNBOOK.pt_BR.md`** (*Eventos estruturados*, *Preflight de contrato de dados*, *Telemetria por exit code*), **[ADR 0041](../adr/ADR-0041-lab-completao-data-contract-preflight.md)**, manifest **`completaoTargetRef`**, **`completaoHealthUrl`**, **`completaoDataContractsPath`**, **`completaoImageRefs`**, **`completaoImageProbeSshHost`**, **`-SkiColleague-KagePreflight`**, opcional **`completaoEngineMode`:** **`container`** / **`completaoSkipEngineImport`** |
| `lab-completao-orchestrate-hybrid-v173.ps1` | Caminho opcional alta densidade (config efêmera + **`docker`/`podman` run`**); **salta o run** se a imagem não existir no nó; **`completao_hybrid_*_events.jsonl`** | **`LAB_COMPLETAO_RUNBOOK.pt_BR.md`** (*Eventos estruturados*); invocado por **`lab-completao-orchestrate.ps1 -HybridLabOpHighDensity173`** |
| `run-benchmark.ps1` + `benchmark_sqlite_diff.py` | *Harness* A/B opcional: duas execuções cronometradas de **`lab-completao-orchestrate.ps1`** (**`-LabGitRef`**, ex.: **`v1.7.3`** vs **`origin/main`**), cópia opcional de SQLite (**`-SqlitePath`**), **`data-boar-report`** opcional após a 2ª rodada, gera **`bench/COMPARISON.log`**; o Python compara dois SQLite quando existem **`bench/v1.7.3/results.db`** e **`bench/v1.7.4/results.db`** | **`LAB_COMPLETAO_RUNBOOK.pt_BR.md`** (*Target git ref*); pasta **`bench/`** no `.gitignore` |
| `benchmark-ab.ps1` | A/B com **Git** no clone do dev: bloqueio de árvore suja (**`-AutoStash`** / **`-AllowDirty`**), **`git checkout`** na tag legada e **`lab-completao-orchestrate.ps1`**, volta ao branch/HEAD, segunda passagem do completão, copia/move logs (SQLite opcional / **`data-boar-report`**) em **`benchmark_runs/`**, grava **`benchmark_runs/times.txt`** com totais do **`Measure-Command`** | **`LAB_COMPLETAO_RUNBOOK.pt_BR.md`** (*Target git ref*; *blast radius* do PC dev: só checkout normal); pasta **`benchmark_runs/`** no `.gitignore` |
| `lab_completao_data_contract_check.py` | Valida colunas obrigatórias na BD a partir de contrato YAML (URL SQLAlchemy só via variável de ambiente); falha rápido antes do smoke SSH por host; códigos de saída **`DATA_BOAR_COMPLETAO_EXIT_v1`** (**0** ok, **1** infra/alcance à BD, **2** esquema/YAML, **3** reservado) | **`LAB_COMPLETAO_RUNBOOK.pt_BR.md`** (*Data contract preflight*, *Telemetria por exit code*), **`docs/private.example/homelab/completao_data_contracts.example.yaml`**; **`uv run python scripts/lab_completao_data_contract_check.py --contracts <caminho>`** |
| `completao-chat-starter.ps1` | Imprime linhas mínimas para o chat (**`completao`** + **`tier:…`**, mais **`semver:`** / **`tag:`** no *tier* **`release-master`**) + comando sugerido; **`release-master -ReleaseSemver X.Y.Z`** para outras tags | **`COMPLETAO_OPERATOR_PROMPT_LIBRARY.pt_BR.md`**, **`COMPLETAO_MESTRE_RELEASE_CHECKLIST_PROMPT*.md`**, **`LAB_COMPLETAO_FRESH_AGENT_BRIEF.pt_BR.md`** (blocos A–E completos quando a prosa muda) |
| `maestro-deep-rc-monitor-collect.ps1` | Sessão de lab em um comando: **`scripts/maestro/Maestro.ps1 -Deep`**, loop opcional de **`Get-LabStatus`** (padrão **15** x **20s**), **`Maestro.ps1 -Collect`**; **`-SkipMonitor`**, **`-SkipCollect`**, **`-ClearHostEachLoop`**; **`Ref`** repassado ao Maestro; código de saída = maior não zero dos filhos (o preflight de imagem/tar no Maestro ainda pede **Docker**/**Podman** local no Windows quando esse caminho roda) | **`scripts/maestro/Maestro.ps1`**, privado **`docs/private/homelab/data/inventory.json`**, **`LAB_COMPLETAO_RUNBOOK.pt_BR.md`**, **`tests/config/benchmark-rc.yaml`**, **`tests/test_maestro_scripts.py`** |
| `lab-op-git-ensure-ref.ps1` | Verificar ou alinhar clones LAB a tag / **`origin/main`** / ponta de branch | **`LAB_COMPLETAO_RUNBOOK.pt_BR.md`**; invocado por **`lab-completao-orchestrate.ps1`** quando há ref alvo |
| `collect-homelab-report-remote.ps1`, `run-homelab-host-report-all.ps1` | Reports remotos | **`HOMELAB_VALIDATION.md`**, manifest privado |
| `lab-allow-data-boar-inbound.ps1`, `lab-allow-data-boar-inbound.sh` | Liberar firewall de lab (TCP 8088) Windows / Linux | **`DATA_BOAR_LAB_SECURITY_TOOLING.pt_BR.md`** |
| `lab-env-load.ps1` | Dot-source env para probes | **`lab-op-systems-context.mdc`** §3 |
| `growatt.ps1`, `enel.ps1`, `energy-report.ps1` | Solar / rede / correlação | SKILL **`homelab-lab-op-data`**, **`solar-snap`**, **`enel-check`**, **`energy-report`**, **`LAB-ROUTER-01-scan`** |
| `growatt-session-collect.ps1`, `enel-session-collect.ps1` | Janela de sessão | SKILL **`session-aware-collect`**, **`session-collect`** |
| `LAB-ROUTER-01.ps1`, `snmp-LAB-ROUTER-01-lab-probe*.ps1`, `LAB-ROUTER-01-api-*.ps1` | UniFi / LAB-ROUTER-01 | SKILL **`homelab-lab-op-data`**, **`LAB-ROUTER-01-scan`** |
| `windows-dev-report.ps1` | Inventário do PC dev | Matriz homelab em **`docs/ops/`** |

### JSON executivo GRC (CLIs Python)

| Script | Função | Ligado a |
| ------ | ------ | -------- |
| `generate_grc_report.py` | Monta JSON ``data_boar_grc_executive_report_v1`` (*hook* de lab; *raw scan* opcional + ``lab_result.json``) | **`LAB_COMPLETAO_RUNBOOK.md`**, **[`REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md`](../REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md)**, **[`GRC_EXECUTIVE_REPORT_SCHEMA.pt_BR.md`](../GRC_EXECUTIVE_REPORT_SCHEMA.pt_BR.md)** |
| `export_reports.py` | Planilha XLSX de remediação + PDF executivo a partir do mesmo JSON v1 | **`report/grc_export_multiformat.py`**, esquema + exemplo em **`schemas/`** |

### Entry points de console do produto (PyPI `[project.scripts]`)

| Comando | Função | Ligado a |
| ------- | ------ | -------- |
| `data-boar` | CLI / API principal (`main.py`) | **[`USAGE.pt_BR.md`](../USAGE.pt_BR.md)** |
| `data-boar-report` | Markdown executivo a partir da sessão no **SQLite local** (`cli.reporter`); não abre conector SQL ao vivo | **[`USAGE.pt_BR.md`](../USAGE.pt_BR.md)** (*Resumo executivo*) · [EN](../USAGE.md), seção 5 |

---

## 4. Talent / ATS (maioria em `docs/private/commercial/`)

| Script | Função | Ligado a |
| ------ | ---- | -------- |
| `talent.ps1` | CLI do pool | SKILL **`candidate-ats-evaluation`**, **`TALENT_SHORTHAND_HUB.pt_BR.md`** (privado) |
| `candidate-dossier-scaffold.ps1` | Scaffold de dossier | **`talent-dossier`** |
| `ats.ps1`, `ats-candidate-import.ps1`, `ats-hub-export.ps1`, `ats-profile.ps1` | Helpers ATS | Mesma skill; alinhar com **`talent.ps1`** ao escolher entry point |
| `normalize_pool_sync_snapshot.ps1` | Higiene de texto da tabela snapshot | **`talent-pool-sync`** |
| `generate_pool_sync_snapshot.py` | Gera markdown de snapshot | Fluxo do pool (ver hub privado) |
| `generate_talent_playbooks_v2.py` | Playbooks v2 LinkedIn (MD + export pandoc) | Privado **`linkedin_peer_review/individual/v2/`** + **`ats_sli_hub/exports/v2/`** — ver **`docs/private.example/commercial/ats_sli_hub/exports/README.md`** |

*Palavras-chave de sessão:* **`talent-dossier`**, **`talent-ats`**, **`talent-pool-sync`**, **`talent-map`**, **`talent-brief`**, **`talent-status`** — ver **`session-mode-keywords.mdc`**.

---

## 5. Git / higiene / release

| Script | Função | Ligado a |
| ------ | ---- | -------- |
| `git-progress-recap.ps1`, `progress-snapshot.ps1` | Progresso / recap | Ritual do operador; **`eod-sync`** / **`git-pr-sync-before-advice.mdc`** |
| `git-cleanup-merged-gone-branches.ps1` | Limpeza de branches | **`docs/ops/BRANCH_AND_DOCKER_CLEANUP.md`**, modo **`houseclean`** |
| `pr-hygiene-remind.ps1` | Lembrete de PR | **`houseclean`**, PRs abertos |
| `recovery-doc-bundle-sanity.ps1` | Recuperação de bundle de docs | **`check-all-gate.mdc`**, **`DOC_BUNDLE_RECOVERY_PLAYBOOK.md`** |
| `new-adr.ps1` | Scaffold de ADR | **`AGENTS.md`**, **`docs/adr/README.md`** |
| `pre-commit-and-tests.ps1` | Wrapper fino | Preferir **`check-all.ps1`** salvo subset necessario |
| `gatekeeper-audit.ps1` | Seeds PII vs **só paths em staging** (`git diff --cached --name-only` + `git grep -F -f`); remove seeds de identidade pública (**FabioLeitao**, **`C:\Users\fabio`**, **`/home/leitao`**) antes do grep; primeiro gate em **`check-all.ps1`** | **`PII_LOCAL_SEEDS.txt`** (privado), **`PII_REMEDIATION_RITUAL.md`** |
| `private-git-sync.ps1` | Repo privado empilhado (`-Push`: **`lab-*`** + bare opcional **`notes-sync.git`** no VeraCrypt (**`Z:`** primeiro, **`Y:`** fallback) + mirror em **`P:`** se montado) | **`docs/ops/PRIVATE_LOCAL_VERSIONING.md`**, **`PRIVATE_STACK_SYNC_RITUAL.md`**, sessao **`private-stack-sync`**, **`PRIVATE_OPERATOR_NOTES.md`**, **ADR 0040**, **`operator-evidence-backup-no-rhetorical-asks.mdc`** |
| `license-smoke.ps1`, `version-readiness-smoke.ps1`, `release-integrity-check.ps1` | Checks de release | **`docs/releases/`**, **`VERSIONING.md`** |
| `generate-sbom.ps1` | SBOM | **`WORKFLOW_DEFERRED_FOLLOWUPS.md`**, docs de seguranca |
| `gitlab-mirror-health-check.ps1` | Saúde do mirror | **`GITLAB_GITHUB_MIRROR.md`** |
| `docker-lab-build.ps1`, `docker-hub-pull.ps1`, `docker-prune-local.ps1`, `docker-scout-critical-gate.ps1` | Docker lab / Hub / Scout | SKILL **`docker-smoke-container-hygiene`**, **`token-aware-automation`** |

---

## 6. Dia do operador / sessao / iCloud

| Script | Função | Ligado a |
| ------ | ---- | -------- |
| `operator-day-ritual.ps1` | Manha / fim do dia | **`carryover-sweep`**, **`eod-sync`** |
| `session-collect.ps1` | Janela de cookies / sessao | SKILL **`session-aware-collect`**, **`session-collect`** |
| `icloud-photos-fetch-range.ps1` | Fetch iCloud por intervalo | Linha **`session-collect`** (iCloud) |

---

## 7. Nicho / avançado (usar quando a tarefa combinar)

| Script | Funcao | Nota |
| ------ | ---- | ---- |
| `external-review-pack.ps1` | Pacote para revisão externa | **`feedback-inbox`**, **`GEMINI_PUBLIC_BUNDLE_REVIEW.md`** |
| `auto-mode-session-pack.ps1` | Pacote de sessao | Experimentos de workflow |
| `lab-node-01-ansible-baseline.ps1` | Baseline Ansible | Provisionamento (detalhes privados) |
| `lab-node-01-ansible-labop-podman-apply.sh` | Ansible só Podman (args fixos no sudoers) | Via `sudo -n` + `LABOP_ANSIBLE_PODMAN` estreito; ver **LAB_OP_PRIVILEGED_COLLECTION.pt_BR.md** |
| `unifi-ssh-deep-audit.ps1` | SSH profundo UniFi | Alto sinal; LAN — só notas **privadas** |
| `linkedin-review-batch.ps1` | Batch LinkedIn | Talent / social; saídas privadas |
| `gh-ensure-default.ps1` | Branch default no GitHub | Setup pontual |

---

## 8. Economia privada do operador (não é automação de produto)

Scripts como **`household-finance.ps1`**, **`claro.ps1`**, **`aguas.ps1`**, **`leste.ps1`** são fluxos **só do operador**; não precisam de skills Cursor. Uso e saídas em **`docs/private/`** / cofre — não em PRs ou evidência rastreada.

---

## 9. Lacunas de cobertura (próximos passos — sem explodir tokens)

| Lacuna | Sugestao |
| --- | --- |
| **`new-b2-verify.ps1`** fora da tabela do SKILL **`token-aware-automation`** | Uma linha apontando para **`PII_PUBLIC_TREE_OPERATOR_GUIDE.md`** (opcional). |
| **`operator-day-ritual.ps1`** so via palavras-chave | Suficiente; este hub so liga. |
| **Divisao ATS** (`ats*.ps1` vs `talent.ps1`) | Documentar entry point preferido no SKILL **`candidate-ats-evaluation`** na proxima mudanca ATS. |
| **Trio de release** | Mini-tabela opcional em **`docs/releases/`** — nao nova palavra-chave de sessao. |
| **`talent-pool-sync`** e scripts do pool | Texto da keyword alinhado a **`generate_pool_sync_snapshot.py`** + **`normalize_pool_sync_snapshot.ps1`** (**`session-mode-keywords.mdc`**). |

**Política:** **`OPERATOR_WORKFLOW_PACE_AND_FOCUS.md`** §3 — evitar muitos tokens novos; preferir **`backlog` + item nomeado** ou este **hub** para descoberta.

---

## Relacionado

- **`.cursor/skills/token-aware-automation/SKILL.md`**
- **`docs/plans/TOKEN_AWARE_USAGE.md`**
- **`docs/ops/OPERATOR_SESSION_SHORTHANDS.md`**
