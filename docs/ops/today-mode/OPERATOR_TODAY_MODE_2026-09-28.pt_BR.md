# Modo today do operador — 2026-09-28 (re-ancoragem: RC + segurança no main, caminho GA)

**English:** [OPERATOR_TODAY_MODE_2026-09-28.md](OPERATOR_TODAY_MODE_2026-09-28.md)

**Manchete:** O **`main`** absorveu um dia forte de **BFF / RC / segurança**: **[#2011](https://github.com/DataBoar/data-boar/pull/2011)** (smoke Maestro RC + extras do sentinel, lado data-boar do maestro#91) e **[#2012](https://github.com/DataBoar/data-boar/pull/2012)** (**#2006** gate REST `pass_from_env`, **#2007** allowlist `login.microsoftonline.com`). **[#1992](https://github.com/DataBoar/data-boar/issues/1992)** fechada **completed**. Maestro: **#92** fechado; **#82** CREDIT_CARD → **Covered**. **Próximo:** fechar **maestro#91** (issue ainda aberta), **smoke no host de lab** (imagens podman; [#756](https://github.com/DataBoar/data-boar/issues/756)), fila **carrion-crow** (**#99** depois lote segurança), thread GA **1.8.0** **[#1980](https://github.com/DataBoar/data-boar/issues/1980)**.

**Relógio da workstation:** `2026-09-28` (domingo) · confirme com `date`.

**Plano de duas semanas:** [PLAN_TWO_WEEK_EXECUTION_NO_REGRESSION.pt_BR.md](../../plans/PLAN_TWO_WEEK_EXECUTION_NO_REGRESSION.pt_BR.md) — **2026-09-28 → 2026-10-11**

---

## Bloco 0 — Realidade matinal (Tier A)

1. **`git pull origin main`** (merge **#2012** no tip)
2. PRs abertas data-boar: sobretudo **Dependabot** (**#1997–#2001**)
3. **carrion-crow #99** antes do lote **#94–#101** (ordem do operador)
4. Puxar **`../maestro`** e **`../carrion-crow`**

---

## Vitórias no `main` (não reabrir)

| Item | Estado |
| ---- | ------ |
| **#2011** / **#2012** | ✅ Merge **28/set** |
| **#1992** | ✅ Fechada |
| **maestro#92** | ✅ Fechado |
| **Slowdown até ~09/09** | ✅ Encerrado |

---

## Um bloco focado (escolha **um** primário)

| P | Fatia |
| - | ----- |
| **P1** | Fechar **maestro#91** (evidência **#2011**; smoke no host de lab opcional ([#756](https://github.com/DataBoar/data-boar/issues/756))) |
| **P2** | Merge **carrion-crow #99** |
| **P3** | Continuar **maestro#82** |
| **P4** | **Dependabot** — um PR Actions |

---

## Carryover do dia

Ver [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md) e o arquivo EN para a tabela **PMO view** completa.

---

## Refs

[CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md) · [WORKBOARD.pt_BR.md](WORKBOARD.pt_BR.md) · [PLANS_TODO.md](../../plans/PLANS_TODO.md)
