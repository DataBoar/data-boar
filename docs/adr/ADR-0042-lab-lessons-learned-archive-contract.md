# ADR 0042 — Public LAB lessons archive + hub (dated snapshots)

## Status

Accepted

## Context

Lab QA and completão work produce **two classes** of evidence:

1. **Private** — hostnames, LAN, credentials, long orchestration transcripts (`docs/private/homelab/COMPLETAO_SESSION_*.md`, reports under `docs/private/homelab/reports/`).
2. **Public** — benchmark JSON checked into `tests/`, metric tables, checkpoint **counts** and timing suitable for GitHub.

We had a single [`docs/ops/LAB_LESSONS_LEARNED.md`](../ops/LAB_LESSONS_LEARNED.md) file. As sessions accumulate, we need the same **segregation pattern** as `docs/plans/completed/`: **immutable dated snapshots** plus a **small hub** that links forward into **`PLANS_TODO.md`** when follow-up work is real.

## Decision

1. Keep **`docs/ops/LAB_LESSONS_LEARNED.md`** as the **canonical hub** (summary + archive table + plan bridges).
2. Add **`docs/ops/lab_lessons_learned/`** with:
   - **`README.md`** / **`README.pt_BR.md`** — naming contract, ritual steps, boundary vs private completão logs.
   - **`LAB_LESSONS_LEARNED_YYYY_MM_DD.md`** — one snapshot per session (append-only history; do not rewrite old files).
3. **Completão** remains governed by [`docs/ops/LAB_COMPLETAO_RUNBOOK.md`](../ops/LAB_COMPLETAO_RUNBOOK.md); this ADR only defines how **public** lesson snapshots relate to that runbook.
4. **Cursor:** add a **situational** rule (not `alwaysApply`) and an English session token **`lab-lessons`** so assistants load the contract when closing a lab evidence loop without bloating every chat.

## Consequences

- **Pros:** Clear audit trail for “what did we prove on date X”; hub stays short; plan hygiene has an explicit promotion path.
- **Cons:** One more folder to remember; operators must run the snapshot ritual (or ask the assistant with **`lab-lessons`**) so the hub and archive do not drift.

## References

- [`docs/ops/lab_lessons_learned/README.md`](../ops/lab_lessons_learned/README.md)
- [`docs/ops/LAB_COMPLETAO_RUNBOOK.md`](../ops/LAB_COMPLETAO_RUNBOOK.md)
- [`.cursor/rules/lab-lessons-learned-archive.mdc`](../../.cursor/rules/lab-lessons-learned-archive.mdc)
- [`.cursor/rules/session-mode-keywords.mdc`](../../.cursor/rules/session-mode-keywords.mdc)
