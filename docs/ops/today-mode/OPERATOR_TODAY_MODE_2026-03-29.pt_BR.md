# “Today mode” do operador — 2026-03-29 (fecho de sessão + dia de tarefas de casa)

**English:** [OPERATOR_TODAY_MODE_2026-03-29.md](OPERATOR_TODAY_MODE_2026-03-29.md)

**Objetivo:** Fechar um **dia misto** (tarefas em casa + trabalho assíncrono de docs com o assistente). Registar **o que ficou pronto**, **dívidas de carryover** de today modes antigos e **o que fazer a seguir** quando voltares — sem culpa: **founder feliz, developer produtivo, SRE menos stressado.**

**Abre este arquivo primeiro** ao voltar (**`today-mode 2026-03-29`**). Limites do dia: **`carryover-sweep`** (manhã) · **`eod-sync`** (fim do dia) — **`scripts/operator-day-ritual.ps1`**, **`.cursor/rules/session-mode-keywords.mdc`**.

---

## Taxonomia (como chamamos “coisa antiga não feita”)

| Termo         | Significado                                                                                                            |
| -----         | -----------                                                                                                            |
| **Carryover** | Itens de um **`OPERATOR_TODAY_MODE_*` anterior** que ainda valem — varrer com **`carryover-sweep`** (ritual da manhã). |
| **Deferred**  | Adiado com **data**, linha no **PLANS_TODO** ou **`WORKFLOW_DEFERRED_FOLLOWUPS.md`** — não é backlog silencioso.       |
| **Dangling**  | Checkbox **sem dono e sem data** — **evitar**; converter em linha de carryover ou defer.                               |

---

## Relatório de sessão — 2026-03-29 (assistente + operador, assíncrono)

## Docs / repo (rastreados):

- **`docs/ops/inspirations/INSPIRATIONS_HUB.md`** (+ **`.pt_BR.md`**) — hub central de navegação das inspirações.
- **`docs/ops/inspirations/README.md`** / **`README.pt_BR.md`** — apontar primeiro para o hub.
- **`docs/ops/inspirations/ENGINEERING_CRAFT_INSPIRATIONS.md`** (+ **`.pt_BR.md`**) — linhas: **Jeremy Ruston**, **Simon Baird**, **TiddlyTools + Eric Shulman** (autoria explícita), **Steve Gibson** como ponteiro (detalhe GRC em **`SECURITY_NOW.md`**).
- **`docs/ops/README.md`** / **`README.pt_BR.md`** — linha de índice do **hub de inspirações**.

## Privado / workspace (gitignored):

- **`docs/private/raw_pastes/supere_blog/20260329_BATCH_INDEX_AND_TW_CROSSREF.pt_BR.md`** — índice dos novos batches Supere + cruzamento TiddlyWiki.
- **`docs/private/raw_pastes/supere_blog/README.pt_BR.md`** — ligação a esse índice.

**Testes:** `pytest` de **locale pt-BR** nos `*.pt_BR.md` de inspirações — verde.

