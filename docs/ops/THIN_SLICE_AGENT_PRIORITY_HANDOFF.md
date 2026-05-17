# Thin slices, priority bands, and when to ping the operator

**Português (Brasil):** [THIN_SLICE_AGENT_PRIORITY_HANDOFF.pt_BR.md](THIN_SLICE_AGENT_PRIORITY_HANDOFF.pt_BR.md)

**Purpose:** Keep assistant and maintainer aligned when burning down GitHub issues and plan rows in **thin PRs** without losing **priority discipline** or duplicating **duplicate-closure** mistakes.

**Related:** [COMMIT_AND_PR.md](COMMIT_AND_PR.md) (*Thin slices* subsection), [PLANS_TODO.md](../plans/PLANS_TODO.md), **`.cursor/rules/execution-priority-and-pr-batching.mdc`**, **`.cursor/rules/git-pr-sync-before-advice.mdc`**. **Duplicate echoes:** after the **canonical** PR merges and CI is green, close the echo with **`gh issue close <echo> --duplicate-of <canonical>`** (see `gh issue close --help`).

## Priority bands (issue titles)

1. Read **`[P0]`**, **`[P1]`**, **`[P2]`**, **`[P3]`** (or **`[decision][Pn]`**) in the **title** when present.
2. **Order:** **`P0` → `P1` → `P2` → `P3`**, then **ascending issue number** inside the band when two items disagree.
3. **Refresh:** New audit issues appear over time — periodically run **`gh issue list --state open --limit 200 --json number,title,createdAt`** and adjust the **next slice** callout in **`PLANS_TODO.md`** if the head of the queue moved.

## Agent autonomy (same band)

- **Do:** Implement **one coherent slice** per commit cluster; **`check-all`** / **`lint-only`** before integration; **`Closes #NNN`** on the **canonical** issue; merge + green CI before **`gh issue close <echo> --duplicate-of <canonical>`** on echoes.
- **Do:** If slice **A** is **blocked** (ambiguous product decision, missing evidence, environment unavailable), leave a **clear resume pointer** — for example a short **comment on the issue**, or **one line** under **Integration / active threads** in **`PLANS_TODO.md`** — then continue **B**, **C** in the **same priority band** only.
- **Do not:** Drop to a **lower** band while **higher-band** items remain **actionable** (not genuinely blocked with a written handoff). When that would happen — **stop and ping the operator** (chat or issue @): the unfinished higher-band work is **more important** than starting **`P3`** cleanup ahead of it.
- **Do not:** Use “backlog” as a silent excuse — either **ship**, **document the blocker**, or **explicitly defer** with a dated / numbered resume pointer.

## PRD / readiness framing

**“Closer to PRD readiness”** here means: accurate **operator surfaces** (man pages, **`USAGE`**, deploy docs), **green CI**, **tracked** sequencing honest in **`PLANS_TODO.md`**, and **no orphan duplicate issues** after merge. It does **not** mean finishing every **`P3`** before any **`P2`** — follow the bands above.

## Quick checklist (assistant)

1. Confirm band of the issue you are holding.
2. If blocked — write **where** to resume; pick **next same-band** issue.
3. Before starting **`P3`** work, scan for open **`P0–P2`** — if any are still actionable and not handed off, **stop** and **call the operator**.
