# Operator “today mode” — 2026-03-31 (carryover + folder hygiene)

**Português (Brasil):** [OPERATOR_TODAY_MODE_2026-03-31.pt_BR.md](OPERATOR_TODAY_MODE_2026-03-31.pt_BR.md)

**Purpose:** Resume after **`today-mode`** files moved under **`docs/ops/today-mode/`** with [README.md](README.md), [CARRYOVER.md](CARRYOVER.md), and [PUBLISHED_SYNC.md](PUBLISHED_SYNC.md). **Parallel:** ThinkPad **LAB-NODE-01 + LMDE** install — use [LMDE7_LAB-NODE-01_DEVELOPER_SETUP.md](../LMDE7_LAB-NODE-01_DEVELOPER_SETUP.md) when you switch to that machine.

**Open first:** [CARRYOVER.md](CARRYOVER.md) then this file (**`today-mode 2026-03-31`**). Boundaries: **`carryover-sweep`** · **`eod-sync`** · **`scripts/operator-day-ritual.ps1`**.

---

## Block 0 — Truth + carryover (≈ 15–25 min)

1. Read **[PUBLISHED_SYNC.md](PUBLISHED_SYNC.md)** — **`v1.6.7`** is **Latest** on GitHub and on Docker Hub; next public line is **1.6.8** when `main` earns it.
1. Walk **[CARRYOVER.md](CARRYOVER.md)** — tick, defer with date, or open **PLANS** / **issue** row for each ⬜ item.
1. Optional: **`carryover-sweep`** + skim [OPERATOR_TODAY_MODE_2026-03-29.md](OPERATOR_TODAY_MODE_2026-03-29.md) Block 0 (history).

---

## Block A — Ship this docs/workflow slice (≈ 30–90 min)

- **`git status`** — if this session added **`today-mode/`**, commit with clear **`docs(ops):`** or **`workflow(ops):`** message; **`.\scripts\lint-only.ps1`** or **`check-all`** before push/PR.
- **`git fetch`** + align **`main`** if you will merge.

---

## Block B — Deps / Band A (≈ 30–45 min)

- Triage open Dependabot PRs (see [CARRYOVER.md](CARRYOVER.md)); **`deps`** session per **`SECURITY.md`**.
- Thin read: [SPRINTS_AND_MILESTONES.md](../../plans/SPRINTS_AND_MILESTONES.md) S0 if you want Scout/Hub hygiene in the same week.

---

## Block C — Optional doc slice (token-aware)

- One **`docs`** PR: first **Gemini Cold** rows from `PLANS_TODO.md` (e.g. **G-26-04**, **G-26-13**) if you want low-risk progress.

---

## Stop condition

Day slice **done** when: **CARRYOVER** updated (no fake-pending **v1.6.7** publish row); **PUBLISHED_SYNC** last-verified date current if you re-checked remotely; **today-mode** PR merged or intentionally deferred with **issue** pointer; LAB-NODE-01 steps only **when** you are on that keyboard.

---

## Chat shorthand

**`today-mode 2026-03-31`** or open this file.
