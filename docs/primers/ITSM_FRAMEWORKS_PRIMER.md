# Primer: ITSM frameworks (ITIL 4, ISO/IEC 20000)

<!-- plans-hub-summary: ITIL 4 SVS and ISO/IEC 20000 — selected practices vs Data Boar evidence, not a service desk -->

**Status:** Active
**Date:** 2026-08-29
**Authors:** Fabio Leitao
**Priority:** H2
**Depends on:** ADR-0004, ADR-0035, ADR-0050, ADR-0058, ADR-0070
**GitHub:** [#630](https://github.com/DataBoar/data-boar/issues/630)

**Português (Brasil):** [ITSM_FRAMEWORKS_PRIMER.pt_BR.md](ITSM_FRAMEWORKS_PRIMER.pt_BR.md)

**Audience:** Compliance engineers, IT operations, and governance teams who speak **service-management** language and need to place discovery scans in that vocabulary.

**Tone:** Technical. No mascot. No reproduction of AXELOS or ISO process tables — buy [ITIL 4](https://www.axelos.com/certifications/itil-service-management) and [ISO/IEC 20000](https://www.iso.org/standard/70636.html) (Brazil: ABNT NBR ISO/IEC 20000) for official text.

This primer is the **execution-layer companion** to GitHub **#629** (IT governance / EDM). Governance directs; ITSM delivers and improves.

---

## Service management as the link between strategy and delivery

Strategy sets intent (value, risk, accountability). **IT service management** turns that intent into repeatable ways of planning, delivering, supporting, and improving services. Data Boar sits **inside delivery and improvement**: it produces **evidence of where sensitive data appeared** in configured targets. It does not run the service desk, own SLAs, or certify an SMS.

Related ops/SRE language: [OBSERVABILITY_SRE.md](../OBSERVABILITY_SRE.md). Methodology: [COMPLIANCE_METHODOLOGY.md](../COMPLIANCE_METHODOLOGY.md).

---

## ITIL 4 — Service Value System (SVS)

ITIL 4 describes a **Service Value System**: how organisational components work together so services create value (guiding principles, governance, service value chain, practices, continual improvement). Public overview: [Axelos — ITIL](https://www.axelos.com/certifications/itil-service-management).

Each Data Boar **session** is an **input** to that system (findings, manifest, report). It is **not** the SVS itself.

Tracked SVG (inspired diagram, not an official ITIL figure): [databoar_svs_inspirado.svg](../assets/diagrams/databoar_svs_inspirado.svg).

---

## ISO/IEC 20000 — service management system

ISO/IEC 20000 is a **management-system** standard for IT services (requirements for an SMS). Catalogue: [ISO/IEC 20000](https://www.iso.org/standard/70636.html). Data Boar can **support evidence** (repeatable scans, bounded sampling documented in a manifest) that teams attach to **their** SMS; it does **not** implement clause-by-clause 20000 controls.

---

## Four ITSM dimensions (product crossing)

ITIL 4 talks about four dimensions of service management. In **this product’s wording** (not a normative table):

| Dimension (plain language) | How a discovery scan crosses it |
| -------------------------- | ------------------------------- |
| **People and organisation** | Who may start scans, who reads reports (API key, optional RBAC) — still your IAM/ITSM |
| **Information and technology** | Targets, connectors, sampling, detector stack |
| **Partners and suppliers** | SaaS/CRM/API connectors; you remain accountable for vendor DPAs |
| **Value streams and processes** | Scan as a step in change, incident, or compliance cadences — you design the stream |

---

## Selected ITIL practices — product contribution (not a practice catalogue)

| Practice (common ITIL label) | How Data Boar can contribute |
| ---------------------------- | ---------------------------- |
| Incident management | PII in production stores is a **data incident surface**. A scan can show exposure **before** a breach ticket exists. |
| Problem management | Recurring PII in logs or non-prod copies is often a **systemic** issue. Session-over-session history shows patterns that one-off cleanups missed. |
| Change control | Pre/post-deploy scans can flag **new** exposure introduced by a change. Optional quality gate in **your** CI/CD — the engine does not own the pipeline. |
| Capacity and performance | Configurable sampling, per-target timeouts, character budgets. The **scan manifest** records what was covered and how deep — honesty about limits. |
| Service continuity | Manifest + metadata findings can join a **post-incident diligence pack**: what existed, where, when it was last verified — not a DR orchestrator. |

---

## What this product is not

- Not a **service desk** or ticket system.
- Not an **ITSM platform** (no CMDB as source of truth, no SLA engine).
- Not an ISO/IEC 20000 or ITIL **certification**.

---

## Related product docs

- [COMPLIANCE_METHODOLOGY.md](../COMPLIANCE_METHODOLOGY.md)
- [OBSERVABILITY_SRE.md](../OBSERVABILITY_SRE.md)
- [ITSM_GOVERNANCE_ALIGNMENT.md](../ITSM_GOVERNANCE_ALIGNMENT.md)
- [GRC_EXECUTIVE_REPORT_SCHEMA.md](../GRC_EXECUTIVE_REPORT_SCHEMA.md)
- Governance companion: GitHub [#629](https://github.com/DataBoar/data-boar/issues/629)
