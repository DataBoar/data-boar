# LAB-OP sync runbook (copy to `docs/private/homelab/`)

**Purpose:** Dated notes for **`scripts/lab-op-sync-and-collect.ps1`** outcomes — **gitignored**; do not commit `docs/private/`.

## Template — run log

| Date (UTC/local)   | Host alias | git pull  | homelab-host-report   | Notes |
| ------------------ | ---------- | --------  | --------------------- | ----- |
| YYYY-MM-DD         | …          | OK / fail | OK / skipped          | …     |

---

## Example entry (structure only — replace with your facts)

| Date       | Host     | git pull                | Report  | Notes                                                                                              |
| ---------- | -------- | --------                | ------  | -----                                                                                              |
| 2026-03-23 | lab-op   | OK (already up to date) | OK      | Ubuntu-family; kernel/sys sample in log                                                            |
| 2026-03-23 | <lab-host-2>  | **fail**                | skipped | Local change blocks merge: `scripts/homelab-host-report.sh` — stash or commit on host, then re-run |
| 2026-03-23 | lab-sbc  | **fail**                | skipped | Same as <lab-host-2>                                                                               |

**Recovery:** SSH to the host → `cd` repo → `git status` → `git stash push -m "wip homelab script"` (or commit) → pull → re-run collect. Or run **`-SkipGitPull`** to capture inventory without updating `main`.

---

**Related:** [HOMELAB_HOST_PACKAGE_INVENTORY.md](../../ops/HOMELAB_HOST_PACKAGE_INVENTORY.md) §4 · [reports/README.md](reports/README.md)
