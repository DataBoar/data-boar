# PLAN: FERPA and EdTech Compliance Vertical

<!-- plans-hub-summary: Technical inventory support for FERPA (US education records) and broader EdTech compliance verticals. Covers pattern detection, YAML sample creation, and use-case alignment for K-12, higher education, and EAD/LMS platforms. -->
<!-- plans-hub-related: PLAN_YAML_PLUGIN_SYSTEM.md, PLAN_COMPLIANCE_EXPANSION_GLOBAL_JURISDICTIONS.md -->

Status: Draft
Date: 2026-05-14
Authors: Fabio Leitao
Priority: H1
Tags: compliance, ferpa, edtech, education, ead, minors, usa, lms, privacy, use-case
Depends on: PLAN_YAML_PLUGIN_SYSTEM.md

---

## Motivation

The **EdTech** and **EAD (Ensino a Distância)** market represents an expanding vertical for Data Boar.
An active commercial conversation (Rio Grande do Sul, May 2026 — special thanks to an EAD provider contact) surfaces
a concrete client need: **where does student PII live across our LMS, integrations, and backups?**

**FERPA (Family Educational Rights and Privacy Act, 20 U.S.C. § 1232g)** is the US federal law governing
education records at institutions receiving federal funding. It is the primary privacy framework for:

- **K-12 school districts** (US)
- **Universities and colleges** (US)
- **EdTech vendors** that process education records on behalf of institutions (acting as "school officials")
- **EAD / distance-learning platforms** operating in or integrating with US institutions

Even for **Brazilian EAD** platforms without a US footprint, FERPA awareness matters when:
- An institutional client holds student data subject to FERPA (e.g. a partner US institution)
- The platform targets **international expansion** (North America)
- Investors or acquirers apply **FERPA-aligned diligence** standards in data rooms

---

## FERPA Technical Scope

### What FERPA governs

| Scope | Covered | Out of scope for scanner |
|---|---|---|
| **Education records** (any record directly related to a student, maintained by institution or its agent) | Yes — inventory | Not a legal scoping authority |
| **PII components**: name, address, DOB, student ID, SSN, grades, transcripts, enrollment | Yes — detection | —  |
| **Directory information** (name, email, major — can be publicly released unless opted-out) | Yes — detected, flagged | Scanner cannot evaluate opt-out status |
| **Who can access** (parent/eligible student rights, FERPA release, school-official exception) | **No** — access-control audit is out of scanner scope | — |
| **Parental consent records** (FERPA release forms) | Partial — can flag consent-related fields by ML terms | Legal sufficiency not evaluated |
| **FPCO enforcement** (Family Policy Compliance Office, US Dept of Education) | N/A | — |

### What Data Boar provides

