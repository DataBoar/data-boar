# “Today mode” do operador — 2026-03-27 (dia inteiro)

**English:** [OPERATOR_TODAY_MODE_2026-03-27.md](OPERATOR_TODAY_MODE_2026-03-27.md)

**Objetivo:** Um **dia completo** em **superfícies de operador + alinhamento docs/código** — não só os primeiros 10 minutos. O **PR de recuperação de docs** já foi **fundido** em `main`; começa por **carryover + Slack**, depois os blocos técnicos.

**Abre este arquivo primeiro** ao sentar-te (**`today-mode 2026-03-27`**). Atalhos em inglês para limites do dia: **`carryover-sweep`** (manhã) e **`eod-sync`** (fim do dia) — ver **`scripts/operator-day-ritual.ps1`** e **`.cursor/rules/session-mode-keywords.mdc`**.

---

## Bloco 0 — Primeiro (≈ 20–40 min): carryover + o Slack tem que te avisar

### 0a — Limpar pendências de “today mode” antigos (sem backlog imortal)

- Abre **[OPERATOR_TODAY_MODE_2026-03-26.pt_BR.md](OPERATOR_TODAY_MODE_2026-03-26.pt_BR.md)** — o que ainda não estiver feito (ex.: **e-mail Corporate-Entity-C WRB**, **branch protection** opcional, **prova de ping no Slack**). **Release `v1.6.7`** já está no **GitHub** (Latest) e no **Docker Hub** (`:1.6.7`, `:latest`, **2026-03-26**) — ver a **seção Atualização** nesse arquivo; não voltar a listar tag/Hub como manual salvo republicação. Ou **fazes hoje**, ou **passas para uma linha no PLANS / issue**, ou **adias com data explícita** — não deixes **sem dono para sempre**.
- Hábito semanal opcional: rever **todos** os `docs/ops/today-mode/OPERATOR_TODAY_MODE_*.md` ainda pertinentes; nota privada **`docs/private/TODAY_MODE_CARRYOVER_AND_FOUNDER_RHYTHM.md`** explica ritmo **diário** vs **checkpoint do founder**.

### 0b — Notificações Slack (obrigatório antes de confiar em “te avisaram”)

- **Problema:** canal privado + PC com a app aberta **não chega** se **Windows** e **iPhone** **nunca** mostram alerta — não vês sinais do agente/CI no **canal B**.
- **Faz:** lê **[OPERATOR_NOTIFICATION_CHANNELS.pt_BR.md](../OPERATOR_NOTIFICATION_CHANNELS.pt_BR.md)** (e o EN se precisares) e **prova** entrega: **teste** no canal, confirma **definições de notificação** (app + SO: Focus/DND, alertas no Slack móvel) e verifica o fluxo **“Slack operator ping (manual)”** / falha de CI se estiver configurado. **Meta:** **um** alerta real no **telefone** e no **PC** que tu **notas**.
- **Segredos** só em GitHub Actions / env — **nunca** colar webhooks no chat ou em docs rastreados.

---

## Hoje (2026-03-27) — blocos técnicos (depois do Bloco 0)

### Bloco A — Portão help-sync (≈ 45–90 min)

- Corre **`uv run pytest tests/test_operator_help_sync.py -v`** na raiz do repo.
- Relê **`docs/OPERATOR_HELP_AUDIT.md`** — trata **Follow-ups** como **backlog do dia**, não rodapé.
- Se verde: anota data da corrida numa linha privada em **`docs/private/GEMINI_WORKFLOW_ROI_AND_HELP_SYNC_PREP.md`** ou no teu diário; se vermelho: corrige **código ou manifesto primeiro**, depois superfícies (USAGE, man, `/help`).

### Bloco B — OpenAPI vs corpos reais (≈ 90–120 min)

- **Meta:** fechar ou encolher o item do audit: texto OpenAPI / Swagger vs **`POST /scan`** (e relacionados) como está em **`api/routes`**.
- **Entrega:** pequenas edições rastreadas em doc ou descrição OpenAPI **ou** um issue único com lacunas intencionais (com ponteiros para o código).

### Bloco C — README e exposição (`--host`) (≈ 30–45 min)

- **Meta:** README + **`.pt_BR.md`**: quando falares de LAN / sem Docker, aparece **`--host`** (e ligação ao USAGE) sem obrigar o leitor a adivinhar o default de loopback.
- **Cruzado:** bullets em SECURITY/DEPLOY ainda batem com **`core/host_resolution.py`**.

### Bloco D — Espreitar `/help` web (≈ 30 min)

- Leitura rápida de **`api/templates/help.html`** vs **`main.py`** (argparse) para flags **recentes** (transporte, API key, opções de scan). Não é duplicar tudo — é **evitar contradições**.

### Bloco E — Dry-run ferramentas de recuperação (≈ 15–30 min, opcional)

- **`.\scripts\recovery-doc-bundle-sanity.ps1`** (sem bundle) — confirma o conjunto de testes de compilação dos scripts.
- Se guardares concat privado: uma corrida **`--sweep-windows`** para tranquilidade ([DOC_BUNDLE_RECOVERY_PLAYBOOK.pt_BR.md](../DOC_BUNDLE_RECOVERY_PLAYBOOK.pt_BR.md)).

### Bloco F — Planos / banda A fino (≈ 30–45 min, opcional)

- Espreita **`docs/plans/PLANS_TODO.md`** banda **–1 / –1b**; **não** abrir espiral de feature nova — **uma** checkbox ou promoção a issue se for óbvio.

---

## Critério de paragem

O dia está “fechado” quando: o **Bloco 0** tem **prova de ping no Slack** ou **nota/issue/PLANS** clara para o que falta; **pendências de today modes anteriores** não estão invisíveis; e **pytest help-sync verde**, **follow-up OpenAPI avançado** (doc fundida ou issue fechada em âmbito), **callout `--host` no README** feito ou **adiado** com ponteiro em **PLANS_TODO** / issue.

---

## Registo de conclusão — 2026-03-27 (parcial)

| Bloco | Estado | Notas |
| ----- | ------ | ----- |
| **A** Help-sync | Feito | `uv run pytest tests/test_operator_help_sync.py -v` — tudo verde. |
| **B** OpenAPI vs `/scan` | Feito | [OPERATOR_HELP_AUDIT.md](../../OPERATOR_HELP_AUDIT.md) Follow-ups: `ScanStartBody` em `api/routes.py` + verificação em `/docs` com o servidor a correr. |
| **C** README `--host` | Já cumprido | Quick start com `--host` + loopback; ver audit “Done recently”. |
| **D** Web `/help` | N/A | Sem flags CLI novas desde o passe de 2026-03-25; novo re-diff quando houver flags. |
| **E** Script de recuperação | Feito | `.\scripts\recovery-doc-bundle-sanity.ps1` verde; linha **Tip** corrigida para PowerShell 5.1 (hífen ASCII). Preferir **`pwsh`** se voltarem problemas de encoding. |
| **F** Banda A | Operador | Checklist S0 em [SPRINTS_AND_MILESTONES.md](../../plans/SPRINTS_AND_MILESTONES.pt_BR.md) §4.0 — Dependabot / Scout / Hub. |
| **0** Carryover + Slack | Operador | [OPERATOR_TODAY_MODE_2026-03-26.pt_BR.md](OPERATOR_TODAY_MODE_2026-03-26.pt_BR.md): **GitHub + Hub `v1.6.7` feitos** (verificado); **Corporate-Entity-C** + **prova Slack telemóvel/desktop** — ainda manual. |

---

## Atalho no chat

**`today-mode 2026-03-27`** ou abre este arquivo.
