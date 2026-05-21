# ADR 0058 - Primer hub registration ritual

**Status:** Accepted
**Date:** 2026-05-20

## Context

Primers under `docs/plans/` are indexed in **`docs/plans/PRIMERS_HUB.md`**. Issues **#598**, **#554**, **#629**, and **#630** were opened without matching hub rows — drift between GitHub backlog and the in-tree index. **`scripts/check_hubs.py`** validates existing primer **links** but does not require every planned issue to appear in the hub table.

Issue **#626** requested a durable ritual so new primer issues do not become "vaporware" invisible to maintainers.

## Decision

1. When opening **any** GitHub issue whose deliverable is a new `*_PRIMER.md`, `*_ALIGNMENT.md`, or equivalent plan-tier explainer under **`docs/plans/`**, add a **`*(planned — #NNN)*`** row to **`PRIMERS_HUB.md`** in the **same PR** that lands the issue reference (or in the PR that creates the primer file).
2. Acceptance criteria on primer issues must include: *"Row added to PRIMERS_HUB.md (planned link until file exists)."*
3. When a primer ships, replace the plain-text planned row with a markdown link to the file and run **`python scripts/plans_hub_sync.py --write`** if plan metadata changed.
4. **`GOVERNANCE_ITSM_DIAGRAMS_SOURCE.md`** and similar **diagram companions** may stay outside the hub table; cross-link from the primer issue or primer doc instead of duplicating rows.

## Consequences

- **Positive:** Agents and contributors see one index; `#625`-class hygiene gaps shrink.
- **Negative:** Small overhead on every primer issue/PR.
- **Enforcement:** Review convention + **`check_hubs.py`** for broken links; optional future pytest for orphan `*(planned — #`* without open issue (not in scope here).

## References

- [PRIMERS_HUB.md](../plans/PRIMERS_HUB.md)
- [ADR-0057](ADR-0057-lightweight-hub-index-co-located-links.md)
- GitHub **#625**, **#626**
