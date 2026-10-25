# Operator today mode — 2026-08-30 (slowdown + recovery)

**Português (Brasil):** [OPERATOR_TODAY_MODE_2026-08-30.pt_BR.md](OPERATOR_TODAY_MODE_2026-08-30.pt_BR.md)

**Headline:** **Desacelerar** até ~**2026-09-09** (refil Cursor Ultra). Manhã = só **Tier A** (`carryover-sweep`). Ontem à noite **`main`** ganhou **#1832** (operator-gated PR guard) e **#1838** (BACKLOG_GTD). **Zero PRs abertos** no `data-boar` no EOD de **2026-08-30 ~00:36 −03**.

**Workstation clock:** `2026-08-30` (Saturday) · `date` on Linux primary.

**Token posture:** Agente quase sem budget — evitar sessões longas, `check-all` só se você abrir slice de código; preferir leitura, merge manual, settings GitHub.

---

## Block 0 — Morning reality (Tier A only, ~10 min)

Run **`carryover-sweep`** or **`./scripts/operator-day-ritual.ps1 -Mode Morning`** (Linux: ritual + `git`; script é PowerShell — use git/gh direto se preferir).

1. **`git fetch`** + **`git checkout main`** + **`git pull origin main`** — tip esperado: merge **#1832** + **#1838** (`3f7bd4de` ou posterior).
2. **`gh pr list`** — confirmar fila vazia (EOD **2026-08-30**).
3. **`gh run list --branch main --limit 3`** — `main` verde após merge noturno.
4. **Ruleset `main-gate-pii` (operator-only, quando tiver energia):** adicionar check **`SSHSIG attestation when gated`** como **required** — workflow já está em `main`; TOFU acabou com o merge de **#1832**.
5. - [ ] **Social skim** (~2 min): `docs/private/social_drafts/editorial/SOCIAL_HUB.md` — ver [SOCIAL_PUBLISH_AND_TODAY_MODE.md](SOCIAL_PUBLISH_AND_TODAY_MODE.md).

**Não é dia de:** novo hardening de gate, Dependabot em lote, completão, ou PR grande de produto — salvo **U0** real em `main`.

---

## Wins locked overnight (do not re-litigate)

| Item | State |
| ---- | ----- |
| **#1709 / PR #1832** — `operator-gated-pr-guard.yml` | ✅ **Merged** `2026-08-30T03:05:56Z` |
| **#1835 / PR #1838** — BACKLOG_GTD docs | ✅ **Merged** |
| **Security Reviewer hardening** (#1832, 6 fixes + 1 risco aceito) | ✅ Fechado neste ciclo |
| **Open PRs** | ✅ Nenhum (EOD madrugada) |

---

## If you have one calm hour (optional — pick **one**)

| Priority | Slice | Notes |
| -------- | ----- | ----- |
| **O1** | Ruleset: required check **SSHSIG attestation when gated** | Human GitHub UI only · [PLAN_OPERATOR_GATED_PR_GUARD.md](../../plans/PLAN_OPERATOR_GATED_PR_GUARD.md) phase 4 |
| **O2** | **#552** / **#1816** | ✅ Merged — **#552** already **CLOSED** |
| **O3** | **`feat/report-multiformat-553`** | WIP local Part A — só se `main` já puxado e energia para `check-all` |
| **Defer** | Dependabot queue (**#1802**…**#1810**) | **`deps`** depois do **09/09** |
| **Defer** | Codeberg / Heptapod outreach | [data-boar-shared#63](https://github.com/DataBoar/data-boar-shared/issues/63) — decantar, não contatar |

---

## Carryover — today rows

- [ ] **`git pull` on `main`** + sanity: `pyproject.toml` / último merge
- [ ] Ruleset **`main-gate-pii`**: marcar guard PR como required (quando pronto)
- [ ] Reconciliar [CARRYOVER.md](CARRYOVER.md) — **#1832** → Done; slowdown até **09/09**
- [ ] Skim **data-boar-shared#63** (AIIDCOBPP / Codeberg) — leitura, sem ação externa
- [ ] **`block-close`** se só passar o dia offline — não precisa **`eod-sync`** pesado de novo

---

## End of day (light)

- **`block-close`**: VeraCrypt / carryover uma linha se algo novo surgir
- **`eod-sync`**: só se você **fez** trabalho com git/PR hoje — senão pule
- Próximo foco produto: após **09/09** ou se **U0** em `main`
- **EOD noite (~20:45 −03):** [PR #1841](https://github.com/DataBoar/data-boar/pull/1841) aberto (**#1840** mapa + script) — ver [OPERATOR_TODAY_MODE_2026-08-31.md](OPERATOR_TODAY_MODE_2026-08-31.md)

---

## Quick refs

- [CARRYOVER.md](CARRYOVER.md) · [WORKBOARD.md](WORKBOARD.md) · [PLANS_TODO.md](../../plans/PLANS_TODO.md)
- Session: **`today-mode`**, **`carryover-sweep`**, **`block-close`**, **`pmo-view`** — **not** default **`feature`** until refill
