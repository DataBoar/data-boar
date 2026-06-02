# Operator today mode — 2026-05-29 (carryover + effective focus)

**Português (Brasil):** [OPERATOR_TODAY_MODE_2026-05-29.pt_BR.md](OPERATOR_TODAY_MODE_2026-05-29.pt_BR.md)

**Note:** Drafted at **eod-sync** after **2026-05-28** — a lab node's disk is the first thing to size before product work. Host-specific detail lives in a **gitignored** private homelab note.

**`main` anchor:** `2fdfbb11` — **#751** maestro PS7 redirect + locale-bypass merged; pitch 30/60/90 deploy-vs-maturity copy on **`main`**. Open PRs: **#664 #663 #662 #661 #660** (Dependabot), **#365** (kill-switch, draft), **#348** (Dependabot hatchling).

---

## Block 0 — Morning reality (10–15 min)

Run **`carryover-sweep`** or **`.\scripts\operator-day-ritual.ps1 -Mode Morning`**. Then:

1. **`origin/main`:** `git fetch` · `git status -sb` · `git pull origin main` when behind — confirm **`ci.yml`** green on **`main`** before deep work.
2. **Open PRs:** `gh pr list --state open` — Dependabot batch (#660–#664) merge when green per **`.\scripts\pr-merge-when-green.ps1`**; skip **#365** while **DRAFT**.
3. **Private stack:** evidence pushed at **2026-05-28 eod-sync** (lab disk note + complete_eval reports). If `docs/private/` changed overnight: **`.\scripts\private-git-sync.ps1 -Push`**.

**Rolling queue:** [CARRYOVER.md](CARRYOVER.md) · **Published:** [PUBLISHED_SYNC.md](PUBLISHED_SYNC.md)

---

## START HERE — lab node disk — #756

> **Begin with `du`/snapper sizing before any cleanup.** Host name + device + findings are in the **gitignored** private note (dated **2026-05-28**) under `docs/private/homelab/`.

| Step | Action |
| ---- | ------ |
| 1 | SSH the lab node (host in the private manifest); `/` is **btrfs**, root **~90%** (~10 G free). `btrfs filesystem df /` → Data ~78.8 GiB used. |
| 2 | **Needs sudo TTY** (`ssh -tt <node>` or local): `sudo snapper list-configs` · `sudo snapper -c root list` · `sudo btrfs subvolume list -t /`. |
| 3 | If snapper snapshots are the bulk: review dates, `sudo snapper -c root delete <range>`; also clear the distro package cache (Void: `sudo xbps-remove -O`). |
| 4 | Target **≥ 20 G free**; re-check `btrfs filesystem df /`; `btrfs balance start -dusage=50 /` if Data total stays inflated. |

---

## Carryover #756 (two pending items from 2026-05-28)

| # | Item | State | Next |
| - | ---- | ----- | ---- |
| 1 | **bw CLI on a lab host** | Installed manually via `npm --prefix ~/.local` | Add to **Ansible playbook** (idempotent reprovision) — not yet done |
| 2 | **lab node disk ~90%** | Sized: btrfs, ~78.8 GiB Data, ~10 G free | Snapper/subvolume diagnosis (sudo) → clean to ≥ 20 G — see private note |

**See also #753** — `docs/plans/PLAN_CMDB_CI_RELATIONSHIP_IMPORT.md` **pending file creation** (confirmed absent on `main`). Scaffold and run **`python scripts/plans_hub_sync.py --write`** when picked up.

---

## Suggested focus (after lab disk)

| Priority | Item | Notes |
| -------- | ---- | ----- |
| **Lab** | #756 disk | Free space before any completão/benchmark on that node |
| **Ops** | #756 bw CLI | Ansible idempotence — small, closes the loop |
| **Plans** | #753 | Create `PLAN_CMDB_CI_RELATIONSHIP_IMPORT.md`; run `python scripts/plans_hub_sync.py --write` |
| **Deps** | #660–#664 | Dependabot batch — merge when green |

---

## End of day (**2026-05-29**)

- **`eod-sync`** + **`private-stack-sync`** if private or social hub changed.
- Tomorrow checklist path: **`OPERATOR_TODAY_MODE_2026-05-30.md`** (create at next **eod-sync** if missing).

---

## Quick references

- Session keywords: **`.cursor/rules/session-mode-keywords.mdc`** (**`completao`**, **`eod-sync`**, **`private-stack-sync`**, **`homelab`**)
- Private rhythm: `docs/private/TODAY_MODE_CARRYOVER_AND_FOUNDER_RHYTHM.md`
- Lab disk note: gitignored under `docs/private/homelab/` (dated 2026-05-28)
