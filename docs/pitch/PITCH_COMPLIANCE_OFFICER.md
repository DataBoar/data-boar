# Compliance officer / General Counsel pitch — liability and multi-regime evidence

**Português (Brasil):** [PITCH_COMPLIANCE_OFFICER.pt_BR.md](PITCH_COMPLIANCE_OFFICER.pt_BR.md) · **Index:** [INDEX.md](INDEX.md)

**Audience:** Chief Compliance Officers, General Counsel, corporate legal, audit liaison — **not** a substitute for the DPO deck.

---

## Distinct from the DPO

The DPO (or equivalent) owns **operational privacy** (lawful basis, DSAR process, minors as a detection lane). Counsel and the CCO own **enterprise liability**, **audit defence**, **multi-regime programmes**, and **transactional** diligence. Use [PITCH_DPO.md](PITCH_DPO.md) for inventory language; use **this** page for **who is on the hook** and **what evidence you can show an auditor or buyer**.

Canonical non-technical legal summary: [COMPLIANCE_AND_LEGAL.md](../COMPLIANCE_AND_LEGAL.md). Framework **profiles** (configuration, not magic): [COMPLIANCE_FRAMEWORKS.md](../COMPLIANCE_FRAMEWORKS.md). **Do not** treat this deck as a reproduction of those documents.

## Strong disclaimer

Data Boar **does not** decide lawfulness, notify regulators, certify ISO/SOC, or opine on deal risk. Outputs are **technical findings** with optional **norm tags**. Interpretation, privilege, and filings stay with counsel and the accountable officers.

## Liability and audit

- Repeatable **session** artefacts (XLSX, optional manifest YAML, audit JSON) support an **audit trail of what was scanned**, not a clean bill of health.
- Sampling and timeouts are **operator-configured** — document them; they bound what you can claim.
- Shared responsibility matches [DECISION_MAKER_VALUE_BRIEF.md](../DECISION_MAKER_VALUE_BRIEF.md): the customer owns legal basis and risk acceptance.

## Multi-regime (inventory language, not certification)

| Regime (examples) | Product role |
| ----------------- | ------------ |
| LGPD / GDPR | Norm-tagged recommendations and samples — not a adequacy decision |
| PCI DSS | Pattern/PAN-oriented detection when configured — not a QSA assessment |
| SOX / internal control | Evidence **input** to ITGC narratives — not management assertion |
| Sector (BACEN-class, HIPAA samples, etc.) | Extensible YAML profiles — [compliance-samples/](../compliance-samples/) |

Collision hints (heuristic only): [JURISDICTION_COLLISION_HANDLING.md](../JURISDICTION_COLLISION_HANDLING.md).

## M&A / due diligence

Bounded discovery on **agreed** systems can feed a diligence workstream (what classes of data appear in **this** perimeter). It does **not** replace vendor questionnaires, reps & warranties analysis, or forensic hold. Scope the targets in writing.

## Next step

- **Privacy operations:** [PITCH_DPO.md](PITCH_DPO.md)
- **Security evidence:** [PITCH_CISO.md](PITCH_CISO.md)
- **Finance:** [PITCH_CFO.md](PITCH_CFO.md)
