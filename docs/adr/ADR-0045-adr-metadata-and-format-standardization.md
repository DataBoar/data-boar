# ADR 0045 — ADR metadata and format standardization

- **Status:** Accepted
- **Date (UTC):** 2026-05-12
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Context

Architecture Decision Records are durable governance artifacts in this repository.
They capture trade-offs, constrain future changes, and support auditability.

As the ADR corpus grows, inconsistent metadata or section structure increases review
cost, weakens traceability, and blocks reliable tooling queries (for example:
"list Deferred decisions", "show superseded ADRs", "find decision owner").

The repository already enforces ADR index parity and multiple gate layers
(pre-commit, tests, CI), but ADR document shape is still convention-heavy and not
fully standardized as a decision record contract.

## Decision

From this ADR forward, repository ADRs must use a MADR-aligned structure with
explicit metadata and canonical sections:

```markdown
# ADR NNNN — Title

- **Status:** [Accepted | Proposed | Deferred | Rejected | Deprecated | Superseded]
- **Date (UTC):** YYYY-MM-DD
- **Authors:** name(s)
- **Deciders:** name(s)
- **Consulted:** name(s) (optional)
- **Informed:** name(s) (optional)

## Context
## Decision
## Rationale
## Consequences
## Alternatives Considered
## Related Decisions
## References (optional)
```

**Filename convention:** ADR files must be named `ADR-NNNN-short-kebab-title.md`
where `NNNN` is a zero-padded four-digit sequential number. The `ADR-` prefix
makes ADR files unambiguously identifiable by filename alone, without relying on
directory position or content inspection. The script `scripts/new-adr.ps1`
generates compliant filenames automatically.

Status lifecycle semantics:

- **Accepted:** In force.
- **Proposed:** Under review.
- **Deferred:** Acknowledged and intentionally delayed.
- **Rejected:** Explicitly not chosen.
- **Deprecated:** Was valid, no longer recommended.
- **Superseded:** Replaced by another ADR (must cite replacement ADR).

## Rationale

1. **Accountability:** Date, Authors, and Deciders establish decision ownership.
2. **Queryability:** Standardized headers and sections allow deterministic
   search, automation, and policy checks.
3. **Governance:** Status values make lifecycle explicit instead of implied.
4. **Traceability:** Related Decisions creates a navigable decision graph.
5. **Community alignment:** Follows Nygard ADR roots, Y-statement thinking, and
   MADR evolution without creating a custom schema.

## Consequences

- **Positive:** Higher consistency and lower cognitive load when creating/reviewing ADRs.
- **Positive:** Easier indexing and future lint/tooling for decision governance.
- **Negative:** Backfill effort for older ADRs when touched.
- **Ongoing:** New ADRs should be corrected in the same PR if structure deviates.
- **Ongoing:** Repo gates can be incrementally extended to validate ADR metadata fields.

## Alternatives Considered

1. **No explicit standard** (rejected): keeps ambiguity and slows review/search.
2. **Custom local template** (rejected): reinvents well-known community practice.
3. **Guideline without enforcement path** (rejected): high drift risk over time.

## Related Decisions

- [ADR 0018 — PII anti-recurrence guardrails](ADR-0018-pii-anti-recurrence-guardrails-for-tracked-files-and-branch-history.md)
- [ADR 0020 — CI full-history PII gate](ADR-0020-ci-full-git-history-pii-gate.md)
- [ADR 0030 — Python dependency update closure](ADR-0030-python-dependency-update-closure-single-pass.md)
- [ADR 0044 — Dependabot uv ecosystem closure](ADR-0044-dependabot-uv-ecosystem-for-pyproject-lock-closure.md)

## References

- [Documenting Architecture Decisions (Michael Nygard)](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) — consulted 2026-05-12
- [MADR project — adr.github.io/madr](https://adr.github.io/madr/) — consulted 2026-05-12
- [MADR Template Primer (Olaf Zimmermann)](https://www.ozimmer.ch/practices/2022/11/22/MADRTemplatePrimer.html) — consulted 2026-05-12
