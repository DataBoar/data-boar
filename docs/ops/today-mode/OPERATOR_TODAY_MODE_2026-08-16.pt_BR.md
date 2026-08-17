# Modo today do operador — 2026-08-16 (renovação do ciclo de 2 semanas + #1602)

**English:** [OPERATOR_TODAY_MODE_2026-08-16.md](OPERATOR_TODAY_MODE_2026-08-16.md)

**Manchete (fechamento):** Docs do ciclo de duas semanas + **#1602** em `main` (**#1604**). Matriz TCP peer-pin **#1586** **fechada** (**#1603**). Próximo foco: Dependabot (**#1573** / majors) → fatia Semana 2 (**#1601** ou M-PILOT nomeado).

**Relógio da workstation (este arquivo):** `2026-08-16` (−03). Issue **#1586** fechada **2026-08-17** UTC (mesma noite −03).

**Plano de duas semanas:** [PLAN_TWO_WEEK_EXECUTION_NO_REGRESSION.pt_BR.md](../../plans/PLAN_TWO_WEEK_EXECUTION_NO_REGRESSION.pt_BR.md)

---

## Bloco 0 — Realidade

1. **`main`:** sincronizado até **`88249008`** (`docs(ops): two-week cycle…` **#1604**).
2. **PRs produto / docs:** **#1602** ✅ mergeado. Nenhum PR de produto aberto obrigatório para fechar o dia.
3. **PRs abertos (Dependabot — não mergear às cegas):**
   - [#1573](https://github.com/DataBoar/data-boar/pull/1573) setup-python **7** (Actions major)
   - [#1487](https://github.com/DataBoar/data-boar/pull/1487) reportlab **5** · [#1485](https://github.com/DataBoar/data-boar/pull/1485) webauthn **3** · [#1484](https://github.com/DataBoar/data-boar/pull/1484) pyarrow **25**
4. - [x] **`carryover-sweep` / refresh de realidade** · **`block-close`** / **`eod-sync`** nas fronteiras.

**Fila viva:** [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md) · Dia anterior: [OPERATOR_TODAY_MODE_2026-08-15.pt_BR.md](OPERATOR_TODAY_MODE_2026-08-15.pt_BR.md) · Próximo: [OPERATOR_TODAY_MODE_2026-08-17.pt_BR.md](OPERATOR_TODAY_MODE_2026-08-17.pt_BR.md)

### Social / editorial (~2 min)

- [ ] Passar o olho em `docs/private/social_drafts/editorial/SOCIAL_HUB.md` (Alvo **2026-08-16** / **2026-08-17**).

---

## Sequência sugerida (resultado)

### A — Âncora do ciclo — ✅

| Passo | Item | Notas |
| ----- | ---- | ----- |
| 1 | Renovar plano de duas semanas | EN + pt-BR (**2026-08-16 → 2026-08-29**) — **#1604** |
| 2 | Merge **#1602** | ✅ |
| 3 | Confirmar `main` verde | Reconferir após merges tardios (`gh run list --workflow ci.yml -L 3`) |

### B — Dependabot (`deps`) — ainda aberto

Triagem com **`.cursor/skills/dependabot-recommendations/SKILL.md`**. Preferir **Actions** antes de **major** Python.

| Ordem | PR | Notas |
| ----- | -- | ----- |
| 1 | [#1573](https://github.com/DataBoar/data-boar/pull/1573) | Major Actions — changelog + matriz CI |
| 2 | Majors **#1487 / #1485 / #1484** | Um por vez; `check-all` + smoke |

### C — #1586 pin TCP — ✅ Feito

Fechada via **#1603** (Oracle). Matriz completa: **#1589–#1603** (incl. SSOT **#1598** / **#1588**). Sem residual nesta mother issue.

### D — Não era padrão deste dia (leva para Semana 2 / amanhã)

- Runtime completo **#1601** RUM
- Maestro **#32** OTel preflight, salvo foco de lab

---

## Carryover — linhas do dia

- [x] Docs do ciclo de duas semanas em `main` (**#1604**)
- [x] Merge **#1602**
- [ ] Triar **≥1** PR Dependabot (preferir Actions **#1573**) — adiado para **2026-08-17**
- [x] Atualizar **CARRYOVER** com **#1586** Feito + deps
- [x] Sem commit de produto sem `check-all` / CI verde nesse PR

---

## Fim do dia

- **`block-close`** + VeraCrypt (política privada) ao sair de bloco profundo
- **`eod-sync`** para git/gh/PR + ponteiro de amanhã
- Arquivo de amanhã: **[OPERATOR_TODAY_MODE_2026-08-17.pt_BR.md](OPERATOR_TODAY_MODE_2026-08-17.pt_BR.md)**

---

## Refs rápidas

- [PLAN_TWO_WEEK_EXECUTION_NO_REGRESSION.pt_BR.md](../../plans/PLAN_TWO_WEEK_EXECUTION_NO_REGRESSION.pt_BR.md)
- Issue [#1586](https://github.com/DataBoar/data-boar/issues/1586) (fechada) · [#1601](https://github.com/DataBoar/data-boar/issues/1601) · skill **dependabot-recommendations**
- `docs/ops/TOKEN_AWARE_SCRIPTS_HUB.md` · sessão: **`deps`**, **`feature`**, **`today-mode`**, **`pmo-view`**, **`carryover-sweep`**