**Não feito no repo hoje:** commit/PR de árvore **local por commitar** (se ainda existir; ver último **`eod-sync`**); PRs **Dependabot** (#134, #143, #144) ainda abertos.

---

## Bloco 0 — Quando voltares (≈ 15–30 min): carryover sweep

### 0a — Dívidas de `today mode` antigo (promover ou deferir — não deixar dangling)

| Dia fonte      | Carryover (se ainda for verdade)                                                                  | Próximo passo sugerido                               |
| ---------      | ---------------------------------                                                                 | -----------------------                              |
| **2026-03-26** | ~~Tag **`v1.6.7`**, GitHub Release, Docker Hub~~ — **✅ feito 2026-03-26** (ver [PUBLISHED_SYNC.pt_BR.md](PUBLISHED_SYNC.pt_BR.md)) | Só ação se fores lançar **1.6.8** |
| **2026-03-26** | E-mail **Corporate-Entity-C** WRB com **`WRB_DELTA_SNAPSHOT_2026-03-26.pt_BR.md`**                            | Enviar ou deferir com data em PLANS / nota privada   |
| **2026-03-27** | **Slack** prova de ping (Windows + iPhone) conforme **`docs/ops/OPERATOR_NOTIFICATION_CHANNELS.pt_BR.md`** | Teste curto; **`CHAN-OK`** / nota se ainda bloqueado |
| **2026-03-27** | ~~**Help-sync**~~ / **`OPERATOR_HELP_AUDIT.md`**                                                  | **Feito** no registro 2026-03-27 — repetir `pytest` quando mudar CLI |
| **2026-03-27** | ~~**OpenAPI** vs **`POST /scan`**~~                                                               | **Feito** (ver audit Follow-ups)                     |
| **2026-03-27** | ~~README **`--host`**~~                                                                           | **Cumprido** — reabrir se o quick start mudar       |
| **2026-03-27** | Web **`/help`** vs flags do **`main.py`**                                                         | Paridade quando houver flags novas                   |

### 0a-def — Defers explícitos (registados 2026-03-30; linha de publish limpa **2026-03-31**)

| Origem (0a)    | Adiar para   | Nota |
| -----          | -----        | ---- |
| ~~Tag **`v1.6.7`** + Release + Docker Hub~~ | — | **Enviado 2026-03-26** — ver [PUBLISHED_SYNC.pt_BR.md](PUBLISHED_SYNC.pt_BR.md); próximo público **1.6.8** |
| E-mail **Corporate-Entity-C** WRB | **2026-04-05** | Enviar ou mover data |
| **Slack** ping (Windows + iPhone) | **2026-04-02** | Teste curto |
| **Help-sync** + **`OPERATOR_HELP_AUDIT.md`** | **2026-04-03** | `pytest` quando mudar flags |
| **OpenAPI** vs **`POST /scan`** | — | Fechado — rever `/docs` após mudanças de schema |
| README **`--host`** LAN | — | Cumprido |
| Web **`/help`** vs **`main.py`** | **2026-04-05** | Paridade quando houver flags novas |

### Bloco 0 — Passos 2 → 3 → 1 (fechamento leve, 2026-03-30)

1. **`git status`** — Árvore **grande** (~dezenas de arquivos modificados + untracked). **Sem** commit em massa neste passo; próxima sessão **`houseclean`**: `preview-commit` / PRs por tema (**`.cursor/rules/execution-priority-and-pr-batching.mdc`**).
2. **Defers** — Tabela **0a-def** acima (nada em **dangling**).
3. **Link `TiddlyTools.com`** — Verificado com `curl`/HEAD: **HTTP 200 OK** (GitHub Pages); **sem** alteração de URL nas tabelas **`ENGINEERING_CRAFT_INSPIRATIONS*`**.

### 0b — Continuidade do journal privado

- Reler **`docs/private/RESUME_TOPICS_JOURNAL.pt_BR.md`** — entrada **2026-03-29** com “o que foi feito + próximo passo”.
- Opcional: **`docs/private/TODAY_MODE_CARRYOVER_AND_FOUNDER_RHYTHM.md`** — ritmo founder vs carryover diário.

---

## Atividades recomendadas — próximo bloco de trabalho (escolhe 1–3, não todas)

1. **`git status`** — se a árvore for grande, **`preview-commit`** / partir commits por **`.cursor/rules/execution-priority-and-pr-batching.mdc`**.
1. **Inspirações:** abrir **[INSPIRATIONS_HUB.pt_BR.md](../inspirations/INSPIRATIONS_HUB.pt_BR.md)** — confirmar que **tiddlytools.com** abre; ajustar link se precisar.
1. **Recuperação Supere:** próximo paste ou **`burst-showcase`** quando tiveres energia — **SiteMap** / backlog Nerd conforme **`RESUME_TOPICS_JOURNAL`**.
1. **Deps:** triagem dos PRs **Dependabot** quando quiser uma sessão **`deps`** — não é obrigação moral hoje.
1. **SRE em calma:** um **`check-all`** ou **`lint-only`** só se fores **commitar** — não como castigo.

---

## Critério de paragem para o “today mode 2026-03-29”

Este arquivo está **fechado para o dia de tarefas** quando leres o **Bloco 0** e escolheres **pelo menos uma** ação para a próxima sessão (mesmo “adiar X para YYYY-MM-DD” escrito).

---

## Atalho no chat

**`today-mode 2026-03-29`** ou abre este arquivo.
