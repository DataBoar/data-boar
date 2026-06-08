# Modo de hoje do operador — 2026-06-08 (Maestro musl + frota lab)

**English:** [OPERATOR_TODAY_MODE_2026-06-08.md](OPERATOR_TODAY_MODE_2026-06-08.md)

**Nota:** Rascunhado no **eod-sync** após **2026-06-07** — espelhamento da frota em **`docs/private/homelab/`** (eMachines Alpine, incidente PSU ML310e, hub procurement). IPs e aliases SSH ficam só em notas privadas **gitignored**.

**Âncora da `main`:** `19b171cd` — **#778** zizmor online findings mergeado (trilha **#777** / **#776**). **`gh auth`** estava expirado no EOD — renovar antes do ritual de merge de PRs.

---

## Bloco 0 — Realidade da manhã (10–15 min)

Rode **`carryover-sweep`** ou **`.\scripts\operator-day-ritual.ps1 -Mode Morning`**. Depois:

1. **`origin/main`:** `git fetch` · `git status -sb` · `git pull origin main` se estiver atrás — confirme **`ci.yml`** verde na **`main`** antes de trabalho profundo.
2. **PRs abertos:** `gh auth login` se precisar · `gh pr list --state open` — mergear quando verde via **`.\scripts\pr-merge-when-green.ps1`**.
3. **Stack privado:** atualização de frota **2026-06-07** enviada para **lab-latitude**, **lab-mini-bt**, **pCloud**; **lab-t14** + **VeraCrypt `Z:`** pulados (offline/desmontado). Se `docs/private/` mudar durante a noite: **`.\scripts\private-git-sync.ps1 -Push`**.

**Fila contínua:** [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md) · **Publicado:** [PUBLISHED_SYNC.pt_BR.md](PUBLISHED_SYNC.pt_BR.md)

---

## COMECE AQUI — Maestro + **alpine-emachines** (5º nó do completão)

> **Build musl no container Alpine no T14 — provado 2026-06-07.** Amanhã valida **open-core** no baremetal **apk/musl** (não só `uv sync` + `--help`). Checklist privado: **`docs/private/homelab/LAB_OP_FLEET_UPDATE_2026-06-07.pt_BR.md`** · inventário Maestro já inclui **`alpine-emachines`**.

| Passo | Ação |
| ----- | ---- |
| 1 | **`ssh alpine`** (ou **`emachines`**) — confirmar clone em **`~/Projects/dev/data-boar`**; se faltar: clone + **`uv sync`** no host. |
| 2 | Incluir **`alpine-emachines`** na orquestra do completão / lista Maestro (5º nó: musl/apk/baremetal). |
| 3 | **Matriz open-core** (na unha ou Maestro): scan PII (`~`, `/var/log`); exports (xlsx/ODF/JSON/PDF); arquivos (7z/zip+senha); storage compartilhado (sshfs/cifs/nfs); imports de drivers DB (MariaDB/MySQL/Oracle/Postgres/MSSQL conforme pyproject); **`main.py --web`** + **curl** health/status/report. |
| 4 | Registrar evidência em **`docs/private/homelab/reports/`**; **`private-git-sync.ps1 -Push`** ao fechar. |

Token de sessão: **`completao`** · **`homelab`**.

---

## Secundário (mesmo dia se couber)

| Prioridade | Item | Notas |
| ---------- | ---- | ----- |
| **Lab** | **#756** disco mini-bt | Ainda em [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md) — liberar espaço antes de completão pesado no **mini-bt** |
| **Procurement** | ML310e **CV550** | Privado **`procurement/PSU-ML310e-Gen8-CV550.pt_BR.md`** — servidor bloqueado até a fonte |
| **Procurement** | Gate RAM T14 | **`sudo dmidecode -t memory`** no T14 antes de comprar DDR5 — privado **`RAM-T14-DDR5-64GB-SODIMM.pt_BR.md`** |
| **Plans** | **#753** arquivo CMDB | Scaffold **`PLAN_CMDB_CI_RELATIONSHIP_IMPORT.md`** quando abrir faixa de produto |

---

## Fim do dia (**2026-06-08**)

- **`eod-sync`** + **`private-stack-sync`** se relatórios homelab privados ou hub social mudarem.
- Checklist de amanhã: **`OPERATOR_TODAY_MODE_2026-06-09.md`** (criar no próximo **eod-sync** se faltar).

---

## Referências rápidas

- Tokens de sessão: **`.cursor/rules/session-mode-keywords.mdc`** (**`completao`**, **`homelab`**, **`eod-sync`**, **`private-stack-sync`**)
- Hub frota privado: **`docs/private/homelab/LAB_OP_FLEET_UPDATE_2026-06-07.pt_BR.md`**
- Ritmo privado: **`docs/private/TODAY_MODE_CARRYOVER_AND_FOUNDER_RHYTHM.md`**
