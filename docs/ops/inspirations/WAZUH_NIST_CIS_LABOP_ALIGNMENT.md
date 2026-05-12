# Wazuh docs, NIST CSF, CIS Controls — lab-op learning and Data Boar alignment

**Português (Brasil):** [WAZUH_NIST_CIS_LABOP_ALIGNMENT.pt_BR.md](WAZUH_NIST_CIS_LABOP_ALIGNMENT.pt_BR.md)

**Source note:** stable **primary** documentation only (no social reposts or vendor template bundles as policy). Use this when planning **LAB-OP** / homelab monitoring and when **buyers** ask how Data Boar sits next to framework language.

---

## Official Wazuh documentation (orientation)

**Entry points:**

- [Getting started](https://documentation.wazuh.com/current/getting-started/index.html)
- [Components](https://documentation.wazuh.com/current/getting-started/components/index.html) — **Wazuh indexer**, **Wazuh server**, **Wazuh dashboard**, **Wazuh agent**
- [Installation guide](https://documentation.wazuh.com/current/installation-guide/index.html)
- [Deployment options](https://documentation.wazuh.com/current/deployment-options/index.html) — Docker, Kubernetes, Ansible, offline, etc.

**Use-case chapters that overlap Data Boar / lab concerns** (SIEM-style platform, not our product):

- [File integrity monitoring](https://documentation.wazuh.com/current/getting-started/use-cases/file-integrity.html)
- [Log data analysis](https://documentation.wazuh.com/current/getting-started/use-cases/log-analysis.html)
- [Vulnerability detection](https://documentation.wazuh.com/current/getting-started/use-cases/vulnerability-detection.html)
- [Incident response](https://documentation.wazuh.com/current/getting-started/use-cases/incident-response.html)
- [Regulatory compliance](https://documentation.wazuh.com/current/getting-started/use-cases/regulatory-compliance.html)
- [Container security](https://documentation.wazuh.com/current/getting-started/use-cases/container-security.html)
- [Posture management](https://documentation.wazuh.com/current/getting-started/use-cases/posture-management.html)

**Lab-op habit:** follow the **version** you install, prefer **TLS** and **least privilege** per Wazuh’s own guides; keep host-specific inventory under **gitignored** `docs/private/homelab/` (see **`AGENTS.md`**). **`scripts/lab-op-sync-and-collect.ps1`** is the repo’s batch path when a manifest exists — it does not replace reading the Wazuh install docs.

---

## NIST Cybersecurity Framework (CSF) 2.0 — how we can use the vocabulary

**Canonical reference:** [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework) (CSF 2.0 adds explicit **Govern** alongside Identify, Protect, Detect, Respond, Recover).

| CSF function | In this repository / operator practice | Product scope (Data Boar) |
| ------------ | -------------------------------------- | ------------------------- |
| **Govern** | ADRs, review discipline, branch protection backlog ([WORKFLOW_DEFERRED_FOLLOWUPS.md](../WORKFLOW_DEFERRED_FOLLOWUPS.md)) | Honest claims in [SECURITY.md](../../SECURITY.md) / [COMPLIANCE_AND_LEGAL.md](../../COMPLIANCE_AND_LEGAL.md) |
| **Identify** | Lockfile, Dependabot, SBOM roadmap ([ADR 0003](../../adr/ADR-0003-sbom-roadmap-cyclonedx-then-syft.md)) | Evidence for **data** and sensitive-content discovery — not full enterprise asset inventory |
| **Protect** | SHA-pinned Actions ([ADR 0005](../../adr/ADR-0005-ci-github-actions-supply-Colleague-Nn-pins.md)), minimal workflow permissions | Secure deployment guidance; customers still own their environment hardening |
| **Detect** | CI + Semgrep/CodeQL, optional Slack on failure | Scanner output; **not** a 24×7 SOC |
| **Respond** | Ecosystem incident checklist ([SUPPLY_Colleague-NN_AND_TRUST_SIGNALS.md](SUPPLY_Colleague-NN_AND_TRUST_SIGNALS.md) deferred block) | Customer runbooks stay customer-owned |
| **Recover** | **Tested** backup/restore for lab-op state (deferred process; see same deferred block) | Same — operational resilience is deployment-specific |

Use CSF language in **sales/engineering** conversations to **position** controls we actually implement; avoid implying **certification** or full CSF coverage unless you have an explicit compliance program.

---

## CIS Controls — prioritization lens

**Canonical reference:** [CIS Controls](https://www.cisecurity.org/controls) (prioritized safeguards; useful for **lean** teams to avoid scatter).

**Rough alignment (examples, not a certification mapping):**

- **Inventory and control of enterprise assets / software** → dependency and image inventory ([ADR 0003](../../adr/ADR-0003-sbom-roadmap-cyclonedx-then-syft.md), `uv.lock`, Dependabot).
- **Secure configuration** → hardened hosts in lab-op; Wazuh **configuration assessment** use case as a **check**, not a product feature of Data Boar.
- **Audit log management** → Wazuh in lab-op for central review; application logging for Data Boar deployments is operator-owned.
- **Malware defenses** → endpoint/tooling on maintainer workstations and servers; outside core repo scope unless documented.

---

## Related in-repo

- [LAB_OP_OBSERVABILITY_LEARNING_LINKS.md](LAB_OP_OBSERVABILITY_LEARNING_LINKS.md) — Grafana / Loki / Graylog / OpenSearch / traces / Dynatrace-style alternatives (lab-op bookmarks)
- [SUPPLY_Colleague-NN_AND_TRUST_SIGNALS.md](SUPPLY_Colleague-NN_AND_TRUST_SIGNALS.md) — trust, supply Colleague-Nn, deferred posture
- [ENTERPRISE_DB_OPS_AND_GRC_EVIDENCE.md](ENTERPRISE_DB_OPS_AND_GRC_EVIDENCE.md) — database operations culture vs **GRC spreadsheet** evidence slots (Data Boar exports)
- [WORKFLOW_DEFERRED_FOLLOWUPS.md](../WORKFLOW_DEFERRED_FOLLOWUPS.md) — backlog row for this track
- [HOMELAB_VALIDATION.md](../HOMELAB_VALIDATION.md) — optional second-environment smoke (when applicable)
