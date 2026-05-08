# ADR 0018: PII anti-recurrence guardrails for tracked files and branch history

**Status:** Accepted
**Date:** 2026-04-07
**Author:** Fabio Leitao

---

## Context

The project suffered repeated public-history exposure incidents involving personal
identifiers and infrastructure hints (for example real Windows user paths and
named personal references). Recovery required multiple history rewrites and manual
audits with high operator cost.

Existing safeguards were not enough because:

- tracked-file scanning did not cover key recurrence patterns case-insensitively;
- no deterministic branch-level history guard blocked reintroduction before PR;
- manual audits were expensive and error-prone under pressure.

| Option | Pros | Cons |
|---|---|---|
| **Chosen approach: deterministic guardrails in pre-commit + tests** | Fast fail before push, low operator overhead, explicit recurrence barriers | Requires ongoing regex maintenance and occasional false-positive tuning |
| Manual periodic audits only | Flexible, no hook maintenance | High token/time cost, non-deterministic, easy to miss edge cases |

## Decision

1. Strengthen tracked-file PII guard patterns in `tests/test_pii_guard.py` for:
   - non-placeholder Windows user paths (`c:\Users\...`);
   - non-placeholder Linux home paths (`/home/...`);
   - explicit LinkedIn profile slugs (excluding placeholders/examples);
   - sensitive family-context phrases;
   - existing medical identifier checks.
2. Add `scripts/pii_history_guard.py` and enforce it in pre-commit as
   `origin/main..HEAD` anti-recurrence gate.
3. Keep `--full-history` mode available for incident-level deep verification.
4. Treat these checks as mandatory for commit/PR workflows (`lint-only`,
   `check-all`, CI parity via pre-commit hooks).

## Consequences

- **Positive:** deterministic prevention of the exact recurrence class that caused
  repeated rewrites; lower operator cognitive load; faster go/no-go decisions.
- **Negative:** stricter hooks may surface false positives that need targeted
  regex tuning.
- **Watch:** keep placeholder allowlist stable, avoid over-broad patterns,
  periodically review forbidden literals after major remediation events.

## References

- `tests/test_pii_guard.py`
- `scripts/pii_history_guard.py`
- `.pre-commit-config.yaml`
- `tests/test_scripts.py`
- `docs/private/security_audit/PII_AUDIT_2026-04-07.pt_BR.md` (private incident record)
