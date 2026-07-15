# Skill: periodic external collect (public template)

## When to use

Operator asks for a **scheduled or on-demand** pull of data from an **authenticated external service** into **gitignored** local notes — without hard-coding vendor-specific accounts in the public tree.

## Policy (generic)

1. Prefer a **repo wrapper** under `scripts/` (token-aware) over long ad-hoc browser walks.
2. Persist credentials/session cookies only under **gitignored** paths (never commit session files).
3. Prefer **read-only** collection; never submit forms that create tickets/orders unless the operator explicitly asks.
4. Record status (last success, next due) in a **local state** file under the private tree — not in tracked Markdown.
5. On failure (expired session, captcha), report the blocker and hand off one clear operator step.

## Operator-specific runbook

Vendor cadence, script names, and service tables for this workstation live under **gitignored** **`.cursor/private/skills/session-aware-collect/`** (issue #1191).
