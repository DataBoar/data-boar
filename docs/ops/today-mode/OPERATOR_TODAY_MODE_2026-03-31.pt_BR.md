# “Today mode” do operador — 2026-03-31 (carryover + higiene da pasta)

**English:** [OPERATOR_TODAY_MODE_2026-03-31.md](OPERATOR_TODAY_MODE_2026-03-31.md)

**Objetivo:** Retomar depois de os arquivos **`today-mode`** passarem para **`docs/ops/today-mode/`** com [README.pt_BR.md](README.pt_BR.md), [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md) e [PUBLISHED_SYNC.pt_BR.md](PUBLISHED_SYNC.pt_BR.md). **Em paralelo:** instalação **LAB-NODE-01 + LMDE** — usa [LMDE7_LAB-NODE-01_DEVELOPER_SETUP.pt_BR.md](../LMDE7_LAB-NODE-01_DEVELOPER_SETUP.pt_BR.md) quando fores para essa máquina.

**Abre primeiro:** [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md) e este arquivo (**`today-mode 2026-03-31`**). Limites: **`carryover-sweep`** · **`eod-sync`** · **`scripts/operator-day-ritual.ps1`**.

---

## Bloco 0 — Verdade + carryover (≈ 15–25 min)

1. Lê **[PUBLISHED_SYNC.pt_BR.md](PUBLISHED_SYNC.pt_BR.md)** — **`v1.6.7`** é **Latest** no GitHub e no Docker Hub; próxima linha pública é **1.6.8** quando `main` justificar.
1. Percorre **[CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md)** — marca, adia com data ou abre linha em **PLANS** / **issue** para cada ⬜.
1. Opcional: **`carryover-sweep`** + espreitar Bloco 0 de [OPERATOR_TODAY_MODE_2026-03-29.pt_BR.md](OPERATOR_TODAY_MODE_2026-03-29.pt_BR.md) (histórico).

---

## Bloco A — Fechar esta fatia docs/workflow (≈ 30–90 min)

- **`git status`** — se esta sessão acrescentou **`today-mode/`**, faz commit com mensagem clara **`docs(ops):`** ou **`workflow(ops):`**; **`.\scripts\lint-only.ps1`** ou **`check-all`** antes de push/PR.
- **`git fetch`** + alinha **`main`** se fores fundir.

---

## Bloco banda B — Deps / banda A (≈ 30–45 min)

- Triagem dos PRs Dependabot (ver [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md)); sessão **`deps`** conforme **`SECURITY.md`**.
- **Status 2026-03-31:** PRs Dependabot relevantes foram mergeados (ver `CARRYOVER`); se surgirem novos, repetir “checks verdes + mergeable” antes de merge.
- Leitura fina: [SPRINTS_AND_MILESTONES.pt_BR.md](../../plans/SPRINTS_AND_MILESTONES.pt_BR.md) S0 se quiser higiene Scout/Hub na mesma semana.

---

## Bloco C — Fatia doc opcional (token-aware)

- Um PR **`docs`**: primeiras linhas **Gemini Cold** no `PLANS_TODO.md` (ex. **G-26-04**, **G-26-13**) se quiser progresso de baixo risco.

---

## Critério de paragem

Fatia do dia **fechada** quando: **CARRYOVER** atualizado (sem “pendente” falso para publicar **v1.6.7**); **PUBLISHED_SYNC** com data “última verificação” atual se revalidaste no remoto; PR **today-mode** fundido ou adiado com ponteiro em **issue**; passos LAB-NODE-01 só **quando** estiveres nesse teclado.

---

## Atalho no chat

**`today-mode 2026-03-31`** ou abra este arquivo.
