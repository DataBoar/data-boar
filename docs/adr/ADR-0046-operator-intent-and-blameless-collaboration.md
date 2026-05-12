# ADR 0046 — Operator intent and blameless collaboration posture

- **Status:** Accepted
- **Date (UTC):** 2026-05-12
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Context

Data Boar is developed under engineering standards shaped by the author's
professional background as an RCDD-certified network infrastructure designer.
That background surfaces directly in how the product is built: hard sampling
caps, explicit fallback hierarchies, mandatory statement attribution, observable
failure modes, and zero tolerance for silent degradation.

The repo uses AI-assisted development extensively — Cursor agent sessions,
completão orchestration, automated merge and lab-op pipelines. Rigorous
requirements (strict PR expectations, mandatory test coverage, tightly scoped
CLI flags, conservative sampling posture, narrow sudoers baseline) can be
misread by AI assistants or contributors as adversarial feedback or as obstacles
to negotiate away.

That misreading creates friction, slows iteration, and degrades collaboration
quality. The standards are professional expectations rooted in operational
experience, not malice. Future contributors are expected to operate under the
same standard of rigor regardless of their own background or credentials.

## Decision

- **Interpret author and contributor requirements as rigor, not friction.** When
  a strict constraint is specified — timeout cap, no ORDER BY, mandatory
  attribution comment, minimal public surface — treat it as a professional
  standard backed by operational experience, not a blocker to negotiate away
  or quietly relax.
- **Use blameless, system-focused language** in all reviews, post-mortems,
  issues, PRs, and agent chat sessions. Attribute failures to systems and
  incentives, not to individuals.
- **Distinguish disagreement from misunderstanding.** If a requirement appears
  to conflict with an existing ADR, guideline, or rule, state the conflict
  clearly and ask for resolution — do not silently modify the constraint to
  avoid friction.
- **High standards are a product signal, not a personality trait.** The same
  rigor that governs SQL sampling caps, PII guardrails, and defensive scan
  posture applies to contributor communication expectations. Relaxing one does
  not justify relaxing the other.

## Rationale

The Data Boar engineering doctrine was assembled because the product runs
against production customer databases and produces compliance evidence that
legal and governance teams rely on. Errors introduced by casual collaboration
carry the same risk as errors in the scanner itself.

The blameless posture mirrors the product's own design contract: just as the
scanner leaves no silent failures (every fallback is logged, every cap
violation is surfaced), the engineering process must leave no silent resentment
— every constraint disagreement is surfaced and resolved, not swallowed.

## Consequences

- **Positive:** Healthier collaboration; faster iteration; higher trust between
  author, contributors, and AI assistants; fewer misread constraints sliding
  into code silently.
- **Positive:** Consistent tone in PRs, issues, and session chat — professional
  regardless of who or what is reviewing.
- **Negative:** Requires agents to hold a nuanced model of "strict = professional"
  vs "strict = hostile"; not all models default to this posture.
- **Ongoing:** Blameless communication is the expected norm in issues, PRs, and
  agent session transcripts.
- **Ongoing:** When a constraint feels unexplained, ask for context — do not
  assume arbitrariness.

## Alternatives Considered

1. **Strict enforcement without nuance** (rejected): damages collaboration
   quality; creates unnecessary friction when a constraint needs clarification
   or exception.
2. **Loose standards to avoid friction** (rejected): compromises operational
   safety and product reliability — unacceptable for a product that touches
   customer databases and produces compliance evidence.
3. **Leaving this implicit in AGENTS.md and doctrine files** (rejected): those
   are behavioural guidelines and manifestos, not a durable decision record.
   An ADR makes the posture explicit, queryable, and citable in PR threads —
   ensuring future agents and contributors cannot claim the expectation was
   ambiguous.

## Related Decisions

- [ADR 0025 — Compliance positioning: evidence and inventory, not a legal-conclusion engine](ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md)
- [ADR 0037 — Data Boar self-audit log governance](ADR-0037-data-boar-self-audit-log-governance.md)
- [ADR 0045 — ADR metadata and format standardization](ADR-0045-adr-metadata-and-format-standardization.md)

## References

- [Defensive scanning manifesto](../ops/inspirations/DEFENSIVE_SCANNING_MANIFESTO.md) — the operational posture contract with customer databases
- [Actionable governance and trust](../ops/inspirations/ACTIONABLE_GOVERNANCE_AND_TRUST.md) — blameless deliverable contract; the report delivers the path to the cure
- [Engineering bench discipline](../ops/inspirations/ENGINEERING_BENCH_DISCIPLINE.md) — checklist culture and narrated logs
- [AGENTS.md](../../AGENTS.md) — agent session rules and operator-direct-execution posture
