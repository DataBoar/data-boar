# Plan: ADR governance enforcement (deterministic test suite)

<!-- plans-hub-summary: Phase 1 anti-regression tests for ADR-0045 lifecycle, locale, immutability, and anti-deletion; Phase 2 prose/dangling refs. GitHub #1162. -->

**Status:** Active
**Date:** 2026-07-04
**Authors:** Fabio Leitao
**Priority:** P1
**GitHub:** [#1162](https://github.com/DataBoar/data-boar/issues/1162)
**Related ADR:** [ADR 0045](../adr/ADR-0045-adr-metadata-and-format-standardization.md) · [ADR 0080](../adr/ADR-0080-local-validation-gate-inviolable.md)

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)

---

## Context

The **ADR-0080 incident** showed that policy in `.cursor/rules/` and ADR-0045 did not prevent agents from materializing an illegal ADR (born `Accepted`, pt-BR body, wrong H1, delete attempt). Issue **#1162** adds **mechanical** anti-regression tests so governance holds regardless of which agent is at the keyboard.

Golden rules (from #1162 — non-negotiable):

1. **Normalize EOL** (`\r\n` → `\n`) before parsing — working tree may be CRLF.
2. **Prove GREEN** against the full ADR corpus before wiring a hard gate; tune tests, not legitimate ADRs.
3. **Never irrecoverable false-block** — smarter tests (rename-aware deletion) or operator override trailer (`ADR-Governance-Override-Approved-By:`).

## Scope

| Track | Deliverable |
| ----- | ----------- |
| Phase 1 | `tests/test_adr_governance_phase1.py` + `tests/adr_governance_support.py` — T1, T2, T5, T6 |
| Fixture | `tests/fixtures/adr_genesis_date_lines.json` — frozen genesis `Date (UTC)` lines (T6 corpus) |
| Hooks | `.pre-commit-config.yaml` — `adr-governance-phase1` pytest hook |
| Phase 2 | T3 prose locale density · T4 anti-dangling `ADR-NNNN` refs (CI) — **deferred** |
| ADR-0074 smoke | Materialize phantom ADR + planted violations — **deferred** (separate slice) |
| ADR-0045 amend | Codify “every mechanizable rule has a test” — **deferred** (in-place §8) |

**Out of scope (existing coverage):** `test_adr_inventory_sync`, `test_adr_readme_index_sync`, cryptographic `inv-adr.ps1` inventory.

## Phase 1 tests (deterministic)

| ID | Rule | Mechanism |
| -- | ---- | ----------- |
| **T1** | New ADR `## Status` ∈ {`Proposed`, `Reserved`} | Staged `git diff --diff-filter=A` on `docs/adr/ADR-*.md` |
| **T2** | H1 `^# ADR \d{4} — `; exact metadata labels; no pt-BR `##`/`###` headings | Full corpus scan |
| **T5** | ADRs never deleted | Staged diff; `R*` rename allowed; bare `D` blocked |
| **T6** | `Date (UTC)` immutable | Frozen fixture vs working tree; staged diff must not mutate line |

## Implementation checklist

| Phase | Task | Status |
| ----- | ---- | ------ |
| 1a | `tests/adr_governance_support.py` + Phase 1 tests | ✅ |
| 1b | Genesis date fixture (78 ADRs) | ✅ |
| 1c | Pre-commit hook `adr-governance-phase1` | ✅ |
| 1d | ADR-0080 brought to ADR-0045 shape on branch (corpus GREEN for T2) | ✅ |
| 1e | `./scripts/check-all.sh --enforced` green | ✅ |
| 1f | PR `Closes #1162` — **operator merge only** | ⬜ |
| 2 | T3 + T4 + ADR-0074 smoke + ADR-0045 governance amend | ⬜ |

## Operator override

When a legitimate exception is required (rare), add to the commit message:

```text
ADR-Governance-Override-Approved-By: Fabio Tavares Leitão
```

Incremental T1/T5/T6 staged checks skip when this trailer is present. Prefer fixing the test or using `git mv` for renames instead.

## References

- [ADR 0045](../adr/ADR-0045-adr-metadata-and-format-standardization.md) — UMADR constitution
- [PLAN_ADR_GOVERNANCE_LIFECYCLE.md](PLAN_ADR_GOVERNANCE_LIFECYCLE.md) — lifecycle manifesto
- GitHub [#1162](https://github.com/DataBoar/data-boar/issues/1162) — spec (Claude Code auditor)
