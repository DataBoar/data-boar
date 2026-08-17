# Cross-surface observability — dashBOARd RUM + OTel backend (gates)

<!-- plans-hub-summary: Active gates for privacy-first Faro/RUM on dashBOARd as complement to shipped OTel emit; default OFF; operator/BYO destinations; no browser tokens; phased signal contract through Crow provenance. Docs/backlog only — no runtime in this plan PR. -->
<!-- plans-hub-related: completed/PLAN_DATABOAR_OTEL_INSTRUMENTATION.md, completed/PLAN_OTEL_CLI_COVERAGE.md, PLAN_LAB_OP_OBSERVABILITY_STACK.md, PLAN_MAESTRO_OTEL_PREFLIGHT.md -->

**Status:** Active (gates / proposals — **no** RUM runtime, **no** ADR in this slice)
**Date:** 2026-08-16
**Authors:** Fabio Leitao
**Priority:** H2 / P2
**Pilot issue:** [#1601](https://github.com/DataBoar/data-boar/issues/1601)

## Purpose

Define **checkable gates** so **browser RUM** (Grafana Faro or equivalent privacy-first Web SDK) on **dashBOARd** and, later, other **bestiais** GUIs **complements** the **already shipped** OpenTelemetry **backend emit** — without turning the browser into a secret store or a silent exfil path.

This plan is **docs/backlog only**. It does **not** implement loaders, collectors, or ADRs. Implementation lands in **thin follow-up PRs** after gate acceptance.

## Already delivered (do not re-plan)

| Surface | Issue / PR | Plan |
| ------- | ---------- | ---- |
| Product OTel emit (traces + metrics) | [#1500](https://github.com/DataBoar/data-boar/issues/1500) / **#1503** | [PLAN_DATABOAR_OTEL_INSTRUMENTATION.md](completed/PLAN_DATABOAR_OTEL_INSTRUMENTATION.md) |
| Logs bridge (`LoggerProvider` → OTLP) | [#1529](https://github.com/DataBoar/data-boar/issues/1529) / **#1544** | same completed plan |
| CLI / oneshot coverage | [#1535](https://github.com/DataBoar/data-boar/issues/1535) / **#1547** | [PLAN_OTEL_CLI_COVERAGE.md](completed/PLAN_OTEL_CLI_COVERAGE.md) |
| Lab / operator **receiving** stack | phases A+C live, F partial | [PLAN_LAB_OP_OBSERVABILITY_STACK.md](PLAN_LAB_OP_OBSERVABILITY_STACK.md) |
| Maestro OTel preflight (product truth) | [#1540](https://github.com/DataBoar/data-boar/issues/1540) | [PLAN_MAESTRO_OTEL_PREFLIGHT.md](PLAN_MAESTRO_OTEL_PREFLIGHT.md) |

**Mental model:** backend OTel = **source of truth for API/CLI/worker RED + logs**. Browser RUM = **optional UX/perf/error signals** that may **correlate** into the same operator backend when the operator opts in.

## Related coordination (do not duplicate)

| Issue | Role vs this plan |
| ----- | ----------------- |
| [#1458](https://github.com/DataBoar/data-boar/issues/1458) | Epic: Observability + Memory (Sensor, MemPalace, OTel GenAI) — **parent coordination** |
| [#1457](https://github.com/DataBoar/data-boar/issues/1457) | Docs north-star: GenAI/MCP OTel + ADR Sensor — **architecture narrative**; this plan covers **product GUI RUM**, not agent forensics |
| [#1599](https://github.com/DataBoar/data-boar/issues/1599) | Cloudflare GraphQL → OTLP/Grafana — **edge analytics export**; **orthogonal**; do **not** fold into the RUM pilot. Runbook: [CLOUDFLARE_GRAPHQL_OTLP_EXPORT.md](../ops/CLOUDFLARE_GRAPHQL_OTLP_EXPORT.md). |

## Non-goals (this plan file)

- Shipping Faro/RUM JS in dashBOARd or marketing site from this PR
- Creating or Accepting an ADR here (propose later only if a durable product law is needed)
- Hardcoding operator/customer collector hostnames, tokens, or LAN topology in tracked defaults
- Copying client names, vault material, or private lab inventory into public plans/issues
- Replacing GenAI/MCP / ADR Sensor work under #1457/#1455

## Hard product gates (must hold in any RUM slice)

| Gate | Requirement |
| ---- | ----------- |
| **Default OFF** | No browser telemetry until explicit operator/customer enablement (config + documented risk). |
| **Destination control** | Emit only to destinations the operator/customer chooses: **local** collector, **BYO** Collector/Grafana, or **air-gapped** path. No vendor SaaS default. |
| **No browser tokens** | Never embed API keys, Grafana Cloud tokens, or OTLP auth secrets in HTML/JS served to the browser. Auth stays on the **server** or **operator-owned** collector edge. |
| **Origin allowlist** | Collector/ingest accepts only allowlisted `Origin` / referer policy as configured by the operator. |
| **Redaction** | Strip or hash **PII**, **secrets**, **query strings**, and **payload bodies** before leave-browser or at the first trusted hop. Prefer fail-closed drop over leak. |
| **Bounded labels** | Cardinality-safe attributes only (enums, coarse routes, status classes). No free-text URLs, user ids, or finding contents as high-cardinality labels. |
| **Auditable opt-out** | Disable path must be documented and leave an **audit-visible** trail when telemetry was previously on (config change / status signal — not silent). |
| **Optional correlation** | Browser → API correlation only via **W3C trace context** and/or an **opaque** request id — never by stuffing secrets or personal identifiers into headers. |

## Phases (gates → implementation later)

| Phase | Deliverable | Acceptance (gate) |
| ----- | ----------- | ----------------- |
| **0 — Signal contract** | Document allowed browser event classes (errors, vitals, nav) vs forbidden (form fields, scan targets, auth cookies) | Written contract in this plan § *Signal contract*; reviewed in pilot issue |
| **1 — GUI pilot** | Privacy-first RUM **pilot** for **dashBOARd** only (default OFF) | Child P2 issue AC; no tokens in browser; redaction tests or checklist |
| **2 — Correlation** | Optional link browser spans/events ↔ backend OTel traces | Prove with synthetic traffic; document header policy |
| **3 — Dashboards / receiving** | Operator playbook: wire RUM into existing lab/customer receive stack ([PLAN_LAB_OP_OBSERVABILITY_STACK.md](PLAN_LAB_OP_OBSERVABILITY_STACK.md)) | Doc-only runbook pointers; no private IPs in public tree |
| **4 — Sidecar starter contract** | Minimal signal schema for other bestiais GUIs (same gates) | Shared checklist; no code required in this phase |
| **5 — Crow (future)** | Crow may **consume** correlated signals only with **explicit provenance** and **correlation grade** fields | Crow issue later; refuse silent merge of RUM into findings without grade |

### Signal contract (Phase 0 draft)

**Allowed (when enabled):** coarse route/template ids; HTTP status class; performance vitals aggregates; sanitized exception **type** (no message dump with paths); session/opt-in opaque id.

**Forbidden:** passwords, JWT/cookies, vault paths, scan target URLs/hosts, finding snippets, query/hash with identifiers, unrestricted `document.URL`, raw POST bodies.

## Sequencing vs other observability work

1. Keep **backend OTel** healthy (already on `main`).
2. Accept **this plan** — dashBOARd RUM pilot child issue is **[#1601](https://github.com/DataBoar/data-boar/issues/1601)** (P2).
3. Implement Phase 1 in a **dedicated code PR** (not this docs PR).
4. Leave **#1599** (Cloudflare → OTLP) on its own track.
5. Keep **#1457** for GenAI/MCP + Sensor docs — cross-link, do not subsume.

## Acceptance (docs slice)

- [x] This active plan file (gates + phases)
- [x] Entry in `PLANS_TODO.md` + `plans_hub_sync.py --write` (+ `plans-stats.py --write` if dashboard rows change)
- [x] Public **P2** child issue for dashBOARd RUM privacy-first pilot — [#1601](https://github.com/DataBoar/data-boar/issues/1601), linked to #1457 / #1458, **not** duplicating #1599
- [x] No RUM/runtime code and no new ADR in the docs PR

## Privacy reminder

Public plans and issues state **gates and categories only**. Operator credentials, customer names, and vault details stay in **gitignored** private notes or customer-owned systems.
