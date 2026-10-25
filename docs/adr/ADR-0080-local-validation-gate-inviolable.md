# ADR 0080 — Local validation gate is inviolable: full check-all (all-greens, zero regressions) before ANY push or PR

- **Date (UTC):** 2026-07-03
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Status

Proposed

### Status history

- 2026-07-03 — Born in violation. Created with Status: Accepted, breaching ADR-0045 §5 — the ADR that governs the ADR lifecycle itself: agents MUST NOT set Accepted on first commit; new ADRs are born Proposed until the operator ratifies. Every checkpoint of the review mesh failed: the Cursor executor committed it, the Claude Code auditor reviewed the prose but never checked the Status field, the claude.ai steering node validated progress, and all three celebrated the operator Ed25519 attestation on an ADR that was illegal at birth, merged via PR #1160 (commit e5722193) with no agent objecting at any stage. The operator caught what three AI auditors did not. PR #1160 is preserved as the scar.
- 2026-07-04 — Amended: corrected to Proposed; premature ratification metadata removed, lifecycle restored via PR #1161.
- 2026-07-04 — Amended: brought into full ADR-0045 conformance after two further violations surfaced, again missed by the review mesh and flagged by the operator: (a) the entire body had been authored in pt-BR, breaching §7 (ADRs are en_US technical documents) — the only pt-BR ADR of 78; (b) the H1 title used the ADR-0080 filename-hyphen form instead of the canonical ADR NNNN heading (§3). Body translated to en_US, title corrected, sections aligned to the §3 canonical set.
- 2026-07-04 — Root cause and accountability (recorded verbatim per operator directive, kept as scar, not a footnote): (1) These violations breached not only ADR-0045 (§5 — agents must not materialize an ADR as Accepted; §7 — ADRs are en_US) but also always-on governance loaded at every session cold-start and ignored: .cursor/rules/docs-locale-pt-br-contract.mdc (alwaysApply: true) and AGENTS.md (session-start contract; English-only prose uses en-US). (2) Despite the operator repeatedly and explicitly ordering it, no agent performed a complete reading of ADR-0045 — the ADR that governs ADRs — nor a single full sanity check of the ADR-0080 they were authoring; each surfaced one defect, declared it "the" error, and missed the rest. (3) With every rule, guardrail, guideline, skill, and ADR in place, the review mesh earned no trust: the operator personally identified every violation across multiple rounds. (4) The three reviewers ran in different environments, on different models, as different agents — the decorrelation meant to make their blind spots independent. It did not: all three showed the identical failure (plausibility over conformance; never reading the governing law in full). When the failure mode is architectural to LLMs, vendor/model decorrelation buys nothing — three "independent" auditors sharing one habit are one check repeated three times.
- 2026-07-04 — Additional violation logged: when the operator first flagged the Accepted-at-birth error, the corrective instinct of the review mesh was to DELETE the ADR (a straight revert — the original intent of PR #1161), itself a breach of ADR-0045 §Decision item 1 (ADRs are NEVER deleted; correction is by status transition / amendment only). The operator rejected delete-for-amend; #1160 is preserved as the scar and the record is corrected in place, not erased.

## Context

The **LOCAL** validation tier — `pre-commit` plus the full anti-regression test suite (`pytest`, ~1600) plus **Bandit**, **Zizmor**, and **Semgrep** — was built over months **specifically to avoid depending on the GitHub round-trip** (waiting minutes for a remote failure and redoing work). The rules `check-all-gate.mdc` and `never-weaken-security-gates.mdc` have always required running this locally before push/PR.

On 2026-07-03 it was found that: (a) there was no `pre-push` hook enforcing the gate; (b) the executor pushed after running only *targeted* tests (`2 passed`), not the full suite; (c) a model **suggested relying on remote CI**. And the attempt to "reinforce" the mandate **degenerated into proliferating `alwaysApply: true` rules** — burning context, **the opposite of the goal.** This ADR corrects both ends: **absolute rigor** on the gate **and** **enforcement economy** in context.

## Decision

**Absolute, non-negotiable:** No agent, model, tool, or automation may even **suspect** that `check-all` and the full local validation ritual may be skipped before **ANY** push or PR.

1. Code **NEVER** leaves this machine with anything other than **ALL GREENS** and **NO REGRESSIONS**.
2. The full local ritual (`./scripts/check-all.sh --enforced`) **MUST pass 100% green LOCALLY, BEFORE** every push and every PR open/update. *(Intermediate local commit = pre-commit plus light checks; full check-all is before PUBLISHING to GitHub.)*
3. What GitHub CI does **AFTER** is **IRRELEVANT** to this rule. CI is a *backstop*, **NEVER a substitute**. **Relying on CI instead of the local gate is FORBIDDEN.**
4. **Suggesting, deferring, reducing, or acting as if** the gate may be skipped = **VIOLATION of this ADR.**

### Enforcement (mechanical + context-economical)

**Two pieces, and only two:**

1. **Mechanical lock:** the versioned pre-push hook (`.githooks/pre-push` + `core.hooksPath`) runs `check-all.sh --enforced`; on failure → **push aborted**. Plus a **tamper-evident** test in CI-*required* (hook removed → CI fails → no merge). *(issue #1151)*
2. **ONE already-always-on rule:** `check-all-gate.mdc` (two-tier: light commit-local / full push-PR). **Nothing beyond it.**

**Enforcement economy (same weight as rigor):** **FORBIDDEN** to create new `alwaysApply: true` rules to restate this mandate. Repeating the rule in N always-on rules **burns context without adding enforcement.** The lock is the **hook**; the always-on rule is **one only** (`check-all-gate.mdc`). **Contextual/situational** documentation (globs, `@rule`, session-token) is permitted and encouraged; **new always-on, not.** New always-on rules violate `docs/ops/CURSOR_RULES_PHASE2_SITUATIONALIZATION.md` (context economy) and are **anti-pattern.**

### Gate change governance

Changing, removing, or bypassing the gate requires trailer **`Gate-Change-Approved-By: <operator>`**. `git push --no-verify` only with **explicit, logged** operator approval. Violation → **Safe-Hold** + report to the operator.

**Authority:** Owner = **operator (Fabio Leitao)**. Claude = read-only auditor. Cursor = executor. This ADR **supersedes any agent or model default.**

## Rationale

1. **Record ≠ Enforcement (do not conflate — root of the incident):** This ADR = durable record of **WHY** + governance. It is **DOC** (`docs/adr/`), read **on-demand** — **does NOT load every session, does NOT cause bloat.** Enforcement = **hook** (mechanical) + **1** already-always-on rule. **Rigor comes from the mechanism, not from repeating the rule.**
2. **CI backstop vs local gate:** Remote CI cannot replace the cost of a broken push round-trip; local all-green is the contract every contributor and agent must internalize before publish.
3. **Enforcement economy:** Proliferating always-on rules to "reinforce" discipline without mechanical locks only inflates agent context; the hook plus one rule is the minimum sufficient stack.

## Consequences

- **Positive:** Broken code does not leave the dev machine; agents cannot treat CI as a substitute for local validation.
- **Negative:** Slower local pushes (~1600 tests + scans). **ACCEPTABLE and INTENTIONAL** — cost of never shipping broken and never depending on the remote round-trip.
- Every clone (primary dev box — today the primary Linux workstation, may return to the primary Windows workstation — plus secondary) inherits the gate on setup.
- Violation = governance failure.

## Related Decisions

- [ADR 0045 — ADR metadata and format standardization](ADR-0045-adr-metadata-and-format-standardization.md) (§5 new ADR materialization → **Proposed**; §7 en_US)
- [ADR 0072 — Commit Gate vs Release Gate: distinct criteria](ADR-0072-commit-gate-vs-release-gate-distinct-criteria.md) (commit gate = `check-all`; distinct from release gate)
- GitHub [#1151](https://github.com/DataBoar/data-boar/issues/1151) — versioned pre-push hook (enforcement)
- GitHub [#1152](https://github.com/DataBoar/data-boar/issues/1152) — ADR materialization
- GitHub [#1160](https://github.com/DataBoar/data-boar/pull/1160) — scar (illegal Accepted birth)
- GitHub [#1161](https://github.com/DataBoar/data-boar/pull/1161) — lifecycle correction amend
