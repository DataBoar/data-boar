# Modo hoje do operador — 2026-05-18 (retomada de manhã)

**English:** [OPERATOR_TODAY_MODE_2026-05-18.md](OPERATOR_TODAY_MODE_2026-05-18.md)

**Nota:** O **`main`** em **`acfaaf49`** já traz hierarquia PMO + rascunho **2026-05-19** — faz `pull` se precisar.

---

## Bloco 0 — Realidade de manhã (10–15 min)

Corre **`carryover-sweep`** ou **`.\scripts\operator-day-ritual.ps1 -Mode Morning`**. Depois:

1. **`origin/main`:** `git fetch` · `git status -sb` · `git pull origin main` se estiver atrás — confirma **`ci.yml`** verde no **`main`** antes de trabalho profundo.
2. **PRs abertos:** `gh pr list --state open` — ex.: **#348** (deps), **#365** (rascunho mute Slack) — merge quando verde com **`.\scripts\pr-merge-when-green.ps1`** onde for seguro.
3. **PMO de planos:** **[PLANS_DOCUMENTATION_HIERARCHY.pt_BR.md](../PLANS_DOCUMENTATION_HIERARCHY.pt_BR.md)** — decide na issue; **`docs/plans/`** persiste.
4. **Checklist de amanhã:** olhar **[OPERATOR_TODAY_MODE_2026-05-19.pt_BR.md](OPERATOR_TODAY_MODE_2026-05-19.pt_BR.md)** para o handoff.

**Fila contínua:** [CARRYOVER.md](CARRYOVER.md) · **Publicado:** [PUBLISHED_SYNC.md](PUBLISHED_SYNC.md)

### Social / editorial (hub privado) — ~2 min

- [ ] Olhar **`docs/private/social_drafts/editorial/SOCIAL_HUB.md`** para **2026-05-18** / **2026-05-19** — [SOCIAL_PUBLISH_AND_TODAY_MODE.pt_BR.md](SOCIAL_PUBLISH_AND_TODAY_MODE.pt_BR.md).

---

## Carryover — espinha

| Trilho | Item | Notas |
| ------ | ---- | ----- |
| Piloto | **M-PILOT-READY** | **PLANS_TODO** + release **#406** / **v1.7.4** quando critérios verdes. |
| Ops de planos | **Planos CLI / contatos** | [PLAN_CLI_VALIDATE_DIFF_AND_DSAR_EXPORT.md](../../plans/PLAN_CLI_VALIDATE_DIFF_AND_DSAR_EXPORT.md), triagem [#512](https://github.com/FabioLeitao/data-boar/issues/512). |
| Governança | **Dependabot** | GitHub mostra alerta **low** no **`main`** — triagem ao abrir **Security**. |

---

## Fim do dia (**2026-05-18**)

- **`eod-sync`** ou **`block-close`** — [README.pt_BR.md](README.pt_BR.md).
- Se **`docs/private/`** mudou: **`.\scripts\private-git-sync.ps1 -Push`**.
