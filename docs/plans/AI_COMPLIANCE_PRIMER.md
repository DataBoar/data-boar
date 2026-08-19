# Primer: AI compliance (EU AI Act, ISO/IEC 42001, NIST AI RMF)

<!-- plans-hub-summary: Primer EU AI Act / ISO 42001 / NIST AI RMF — Data Boar como compliance layer para AI pipelines -->

**Audience:** AI/ML engineers, CDOs, CISOs, and compliance teams that develop or deploy AI systems (especially EU-facing programmes).

**Product stance:** Data Boar covers the **data layer** — it does **not** evaluate the model itself. Discovery can inventory personal and sensitive fields in **configured targets** that happen to feed training, fine-tuning, or RAG corpora. The engine does **not** classify an AI system as high-risk, run conformity assessment, certify an AI Management System, score model quality or bias, or produce a NIST AI RMF attestation.

**Related:** [COMPLIANCE_FRAMEWORKS.md](../COMPLIANCE_FRAMEWORKS.md#cyber-ai-governance-evidence-not-samples) · [COMPLIANCE_AND_LEGAL.md](../COMPLIANCE_AND_LEGAL.md) · [PLAN_COMPLIANCE_EVIDENCE_MAPPING.md](PLAN_COMPLIANCE_EVIDENCE_MAPPING.md) (NIST AI RMF = adjacent inventory) · [docs/primers/AI_EVOLUTION_PRIMER.md](../primers/AI_EVOLUTION_PRIMER.md) (vocabulary; not this compliance primer) · [GLOSSARY.md](../GLOSSARY.md) (**Data Sniffing**, **LLM**)

There is **no** `compliance-sample-*.yaml` for the EU AI Act, ISO/IEC 42001, or NIST AI RMF. [COMPLIANCE_FRAMEWORKS.md](../COMPLIANCE_FRAMEWORKS.md#cyber-ai-governance-evidence-not-samples) treats those instruments as **evidence and inventory**, not PII vocabulary packs. Shipping an “AI Act sample” would be a **category mismatch** and an overclaim risk.

---

## Framework × obligation × Data Boar (status)

| Framework | Obligation (typical ask) | How Data Boar addresses it | Status |
| --------- | ------------------------ | -------------------------- | ------ |
| EU AI Act Art. 10 | Quality / relevance of training, validation, and testing data; examine bias in data | Point **Data Sniffing** at the corpus as a filesystem or connector **target**; built-in `DEFAULT_PATTERNS` + optional jurisdiction samples flag PII/sensitive **shapes** | Partial — inventory only; no dataset-quality or bias metrics |
| EU AI Act Art. 12 | Automatic logging of high-risk system events | Session SQLite + **`--export-audit-trail`** records **who scanned which targets** | Partial — scanner-session log, **not** Art. 12 model-operation logs; **not** WORM |
| EU AI Act Art. 13 | Transparency / instructions for use to deployers | Excel / heatmap / optional **`--governance-report`** (Pro+) summarise **findings in scanned stores** | Partial — not a model card or deployer instructions |
| EU AI Act Annex III / Art. 6 | Classify high-risk use cases | — | Roadmap / out of scope — counsel + provider classify the **system** |
| ISO/IEC 42001:2023 cl. 6.1.2 | Repeatable AI risk assessment (incl. data risks) | Same inventory as Art. 10; findings + `norm_tag` feed a **human** AIMS assessment | Partial — does **not** perform or certify the assessment |
| ISO/IEC 42001:2023 cl. 6.2 | AI objectives and plans to achieve them | — | Roadmap / organisational — not a product control |
| ISO/IEC 42001:2023 cl. 9.1 | Monitor, measure, analyse, evaluate AIMS performance | **`--diff`**, repeatable scans, audit-trail JSON | Partial — scan ops evidence, not AIMS KPIs |
| NIST AI RMF **MAP** | Understand data that feeds AI | **Data Sniffing** on configured corpora ([GLOSSARY.md](../GLOSSARY.md)) | Partial — configured targets only |
| NIST AI RMF **MEASURE** | Measure AI risks | Finding **severity** (e.g. HIGH) + reports on **PII matches** | Partial — not model accuracy, fairness, or robustness scores |
| NIST AI RMF **GOVERN** / **MANAGE** | Policies, roles, treatment | Config profiles, licensing tiers, optional Governance Lens | Partial — organisational AIMS/RMF stays with the operator |

**(roadmap)** Named-engagement `recommendation_overrides` that cite Art. 10 / AI RMF **MAP** wording in Excel — consulting copy, not a default public “implements the AI Act” claim.

---

## EU AI Act — Regulation (EU) 2024/1689

Official text: [Regulation (EU) 2024/1689](https://eur-lex.europa.eu/eli/reg/2024/1689/oj). Application dates below follow **Art. 113** as **amended** by [Regulation (EU) 2026/1744](https://eur-lex.europa.eu/eli/reg/2026/1744/oj) (Digital Omnibus on AI; entered into force **27 July 2026**).

### Timeline (verify on EUR-Lex before citing in an RFP)

| Date | What applies | Notes |
| ---- | ------------ | ----- |
| 1 August 2024 | 2024/1689 entered into force | Not the general application date |
| 2 February 2025 | Prohibited practices (Art. 5); AI literacy (Art. 4) | Already in application; unchanged by 2026/1744 |
| 2 August 2025 | GPAI model obligations | Already in application; unchanged by 2026/1744 |
| **2 August 2026** | General application in original Art. 113; **Art. 50** transparency (certain systems, including generative / deepfake marking) | **Not** the current date for Chapter III high-risk core duties |
| **2 December 2027** | Chapter III §§ 1–3 for **Annex III** high-risk systems (Art. 6(2)) | **2026/1744** moved this from the original **2 August 2026** high-risk date |
| **2 August 2028** | Chapter III §§ 1–3 for **Annex I** product-embedded high-risk systems (Art. 6(1)) | Original date was 2 August 2027 |

Issue sketches that still say “August 2026 = high-risk systems enforcement” describe the **pre-omnibus** Art. 113 plan. Use the **amended** dates above.

### Article 10 — data and data governance

Art. 10 (high-risk) asks providers to ensure training, validation, and testing data are relevant, sufficiently representative, and examined for bias. Data Boar **does not** measure representativeness or statistical bias. If the corpus is a **configured target**, the shipped detector can surface **PII and sensitive-field shapes** (built-in patterns; optional LGPD/GDPR/HIPAA/… samples when those files are enabled). That inventory can **feed** a human Art. 10 review. It is **not** an Art. 10 conformity pack.

### Article 12 — record-keeping

Art. 12 requires automatic logging of events over the lifetime of a **high-risk AI system**. **`--export-audit-trail`** exports scanner-session JSON from SQLite (`data_wipe_log`, session summary, `trust_state`, …) — [USAGE.md](../USAGE.md). That is **operator accountability for scans**, not model-inference or training-run logs. Same limit as other primers: **not** a WORM / legally immutable archive.

### Article 13 — transparency

Art. 13 requires information that lets **deployers** use the system appropriately. Reports and optional **`--governance-report`** document **what the scanner found in stores you pointed at**. They do **not** replace instructions for use, user-facing AI notices, or Art. 50 marking.

### Annex III

Annex III lists high-risk **use-case** families (biometrics, critical infrastructure, education, employment, essential private/public services, law enforcement, migration, administration of justice — confirm the live annex). Data Boar **does not** decide whether a system falls in Annex III.

---

## ISO/IEC 42001:2023 — AI Management Systems

ISO/IEC 42001 is the first **certifiable** AI management-system standard (AIMS), analogous to ISO/IEC 27001 for an ISMS. Data Boar **does not** certify 42001 and **does not** replace the AIMS.

Clause numbering (do not copy stale sketches that pin risk assessment on **6.2**):

| Clause | Intent | Data Boar capability (shipped) | Notes |
| ------ | ------ | ------------------------------ | ----- |
| **6.1.2** | Define and apply a repeatable **AI risk assessment** | Inventory of personal/sensitive data in AI-adjacent **targets** | Feeds the assessment; does not score likelihood/impact for the **model** |
| **6.2** | **AI objectives** and planning to achieve them | — | Organisational; not a scanner feature |
| **9.1** | Monitor, measure, analyse, and evaluate AIMS performance | Repeatable scans, **`--diff`**, **`--export-audit-trail`** | Evidence that **scans ran**; not AIMS effectiveness KPIs |

Optional Enterprise Governance Lens adds GRC **storytelling** in Markdown ([USAGE.md](../USAGE.md#governance-lens-enterprise)). It is **not** an ISO 42001 audit report.

---

## NIST AI RMF 1.0 — GOVERN, MAP, MEASURE, MANAGE

The [NIST AI Risk Management Framework](https://airc.nist.gov) is **voluntary** US vocabulary. Per [PLAN_COMPLIANCE_EVIDENCE_MAPPING.md](PLAN_COMPLIANCE_EVIDENCE_MAPPING.md), AI RMF is **adjacent** when a client needs to **map or inventory data that feeds AI systems**. The product does **not** walk AI RMF functions as a certification tool and does **not** produce NIST attestations.

| Function | Typical ask | Data Boar capability (shipped) | Notes |
| -------- | ----------- | ------------------------------ | ----- |
| **MAP** | Know what data and context the AI system uses | **Data Sniffing** (bounded discovery + sensitivity detection) on configured targets | Same motor as other primers — [GLOSSARY.md](../GLOSSARY.md) |
| **MEASURE** | Evaluate AI risks with metrics | Finding **severity** and Excel/heatmap on **PII matches** | **Not** model eval (accuracy, fairness, robustness, drift) |
| **GOVERN** | Policies, roles, accountability | Config, tiers, optional dashboard RBAC | SSO/OIDC remains a plan — [PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md](PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md) |
| **MANAGE** | Prioritise and treat risks | Triage findings; **`--diff`** after remediation | Treatment (delete, minimise, retrain) is organisational |

Do **not** treat [PLAN_G_TIER.md](PLAN_G_TIER.md) (**G0–G3**) as a NIST **MEASURE** score on AI datasets. That plan is **repo gravity** for operator issues (orthogonal to H/U/P). It is **not** a shipped detector field on scan findings.

---

## Anti-overclaim checklist

Before citing this primer in RFPs or AIMS packs:

1. State **which connectors and corpora** were scanned (training dump, feature store, RAG bucket — only if they are **targets**).
2. Keep the sentence: Data Boar covers the **data layer** — it does **not** evaluate the model itself.
3. Do **not** claim an AI Act / 42001 / AI RMF **sample pack** exists.
4. Do **not** call `--export-audit-trail` an Art. 12 automatic log of the **AI system**.
5. Quote **amended** high-risk dates (**2 December 2027** Annex III; **2 August 2028** Annex I), not the original 2 August 2026 high-risk date alone.
6. Mark **(roadmap)** rows as planned, not delivered.
7. Run **`--validate-config`** before production scans ([USAGE.md](../USAGE.md)).

---

## Maintainer

When capabilities ship, update the status table and [PRIMERS_HUB.md](PRIMERS_HUB.md). Run `python scripts/plans_hub_sync.py --write` after hub-summary edits (hub table lists `PLAN_*.md` only; this primer is indexed in **PRIMERS_HUB**).
