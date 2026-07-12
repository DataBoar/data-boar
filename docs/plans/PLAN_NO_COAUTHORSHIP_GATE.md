# Plan: No-coauthorship gate (kombi — gitleaks + pytest)

<!-- plans-hub-summary: Fail-closed kombi blocking any Co-authored-by trailer in commit messages (pytest) plus governance rule in .gitleaks.toml; A.I.I.D.C.O.B.P.P. v1.4 / ADR-0049 / ADR-0079. -->

**Status:** Active
**Date:** 2026-07-04
**Authors:** Fabio Leitao
**Priority:** P0
**GitHub:** _(operator issue TBD — kombi slice)_
**Related ADR:** [ADR 0046](../adr/ADR-0046-operator-intent-and-blameless-collaboration.md) · [ADR 0047](../adr/ADR-0047-rca-first-defect-investigation-and-fix-discipline.md) · [ADR 0049](../adr/ADR-0049-no-brittle-mitigations-robust-input-handling.md) · [ADR 0056](../adr/ADR-0056-cryptographic-adr-inventory-inv-adr-ssh-attestation.md) · [ADR 0062](../adr/ADR-0062-agent-containment-triple-audit-offband-pingpong.md) · [ADR 0071](../adr/ADR-0071-self-protecting-pii-gate.md) · [ADR 0079](../adr/ADR-0079-ecosystem-engineering-rigor-canon.md) · [ADR 0080](../adr/ADR-0080-local-validation-gate-inviolable.md)

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)

---

## Context

Cursor (and other agent UIs) may **inject** `Co-authored-by: Cursor <cursoragent@cursor.com>` into commit messages **after** `git commit` — that is **platform behaviour**, not repo policy. The org contract (**A.I.I.D.C.O.B.P.P. v1.4**, **Matriz de Regras Duras**) states: **one author per commit**; AI is a **tool** (like Ruff/Semgrep), never a co-author; **no bypass** (`--no-verify`, `commit-tree`, hook edits, skip/xfail).

## Decision (kombi — defense-in-depth)

| Layer | Mechanism | What it scans |
| ----- | --------- | ------------- |
| **A** | `.gitleaks.toml` rule `no-coauthorship-at-all` (`extend.useDefault = true`) | Tracked **content** / git-visible text matching `^Co-authored-by:` |
| **B** | `tests/test_commit_no_tool_coauthorship.py` | **Commit messages** on `origin/main..HEAD` (layer gitleaks cannot reach) |
| **C** | `tests/test_gitleaks_config.py` | Config presence + `gitleaks detect --config .gitleaks.toml` from repo root |
| **D** | `.github/workflows/gitleaks.yml` | Scheduled/push scan with `--config .gitleaks.toml` |

**Cursor injection:** If layer **B** fails because HEAD already carries `Co-authored-by: Cursor`, the **agent stops** — cure is the operator **disabling co-author injection in Cursor IDE**, then a normal `git commit --amend` that **runs hooks** (no `--no-verify`, no `commit-tree`).

## Implementation checklist

| Phase | Task | Status |
| ----- | ---- | ------ |
| 1 | Copy tested `.gitleaks.toml` + `test_commit_no_tool_coauthorship.py` from scratchpad | ✅ |
| 2 | `tests/test_gitleaks_config.py` + pre-commit hooks + CI pytest | ✅ |
| 3 | `gitleaks.yml` uses `--config .gitleaks.toml` | ✅ |
| 4 | `./scripts/check-all.sh` green before merge | ⬜ |
| 5 | Operator: Cursor co-author toggle + amend polluted commits on branch | ⬜ |

## Hard rules (agent)

1. **RED = law** — fix root cause; never weaken the gate to pass.
2. **Forbidden:** `--no-verify`, `git commit-tree`, `git update-ref` to dodge hooks, `@skip`/`xfail`/`-k` by choice, `Co-authored-by` trailers.
3. **History:** never `reset` to erase mistakes — **amend forward** after operator fixes Cursor injection.

## References

- `tests/test_commit_no_tool_coauthorship.py` — deterministic esporro + ADR list on failure
- `.gitleaks.toml` — governance rule + existing secret allowlist paths
- [PLAN_ADR_GOVERNANCE_ENFORCEMENT.md](PLAN_ADR_GOVERNANCE_ENFORCEMENT.md) — adjacent ADR Phase 1 gates
