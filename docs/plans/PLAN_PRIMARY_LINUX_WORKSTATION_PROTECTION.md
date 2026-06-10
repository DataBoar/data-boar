# Plan: Primary Linux workstation protection (Linux primary canonical clone)

**Status:** Active
**Date:** 2026-06-09
**Authors:** Fabio Leitao
**Priority:** P1
**GitHub:** [#801](https://github.com/FabioLeitao/data-boar/issues/801)

<!-- plans-hub-summary: proteção do clone canônico no Linux primary, pre-commit, check-all.sh, busca find/fd/plocate/git grep — temporário até Windows primary voltar -->
<!-- plans-hub-related: docs/ops/PRIMARY_LINUX_WORKSTATION_PROTECTION.md, ADR-0068-primary-linux-dev-workstation-temporary.md, docs/ops/PRIMARY_WINDOWS_WORKSTATION_PROTECTION.md -->

## Context

The Windows primary dev workstation failed **2026-06-07** (Lenovo **E0482B2DMD**). **primary Linux dev workstation** (LMDE 7) hosts the canonical **`data-boar`** clone. Hooks and docs still assumed Windows-only protection; **`pre-commit install`** was never run on the Linux primary dev workstation, bypassing all commit guards.

## Scope

| Track | Deliverable |
| ----- | ----------- |
| Docs | **`PRIMARY_LINUX_WORKSTATION_PROTECTION.md`** (+ pt-BR) |
| Rule | **`primary-linux-workstation-protected-no-destructive-repo-ops.mdc`** (`alwaysApply: true`) |
| ADR | **ADR 0068** — temporary primary + reversion checklist |
| Agent contract | **`AGENTS.md`** — primary dev workstation (Linux primary, temporary); **`es-find`** Windows-only; Linux search tools |
| Operator ritual | **`pre-commit install`** + **`./scripts/check-all.sh`** before PR |

**Out of scope:** Removing Windows protection docs (needed when Windows primary returns).

## Linux file search (replaces `es.exe` on the Linux primary dev workstation)

| Tool | Role |
| ---- | ---- |
| **`find`** | Scoped walks |
| **`fd`** | Fast filename search |
| **`locate` / `plocate`** | Indexed lookup — **plocate 1.1.23** on primary Linux dev workstation |
| **`git grep`** | Tracked content / history |
| **`grep -r`** | Working-tree content |

## Implementation checklist

| Phase | Task | Status |
| ----- | ---- | ------ |
| 1 | Linux protection docs (EN + pt-BR) | ✅ |
| 2 | **`primary-linux-workstation-protected-no-destructive-repo-ops.mdc`** | ✅ |
| 3 | **ADR 0068** + README index + INVENTORY | ⬜ |
| 4 | **`AGENTS.md`** primary-workstation updates | ⬜ |
| 5 | **`uv run pre-commit install`** on the Linux primary dev workstation clone | ⬜ Operator |
| 6 | **`./scripts/check-all.sh`** green; open PR | ⬜ |
| 7 | **Reversion** when Windows primary returns (ADR § Reversion) | ⬜ Deferred |

## Verification

```bash
cd ~/Projects/dev/data-boar
test -x .git/hooks/pre-commit
./scripts/check-all.sh
```

## References

- [PRIMARY_LINUX_WORKSTATION_PROTECTION.md](../ops/PRIMARY_LINUX_WORKSTATION_PROTECTION.md)
- [ADR 0068](../adr/ADR-0068-primary-linux-dev-workstation-temporary.md)
- [COMMIT_AND_PR.md](../ops/COMMIT_AND_PR.md)
