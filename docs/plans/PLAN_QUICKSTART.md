# Plan: Root QUICKSTART (5-minute first contact)

<!-- plans-hub-summary: Guia de 5 minutos para primeiro contato — DPO, jurídico e não-técnico -->

**Status:** Active
**Date:** 2026-05-20
**Priority:** H1

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md) · GitHub **#609**

**Related:** [SCOPE_IMPORT_QUICKSTART.md](../ops/SCOPE_IMPORT_QUICKSTART.md), [AUDIENCE_GUIDE.md](../AUDIENCE_GUIDE.md), [pitch/INDEX.md](../pitch/INDEX.md), [QUICKSTART_WINDOWS.md](../QUICKSTART_WINDOWS.md) · GitHub **#1128**, **#1126**

---

## Problem

USAGE and TECH_GUIDE are complete but heavy for first contact (DPO, legal, programme sponsors). Root QuickStart is still too terse for a Windows non-techie who has never used a terminal (validated field path: pipx, no Docker).

## Goal

Single **root** `QUICKSTART.md` (pt-BR) — clone to visible scan outcome without assuming YAML fluency; point to USAGE / TECH_GUIDE / scope import. Plus a **separate** hand-holding Windows guide (no Docker) so the root stays terse for Linux/Mac/dev.

## Deliverables

| Item | Status |
| ---- | ------ |
| `QUICKSTART.md` at repo root | ✅ |
| `PLAN_QUICKSTART.md` + hub row | ✅ |
| `PLANS_TODO.md` row | ✅ |
| `plans_hub_sync.py --write` | ✅ with PR |
| `docs/QUICKSTART_WINDOWS.md` (non-techie, pipx, no Docker) | ✅ |
| Prominent pointer from README + root QUICKSTART | ✅ |

## Out of scope

- Duplicating USAGE.md
- English mirror at root (AUDIENCE_GUIDE + USAGE remain EN entry for integrators)
- MSI / embedded CPython installer ([#1467](https://github.com/DataBoar/data-boar/issues/1467)) — future; guide only points forward
- `--install-shortcut` CLI ([#1127](https://github.com/DataBoar/data-boar/issues/1127)) — docs mention only
