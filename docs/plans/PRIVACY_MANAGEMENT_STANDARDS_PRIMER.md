# Primer: Privacy management standards (ISO/IEC 27701, ISO/IEC 27018, NIST Privacy Framework)

<!-- plans-hub-summary: Primer ISO 27701 / 27018 / NIST Privacy Framework — Data Boar alignment -->

**Audience:** Compliance engineers, privacy architects, GRC teams, ISO 27001/27701 auditors.

**Product stance:** Data Boar **supports evidence** for privacy programmes; it does **not** certify ISO 27701, ISO 27018, or NIST PF implementation. Map controls to **your** ISMS/PIMS with counsel.

**Related:** [COMPLIANCE_FRAMEWORKS.md](../COMPLIANCE_FRAMEWORKS.md) · [pitch/PITCH_DPO.md](../pitch/PITCH_DPO.md) · [completed/PLAN_COMPLIANCE_STANDARDS_ALIGNMENT.md](completed/PLAN_COMPLIANCE_STANDARDS_ALIGNMENT.md)

---

## ISO/IEC 27701:2019 (PIMS)

Extension of **ISO/IEC 27001** for privacy information management. Annex **B** maps to **GDPR**; annex **C** to **ISO/IEC 29100** themes. Organisations declare which regulations apply; the standard structures **controls**, not legal outcomes.

### How Data Boar fits (today)

| Theme / control area | Typical 27701 ask | Data Boar capability (shipped) | Notes |
| -------------------- | ----------------- | ------------------------------ | ----- |
| PII inventory | Know what you process and where | Configured **targets** (filesystem, SQL/NoSQL, APIs, shares, BI connectors) + **findings** with location metadata | Metadata-first; no bulk PII exfiltration |
| Processing scope | Document systems in scope | **Scope import** (CSV → YAML fragment), starter configs under `deploy/samples/` | [SCOPE_IMPORT_QUICKSTART.md](../ops/SCOPE_IMPORT_QUICKSTART.md) |
| Risk / impact evidence | Support DPIA-style workshops | **norm_tag** + recommendation overrides; **MINOR_DETECTION** lane; jurisdiction **hints** (heuristic) | Hints are **not** legal conclusions |
| Control operation | Repeatable checks | Scheduled/API scans, session **SQLite**, Excel + heatmap + optional **scan_manifest** YAML | [REPORTS_AND_COMPLIANCE_OUTPUTS.md](../REPORTS_AND_COMPLIANCE_OUTPUTS.md) |
| Accountability trail | Show who ran what | Session metadata, **`--export-audit-trail`**, **`--diff`** between sessions | Dashboard transport in audit JSON |

### Clause-oriented map (illustrative — verify with your auditor)

| Reference | Control intent | Data Boar feature |
| --------- | -------------- | ----------------- |
| 6.15.1 (PII inventory) | Identify PII locations | Discovery engine + reports |
| 6.15.2 (privacy impact) | Impact assessment inputs | Findings + minor/sensitive categories + executive Markdown |
| 8.2.x (operational controls) | Run technical measures | CLI, API, dashBOARd, rate limits |
| Annex B (GDPR mapping) | Align to GDPR articles | Built-in **GDPR** norm tags + EU samples in `compliance-samples/` |

**(roadmap)** Deeper PIMS **control checklist packs** in the maturity questionnaire content packs — see [PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md](completed/PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md).

---

## ISO/IEC 27018:2019 (PII in public cloud)

Code of practice for **PII processors** in **public cloud** environments. Extends ISO/IEC 27001 with cloud-specific objectives (customer transparency, breach notification cooperation, sub-processor discipline).

### Cloud PII alignment (today)

| 27018 theme | Data Boar capability (shipped) | Gap / roadmap |
| ----------- | ------------------------------ | ------------- |
| Know customer PII in cloud workloads | Scan **cloud-adjacent** targets when you configure them (APIs, exports, mounted shares) | **(roadmap)** First-class **S3 / Azure Blob / GCS** connectors — [PLAN_OBJECT_STORAGE_CLOUD_CONNECTORS.md](PLAN_OBJECT_STORAGE_CLOUD_CONNECTORS.md) |
| Evidence for customer audits | Excel + manifest + audit trail export | Customer still owns cloud IAM and DPA |
| Segregation / access | **API key**, optional **WebAuthn**, optional **RBAC** (Pro+ tier) | Network and cloud IAM remain customer scope |

**Practical pattern today:** export object inventories or sync buckets to a **filesystem/SQL** target the engine already scans; document that boundary in your RoPA.

---

## NIST Privacy Framework v1.0

Five functions: **Identify-P**, **Govern-P**, **Control-P**, **Communicate-P**, **Protect-P**. Widely used for US federal and enterprise readiness (complements FedRAMP **system** controls, not a replacement).

| Function | Outcome | Data Boar capability (shipped) | Roadmap |
| -------- | ------- | ------------------------------ | ------- |
| **Identify-P** | Inventory and understand data processing | **Data Sniffing** pass: connectors, bounded reads, sensitivity detection | Richer cloud object inventory when object-storage plan ships |
| **Govern-P** | Policies and roles | Config profiles, licensing tiers, optional **dashboard RBAC** | SSO/OIDC Phase 3 — [PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md](PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md) |
| **Control-P** | Manage privacy risk | Findings triage, rate limits, **Safe-Hold** posture (stop on critical engine risk — operator runbooks) | Enterprise remediation plugins — **#606** |
| **Communicate-P** | Transparency to stakeholders | Reports, **GRC executive JSON** schema, **`--export-dsar`** (metadata-first) | DSAR export helpers expanding — USAGE roadmap bullets |
| **Protect-P** | Data security safeguards | TLS / explicit HTTP modes, audit exports, optional **maturity row HMAC** (POC) | Build identity / release integrity — [PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md](PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md) |

Deck vocabulary **Data Sniffing** / **Deep Boring** maps to discovery vs structured compliance report depth — [COMPLIANCE_FRAMEWORKS.md](../COMPLIANCE_FRAMEWORKS.md#deterministic-detection-vs-generative-llm-hype).

---

## Anti-overclaim checklist

Before citing this primer in RFPs or audit packs:

1. State **which connectors** are in scope for the engagement.
2. Mark **(roadmap)** items as planned, not delivered.
3. Pair tool output with **legal review** (DPO/counsel sign-off).
4. Run **`--validate-config`** before production scans ([USAGE.md](../USAGE.md)).

---

## Maintainer

When features ship, update the tables above and [PRIMERS_HUB.md](PRIMERS_HUB.md). Run `python scripts/plans_hub_sync.py --write` after hub-summary edits.
