# Modo hoje do operador — 2026-05-19 (retomada de manhã)

**English:** [OPERATOR_TODAY_MODE_2026-05-19.md](OPERATOR_TODAY_MODE_2026-05-19.md)

**Nota:** Preparado no fecho da noite **2026-05-18** — o **Bloco 0** manda na abertura do dia.

---

## Bloco 0 — Realidade de manhã (10–15 min)

Corre **`carryover-sweep`** ou **`.\scripts\operator-day-ritual.ps1 -Mode Morning`**. Depois:

1. **`origin/main`:** `git fetch` · `git status -sb` · `git pull origin main` se estiver atrás — confirma **`ci.yml`** verde no **`main`** antes de trabalho profundo.
2. **PRs abertos:** `gh pr list --state open` — faz merge quando verde com **`.\scripts\pr-merge-when-green.ps1`** onde for seguro.
3. **PMO de planos:** Lê a intro de **`docs/plans/PLANS_TODO.md`** + **[PLANS_DOCUMENTATION_HIERARCHY.pt_BR.md](../PLANS_DOCUMENTATION_HIERARCHY.pt_BR.md)** se fores promover trabalho de **issue** para **`PLAN_*.md`** (depois **`plans_hub_sync.py --write`**).
4. **Handoff em issue:** Se continuares uma **issue** do GitHub com outro assistente ou revisor, **decisões** na thread; **persiste** o resultado em **`docs/plans/`** conforme o doc de hierarquia.

**Fila contínua:** [CARRYOVER.md](CARRYOVER.md) · **Publicado:** [PUBLISHED_SYNC.md](PUBLISHED_SYNC.md)

### Social / editorial (hub privado) — ~2 min

- [ ] Olhar **`docs/private/social_drafts/editorial/SOCIAL_HUB.md`** para **2026-05-19** / **2026-05-20** — [SOCIAL_PUBLISH_AND_TODAY_MODE.pt_BR.md](SOCIAL_PUBLISH_AND_TODAY_MODE.pt_BR.md).

---

## Carryover — espinha

| Trilho | Item | Notas |
| ------ | ---- | ----- |
| Piloto | **M-PILOT-READY** | Critérios no **PLANS_TODO**; **v1.7.4** quando checklist verde. |
| Ops de planos | **Doc de hierarquia + fatias `PLAN_*.md`** | Commit/push **`docs/ops/PLANS_DOCUMENTATION_HIERARCHY*.md`** + links no README/cold-start quando pronto; alinha issues a planos commitados. |
| Governança | Triagem **P0/P1** aberta | [#512](https://github.com/FabioLeitao/data-boar/issues/512) plano de processo; promove trabalho durável para **`docs/plans/`**. |

---

## Fim do dia (**2026-05-19**)

- **`eod-sync`** ou **`block-close`** conforme carga — [README.pt_BR.md](README.pt_BR.md).
- Se **`docs/private/`** mudou: **`.\scripts\private-git-sync.ps1 -Push`**.
