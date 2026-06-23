# PLAN — Maestro canonical guard (#948)

<!-- plans-hub-summary: Fail-closed guard — canonical/maestro regent never align or WorkingTree overwrite; ephemeral refs under /tmp/databoar_bench. -->

**Status:** In progress
**Issue:** [#948](https://github.com/FabioLeitao/data-boar/issues/948)
**ADR:** [ADR-0068](../adr/ADR-0068-primary-linux-dev-workstation-temporary.md) (amended)

## Goal

Encode in code (not agent runtime judgment) that the **orchestrator / canonical clone** is never a target for `git reset --hard` align or Maestro WorkingTree rsync overwrite. Ephemeral benchmark refs use an **isolated parent** (`/tmp/databoar_bench/<ref>`).

## Load-bearing layers (fail-closed)

| Layer | Signal | Effect |
| ----- | ------ | ------ |
| **(d)** | `protect_canonical: true` in inventory / `protectCanonical` in manifest | Skip destructive ops |
| **(a)** | persona `maestro` | Always protected (regent = source, not destination) |
| **(b)+(c)** | orchestrator hostname match + canonical `Projects/dev/data-boar` path | Defense in depth |
| **Transversal** | ambiguous / missing flag on canonical orchestrator path | **Protected** |

## Implementation map

| Location | Behaviour |
| -------- | --------- |
| `scripts/maestro/Maestro-CanonicalGuard.ps1` | Shared predicates |
| `scripts/maestro/Sync-WorkingTree.ps1` | Guard **before** rsync; ephemeral path |
| `scripts/lab-op-git-ensure-ref.ps1` | Skip `Reset` on protected `repoPaths` |
| `docs/private/.../inventory.json` | `protect_canonical` on regent host (private git) |

## Phase table

| Phase | Item | Status |
| ----- | ---- | ------ |
| 1 | Guard module + Sync + ensure-ref | ✅ |
| 2 | pytest guards | ✅ |
| 3 | Operator inventory/manifest flags (private) | ✅ operator tree |
| 4 | LAB_LESSONS + ADR-0068 amendment | ✅ |

## Non-goals

- Does **not** close release gate **#406**
- Does **not** bump semver
