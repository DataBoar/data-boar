# ADR 0081 — No silent ML confidence failures on single-class compliance profiles

- **Date (UTC):** 2026-07-12
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Status

Proposed

## Context

Issue [#1195](https://github.com/DataBoar/data-boar/issues/1195) exposed a compliance
detection gap in `core/detector.py`:

1. The ML confidence path assumed `predict_proba(...)[0][1]`, which is not valid for
   single-class models (`shape == (n,1)`). The raised `IndexError` was swallowed and
   confidence silently fell to zero.
2. Profile ML terms from `ml_patterns_file` and inline config replaced defaults instead
   of extending them, shrinking baseline detection coverage.
3. Profiles that define only `sensitive` terms are common in the compliance samples,
   increasing the chance of single-class training paths.

This violates the anti-silent-failure posture already established in
[ADR 0049](ADR-0049-no-brittle-mitigations-robust-input-handling.md), but ADR-0049 is a
gate-protected file and must not be edited without explicit operator marker.

## Decision

1. **Single-class-safe ML confidence path:** detector ML confidence must use
   class-aware indexing from `model.classes_` and never rely on fixed `[0][1]`.
2. **No silent swallow:** ML confidence exceptions must be logged once and mapped to
   deterministic fallback behavior, never hidden by broad silent handlers.
3. **Additive ML vocabulary contract:** effective ML terms are
   `DEFAULT_ML_TERMS + ml_patterns_file + inline ml_terms` with deterministic dedupe.
4. **Declared-term deterministic fallback:** when regex does not match and confidence is
   insufficient, exact declared sensitive terms can still trigger detection outside
   entertainment contexts.
5. **Behavioral regression gate:** tests must prove that a single-class compliance sample
   still detects an exact declared term.

## Consequences

- **Positive:** compliance profiles with single-class terms no longer degrade silently to
  `ml_confidence=0`.
- **Positive:** profile customizations extend default vocabulary instead of replacing it.
- **Positive:** exact declared terms remain detectable even when ML training is skipped.
- **Trade-off:** deterministic declared-term fallback must stay scoped to avoid broad
  false positives; entertainment context remains a protected branch.

## Related Decisions

- [ADR 0049 — No brittle mitigations — robust input handling over symptom suppression](ADR-0049-no-brittle-mitigations-robust-input-handling.md)
- [ADR 0071 — Self-protecting PII gate](ADR-0071-self-protecting-pii-gate.md)

## References

- GitHub issue [#1195](https://github.com/DataBoar/data-boar/issues/1195)
