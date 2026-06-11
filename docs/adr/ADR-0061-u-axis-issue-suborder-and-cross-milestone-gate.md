# ADR 0061 — U-axis issue sub-order and cross-milestone gate

- **Date (UTC):** 2026-05-22
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Status

Accepted

### Status history

- 2026-05-22 — Accepted
- 2026-06-11 — Amended: retrofit to ADR-0045 UMADR format (metadata list, EN sections, Status history, Rationale, Alternatives Considered, Related Decisions) — GitHub #674

## Context

ADR-0055 establishes that prioritisation axes are orthogonal and must not be collapsed. It does **not** define how an agent should use the U axis to order issues when multiple issues share the same P label and milestone. Without this ADR, an agent could pick any P2/v1.7.5-beta issue in any order.

The rule `.cursor/rules/execution-priority-and-pr-batching.mdc` implements the behaviour; this ADR is the formal contract that gives it binding status in the repository.

## Decision

### U-axis sub-ordering within the same P+milestone

| U      | Description                               | Agent behaviour                               |
|--------|-------------------------------------------|-----------------------------------------------|
| U0     | security/safety now                       | Blocks the entire session until resolved      |
| U1     | high-value / chain blocker / ext deadline | Executes before U2/U3/no-U                    |
| U2     | valuable, no hard external deadline       | Executes before U3/no-U                       |
| U3     | explicitly deferred within milestone      | Executes after U0/U1/U2                       |
| no-U   | U tag absent from issue body              | Treated as U3 — lowest sub-priority in milestone |

### Cross-milestone gate

- Issues in a later milestone (e.g. v1.7.5-beta) **must not start** before the earlier milestone (e.g. v1.7.4) is fully closed.
- The annotation `**NÃO INICIAR ANTES DE #N FECHADA**` in an issue body is a **hard constraint** — not advisory.
- Cross-milestone reprioritisation requires **explicit operator instruction** at the start of the session.

## Rationale

Agents operating on a large backlog without a deterministic sub-ordering rule introduce variance: different sessions pick different P2 issues first, making progress non-reproducible. The U axis provides a single, auditable ordering key within a P+milestone slice without collapsing it with the H (horizon), A (band), or G (gravity) axes. Chain-blocker issues (U1) stall the batch if skipped; hard-safety issues (U0) warrant session-wide suspension.

The cross-milestone gate prevents agents from starting work on features that depend on a completed, tested baseline. It mirrors the reasoning behind feature-branch sequencing in CI — merging an untested milestone's issues into the next one's scope creates debt that is hard to isolate.

## Alternatives Considered

| Alternative | Why not |
|-------------|---------|
| FIFO (creation date) | Does not capture urgency or chain dependencies |
| Random within P+milestone | Non-reproducible; agent picks cheapest or most-familiar item |
| Single global priority number | Collapses orthogonal axes — explicitly rejected by ADR-0055 |
| Operator-specified order each session | Too much toil; defeats the purpose of autonomous U-axis ordering |

## Consequences

- **Positive:** Deterministic sequencing within P+milestone; agents cannot improvise order.
- **Negative:** New issues without a U tag are automatically treated as U3 — creators must be explicit when U1/U2 is intended.
- **Watch:** Update U tag when external deadline pressure changes (e.g. partner confirms deadline).

## Related Decisions

- [ADR-0055](ADR-0055-orthogonal-priority-axes-anti-collision-contract.md) — anti-collision contract (orthogonal axes)
- [ADR-0062](ADR-0062-agent-containment-triple-audit-offband-pingpong.md) — agent containment (context for sequencing governance)

## References

- `.cursor/rules/execution-priority-and-pr-batching.mdc` — rule implementation
- Issue #655 — origin of this ADR
- Issue #654 — `docs/ops/ISSUE_QUEUE_SEQUENCING_MAP.md` (Mermaid queue map)
