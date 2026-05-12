# ADR 0020 — CI must scan full Git history for PII anti-recurrence patterns

**Date:** 2026-04-08
**Status:** Accepted
**Author:** Fabio Leitao

---

## Context

Tracked-file guards (`tests/test_pii_guard.py`) and incremental history checks catch many issues before merge, but **public Git history** can still contain sensitive literals in **old commits** unless the full object graph is scanned. Shallow CI checkouts would miss that class of defect.

## Decision

1. The **CI test job** runs `uv run python scripts/pii_history_guard.py --full-history` after the full pytest suite, on every push/PR to `main`/`master`.
2. **Checkout** for the test (and lint) jobs uses `fetch-depth: 0` so `git log --all` in the guard sees complete history.
3. Surgical remediation of past history uses `git filter-repo` and `scripts/filter_repo_pii_replacements.txt` (see `scripts/run-pii-history-rewrite.ps1`); **stale remote branches** that still point at pre-rewrite commits must be deleted or updated or the guard will still see old blobs via `refs/remotes/*`.

## Consequences

- **Positive:** Regressions that reintroduce forbidden patterns anywhere in history fail CI before merge.
- **Cost:** Slightly longer CI (~seconds to low tens of seconds depending on repo size) and full clone bandwidth.
- **Operational:** Contributors must not rely on shallow clones if they run `--full-history` locally; CI remains the canonical full scan on clean trees.

## References

- [ADR 0018](ADR-0018-pii-anti-recurrence-guardrails-for-tracked-files-and-branch-history.md)
- [ADR 0019](ADR-0019-pii-verification-cadence-and-manual-review-gate.md)
- `scripts/pii_history_guard.py`, `scripts/run-pii-history-rewrite.ps1`
- `docs/ops/PII_PUBLIC_TREE_OPERATOR_GUIDE.md` (Parts I–II; `PII_VERIFICATION_RUNBOOK*.md` remains a redirect stub)
