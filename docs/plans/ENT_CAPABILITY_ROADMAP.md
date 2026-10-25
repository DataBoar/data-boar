# Enterprise (ENT) subscription capability roadmap

<!-- plans-hub-summary: Canonical ENT subscription capability backlog (role reports, multi-entity, maturity, audit evidence, PSI/DGA, ITSM/IAM); doc-only until per-capability ADR -->

**Português (Brasil):** [ENT_CAPABILITY_ROADMAP.pt_BR.md](ENT_CAPABILITY_ROADMAP.pt_BR.md)

**Status:** Roadmap (doc only — no product implementation without an operator-approved ADR)
**Date:** 2026-08-17
**Priority:** H1 / U1 (commercialization framework)
**Issue:** [#643](https://github.com/DataBoar/data-boar/issues/643)

**Related:** [ADR-0035](../adr/ADR-0035-readme-stakeholder-pitch-vs-deck-vocabulary.md) · [PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md](PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md) · [SPRINTS_AND_MILESTONES.md](SPRINTS_AND_MILESTONES.md) §4.1 / **M-ACCESS** · [ACTIONABLE_GOVERNANCE_AND_TRUST.md](../ops/inspirations/ACTIONABLE_GOVERNANCE_AND_TRUST.md) · hub entry [PLAN_ENT_CAPABILITY_ROADMAP.md](PLAN_ENT_CAPABILITY_ROADMAP.md)

---

## 1. Purpose

This file is the **canonical** backlog for **Enterprise (ENT) subscription** capabilities: product features that turn scan utility into **verified organizational process** for boards, DPOs, auditors, and security committees.

It does **not** replace:

| Doc | Owns |
| --- | ---- |
| [PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md](PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md) | Tier matrix, JWT `dbtier` narrative, what ships per Community/Trial/Pro/Partner/Enterprise |
| [SPRINTS_AND_MILESTONES.md](SPRINTS_AND_MILESTONES.md) §4.1 | Commercial entitlement, activation, dashBOARd/API access, **M-ACCESS** |
| [LICENSING_SPEC.md](../LICENSING_SPEC.md) | Runtime license claims and enforcement phases |

Keep those files as pointers into this roadmap for ENT *capabilities*; keep the feature matrices and SKU/JWT work there.

---

## 2. Open-core vs ENT

| Layer | Delivers | Audience |
| ----- | -------- | -------- |
| **Open-core** | Technical **utility**: scan engine, `norm_tags`, findings, scan manifest, basic GRC report, CLI + API, single-org scans, technical dashBOARd | Operators, engineers, researchers |
| **ENT subscription** | **Organizational process** artefacts and workflows that boards, DPOs, auditors, and security committees need for governance, compliance, and diligence | Regulated orgs with real LGPD / GDPR / DGA / ISO 27001 / external audit obligations |

**Who pays for ENT:** organizations with legal, regulatory, or board-level governance duties — not individual hobbyists.

**Product framing:** open-core makes the technical delivery tangible; ENT makes the **governance and compliance delivery** tangible for people who own risk and attestation.

---

## 3. Boundary — what is *not* ENT (stays open-core)

These remain Community / open-core (subject to the tier matrix in the product-tiers plan):

- Core scan engine
- `norm_tags` + `plugin_schema.yaml`
- Scan manifest (baseline)
- Basic GRC report
- CLI + API
- Single-organization scans
- Technical dashBOARd views

---

## 4. Capability backlog (roadmap only)

Checkboxes track **product intent**, not shipped code. Do not implement an item without an **operator-approved ADR** for that capability (or an explicit sub-issue the operator opens).

### P0 — Unblock sales

- [ ] **Role-based report generation** — Same scan, different views by persona (DPO, CISO, CDO, board). Value object changes with audience. Aligns with COBIT-style Evaluate–Direct–Monitor and ITIL-style service tangibilization for non-technical stakeholders.
- [ ] **Multi-entity / subsidiaries** — One central tenant manages scans across N business units or group companies. Aligns with corporate → IT governance pyramids.

### P1 — Retention and expansion

- [ ] **DMBOK maturity scorer** — Score organizational data-security (and related DMBOK areas) maturity from scan evidence; levels 1–5; trend over time. Related product surface: [PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md](completed/PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md) (questionnaire POC — complementary, not identical). Pitch / CDO narrative: [#639](https://github.com/DataBoar/data-boar/issues/639); DMBOK primer track: [#637](https://github.com/DataBoar/data-boar/issues/637).
- [ ] **Security committee report** — Packaged agenda artefact: executive summary, material incidents/exposures, decisions required for a periodic committee meeting.
- [ ] **Audit-grade evidence chain** — Signed scan manifest, custody chain, integrity hashes suitable for legal and external audit. Differentiates from typical OSS scanners. Complements trust/audit-trail vocabulary in [PLAN_GRC_INSPIRED_ENTERPRISE_TRUST_ACCELERATORS.md](PLAN_GRC_INSPIRED_ENTERPRISE_TRUST_ACCELERATORS.md); does not replace open-core `--export-audit-trail` until gated.

### P2 — New segments / ICP

- [ ] **PSI builder** — Draft information-security policy outline driven by findings (e.g. which data classes appear where → policy coverage checklist). Not legal advice; template aid for customers.
- [ ] **DGA data-sharing assessment** — Pre-share check against EU Data Governance Act (Reg. 2022/868) style outcomes: may share / needs anonymization / must not share.
- [ ] **Anonymization quality validator** — Detect residual PII or re-identifiable combinations in datasets claimed as anonymized (e.g. k-anonymity style failures).

### P3 — Ecosystem integration

- [ ] **ITSM connector** (ServiceNow / Jira) — PII exposure → incident ticket with risk-based priority (ITIL incident management pattern).
- [ ] **IAM recommender** — Suggest RBAC / least-privilege policies from findings (which roles should not see which tables/fields).

---

## 5. Sequencing vs existing enforcement work

ENT capabilities are **not** the same as JWT `dbtier` / `dbfeatures` gates already listed in [PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md](PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md) (Phases 1–5) or the entitlement slices in [SPRINTS_AND_MILESTONES.md](SPRINTS_AND_MILESTONES.md) §4.1.

| Prerequisite | Why |
| ------------ | --- |
| Tiers plan **Phases 1–2** (`dbtier` + `LicenseGuard.check_feature`) | Gate paid ENT packs without soft-fail leaks |
| **M-ACCESS** (documented + smoke-tested identity path) | Do not promise multi-user ENT on a reachable host without auth |
| Open-core plugin / Pro auditability track ([#811](https://github.com/DataBoar/data-boar/issues/811)) | Partner onboarding and Pro least-privilege audit model — cross-ref only; decisions live in that issue/ADR |

Ship open-core trust and access milestones first; promote ENT capabilities only when the commercial and access story is honest.

---

## 6. Implementation gate (hard)

1. **No product code** for items in §4 without an **ADR approved by the operator** for that capability.
2. **Sub-issues** per capability only when the operator asks.
3. **Pricing, contracts, and SKU legal language** stay with counsel / Priority band A (A7) — out of scope for this file beyond pointers to [LICENSING_OPEN_CORE_AND_COMMERCIAL.md](../LICENSING_OPEN_CORE_AND_COMMERCIAL.md).
4. Named partner examples and commercial rates belong only under **gitignored** `docs/private/` — never in this public roadmap.

---

## 7. Related index

| Kind | Link |
| ---- | ---- |
| Tracking issue | [#643](https://github.com/DataBoar/data-boar/issues/643) |
| Pitch / vocabulary ADR | [ADR-0035](../adr/ADR-0035-readme-stakeholder-pitch-vs-deck-vocabulary.md) |
| Tier boundaries | [PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md](PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md) · [ADR-0027](../adr/ADR-0027-commercial-tier-boundaries-licensing-docs-and-future-jwt-claims.md) |
| Access / subscription surfaces | [SPRINTS_AND_MILESTONES.md](SPRINTS_AND_MILESTONES.md) §4.1 · **M-ACCESS** |
| Trust accelerators | [PLAN_GRC_INSPIRED_ENTERPRISE_TRUST_ACCELERATORS.md](PLAN_GRC_INSPIRED_ENTERPRISE_TRUST_ACCELERATORS.md) |
| Maturity questionnaire POC | [PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md](completed/PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md) |
| Governance inspiration | [ACTIONABLE_GOVERNANCE_AND_TRUST.md](../ops/inspirations/ACTIONABLE_GOVERNANCE_AND_TRUST.md) |
| Open-core / plugin governance (next P1) | [#811](https://github.com/DataBoar/data-boar/issues/811) |
| DMBOK / CDO related | [#637](https://github.com/DataBoar/data-boar/issues/637) · [#639](https://github.com/DataBoar/data-boar/issues/639) |

---

## Changelog

| Date | Change |
| ---- | ------ |
| 2026-08-17 | Initial consolidation from [#643](https://github.com/DataBoar/data-boar/issues/643) (product-only; no personal/academic framing). |
