# Modo today do operador — 2026-08-12 (OTel de produto + fechamento spinout Maestro #8)

**English:** [OPERATOR_TODAY_MODE_2026-08-12.md](OPERATOR_TODAY_MODE_2026-08-12.md)

**Manchete (EOD):** Gaps OTel de produto **#1529 / #1535 / #1540** fechados no data-boar; companion do spinout Maestro [PR #1551](https://github.com/DataBoar/data-boar/pull/1551) mergeado (`69c8ee0d`) — `scripts/maestro/` removido; [DataBoar/maestro#8](https://github.com/DataBoar/maestro/issues/8) **CLOSED**; [#32](https://github.com/DataBoar/maestro/issues/32) desbloqueada para **código** de preflight OTel. Operador ainda dono de **ADR-0001 Proposed → Accepted**.

---

## Bloco 0 — Realidade (EOD)

1. **`main`:** no merge do #1551 — `git pull origin main` antes da próxima edição.
2. **Fechado hoje (não reabrir):**
   - [#1529](https://github.com/DataBoar/data-boar/issues/1529) LoggerProvider → PR **#1544**
   - [#1535](https://github.com/DataBoar/data-boar/issues/1535) OTel oneshot CLI → PR **#1547**
   - [#1540](https://github.com/DataBoar/data-boar/issues/1540) plano preflight Maestro → PR **#1548** (código = maestro#32)
   - [#1541](https://github.com/DataBoar/data-boar/issues/1541) links packaging → fechada
   - [#1542](https://github.com/DataBoar/data-boar/issues/1542) Status plano lab observability → PR **#1545**
   - Dependabot **#1492** virtualenv → mergeado
   - **Maestro** [#8](https://github.com/DataBoar/maestro/issues/8) spinout incompleto → companion **data-boar#1551** + paridade **maestro#33/#34**
3. **Ainda aberto / próximo:** ver carryover + sequência abaixo.
4. - [x] **`eod-sync`** neste limite · **`block-close`** se pausar lab/VC depois.

**Fila viva:** [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md) · **Publicado:** [PUBLISHED_SYNC.pt_BR.md](PUBLISHED_SYNC.pt_BR.md)

### Social / editorial (~2 min)

- [ ] Skim `docs/private/social_drafts/editorial/SOCIAL_HUB.md` (alvos hoje/amanhã).

---

## Inventário meio-caminho (após os ships de hoje)

| Faixa | Item | Estado | Próxima fatia |
| ----- | ---- | ------ | ------------- |
| **Maestro OTel** | [maestro#32](https://github.com/DataBoar/maestro/issues/32) código de preflight | OPEN · desbloqueada | Implementar em DataBoar/maestro `core/`/`engine/` |
| **Gate humano ADR** | Maestro ADR-0001 | Proposed | Operador: **Accepted** quando travado |
| **Drift docs** | [#1538](https://github.com/DataBoar/data-boar/issues/1538) tiers / open-core | OPEN | Docs fino |
| **Packaging P1** | [#1427](https://github.com/DataBoar/data-boar/issues/1427) CI Windows zero jobs | OPEN · P1 | Bloqueia MSI/winget com [#1467](https://github.com/DataBoar/data-boar/issues/1467) |
| **Produto parcial** | [#828](https://github.com/DataBoar/data-boar/issues/828) scan_failures residual Pro | Parcial em `main` | Fixtures / fechar plano |
| **Lab hygiene** | [#756](https://github.com/DataBoar/data-boar/issues/756) disco ~90% + `bw` Ansible | Pendente | Liberar espaço antes de completão nesse host |
| **deps pendurados** | PRs **#1487** · **#1485** · **#1484** | OPEN | Skill de triage — **sem merge cego** |
| **Bestiário** | #994 (faltam 7 repos) | Em progresso | Um PR/repo |
| **Pesquisa estacionada** | #1518 / #1520 / #1521 | `no-code-yet` | **Não** padrão amanhã |
| **Deploy lab** | Hosts pré-#1551 | Ops | Pull data-boar + `MAESTRO_ROOT` / sibling `../maestro` |

---

## Sequência sugerida (amanhã / próximo bloco)

### A — Follow-through Maestro

1. Operador: **ADR-0001 → Accepted** (se a decisão estiver travada).
2. [maestro#32](https://github.com/DataBoar/maestro/issues/32) implementação do preflight OTel.
3. Hosts de lab: pull `main` + path do clone Maestro para os wrappers.

### B — Packaging / deps (quando não for Maestro)

1. [#1427](https://github.com/DataBoar/data-boar/issues/1427) ou um Dependabot se a skill liberar.
2. Opcional: [#1538](https://github.com/DataBoar/data-boar/issues/1538).

### C — Explicitamente **fora** do padrão

- Ondas de pesquisa #1518 / #1520 / #1521
- Burn-down completo do bestiário
- Reintroduzir `data-boar/scripts/maestro/` (proibido — #8 fechada)

---

## Carryover — linhas do dia

- [x] Sync `main` / landar docs observability (#1542 / #1545)
- [x] Ship fatias OTel (#1529 / #1535 / plano #1540)
- [x] Companion Maestro #1551 + fechar maestro#8 + ping #32
- [x] Atualizar [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md) (este EOD)
- [ ] Operador: ADR-0001 Accepted
- [ ] No máximo **um** de: código maestro#32 · triage deps · #1427
- [ ] Sem issues de “inspiração” sem AIIDCOBPP + label P*

---

## Fim do dia

- `eod-sync` / `block-close` conforme o limite
- Rascunhar `OPERATOR_TODAY_MODE_2026-08-13.md` se A for o foco do próximo dia

---

## Refs rápidas

- `docs/ops/TOKEN_AWARE_SCRIPTS_HUB.md` · `scripts/Resolve-MaestroRoot.ps1`
- `.cursor/rules/session-mode-keywords.mdc` (`pmo-view`, `today-mode`, `eod-sync`)
- `docs/ops/COMMIT_AND_PR.pt_BR.md`
- [DataBoar/maestro](https://github.com/DataBoar/maestro)
