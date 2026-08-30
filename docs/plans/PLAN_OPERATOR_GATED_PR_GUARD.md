# Plan: operator-gated PR merge guard (SSHSIG)

<!-- plans-hub-summary: CI check fails PRs that touch GATE_FILES or carry label operator-gated unless the latest PR comment is Gate-Change-Approved-By plus SSHSIG bound to PR number and head SHA. Brother of issue-close guard #990. -->
<!-- plans-hub-related: PLAN_PII_GATE_INTEGRITY.md -->

**Status:** In progress (workflow + tests in implementing PR; ruleset required-check is operator-only)
**Date:** 2026-08-29
**Authors:** Fabio Leitao (operator); Cursor executor
**Priority:** **`[H0][U0]`** [P1] security-gate
**GitHub:** [#1709](https://github.com/DataBoar/data-boar/issues/1709)

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md) · [ADR 0071](../adr/ADR-0071-self-protecting-pii-gate.md) · [ADR 0072](../adr/ADR-0072-commit-gate-vs-release-gate-distinct-criteria.md) · [ADR 0056](../adr/ADR-0056-cryptographic-adr-inventory-inv-adr-ssh-attestation.md)

## Problem

`operator-gated-reopen.yml` (#990) only runs on **issue close**. A PR labeled `operator-gated` (or a PR that edits `GATE_FILES`) could merge if an agent typed `Gate-Change-Approved-By:` without SSHSIG — theatre HITL (incident class: PR #1707).

## Non-negotiables

- Do **not** trust `github.actor` (shared GitHub account).
- Do **not** scan PR **body** or **comment history** for the trailer.
- Evaluate **only the latest PR comment**.
- Trailer without verified SSHSIG is **not** approval.
- Do **not** swallow `gate_trailer_attest.py` / guard CLI exit codes.
- Reuse **`GATE_FILES`** from `scripts/gate_change_tripwire.py` (no second list).
- PR-comment SSHSIG is over **trailer + PR number + head SHA** (not trailer-only replay).
- CI runs **`pull_request_target`** with checkout of the PR **base SHA only** (never the PR tree). Changed paths and the latest comment come from the GitHub API. `scripts/__init__.py` is in **`GATE_FILES`**.

## Phases

| # | Phase | Status |
| - | ----- | ------ |
| 1 | Decision core `scripts/operator_gated_pr_guard.py` + pytest | ✅ Done (this PR) |
| 2 | Workflow `.github/workflows/operator-gated-pr-guard.yml` (`pull_request_target`, base checkout) | ✅ Done (this PR) |
| 3 | `AGENTS.md`: agents never fill `Gate-Change-Approved-By` | ✅ Done (this PR) |
| 4 | Operator: required check on ruleset `main-gate-pii` | ⬜ Pending (human GitHub settings) |
| 5 | Security Reviewer #1832: base-ref verifier + PR-bound payload | ✅ Done (this PR) |
| 6 | Security Reviewer #1832: pin YAML via `pull_request_target`; never execute PR tree; `scripts/__init__.py` in GATE_FILES | ✅ Done (this PR) |
| 7 | Security Reviewer #1832: `pulls.listFiles` includes `previous_filename` on rename/copy | ✅ Done (this PR) |

## Out of scope

- Changing global `required_approving_review_count`.
- Replacing the issue-close reopen workflow.
- Adding `on: pull_request` with the **same** required job name (untrusted YAML).
- Treating label `gate-merge-approved` as sufficient (SSHSIG required).
- Checking out `github.event.pull_request.head.sha` on `pull_request_target`.

## Operator follow-up

Add job **SSHSIG attestation when gated** as a **required** status check on **`main-gate-pii`**. Agents cannot do that.

PR comment attestation (after this lands): sign with

`uv run python scripts/gate_trailer_attest.py sign --text 'Gate-Change-Approved-By: @FabioLeitao' --pr <N> --head <40-hex> --key <operator-ed25519> -o trailer.sig`

then `format-commit-body` and paste as the **latest** PR comment. A trailer signature copied from git history will not verify.
