# ADR 0040 — Assistant default: private stack evidence mirrors without rhetorical asks

## Context

The stacked private repository under **`docs/private/`** holds **operator-owned progress history** and evidence that must **not** live on the public **`origin`**. Redundancy typically spans **multiple non-GitHub mirrors** (e.g. SSH **`lab-*`** bare repos on lab hosts and a **bare Git repository on a VeraCrypt-mounted volume** synced with cloud storage).

In chat, the operator may ask to **verify alignment**, **check drift**, or **close hygiene** after work that touched the private tree. Treating “synced” as **only** one destination (e.g. lab remotes) while omitting another reachable mirror creates **silent drift** — the opposite of evidence discipline.

## Decision

1. **Default assistant behaviour:** When the session goal clearly includes **keeping private history consistent** (verify / align / drift / hygiene / push private / **`private-stack-sync`**), the assistant **updates every configured and reachable mirror** in the same flow. **Do not** ask redundant permission for steps whose intent is already established by the request.

2. **Documentation and tooling alignment:** This contract is recorded in **always-applied** Cursor rules (**`operator-evidence-backup-no-rhetorical-asks.mdc`**), **`operator-direct-execution.mdc`**, **`agent-session-ritual-sync-main-and-private-stack.mdc`**, root **`AGENTS.md`**, **`docs/ops/PRIVATE_STACK_SYNC_RITUAL*.md`**, **`docs/ops/CURSOR_AGENT_POLICY_HUB*.md`**, **`.cursor/skills/stacked-private-sync/SKILL.md`**, and **`scripts/private-git-sync.ps1`** (optional **`-Push`** path that probes VeraCrypt **`Z:`** then **`Y:`** for a **`notes-sync.git`** bare when those drive roots exist).

3. **Boundaries unchanged:** No secrets in tracked files; no volume passphrases in chat; **primary Windows canonical clone** protection and destructive Git policy remain as in **`PRIMARY_WINDOWS_WORKSTATION_PROTECTION.md`**.

## Consequences

- Fewer “obvious answer” interruptions; clearer operator expectation that **mirrors are one ritual**, not a menu.
- Assistants must **probe mounts** and **report concrete failures** instead of deferring on implied backup steps.
- Operators who use a **local bare on an encrypted volume** may need a one-time **`git config --global --add safe.directory <bare-path>`** when Git raises **dubious ownership**; the sync script may add that entry **once** when it detects that specific error and retries.

## References

- **`docs/ops/PRIVATE_STACK_SYNC_RITUAL.md`**
- **`scripts/private-git-sync.ps1`**
- **`.cursor/rules/operator-evidence-backup-no-rhetorical-asks.mdc`**
- **`docs/adr/0039-retention-evidence-posture-bonded-customs-adjacent-contexts.md`** (product retention posture — distinct from this **workflow** ADR)
