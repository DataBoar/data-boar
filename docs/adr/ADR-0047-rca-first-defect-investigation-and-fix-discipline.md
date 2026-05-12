# ADR 0047 — RCA-first defect investigation and fix discipline

- **Status:** Accepted
- **Date (UTC):** 2026-05-12
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Context

Past defects in this codebase were sometimes addressed with surface-level
fixes that masked root causes, leading to regressions on edge-case inputs —
for example, connector edge cases (special characters in column names, empty
result sets, null contexts from sparse SQL dialects), sampling cap boundary
conditions, and lab-op orchestration failures that reappeared after
"fixed" releases.

Fast symptom-suppression without understanding propagates fragility. A fix
that passes CI but does not address the root cause is a deferred regression.

## Decision

For incidents, defects, and unexpected failures:

1. Identify and document the root cause **before** implementing any fix.
2. Enumerate the failing conditions and edge cases explicitly — not just
   the reproducer, but the class of input or state that triggers the failure.
3. Validate the fix against the documented root cause, not just the observed
   symptom; a fix that closes the symptom but leaves the root cause reachable
   is incomplete.
4. Non-trivial PRs that address defects or regressions must include a short
   RCA summary in the PR description — one paragraph is enough; the goal is
   institutional learning, not bureaucracy.

## Rationale

The scanning engine runs against production customer databases and produces
compliance evidence. A regression in sampling, PII detection, or report output
can reach a DPO or legal team before it is caught. The cost of a second
regression on the same root cause is higher than the cost of a short RCA pass
before the first fix ships.

This discipline also feeds the public lessons archive (ADR 0042): RCA summaries
in PRs become the raw material for `docs/ops/lab_lessons_learned/` entries and
for updating the engineering manifests when a pattern recurs.

## Consequences

- **Positive:** Higher fix quality, fewer regressions, clearer post-mortems.
- **Positive:** RCA summaries in PRs reinforce institutional learning and feed
  the lab lessons archive.
- **Negative:** Slightly longer time-to-first-response for defect reports;
  acceptable given the product's compliance evidence responsibilities.
- **Ongoing:** Every non-trivial fix PR carries a short RCA block; reviewers
  (human or agent) may request one if absent.

## Alternatives Considered

1. **Fast symptom-only fixes** (rejected): Faster initial response but higher
   regression risk; acceptable only for urgent hotfixes where a follow-up RCA
   issue is filed immediately.
2. **Root-cause documentation after fix** (rejected): Loses the learning loop
   during investigation; the author's mental model of the failure is freshest
   before the fix is written, not after.
3. **Leaving this in manifesto docs only** (rejected): The defensive scanning
   manifesto and ADR 0046 cover operational posture and communication tone;
   neither constitutes a durable decision record that commits this project to
   RCA-first discipline in defect PRs.

## Related Decisions

- [ADR 0042 — Public LAB lessons archive + hub](ADR-0042-lab-lessons-learned-archive-contract.md)
- [ADR 0046 — Operator intent and blameless collaboration posture](ADR-0046-operator-intent-and-blameless-collaboration.md)
- [ADR 0015 — PoC test infrastructure with synthetic corpus and API testing](ADR-0015-poc-test-infrastructure-synthetic-corpus-and-api-testing.md)

## References

- [Defensive scanning manifesto](../ops/inspirations/DEFENSIVE_SCANNING_MANIFESTO.md) — "test what you fly; failing in production is not an acceptable outcome"
- [Engineering bench discipline](../ops/inspirations/ENGINEERING_BENCH_DISCIPLINE.md) — checklist culture; the bench that produces repeatable diagnostics
- [Cloudflare Engineering blog](https://blog.cloudflare.com/) — consulted 2026-05-12; public post-mortems with numeric evidence as the operational posture seed
