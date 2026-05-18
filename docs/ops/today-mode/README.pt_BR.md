# Modo “hoje” do operador (checklists datados)

**English:** [README.md](README.md)

**Objetivo:** Este diretório reúne **planos de dia com data** (`OPERATOR_TODAY_MODE_YYYY-MM-DD.md`), a **fila de carryover** e **como manter o “publicado” alinhado ao `pyproject.toml`** — para os checklists não ficarem defasados.

**Atalhos no chat:** escreve **`today-mode YYYY-MM-DD`** (token **só em inglês**); ver **`.cursor/rules/session-mode-keywords.mdc`**. Para **fim de bloco de trabalho ou saída do lab** (VeraCrypt / carryover / private stack opcional — não necessariamente fim do dia no calendário), usa **`block-close`**. Ritual manhã/fim de dia: **`scripts/operator-day-ritual.ps1`** (readiness Tier A + lista de arquivos — ver **Prontidão de manhã** abaixo).

### Para assistentes (Cursor / agente)

O **“hoje”** para nomes de checklist e trabalho datado deve bater com o **relógio da estação de trabalho do operador**, não só com contexto estático do chat.

1. No **terminal integrado** do PC de desenvolvimento: **PowerShell** `Get-Date -Format "yyyy-MM-dd"` (ou `Get-Date -Format "o"` para ISO com fuso); **cmd** `date /t` (e `time /t` se precisar).
2. Abre ou cria **`OPERATOR_TODAY_MODE_<esse-YYYY-MM-DD>.md`** nesta pasta ao alinhar ao **today-mode**.
3. Se o operador **disser outra data** no chat, usa a data dele como âncora do arquivo.

Ver **`AGENTS.md`** (*Workstation calendar clock*) e **`.cursor/rules/agent-session-ritual-sync-main-and-private-stack.mdc`**.

---

## Prontidão de manhã (escada estilo SRE)

**Objetivo:** começar o dia com **sync barato e com evidência** — sem fingir que **todo** passo de confiança/produção roda **toda** manhã. No chat, **`carryover-sweep`** corresponde a **`.\scripts\operator-day-ritual.ps1 -Mode Morning`** (o mesmo script).

| Tier | O quê | Quando |
| ---- | ----- | ------ |
| **A — Sync e superfície** | `git fetch`, `git status -sb`, PRs abertos, últimos runs de **CI** do **`main`** (`ci.yml`), e se existe **`OPERATOR_TODAY_MODE_YYYY-MM-DD.md`** para **hoje** | **Diário** (~2 min). Sempre seguro antes do trabalho fundo. |
| **B — Cadeia de dependências (-1)** | `uvx pip-audit -r requirements.txt` (mesma família do job **Dependency audit** no CI) | **Semanal**, antes de **release**, ou logo após **`deps`** / mudança de lock — não todo café da manhã. |
| **C — Imagem (-1b)** | `docker scout quickview` (ou política do projeto) na imagem **publicada** depois de mudança em **Dockerfile** / lock / base | Quando a **imagem** ou a história de **supply** mudou — não diário. |
| **D — Segundo ambiente (-1L)** | **[HOMELAB_VALIDATION.md](../HOMELAB_VALIDATION.md)**; opcional **`scripts/lab-op-sync-and-collect.ps1`** se existir **`docs/private/homelab/lab-op-hosts.manifest.json`** | Ao provar **deploy + conector** em **outra** máquina, ou em passada **agendada** de saúde do lab — não toda manhã. |

**Por que não B–D todo dia?** São mais lentos ou dependem de ambiente. Rodar **pip-audit + Scout + SSH lab** diariamente vira ruído se o **`main`** já está verde. O tier **A** pega **WIP surpresa**, **refs velhas**, **PRs abertos** e **CI vermelho** antes de gastar horas.

**Atalho rápido:** `.\scripts\operator-day-ritual.ps1 -Mode Morning -SkipReadiness` — só lista de arquivos + dicas sociais (raro). Isto **pula o Tier A** (`git fetch`, PRs, snapshot da CI); **não** é o gate completo de código/regressão.

**Gate de código / dependências:** use **`.\scripts\check-all.ps1`** antes do PR ou merge (opcional **`-IncludeVersionSmoke`** para coerência de versão vs release publicado). A CI roda o mesmo pytest, incluindo testes de lock/export — veja [SECURITY.pt_BR.md](../../SECURITY.pt_BR.md) e [ADR 0030](../../adr/ADR-0030-python-dependency-update-closure-single-pass.md).

**Chat:** token opcional em inglês **`morning-readiness`** — mesmo objetivo do **`carryover-sweep`** para Tier A + ponteiro de doc (ver **`.cursor/rules/session-mode-keywords.mdc`**).

