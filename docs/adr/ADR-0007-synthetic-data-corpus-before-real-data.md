# ADR 0007 — Synthetic data corpus as mandatory pre-requisite before real production data

- **Status:** Accepted
- **Date (UTC):** 2026-04-03
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Context

Data Boar's detector pipeline needs to be validated against realistic personal and sensitive data
(CPF, RG, health records, financial data, minors data, pseudo-anonymised datasets, cloaked file
types) before it can be trusted in real client engagements.

Three risks make it unacceptable to start validation with real production data immediately:

1. **Legal/privacy exposure:** accepting real client data before a controlled test baseline exists
   creates unnecessary LGPD/GDPR surface. A bug that causes data exfiltration or incorrect
   classification would be harder to detect and explain.
2. **NDA and confidentiality:** collaborators (team members) who provide real or near-production
   samples are volunteers at this stage. Their employers data must not be implicitly used as a
   test corpus without explicit data-processing agreements.
3. **FP/FN blindness:** without a ground-truth corpus where expected detections are known in
   advance, a regression in detector sensitivity is indistinguishable from correct behaviour on
   noisy data.

## Decision

Build and maintain a **synthetic data corpus** (gitignored under `docs/private/lab/`) before
accepting any real production datasets. The corpus must cover:

- **Database containers:** MariaDB, PostgreSQL, Oracle XE, MongoDB — seeded with synthetic PII
  and sensitive data in all category types defined in the detector compatibility matrix.
- **File format matrix:** PDF, DOCX, XLSX, CSV, JSON, XML, TXT, SQLite, ODS, PPTX, EML — in
  plain, password-protected, and compressed (ZIP, 7z, GZIP, TAR) variants.
- **Cloaking scenarios:** files renamed to misleading extensions (e.g. `.pdf` -> `.mp3`,
  `.xlsx` -> `.jpg`) to validate MIME-type detection over extension heuristics.
- **Minor-data scenarios:** synthetic records where `dt_nasc` places the subject under 18,
  flagged with `flag_menor=TRUE` and `fonte=SINTETICO`. Every such row must be detected.
- **FP-forced cases:** data that resembles PII structurally (fiscal codes, GPS coordinates, order
  numbers) but is not personal data. Ensures the detector whitelist/contextual logic is tuned.
- **FN-forced cases:** PII deliberately obfuscated or fragmented (unformatted CPF, aliased emails,
  split name fields). Maps known blind spots for prioritised remediation.
- **Pseudo-anonymisation and re-identification:** datasets processed with suppression, generalisation,
  k-anonymity, and pseudonymisation. Confirms that the detector flags residual re-identification
  risk correctly.

Execution follows a phased plan documented in `PLAN_SYNTHETIC_DATA_LAB.pt_BR.md`:
**Phase 0** (scaffolding) -> **Phase 1** (basic corpus) -> **Phase 2** (advanced: passwords,
cloaking, minors) -> **Phase 3** (pseudo-anon) -> **Phase 4** (real data with collaborators).
Phase 4 is explicitly blocked until Phases 1-3 pass.

## Consequences

- **No real client or collaborator data** is accepted for testing until Phases 1-3 are complete
  and documented. This is a hard gate, not a suggestion.
- Corpus generator scripts live under `scripts/lab/` (tracked). Generated data lives under
  `docs/private/lab/synthetic-data-lab/` (gitignored). CI never sees the data.
- FP/FN baseline results are recorded per sprint in `docs/private/lab/reports/` (gitignored)
  and reviewed as part of the detector regression checklist.
- When a new file format or connector is added to the compatibility matrix, a corresponding
  synthetic sample must be added to the corpus before the connector is considered production-ready.
- Docker Compose for lab DBs relies on the Ansible `lab-node-01_docker_ce` role being enabled on the
  test host -- cross-dependency with ADR 0008.

## References

- `docs/plans/PLAN_SYNTHETIC_DATA_LAB.pt_BR.md` -- phased execution plan.
- `docs/TECH_GUIDE.md` -- detector compatibility matrix (file formats and connectors).
- `docs/adr/0008-ansible-opt-in-knob-pattern-lab-infra.md` -- container infrastructure on LAB-NODE-01.
