# “Today mode” do operador — 2026-04-01 (fatia release-ready, token-aware)

**English:** [OPERATOR_TODAY_MODE_2026-04-01.md](OPERATOR_TODAY_MODE_2026-04-01.md)

**Objetivo:** Fechar uma **fatia coesa e revisável** rumo a production readiness, sem criar backlog silencioso. Limites: **`carryover-sweep`** · **`eod-sync`** · **`scripts/operator-day-ritual.ps1`**.

---

## Bloco 0 — Verdade + carryover (≈ 15–25 min)

1) Percorre **[CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md)** — fecha, adia com data ou promove para PLANS/issue cada ⬜.
1) Confirma a verdade de versão (vê **[PUBLISHED_SYNC.pt_BR.md](PUBLISHED_SYNC.pt_BR.md)**):
   - **Publicado**: **`v1.6.8`** no GitHub + Docker Hub quando o pipeline de release estiver completo; se o Hub atrasar, regista isso ali — não prometas ao mercado uma versão que ainda não dá para puxar.
   - **Trabalho**: `main` deve bater com **`pyproject.toml`**; sufixos `-beta`/`-rc` são só de trabalho.

---

## Bloco A — Fechar a fatia Cursor/MCP + tracking de versão (≈ 30–60 min)

- Se ainda houver PR separando **trabalho** de **publicado** (ex.: fatia de docs **1.6.8**), fechar; senão, ignorar.
- Manter o PR **focado em workflow/docs**; não misturar feature/fix aqui.

**Gate token-aware:** `.\scripts\lint-only.ps1` é suficiente para esta fatia (já está verde localmente).

---

## Bloco B — WRB (Corporate-Entity-C) e evidência mínima (≈ 20–40 min)

- Usar o bloco para colar: **`docs/ops/WRB_DELTA_SNAPSHOT_2026-03-31.pt_BR.md`**
- Atualizar os bullets de “verdade de versão” se a linha de base tiver mudado (publicado **`v1.6.8`** conforme **PUBLISHED_SYNC**).
- Enviar o e-mail (ou adiar explicitamente com data no **CARRYOVER**).

---

## Bloco C — Slack ping proof-of-life (≈ 10–15 min)

- Seguir **`docs/ops/OPERATOR_NOTIFICATION_CHANNELS.pt_BR.md`** e registrar uma nota **CHAN-OK** quando o alerta em telefone + PC estiver confirmado.

---

## Critério de paragem

Fatia do dia **fechada** quando:

- **CARRYOVER** atualizado (sem pendência silenciosa).
- Qualquer PR de **versão/docs** necessário para verdade de publicação **1.6.8** está **fechado** ou **N/A** (vê **PUBLISHED_SYNC**).
- WRB foi **enviado** (ou adiado com data).
- Ping Slack foi **confirmado** (ou adiado com data).
