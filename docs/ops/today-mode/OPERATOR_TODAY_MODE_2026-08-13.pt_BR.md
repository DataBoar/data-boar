# Modo today do operador — 2026-08-13 (Maestro #32 + packaging/deps)

**English:** [OPERATOR_TODAY_MODE_2026-08-13.md](OPERATOR_TODAY_MODE_2026-08-13.md)

**Manchete:** Ontem fechou o spinout Maestro **#8** + OTel de produto. Foco padrão: código de preflight **maestro#32** **ou** um Dependabot / **#1427** CI Windows — não ondas de pesquisa.

---

## Bloco 0 — Realidade (manhã)

1. **`main`:** `git pull origin main` (pós-#1551).
2. **Não reabrir:** OTel data-boar **#1529/#1535/#1540** · maestro **#8** · docs packaging **#1541/#1542**.
3. **Gate humano:** Maestro **ADR-0001** ainda Proposed até você Aceitar.
4. - [ ] **`carryover-sweep` / `morning-readiness`** · **`block-close`** / **`eod-sync`** nos limites.

**Fila viva:** [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md) · Ontem: [OPERATOR_TODAY_MODE_2026-08-12.pt_BR.md](OPERATOR_TODAY_MODE_2026-08-12.pt_BR.md)

### Social / editorial (~2 min)

- [ ] Skim `docs/private/social_drafts/editorial/SOCIAL_HUB.md` (Alvo hoje/amanhã).

---

## Sequência sugerida

### A — Maestro (preferido se o foco for lab)

1. Operador: ADR-0001 → Accepted (se travado).
2. [maestro#32](https://github.com/DataBoar/maestro/issues/32) PR fino de implementação.
3. Lab: garantir `MAESTRO_ROOT` / clone sibling após pull do data-boar.

### B — packaging / deps no data-boar

1. Um de: Dependabot **#1487 / #1485 / #1484** · [#1427](https://github.com/DataBoar/data-boar/issues/1427).
2. Opcional: [#1538](https://github.com/DataBoar/data-boar/issues/1538).

### C — Fora do padrão

- Pesquisa #1518 / #1520 / #1521
- Reintroduzir `scripts/maestro/` no data-boar

---

## Carryover — linhas do dia

- [ ] Escolher **um** de A ou B
- [ ] Atualizar CARRYOVER se fechar linha
- [ ] Sem issues de inspiração sem AIIDCOBPP + P*

---

## Refs rápidas

- `scripts/Resolve-MaestroRoot.ps1` · [DataBoar/maestro](https://github.com/DataBoar/maestro)
- `docs/ops/TOKEN_AWARE_SCRIPTS_HUB.md`
