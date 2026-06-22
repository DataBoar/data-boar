# ADR 0060 — `db/` Ruff and Bandit exclusion — risk accepted (temporary)

- **Date (UTC):** 2026-06-21
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Status

Proposed

### Status history

- 2026-06-21 — Proposed (materializes number reserved by GitHub #381; disambiguation per #993)

## Context

The `db/` package ships in the production wheel but is **excluded** from Ruff lint and
Bandit security scans in `pyproject.toml` (`extend-exclude` / `exclude_dirs`). The
exclusion traces to legacy SQLAlchemy patterns and structural debt documented in the
completed Bandit security linter plan (plain-text path:
`docs/plans/completed/PLAN_BANDIT_SECURITY_LINTER.md`).

For a compliance-oriented product, **production code without linter or security-scanner
coverage** is a documented risk that must not remain a silent gap in governance.

### Numbering disambiguation (GitHub #993)

| Claimant | Relationship to ADR-0060 |
| --- | --- |
| **#381** | **Authoritative owner** — this ADR records risk acceptance for `db/` Ruff/Bandit exclusion. |
| **#382** | **Does not own** ADR-0060 — may **reference** this ADR when aligning a future mypy `db/` override policy; mypy strictness is a separate track. |
| **#675** (closed) | UMADR format audit — **did not** materialize ADR-0060; no supersession of this record. |

## Decision

1. **Accept temporary risk:** `db/` remains excluded from Ruff and Bandit until a
   tracked remediation plan removes the exclusions and a **new ADR** declares mandatory
   coverage (do **not** amend this ADR in-place when coverage is restored).
2. **Track remediation** in a dedicated plan file (`PLAN_DB_LINT_BANDIT_COVERAGE.md`,
   GitHub #381) with phased triage, fix/suppress, exclusion removal, and ADR lifecycle.
3. **CI behaviour unchanged** by this ADR alone — exclusion stays in `pyproject.toml`
   until Phase 2 of the plan lands in a separate change set.

## Rationale

1. **Auditability:** Names the gap explicitly instead of a comment-only exclusion.
2. **Lifecycle clarity:** Supersession requires a **new** ADR when `db/` enters mandatory
   coverage — behaviour change, not a typo fix.
3. **Disambiguation:** One number, one decision — `db/` lint/Bandit only.

## Consequences

- **Positive:** Reviewers and CI auditors can trace why `db/` is excluded.
- **Negative:** Production `db/` code remains outside Ruff/Bandit until the plan executes.
- **Watch:** When `db` is removed from `extend-exclude` and `exclude_dirs`, create
  **ADR-NNNN** with status **Accepted** (or **Proposed** first) and mark this ADR
  **Superseded by ADR-NNNN** — **never** flip this file to “now covered” in-place.

## Alternatives Considered

1. **Immediate inclusion in Ruff/Bandit** (deferred): blocked by structural debt; belongs
   to plan Phase 0–2, not this governance slice.
2. **No ADR — comment only** (rejected): repeats the “silent gap” pattern #993 targets.
3. **Use ADR-0060 for mypy strictness** (rejected): #382 does not own this number.

## Related Decisions

- [ADR 0045 — ADR metadata and format standardization (UMADR)](ADR-0045-adr-metadata-and-format-standardization.md) — **Reserved** → **Proposed** materialization
- GitHub #381 — plan + ADR owner
- GitHub #993 — dangling-number review

## References

- [Documenting Architecture Decisions (Michael Nygard)](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
- `pyproject.toml` — `[tool.ruff]` / `[tool.bandit]` exclusions (unchanged by this ADR)