---

## Companheiros canônicos (ler com frequência)

| Doc | Função |
| --- | ------ |
| [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md) | **Fila viva** — promover, deferir ou fechar (sem backlog silencioso). |
| [WORKBOARD.pt_BR.md](WORKBOARD.pt_BR.md) | **Cockpit central** — roteamento em uma página entre backlog, carryover e lembretes (sem duplicar fonte de verdade). |
| [PUBLISHED_SYNC.pt_BR.md](PUBLISHED_SYNC.pt_BR.md) | **GitHub Release + Docker Hub vs versão no repo** — atualizar após cada publish. |
| [SOCIAL_PUBLISH_AND_TODAY_MODE.pt_BR.md](SOCIAL_PUBLISH_AND_TODAY_MODE.pt_BR.md) | **Hub social privado + today-mode** — posts planeados, adiamentos, evidência ad-hoc; casa com **`docs/private/social_drafts/`** (gitignored). EN: [SOCIAL_PUBLISH_AND_TODAY_MODE.md](SOCIAL_PUBLISH_AND_TODAY_MODE.md). |
| [PRIVATE_OPERATOR_NOTES.pt_BR.md](../../PRIVATE_OPERATOR_NOTES.pt_BR.md) | Notas privadas de ritmo (`docs/private/…`) quando aplicável. |
| [OPERATOR_TODAY_MODE_TEMPLATE.pt_BR.md](OPERATOR_TODAY_MODE_TEMPLATE.pt_BR.md) | **Casca para copiar** dias novos (Bloco 0 + Fim do dia: **`block-close`** + VeraCrypt vs **`eod-sync`**). EN: [OPERATOR_TODAY_MODE_TEMPLATE.md](OPERATOR_TODAY_MODE_TEMPLATE.md). |

---

## Checklists datados (mais recente por último)

