---
name: autonomous-merge-and-lab
description: >-
  After CI is green and PR is mergeable, run scripts/pr-merge-when-green.ps1; for LAB-OP inventory,
  run scripts/lab-op-sync-and-collect.ps1 with docs/private/homelab/lab-op-hosts.manifest.json.
  Escalate to the operator on gh/ssh failures or suspected regressions.
---

# Autonomous merge + LAB-OP collection

## Merge (GitHub)

1. `git fetch origin`
1. `gh pr view <N> --json state,mergeable` → must be OPEN, not CONFLICTING
1. `gh pr checks <N>` → exit 0
1. `.\scripts\pr-merge-when-green.ps1 -PrNumber <N>` (add `-Method squash` if agreed)

Optional local gate: `-RunLocalCheckAll` (slow).

## LAB-OP (SSH from operator PC)

1. **Copy** `docs/private.example/homelab/lab-op-hosts.manifest.example.json` → `docs/private/homelab/lab-op-hosts.manifest.json` and edit SSH host aliases + Linux `repoPaths`.
1. `.\scripts\lab-op-sync-and-collect.ps1` from repo root.
1. Read new `docs/private/homelab/reports/*_labop_sync_collect.log`; redact if sharing.

**Rule file:** `.cursor/rules/agent-autonomous-merge-and-lab-ops.mdc` (always on).
