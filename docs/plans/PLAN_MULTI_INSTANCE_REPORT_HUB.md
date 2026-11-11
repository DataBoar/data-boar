# Plan: Multi-instance report hub (consolidate findings from several nodes into one report)

**Status:** Pending (Phase 0 proof-of-concept script delivered; hub mode not started)
**Date:** 2026-11-10
**Authors:** Fabio Leitao
**Priority:** H1
**GitHub:** [#2208](https://github.com/DataBoar/data-boar/issues/2208)
**Depends on:** none for Phase 0; [PLAN_CONNECTOR_TIER_GATING.md](PLAN_CONNECTOR_TIER_GATING.md) for tier framing
**Tier (default for new features):** Enterprise (also aligns with the "multi-entity" item in [ENT_CAPABILITY_ROADMAP.md](ENT_CAPABILITY_ROADMAP.md) and the findings-sink family); lowered only after validation, by operator decision

<!-- plans-hub-summary: Consolidated view across several Data Boar instances (per VLAN, site or endpoint): Phase 0 is a documented pull-and-merge CSV script that adds a node_id the API does not emit; Phase 1 is a hub mode with provenance, dedupe and a unified Excel report. -->
<!-- plans-hub-related: ENT_CAPABILITY_ROADMAP.md, PLAN_ENDPOINT_AGENT.md, PLAN_M365_GRAPH_CONNECTORS.md, PLAN_CONNECTOR_TIER_GATING.md -->

## Context

Customers with several instances (per VLAN, per site, or one agent per endpoint) have no
consolidated view: each instance produces its own isolated report.

## Verified state (2026-11-10, `origin/main`)

- `api/routes.py` exposes `GET /findings`, `/findings/csv`, `/findings/{session_id}`,
  `/findings/{session_id}/csv` and `/reports/{session_id}`. A central node can **pull** results
  from the others. The API is pull-only today (push for SARIF/SIEM/webhook is open, #838).
- **The unified CSV does not identify the node.** Its columns are `id`, `session_id`,
  `source_type`, `target_name`, `path`, `file_name`, `data_type`, `schema_name`, `table_name`,
  `column_name`, `sensitivity_level`, `pattern_detected`, `norm_tag`, `ml_confidence`,
  `source_mtime_ns`, `source_size`, `content_fingerprint`, `created_at`. There is no host or node
  column. Measured on two isolated synthetic `--demo` instances (2026-11-11): the per-node row
  `id` overlapped on **26 of 26** rows (it is a local counter), while `session_id` differed
  between the two nodes in that run. Cross-node uniqueness of `session_id` is not guaranteed by
  contract, so the hub must not rely on it alone. Merging CSVs without adding provenance
  silently loses where each row came from.
- **Finding for the demo runbook:** two `--demo` instances on one host share the fixed workspace
  `<tmp>/data_boar_demo`; the second start broke the first (`unable to open database file`,
  HTTP 500 on `/findings/csv`). Isolate each instance with its own `TMPDIR`.
- No issue or plan covered multi-instance consolidation; #1518 is research on distributed workers.

## Phases

| Phase | Deliverable | Status |
| ----- | ----------- | ------ |
| 0 | Documented PoC: [`scripts/multi_instance_findings_poc.py`](../../scripts/multi_instance_findings_poc.py) pulls `/findings/csv` from N nodes and adds `node_id` + `fetched_at_utc`; runbook [MULTI_INSTANCE_FINDINGS_CSV_POC.md](../ops/MULTI_INSTANCE_FINDINGS_CSV_POC.md) ([pt-BR](../ops/MULTI_INSTANCE_FINDINGS_CSV_POC.pt_BR.md)); tests with simulated nodes. **Not** a centralization feature | ✅ Done (this slice) |
| 0b | Evidence with two real instances running the synthetic `--demo` corpus (each with its own `TMPDIR`) | ✅ Done 2026-11-11: 2 nodes x 26 rows = 52 merged rows; exit 0 |
| 1 | Hub mode: scheduled pull of `/findings/{session_id}` and `/reports/{session_id}` from N nodes; data model storing `node_id`, `session_id`, fetch time and node version; stable dedupe key; tests for `session_id` collision, node down, incomplete session | ⬜ Pending |
| 2 | Unified Excel report with a per-node filter, same evidence language (evidence, not a legal conclusion) | ⬜ Pending |

## Security requirements (Phase 1)

Token per node, TLS, host allowlist. Findings are metadata-only, but paths and hostnames are
already sensitive: nothing in logs, no public exposure, no node URL written into outputs.
Phase 0 enforces the minimum: tokens only from environment variables, `https` required except
loopback, size and time limits, and the merged CSV is never written inside the repository tree.

## Out of scope

Narrative per audience (SecOps, CISO, DPO) belongs to the GRC composer (#1949), which consumes
the consolidated set.

## Relationship to other plans

- [ENT_CAPABILITY_ROADMAP.md](ENT_CAPABILITY_ROADMAP.md): "multi-entity / subsidiaries" capability.
- [PLAN_ENDPOINT_AGENT.md](PLAN_ENDPOINT_AGENT.md): agents are producers for this hub.
- [PLAN_M365_GRAPH_CONNECTORS.md](PLAN_M365_GRAPH_CONNECTORS.md): another multi-instance producer scenario.
- [PLAN_CONNECTOR_TIER_GATING.md](PLAN_CONNECTOR_TIER_GATING.md): tier boundary decision.

Synced with [PLANS_TODO.md](PLANS_TODO.md).
