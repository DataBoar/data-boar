# Operator workboard (backlog + carryover + reminders)

**Português (Brasil):** [WORKBOARD.pt_BR.md](WORKBOARD.pt_BR.md)

**Purpose:** Give one practical cockpit for active work without creating a second source of truth. This file is a **routing layer**: it points to canonical docs and records only short "now/next" summaries.

---

## 1) Canonical sources (do not duplicate)

| Topic | Source of truth | Use this for |
| ----- | --------------- | ------------ |
| Product backlog and sequencing | [../../plans/PLANS_TODO.md](../../plans/PLANS_TODO.md) | Priority order, dependency logic, active execution rows |
| Plan index/map | [../../plans/PLANS_HUB.md](../../plans/PLANS_HUB.md) | Fast lookup of `PLAN_*.md` files |
| Sprint and milestones view | [../../plans/SPRINTS_AND_MILESTONES.md](../../plans/SPRINTS_AND_MILESTONES.md) | Theme-level sequencing and milestone semantics |
| Carryover queue (rolling) | [CARRYOVER.md](CARRYOVER.md) | Open items crossing days/blocks |
| WRB follow-up (token window) | [GitHub issue #189](https://github.com/DataBoar/data-boar/issues/189) | Resume external review cycle now that tokens are available |
| Dated execution checklist | [README.md](README.md) + `OPERATOR_TODAY_MODE_YYYY-MM-DD.md` | Daily focus and closure flow |
| Publish alignment | [PUBLISHED_SYNC.md](PUBLISHED_SYNC.md) | Repo version vs GitHub Release vs Docker Hub |
| Private rhythm/reminders | `docs/private/TODAY_MODE_CARRYOVER_AND_FOUNDER_RHYTHM.md` | Operator-only reminders and cadence |
| Social editorial carryover | `docs/private/social_drafts/editorial/SOCIAL_HUB.md` | Planned/deferred/published social rows |

---

## 2) Current workboard snapshot (short, manual)

Update this section with concise bullets only. Keep details in canonical docs above.

**Last refresh:** **2026-09-28** · Today file: [OPERATOR_TODAY_MODE_2026-09-28.md](OPERATOR_TODAY_MODE_2026-09-28.md)

- **Now (top 1):** **BFF / GA validation** — **[#1980](https://github.com/DataBoar/data-boar/issues/1980)** with Maestro **#82/#91** closure and **carrion-crow #99** on the operator queue.
- **Next (top 3):**
  - Close **maestro#91** (fix merged as **data-boar#2011**); optional lab-host RC smoke after podman images ([#756](https://github.com/DataBoar/data-boar/issues/756)).
  - Merge **carrion-crow #99**, then security issues **#94–#101**.
  - One **Dependabot** PR (**#1999** / **#1998** first) — not blind majors.
- **Blockers:**
  - Lab **podman** smoke images removed **2026-09-27** — restore before claiming lab RC proof ([#756](https://github.com/DataBoar/data-boar/issues/756)).
  - **maestro#82** still open while product RC/security landed on `main`.
- **Deferred with date:** Maestro `engine/` RC `uv sync` mirror — post-#2011, no date (operator **2026-09-28**).

---

## 3) Ritual usage

### Morning (quick)

1. Run `.\scripts\operator-day-ritual.ps1 -Mode Morning`.
2. Open today's `OPERATOR_TODAY_MODE_YYYY-MM-DD.md`.
3. Check `CARRYOVER.md` and pull only what is realistic for today.

### During the block

1. Keep this file short ("Now", "Next", "Blockers").
2. Update canonical docs when something changes state.
3. Avoid large narrative text here; this is an operations board.

### End of block / end of day

1. Use `block-close` (or `eod-sync` when calendar close applies).
2. Move unfinished items into `CARRYOVER.md` with a next date.
3. If publish happened, update `PUBLISHED_SYNC.md`.

---

## 4) Editing policy

- This file can summarize, but it must not replace:
  - `PLANS_TODO.md` for backlog truth,
  - `CARRYOVER.md` for cross-day queue,
  - dated `OPERATOR_TODAY_MODE_*.md` for day execution.
- Prefer links over copied tables.
