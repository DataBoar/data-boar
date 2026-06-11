# ADR 0057 — Lightweight hub index (co-located links, no file moves)

- **Date (UTC):** 2026-05-20
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Status

Accepted

### Status history

- 2026-05-20 — Accepted
- 2026-06-11 — Amended: retrofit to ADR-0045 UMADR format (metadata list, Authors, Status history) — GitHub #675

## Context

The repository has grown to dozens of ops runbooks, plans, ADRs, Cursor rules, and skills. Moving files into new folder hierarchies would break hard-coded paths in scripts, CI, and existing cross-links. Navigation degraded for humans and agents.

Issue **#577** introduced `docs/hubs/INDEX.md` and `scripts/check_hubs.py` inside `check-all` to validate hub backtick paths and primer links.

## Rejected alternatives

| Option | Why not |
| ------ | ------- |
| **Reorganize directories (move files)** | Cascading breakage in workflows, ADR references, and operator muscle memory. |
| **External wiki** | Not versioned with code; not gated by CI. |
| **No hubs** | Confirmed cognitive load; agents rediscover paths every session. |

## Decision

1. Adopt the **lightweight hub** pattern: a `*HUB*.md` or `INDEX.md` file **co-located** with content (or under `docs/hubs/` for cross-cutting maps) that **links only** — never moves canonical files.
2. **`docs/hubs/INDEX.md`** is the hub-of-hubs for cross-cutting navigation.
3. **`scripts/check_hubs.py`** (invoked from `check-all`) fails CI when any indexed backtick path or `PRIMERS_HUB` link is missing.
4. **Exception:** the ADR narrative index remains **`docs/adr/README.md`** (and `README.pt_BR.md`), not duplicated under `docs/hubs/`.
5. New major doc categories add a hub row in the **same PR** as the hub file.

### Guardrails

- **NEVER** move an existing tracked file solely to populate a hub.
- **Every** new `*HUB*.md` or category `INDEX.md` under `docs/` gets an entry in `docs/hubs/INDEX.md` in the same PR.
- **Broken hub links** fail `check-all` via `check_hubs.py`.
- **PR that moves** a path referenced from a hub must update **all** hub backtick paths in the same PR.

## Consequences

- **Positive:** Stable paths; agents have a single map; CI prevents link rot on indexed hubs.
- **Negative:** More index files to maintain; regenerators (e.g. rules/skills hub) must be run after bulk rule adds.
- **Watch:** Hubs that use markdown links outside backtick-path convention need explicit tests if added later.

## References

- `docs/hubs/INDEX.md`, `scripts/check_hubs.py`
- `docs/hubs/RULES_AND_SKILLS_HUB.md` (generated index, issue **#578**)
- `.cursor/rules/hub-pattern.mdc`
- Issue **#577**, **#583**, **#571**
