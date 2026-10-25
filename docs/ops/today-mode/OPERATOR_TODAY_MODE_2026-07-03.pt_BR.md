# Today mode do operador — 2026-07-03 (Pós-#828 · doutrina bestiário · Maestro)

**English:** [OPERATOR_TODAY_MODE_2026-07-03.md](OPERATOR_TODAY_MODE_2026-07-03.md)

**Manchete:** **`main`** recebeu **#1146** (fatia open-core **#828** + Bugbot) · retomar **sidequest doutrina** (10 repos — SOUL do vault → DOUTRINA + ADRs) · depois **Maestro** privado (**PR #9** migração fase 1).

**Âncora `main` (EOD 2026-07-03 ~00:20 -03):** merge **#1146** · **`pyproject.toml`** = **`1.7.4.post1`**. **Estável:** [PUBLISHED_SYNC.pt_BR.md](PUBLISHED_SYNC.pt_BR.md).

**Esta noite em `main`:** **#1144** (#1140 SQL `sampling_error`) · **#1146** (#828 `scan_failures` + barrier interno, CRC-32, reasons 7z).

---

## Bloco 0 — Manhã (10–15 min)

**`carryover-sweep`** / **`morning-readiness`**. Depois:

1. **`git fetch`** · **`git checkout main`** · **`git pull origin main`** (local pode estar **divergente**).
2. **CI** em `main` após merge **#1146**.
3. **PRs:** **#1132** · **#1143** (draft) · **#1122** / **#1124**.
4. **Issue #828** ainda **aberta** — open-core entrou; Pro/fixtures/plano ficam.
5. **Bestiário:** `~/.local/bin/bestiais-*.sh` ou script local `beastie-ecosystem-sync` (script gitignored no `main`; **today-mode é público** — **#1147**).
6. **`private-stack-sync`** se `docs/private/` mudou.

**Fila:** [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md)

### Social (~2 min)

- [ ] **`docs/private/social_drafts/editorial/SOCIAL_HUB.md`**

---

## Prioridades

| Ordem | Trilha | Intenção |
| ----- | ------ | -------- |
| **1** | **Sidequest doutrina (10 repos)** | SOUL vault → DOUTRINA + ADRs; marcar AC nas issues · **um PR por repo** |
| **2** | **Maestro** (`FabioLeitao/maestro`) | **PR #9** migração fase 1 · **PR #7** skeleton |
| **3** | **#828** (público) | Fixtures · paths corrompidos · plano Pro |
| **4** | **PRs data-boar** | **#1132** / **#1143** / docs |
| **5** | **Adiar** | Dependabot RED |

---

## Onde paramos — Maestro + bestiais

- **Housekeeping mecânico (01/jul):** inventário honesto; Homing Robin birth-triplet; fila apontava **Maestro `set-remote`**.
- **Sidequest doutrina (02/jul):** Faithful Ferret, Sage Remora, Stealthy Stoat **rascunhados localmente**; faltam merges/PRs nos outros 7.
- **Maestro hoje:** branch **`feat/phase1-migrate-from-data-boar`** · **PR #9** aberto (migração ADR-0001) — **avançou além** do só `set-remote`.

---

## Fim do dia

- **`eod-sync`** + **`private-stack-sync`**
- Próximo: **`OPERATOR_TODAY_MODE_2026-07-04.md`**
