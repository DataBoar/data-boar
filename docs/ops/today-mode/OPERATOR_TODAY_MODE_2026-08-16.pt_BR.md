# Modo today do operador — 2026-08-16 (renovação do ciclo de 2 semanas + #1602)

**English:** [OPERATOR_TODAY_MODE_2026-08-16.md](OPERATOR_TODAY_MODE_2026-08-16.md)

**Manchete:** Renovar ciclo de **duas semanas** (**2026-08-16 → 2026-08-29**) → merge **[#1602](https://github.com/DataBoar/data-boar/pull/1602)** quando verde → triagem Dependabot → continuar **#1586** se houver capacidade.

**Relógio da workstation (este arquivo):** `2026-08-16` (−03).

**Plano de duas semanas:** [PLAN_TWO_WEEK_EXECUTION_NO_REGRESSION.pt_BR.md](../../plans/PLAN_TWO_WEEK_EXECUTION_NO_REGRESSION.pt_BR.md)

---

## Bloco 0 — Realidade

1. **`main`:** `git fetch` + `git pull origin main`.
2. **PRs abertos (produto / docs):**
   - [#1602](https://github.com/DataBoar/data-boar/pull/1602) — gates de observabilidade cross-surface (docs/backlog) — **merge com Tests verdes**.
3. **PRs abertos (Dependabot — não mergear às cegas):**
   - [#1573](https://github.com/DataBoar/data-boar/pull/1573) setup-python **7** (Actions major)
   - [#1487](https://github.com/DataBoar/data-boar/pull/1487) reportlab **5** · [#1485](https://github.com/DataBoar/data-boar/pull/1485) webauthn **3** · [#1484](https://github.com/DataBoar/data-boar/pull/1484) pyarrow **25**
4. - [ ] **`carryover-sweep` / `morning-readiness`** no início · **`block-close`** / **`eod-sync`** nas fronteiras.

**Fila viva:** [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md) · Dia anterior: [OPERATOR_TODAY_MODE_2026-08-15.pt_BR.md](OPERATOR_TODAY_MODE_2026-08-15.pt_BR.md)

### Social / editorial (~2 min)

- [ ] Passar o olho em `docs/private/social_drafts/editorial/SOCIAL_HUB.md` (Alvo **2026-08-16** / **2026-08-17**).

---

## Sequência sugerida

### A — Fechar a âncora do ciclo

| Passo | Item | Notas |
| ----- | ---- | ----- |
| 1 | Renovar plano de duas semanas | Tabela do ciclo EN + pt-BR (**2026-08-16 → 2026-08-29**) — esta sessão |
| 2 | Merge **#1602** | Hub **não** deve incluir planos só locais/untracked |
| 3 | Confirmar `main` verde | `gh run list --workflow ci.yml -L 3` após o merge |

### B — Dependabot (`deps`)

Triagem com **`.cursor/skills/dependabot-recommendations/SKILL.md`**. Preferir **Actions** antes de **major** Python.

| Ordem | PR | Notas |
| ----- | -- | ----- |
| 1 | [#1573](https://github.com/DataBoar/data-boar/pull/1573) | Major Actions — changelog + matriz CI |
| 2 | Majors **#1487 / #1485 / #1484** | Um por vez; `check-all` + smoke |

### C — #1586 pin TCP (se sobrar energia)

| Passo | Item | Notas |
| ----- | ---- | ----- |
| 1 | Pin Redis (subclass) | Próximo após Postgres/Mongo em `main` |
| 2 | MySQL / Oracle | Caso a caso |
| — | mssql | Adiado → [#1588](https://github.com/DataBoar/data-boar/issues/1588) |

### D — Não é padrão hoje

- Runtime completo **#1601** RUM (Semana 2 após #1602)
- Maestro **#32** OTel preflight, salvo foco de lab ganhar

---

## Carryover — linhas do dia

- [ ] Docs do ciclo de duas semanas em branch/PR **docs** (ou após merge do #1602)
- [ ] Merge **#1602** quando verde
- [ ] Triar **≥1** PR Dependabot (preferir Actions)
- [ ] Atualizar **CARRYOVER** se #1586 / deps mudarem de status
- [ ] Sem commit de produto sem `check-all` / CI verde nesse PR

---

## Fim do dia

- **`block-close`** + VeraCrypt (política privada) ao sair de bloco profundo
- **`eod-sync`** para git/gh/PR + ponteiro de amanhã
- Arquivo de amanhã: **`OPERATOR_TODAY_MODE_2026-08-17.md`** (criar a partir deste se precisar)

---

## Refs rápidas

- [PLAN_TWO_WEEK_EXECUTION_NO_REGRESSION.pt_BR.md](../../plans/PLAN_TWO_WEEK_EXECUTION_NO_REGRESSION.pt_BR.md)
- Issue [#1586](https://github.com/DataBoar/data-boar/issues/1586) · [#1601](https://github.com/DataBoar/data-boar/issues/1601) · skill **dependabot-recommendations**
- `docs/ops/TOKEN_AWARE_SCRIPTS_HUB.md` · sessão: **`deps`**, **`feature`**, **`today-mode`**, **`pmo-view`**, **`carryover-sweep`**
