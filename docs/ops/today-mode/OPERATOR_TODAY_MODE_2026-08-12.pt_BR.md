# Modo today do operador — 2026-08-12 (recuperar meio-caminho + docs de observabilidade)

**English:** [OPERATOR_TODAY_MODE_2026-08-12.md](OPERATOR_TODAY_MODE_2026-08-12.md)

**Manchete:** Lacuna desde o today-mode **2026-08-10**; sessão de lab observability (**2026-08-11→12**) deixou **drift de plano/doc** e gaps de OTel de produto abertos. Preferir **fechar docs quase prontos** antes de novas ondas de pesquisa. Dependabot ainda pendurado.

---

## Bloco 0 — Realidade (manhã)

1. **`main`:** sync (`git fetch` / `git pull origin main`) antes de editar.
2. **Fechado desde 2026-08-10 (não reabrir):**
   - [#1517](https://github.com/DataBoar/data-boar/issues/1517) UID 65532 → PR **#1530**
   - [#1526](https://github.com/DataBoar/data-boar/issues/1526) methodology → PR **#1531**
   - [#1524](https://github.com/DataBoar/data-boar/issues/1524) mapa de issues → PR **#1533**
   - [#1537](https://github.com/DataBoar/data-boar/issues/1537) gaps de conectores → PR **#1539**
   - CARRYOVER Maestro fase 1 → PR **#1532**
3. **Em voo / meio-pronto:** ver sequência abaixo + [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md).
4. - [ ] **`block-close`** ao pausar lab/VC; **`eod-sync`** no EOD de calendário.

**Fila viva:** [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md) · **Publicado:** [PUBLISHED_SYNC.pt_BR.md](PUBLISHED_SYNC.pt_BR.md)

### Social / editorial (~2 min)

- [ ] Skim `docs/private/social_drafts/editorial/SOCIAL_HUB.md` (alvos hoje/amanhã).

---

## Inventário meio-caminho (parado ou quase pronto)

| Faixa | Item | Estado | Próxima fatia |
| ----- | ---- | ------ | ------------- |
| **Docs quase prontos** | [#1542](https://github.com/DataBoar/data-boar/issues/1542) — Status do `PLAN_LAB_OP_OBSERVABILITY_STACK` + receivers nativos | OPEN — lab feito, **header do plano velho** | Um PR só docs |
| **Drift docs** | [#1538](https://github.com/DataBoar/data-boar/issues/1538) tiers / open-core | OPEN | Docs fino |
| **Drift docs** | [#1541](https://github.com/DataBoar/data-boar/issues/1541) links MSI/Homebrew/Windows-CI no plano de packaging | Em PR — Related + tabela irmã + hedge brew no ADR-0085 | Merge do PR docs/ADR |
| **Gaps OTel produto** | [#1529](https://github.com/DataBoar/data-boar/issues/1529) LoggerProvider → Loki | OPEN · P3 | Depois do path de log do lab estável |
| **Gaps OTel produto** | [#1535](https://github.com/DataBoar/data-boar/issues/1535) OTel só em `--web`/`--demo` | OPEN | Design: oneshot CLI |
| **Maestro / lab** | [#1540](https://github.com/DataBoar/data-boar/issues/1540) preflight OTel no gate | OPEN | Verificar, não assumir |
| **Packaging P1** | [#1427](https://github.com/DataBoar/data-boar/issues/1427) CI Windows zero jobs | OPEN · P1 | Bloqueia narrativa MSI com [#1467](https://github.com/DataBoar/data-boar/issues/1467) |
| **Produto parcial** | [#828](https://github.com/DataBoar/data-boar/issues/828) scan_failures residual Pro | Parcial em `main` | Fixtures / fechar plano |
| **Lab hygiene** | [#756](https://github.com/DataBoar/data-boar/issues/756) disco ~90% + `bw` Ansible | Pendente | Liberar espaço antes de completão nesse host |
| **deps pendurados** | PRs **#1492** · **#1487** · **#1485** · **#1484** | OPEN | Skill de triage — **sem merge cego** |
| **Bestiário** | #994 (faltam 7 repos) | Em progresso | Um PR/repo |
| **Pesquisa estacionada** | #1518 / #1520 / #1521 | `no-code-yet` | **Não** hoje |

---

## Sequência sugerida (2026-08-12)

### A — Quase pronto primeiro

1. **[#1542](https://github.com/DataBoar/data-boar/issues/1542)** — Status do plano + inventário de receivers.
2. Opcional: **#1541** ou um Dependabot se verde + skill ok.

### B — Observabilidade de produto

| Ordem | Issue | Por quê |
| ----- | ----- | ------- |
| B1 | [#1529](https://github.com/DataBoar/data-boar/issues/1529) LoggerProvider | Prova em Loki |
| B2 | [#1535](https://github.com/DataBoar/data-boar/issues/1535) OTel oneshot | Mesmo tema |
| B3 | [#1540](https://github.com/DataBoar/data-boar/issues/1540) preflight Maestro | Honestidade do gate |

### C — Packaging / Windows (quando o foco for packaging)

1. [#1427](https://github.com/DataBoar/data-boar/issues/1427) job Windows no CI.

### D — Explicitamente **fora** do padrão de hoje

- Ondas de pesquisa #1518 / #1520 / #1521
- Burn-down completo do bestiário
- Adoção Graylog / Phase D (fora do escopo do #1542)

---

## Carryover — linhas do dia

- [x] Sync `main` (esta sessão)
- [ ] Landar ou agendar PR do **#1542**
- [ ] Atualizar [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md) (este PR)
- [ ] No máximo **um** de: triage deps · #1541 · spike B1 #1529
- [ ] Sem issues de “inspiração” sem AIIDCOBPP + label P*

---

## Fim do dia

- `block-close` / `eod-sync` conforme o limite
- Rascunhar `OPERATOR_TODAY_MODE_2026-08-13.md` só se A–C mudar

---

## Refs rápidas

- `docs/ops/TOKEN_AWARE_SCRIPTS_HUB.md`
- `.cursor/rules/session-mode-keywords.mdc` (`pmo-view`, `today-mode`, `carryover-sweep`)
- `docs/ops/COMMIT_AND_PR.pt_BR.md`
- `docs/plans/PLAN_LAB_OP_OBSERVABILITY_STACK.md`
