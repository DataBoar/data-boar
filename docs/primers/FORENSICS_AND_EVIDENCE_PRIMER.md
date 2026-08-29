# Primer: digital forensics and evidence (integrator KT)

**Português (Brasil):** [FORENSICS_AND_EVIDENCE_PRIMER.pt_BR.md](FORENSICS_AND_EVIDENCE_PRIMER.pt_BR.md)

This note is for **integrators, CISOs, and compliance engineers** who hear “forensic-grade” on a
**discovery scanner** and need a **shared mental model**. It is **not** a forensic-science textbook,
**not** a substitute for an official expert report (*laudo pericial*), and **not** legal advice.

**Positioning ceiling:** [ADR-0025](../adr/ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md)
(evidence and inventory, **not** a legal-conclusion engine). Product legal page:
[COMPLIANCE_AND_LEGAL.md](../COMPLIANCE_AND_LEGAL.md). Glossary:
[GLOSSARY.md](../GLOSSARY.md) (§2 `scan_manifest`, §9 evidence terms).

**Do not duplicate:** DPO pitch, TECH_GUIDE live/offline notes, and the README tagline stay in those
files — this primer **links**; it does not rewrite them.

---

## 1. What digital forensics is (product wording)

**Digital forensics** is the technical practice of **identifying, collecting, preserving, analysing,
and interpreting** digital artefacts so findings can be **defended** in an audit, incident, or legal
process. Inspiration (not reproduced): [ISO/IEC 27037:2012](https://www.iso.org/standard/44381.html);
[NIST SP 800-86](https://csrc.nist.gov/publications/detail/sp/800-86/final) (2006).

Data Boar’s job in that world is **narrow**: **non-destructive, metadata-only discovery** of personal
and sensitive data on **configured targets**, plus **session artefacts** you can attach to *your*
evidence pack.

---

## 2. Evidence lifecycle (six stages)

A common six-stage loop (NIST SP 800-86; [ISO/IEC 27043:2015](https://www.iso.org/standard/60943.html)
for investigation process language — buy the standards for official text):

| Stage | What it means here | Data Boar mapping |
| ----- | ------------------ | ----------------- |
| Identification | Decide **what** might hold relevant data | Configured **targets** + sampling policy |
| Collection | Obtain artefacts **without** unnecessary alteration | **Read-only** connectors; no wipe/write of source rows as part of scan |
| Preservation | Keep collected material **stable and attributable** | Session UUID, UTC window, `scan_manifest_*.yaml`, SQLite session store |
| Analysis | Interpret **what matched** | Detector stack + `norm_tag`; **not** legal characterisation |
| Documentation | Record method, limits, and results | Excel + executive Markdown + manifest + audit-trail bullets |
| Presentation | Hand a pack to DPO/counsel/IR | Artefacts are **inputs**; counsel presents conclusions |

Tracked SVG: [data_boar_evidence_lifecycle.svg](../assets/diagrams/data_boar_evidence_lifecycle.svg).

---

## 3. Key distinctions

| Contrast | Operational recovery | Forensic-grade posture |
| -------- | -------------------- | ---------------------- |
| Goal | Restore service / find the leak fast | Defensible **inventory** of *where* sensitive data sat |
| Risk if sloppy | Longer outage | Contaminated or unexplained evidence |
| Documentation | Tickets, runbooks | Manifest + hashes of **scope/config**, timestamps, tool version |

- **Collection ≠ acquisition ≠ preservation.** Copying a live sample is not imaging a disk; writing a
  YAML manifest is not sealing an exhibit bag. ISO/IEC 27037 draws those lines — this product does
  **not** implement forensic imaging.
- **Live vs offline.** A Data Boar session typically reads **live** configured systems (bounded
  samples). **Offline** acquisition (write-blocked disk image) is a **different** discipline with
  different contamination risk. See [TECH_GUIDE.md](../TECH_GUIDE.md) for engine behaviour; do not
  treat a live scan as a bit-for-bit image.

SVG: [data_boar_operational_vs_forensic.svg](../assets/diagrams/data_boar_operational_vs_forensic.svg).

---

## 4. Volatility triage (gap)

When data can disappear (RAM, logs that rotate, ephemeral containers), responders **document a
priority order**. [ISO/IEC 27037](https://www.iso.org/standard/44381.html) discusses volatility as a
collection concern.

**Product gap:** there is **no** `volatility_class` field in `plugin_schema.yaml` (or equivalent) in
this tree today. Do **not** invent plugin metadata. Until a dedicated issue lands, treat volatility
as an **operator/IR runbook** concern, not a shipped schema.

---

## 5. Integrity and hash

A **hash** (typically SHA-256) shows a byte string has not changed **since it was hashed**. It is
**not** a full **chain of custody**. Custody still needs **who**, **when** (timezone), **which tool
and version**, **what identifiers**, and **where** the artefact is stored.

**What this product actually records today** (see `report/scan_evidence.py`): a
`scan_manifest_*.yaml` with product/version, UTC generation time, **session id**,
**`config_scope_hash`**, scan window, sampling/timeouts, and finding **counts** — **metadata**, not
raw PII. That supports **repeatable inventory**. It is **not** a signed exhibit seal.

**ed25519** in this repo is used for **license JWT** verification and **ADR inventory attestation**
— **not** as a signature over each scan manifest. Do not claim the YAML is SSH-signed.

---

## 6. Normative framework (pointers only)

| Norm | Year / id | Scope (plain language) | URL |
| ---- | --------- | ---------------------- | --- |
| ISO/IEC 27037 | 2012 | Identification, collection, acquisition, preservation | [ISO 44381](https://www.iso.org/standard/44381.html) |
| ISO/IEC 27041 | — | Whether methods are adequate and sufficient | [ISO 44405](https://www.iso.org/standard/44405.html) |
| ISO/IEC 27042 | — | Analysis and technical interpretation | [ISO 44406](https://www.iso.org/standard/44406.html) |
| ISO/IEC 27043 | 2015 | Investigation principles and processes | [ISO 60943](https://www.iso.org/standard/60943.html) |
| ISO/IEC 27050-1 | — | e-discovery / ESI concepts | [ISO 78525](https://www.iso.org/standard/78525.html) |
| NIST SP 800-86 | 2006 | Integrating forensic techniques into incident response | [NIST SP 800-86](https://csrc.nist.gov/publications/detail/sp/800-86/final) |
| ENISA first-responder guide | — | Field guidance for first responders | [ENISA](https://www.enisa.europa.eu/publications/electronic-evidence-a-basic-guide-for-first-responders) |
| CPP (Brazil) Arts. 158-A–158-F | Lei 13.964/2019 | Chain of custody in Brazilian criminal procedure | [Planalto CPP](https://www.planalto.gov.br/ccivil_03/decreto-lei/del3689compilado.htm) |

SVG (family map, **not** an ISO figure): [data_boar_isoiec_forensics_family.svg](../assets/diagrams/data_boar_isoiec_forensics_family.svg).

This page **does not** quote those texts.

---

## 7. Ethics, privacy, and governance

- **Minimisation:** collect only what the **authorised scope** needs (LGPD Arts. 6–7 as
  **organisational** duties — the scanner does not decide lawfulness).
- **Access control:** findings and manifests can still be sensitive **metadata**; treat report dirs
  like any other compliance share.
- **Uncertainty (*visum et repetum*):** keep **observed matches** separate from **interpretations**.
  Declare limits (encryption, sampling, unreachable targets) in the report — Safe-Hold when evidence
  is insufficient.

ISO/IEC 27041 (method adequacy) + LGPD: buy/read official texts; do not treat this primer as either.

---

## 8. Data Boar positioning

The engine implements **forensic-grade PII discovery** in the **compliance-inventory** sense:
non-destructive reads, metadata-only findings, a **scan manifest** for how the session was bounded,
plugin/schema **collection records**, and `norm_tag` as an **analysis label** — not a court finding.

It is **not** a substitute for an official forensic report. Counsel and accredited experts still
own legal conclusions. See [ADR-0025](../adr/ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md).

**Related (echoes — read there, do not copy here):**

- Pitch (DPO/legal): [PITCH_DPO.md](../pitch/PITCH_DPO.md)
- Technical client / CISO: [TECH_GUIDE.md](../TECH_GUIDE.md)
- Compliance page: [COMPLIANCE_AND_LEGAL.md](../COMPLIANCE_AND_LEGAL.md)
- Product one-liner: [README.md](../../README.md)

First-responder **checklist** expansion is tracked separately as GitHub **#747**.
