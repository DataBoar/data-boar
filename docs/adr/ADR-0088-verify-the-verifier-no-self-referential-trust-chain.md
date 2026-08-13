# ADR 0088 — Verify the verifier: integrity/authorization checks must not depend on the artifact they are verifying

- **Date (UTC):** 2026-08-13
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Status

Proposed

### Status history

- 2026-08-13 — Proposed (born Proposed per ADR-0045; Accepted only via HITL ratification / SSHSIG per ADR-0056).

## Context

Integrity and authorization mechanisms sometimes import, load, or rely on a module, function,
or artifact as part of establishing trust — while only validating that same artifact *after*
it has already been used. If that dependency is tampered with, the check can report success
regardless of tampering: the check verifies nothing, because its own foundation was never
verified. This pattern has recurred across the ecosystem in different shapes: a trust-check
module executed before its own integrity is confirmed; a hashing primitive relied on by
multiple downstream checks without itself being pinned or verified first; a manifest of
trusted artifacts that does not include itself within its own trust boundary.

The project doctrine (see ADR-0049) already rejects brittle, symptom-level mitigations in
favor of fixing root cause. This ADR names the specific recurring root cause in the
integrity/trust domain and fixes the general pattern, not just individual instances.

## Decision

1. **Bottom-up verification order:** any verification chain must verify its own dependencies
   — the code doing the verifying — before using them to verify anything else. Establish
   integrity bottom-up: pin/verify the primitive (hash function, crypto library) first, then
   verify the mechanism that depends on it, and only then use that mechanism on application
   data.
2. **Self-inclusion:** any manifest or allowlist of "things we trust" must include the
   manifest-processing code and its direct dependencies within its own coverage — not only the
   artifacts it lists.
3. **No inherited-trust assumption:** do not assume that verifying layer N automatically
   covers layer N+1. Any layer that can be independently tampered with must be independently
   checked.
4. **Loud-failure still required:** tamper-evident (not tamper-proof) remains acceptable
   doctrine when a check genuinely cannot be made self-verifying — but it must fail loud and
   report to the operator. A self-referential bypass instead produces a false "OK" with zero
   evidence of tampering, which is strictly worse than an honest degraded or failed state.

## Consequences

- **Positive:** closes a class of "looks-verified-but-isn't" bugs rather than individual
  instances.
- **Positive:** gives reviewers (human or automated) a named, checkable pattern for future
  audits: "does this verifier verify itself first?"
- **Trade-off:** adds an extra verification hop to bootstrap sequences (verify-the-verifier
  before verify-the-target); minor complexity/perf cost, justified by the alternative being
  silent compromise.

## Related Decisions

- [ADR 0049 — No brittle mitigations — robust input handling over symptom suppression](ADR-0049-no-brittle-mitigations-robust-input-handling.md)
- [ADR 0071 — Self-protecting PII gate](ADR-0071-self-protecting-pii-gate.md)
- [ADR 0080 — Local validation gate is inviolable](ADR-0080-local-validation-gate-inviolable.md)

## References

- Generic doctrine — deliberately does not cite private satellite issue numbers (this ADR
  is public; recurring instances that motivated it live outside this repository). Satellite
  repos in the ecosystem should link back to this ADR from their own local decision records
  when they hit this pattern, rather than re-deriving the reasoning.
