# Primer: SOC 2 Privacy Trust Services Criteria

<!-- plans-hub-summary: Primer SOC 2 Privacy TSC — Data Boar como gerador de evidência para auditoria SOC 2 -->

**Audience:** Compliance teams at SaaS / tech / healthtech / fintech service organizations preparing SOC 2 Type I or Type II; CPA / AICPA examiners; CISOs who own the SOC 2 workstream.

**Product stance:** Data Boar **generates evidence inputs** (inventory, metadata-only reports, optional exports). It does **not** perform a SOC 2 examination and does **not** issue a SOC 2 report. A licensed **CPA** issues Type I (design at a point in time) or Type II (operating effectiveness over a period). See [GLOSSARY.md](../GLOSSARY.md) (**SOC 2**) and [COMPLIANCE_FRAMEWORKS.md](../COMPLIANCE_FRAMEWORKS.md#auditable-and-management-standards-supporting-role).

**Related:** [ADR 0037](../adr/ADR-0037-data-boar-self-audit-log-governance.md) (honest self-audit baseline) · [USAGE.md](../USAGE.md) (`--export-audit-trail`, `--export-dsar`, `--diff`, HTTPS / API key) · [SECURITY.md](../SECURITY.md)

There is **no** `compliance-sample-*.yaml` for SOC 2. Control-framework mapping stays **norm tags / recommendation overrides / this primer** — not a PII vocabulary pack ([PLAN_ADDITIONAL_COMPLIANCE_SAMPLES.md](completed/PLAN_ADDITIONAL_COMPLIANCE_SAMPLES.md)).

---

## Privacy TSC (P1–P8)

Criteria names follow AICPA **Trust Services Criteria** (Privacy category). Coverage is **heuristic inventory and operator-surface evidence**, not a Privacy TSC walkthrough.

| Criterion | Typical ask | Data Boar capability (shipped) | Status |
| --------- | ----------- | ------------------------------ | ------ |
| **P1** Notice and communication | Privacy notice; tell subjects how you use PI | Excel / heatmap / optional **`--governance-report`** (Pro+) are **inventory artefacts** for *your* team | Partial — **not** a data-subject privacy notice |
| **P2** Choice and consent | Capture and honour consent / opt-out | — | Roadmap / out of scope — **`--export-audit-trail` is not a consent log** |
| **P3** Collection | Know what PI you collect and from where | **Data Sniffing** on configured **targets** ([GLOSSARY.md](../GLOSSARY.md)) | Partial — documents what is **found in stores**, not collection practices or lawful basis |
| **P4** Use, retention, disposal | Limit use; retain only as needed; dispose | Locate PII copies; **`--diff SESSION_A SESSION_B`** after cleanup | Partial — does **not** decide “inadequate retention” or delete/dispose data |
| **P5** Access | Subject access; restrict who can see PI (and scanner outputs) | Optional **`api.require_api_key`**, WebAuthn, Pro+ **RBAC**; **`--export-dsar`** = metadata-first findings for **one scan session** ([USAGE.md](../USAGE.md)) | Partial — DSAR JSON is **not** subject access into the customer’s production systems; ADR 0037: **no** per-download / per-config-save audit row |
| **P6** Disclosure to third parties | Track onward sharing; notify as required | Same reports / DSAR JSON can **feed** a human vendor questionnaire | Partial — audit export does **not** record third-party disclosures |
| **P7** Quality | Accurate, complete, up-to-date PI | Findings carry **source** (path / column) and **severity** | Partial — `output_confidence` on `/status` is **transport / license / integrity**, not per-finding data-quality or ML accuracy |
| **P8** Monitoring and enforcement | Ongoing monitoring that privacy controls operate | Repeatable scans, **`--diff`**, optional Slack / webhook notify ([USAGE.md](../USAGE.md#51-operator-notifications-optional)) | Partial — **no** built-in scheduler ([#558](https://github.com/DataBoar/data-boar/issues/558)); Data Boar **CI** is the **vendor repo**, not the customer’s Type II period |

**(roadmap)** Operator-action audit table (report download + config save) per ADR 0037 Decision 5; optional SOC 2-oriented `recommendation_overrides` for a **named engagement** — never a default “we are SOC 2 certified” claim.

### How to use Data Boar in a SOC 2 evidence pack

| Artefact | What a CPA can treat it as | What it is **not** |
| -------- | -------------------------- | ------------------ |
| Excel + heatmap + `scan_manifest_*.yaml` | Scope / inventory of **where PI-like fields sat** in **configured** targets | A Privacy notice (P1) or completeness of the estate |
| **`--export-dsar`** | Metadata inventory for one session (subject-rights **prep**) | Fulfilment of P5 access or P6 disclosure |
| **`--export-audit-trail`** | Aggregate JSON: `data_wipe_log`, `scan_sessions_summary`, `trust_state`, `dashboard_transport` | Immutable / WORM log; per-session operator or target lists ([AI primer](AI_COMPLIANCE_PRIMER.md) Art. 12 note) |
| Optional maturity HMAC + `maturity_assessment_integrity` | Tamper-evident **questionnaire POC** rows | Hash chain of all SOC 2 evidence |
| **`--diff`** in the **customer’s** cron / CI | Change detection between two sessions (P8 **support**) | Built-in continuous monitoring |

---

## Security TSC — CC6 (not Confidentiality)

**CC6** is **logical and physical access** under the **Security** (common) criteria. **Confidentiality** is a **separate** TSC category (**C1.x**). Do not label CC6 as “Confidentiality TSC.”

| Criterion | Typical ask | Data Boar capability (shipped) | Notes |
| --------- | ----------- | ------------------------------ | ----- |
| **CC6.1** | Logical access to the system and data | Opt-in **`api.require_api_key`** (`X-API-Key` / Bearer); **`GET /health`** stays public; fail-closed start if the flag is true but no key resolves ([SECURITY.md](../SECURITY.md), [USAGE.md](../USAGE.md)) | **Default is off** (demo / loopback). **[#549](https://github.com/DataBoar/data-boar/issues/549) is closed** (documented risk + fail-closed when misconfigured). Remaining gap: operators must **turn the key on** for exposed dashboards |
| **CC6.1** (finer roles) | Least privilege on operator UI | Optional **WebAuthn** + Pro+ **`dashboard_rbac`** (`audit_logs.read`, …) | Phase 3 SSO/OIDC remains [PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md](PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md) / **#86** |
| **CC6.7** | Restrict transmission; protect data in transit | **HTTPS-by-default** for `--web`; plaintext only with **`--allow-insecure-http`**; `dashboard_transport` on `/status` and audit export | Does **not** encrypt findings **at rest** in SQLite or Excel |

Governance Lens **Enterprise** adds BACEN / PCI / FEBRABAN **storytelling** only — **no** SOC 2 TSC map in `--governance-report` ([USAGE.md](../USAGE.md#governance-lens-enterprise)).

---

## Anti-overclaim checklist

Before citing this primer in an SOC 2 PBC list or RFP:

1. Keep the sentence: Data Boar **generates evidence** — a **CPA** issues the SOC 2 report.
2. Do **not** call `--export-audit-trail` **immutable** or a full admin audit log (ADR 0037).
3. Do **not** map `--export-dsar` to P5/P6 fulfilment.
4. Do **not** claim a built-in scheduler or that **this repo’s CI** is the customer’s P8 programme.
5. Do **not** claim a SOC 2 sample YAML or a Governance Lens SOC 2 module.
6. State **Type I vs Type II** and the **period** the CPA will test — the scanner does not define it.
7. Mark **(roadmap)** rows as planned, not delivered.
8. Run **`--validate-config`** before production scans ([USAGE.md](../USAGE.md)).

---

## Maintainer

When access-log or scheduler work ships, update the P5/P8 rows and [PRIMERS_HUB.md](PRIMERS_HUB.md). Run `python scripts/plans_hub_sync.py --write` after hub-summary edits (hub table lists `PLAN_*.md` only; this primer is indexed in **PRIMERS_HUB**).
