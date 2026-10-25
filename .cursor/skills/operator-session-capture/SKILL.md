# Operator session capture (chat → repo memory)

## When to use

The operator wants **high-value** chat (decisions, policy, tooling, career/academic framing) **preserved** for later—without bloating tracked docs or committing secrets.

## Steps

1. Read **`docs/ops/OPERATOR_SESSION_CAPTURE_GUIDE.md`** (and **`.pt_BR.md`** if the operator uses pt-BR).
1. For each takeaway, assign **tracked** vs **`docs/private/`** vs **plan file** per the guide’s table.
1. Write the **smallest** change that future search recovers the intent (bullet list > long prose).
1. If multiple **private** topics, add or update **`docs/private/author_info/RECENT_OPERATOR_SYNC_INDEX.pt_BR.md`** with **date + pointers** (relative paths).
1. If the outcome is **product work**, propose **`PLANS_TODO.md`** / **`PLAN_*.md`** updates in a **separate** commit theme—do not mix with personal private notes.

## Never

- Commit **`docs/private/`** or paste LAN/session dumps into **issues/PRs/tracked** Markdown.
- Store webhooks, tokens, or client pricing in tracked files.

## Related

- **`docs/PRIVATE_OPERATOR_NOTES.md`**
- **`docs/ops/PRIVATE_LOCAL_VERSIONING.md`** — nested Git (or local backups) for **`docs/private/`** without GitHub
- **`docs/ops/OPERATOR_NOTIFICATION_CHANNELS.md`** (Slack + Signal phased pattern)
- **`.cursor/rules/operator-session-capture.mdc`**
