# Operator today mode — 2026-06-08 (Maestro musl + lab fleet)

**Português (Brasil):** [OPERATOR_TODAY_MODE_2026-06-08.pt_BR.md](OPERATOR_TODAY_MODE_2026-06-08.pt_BR.md)

**Note:** Drafted at **eod-sync** after **2026-06-07** — private homelab fleet mirror landed in **`docs/private/homelab/`** (eMachines Alpine, ML310e PSU incident, procurement hub). Host IPs and SSH aliases stay in **gitignored** private notes only.

**`main` anchor:** `19b171cd` — **#778** zizmor online findings merged (**#777** / **#776** workflow security lane). **`gh auth`** was stale at eod — refresh before PR merge ritual.

---

## Block 0 — Morning reality (10–15 min)

Run **`carryover-sweep`** or **`.\scripts\operator-day-ritual.ps1 -Mode Morning`**. Then:

1. **`origin/main`:** `git fetch` · `git status -sb` · `git pull origin main` when behind — confirm **`ci.yml`** green on **`main`** before deep work.
2. **Open PRs:** `gh auth login` if needed · `gh pr list --state open` — merge when green per **`.\scripts\pr-merge-when-green.ps1`**.
3. **Private stack:** fleet update **2026-06-07** pushed to **lab-latitude**, **lab-mini-bt**, **pCloud**; **lab-t14** + **VeraCrypt `Z:`** skipped (offline/unmounted). If `docs/private/` changed overnight: **`.\scripts\private-git-sync.ps1 -Push`**.

**Rolling queue:** [CARRYOVER.md](CARRYOVER.md) · **Published:** [PUBLISHED_SYNC.md](PUBLISHED_SYNC.md)

---

## START HERE — Maestro + **alpine-emachines** (5th completão node)

> **Musl builds on T14 container — proven 2026-06-07.** Tomorrow validates **open-core** on baremetal **apk/musl** (not just `uv sync` + `--help`). Private checklist: **`docs/private/homelab/LAB_OP_FLEET_UPDATE_2026-06-07.pt_BR.md`** · Maestro inventory already lists **`alpine-emachines`**.

| Step | Action |
| ---- | ------ |
| 1 | **`ssh alpine`** (or **`emachines`**) — confirm clone at **`~/Projects/dev/data-boar`**; if missing: clone + **`uv sync`** on host. |
| 2 | Wire **`alpine-emachines`** into completão / Maestro host list (5th node: musl/apk/baremetal). |
| 3 | **Open-core matrix** (na unha or Maestro): PII scan (`~`, `/var/log`); exports (xlsx/ODF/JSON/PDF); archives (7z/zip+password); shared storage (sshfs/cifs/nfs); DB driver imports (MariaDB/MySQL/Oracle/Postgres/MSSQL per pyproject); **`main.py --web`** + **curl** health/status/report. |
| 4 | Log evidence under **`docs/private/homelab/reports/`**; **`private-git-sync.ps1 -Push`** when done. |

Session keyword: **`completao`** · **`homelab`**.

---

## Secondary (same day if bandwidth)

| Priority | Item | Notes |
| -------- | ---- | ----- |
| **Lab** | **#756** mini-bt disk | Still in [CARRYOVER.md](CARRYOVER.md) — free space before heavy completão on **mini-bt** |
| **Procurement** | ML310e **CV550** | Private **`procurement/PSU-ML310e-Gen8-CV550.pt_BR.md`** — server blocked until PSU |
| **Procurement** | T14 RAM gate | **`sudo dmidecode -t memory`** on T14 before buying DDR5 — private **`RAM-T14-DDR5-64GB-SODIMM.pt_BR.md`** |
| **Plans** | **#753** CMDB plan file | Scaffold **`PLAN_CMDB_CI_RELATIONSHIP_IMPORT.md`** when product lane opens |

---

## End of day (**2026-06-08**)

- **`eod-sync`** + **`private-stack-sync`** if private homelab reports or social hub changed.
- Tomorrow checklist path: **`OPERATOR_TODAY_MODE_2026-06-09.md`** (create at next **eod-sync** if missing).

---

## Quick references

- Session keywords: **`.cursor/rules/session-mode-keywords.mdc`** (**`completao`**, **`homelab`**, **`eod-sync`**, **`private-stack-sync`**)
- Private fleet hub: **`docs/private/homelab/LAB_OP_FLEET_UPDATE_2026-06-07.pt_BR.md`**
- Private rhythm: **`docs/private/TODAY_MODE_CARRYOVER_AND_FOUNDER_RHYTHM.md`**
