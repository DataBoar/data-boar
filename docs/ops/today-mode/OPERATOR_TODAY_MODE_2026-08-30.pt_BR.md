# Modo operador hoje — 2026-08-30 (desacelerar + recuperação)

**English:** [OPERATOR_TODAY_MODE_2026-08-30.md](OPERATOR_TODAY_MODE_2026-08-30.md)

**Manchete:** **Desacelerar** até ~**2026-09-09** (refil Cursor Ultra). Manhã = só **Tier A** (`carryover-sweep`). Na madrugada o **`main`** recebeu **#1832** (guard PR operator-gated) e **#1838** (BACKLOG_GTD). **Zero PRs abertos** no `data-boar` no EOD de **2026-08-30 ~00:36 −03**.

**Relógio da estação:** `2026-08-30` (sábado) · `date` no Linux primário.

**Postura de token:** Agente quase sem budget — evitar sessões longas; `check-all` só se abrir slice de código; preferir leitura, merge manual, settings no GitHub.

---

## Bloco 0 — Realidade de manhã (só Tier A, ~10 min)

Rodar **`carryover-sweep`** ou **`.\scripts\operator-day-ritual.ps1 -Mode Morning`**.

1. **`git fetch`** + **`git checkout main`** + **`git pull origin main`**
2. **`gh pr list`** — fila vazia (EOD **2026-08-30**)
3. **`gh run list --branch main --limit 3`** — `main` verde após merges
4. **Ruleset `main-gate-pii`:** quando tiver energia, tornar **`SSHSIG attestation when gated`** obrigatório (**#1832** já em `main`)
5. - [ ] Social (~2 min): `docs/private/social_drafts/editorial/SOCIAL_HUB.md`

**Não é dia de:** novo hardening, Dependabot em lote, completão ou PR grande — salvo **U0** em `main`.

---

## Vitórias da madrugada

| Item | Estado |
| ---- | ------ |
| **#1709 / PR #1832** | ✅ **Merged** |
| **#1835 / PR #1838** | ✅ **Merged** |
| Hardening Security Reviewer | ✅ Ciclo fechado |
| PRs abertos | ✅ Nenhum (EOD madrugada) |

---

## Se tiver uma hora calma (opcional — **uma** coisa)

| Prioridade | Slice |
| ---------- | ----- |
| **O1** | Ruleset: check obrigatório do guard |
| **O2** | **#552** / **#1816** — ✅ Merged; **#552** **CLOSED** |
| **O3** | **`feat/report-multiformat-553`** só com energia para `check-all` |
| **Adiar** | Dependabot, outreach Codeberg/Heptapod (**shared#63**) |

---

## Carryover — linhas de hoje

- [ ] `git pull` em `main`
- [ ] Ruleset quando pronto
- [ ] Atualizar [CARRYOVER.md](CARRYOVER.md)
- [ ] Ler **shared#63** sem contato externo
- [ ] **`block-close`** se o dia for offline

---

## Fim do dia (leve)

- **`block-close`** ou **`eod-sync`** só se houve trabalho git/PR
- Produto de novo após **09/09** ou **U0**
- **EOD noite (~20:45 −03):** [PR #1841](https://github.com/DataBoar/data-boar/pull/1841) aberto — ver [OPERATOR_TODAY_MODE_2026-08-31.pt_BR.md](OPERATOR_TODAY_MODE_2026-08-31.pt_BR.md)

---

## Referências

- [CARRYOVER.md](CARRYOVER.md) · [PLANS_TODO.md](../../plans/PLANS_TODO.md)
