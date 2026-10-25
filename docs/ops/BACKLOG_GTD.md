# Backlog as GTD (GitHub issues are the bus)

**Português:** [BACKLOG_GTD.pt_BR.md](BACKLOG_GTD.pt_BR.md)

Short operator page. Not a new app. Issues stay the AIIDCOBPP bus.

**Also:** [GITHUB_ISSUE_CANONICAL_AND_DUPLICATE_CLOSE.md](GITHUB_ISSUE_CANONICAL_AND_DUPLICATE_CLOSE.md) (how to close), [ISSUE_QUEUE_SEQUENCING_MAP.md](ISSUE_QUEUE_SEQUENCING_MAP.md) (mirror only — GitHub milestones are source of truth).

## Five buckets

| GTD | Here | Hard rule |
| --- | --- | --- |
| **Inbox** | Open issue with **no milestone and no `P*` label** | Not sprint work. Process in ≤7 days or it is a skeleton. |
| **Next** | Milestone `v1.8.0` + P0/P1 (P2 only with PLAN/AC) | If it will not fit in one operator head (~30), the milestone is lying. |
| **Waiting** | Blocker text with `#N` still **open** | If `#N` is already closed, stale `NÃO INICIAR` is hygiene — not a live edge. |
| **Someday** | Milestone `backlog`, **or any numbered milestone beyond the active release (`v1.8.1`, `v1.8.2`, ...)**, or labels `proposta-de-plan` / `no-code-yet` | Lab (Growatt, Slack, course lists) lives here. **Numbered future milestones are horizon-ordered Someday waves — lower number = sooner revisit — not a promise, not Next.** Never count as v1.8.0. |
| **Done** | `closed` + explicit reason | `completed` = artifact (PR/path). `not_planned` = honest refusal. `duplicate` uses `duplicate_of`. |

A `[P2]` **title** is not a label. Filters and agents read labels.

Opening an issue is **capture**. Leaving Inbox requires a processing comment:

```text
Inbox → ?
- Outcome: …
- Next physical: PR | PLAN | comment-only | close
- Bucket: v1.8.0 | v1.8.1 | backlog | not_planned
- P label matches title Pn
- Done looks like: …
```

## Anti-skeleton / anti-accidental-done

1. Close only with evidence in the close comment (`via #PR`, path in tree, or `not_planned: lab not product`).
2. Do not close P0/P1/bugs in the same sweep as P3 docs.
3. Stale ≠ done. 90 days + no milestone + P3 → `stale-review` comment, then `not_planned` or `backlog`. No silent stale-bot on this bus.
4. Agents do not close because the body “looks shipped.” HITL or a checklist with an artifact path.
5. Refresh `ISSUE_QUEUE_SEQUENCING_MAP.md` in the **same PR** that closes a hygiene group (`uv run python scripts/issue_queue_sequencing_map.py --write`). A stale map is itself a skeleton.
6. Practical axes: **`Pn` label + milestone**. U-axis (ADR-0061) only on Next, or stop pretending it exists.
7. A `Pn` label that undercounts real severity (e.g. `P3` on an issue with a confirmed vulnerability from an active scanner) may still enter Next — cite the evidence (scanner run id, confirmed-in-main date) in the processing comment instead of waiting for the label to catch up.

## Weekly review (30–45 min)

Not a Saturday houseclean.

1. Inbox: `is:issue is:open no:milestone` — process or refuse.
2. Waiting: blocker already closed? Clean text or unblock.
3. Next `v1.8.0`: still fits? Push leftover P3 to `backlog`.
4. Closed last 7d with no `via #PR` — reopen if the close was accidental.
5. Regenerate the sequencing map — one command, one commit.

Houseclean groups (E–H style) are a **quarterly** review. Daily mode is Next + Inbox.

## Do not

- Stamp milestone `backlog` on everything so “nothing is unassigned” — that hides Inbox.
- Keep four sources of truth (title, label, Projects field, map). Label P + GitHub milestone; the map derives.
- File a meta-issue named “implement GTD.”
