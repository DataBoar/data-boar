# Skill: private-stack sync policy (public template)

## When to use

The operator types **`private-stack-sync`**, or wants a **repeatable close** for the **nested Git repo** under **`docs/private/`** (not the public GitHub `origin`) — analogous to **`eod-sync`** for the product tree.

## Policy (generic)

1. Read **`docs/ops/PRIVATE_STACK_SYNC_RITUAL.md`** (and **`.pt_BR.md`** when the operator prefers pt-BR). Optional orientation: **`docs/ops/OPERATOR_AGENT_COLD_START_LADDER.md`** task-router row for the private stack; situational rule **`.cursor/rules/docs-private-workspace-context.mdc`**.
2. From the **product repo root**, run **`scripts/private-git-sync.ps1`** (Windows) or **`scripts/private-git-sync.sh`** (Linux/macOS). Add **`-Push`** / **`--push`** when policy includes **all non-public mirrors** configured for this workstation (SSH remotes, encrypted-volume bare mirrors, optional sync-client file mirrors — see the script and ritual stub; **do not** invent host inventory in chat).
3. When the operator asks to **align**, **verify drift**, or **sync** private history, **do not** ask redundant permission to include obvious backup targets — **`operator-evidence-backup-no-rhetorical-asks.mdc`** and **[ADR 0040](../../../docs/adr/ADR-0040-assistant-private-stack-evidence-mirrors-default.md)**.
4. If the workflow uses **encrypted volumes**, remind **mount → git → unmount** from **`docs/ops/PRIVATE_LOCAL_VERSIONING.md`** and **private** runbooks — **never** paste passphrases, keyfiles, or absolute volume paths into tracked Markdown or chat.
5. Confirm **no** secrets land in **tracked** files or public issues/PRs.

## Never

- Commit **`docs/private/`** into the **public** remote.
- Claim SSH or LAN operations “completed” without the operator’s **actual** terminal success on their network.
- Paste host alias lists, vendor account names, or drive-letter mount maps into **public** skills or docs.

## Operator-specific runbook

Host inventory, encrypted-volume letters, secret-leaf copy rules, and mirror names for this workstation live under **gitignored** **`.cursor/private/skills/stacked-private-sync/`** (issue #1191).
