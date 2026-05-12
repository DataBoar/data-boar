# ADR 0017 — Quasi-identification risk/confidence contract and LGPD guardrails

- **Status:** Accepted
- **Date (UTC):** 2026-04-07
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Context

The project now formalizes quasi-identification analysis for combinations such as `IP + geolocation + breadcrumbs` in logs/proxy traces. We need durable decisions that prevent ad-hoc behavior drift and future cognitive overload.

## Decision

1. Use a **dual output model**:
   - `risk_score` / `risk_label` for deanonymization potential.
   - `confidence_score` / `confidence_label` for inference reliability.
2. Keep **LGPD-safe defaults**:
   - local-first inference;
   - online enrichment disabled by default;
   - redaction enabled for report evidence;
   - bounded enrichment lookups if opt-in is enabled.
3. Define a stable **record contract**:
   - schema and example files under `docs/ops/schemas/`.
   - regression test to keep labels/scores coherent.
4. Keep rollout **token-aware**:
   - one daily slice at a time (`score`, `report`, `guardrail`, `fixture`, `docs`).

## Consequences

- Pros:
  - clearer decision boundaries across tiers and sprints;
  - lower regression risk for future models/agents;
  - easier testability and auditability.
- Cons:
  - adds initial documentation/test maintenance overhead;
  - optional enrichment remains constrained until explicit product/legal decision.

## References

- `docs/plans/PLAN_QUASI_IDENTIFICATION_COMPOSITE_RISK.md`
- `docs/ops/QUASI_IDENTIFICATION_OPERATOR_PLAYBOOK.md`
- `docs/ops/schemas/quasi-identification-risk-record.schema.json`
- `docs/ops/schemas/quasi-identification-risk-record.example.json`
