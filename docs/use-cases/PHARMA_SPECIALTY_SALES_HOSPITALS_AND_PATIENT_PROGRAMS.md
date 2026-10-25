# Use-case storyboard — specialty pharma sales, hospitals/pharmacies, and patient-adjacent programs

**Português (Brasil):** [PHARMA_SPECIALTY_SALES_HOSPITALS_AND_PATIENT_PROGRAMS.pt_BR.md](PHARMA_SPECIALTY_SALES_HOSPITALS_AND_PATIENT_PROGRAMS.pt_BR.md)

This is a **documentation storyboard** for workshops where a **representative or distributor** sells **high-complexity** medicines (e.g. oncology, rare disease) to **hospitals and pharmacies**, sometimes with **patient-support** or **access** programmes that touch **end patients**. It is **not** clinical, pharmacovigilance, or sector-regulator advice (e.g. **FDA**, **EMA**, **ANVISA**-shaped obligations stay with qualified teams).

## Cast (generic roles)

- **Organisation:** Mid-market **field force** + inside sales + **market access**; data spans **B2B** orders and **B2C-adjacent** programme spreadsheets.
- **Data subjects:** HCPs (prescribers, hospital buyers), pharmacy staff, **patients** or caregivers when a programme collects contact or treatment-window fields.
- **Systems:** CRM, **order / allocation** exports, sample logistics spreadsheets, **call notes**, email attachments with hospital letterheads, **programme** workbooks (enrolment, shipment-to-patient).

## Storyboard (flow)

1. **Hospital order** — high-value line items; **institution** identifiers mixed with prescriber names in the same row.
2. **Pharmacy chain** — recurring deliveries; **national ID** fragments may appear in “verification” comments.
3. **Rare or oncology context** — low-volume SKUs; **small *n*** in tables increases the chance that **every** row is highly sensitive when patient-adjacent fields exist.
4. **Optional patient programme** — a separate workbook may hold **phone + address + therapy window**; teams may **accept** handling that data under strict policy—Data Boar still only sees **what the scan is pointed at**.
5. **Boar sniffs (strict scope)** — connectors flag **health-adjacent** and **identifier** patterns; [minor detection](../MINOR_DETECTION.md) may matter where **guardian** contact appears.
6. **Human moment** — **DPO + medical affairs + compliance** align lawful basis, **BA**/**DPA**-style contracts, retention, and **whether** patient fields may enter a given environment at all. The tool does **not** classify **PHI** under **HIPAA** or “special category” under **GDPR**—it surfaces **signals** for governance.

## How Data Boar helps without deciding

- **Shows concentration** of **health-related** and **identifier** metadata across CRM, files, and ad-hoc spreadsheets.
- **Supports** decisions to **narrow** scan roots, **delete** programme copies from general shares, or **move** evidence to governed stores.
- **Does not** replace **PV** systems, **Hub** data, validated **RIM**, or ethics-committee records.

## Partner opportunity

Life-sciences consultancies use this storyboard for **field-force data-room** prep and **market-access** workshops where CRM + programme workbooks are the “data soup” reality.

## Product alignment (maintainers)

Stress **health-adjacent** sensitivity, **small-*n*** table narratives, and **SQL sampling** discipline. Maintainer sequencing: [docs/README.md](../README.md) *Internal and reference*.

## Related docs

- [use-cases/README.md](README.md) ([pt-BR](README.pt_BR.md))
- [COMPLIANCE_AND_LEGAL.md](../COMPLIANCE_AND_LEGAL.md) ([pt-BR](../COMPLIANCE_AND_LEGAL.pt_BR.md)) — health-adjacent positioning
- [SENSITIVITY_DETECTION.md](../SENSITIVITY_DETECTION.md) ([pt-BR](../SENSITIVITY_DETECTION.pt_BR.md)) — aggregated risk, minors
- [GLOSSARY.md](../GLOSSARY.md) ([pt-BR](../GLOSSARY.pt_BR.md)) — **VBA** (*value-based agreement* sense, not Office VBA)
- [USAGE.md](../USAGE.md) ([pt-BR](../USAGE.pt_BR.md)) — relational sampling caps and optional **`DATA_BOAR_SQL_SAMPLE_LIMIT`**
- [TOPOLOGY.md](../TOPOLOGY.md) ([pt-BR](../TOPOLOGY.md)) — `connectors/sql_sampling.py` (sampling SQL shape)
