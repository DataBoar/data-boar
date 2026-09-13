# DPO and legal pitch — litigation, custody, and counsel (Brazil)

**Português (Brasil):** [PITCH_DPO_AND_LEGAL.pt_BR.md](PITCH_DPO_AND_LEGAL.pt_BR.md) · **Index:** [INDEX.md](INDEX.md)

**Audience:** DPOs in incident mode, litigators, compliance officers, and law-firm partners who need **defensible inventory artefacts** — not another privacy-operations overview.

**Companion, not a duplicate:** programme language (lawful basis, DSAR, minors, multinational hints) lives in [PITCH_DPO.md](PITCH_DPO.md). This page is the **litigation and chain-of-custody** angle. Canonical technical primer: [FORENSICS_AND_EVIDENCE_PRIMER.md](../primers/FORENSICS_AND_EVIDENCE_PRIMER.md). Non-technical legal ceiling: [COMPLIANCE_AND_LEGAL.md](../COMPLIANCE_AND_LEGAL.md).

---

## The problem (opening hook)

An employee is walked out. Security believes a mailbox or share was copied to a personal account. The laptop is still on the desk. Someone in IT reboots it “to stop further damage”, then logs in as themselves, opens folders by hand, pastes screenshots into a ticket, and writes nothing about **who** touched the machine, **when**, or **with which tool**.

What that sequence actually does: volatile traces are gone, the workstation is now a **contaminated exhibit**, and counsel inherits a story that will not survive a serious challenge — administrative or criminal. The leak may still be real. The **proof pack** is already broken.

**What Data Boar can contribute before that reboot** (if the relevant stores are **configured targets**): a **non-destructive, read-only** discovery pass; a `scan_manifest_*.yaml` that records product version, session id, UTC window, sampling/timeouts, and a **hash of configured scope**; Excel plus optional executive Markdown with **counts**, not bulk PII. That is **inventory evidence you can attach** to *your* pack. It is **not** a RAM capture, disk image, or mailbox hold. Do not reboot first if the job is still “where did personal data sit on these systems?”

---

## What DPOs and lawyers need to know

- **LGPD / ANPD.** Administrative work with the [Brazilian data-protection authority (ANPD)](https://www.gov.br/anpd/pt-br) expects **documented** inventory of personal data — not a slide deck of good intentions. Data Boar produces **repeatable session artefacts** so the office can show *what was scanned, when, and under which bounds*. It does **not** decide notifiability or draft the filing.
- **Brazilian criminal procedure (CPP).** Lei 13.964/2019 added a **statutory chain-of-custody** frame for digital evidence (Arts. **158-A** through **158-F**). Official text: [Código de Processo Penal (Planalto)](https://www.planalto.gov.br/ccivil_03/decreto-lei/del3689compilado.htm). This product **does not** implement that statute. A scan manifest can **enter** a custody pack (who/what/when/tool version/scope hash); it **does not** replace seals, accredited experts, or the court’s own rules.
- **ISO/IEC 27037:2012.** International language for identification, collection, and preservation of digital evidence ([ISO catalogue](https://www.iso.org/standard/44381.html)). Buy the standard for official wording. Data Boar maps to **bounded collection + documentation**, not forensic imaging.
- **e-discovery concepts.** ISO/IEC 27050-1 is a pointer for ESI process language ([ISO 78647](https://www.iso.org/standard/78647.html)) — still **your** hold and production workflow.

**Integrity (honest):** SHA-256-class hashes in this product describe **configured scope / artefact bytes since hashed**. They are **not** a full legal chain of custody. **ed25519** in this repository signs **license JWTs** and **ADR inventory attestation** — **not** each `scan_manifest`. Do not tell a court the YAML is SSH-signed. Primer §5 is the source of truth.

---

## What Data Boar is not

Per **[ADR 0025](../adr/ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md)** (evidence and inventory, **not** a legal-conclusion engine):

- **Not** a substitute for an official expert report (*laudo pericial oficial*).
- **Not** a legal-opinion engine (no “violation”, no “must notify”, no admissibility ruling).
- **Not** a DFIR suite, write-blocker, or courtroom exhibit seal.

**What it does provide:** forensic-**grade inventory** artefacts (metadata-only findings, session trail, manifest) for **compliance support** and **counsel’s file**. [ADR 0027](../adr/ADR-0027-commercial-tier-boundaries-licensing-docs-and-future-jwt-claims.md) is the commercial-tier documentation boundary (open core vs Pro/Enterprise in public licensing docs — **no** client pricing on this page).

Shared responsibility: [DECISION_MAKER_VALUE_BRIEF.md](../DECISION_MAKER_VALUE_BRIEF.md). Outputs and manifests: [REPORTS_AND_COMPLIANCE_OUTPUTS.md](../REPORTS_AND_COMPLIANCE_OUTPUTS.md).

---

## Differentiator (generic scanner vs this product)

| Aspect                | Typical generic scanner            | Data Boar                                                                                             |
| ------                | ----------------------             | ---------                                                                                             |
| Chain of custody      | Often none beyond a CSV dump       | `scan_manifest` + session id + UTC window + **scope hash** — **input** to custody, not a seal         |
| Legal alignment       | Usually undeclared                 | **Pointers** to CPP Arts. 158-A–F and ISO/IEC 27037 — **alignment language**, not a legal certificate |
| Admissibility posture | Operational convenience            | **Evidence-support** grade: documented method and limits; counsel argues admissibility                |
| Audit trail           | Often a log file nobody can replay | Session SQLite + report artefacts + audit-trail bullets — **repeatable**, not “immutable via SSH”     |

---

## Audiences on this page

### DPO

Use this deck when the clock is an **incident** or an **ANPD** conversation: preserve **inventory of where PII-like data sat**, with sampling limits written down. Keep [PITCH_DPO.md](PITCH_DPO.md) for day-to-day rights and minors.

### Lawyer (litigator)

PII **locations and classes** as **technical indicators** for litigation strategy — not production-ready ESI. Pair with your hold letter and, where criminal/administrative digital evidence is in play, **your** CPP custody procedure. e-discovery process remains ISO/IEC 27050-1 **on your side**.

### Compliance officer

The **ISO/IEC 27001 + 27701 + LGPD** story is **governance + PIMS language + Brazilian law** — Data Boar is **evidence input** to that triad, not a certification. See [PITCH_COMPLIANCE_OFFICER.md](PITCH_COMPLIANCE_OFFICER.md) for liability and M&A DD.

### Law-firm partner

**Commercial framing:** fewer “we looked around and took screenshots” incidents; faster first pack for the DPO/CISO workshop; lower risk of **self-inflicted** contamination. ROI is **risk reduction and time-to-defensible inventory**, not a promised win in court. Named clients and rates stay off this public page ([ADR 0027](../adr/ADR-0027-commercial-tier-boundaries-licensing-docs-and-future-jwt-claims.md)).

---

## Next step

- **Privacy operations (DSAR, minors):** [PITCH_DPO.md](PITCH_DPO.md)
- **Enterprise liability:** [PITCH_COMPLIANCE_OFFICER.md](PITCH_COMPLIANCE_OFFICER.md)
- **Security evidence:** [PITCH_CISO.md](PITCH_CISO.md)
- **Integrator primer:** [FORENSICS_AND_EVIDENCE_PRIMER.md](../primers/FORENSICS_AND_EVIDENCE_PRIMER.md)
- **Legal page (do not reprint here):** [COMPLIANCE_AND_LEGAL.md](../COMPLIANCE_AND_LEGAL.md)
