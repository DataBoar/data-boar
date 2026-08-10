# Today mode do operador — 2026-08-10 (higiene de labels + sequencing pós-pausa Claude)

**English:** [OPERATOR_TODAY_MODE_2026-08-10.md](OPERATOR_TODAY_MODE_2026-08-10.md)

**Manchete:** ~38 issues novas no org (maioria R&D em `data-boar-shared`); P1 **#1515** já fechado; Claude em pausa (~96% weekly → refil ~17h); lab adversário Strix/Caido em paralelo; hygiene de **labels ↔ títulos** + sequencing abaixo **sem atropelar** carryover / deps / bestiário.

---

## Bloco 0 — Realidade (agora / tarde)

1. **`main`:** sync quando for mexer em código (`git fetch` / `git pull origin main`).
2. **Outros assuntos em voo (não abandonar):**
   - Carryover bestiário / Maestro / private stack — [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md)
   - Dependabot abertos no core (#1492, #1487, #1485, #1484…) — triagem `deps`, sem merge cego
   - Lab adversário (Strix + Caido + qwen/`--demo` 1.7.4-post12) — só promover a issue/lesson quando estabilizar
3. **Stripe MCP:** plugin instalado; OAuth ainda no desktop se quiser tools ao vivo.
4. - [ ] **`block-close`** ao pausar lab/VC; **`eod-sync`** se fechar o dia calendário.

**Fila viva:** [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md) · **Publicado:** [PUBLISHED_SYNC.pt_BR.md](PUBLISHED_SYNC.pt_BR.md)

### Social / editorial (~2 min)

- [ ] Olhar `docs/private/social_drafts/editorial/SOCIAL_HUB.md` (alvo hoje/amanhã).

---

## Hygiene feita (labels ↔ títulos) — 2026-08-10

| Repo | Ação |
| ---- | ---- |
| `data-boar` | #1517/#1526 → `P3`+docs; #1518/#1520/#1521 → `P2`+`no-code-yet`; #1527 → `P3`; #1525 → `no-code-yet` |
| `data-boar-shared` | #34–51: `P2`/`P3` + `doutrina`/`governanca`/`documentation` conforme título |
| `data-boar-sdk` | #7–9 → `P2` (+ labels P2/P3 criadas no repo) |
| `sage-remora` | #20 → `P3` + **título clarificado** (conclusão ≠ missão Remora) + comentário |
| `tidy-tortoise` / `design-system` / `homing-robin` | #13–14 / #9 / #27 → `P2` |
| `data-boar-site` | #67 já `P3` (+ documentation se aceito) |

---

## Sequencing sugerido (pós-refil / resto do dia)

Ordem **dentro da banda**, sem abrir nova frente até fechar a fatia atual dos “outros assuntos”.

### A — Terminar o que já está em voo (antes de R&D novo)

1. Uma fatia de **carryover** (bestiário PR/repo **ou** Maestro private **ou** private-stack-sync se tree suja).
2. Lab adversário: 1 parágrafo de evidência → shared **#46** *ou* lesson pública — **só** se o run estabilizar (senão defer com data).
3. Opcional fino `deps`: um PR Dependabot só se verde + skill de triagem.

### B — Thin ship no core (Claude-light / Cursor)

| Ordem | Issue | Por quê |
| ----- | ----- | ------- |
| B1 | [#1517](https://github.com/DataBoar/data-boar/issues/1517) UID 65532 | Doc drift óbvio; PR minúsculo |
| B2 | [#1526](https://github.com/DataBoar/data-boar/issues/1526) methodology cross-links | HITL já; fecha fatia docs de #1525 |
| B3 | [#1524](https://github.com/DataBoar/data-boar/issues/1524) mapa Mermaid | Só se a PMO visual estiver atrapalhando |

### C — Doutrina bela (1 fatia, não 18)

| Ordem | Issue | Por quê |
| ----- | ----- | ------- |
| C1 | shared [#37](https://github.com/DataBoar/data-boar-shared/issues/37) → [#50](https://github.com/DataBoar/data-boar-shared/issues/50) | Negative capability → testes |
| C2 | sdk [#7](https://github.com/DataBoar/data-boar-sdk/issues/7) + handoff Remora↔Ferret | Envelope; missões ortogonais (metadados vs grant completo) |
| C3 | tortoise [#13](https://github.com/DataBoar/tidy-tortoise/issues/13) | Preview destrutivo — segurança operacional |

### D — Explicitamente **não** hoje (horizonte)

- core #1518 / #1520 / #1521 (research)
- remora #20 corpo completo (só hygiene de título já feita)
- shared #34–36, #39–42, #45, #48, #51 — backlog R&D rotulado, sem commitment

---

## Carryover — linhas do dia

- [ ] Hygiene labels (acima) — **feito** nesta sessão Cursor
- [ ] Remora #20 título/comentário — **feito**
- [ ] Escolher **uma** de A + no máx. **uma** de B ou C após ~17h
- [ ] Não abrir mais issues “inspiração” sem trailing AIIDCOBPP + label P*

---

## Fim do dia

- `block-close` / `eod-sync` conforme fronteira
- Preparar `OPERATOR_TODAY_MODE_2026-08-11.pt_BR.md` só se o sequencing A–C mudar

---

## Referências rápidas

- `docs/ops/TOKEN_AWARE_SCRIPTS_HUB.pt_BR.md`
- `.cursor/rules/session-mode-keywords.mdc`
- `docs/ops/COMMIT_AND_PR.pt_BR.md`
