# Runbooks do operador (`docs/ops/`)

Esta pasta reúne documentação **procedural** para mantenedor/operador. Documentação de **uso do produto** (`USAGE`, `TESTING`, `DOCKER_SETUP`, etc.) permanece em `[docs/](../README.pt_BR.md)` para não misturar fluxos de usuário da aplicação com material operacional.

**Idiomas:** Cada runbook tem versão em inglês e **pt-BR** (`*.pt_BR.md`). *O histórico de planos em `[docs/plans/](../plans/)` é apenas em inglês.*

## Antes de abrir um PR (operadores)

1. Na raiz: **Windows:** `**.\scripts\check-all.ps1**` (atualiza o dashboard dos planos, pre-commit e pytest completo). **Linux / macOS:** `./scripts/check-all.sh` (mesmo fluxo; **`gatekeeper_audit.py`** por **`uv`**, sem **`pwsh`** obrigatório — **`#560`**`). **Gêmeos finos:** `./scripts/lint-only.sh`, `./scripts/quick-test.sh`, `./scripts/pre-commit-and-tests.sh` — ver **[SCRIPTS_CROSS_PLATFORM_PAIRING.pt_BR.md](SCRIPTS_CROSS_PLATFORM_PAIRING.pt_BR.md)** ([EN](SCRIPTS_CROSS_PLATFORM_PAIRING.md)). Em alternativa manual: `python3 scripts/plans-stats.py --write` (ou `python`), `uv run pre-commit run --all-files`, `uv run pytest -v -W error`.
2. **Não** versionar `**docs/private/`** (inventário real do lab; ignorado pelo git) nem `**git add -f config.yaml**`. Use o modelo versionado `**docs/private.example/**` e a política **[PRIVATE_OPERATOR_NOTES.pt_BR.md](../PRIVATE_OPERATOR_NOTES.pt_BR.md)**.

### Atalho no chat: `pmo-view` (planos / docs estilo PMO, preview Markdown)

**O atalho é só em inglês** (como `**deps`**, `**feature**`, … — ver **[AGENTS.md](../../AGENTS.md)** e `**.cursor/rules/session-mode-keywords.mdc`**). Digite `**pmo-view**` exatamente assim; o resto da mensagem pode ser pt-BR.

No chat do Cursor, diga `**pmo-view**` quando quiser que o assistente **destaque planos e docs PMO** e lembre como lê-los **renderizados** (tabelas, Gantt/Mermaid).

- **Você** abre cada arquivo no editor e usa: **Windows / Linux:** `Ctrl+Shift+V` (Abrir pré-visualização) ou `Ctrl+K` e depois `V` (lado a lado). **macOS:** `Cmd+Shift+V` ou `Cmd+K` e `V`.
- O assistente **não consegue** mudar sua aba para Preview sozinho — é gesto do editor.
- **Arquivos típicos:** `[plans/PLANS_TODO.md](../plans/PLANS_TODO.md)`, [PLANS_DOCUMENTATION_HIERARCHY.pt_BR.md](PLANS_DOCUMENTATION_HIERARCHY.pt_BR.md) ([EN](PLANS_DOCUMENTATION_HIERARCHY.md)), `[plans/SPRINTS_AND_MILESTONES.pt_BR.md](../plans/SPRINTS_AND_MILESTONES.pt_BR.md)` ([EN](../plans/SPRINTS_AND_MILESTONES.md)), `[plans/TOKEN_AWARE_USAGE.md](../plans/TOKEN_AWARE_USAGE.md)`, [COMMIT_AND_PR.pt_BR.md](COMMIT_AND_PR.pt_BR.md) ([EN](COMMIT_AND_PR.md)), [OPERATOR_LAB_DOCUMENT_MAP.pt_BR.md](OPERATOR_LAB_DOCUMENT_MAP.pt_BR.md) ([EN](OPERATOR_LAB_DOCUMENT_MAP.md)), [Corporate-Entity-C_IN_REPO_BASELINE.md](Corporate-Entity-C_IN_REPO_BASELINE.md) (caminhos no repositório para revisores Corporate-Entity-C).

Definido em `**.cursor/rules/session-mode-keywords.mdc`**.

---

## Modo “hoje” (foco de um dia)

Checklists **datados** (`OPERATOR_TODAY_MODE_YYYY-MM-DD.md`), **fila de carryover**, **escada de prontidão de manhã** (Tier A diário; cadência –1 / –1b / –1L) e **sincronização do publicado com `pyproject.toml`** estão em `**[today-mode/](today-mode/README.pt_BR.md)**` — comece por ali em vez de procurar arquivos soltos em `docs/ops/`. Tokens no chat: `**today-mode YYYY-MM-DD**`, **`carryover-sweep`** / **`morning-readiness`** (só em inglês). **Redes sociais + hub (privado):** [today-mode/SOCIAL_PUBLISH_AND_TODAY_MODE.pt_BR.md](today-mode/SOCIAL_PUBLISH_AND_TODAY_MODE.pt_BR.md) ([EN](today-mode/SOCIAL_PUBLISH_AND_TODAY_MODE.md)); token **`social-today-check`**.

---

## Índice

| Tópico                                                                | English                                                                                          | Português (pt-BR)                                                                                            |
| --------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------ |
| SonarQube (home lab, Docker, CI / IDE / MCP)                          | [SONARQUBE_HOME_LAB.md](SONARQUBE_HOME_LAB.md)                                                   | [SONARQUBE_HOME_LAB.pt_BR.md](SONARQUBE_HOME_LAB.pt_BR.md)                                                   |
| Home lab — smoke de deploy e alvos de dados                           | [HOMELAB_VALIDATION.md](HOMELAB_VALIDATION.md)                                                   | [HOMELAB_VALIDATION.pt_BR.md](HOMELAB_VALIDATION.pt_BR.md)                                                   |
| QA com licensing enforced (.lic de 60 dias vinculada à máquina)       | [QA_LOCAL_LICENSE.md](QA_LOCAL_LICENSE.md)                                                       | [QA_LOCAL_LICENSE.pt_BR.md](QA_LOCAL_LICENSE.pt_BR.md)                                                       |
| Lab — APIs externas / DBs read-only (sem segredos no git)             | [LAB_EXTERNAL_CONNECTIVITY_EVAL.md](LAB_EXTERNAL_CONNECTIVITY_EVAL.md)                           | [LAB_EXTERNAL_CONNECTIVITY_EVAL.pt_BR.md](LAB_EXTERNAL_CONNECTIVITY_EVAL.pt_BR.md)                           |
| Completão no lab (runbook, smoke multi-host, contratos)               | [LAB_COMPLETAO_RUNBOOK.md](LAB_COMPLETAO_RUNBOOK.md)                                             | [LAB_COMPLETAO_RUNBOOK.pt_BR.md](LAB_COMPLETAO_RUNBOOK.pt_BR.md)                                             |
| Completão — brief para agente novo (copy-paste)                       | [LAB_COMPLETAO_FRESH_AGENT_BRIEF.md](LAB_COMPLETAO_FRESH_AGENT_BRIEF.md)                         | [LAB_COMPLETAO_FRESH_AGENT_BRIEF.pt_BR.md](LAB_COMPLETAO_FRESH_AGENT_BRIEF.pt_BR.md)                         |
| Time Machine USB — recuperar agora e reaproveitar com segurança       | [TIME_MACHINE_USB_RECOVERY_AND_REPURPOSE.md](TIME_MACHINE_USB_RECOVERY_AND_REPURPOSE.md)         | [TIME_MACHINE_USB_RECOVERY_AND_REPURPOSE.pt_BR.md](TIME_MACHINE_USB_RECOVERY_AND_REPURPOSE.pt_BR.md)         |
| Dossiê de talento (`talent-dossier next`) + snapshot do pool          | [TALENT_DOSSIER_AND_POOL_SYNC.md](TALENT_DOSSIER_AND_POOL_SYNC.md)                               | [TALENT_DOSSIER_AND_POOL_SYNC.pt_BR.md](TALENT_DOSSIER_AND_POOL_SYNC.pt_BR.md)                               |
| Playbook LinkedIn + ATS (SSI, keywords por arquétipo)                 | [LINKEDIN_ATS_PLAYBOOK.md](LINKEDIN_ATS_PLAYBOOK.md)                                             | [LINKEDIN_ATS_PLAYBOOK.pt_BR.md](LINKEDIN_ATS_PLAYBOOK.pt_BR.md)                                             |
| Lab-op — stack mínimo de contêineres (Podman + k3s)                   | [LAB_OP_MINIMAL_CONTAINER_STACK.md](LAB_OP_MINIMAL_CONTAINER_STACK.md)                           | [LAB_OP_MINIMAL_CONTAINER_STACK.pt_BR.md](LAB_OP_MINIMAL_CONTAINER_STACK.pt_BR.md)                           |
| POC de autoavaliação de maturidade (pytest + smoke manual)            | [SMOKE_MATURITY_ASSESSMENT_POC.md](SMOKE_MATURITY_ASSESSMENT_POC.md)                             | [SMOKE_MATURITY_ASSESSMENT_POC.pt_BR.md](SMOKE_MATURITY_ASSESSMENT_POC.pt_BR.md)                             |
| WebAuthn JSON RP — subconjunto pytest (fase 1a)                       | [SMOKE_WEBAUTHN_JSON.md](SMOKE_WEBAUTHN_JSON.md)                                                 | [SMOKE_WEBAUTHN_JSON.pt_BR.md](SMOKE_WEBAUTHN_JSON.pt_BR.md)                                                 |
| Lab-op - baseline de revisao de firewall (publico-safe)               | [LAB_OP_FIREWALL_REVIEW_BASELINE.md](LAB_OP_FIREWALL_REVIEW_BASELINE.md)                         | [LAB_OP_FIREWALL_REVIEW_BASELINE.pt_BR.md](LAB_OP_FIREWALL_REVIEW_BASELINE.pt_BR.md)                         |
| ThinkPad LAB-NODE-01 + LMDE 7 - setup de desenvolvimento (apt, uv, seguranca) | [LMDE7_LAB-NODE-01_DEVELOPER_SETUP.md](LMDE7_LAB-NODE-01_DEVELOPER_SETUP.md)                                     | [LMDE7_LAB-NODE-01_DEVELOPER_SETUP.pt_BR.md](LMDE7_LAB-NODE-01_DEVELOPER_SETUP.pt_BR.md)                                     |
| Windows WSL2 - testes de dev Data Boar (segunda superfície de execução) | [WSL2_DATA_BOAR_DEV_TESTING.md](WSL2_DATA_BOAR_DEV_TESTING.md)                                   | [WSL2_DATA_BOAR_DEV_TESTING.pt_BR.md](WSL2_DATA_BOAR_DEV_TESTING.pt_BR.md)                                                  |
| Grafana Cloud — reativação + primeiros passos seguros                 | [GRAFANA_CLOUD_REACTIVATION.md](GRAFANA_CLOUD_REACTIVATION.md)                                   | [GRAFANA_CLOUD_REACTIVATION.pt_BR.md](GRAFANA_CLOUD_REACTIVATION.pt_BR.md)                                   |
| Ritmo, foco, tokens de sessão (Corporate-Entity-C + caminho demo)                 | [OPERATOR_WORKFLOW_PACE_AND_FOCUS.md](OPERATOR_WORKFLOW_PACE_AND_FOCUS.md)                       | [OPERATOR_WORKFLOW_PACE_AND_FOCUS.pt_BR.md](OPERATOR_WORKFLOW_PACE_AND_FOCUS.pt_BR.md)                       |
| Índice de keywords de sessão + SSH LAB-OP (`lab-op`)                 | [OPERATOR_SESSION_SHORTHANDS.md](OPERATOR_SESSION_SHORTHANDS.md)                                 | [OPERATOR_SESSION_SHORTHANDS.pt_BR.md](OPERATOR_SESSION_SHORTHANDS.pt_BR.md)                                 |
| Mapa de políticas Cursor / agente (Quick index — rules, skills, ops) | [CURSOR_AGENT_POLICY_HUB.md](CURSOR_AGENT_POLICY_HUB.md)                                         | [CURSOR_AGENT_POLICY_HUB.pt_BR.md](CURSOR_AGENT_POLICY_HUB.pt_BR.md)                                         |
| Hub de scripts token-aware (mapa → skills / keywords)               | [TOKEN_AWARE_SCRIPTS_HUB.md](TOKEN_AWARE_SCRIPTS_HUB.md)                                         | [TOKEN_AWARE_SCRIPTS_HUB.pt_BR.md](TOKEN_AWARE_SCRIPTS_HUB.pt_BR.md)                                         |
| Scripts — contrato de pares `.ps1` ↔ `.sh` (Windows / Linux)        | [SCRIPTS_CROSS_PLATFORM_PAIRING.md](SCRIPTS_CROSS_PLATFORM_PAIRING.md)                           | [SCRIPTS_CROSS_PLATFORM_PAIRING.pt_BR.md](SCRIPTS_CROSS_PLATFORM_PAIRING.pt_BR.md)                           |
| PII na árvore pública — guia do operador (Partes I–III; caminhos antigos são redirecionamentos) | [PII_PUBLIC_TREE_OPERATOR_GUIDE.md](PII_PUBLIC_TREE_OPERATOR_GUIDE.md) | [PII_PUBLIC_TREE_OPERATOR_GUIDE.pt_BR.md](PII_PUBLIC_TREE_OPERATOR_GUIDE.pt_BR.md) |
| Ritual de remediação de PII (sob demanda; seeds privados; token `pii-remediation-ritual`) | [PII_REMEDIATION_RITUAL.md](PII_REMEDIATION_RITUAL.md) | [PII_REMEDIATION_RITUAL.pt_BR.md](PII_REMEDIATION_RITUAL.pt_BR.md) |
| Convenções de commit e PR                                             | [COMMIT_AND_PR.md](COMMIT_AND_PR.md)                                                             | [COMMIT_AND_PR.pt_BR.md](COMMIT_AND_PR.pt_BR.md)                                                             |
| GitHub — issue canônica vs duplicata (`gh issue close --duplicate-of`) | [GITHUB_ISSUE_CANONICAL_AND_DUPLICATE_CLOSE.md](GITHUB_ISSUE_CANONICAL_AND_DUPLICATE_CLOSE.md) | [GITHUB_ISSUE_CANONICAL_AND_DUPLICATE_CLOSE.pt_BR.md](GITHUB_ISSUE_CANONICAL_AND_DUPLICATE_CLOSE.pt_BR.md) |
| Fatias finas, faixas de prioridade, handoff do agente (`P0`→`P3`)     | [THIN_SLICE_AGENT_PRIORITY_HANDOFF.md](THIN_SLICE_AGENT_PRIORITY_HANDOFF.md)                     | [THIN_SLICE_AGENT_PRIORITY_HANDOFF.pt_BR.md](THIN_SLICE_AGENT_PRIORITY_HANDOFF.pt_BR.md)                       |
| Follow-ups de workflow (branch protection, SBOM, etc.)                | [WORKFLOW_DEFERRED_FOLLOWUPS.md](WORKFLOW_DEFERRED_FOLLOWUPS.md)                                 | [WORKFLOW_DEFERRED_FOLLOWUPS.pt_BR.md](WORKFLOW_DEFERRED_FOLLOWUPS.pt_BR.md)                                 |
| Instantâneo WRB (bloco para colar no próximo e-mail)                  | [WRB_DELTA_SNAPSHOT_2026-04-16.md](WRB_DELTA_SNAPSHOT_2026-04-16.md)                             | [WRB_DELTA_SNAPSHOT_2026-04-16.pt_BR.md](WRB_DELTA_SNAPSHOT_2026-04-16.pt_BR.md)                             |
| **Modo “hoje”** (índice + carryover + sync do publicado)              | [today-mode/README.md](today-mode/README.md)                                                     | [today-mode/README.pt_BR.md](today-mode/README.pt_BR.md)                                                     |
| Corporate-Entity-C — caminhos baseline no repositório (revisores)                 | [Corporate-Entity-C_IN_REPO_BASELINE.md](Corporate-Entity-C_IN_REPO_BASELINE.md)                                         | — (nota EN; pedidos WRB em [Corporate-Entity-C_WRB_REVIEW_AND_SEND.pt_BR.md](Corporate-Entity-C_WRB_REVIEW_AND_SEND.pt_BR.md))       |
| Bloqueios do secure-by-default + trilha de migração                   | [SECURE_BY_DEFAULT_BLOCKERS_AND_MIGRATION.md](SECURE_BY_DEFAULT_BLOCKERS_AND_MIGRATION.md)       | [SECURE_BY_DEFAULT_BLOCKERS_AND_MIGRATION.pt_BR.md](SECURE_BY_DEFAULT_BLOCKERS_AND_MIGRATION.pt_BR.md)       |
| Revisão de inspiração em segurança (GRC / Security Now)               | [SECURITY_INSPIRATION_GRC_SECURITY_NOW.md](SECURITY_INSPIRATION_GRC_SECURITY_NOW.md)             | [SECURITY_INSPIRATION_GRC_SECURITY_NOW.pt_BR.md](SECURITY_INSPIRATION_GRC_SECURITY_NOW.pt_BR.md)             |
| Hub de inspirações (navegação — comece aqui)                          | [inspirations/INSPIRATIONS_HUB.md](inspirations/INSPIRATIONS_HUB.md)                             | [inspirations/INSPIRATIONS_HUB.pt_BR.md](inspirations/INSPIRATIONS_HUB.pt_BR.md)                             |
| Baseline de inspirações security/GRC (multi-fonte)                    | [inspirations/README.md](inspirations/README.md)                                                 | [inspirations/README.pt_BR.md](inspirations/README.pt_BR.md)                                                 |
| Inspirações de craft de engenharia (pessoas, canais)                  | [inspirations/ENGINEERING_CRAFT_INSPIRATIONS.md](inspirations/ENGINEERING_CRAFT_INSPIRATIONS.md) | [inspirations/ENGINEERING_CRAFT_INSPIRATIONS.pt_BR.md](inspirations/ENGINEERING_CRAFT_INSPIRATIONS.pt_BR.md) |
| Gordon (Docker AI) — fluxo token-aware, sem segredos                  | [GORDON_DOCKER_AI_USAGE.md](GORDON_DOCKER_AI_USAGE.md)                                           | [GORDON_DOCKER_AI_USAGE.pt_BR.md](GORDON_DOCKER_AI_USAGE.pt_BR.md)                                           |
| Pacote para LLM externa (Gemini) — export seguro (git)                | [GEMINI_PUBLIC_BUNDLE_REVIEW.md](GEMINI_PUBLIC_BUNDLE_REVIEW.md)                                 | [GEMINI_PUBLIC_BUNDLE_REVIEW.pt_BR.md](GEMINI_PUBLIC_BUNDLE_REVIEW.pt_BR.md)                                 |
| Cautela com edição por LLM (chat do fornecedor vs scripts validados) | [LLM_AGENT_EDITING_CAUTION.md](LLM_AGENT_EDITING_CAUTION.md)                                   | [LLM_AGENT_EDITING_CAUTION.pt_BR.md](LLM_AGENT_EDITING_CAUTION.pt_BR.md)                                     |
| Recuperação após `cat` / cópia manual de docs                         | [DOC_BUNDLE_RECOVERY_PLAYBOOK.md](DOC_BUNDLE_RECOVERY_PLAYBOOK.md)                               | [DOC_BUNDLE_RECOVERY_PLAYBOOK.pt_BR.md](DOC_BUNDLE_RECOVERY_PLAYBOOK.pt_BR.md)                               |
| Remotes, `origin`, fluxo de fork                                      | [REMOTES_AND_ORIGIN.md](REMOTES_AND_ORIGIN.md)                                                   | [REMOTES_AND_ORIGIN.pt_BR.md](REMOTES_AND_ORIGIN.pt_BR.md)                                                   |
| Limpeza de branches + Docker (remote legado §7)                       | [BRANCH_AND_DOCKER_CLEANUP.md](BRANCH_AND_DOCKER_CLEANUP.md)                                     | [BRANCH_AND_DOCKER_CLEANUP.pt_BR.md](BRANCH_AND_DOCKER_CLEANUP.pt_BR.md)                                     |
| Canais de notificação ao operador                                     | [OPERATOR_NOTIFICATION_CHANNELS.md](OPERATOR_NOTIFICATION_CHANNELS.md)                           | [OPERATOR_NOTIFICATION_CHANNELS.pt_BR.md](OPERATOR_NOTIFICATION_CHANNELS.pt_BR.md)                           |
| Chat → notas duráveis (política de captura de sessão)                 | [OPERATOR_SESSION_CAPTURE_GUIDE.md](OPERATOR_SESSION_CAPTURE_GUIDE.md)                           | [OPERATOR_SESSION_CAPTURE_GUIDE.pt_BR.md](OPERATOR_SESSION_CAPTURE_GUIDE.pt_BR.md)                           |
| Árvore private — Git/VCS local (nunca GitHub)                         | [PRIVATE_LOCAL_VERSIONING.md](PRIVATE_LOCAL_VERSIONING.md)                                       | [PRIVATE_LOCAL_VERSIONING.pt_BR.md](PRIVATE_LOCAL_VERSIONING.pt_BR.md)                                       |
| Operador / TI (permissões mínimas)                                    | [OPERATOR_IT_REQUIREMENTS.md](OPERATOR_IT_REQUIREMENTS.md)                                       | [OPERATOR_IT_REQUIREMENTS.pt_BR.md](OPERATOR_IT_REQUIREMENTS.pt_BR.md)                                       |
| Ajuste prático de identificação agregada (Fase C)                     | [AGGREGATED_IDENTIFICATION_TUNING.md](AGGREGATED_IDENTIFICATION_TUNING.md)                       | [AGGREGATED_IDENTIFICATION_TUNING.pt_BR.md](AGGREGATED_IDENTIFICATION_TUNING.pt_BR.md)                       |
| Resolução de problemas — implantação Docker                           | [TROUBLESHOOTING_DOCKER_DEPLOYMENT.md](TROUBLESHOOTING_DOCKER_DEPLOYMENT.md)                     | [TROUBLESHOOTING_DOCKER_DEPLOYMENT.pt_BR.md](TROUBLESHOOTING_DOCKER_DEPLOYMENT.pt_BR.md)                     |

**Relacionado (fora desta pasta):** [SECURITY.md](../SECURITY.md) / [SECURITY.pt_BR.md](../SECURITY.pt_BR.md) e [CODE_PROTECTION_OPERATOR_PLAYBOOK.md](../CODE_PROTECTION_OPERATOR_PLAYBOOK.md) / [CODE_PROTECTION_OPERATOR_PLAYBOOK.pt_BR.md](../CODE_PROTECTION_OPERATOR_PLAYBOOK.pt_BR.md) — postura de segurança e endurecimento **Priority band A**, listados junto da política principal em `[docs/README.pt_BR.md](../README.pt_BR.md)`.

### Scripts auxiliares opcionais (`scripts/`)

| Script                                                           | Finalidade                                                                                                                                                                                                                                                                                                                                                                                                                    |
| ---------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `[poll_dashboard_scan.py](../../scripts/poll_dashboard_scan.py)` | Faz POST em `/scan`, consulta `/status` até ocioso e sugere download do relatório. `**DATA_BOAR_BASE`** ou `**--base**`; opcional `**DATA_BOAR_API_KEY**` / `**--api-key**` com `require_api_key`; `**--interval**` / `**--max-polls**` para ajustar espera. `**uv run python scripts/poll_dashboard_scan.py --help**`. Por **[AGENTS.md](../../AGENTS.md)**, não versionar hostname nem chave—só env ou `**docs/private/`**. |
| `[git-progress-recap.ps1](../../scripts/git-progress-recap.ps1)` | **Ritmo token-aware:** agrupa commits recentes de `**origin/main`** por **data** (padrão **3** dias; `**-Days 7`**, `**-MaxPerDay**`, `**-NoFetch**`). Ver [OPERATOR_WORKFLOW_PACE_AND_FOCUS.pt_BR.md](OPERATOR_WORKFLOW_PACE_AND_FOCUS.pt_BR.md) §8 ([EN](OPERATOR_WORKFLOW_PACE_AND_FOCUS.md)). Complementa `**today-mode**`, `**carryover-sweep**`, `**eod-sync**` — não substitui `PLANS_TODO.md`.                        |
| `[smoke-maturity-assessment-poc.ps1](../../scripts/smoke-maturity-assessment-poc.ps1)` | Subconjunto **pytest** rápido para o POC de autoavaliação de maturidade (portão 1 em [SMOKE_MATURITY_ASSESSMENT_POC.pt_BR.md](SMOKE_MATURITY_ASSESSMENT_POC.pt_BR.md)). **Não** substitui `**check-all**` antes do merge. |

---

## Checklist de auditoria de links (após mover ou renomear docs)

Use ao abrir um PR do tipo **docs: cluster ops runbooks under docs/ops**.

- **[README.md](../README.md)** / **[README.pt_BR.md](../README.pt_BR.md)** — tabelas em **Uso** / **Interno** e ponteiros a **ops/**.
- **Raiz [CONTRIBUTING.md](../../CONTRIBUTING.md)** — caminhos `docs/…` afetados.
- `**[.cursor/rules/](../../.cursor/rules/)`** e `**[.cursor/skills/](../../.cursor/skills/)**` — links para `docs/` ou `docs/ops/`.
- **Links entre docs** dentro dos arquivos movidos (`../`, `ops/`, `plans/`).
- `**docs/plans/*.md`** — links relativos de `plans/` para `../ops/…` ou `../CODE_PROTECTION…`.
- **Opcional:** `rg` pelo **caminho antigo** e corrigir resíduos.

**Não** alterar `.github/`, `sonar.sources` nem a disposição de **SECURITY** / **CONTRIBUTING** na raiz, salvo objetivo explícito; preferir só atualização de links.

**Automatização:** `uv run pytest tests/test_docs_markdown.py tests/test_markdown_lint.py`
