# Plan: PII gate integrity — self-protecting seed gate

**Status:** In progress
**Date:** 2026-06-18
**Authors:** Fabio Leitao
**Priority:** H0 / U0
**GitHub:** [#944](https://github.com/FabioLeitao/data-boar/issues/944) (self-protecting gate — closed; ongoing maintenance per ADR-0071)

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md) · [ADR 0071](../adr/ADR-0071-self-protecting-pii-gate.md) · [ADR 0018](../adr/ADR-0018-pii-anti-recurrence-guardrails-for-tracked-files-and-branch-history.md) · [ADR 0020](../adr/ADR-0020-ci-full-git-history-pii-gate.md) · [ADR 0049](../adr/ADR-0049-no-brittle-mitigations-robust-input-handling.md)

<!-- plans-hub-summary: Harden the PII seed gate to be self-protecting (issue #944): word-boundary matcher, distinctive real seeds (no synthesis), CODEOWNERS + branch protection, CI modification tripwire, operator-approved per-location FP allowlist, hard rule against weakening gates. -->
<!-- plans-hub-related: PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md -->

## Motivation

The PII seed gate fired on a false positive: a short seed (an isolated fragment of a
real name) substring-collided with a common word (`Chain`) in the firewall library.
The gate was then **weakened** (matcher made case-insensitive) to pass the commit —
the exact failure class the gate exists to prevent (issue #944, [ADR 0049](../adr/ADR-0049-no-brittle-mitigations-robust-input-handling.md)).
Nothing in CI shouted when the gate itself was modified. This plan makes the gate
**self-protecting** so it cannot be silently weakened, and resolves the FP the right
way (tighten + sanctioned exception), never by loosening detection.

The seed file stays a denylist of **real** PII (never synthesized; synthetic strings
are only for detector test fixtures). Real PII is never written to a tracked file.

## Phases

| # | Phase | Status |
| - | ----- | ------ |
| 1 | Revert the case-insensitive matcher hack in `scripts/labop-firewall-lib.sh` (atomic with phase 2) | ✅ Done |
| 2 | Word-boundary matcher (`git grep -w`) in `gatekeeper_audit.py` + `gatekeeper-audit.ps1` | ✅ Done |
| 3 | Curate seeds: remove isolated fragments, replace with distinctive real strings; placeholder for the incident name; audit the file (operator finishes locally) | 🔄 Tracked (operator pass) |
| 4 | `.github/CODEOWNERS` covering gate files → operator | ✅ Done |
| 5 | CI modification tripwire (`scripts/gate_change_tripwire.py` + ci.yml step) + per-location FP allowlist (`security/pii_gate_allowlist.txt`, consumed by both matchers) | ✅ Done |
| 6 | [ADR 0071](../adr/ADR-0071-self-protecting-pii-gate.md) (Proposed) + tests (word-boundary; tripwire) + hard rule (`.cursor/rules/never-weaken-security-gates.mdc`, AGENTS.md) | ✅ Done (ADR Proposed) |

## Operator follow-ups (settings / local, not the agent)

- ⬜ Branch protection on `main`: "Require review from Code Owners" + "Do not allow bypass".
- ⬜ Scope the automation/bot token so it cannot self-approve gate paths.
- ⬜ Live seed file (`docs/private/security_audit/PII_LOCAL_SEEDS.txt`, gitignored):
  fill the operator placeholder seed line (added in place of the incident fragments)
  with the distinctive full string, and upgrade the remaining isolated fragments to
  distinctive bigrams.
- ⬜ Ratify [ADR 0071](../adr/ADR-0071-self-protecting-pii-gate.md) (Proposed → Accepted).

## Acceptance

- Revert + word-boundary atomic; distinctive seeds; CODEOWNERS; tripwire; allowlist;
  ADR; green tests. The release gate (#406) is **not** closed by this work.