1. **Inventory**: discovers where student PII concentrates across files, databases, APIs, LMS exports.
2. **Evidence for due diligence**: heatmaps and GRC JSON for compliance programme planning or acquirer data rooms.
3. **YAML sample** (`compliance-sample-us_ferpa.yaml` — see Phase 1 below): custom regex, ML terms, `recommendation_overrides` with `norm_tag: "FERPA"`.
4. **Minor detection alignment**: existing `MINOR_DETECTION.md` and `EDTECH_LMS_EXPORTS_AND_MINORS` use-case complement FERPA signals.
5. **COPPA bridge**: FERPA and COPPA (Children's Online Privacy Protection Act) often co-apply; `compliance-sample-us_ftc_coppa.yaml` (A8) will cover the COPPA layer.

---

## Phases

### Phase 1 — YAML sample: `compliance-sample-us_ferpa.yaml`

**Deliverable**: a YAML compliance sample following the geometry established in `compliance-sample-us_va_vcdpa.yaml`.

| Component | Content |
|---|---|
| **Regex** | `FERPA_SSN` (mirrors core), `FERPA_STUDENT_ID` (heuristic: 6–10 alphanumeric with contextual field name), `FERPA_DOB`, + four precise geolocation patterns |
| **ML terms** (~30) | `education record`, `transcript`, `gpa`, `grade report`, `enrollment status`, `student id`, `directory information`, `non-directory information`, `eligible student`, `school official`, `legitimate educational interest`, `FERPA consent`, `FERPA release`, `parent rights`, `guardian`, `minor student`, `lms`, `sis` (student information system), `roster`, `gradebook`, `course completion`, `disability accommodation`, `iep` (individualized education plan), `504 plan`, `financial aid`, `fafsa`, `student loan` |
| **`recommendation_overrides`** | `base_legal`: "FERPA (20 U.S.C. § 1232g); FPCO — Family Policy Compliance Office, US Dept of Education"; `risk`: "Education records containing student PII subject to FERPA..."; `relevant_for`: "FERPA Compliance Officer, DPO, Legal, Student Records" |

**Acceptance criteria:**
- `uv run pytest tests/test_compliance_samples.py -k ferpa` passes (≥2 items)
- All four geolocation regex patterns present
- At least 25 ML terms

### Phase 2 — Use-case alignment

Update **`docs/use-cases/EDTECH_LMS_EXPORTS_AND_MINORS.md`** (and `.pt_BR.md`) to:
- Reference `compliance-sample-us_ferpa.yaml` and `norm_tag: FERPA` explicitly
- Add FERPA to the "partner opportunity" and "compliance frameworks" sections
- Link to `COMPLIANCE_FRAMEWORKS.md` FERPA row once it exists

### Phase 3 — COMPLIANCE_FRAMEWORKS.md + README table row

Add FERPA row to `docs/COMPLIANCE_FRAMEWORKS.md` table and `compliance-samples/README.md`.
Update pt-BR mirrors.

### Phase 4 — PLANS_TODO.md and sprint alignment

- Add FERPA to the compliance vertical sprint theme
- Link to `EDTECH_LMS_EXPORTS_AND_MINORS` use-case for commercial visibility

---

## Context: Brazilian EAD market (RS conversation, 2026-05)

**Profile**: Brazilian EAD platforms increasingly process student data regulated by **LGPD** (not FERPA by default),
but several factors make FERPA awareness a differentiator:

- **International partnerships** with accredited US HEIs expose the platform to FERPA obligations
- **MEC/INEP** accreditation processes increasingly require LGPD + privacy-by-design evidence, for which Data Boar's inventory signal is directly applicable
- **Investor diligence** for VC-backed EAD in Brazil follows international standards; FERPA-aligned language in the data room is recognised as maturity signal

The immediate deliverable for this conversation is demonstrating that Data Boar can **find and tag student PII** (student IDs, DOBs, guardian contacts, grade records) across LMS exports and integration artefacts — and that a **FERPA YAML sample** allows customisation of the recommendation language for institutions in scope.

---

## Acceptance criteria (overall plan)

- [ ] `compliance-sample-us_ferpa.yaml` committed and tests passing
- [ ] `EDTECH_LMS_EXPORTS_AND_MINORS.md` updated with FERPA reference
- [ ] FERPA row in `COMPLIANCE_FRAMEWORKS.md` table
- [ ] `PLANS_TODO.md` updated with FERPA compliance vertical status
- [ ] pt-BR mirrors updated

---

## Related docs

- [`docs/use-cases/EDTECH_LMS_EXPORTS_AND_MINORS.md`](../use-cases/EDTECH_LMS_EXPORTS_AND_MINORS.md) ([pt-BR](../use-cases/EDTECH_LMS_EXPORTS_AND_MINORS.pt_BR.md))
- [`docs/MINOR_DETECTION.md`](../MINOR_DETECTION.md)
- [`docs/COMPLIANCE_FRAMEWORKS.md`](../COMPLIANCE_FRAMEWORKS.md)
- [`docs/plans/PLAN_COMPLIANCE_EXPANSION_GLOBAL_JURISDICTIONS.md`](PLAN_COMPLIANCE_EXPANSION_GLOBAL_JURISDICTIONS.md)
- [`docs/compliance-samples/compliance-sample-us_ftc_coppa.yaml`](../compliance-samples/compliance-sample-us_ftc_coppa.yaml) (A8 — pending)
