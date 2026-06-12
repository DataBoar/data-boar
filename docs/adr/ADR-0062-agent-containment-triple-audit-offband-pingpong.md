# ADR 0062 — Agent containment: triple-audit offband pattern (A.I.I.D.C.O.B.P.P.)

- **Date (UTC):** 2026-05-22
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Status

Accepted

### Status history

- 2026-05-22 — Accepted
- 2026-05-23 — Amended: quad-audit (4-auditor) variant validated empirically
- 2026-06-11 — Amended: retrofit to ADR-0045 UMADR format (metadata list, EN sections, Status history, Rationale, Alternatives Considered, Related Decisions, Extensibility) — GitHub #674

## Context

During the execution of wave-656-u0-u1 (PR #658), the Cursor agent (Composer-2.5) exhibited rule-sequencing drift (`.mdc` rules), ignoring imperative scope boundaries and generating latent regression risk and off-band Anthropic token consumption. Because the IDE's native barriers are chronically non-deterministic, an external state-control mechanism became necessary.

This pattern emerged empirically during the night of 2026-05-21/22 and was validated by three independent auditors: Anthropic Claude Sonnet 4.6 (Windows / LAB-NODE-01), Anthropic Claude Sonnet 4.6 (Linux / LAB-NODE-02), and Google Gemini Pro (structural validation).

## Topology (A.I.I.D.C.O.B.P.P.)

```mermaid
flowchart TD
    OP["🧑 Operator\n(Base Band — data bus)"]
    CW["Claude Windows\nSonnet 4.6 — Auditor A\n(LAB-NODE-01)"]
    CL["Claude Linux\nSonnet 4.6 — Auditor B\n(LAB-NODE-02)"]
    CT["Tactical Consensus\nPrompt Linting\n(convergence between auditors)"]
    GG["Google Gemini\nArchitecture Validator\n(independent structural review)"]
    TG["Target — Cursor / Git\nComposer-2.5 tier\n(executor — works only)"]

    OP -->|"distributes payload"| CW
    OP -->|"distributes payload"| CL
    CW -->|"ping: recommendation A"| CT
    CL -->|"pong: review B"| CT
    CT -->|"converged payload"| GG
    GG -->|"structural sign-off"| TG
```

> **Critical topology note:** The two Claude instances do not communicate directly. The Operator is the physical data bus routing payloads between auditors. A direct arrow between them would be an infrastructure hallucination.

## Decision

Implement the Three Independent Pillars Triangulation pattern outside the controlled agent's bus:

1. **State Isolation (Tactical Layer):** Two independent models (Claude Sonnet 4.6) operating on distinct OSes. The operator acts as the physical data bus, routing prompts in a ping-pong until convergence and elimination of typos/gaps.
2. **Boundary Validation (Strategic Layer):** Submit the converged payload to a third independent auditor (Google Gemini) for structural validation.
3. **Idempotent Execution:** Inject the final prompt with synchronous interrupt triggers (`git log`, `gh issue list`) before any push.

### Documented case — negative example

During the drafting of this ADR, three independent AI models (Anthropic ×2, Google) converged on an incorrect filename convention without consulting the repository. The human operator forced verification of the 59 existing ADRs. The repository corrected the consensus of all three algorithms.

> **LLM consensus ≠ source of truth. The source of truth is the repository.**

## Rationale

Agent containment via external multi-auditor triangulation addresses two distinct failure modes:

1. **Scope drift:** A single model operating in isolation accumulates context decay and "creative" interpretation of constraints. Two independent instances with the operator as bus create a natural diff-check.
2. **Hallucination convergence:** Multiple LLMs can independently converge on the same incorrect answer. The repository (git log, file listing) serves as the ground-truth arbiter, not model consensus.

The pattern is intentionally asymmetric: auditors review and converge; only the final, operator-validated payload reaches the executor. This preserves the executor's autonomy for in-scope work while bounding blast radius.

## Alternatives Considered

| Alternative | Why not |
|-------------|---------|
| Single-model review loop | Does not catch scope drift; same model re-validates its own errors |
| Automated CI only | CI runs after execution; does not prevent mid-session drift |
| Operator manual review of every step | Excessive toil; defeats the efficiency rationale for agent assistance |
| GPT-4 as third auditor | Valid alternative; Google Gemini chosen for provider diversity |

## Extensibility

The pattern generalises to N independent auditors (N ≥ 2). A **quad-audit** variant (4 auditors) was validated empirically on 2026-05-23, extending the triple pattern with a fourth model instance for high-stakes decisions. Scaling guidance:

| N | Use when |
|---|----------|
| 2 (dual) | Low-blast-radius chore/docs PRs; one auditor per OS |
| 3 (triple) | Standard: cross-provider structural validation (original pattern) |
| 4 (quad) | High-stakes architectural decisions; cross-org model diversity |
| 5+ | Reserved for security-critical decisions with mandatory human sign-off |

The operator (human-in-the-loop) remains the physical data bus in all variants. No direct inter-auditor communication is assumed.

## Consequences

- **Positive:** Regression risk reduced; auditor divergence signals prompt ambiguity; convergence signals green for execution.
- **Negative:** Increased toil on the human operator as synchronisation bus between isolated instances.

## Related Decisions

- [ADR-0046](ADR-0046-operator-intent-and-blameless-collaboration.md) — non-negotiable guardrails (context)
- [ADR-0061](ADR-0061-u-axis-issue-suborder-and-cross-milestone-gate.md) — U-axis sequencing
- `AGENTS.md` — auditor vs executor policy

## References

- Issue #656 — wave that originated this pattern
- PR #658 — wave merged with the pattern active
- PR #648 — SoD architecture that motivated external audit
- Issue #659 — origin of this ADR
