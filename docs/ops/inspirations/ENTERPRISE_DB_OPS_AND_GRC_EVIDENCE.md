# Enterprise database operations and GRC evidence — patterns for Data Boar alignment

**Português (Brasil):** [ENTERPRISE_DB_OPS_AND_GRC_EVIDENCE.pt_BR.md](ENTERPRISE_DB_OPS_AND_GRC_EVIDENCE.pt_BR.md)

**Source note:** synthesizes **stable vendor docs** and **recurring themes** in public Oracle-DBA / DBRE discourse (backup, HA, patching, segregation). It does **not** copy third-party post text or treat LinkedIn infographic grids as **automatic** product requirements. **Named talent-pool pointers** stay under **gitignored** `docs/private/commercial/` if you want roster context off the canonical repo.

---

## Why this belongs next to NIST/CIS and Wazuh notes

**Database operations** teams and **GRC** template packs often speak different dialects: RTO/RPO, change windows, and “restore drill” on one side; RACI, audit registers, and third-party risk sheets on the other. Data Boar sits mainly on **data discovery and evidence** (what sensitive information exists and where). Mapping the three avoids **over-claiming** (“we replace the DBA”) and shows **where exports** can **slot into** customer spreadsheets **if** they define columns.

---

## Stable primary references (Oracle — backup / recovery framing)

Use these instead of scraping social feeds when teaching the team:

- [Oracle Database Backup and Recovery User’s Guide](https://docs.oracle.com/en/database/oracle/oracle-database/19/bradv/) (conceptual home for RMAN-oriented **backup and recovery** discipline in vendor docs).

Themes that recur in practitioner training and public discourse (including activity around HA features, patching, and standby validation):

- **Proven restore** beats “we take backups” — same idea as deferred **recovery discipline** in [SUPPLY_Colleague-NN_AND_TRUST_SIGNALS.md](SUPPLY_Colleague-NN_AND_TRUST_SIGNALS.md) / [WAZUH_NIST_CIS_LABOP_ALIGNMENT.md](WAZUH_NIST_CIS_LABOP_ALIGNMENT.md).
- **Change control** and **rollback** paths for schema/deploy risk — parallel to **review discipline** for `.github/workflows` and dependency merges.
- **Patch level and supply Colleague-Nn** awareness (verified patch state) — aligns with **ecosystem incident** and **SHA pin** habits ([ADR 0005](../../adr/ADR-0005-ci-github-actions-supply-Colleague-Nn-pins.md)).
- **Segregation** (prod vs non-prod, least privilege for break-glass admin) — organizational; Data Boar supports **evidence** for **data** exposure, not OS/DB IAM design.

---

## “Must-have” GRC / cybersecurity template grids (social infographics)

Lists that circulate as **Excel packs** (incident dashboard, patch tracker, third-party risk scorecard, audit findings register, KPI/KRI mapping, etc.) are **useful mental models**, not a contract for Data Boar.

| Template class (generic) | What Data Boar can **honestly** contribute | What stays outside product scope |
| ------------------------- | ------------------------------------------- | --------------------------------- |
| **Audit findings / evidence** | Exports that show **where** policy-relevant content was found (path, type, sample policy) — **attachment** to a finding row if the customer maps fields | Severity scoring for **database uptime** or **network** control |
| **Data / processing inventory** | Discovery output supports **Identify** for **data** (see [NIST CSF](https://www.nist.gov/cyberframework) table in Wazuh alignment note) | Full CMDB or **asset** lifecycle |
| **Third-party / vendor risk** | Evidence that **subprocessors** or **copies** of data were surfaced in scans (when in scope) | Vendor financial or legal scoring |
| **Patch / vuln management** | `pip-audit`, Dependabot, image SBOM roadmap ([ADR 0003](../../adr/ADR-0003-sbom-roadmap-cyclonedx-then-syft.md)) for **our** stack | Oracle RU / DB patch cadence |
| **Incident / IR dashboard** | Timestamps and exports for **scanner** or **pipeline** events if customers integrate logs | SOC tier-1 triage for DB alerts |

**Bidirectional learning:** if buyers repeatedly ask for **column X** in an export, that is a **product/docs** signal (field in CSV/JSON/API), not a reason to clone a 36-tab workbook in-repo.

---

## Product and doc improvements to consider (deferred, not committed here)

- Document a **minimal “evidence bundle”** narrative: what artifacts ship with a scan for **DPO / audit** consumers (aligns with [COMPLIANCE_AND_LEGAL.md](../../COMPLIANCE_AND_LEGAL.md) honesty).
- Optional **operator playbook** snippet: how to **attach** Data Boar output to a customer’s existing **GRC row** (process only; no mandatory tooling).
- Keep **Oracle / MSSQL / NoSQL operational runbooks** as **customer** or **partner** (e.g. DBA) scope unless the product explicitly ships DB agents.

---

## Related in-repo

- [WAZUH_NIST_CIS_LABOP_ALIGNMENT.md](WAZUH_NIST_CIS_LABOP_ALIGNMENT.md) — CSF/CIS vocabulary and lab **Detect/Recover**
- [SUPPLY_Colleague-NN_AND_TRUST_SIGNALS.md](SUPPLY_Colleague-NN_AND_TRUST_SIGNALS.md) — trust, deferred posture
- [WORKFLOW_DEFERRED_FOLLOWUPS.md](../WORKFLOW_DEFERRED_FOLLOWUPS.md) — backlog
