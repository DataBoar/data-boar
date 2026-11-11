# Plan: Windows endpoint agent (GPO / MSI / Intune) and a measured SMB desktop-scan recipe

**Status:** Pending (Phase 0 recipe drafted without figures; agent design not started)
**Date:** 2026-11-10
**Authors:** Fabio Leitao
**Priority:** H1
**GitHub:** [#2207](https://github.com/DataBoar/data-boar/issues/2207)
**Depends on:** [PLAN_MULTI_INSTANCE_REPORT_HUB.md](PLAN_MULTI_INSTANCE_REPORT_HUB.md) (the agent reports to a hub)
**Tier (proposed, pending operator ratification):** Enterprise (fleet-style deployment and central consolidation); not claimed until ratified

<!-- plans-hub-summary: Reach thousands of Windows desktops: Phase 0 documents a measured SMB scan recipe (one instance per VLAN, pilot of 20-50 machines, no figures until measured); Phase 1 designs a signed, GPO/MSI/Intune-distributed endpoint agent that sends metadata-only findings to a hub. -->
<!-- plans-hub-related: PLAN_MULTI_INSTANCE_REPORT_HUB.md, PLAN_CONNECTOR_TIER_GATING.md, PLAN_NATIVE_PACKAGES.md -->

## Context

An enterprise prospect with a large Windows desktop estate asked for endpoint scanning with the
collector distributed by Group Policy. Today Data Boar reaches desktops only through shares (SMB
connector with user, password and domain). No endpoint agent exists. A search of the issues, code
and plans on 2026-11-10 for agent / GPO / Group Policy / endpoint / desktop found nothing.

## Hypotheses about the SMB path (NOT measured)

These are hypotheses to be confirmed or refuted by the pilot, never stated as facts:

- needs an account with administrative access on each machine;
- does not reach machines that are powered off or off the network;
- bulk reads may trigger endpoint-protection alerts;
- scale and wall-clock time are unknown.

## Phases

| Phase | Deliverable | Status |
| ----- | ----------- | ------ |
| 0 | Recipe "scan Windows desktops over SMB, one instance per VLAN" (runbook: [WINDOWS_DESKTOP_SMB_SCAN_RECIPE.md](../ops/WINDOWS_DESKTOP_SMB_SCAN_RECIPE.md), [pt-BR](../ops/WINDOWS_DESKTOP_SMB_SCAN_RECIPE.pt_BR.md)) with a **measurement template and no figures** | 🔄 Drafted; pilot of 20-50 machines pending |
| 0b | Fill the template with real pilot measurements (time, network load, failures by cause, protection-software alerts) | ⬜ Pending (no pilot environment yet) |
| 1 | **PLAN approval before any code** (decisions below). This issue may be split only if the operator orders it | ⬜ Pending |
| 2 | Agent build: light Windows collector; GPO (ADMX) or registry configuration; runs the existing detection locally; sends **metadata-only findings** to the hub; offline queue with retry; enrolment token and `node_id`; no remote-admin dependency; low CPU/IO priority, run window, exclusions, clean uninstall; signed binary | ⬜ Pending (blocked on Phase 1 and on the hub ingestion path) |

## Decisions the Phase 1 plan must settle

- Packaging: frozen executable vs. managed environment; Rust wheels / `boar_fast_filter` on Windows.
- Hardware floor of the target desktops.
- Tier framing (operator decision; see [PLAN_CONNECTOR_TIER_GATING.md](PLAN_CONNECTOR_TIER_GATING.md)).
- Transport and authentication to the hub (token per node, TLS), shared with the hub plan.

## Honesty guardrails

No capacity, duration or "supports N machines" statement may be published until Phase 0b
produces measurements. The recipe documents what to measure, not what to expect.

## Relationship to other plans

- [PLAN_MULTI_INSTANCE_REPORT_HUB.md](PLAN_MULTI_INSTANCE_REPORT_HUB.md): receiving side of the agent.
- [PLAN_NATIVE_PACKAGES.md](PLAN_NATIVE_PACKAGES.md): MSI / winget packaging work that the agent may reuse.
- [PLAN_CONNECTOR_TIER_GATING.md](PLAN_CONNECTOR_TIER_GATING.md): tier boundary.

Synced with [PLANS_TODO.md](PLANS_TODO.md).
