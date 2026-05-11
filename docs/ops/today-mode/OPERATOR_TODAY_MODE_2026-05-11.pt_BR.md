# Modo operador do dia — 2026-05-11 (pós **v1.7.4-rc**; métricas de lab + fechamento de sprint curto)

**English:** [OPERATOR_TODAY_MODE_2026-05-11.md](OPERATOR_TODAY_MODE_2026-05-11.md)

**Tema:** **`main`** em **`1.7.4-rc`** com pré-release GitHub **`v1.7.4-rc`**; **Docker Hub para consumidor** segue **`1.7.3`** / **`latest`**. **Hoje:** fechar **higiene de CI/workflow** (workflow **`zizmor`** ainda não commitado), depois **medição controlada no lab** (**`1.7.3`** Hub vs linha atual) antes de promover fatias **quase prontas** (**CNPJ fase 5**, **Bandit fase 3**, **Scope import fase E**). **Primeiro:** **`git fetch origin`** · **`git checkout main`** · **`git pull origin main`** · **`git status -sb`**.

---

## Bloco 0 — Checagem de manhã (10–15 min)

Rode **`carryover-sweep`** ou **`.\scripts\operator-day-ritual.ps1 -Mode Morning`**. Depois:

1. **`origin/main`:** atualize se estiver atrás; confirme **`1.7.4-rc`** em **`pyproject.toml`**.
2. **Verdade publicada:** [PUBLISHED_SYNC.pt_BR.md](PUBLISHED_SYNC.pt_BR.md) — **Latest** estável = **`v1.7.3`**; pré-release = **`v1.7.4-rc`** (sem refresh de marketing no Hub para RC, salvo tag de lab explícita).
3. **PRs abertos:** triagem **Dependabot** / **deps** (**#348** aberto; **#349–#352** rascunho) — merge ou adiar com data.
4. **Git privado empilhado (`docs/private/`):** **`.\scripts\private-git-sync.ps1`** (**`-Push`** conforme política) após evidência de lab ou rascunhos sociais.

**Fila rolante:** [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md) · **Publicado:** [PUBLISHED_SYNC.pt_BR.md](PUBLISHED_SYNC.pt_BR.md)

### Social / editorial (hub privado) — ~2 min

- [ ] Passar **`docs/private/social_drafts/editorial/SOCIAL_HUB.md`** por **Alvo editorial** em **2026-05-11** / **2026-05-12** — [SOCIAL_PUBLISH_AND_TODAY_MODE.pt_BR.md](SOCIAL_PUBLISH_AND_TODAY_MODE.pt_BR.md).

---

## Carryover — sessão 2026-05-10

- [ ] **Maestro / completão:** arquivo [`LAB_LESSONS_LEARNED_2026_05_10.md`](../lab_lessons_learned/LAB_LESSONS_LEARNED_2026_05_10.md); hub [`LAB_LESSONS_LEARNED.md`](../LAB_LESSONS_LEARNED.md). Itens **1–6** de hardening Maestro em **`PLANS_TODO.md`** = **feitos** em **`main`**.
- [ ] **Matriz DB all-to-all:** uma rodada consolidada com config por host.
- [ ] **Mongo no WSL2:** escopo aceito (Mongo no host x86 secundário); follow-up de infra só se quiser mover de volta.
- [ ] **Narrativa de performance:** tratar regressão Rust/PyO3 em lições antigas como **stale** até remedição controlada **`1.7.3`** vs **`1.7.4-rc`**.
- [ ] **Lint de segurança de workflows:** commit + PR de **`.github/workflows/zizmor.yml`** (modo advisory; enforce depois).

---

## Foco A — Higiene CI / pipeline (≤1 h)

| # | Atividade | Pronto quando |
| - | --------- | ------------- |
| A1 | **`zizmor`** em **`main`** | PR mergeado; job no GitHub Actions |
| A2 | Pré-release **`v1.7.4-rc`** sem mover Hub **`latest`** | **`gh release view v1.7.4-rc`** |
| A3 | Opcional: atualizar [PUBLISHED_SYNC.pt_BR.md](PUBLISHED_SYNC.pt_BR.md) | Data e ponteiro de pré-release corretos |

---

## Foco B — Métricas controladas no lab (meio dia com slot LAB)

| # | Atividade | Pronto quando |
| - | --------- | ------------- |
| B1 | **`1.7.3`** Hub + **`1.7.4-rc`** da **`main`** | Dois configs reproduzíveis em notas **privadas** |
| B2 | **`.\scripts\benchmark-ab.ps1`** no mesmo corpus | Tempos em **`benchmark_runs/`** ou relatório privado |
| B3 | Lições públicas só com números verificados | Sem métricas inventadas em arquivos rastreados |
| B4 | Reescrever bullets de performance stale se preciso | Uma linha em **`PLANS_TODO.md`** ou arquivo datado |

---

## Foco C — Planos quase prontos (escolha **uma** fatia principal)

Fonte: fila *Post-`1.7.4` short-sprint closure* em **`docs/plans/PLANS_TODO.md`**.

| Sprint | Fatia | Saída (resumo) | Plano |
| ------ | ----- | -------------- | ----- |
| **S3** | **CNPJ fase 5 (checksum)** | Caminho opt-in; **5.1–5.3**; regex padrão intacto | [PLAN_CNPJ_ALPHANUMERIC_FORMAT_VALIDATION.md](../../plans/PLAN_CNPJ_ALPHANUMERIC_FORMAT_VALIDATION.md) |
| **S1** | **Bandit fase 3** | Gate **`-ll -ii`**; triagem low; arquivar plano | [PLAN_BANDIT_SECURITY_LINTER.md](../../plans/PLAN_BANDIT_SECURITY_LINTER.md) |
| **S2** | **Scope import fase E** | Adapter GLPI-like + fixtures | [PLAN_SCOPE_IMPORT_FROM_EXPORTS.md](../../plans/PLAN_SCOPE_IMPORT_FROM_EXPORTS.md) |

**Secundário:** magic-byte (content type) · Notificações fase 4 — ver H1/U1.

**Antes do PR:** **`.\scripts\check-all.ps1`**.

---

## Backlog — promover ou adiar

| Item | Padrão | Promover quando |
| ---- | ------ | --------------- |
| **–1L** matriz segundo ambiente | Adiar | Dia de lab / hardware |
| **S2a** + **#86** fase 1 | Após métricas RC | Sprint de confiança demo |
| **Dependabot #349–#352** | Triagem | Sessão **`deps`** |
| **WRB Corporate-Entity-C** | Carryover | Janela de comunicação |
| **Observabilidade / Wazuh** | H2 | Pré-requisitos de stack mínima |

---

## Fim do dia

- **`block-close`** ao sair do lab / VC — política VeraCrypt em **`docs/private/homelab/`**
- **`eod-sync`** ou ritual **Eod** — adiamentos com **data** em [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md)
- Esboço **`OPERATOR_TODAY_MODE_2026-05-12.md`** a partir do [template](OPERATOR_TODAY_MODE_TEMPLATE.pt_BR.md)

---

## Referências rápidas

- **`docs/releases/1.7.4-rc.md`** · **`docs/VERSIONING.md`**
- Lições de lab: **`docs/ops/lab_lessons_learned/`**
- Tokens: **`feature`**, **`deps`**, **`homelab`**, **`completao`**, **`backlog`**, **`eod-sync`**
