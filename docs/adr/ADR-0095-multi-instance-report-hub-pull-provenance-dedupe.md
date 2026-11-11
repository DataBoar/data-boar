# ADR 0095 — Multi-instance report hub: pull model, node provenance and a stable dedupe key

- **Date (UTC):** 2026-11-11
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Status

Proposed

### Status history

- 2026-11-11 — Proposed — records the design of the multi-instance report hub for [#2208](https://github.com/DataBoar/data-boar/issues/2208).

## Context

Customers with several instances (per VLAN, per site, or one agent per endpoint) get one isolated report
per instance. The unified findings API only **pulls** (`/findings`, `/findings/{session_id}`, `/list`,
`/about/json`), the unified CSV has no node or host column, and the per-node row `id` is a local counter
(on two synthetic demo instances **all 26 ids overlapped**). Concatenating exports silently loses where
each row came from, and a `session_id` is not guaranteed to be unique across nodes. Findings are metadata
only, but paths and host names are already sensitive.

New features start at Enterprise, and the tier map is fail-closed (#854), so the hub needs an explicit
entry before it can run outside `Tier.OPEN`.

## Decision

1. **Pull model.** A hub instance reads each configured node through its existing API with one key per
   node (from an environment variable) over TLS. `https` is required except for loopback; redirects are
   never followed; URLs, tokens and paths are never logged. Mode 1 (on-premises) is what this ADR
   implements. A hosted mode in which nodes **push** is design only (see the plan) and depends on #838.
2. **Provenance on every row.** `node_id` (an operator-chosen label), `node_version`, `node_session_id` and
   `fetched_at_utc`. Local row ids and session ids never decide identity.
3. **Stable dedupe key.** `sha256(node_id, session_id, source_type, target_name, path, file_name,
   data_type, schema_name, table_name, column_name, pattern_detected, norm_tag)`, truncated. Content that is
   identical inside one node and session collapses; the same content on two nodes does not.
4. **Only completed sessions.** The hub consolidates the newest **completed** session of a node. If the
   newest session is still running or failed it falls back to the newest completed one and says so; a node
   with no completed session is reported, not merged. A node that is down is reported while the rest is
   consolidated (exit 2); nothing consolidated exits 1 and writes nothing.
5. **Report.** One Excel workbook with a Summary (per node status), a Findings sheet with a per-node filter
   and a Notes sheet that states the evidence posture: technical evidence, not a legal conclusion.
6. **Tier.** `multi_instance_hub` is **Enterprise** in `FEATURE_TIER_MAP` (default for new features); lowering
   it happens only after validation, by operator decision. The CLI flag is `--hub-report OUTPUT.xlsx`.

## Consequences

- **Positive:** one consolidated, attributable report across instances; no change to the nodes' API; the
  same data model can later receive pushed findings.
- **Negative:** the hub needs network reach to every node and one key per node; persistence across runs
  (history, trends) is not part of this decision.
- **Watch:** paths and host names are sensitive even as metadata; the output file is created with mode
  `0600` and must be stored accordingly. A hosted mode needs contract, LGPD and retention groundwork
  before it exists.

## References

- [PLAN_MULTI_INSTANCE_REPORT_HUB.md](../plans/PLAN_MULTI_INSTANCE_REPORT_HUB.md)
- [PLAN_CONNECTOR_TIER_GATING.md](../plans/PLAN_CONNECTOR_TIER_GATING.md) (fail-closed tier map, #854)
- [ADR-0055](ADR-0055-orthogonal-priority-axes-anti-collision-contract.md)
