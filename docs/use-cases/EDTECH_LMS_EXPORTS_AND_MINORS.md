# Use-case storyboard — EdTech, LMS exports, and minors (due diligence and hygiene)

**Português (Brasil):** [EDTECH_LMS_EXPORTS_AND_MINORS.pt_BR.md](EDTECH_LMS_EXPORTS_AND_MINORS.pt_BR.md)

Storyboard for **education platforms** exporting **rosters**, **grades**, and **guardian contact** fields. **Not** pedagogical assessment, **not** child-safety moderation of live chat, and **not** a COPPA/LGPD “compliance certificate.”

## Cast (generic roles)

- **Organisation:** EdTech vendor or school district IT team managing **LMS** backups and integration CSVs.
- **Data subjects:** Students (including **minors**), parents/guardians, instructors.
- **Systems:** LMS CSV/JSON exports, help-desk ticket archives, optional SQL replicas of roster tables.

## Storyboard (flow)

1. **Semester export** — wide spreadsheets mix **student IDs**, **parent phones**, and free-text “notes.”
2. **Integration sprawl** — third-party apps leave **duplicate** copies under `/integrations/` trees.
3. **Boar sniffs (scoped targets)** — [MINOR_DETECTION.md](../MINOR_DETECTION.md) class hints surface as **signals** for human triage, not automated blocking.
4. **Investor / district review** — heatmap supports **question lists** for subprocessors and retention.
5. **Human moment** — **Parental consent** records are legal artefacts; counsel decides sufficiency.

## How Data Boar helps without deciding

- **Supports** **technical due diligence** packages for buyers or districts (metadata inventory).
- **Aligns** engineering and DPO on **where** minors’ data concentrates before architectural refactors.
- **Does not** replace LMS, SIS, or statutory education-reporting systems.

## Partner opportunity

Consultancies bundle a **scoped Boar pass** with **privacy programme** design for Series A–B EdTech or for **district** RFP hygiene. For US institutions and school-official vendors, combine the pass with FERPA-oriented `norm_tag` wording via [compliance-sample-us_ferpa.yaml](../compliance-samples/compliance-sample-us_ferpa.yaml).

## Product alignment (maintainers)

Strong overlap with **US child-privacy technical alignment** and **minor detection** roadmap themes—ship **documented, conservative** behaviour and **clear limits** in [MINOR_DETECTION.md](../MINOR_DETECTION.md) and [USAGE.md](../USAGE.md). Maintainer sequencing: [docs/README.md](../README.md) **Internal and reference**.

**FERPA (US education records):** Use [compliance-sample-us_ferpa.yaml](../compliance-samples/compliance-sample-us_ferpa.yaml) for `norm_tag` **FERPA** (SSN-shaped values, contextual student IDs, DOB labels, LMS/SIS vocabulary, four-pattern geolocation). Co-apply [compliance-sample-us_ftc_coppa.yaml](../compliance-samples/compliance-sample-us_ftc_coppa.yaml) when under-13 online collection is in scope. Entry point: [COMPLIANCE_FRAMEWORKS.md](../COMPLIANCE_FRAMEWORKS.md#list-of-samples-and-links) ([pt-BR](../COMPLIANCE_FRAMEWORKS.pt_BR.md#lista-de-amostras-e-links)).

**Signal strengths:** minor hints, jurisdiction samples, audit JSON / GRC JSON for acquirer data rooms ([GRC_EXECUTIVE_REPORT_SCHEMA.md](../GRC_EXECUTIVE_REPORT_SCHEMA.md)).

## Related docs

- [use-cases/README.md](README.md) ([pt-BR](README.pt_BR.md))
- [MINOR_DETECTION.md](../MINOR_DETECTION.md) ([pt-BR](../MINOR_DETECTION.pt_BR.md))
- [COMPLIANCE_FRAMEWORKS.md](../COMPLIANCE_FRAMEWORKS.md) ([pt-BR](../COMPLIANCE_FRAMEWORKS.pt_BR.md))
- [USAGE.md](../USAGE.md) ([pt-BR](../USAGE.pt_BR.md))
