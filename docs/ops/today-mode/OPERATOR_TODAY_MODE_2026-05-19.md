# Operator today mode — 2026-05-19 (morning pickup)

**Português (Brasil):** [OPERATOR_TODAY_MODE_2026-05-19.pt_BR.md](OPERATOR_TODAY_MODE_2026-05-19.pt_BR.md)

**Note:** Prepared end of **2026-05-18** — **Block 0** runs first.

---

## Block 0 — Morning reality (10–15 min)

Run **`carryover-sweep`** or **`.\scripts\operator-day-ritual.ps1 -Mode Morning`**. Then:

1. **`origin/main`:** `git fetch` · `git status -sb` · `git pull origin main` when behind — confirm **`ci.yml`** green on **`main`** before deep work.
2. **Open PRs:** `gh pr list --state open` — merge when green per **`.\scripts\pr-merge-when-green.ps1`** where safe.
3. **Plans PMO:** Read **`docs/plans/PLANS_TODO.md`** intro + **[PLANS_DOCUMENTATION_HIERARCHY.md](../PLANS_DOCUMENTATION_HIERARCHY.md)** if you are promoting issue work into **`PLAN_*.md`** (then **`plans_hub_sync.py --write`**).
4. **Carry thread / handoff:** If continuing a **GitHub issue** with another assistant or reviewer, **decisions** in the issue; **persist** outcomes in **`docs/plans/`** per the hierarchy doc.

**Rolling queue:** [CARRYOVER.md](CARRYOVER.md) · **Published:** [PUBLISHED_SYNC.md](PUBLISHED_SYNC.md)

### Social / editorial (private hub) — ~2 min

- [ ] Skim **`docs/private/social_drafts/editorial/SOCIAL_HUB.md`** for **2026-05-19** / **2026-05-20** — [SOCIAL_PUBLISH_AND_TODAY_MODE.md](SOCIAL_PUBLISH_AND_TODAY_MODE.md).

---

## Carryover — spine

| Track | Item | Notes |
| ----- | ---- | ----- |
| Pilot gate | **M-PILOT-READY** | Release / Maestro / pilot criteria in **PLANS_TODO**; **v1.7.4** when checklist green. |
| Plans ops | **Hierarchy doc + new `PLAN_*.md` slices** | Commit/push **`docs/ops/PLANS_DOCUMENTATION_HIERARCHY*.md`** + README/cold-start links when ready; align issue threads to committed plans. |
| Governance | Open **P0/P1** triage | [#512](https://github.com/FabioLeitao/data-boar/issues/512) process plan; promote durable work into **`docs/plans/`**. |

---

## End of day (**2026-05-19**)

- **`eod-sync`** or **`block-close`** per workload — [README.md](README.md).
- If **`docs/private/`** changed: **`.\scripts\private-git-sync.ps1 -Push`**.
