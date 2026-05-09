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
| Dated execution checklist | [README.md](README.md) + `OPERATOR_TODAY_MODE_YYYY-MM-DD.md` | Daily focus and closure flow |
| Publish alignment | [PUBLISHED_SYNC.md](PUBLISHED_SYNC.md) | Repo version vs GitHub Release vs Docker Hub |
| Private rhythm/reminders | `docs/private/TODAY_MODE_CARRYOVER_AND_FOUNDER_RHYTHM.md` | Operator-only reminders and cadence |
| Social editorial carryover | `docs/private/social_drafts/editorial/SOCIAL_HUB.md` | Planned/deferred/published social rows |

---

## 2) Current workboard snapshot (short, manual)

Update this section with concise bullets only. Keep details in canonical docs above.

- **Now (top 1):** `S2a` transport + trust checkpoint from `PLANS_TODO`.
- **Next (top 3):**
  - `-1L` homelab proof pass when calendar allows.
  - Continue prioritized trust/commercial slices after `S2a`.
  - Keep carryover queue clean (`CARRYOVER.md`).
- **Blockers:** write one line per blocker and link to the owning doc.
- **Deferred with date:** keep date + owner in `CARRYOVER.md`.

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
