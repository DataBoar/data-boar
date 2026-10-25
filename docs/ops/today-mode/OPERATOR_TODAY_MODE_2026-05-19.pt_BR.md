# Modo hoje do operador — 2026-05-19 (retomada de manhã)

**English:** [OPERATOR_TODAY_MODE_2026-05-19.md](OPERATOR_TODAY_MODE_2026-05-19.md)

**Nota:** Atualizado no fim da noite **2026-05-19** (fuso do operador **-03**) após passagem noturna do agente — o **Bloco 0** manda na abertura do dia.

**Âncora `main`:** Fatias CLI **#520–#522** mergeadas (**#565** `--diff`, **#566** `--export-dsar`). Trabalho de tier **#559** pode estar em PR aberto — confirma com `gh pr list`.

---

## Bloco 0 — Realidade de manhã (10–15 min)

Corre **`carryover-sweep`** ou **`.\scripts\operator-day-ritual.ps1 -Mode Morning`**. Depois:

1. **`origin/main`:** `git fetch` · `git status -sb` · `git pull origin main` se estiver atrás — confirma **`ci.yml`** verde no **`main`** antes de trabalho profundo.
2. **PRs abertos:** `gh pr list --state open` — faz merge quando verde com **`.\scripts\pr-merge-when-green.ps1`** onde for seguro (ex.: tier licensing **#559**).
3. **PMO de planos:** Lê a intro de **`docs/plans/PLANS_TODO.md`** + **[PLANS_DOCUMENTATION_HIERARCHY.pt_BR.md](../PLANS_DOCUMENTATION_HIERARCHY.pt_BR.md)** se fores promover trabalho de **issue** para **`PLAN_*.md`** (depois **`plans_hub_sync.py --write`**).
4. **Handoff em issue:** Decisões na thread da issue; **persiste** o resultado em **`docs/plans/`** conforme o doc de hierarquia.

**Fila contínua:** [CARRYOVER.md](CARRYOVER.md) · **Publicado:** [PUBLISHED_SYNC.md](PUBLISHED_SYNC.md)

### Social / editorial (hub privado) — ~2 min

- [ ] Olhar **`docs/private/social_drafts/editorial/SOCIAL_HUB.md`** para **2026-05-19** / **2026-05-20** — [SOCIAL_PUBLISH_AND_TODAY_MODE.pt_BR.md](SOCIAL_PUBLISH_AND_TODAY_MODE.pt_BR.md).

---

## Foco sugerido (fatias finas P1)

| Prioridade | Item | Notas |
| ---------- | ---- | ----- |
| **P1** | [#559](https://github.com/FabioLeitao/data-boar/issues/559) fixtures + negação graciosa | Merge do PR se verde; depois enforcement real. |
| **P1** | [#544](https://github.com/FabioLeitao/data-boar/issues/544) `governance_lens` no mapa | Chaves podem existir após **#559** — ligar gate API/CLI em seguida. |
| **P1** | [#512](https://github.com/FabioLeitao/data-boar/issues/512) lote de processo | Promove para **`docs/plans/`**; fecha ecos com evidência. |
| **H1** | Plano CLI **completo** | [PLAN_CLI_VALIDATE_DIFF_AND_DSAR_EXPORT.md](../../plans/PLAN_CLI_VALIDATE_DIFF_AND_DSAR_EXPORT.md) — próximo tema no **PLANS_TODO** (docs governança **#556+**). |

---

## Carryover — espinha

| Trilho | Item | Notas |
| ------ | ---- | ----- |
| Piloto | **M-PILOT-READY** | Critérios no **PLANS_TODO**; **v1.7.4** quando checklist verde. |
| Ops de planos | **Doc de hierarquia + fatias `PLAN_*.md`** | Commit/push **`docs/ops/PLANS_DOCUMENTATION_HIERARCHY*.md`** quando pronto. |
| Governança | Triagem **P0/P1** aberta | **#512**; **#550** fechada (duplicata do timeout pwsh **#563**). |

---

## Fim do dia (**2026-05-19**)

- **`eod-sync`** ou **`block-close`** conforme carga — [README.pt_BR.md](README.pt_BR.md).
- Se **`docs/private/`** mudou: **`.\scripts\private-git-sync.ps1 -Push`**.
