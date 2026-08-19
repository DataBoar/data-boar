# Primer: Health sector compliance (HIPAA/PHI, ANS, ANVISA, CFM)

<!-- plans-hub-summary: Primer HIPAA/PHI / ANS / ANVISA / CFM — alinhamento Data Boar para setor de saúde -->

**Audience:** CISOs and DPOs at hospitals, health plans, healthtechs, labs, and pharma; Privacy / Security Officers on US covered entities or business associates.

**Product stance:** PHI detection by Data Boar is **Discovery** — it does **not** replace access controls, encryption, or a **BAA** (Business Associate Agreement). The engine does **not** decide whether a HIPAA **breach** occurred, count individuals for HHS OCR notice, certify Security Rule safeguards, or file with **ANS**, **ANVISA**, or **CFM**.

**Related:** [COMPLIANCE_FRAMEWORKS.md](../COMPLIANCE_FRAMEWORKS.md) · [COMPLIANCE_AND_LEGAL.md](../COMPLIANCE_AND_LEGAL.md) (HIPAA / HITECH inventory limits) · [compliance-sample-us_hipaa_phi.yaml](../compliance-samples/compliance-sample-us_hipaa_phi.yaml) · [compliance-sample-brazil_saude.yaml](../compliance-samples/compliance-sample-brazil_saude.yaml) (**#511**) · [GLOSSARY.md](../GLOSSARY.md) (PHI, ePHI, HIPAA)

There is **no** Brazilian statute that copies HIPAA/HITECH as one package. In Brazil, **LGPD Art. 11** (sensitive health data) plus sector layers (**ANS**, **CFM**, **ANVISA**) apply — [PLAN_COMPLIANCE_EVIDENCE_MAPPING.md](PLAN_COMPLIANCE_EVIDENCE_MAPPING.md).

---

## HIPAA — Privacy, Security, and Breach Notification (US)

HIPAA (and **HITECH**) apply to **covered entities** and **business associates**. **PHI** is individually identifiable health information; **ePHI** is the electronic subset ([GLOSSARY.md](../GLOSSARY.md)).

| Rule | Typical ask | Data Boar capability (shipped) | Notes |
| ---- | ----------- | ------------------------------ | ----- |
| Privacy Rule (45 CFR Part 164 Subpart E) | Know where PHI lives; minimum necessary | Built-in tags **HIPAA** in reports; [us_hipaa_phi sample](../compliance-samples/compliance-sample-us_hipaa_phi.yaml) (`US_HIPAA_NPI`, `US_HIPAA_DEA`, `US_HIPAA_MRN`, `US_HIPAA_ICD10`, precise geolocation) | Discovery / mapping only |
| Security Rule (45 CFR Part 164 Subpart C) | Administrative, physical, technical safeguards for ePHI | Repeatable scans + **`--export-audit-trail`** as **inventory evidence** | Does **not** implement access control, encryption, or risk analysis |
| Breach Notification Rule (45 CFR §§ 164.400–414) | Notify individuals / HHS OCR (60 days); media if >500 in a state | Locate possible PHI copies; **`--diff`** between sessions | Does **not** send OCR notices or decide “breach” |

**Special sensitivity** (sample lexicon + recommendation text only): psychotherapy notes, 42 CFR Part 2, GINA. Not dedicated detectors.

### Eighteen Safe Harbor identifiers (45 CFR § 164.514(b)(2))

HHS Safe Harbor de-identification lists **18** identifier types. Coverage below is **heuristic inventory**, not a legal PHI classification. Pair the HIPAA sample (`regex_overrides_file` + `ml_patterns_file` + `report.recommendation_overrides`).

| # | Identifier | Coverage | What ships today | Gap / roadmap |
| - | ---------- | -------- | ---------------- | ------------- |
| 1 | Names | Partial | Default ML terms (`first name`, `last name`, `full name`, …) | No dedicated name NER |
| 2 | Geographic subdivisions smaller than a state (address, city, ZIP, geocode) | Partial | HIPAA sample **precise geolocation** (Safe Harbor item as mapped in the sample header); ML terms `ZIP code`, `geographic subdivisions` | No street-address regex |
| 3 | Dates (except year) related to the individual; ages over 89 | Partial | Built-in **`DATE_DMY`**; ML `birth date` / `data de nascimento`; HIPAA sample ML `admission date`, `discharge date`, `date of death` | No age-over-89 rule |
| 4 | Telephone numbers | Partial | Built-in **`PHONE_BR`**; ML phone/contact terms | US NANP shape is override-only |
| 5 | Fax numbers | Roadmap | — | No dedicated fax pattern |
| 6 | Email addresses | Shipped | Built-in **`EMAIL`** | — |
| 7 | Social Security numbers | Shipped | Built-in **`CCPA_SSN`** (`XXX-XX-XXXX`) | Other SSN punctuations need overrides |
| 8 | Medical record numbers | Partial | HIPAA sample **`US_HIPAA_MRN`**; BR sample **`BR_SAUDE_PRONTUARIO`** (**#511**) | Institution formats vary — high FP risk |
| 9 | Health plan beneficiary numbers | Partial | BR sample **`PHI_HEALTH_PLAN`** / **`BR_SAUDE_ANS`** (column / ANS registry) | No dedicated US member-ID regex |
| 10 | Account numbers | Roadmap | — | Do not treat **`CREDIT_CARD`** as this row |
| 11 | Certificate / license numbers | Partial | HIPAA sample **`US_HIPAA_NPI`**, **`US_HIPAA_DEA`** (provider IDs) | Patient licences / state IDs not covered |
| 12 | Vehicle identifiers / plates | Roadmap | Custom-regex example in [SENSITIVITY_DETECTION.md](../SENSITIVITY_DETECTION.md) | Not a default pattern |
| 13 | Device identifiers / serials | Roadmap | — | — |
| 14 | URLs | Roadmap | — | — |
| 15 | IP addresses | Roadmap | — | — |
| 16 | Biometric identifiers | Partial | Sensitive-category ML/DL terms (biometric / genetic) when those packs are enabled | No fingerprint/voice matcher |
| 17 | Full-face photos and comparable images | Roadmap | Image / OCR work is a **plan**, not a default HIPAA detector | Do not claim photo PHI from this primer |
| 18 | Any other unique identifying number, characteristic, or code | Partial | HIPAA **`US_HIPAA_ICD10`**; BR **`PHI_CID10_COL`**, CNS, council IDs (**#511**) | Catch-all stays counsel-scoped |

**(roadmap)** Optional extra US health-plan / device / IP-URL patterns if a named engagement needs them — do not loosen regexes in public samples without FP tests.

---

## Brazil — LGPD Art. 11 plus ANS, ANVISA, CFM

**Baseline (#511, merged):** [compliance-sample-brazil_saude.yaml](../compliance-samples/compliance-sample-brazil_saude.yaml). **Always pair** with [compliance-sample-lgpd.yaml](../compliance-samples/compliance-sample-lgpd.yaml). Heuristic regex — **not** CRM/CRF checksum validation ([COMPLIANCE_FRAMEWORKS.md](../COMPLIANCE_FRAMEWORKS.md)).

| Identifier / lexicon (sample) | `norm_tag` in sample | Role |
| ----------------------------- | -------------------- | ---- |
| CRM / CRF / CRO / COREN | `LGPD Art. 5` (council IDs) | Professional registers — high FP in generic text |
| CNS (Cartão Nacional de Saúde) | `LGPD Art. 5` | Patient-adjacent health ID |
| ANVISA RMS / contextual registro | `LGPD Art. 5` (regulatory) | Product / medicine register — **not** a patient PHI analogue |
| ANS operadora (6 digits) | `LGPD Art. 5` | Plan operator registry |
| Receituário / prontuário | `LGPD Art. 5` | Prescription / record numbers |
| CID-10 / health-plan **column names** | `LGPD Art. 11` | Diagnosis / carteirinha-style headers |

ML terms in the same file cover diagnóstico, exames, medicamentos, prontuário, farmacovigilância — **lexicon**, not structured clinical coding.

### CFM 1821/2007 and Lei 13.787/2018

These norms address **digitisation and retention** of medical records (prontuário: diagnosis, CID, exams, prescribed medicines). Data Boar **finds field-like patterns** (`BR_SAUDE_PRONTUARIO`, CID columns, receita, ML “histórico clínico”). It does **not** implement digitalisation, legal retention clocks, or CFM archival certification.

### ANS and ANVISA

| Body | What the #511 sample adds | What Data Boar does **not** do |
| ---- | ------------------------- | ------------------------------ |
| **ANS** | Operator registry + plan/carteirinha column gates + ML “plano de saúde” | ANS filings, beneficiary-roll certification |
| **ANVISA** | RMS / registro MS shapes + pharmacovigilance lexicon | RDC compliance, lot recall, or product registration |

**(roadmap)** Extra ANS/ANVISA identifier packs only when a named engagement needs them — same config-override model, not a new engine.

---

## Anti-overclaim checklist

Before citing this primer in RFPs or BAAs:

1. State **which samples** were enabled (HIPAA, BR saúde, LGPD).
2. Mark **Roadmap** / **(roadmap)** rows as planned, not delivered.
3. Keep the **Discovery ≠ access control / encryption / BAA** sentence in customer text.
4. Do **not** claim OCR/photo PHI, US fax/IP/URL defaults, or official regulator filings.
5. Run **`--validate-config`** before production scans ([USAGE.md](../USAGE.md)).

---

## Maintainer

When patterns ship, update the 18-row table and [PRIMERS_HUB.md](PRIMERS_HUB.md). Run `python scripts/plans_hub_sync.py --write` after hub-summary edits (hub table lists `PLAN_*.md` only; this primer is indexed in **PRIMERS_HUB**).
