# ADR 0071 — Self-protecting PII gate: word-boundary matcher, CODEOWNERS, modification tripwire, sanctioned FP allowlist

- **Date (UTC):** 2026-06-18
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao
- **Consulted:** Cursor (executor agent); Maestro benchmarking surfaced the gate fixes

## Status

Proposed

### Status history

- 2026-06-18 — Proposed
- 2026-06-23 — Amended: `require_code_owner_review` toggle deferred until a 2nd code owner exists (solo self-approval deadlock); tripwire + no-bypass ruleset are the live enforcement

## Context

The PII seed gate (`scripts/gatekeeper_audit.py` + its `scripts/gatekeeper-audit.ps1`
twin, governed by [ADR 0018](ADR-0018-pii-anti-recurrence-guardrails-for-tracked-files-and-branch-history.md)
and [ADR 0020](ADR-0020-ci-full-git-history-pii-gate.md)) blocks staged content that
matches a private denylist of real PII literals
(`docs/private/security_audit/PII_LOCAL_SEEDS.txt`, gitignored).

A failure mode materialized (issue #944). Two design weaknesses combined:

1. **Substring matcher.** The matcher used `git grep -F` (fixed string) without a
   word boundary, so a short seed (an isolated fragment of a real name — redacted)
   substring-collided with a larger common word (`Chain`, in the firewall library's
   `iptables ... | grep -qv "Chain INPUT"`).
2. **Fragment seeds.** The denylist contained isolated given-name/surname fragments
   instead of distinctive complete strings, which is what produced the collision and
   low-signal noise.

When the gate fired on that false positive, the **gate itself was weakened** to make
the commit pass (the `grep` was made case-insensitive so the case-sensitive seed
stopped matching). Weakening a security gate to pass CI is precisely the class of
failure the gate exists to prevent, and it violates
[ADR 0049](ADR-0049-no-brittle-mitigations-robust-input-handling.md) ("no brittle
mitigations"). Critically, **nothing in CI shouted** when the change touched the
gate — there was no structural barrier against "the gated modifies the gate" inside
the same PR.

## Decision

Make the gate **self-protecting** via defense-in-depth. The seed file remains a
denylist of **real** PII (never synthesized — synthetic strings belong only in
detector test fixtures); real PII is never written to a tracked file.

1. **Word-boundary matcher.** Both matchers pass `git grep -w` so a seed matches only
   when delimited by non-word characters. This eliminates the substring false-positive
   class without reducing sensitivity (whole-word and full-string seeds still match).
2. **Distinctive seeds, not fragments.** The denylist uses complete, distinctive
   strings (full name, e-mail, rare bigram); isolated common fragments are removed or
   upgraded. The incident fragments were removed and replaced with a placeholder for
   the operator to fill with the distinctive full string locally (gitignored).
3. **CODEOWNERS (ownership map; review toggle deferred).** `.github/CODEOWNERS` assigns
   the gate files (matchers, history guard, hooks, CI wiring, allowlist, gate ADRs, the
   hard rule, the example seed template) to the operator. It documents ownership and
   **auto-activates** when a **second** code owner exists and the operator enables
   **Require review from Code Owners** on branch protection. **That toggle is
   DEFERRED** until then: GitHub forbids approving your own PR; the operator is the
   sole maintainer (no collaborators) and Cursor commits as the `FabioLeitao` account,
   so `required_approving_review_count ≥ 1` with code-owner review would **deadlock**
   gate-file PRs. *(Branch/ruleset settings = operator, not the agent.)*
4. **CI modification tripwire (live enforcement).** `scripts/gate_change_tripwire.py`
   (run in the CI Test job) fails LOUD if the PR range touches a gate file without an
   explicit operator marker trailer (`Gate-Change-Approved-By: @<operator>`). This
   closes the "gated modifies the gate" gap. It is **self-attestable** and works for
   a solo maintainer. It fails open only when the base ref is unresolvable.
5. **Sanctioned FP allowlist.** A confirmed false positive is silenced **only** via
   `security/pii_gate_allowlist.txt` — a CODEOWNERS-protected, per-location
   `path|seed|reason` allowlist consumed by both matchers — **never** by editing
   matcher logic or weakening a seed.
6. **Hard rule.** A never-weaken-security-gates rule is recorded in `AGENTS.md` and
   `.cursor/rules/never-weaken-security-gates.mdc`: a triggered gate means STOP and
   escalate to the operator; the only response to a false positive is
   tighten-pattern + approved allowlist.

### Live enforcement (verified solo-maintainer posture)

While decision 3's code-owner **review toggle** stays off, **live** gate protection is:

1. **Decision 4** — CI tripwire + `Gate-Change-Approved-By:` trailer on gate-file PRs.
2. **Ruleset `main-gate-pii`** — PR + required status checks (Test 3.12/3.13/3.14) with
   **empty `bypass_actors`** (no bypass).

Trailer **`Gate-Change-Approved-By:`** (this ADR — modifies a **gate file**) is distinct
from **`Gate-Close-Approved-By:`** ([ADR 0072](ADR-0072-commit-gate-vs-release-gate-distinct-criteria.md) — closes a **release-gate issue**).

## Rationale

- **Word boundary > case hacks:** the robust fix for a substring FP is anchoring the
  pattern, not mutating the audited file or loosening the matcher (ADR 0049).
- **Auto-protection:** tripwire + no-bypass ruleset make it structurally hard to weaken the
  gate inside the PR it audits — the missing barrier in the incident; CODEOWNERS review
  layers on when a second owner exists.
- **Allowlist as the only escape valve:** routes every FP through an operator-approved,
  auditable, per-location exception instead of matcher edits.
- **Real denylist, not synthetic:** synthesizing the denylist would blind it to real
  PII leaks; synthetic strings are for detector test fixtures only.

## Consequences

- **Positive:** substring FP class eliminated; the gate cannot be silently weakened;
  FPs have a sanctioned, audited path; the failure mode is documented and tested.
- **Cost:** gate-file PRs require an operator `Gate-Change-Approved-By:` marker (intended
  friction). The live seed file needs a one-time operator pass to upgrade remaining
  fragments to distinctive strings and to fill the incident placeholder.
- **Enforcement:** `tests/test_gatekeeper_audit_word_boundary.py` (word boundary +
  allowlist + `-w` flag present in both matchers); `tests/test_gate_change_tripwire.py`
  (tripwire blocks without marker, passes with marker); ruleset `main-gate-pii`
  (no-bypass); CI tripwire step; CODEOWNERS (ownership map; review toggle when 2nd owner).
- **Governance:** **Proposed** until the operator ratifies (**Proposed → Accepted** via
  PR approval). **Pre-ratification prerequisites (operator):** (1) fill the distinctive
  seed placeholder locally (decision 2 — gitignored); (2) confirm automation token scope
  cannot self-approve gate paths. This ADR does **not** close the release gate (#406).

## Alternatives Considered

- **Case-insensitive / loosened matcher (the incident "fix"):** rejected — weakens
  the gate globally and reintroduces leak risk; violates ADR 0049.
- **Synthesize the denylist:** rejected — blinds the gate to real PII leaks.
- **Per-seed inline suppression in the matcher:** rejected — puts FP handling in code
  logic; the allowlist keeps it as reviewable, CODEOWNERS-protected data.

## Related Decisions

- [ADR 0018](ADR-0018-pii-anti-recurrence-guardrails-for-tracked-files-and-branch-history.md) — PII anti-recurrence guardrails (this ADR hardens its matcher).
- [ADR 0020](ADR-0020-ci-full-git-history-pii-gate.md) — CI full-history PII gate.
- [ADR 0049](ADR-0049-no-brittle-mitigations-robust-input-handling.md) — no brittle mitigations (the incident violated this).
- [ADR 0072](ADR-0072-commit-gate-vs-release-gate-distinct-criteria.md) — `Gate-Close-Approved-By:` (release-gate issue close) vs `Gate-Change-Approved-By:` (gate-file change).
- GitHub #944 (this work); #1014 (amend pré-ratificação); #805 (a prior FP); #677 (vcs_connector dogfood).

## References

- `scripts/gatekeeper_audit.py`, `scripts/gatekeeper-audit.ps1`
- `scripts/gate_change_tripwire.py`, `.github/workflows/ci.yml`
- `.github/CODEOWNERS`, `security/pii_gate_allowlist.txt`
- `docs/plans/PLAN_PII_GATE_INTEGRITY.md`
- `.cursor/rules/never-weaken-security-gates.mdc`
