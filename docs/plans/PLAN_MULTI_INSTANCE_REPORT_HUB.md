# Plan: Multi-instance report hub (consolidate findings from several nodes into one report)

**Status:** In progress (Phases 0 to 2 delivered; the hosted push mode is design only)
**Date:** 2026-11-10
**Authors:** Fabio Leitao
**Priority:** H1
**GitHub:** [#2208](https://github.com/DataBoar/data-boar/issues/2208)
**Depends on:** none for Phase 0; [PLAN_CONNECTOR_TIER_GATING.md](PLAN_CONNECTOR_TIER_GATING.md) for tier framing
**Tier (default for new features):** Enterprise (also aligns with the "multi-entity" item in [ENT_CAPABILITY_ROADMAP.md](ENT_CAPABILITY_ROADMAP.md) and the findings-sink family); lowered only after validation, by operator decision

<!-- plans-hub-summary: Consolidated view across several Data Boar instances (per VLAN, site or endpoint): a pull-based hub with provenance, dedupe and a unified Excel report (Enterprise), plus the deployment modes written down as design: on-premises pull, and a hosted push mode that depends on #838. -->
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
| 1 | Hub (`--hub-report`, [ADR-0095](../adr/ADR-0095-multi-instance-report-hub-pull-provenance-dedupe.md)): pulls the newest **completed** session of each node (`/list`, `/findings/{session_id}`, `/about/json`) with provenance (`node_id`, version, session, fetch time) and a stable dedupe key; tests for `id` and `session_id` collision, a node that is down and an incomplete session. One-shot command: schedule it with cron or a systemd timer | ✅ Done |
| 2 | Unified Excel report (Summary, Findings with a per-node filter, Notes), same evidence language (evidence, not a legal conclusion); output created with mode `0600` | ✅ Done |
| 3 | Hosted mode where nodes push (see *Deployment modes*): **design only**, depends on #838 and on contract and LGPD groundwork; no commitment | ⬜ Design (not planned for delivery) |

## Deployment modes (DESIGN, not available as a product)

This section records how the hub could be deployed. The **on-premises pull mode is what Phases 1 and 2
of this plan implement**. The **hosted mode is a design only**: nothing here is a commitment, a delivery
date or a price, and it is not available as a product.

| | Mode 1: on-premises, the hub pulls | Mode 2: hosted, the nodes push (design only) |
| - | ---------------------------------- | -------------------------------------------- |
| Where the hub runs | Inside the customer's own network | Outside the customer's network |
| Who opens the connection | The hub reads each node's existing API (`/list`, `/findings/{session_id}`, `/about/json`) | Each node sends its findings to the hub |
| Network requirement | The hub reaches every node; nothing leaves the customer's network | **Outbound only** from the customer; no inbound port opened |
| Authentication | One key per node, from an environment variable, over TLS | One enrolment token per node, over TLS |
| Depends on | The pull API that exists today | The push capability of #838 (post-scan webhook with delta) plus an authenticated ingestion endpoint on the hub |
| Same in both | Provenance (`node_id`, version, session), the stable `dedupe_key` and the unified report | the same |

### Why pull does not fit the hosted mode

A hosted hub that pulls would have to reach **into** every customer network. That means an inbound port,
a firewall rule or a VPN per customer, which most security teams refuse and which widens the attack
surface. A hosted hub therefore has to receive: the customer's nodes initiate the connection and only
outbound traffic is required.

### Paths and host names are sensitive even as metadata

The hub carries metadata only, never sample content. Even so, file paths, table and column names and
host names reveal how an organization is structured and can identify people and systems. They have to be
treated as confidential, and, where they identify individuals, as personal data. Any hosted use therefore
needs, before it exists:

- a **contract** that fixes the roles (controller and processor), purposes, retention, sub-processors and
  the location of processing;
- the **LGPD/GDPR** basics: legal basis, minimization, retention and deletion, access control and an audit
  trail of what was received;
- the **evidence posture** of the product: the report is technical evidence to support a review, never a
  legal conclusion, and no claim of guaranteed compliance is made;
- encryption in transit and at rest, and isolation between customers.

Open design questions: whether paths can be pseudonymized before they leave the customer; per-customer
isolation of stored data; retention and deletion; enrolment and revocation of a node; data residency.

Out of scope here: pricing, packaging, delivery dates and any named customer or partner.

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
