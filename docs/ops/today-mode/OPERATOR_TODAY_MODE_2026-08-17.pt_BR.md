# Modo today do operador — 2026-08-17 (deps + primária Semana 2)

**English:** [OPERATOR_TODAY_MODE_2026-08-17.md](OPERATOR_TODAY_MODE_2026-08-17.md)

**Manchete:** Depois do fechamento **#1586** + docs do ciclo em `main` → triar **Dependabot** (Actions **#1573** primeiro) → escolher **uma** entrega Semana 2 (**#1601** piloto RUM **ou** sample **#1453** CMMC **ou** bloqueador M-PILOT nomeado).

**Relógio da workstation (este arquivo):** confirmar com `date` / `Get-Date` na workstation (−03).

**Plano de duas semanas:** [PLAN_TWO_WEEK_EXECUTION_NO_REGRESSION.pt_BR.md](../../plans/PLAN_TWO_WEEK_EXECUTION_NO_REGRESSION.pt_BR.md) (ciclo **2026-08-16 → 2026-08-29**)

---

## Bloco 0 — Realidade

1. **`main`:** `git fetch` + `git pull origin main` (esperar **#1586** / **#1602** / **#1604** já em `main`).
2. **PRs de produto abertos:** nenhum obrigatório; abrir só para a fatia do dia.
3. **Dependabot aberto (não mergear às cegas):**
   - [#1573](https://github.com/DataBoar/data-boar/pull/1573) setup-python **7**
   - [#1487](https://github.com/DataBoar/data-boar/pull/1487) reportlab **5** · [#1485](https://github.com/DataBoar/data-boar/pull/1485) webauthn **3** · [#1484](https://github.com/DataBoar/data-boar/pull/1484) pyarrow **25**
4. - [ ] **`carryover-sweep` / `morning-readiness`** · **`block-close`** / **`eod-sync`** nas fronteiras.

**Fila viva:** [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md) · Dia anterior: [OPERATOR_TODAY_MODE_2026-08-16.pt_BR.md](OPERATOR_TODAY_MODE_2026-08-16.pt_BR.md)

### Social / editorial (~2 min)

- [ ] Passar o olho em `docs/private/social_drafts/editorial/SOCIAL_HUB.md` (Alvo **2026-08-17** / **2026-08-18**).

---

## Sequência sugerida

### A — Dependabot (`deps`)

| Ordem | PR | Notas |
| ----- | -- | ----- |
| 1 | [#1573](https://github.com/DataBoar/data-boar/pull/1573) | Preferir primeiro — Actions major |
| 2 | Um de **#1487 / #1485 / #1484** | Skill + `check-all`; só um PR |

### B — Uma primária Semana 2 (`feature`)

Escolher **uma** (operador nomeia se estiver ambíguo):

| Candidato | Issue / plano | Notas |
| --------- | ------------- | ----- |
| Piloto RUM | [#1601](https://github.com/DataBoar/data-boar/issues/1601) · [PLAN_CROSS_SURFACE_OBSERVABILITY.md](../../plans/PLAN_CROSS_SURFACE_OBSERVABILITY.md) | Privacy-first; default OFF |
| Sample CMMC | [#1453](https://github.com/DataBoar/data-boar/issues/1453) | Docs/config sample |
| Lab / license | [#756](https://github.com/DataBoar/data-boar/issues/756) / [#719](https://github.com/DataBoar/data-boar/issues/719) | Só se o operador nomear como M-PILOT |

### C — Opcional (não padrão)

- Maestro [maestro#32](https://github.com/DataBoar/maestro/issues/32) OTel preflight (repo sibling)
- [#1427](https://github.com/DataBoar/data-boar/issues/1427) CI Windows (bloqueia MSI/winget **#1467**)

---

## Carryover — linhas do dia

- [ ] Triar **≥1** PR Dependabot
- [ ] Começar **ou** adiar com data a primária Semana 2
- [ ] Atualizar **CARRYOVER** se deps / #1601 mudarem
- [ ] Sem commit de produto sem `check-all` / CI verde

---

## Fim do dia

- **`block-close`** / **`eod-sync`**
- Arquivo de amanhã: **`OPERATOR_TODAY_MODE_2026-08-18.md`** (criar a partir deste se precisar)

---

## Refs rápidas

- [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md) · [PLANS_TODO.md](../../plans/PLANS_TODO.md) · skill **dependabot-recommendations**
- Sessão: **`deps`**, **`feature`**, **`today-mode`**, **`carryover-sweep`**
