# Operator today mode — 2026-05-19 (morning pickup)

**Português (Brasil):** [OPERATOR_TODAY_MODE_2026-05-19.pt_BR.md](OPERATOR_TODAY_MODE_2026-05-19.pt_BR.md)

**Note:** Updated end of **2026-05-19** (operator TZ **-03**) after overnight agent pass — **Block 0** runs first.

**`main` anchor:** CLI plan slices **#520–#522** merged (**#565** `--diff`, **#566** `--export-dsar`). Tier gate work **#559** may be open as PR — confirm with `gh pr list`.

---

## Block 0 — Morning reality (10–15 min)

Run **`carryover-sweep`** or **`.\scripts\operator-day-ritual.ps1 -Mode Morning`**. Then:

1. **`origin/main`:** `git fetch` · `git status -sb` · `git pull origin main` when behind — confirm **`ci.yml`** green on **`main`** before deep work.
2. **Open PRs:** `gh pr list --state open` — merge when green per **`.\scripts\pr-merge-when-green.ps1`** where safe (e.g. licensing tier gates **#559**).
3. **Plans PMO:** Read **`docs/plans/PLANS_TODO.md`** intro + **[PLANS_DOCUMENTATION_HIERARCHY.md](../PLANS_DOCUMENTATION_HIERARCHY.md)** when promoting issue work into **`PLAN_*.md`** (then **`plans_hub_sync.py --write`**).
4. **Carry thread / handoff:** Decisions on the GitHub issue; persist outcomes in **`docs/plans/`** per hierarchy doc.

**Rolling queue:** [CARRYOVER.md](CARRYOVER.md) · **Published:** [PUBLISHED_SYNC.md](PUBLISHED_SYNC.md)

### Social / editorial (private hub) — ~2 min

- [ ] Skim **`docs/private/social_drafts/editorial/SOCIAL_HUB.md`** for **2026-05-19** / **2026-05-20** — [SOCIAL_PUBLISH_AND_TODAY_MODE.md](SOCIAL_PUBLISH_AND_TODAY_MODE.md).

---

## Suggested focus (P1 thin slices)

| Priority | Item | Notes |
| -------- | ---- | ----- |
| **P1** | [#559](https://github.com/FabioLeitao/data-boar/issues/559) tier fixtures + graceful denial | Merge PR if green; then enable enforcement follow-ups. |
| **P1** | [#544](https://github.com/FabioLeitao/data-boar/issues/544) `governance_lens` in runtime map | Keys may already exist after **#559** — wire API/CLI gate next. |
| **P1** | [#512](https://github.com/FabioLeitao/data-boar/issues/512) process batch | Promote durable rows into **`docs/plans/`**; close echo issues with evidence. |
| **H1** | CLI plan **complete** | [PLAN_CLI_VALIDATE_DIFF_AND_DSAR_EXPORT.md](../../plans/PLAN_CLI_VALIDATE_DIFF_AND_DSAR_EXPORT.md) — next theme from **PLANS_TODO** (licensing / governance docs **#556+**). |

---

## Carryover — spine

| Track | Item | Notes |
| ----- | ---- | ----- |
| Pilot gate | **M-PILOT-READY** | Release / Maestro / pilot criteria in **PLANS_TODO**; **v1.7.4** when checklist green. |
| Plans ops | **Hierarchy doc + new `PLAN_*.md` slices** | Commit/push **`docs/ops/PLANS_DOCUMENTATION_HIERARCHY*.md`** when ready. |
| Governance | Open **P0/P1** triage | **#512**; **#550** closed (pwsh timeout duplicate of **#563**). |

---

## End of day (**2026-05-19**)

- **`eod-sync`** or **`block-close`** per workload — [README.md](README.md).
- If **`docs/private/`** changed: **`.\scripts\private-git-sync.ps1 -Push`**.
