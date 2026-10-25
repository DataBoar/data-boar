# Modo operador hoje — 2026-08-31 (desacelerar — Tier A + merge docs)

**English:** [OPERATOR_TODAY_MODE_2026-08-31.md](OPERATOR_TODAY_MODE_2026-08-31.md)

**Manchete:** **Domingo** em modo **desacelerar** até **2026-09-09** (refil Cursor Ultra). Manhã = só **Tier A**. **`main`** já tem **#1832** / **#1838**; PR ativo: **[#1841](https://github.com/DataBoar/data-boar/pull/1841)** (**#1840** — mapa de fila + script gerador).

**Relógio da estação:** `2026-08-31` — confirme com `date` na estação de trabalho.

**Postura de token:** Sem maratona de agente; `lint-only` / `quick-test` em slice de docs; **`check-all`** completo só antes de merge se mexer em código.

---

## Bloco 0 — Manhã (Tier A, ~10 min)

Rodar **`carryover-sweep`** ou ritual matinal (`git` + `gh` no Linux está ok).

1. **`git fetch`** + **`git pull origin main`**
2. **`gh pr list`** — esperar **[#1841](https://github.com/DataBoar/data-boar/pull/1841)** aberto
3. **`gh pr checks 1841`** — mergear quando verde (`Closes #1840`)
4. **Ruleset `main-gate-pii`:** check **`SSHSIG attestation when gated`** obrigatório (quando pronto)
5. - [ ] Social (~2 min): `docs/private/social_drafts/editorial/SOCIAL_HUB.md`

**Não é dia de:** Dependabot em lote, completão, novo hardening, PR grande de **`feature`** — salvo **U0** em `main`.

---

## Já em `main` (não reabrir)

| Item | Estado |
| ---- | ------ |
| **#1832** guard PR | ✅ Mergeado **2026-08-30** |
| **#1838** BACKLOG_GTD | ✅ Mergeado |
| **#552 / #1816** | ✅ Mergeado; **#552** fechada |
| Espelho da fila | 🔄 **#1840** / PR **#1841** |

---

## Uma hora calma (opcional — **uma** coisa)

| Prioridade | Slice |
| ---------- | ----- |
| **O1** | Merge **#1841** com CI verde |
| **O2** | Ruleset SSHSIG |
| **O3** | Milestones **`#696`**, **`#697`**, **`#1538`** (3 sem milestone) |
| **Adiar** | **`feat/report-multiformat-553`**, outreach Heptapod/Codeberg (**shared#63**) |

---

## Carryover — linhas de hoje

- [ ] `git pull` em `main` depois do merge **#1841**
- [ ] Ler [ISSUE_QUEUE_SEQUENCING_MAP.md](../ISSUE_QUEUE_SEQUENCING_MAP.md) atualizado
- [ ] Ruleset quando pronto
- [ ] Opcional: milestone nas 3 issues sem milestone
- [ ] **`block-close`** se dia leve

---

## Fim do dia

- **`eod-sync`** só se mergeou PR ou moveu backlog
- **`feature`** / **`deps`** de rotina após **09/09** ou **U0**

---

## Referências

- [CARRYOVER.md](CARRYOVER.md) · [PLANS_TODO.md](../../plans/PLANS_TODO.md)
- Regenerar mapa: `uv run python scripts/issue_queue_sequencing_map.py --write`
