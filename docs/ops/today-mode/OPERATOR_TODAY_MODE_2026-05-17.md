# Operator today mode — 2026-05-17 (morning pickup)

**Português (Brasil):** [OPERATOR_TODAY_MODE_2026-05-17.pt_BR.md](OPERATOR_TODAY_MODE_2026-05-17.pt_BR.md)

**Note:** Drafted from **2026-05-16** evening close — **Block 0** wins first tomorrow.

---

## Block 0 — Morning reality (10–15 min)

Run **`carryover-sweep`** or **`.\scripts\operator-day-ritual.ps1 -Mode Morning`**. Then:

1. **`origin/main`:** `git fetch` · `git status -sb` · `git pull origin main` when behind — confirm **`ci.yml`** green on **`main`** before deep work.
2. **Open PRs:** triage **#365** (draft), **#348**, and any new items from `gh pr list` — merge when green per **`.\scripts\pr-merge-when-green.ps1`** where safe.
3. **Milestone **M-PILOT-READY**:** exit checklist in **[PLANS_TODO.md](../../plans/PLANS_TODO.md)** — Maestro **#403** / **#404**+**#408** / release **#406** / PR **#391** / completão smoke on four hosts / **`docs/releases/1.7.4.md`**.
4. **`plans-stats` / `PLANS_TODO`:** if you add `H0`–`H5` subsection headings mid-file, recall **`AGENTS.md`** *Learned Workspace Facts* — **`plans-stats.py`** buckets rows by the **latest** such heading; prefer inline **`[H1]`** tags instead of stray **`#### H1`** labels.

**Rolling queue:** [CARRYOVER.md](CARRYOVER.md) · **Published:** [PUBLISHED_SYNC.md](PUBLISHED_SYNC.md)

### Social / editorial (private hub) — ~2 min

- [ ] Skim **`docs/private/social_drafts/editorial/SOCIAL_HUB.md`** for **2026-05-17** / **2026-05-18** — [SOCIAL_PUBLISH_AND_TODAY_MODE.md](SOCIAL_PUBLISH_AND_TODAY_MODE.md).

---

## Carryover — spine

| Track | Item | Notes |
| ----- | ---- | ----- |
| Pilot gate | **M-PILOT-READY** | Law / pharma / EdTech use-case rows in **PLANS_TODO**; ship **v1.7.4** bundle when criteria met. |
| Maestro | **#403** SSH `ConnectTimeout`, **#404**+**#408** `--bench-config` | Keep scripts + tests aligned; avoid regressing completão smoke. |
| Release | **#406** **1.7.4** tag + Hub + **`docs/releases/1.7.4.md`** | After green **`check-all`** / release ritual. |
| Toolchain | **PR #391** PII filter fix | Merge when review + CI pass. |
| Governance | **ADR-0055** | Still **`Proposed`** until explicit ratification — see **2026-05-15** today-mode if still open. |

---

## End of day (**2026-05-17**)

- **`eod-sync`** or **`block-close`** per workload — [README.md](README.md).
- If **`docs/private/`** changed: **`.\scripts\private-git-sync.ps1 -Push`**.
