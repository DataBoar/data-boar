# ADR 0019 — PII verification cadence and manual review gate

- **Status:** Accepted
- **Date (UTC):** 2026-04-07
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Context

ADR 0018 established deterministic anti-recurrence guardrails in pre-commit and
tests, centered on tracked-file and branch-level checks.

After incident recovery and repeated fresh-clone validations, another gap became
clear: automated checks alone are necessary but not sufficient for final SAFE
decisions because the operator keeps curated local/private criteria that are not
stored in tracked docs.

Without an explicit operational cadence and a mandatory manual review gate:

- teams can run scripts but still miss context-sensitive classification decisions;
- SAFE/NOT SAFE outcomes may drift between operators and sessions;
- recurring audits become ad-hoc and higher-cost.

## Decision

1. Adopt a tiered verification cadence in `docs/ops/PII_PUBLIC_TREE_OPERATOR_GUIDE.md` (Part I — verification cadence). The former `PII_VERIFICATION_RUNBOOK*.md` paths remain as **redirect stubs** only.
   - short run (weekly / pre-sensitive PR);
   - mid run (monthly);
   - long run (quarterly or post-incident).
2. Make manual review of local/private criteria a **required gate** before marking
   SAFE.
3. Keep deterministic scripts as first-class controls inside that runbook:
   - `scripts/new-b2-verify.ps1`
   - `scripts/pii_history_guard.py`
   - `tests/test_pii_guard.py`
4. Keep person-specific and case-specific seeds in private notes/files only (not
   tracked docs).

## Consequences

- **Positive:** clearer operator protocol, consistent SAFE decisions, lower
  ambiguity around context-sensitive terms, less rework.
- **Negative:** includes a manual step that cannot be fully automated.
- **Watch:** periodically tune runbook seeds and classifications as private policy
  evolves; keep scripts and runbook in sync.

## References

- `docs/adr/0018-pii-anti-recurrence-guardrails-for-tracked-files-and-branch-history.md`
- `docs/ops/PII_PUBLIC_TREE_OPERATOR_GUIDE.md` (canonical procedural text)
- `docs/ops/PII_PUBLIC_TREE_OPERATOR_GUIDE.pt_BR.md`
- Legacy redirect stubs (bookmarks / old links): `docs/ops/PII_VERIFICATION_RUNBOOK.md`, `docs/ops/PII_VERIFICATION_RUNBOOK.pt_BR.md`
- `scripts/new-b2-verify.ps1`
- `scripts/pii_history_guard.py`
- `tests/test_pii_guard.py`
