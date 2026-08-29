# Plan: mypy gradual strictness

<!-- plans-hub-summary: Incremental mypy strictness by module, dev-only signal until CI-ready -->
<!-- plans-hub-related: completed/PLAN_BANDIT_SECURITY_LINTER.md, completed/PLAN_SEMGREP_CI.md -->

**Status:** Not started
**Priority:** H3
**Related:** [docs/QUALITY_WORKFLOW_RECOMMENDATIONS.md](../QUALITY_WORKFLOW_RECOMMENDATIONS.md) §5, [#382](https://github.com/DataBoar/data-boar/issues/382), [ADR-0060](../adr/ADR-0060-db-lint-bandit-exclusion-risk-accepted.md)

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)

## Problem

mypy is effectively disabled (`disallow_untyped_defs = false`, `check_untyped_defs = false`,
`warn_return_any = false`). Without a concrete plan, "tighten later" accumulates indefinitely.

## Constraints (must respect before any phase)

- mypy stays **dev-only** (NOT added to the CI gate) until Phase 3 report is clean.
- `db/` must be in `[[tool.mypy.overrides]]` with `ignore_errors = true` from **Phase 0** onward,
  aligned with [ADR-0060](../adr/ADR-0060-db-lint-bandit-exclusion-risk-accepted.md) (`db/` has
  structural issues; Ruff/Bandit exclusion remediation is tracked from [#381](https://github.com/DataBoar/data-boar/issues/381) as `PLAN_DB_LINT_BANDIT_COVERAGE.md` — do not type `db/` here).
- Per-module overrides are the mechanism — **no global flag changes** until Phase 3.

This tracking issue (**#382**) is **docs only**: it does **not** change `pyproject.toml`, CI
workflows, or Python sources. Phase 0+ is a **separate** issue after this plan lands.

## Phases

| Phase | Deliverable | Status |
| ----- | ----------- | ------ |
| 0 – Baseline triage | Run `uv run mypy api core config` locally; document error count by module; add `[[tool.mypy.overrides]] ignore_errors = true` for `db/` and any other module with > 50 errors | ⬜ Pending |
| 1 – Wave 1 modules | Enable `check_untyped_defs = true` per-module for the 3 modules with fewest errors from Phase 0 triage; fix errors; no global changes | ⬜ Pending |
| 2 – Wave 2 modules | Expand to next 3–5 modules; add type stubs where needed (`types-PyYAML` already present); add `disallow_untyped_defs` per-module progressively | ⬜ Pending |
| 3 – CI gate | When global error count < 20: add mypy to CI with `continue-on-error = false`; remove `ignore_errors` overrides for cleaned modules | ⬜ Pending |

## Non-goals

- Enabling mypy strict mode globally before Phase 3
- Adding mypy to CI before Phase 3 is complete
- Typing `db/` before the ADR-0060 / #381 `db/` lint-Bandit coverage work is done
