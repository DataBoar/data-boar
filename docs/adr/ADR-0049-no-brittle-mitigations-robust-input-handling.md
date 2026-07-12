# ADR 0049 — No brittle mitigations — robust input handling over symptom suppression

- **Status:** Accepted
- **Date (UTC):** 2026-05-12
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

### Status history

- 2026-05-12 — Accepted
- 2026-07-12 — Amended: detector ML path now avoids single-class `predict_proba` silent failures, merges profile ML terms with defaults, and adds deterministic declared-term fallback for exact matches outside entertainment contexts (#1195).

## Context

Data Boar processes inputs from environments it does not control: filesystems with
filenames that contain `[`, `]`, `&`, `#`, spaces, HTML-encoded sequences, and mixed
encodings; database schemas with column names containing special characters, reserved
words, mixed collations, empty result sets, and null contexts from sparse SQL dialects;
and API endpoints with non-standard query parameter encoding.

Past connector edge cases — special characters in column names, Windows-1252 encoded
filesystem paths, empty `INFORMATION_SCHEMA` result sets from non-standard MySQL forks —
were sometimes resolved with quick workarounds: skipping problematic columns, requiring
UTF-8-only input paths, or catching broad exceptions and continuing silently.

These mitigations pass CI on clean synthetic corpora but fail against real customer
databases and filesystems. More critically: a brittle fix that silently skips a
problematic column or file does not raise an error — it produces a **false negative** in
the compliance evidence report. The customer receives an audit trail that appears complete
but has a hole the size of the skipped input. A DPO or legal team relying on that output
cannot know it is incomplete.

## Decision

Disallow brittle mitigations as primary fix strategies across all connectors, sampling
pipelines, and report generation:

1. **No "skip and continue" without explicit logging and surface.** If an input cannot be
   processed, the failure must appear in the report output or session log — never swallowed
   silently. A scan that skips items must count and name them.
2. **No requirement to rename or pre-process inputs.** Operators must not be required to
   rename files, columns, or config values to avoid processing errors. The scanner handles
   inputs as they exist in production.
3. **No escape hacks without documented semantic justification.** If an identifier requires
   quoting or escaping, the commit must include an inline comment that cites the reason:
   the SQL vendor or dialect (e.g. `# MySQL 5.7 backtick quoting — ANSI mode not enabled
   by default`), the encoding contract (e.g. `# Windows-1252 path; Python open() requires
   explicit codec`), or the relevant RFC or spec. A single comment meeting this bar is
   sufficient — no separate doc required.
4. **No disabling of core functionality to avoid edge cases.** Disabling a connector, a
   sampling strategy, or a detection pattern because one input class causes errors reduces
   coverage and may produce silent false negatives.
5. **Fixes must handle the edge case as it exists in reality.** If the fix only works
   against a sanitized or renamed input, it is not a fix — it is a precondition that
   transfers the problem to the operator. Test fixtures must use the real problematic input
   (actual special-character filename, actual Latin-1 encoded column), not a sanitized
   proxy.

## Rationale

The product produces compliance evidence that legal and governance teams rely on.
The failure mode of a brittle mitigation — silent skip, incomplete inventory, missing
finding — is worse than a loud failure: a loud failure is visible and correctable; a
silent false negative reaches the customer and becomes part of their compliance record.

This rule is the natural consequence of ADR 0047 (RCA-first): once the root cause is
identified, the fix must address it at the root rather than suppress the symptom at the
call site.

## Consequences

- **Positive:** Connector and scanner behavior is consistent against real-world production
  inputs, not only clean synthetic corpora.
- **Positive:** False negatives from silent skips are eliminated; any scan gap is visible
  in the report or session log.
- **Negative:** Fixing edge cases properly requires deeper implementation effort and more
  rigorous testing against diverse encoding and schema corpora.
- **Ongoing:** Code reviewers verify semantic correctness of the fix, not only that the
  reported symptom no longer reproduces in CI.
- **Ongoing:** Any "skip" path in connector or sampling code must have an explicit counter
  and log line — reviewers check for bare `except: continue`, `except Exception: pass`, or
  silent `None` returns in connector paths. Bandit rules B110 and B112 catch a subset of
  these automatically.
- **Detection hardening (#1195):** the detector no longer swallows one-class ML probability indexing errors. When profile ML terms provide only one class, ML training is skipped with warning and declared exact terms still produce deterministic detection outside entertainment contexts.
- **Watch:** Skipped items that affect the completeness of a compliance report must
  appear in the report output, not only in the session log — customers cannot read
  host-bound audit logs. Logging to `audit_YYYYMMDD.log` alone does not satisfy
  Decision 1 for customer-facing scan gaps.

## Alternatives Considered

1. **Input sanitization / renaming requirement** (rejected): transfers the problem to the
   operator; production environments cannot always be sanitized before scanning.
2. **Catch-all exception handler + continue** (rejected): converts a detectable error into
   an invisible false negative in compliance output.
3. **Disabling problematic connector modes** (rejected): reduces coverage; a partial scan
   that looks complete is more dangerous than a scan that fails loudly.

## Related Decisions

- [ADR 0047 — RCA-first defect investigation and fix discipline](ADR-0047-rca-first-defect-investigation-and-fix-discipline.md)
- [ADR 0037 — Data Boar self-audit log governance](ADR-0037-data-boar-self-audit-log-governance.md)
- [ADR 0025 — Compliance positioning: evidence and inventory, not a legal-conclusion engine](ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md)

## References

- [Defensive scanning manifesto](../ops/inspirations/DEFENSIVE_SCANNING_MANIFESTO.md) — "no silent failure; every gap is surfaced"
- [Engineering bench discipline](../ops/inspirations/ENGINEERING_BENCH_DISCIPLINE.md) — test against production-realistic corpora, not only clean fixtures