| Data | English | pt-BR |
| ---- | ------- | ----- |
| 2026-03-26 | [OPERATOR_TODAY_MODE_2026-03-26.md](OPERATOR_TODAY_MODE_2026-03-26.md) | [OPERATOR_TODAY_MODE_2026-03-26.pt_BR.md](OPERATOR_TODAY_MODE_2026-03-26.pt_BR.md) |
| 2026-03-27 | [OPERATOR_TODAY_MODE_2026-03-27.md](OPERATOR_TODAY_MODE_2026-03-27.md) | [OPERATOR_TODAY_MODE_2026-03-27.pt_BR.md](OPERATOR_TODAY_MODE_2026-03-27.pt_BR.md) |
| 2026-03-29 | [OPERATOR_TODAY_MODE_2026-03-29.md](OPERATOR_TODAY_MODE_2026-03-29.md) | [OPERATOR_TODAY_MODE_2026-03-29.pt_BR.md](OPERATOR_TODAY_MODE_2026-03-29.pt_BR.md) |
| 2026-03-30 | [OPERATOR_TODAY_MODE_2026-03-30.md](OPERATOR_TODAY_MODE_2026-03-30.md) | [OPERATOR_TODAY_MODE_2026-03-30.pt_BR.md](OPERATOR_TODAY_MODE_2026-03-30.pt_BR.md) |
| **2026-03-31** | [OPERATOR_TODAY_MODE_2026-03-31.md](OPERATOR_TODAY_MODE_2026-03-31.md) | [OPERATOR_TODAY_MODE_2026-03-31.pt_BR.md](OPERATOR_TODAY_MODE_2026-03-31.pt_BR.md) |
| **2026-04-01** | [OPERATOR_TODAY_MODE_2026-04-01.md](OPERATOR_TODAY_MODE_2026-04-01.md) | [OPERATOR_TODAY_MODE_2026-04-01.pt_BR.md](OPERATOR_TODAY_MODE_2026-04-01.pt_BR.md) |
| **2026-04-02** | [OPERATOR_TODAY_MODE_2026-04-02.md](OPERATOR_TODAY_MODE_2026-04-02.md) | [OPERATOR_TODAY_MODE_2026-04-02.pt_BR.md](OPERATOR_TODAY_MODE_2026-04-02.pt_BR.md) |
| 2026-04-06 | [OPERATOR_TODAY_MODE_2026-04-06.md](OPERATOR_TODAY_MODE_2026-04-06.md) | [English](OPERATOR_TODAY_MODE_2026-04-06.md) *(sem `.pt_BR.md`)* |
| 2026-04-08 | [OPERATOR_TODAY_MODE_2026-04-08.md](OPERATOR_TODAY_MODE_2026-04-08.md) | [English](OPERATOR_TODAY_MODE_2026-04-08.md) *(sem `.pt_BR.md`)* |
| 2026-04-09 | [OPERATOR_TODAY_MODE_2026-04-09.md](OPERATOR_TODAY_MODE_2026-04-09.md) | [English](OPERATOR_TODAY_MODE_2026-04-09.md) *(sem `.pt_BR.md`)* |
| **2026-04-10** | [OPERATOR_TODAY_MODE_2026-04-10.md](OPERATOR_TODAY_MODE_2026-04-10.md) | [OPERATOR_TODAY_MODE_2026-04-10.pt_BR.md](OPERATOR_TODAY_MODE_2026-04-10.pt_BR.md) |
| **2026-04-16** | [OPERATOR_TODAY_MODE_2026-04-16.md](OPERATOR_TODAY_MODE_2026-04-16.md) | [OPERATOR_TODAY_MODE_2026-04-16.pt_BR.md](OPERATOR_TODAY_MODE_2026-04-16.pt_BR.md) |
| **2026-04-22** | [OPERATOR_TODAY_MODE_2026-04-22.md](OPERATOR_TODAY_MODE_2026-04-22.md) | [OPERATOR_TODAY_MODE_2026-04-22.pt_BR.md](OPERATOR_TODAY_MODE_2026-04-22.pt_BR.md) |
| **2026-05-11** | [OPERATOR_TODAY_MODE_2026-05-11.md](OPERATOR_TODAY_MODE_2026-05-11.md) | [OPERATOR_TODAY_MODE_2026-05-11.pt_BR.md](OPERATOR_TODAY_MODE_2026-05-11.pt_BR.md) |
| **2026-05-14** | [OPERATOR_TODAY_MODE_2026-05-14.md](OPERATOR_TODAY_MODE_2026-05-14.md) | [OPERATOR_TODAY_MODE_2026-05-14.pt_BR.md](OPERATOR_TODAY_MODE_2026-05-14.pt_BR.md) |
| **2026-05-15** | [OPERATOR_TODAY_MODE_2026-05-15.md](OPERATOR_TODAY_MODE_2026-05-15.md) | [OPERATOR_TODAY_MODE_2026-05-15.pt_BR.md](OPERATOR_TODAY_MODE_2026-05-15.pt_BR.md) |
| **2026-05-17** | [OPERATOR_TODAY_MODE_2026-05-17.md](OPERATOR_TODAY_MODE_2026-05-17.md) | [OPERATOR_TODAY_MODE_2026-05-17.pt_BR.md](OPERATOR_TODAY_MODE_2026-05-17.pt_BR.md) |
| **2026-05-18** | [OPERATOR_TODAY_MODE_2026-05-18.md](OPERATOR_TODAY_MODE_2026-05-18.md) | [OPERATOR_TODAY_MODE_2026-05-18.pt_BR.md](OPERATOR_TODAY_MODE_2026-05-18.pt_BR.md) |
| **2026-05-19** | [OPERATOR_TODAY_MODE_2026-05-19.md](OPERATOR_TODAY_MODE_2026-05-19.md) | [OPERATOR_TODAY_MODE_2026-05-19.pt_BR.md](OPERATOR_TODAY_MODE_2026-05-19.pt_BR.md) |

Os blocos **WRB** para colar no e-mail ficam em **`docs/ops/WRB_DELTA_SNAPSHOT_*.md`**.

---

## Criar um dia novo

1. Copie **[OPERATOR_TODAY_MODE_TEMPLATE.pt_BR.md](OPERATOR_TODAY_MODE_TEMPLATE.pt_BR.md)** (ou a estrutura do **`OPERATOR_TODAY_MODE_*.md` mais recente**) e renomeie para **`OPERATOR_TODAY_MODE_YYYY-MM-DD.md`**. Mantenha o **item 5 do Bloco 0** e a linha de **Fim do dia** que emparelham **`block-close`** com VeraCrypt (**privado** **`docs/private/homelab/OPERATOR_VERACRYPT_SESSION_POLICY*.md`**) vs **`eod-sync`**.
1. Liga **`CARRYOVER.pt_BR.md`** e **`PUBLISHED_SYNC.pt_BR.md`** no Bloco 0 quando o dia mexer em release ou carryover.
1. Depois de um **publish real** (tag + GitHub Release + Docker Hub), atualiza **`PUBLISHED_SYNC.*`**, as linhas de release em **`docs/plans/PLANS_TODO.md`** se preciso, e **`python scripts/plans-stats.py --write`**.

---

## Navegação

- Índice pai: **[`docs/ops/README.pt_BR.md`](../README.pt_BR.md)** ([EN](../README.md)).
