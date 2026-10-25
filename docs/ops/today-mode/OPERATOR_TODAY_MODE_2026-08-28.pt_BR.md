# Modo today do operador — 2026-08-28 (captura no fim do dia: #552/#553 + #1061)

**English:** [OPERATOR_TODAY_MODE_2026-08-28.md](OPERATOR_TODAY_MODE_2026-08-28.md)

**Manchete:** Escrito no **fim da sexta** (quando o operador lembrou). Fechar **#552** (PR **#1816**) com CI verde; terminar **#553** Part A (ODS + allowlist de caminho) e depois Part B; **#1061** já fechada como not-planned → [tidy-tortoise#14](https://github.com/DataBoar/tidy-tortoise/issues/14). O ciclo de duas semanas **2026-08-16 → 2026-08-29** acaba **amanhã**.

**Relógio da workstation (este arquivo):** `2026-08-28` (sexta, −03) via `date` no Linux primary.

**Plano de duas semanas:** [PLAN_TWO_WEEK_EXECUTION_NO_REGRESSION.pt_BR.md](../../plans/PLAN_TWO_WEEK_EXECUTION_NO_REGRESSION.pt_BR.md)

---

## Bloco 0 — Realidade (escrito tarde)

Este arquivo é **recap do mesmo dia + carryover**, não um plano de manhã. Ainda assim: **`eod-sync`** / **`block-close`** antes de sair.

1. **`main`:** `git fetch` + `git pull origin main` ao sair das branches de feature (`origin/main` na escrita: **#1801** SSRF SMB).
2. **PR de produto aberto:** [#1816](https://github.com/DataBoar/data-boar/pull/1816) — sink de achados **#552** + lote ADR + correção SSRF da URL (`7d6eb387`). Mergear quando os checks estiverem verdes (`pr-merge-when-green`).
3. **WIP local (não misturar com #1816):** branch **`feat/report-multiformat-553`** — Part A ODS sem commit; HIGH do Bugbot (allowlist `.ods`) já no working tree.
4. **Dependabot (não mergear às cegas):** fila nova **2026-08-28** — **#1802** setup-uv **10**, **#1803** claude-code-action, **#1805** CodeQL analyze, **#1804** pin distroless, **#1807** grupo uv-minor-patch, **#1808** sentence-transformers **6**, **#1810** types-pyyaml. Preferir pin de Actions **#1802** / **#1805** depois da skill **`deps`**; **#1808** é major.
5. - [ ] **`block-close`** / **`eod-sync`** na fronteira (este *é* o fim do dia).

**Fila viva:** [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md) · Último arquivo datado antes deste: [OPERATOR_TODAY_MODE_2026-08-17.pt_BR.md](OPERATOR_TODAY_MODE_2026-08-17.pt_BR.md)

### Social / editorial (~2 min)

- [ ] Passar o olho em `docs/private/social_drafts/editorial/SOCIAL_HUB.md` — **nenhum** **Alvo editorial** do inventário bate **2026-08-28** / **2026-08-29** na hora da escrita (fluxo: [SOCIAL_PUBLISH_AND_TODAY_MODE.pt_BR.md](SOCIAL_PUBLISH_AND_TODAY_MODE.pt_BR.md)).

---

## Sequência sugerida (hoje à noite / sábado)

### A — Fechar #552 (`feature`)

| Passo | Notas |
| ----- | ----- |
| CI da **#1816** | `check-all` local já rodou antes do push da correção SSRF |
| Merge | `Closes #552` (e as ADRs no corpo do PR) — **não** `gh issue close` à mão |

### B — Terminar #553 (`feature`)

| Fatia | Notas |
| ----- | ----- |
| Part A | Planilha ODS + **`_REPORT_FILENAME_PATTERN`** `.xlsx`\|`.ods` + stem do heatmap; commit em **`feat/report-multiformat-553`** depois do `check-all` |
| Part B | pandoc GRC DOCX/ODT/PDF — fail-soft; PDF Enterprise + lualatex; **não** empilhar na #1816 |

### C — Drift de docs da #1061

- [ ] `PLANS_TODO.md` ainda lista **#1061** como restante da survey v1.8.0 — um commit **`docs`** (não misturar com ODS). Ponteiro: tortoise **#14**.

### D — Opcional (não padrão nesta noite)

- Dependabot **um** PR (`deps`) — fila reaberta
- Encerramento das duas semanas **2026-08-29**: item Semana 2 restante ou adiamento com data ([#1601](https://github.com/DataBoar/data-boar/issues/1601) / [#1453](https://github.com/DataBoar/data-boar/issues/1453))

---

## Carryover — linhas do dia

- [ ] Mergear **#1816** quando verde → **#552** fecha sozinha
- [ ] Commit + PR **#553** Part A (ODS + allowlist); Part B em seguida
- [ ] **`docs`:** tirar **#1061** da survey v1.8.0 restante em `PLANS_TODO.md` (`plans-stats.py --write` se as linhas do dashboard mudarem)
- [ ] Reabrir a linha Dependabot do carryover até triar os PRs de **2026-08-28**
- [ ] Criar ou reler **`OPERATOR_TODAY_MODE_2026-08-29.md`** (último dia do ciclo de duas semanas)

---

## Fim do dia

- **`block-close`** + VeraCrypt (política privada do homelab) · **`eod-sync`** para git/gh
- Amanhã: **`OPERATOR_TODAY_MODE_2026-08-29.md`** (criar a partir deste se precisar)

---

## Refs rápidas

- [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md) · [PLANS_TODO.md](../../plans/PLANS_TODO.md) · [PUBLISHED_SYNC.pt_BR.md](PUBLISHED_SYNC.pt_BR.md)
- Sessão: **`feature`**, **`deps`**, **`today-mode`**, **`eod-sync`**, **`block-close`**, **`pmo-view`**
