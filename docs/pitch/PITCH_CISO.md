# CISO pitch — security and GRC leadership

**Português (Brasil):** [PITCH_CISO.pt_BR.md](PITCH_CISO.pt_BR.md) · **Index:** [INDEX.md](INDEX.md)

**Audience:** CISOs, security architects, GRC leads integrating discovery into control programmes.

---

## Security value proposition

Data Boar reduces **unknown personal-data sprawl** before it becomes incident material. It produces **repeatable, session-bound** technical evidence—not a replacement for SIEM, DLP, IAM, or vulnerability management.

Public security posture: [SECURITY.md](../SECURITY.md).

## Controls you care about

| Control theme | How the product supports it |
| ------------- | --------------------------- |
| **Least privilege** | Connectors use credentials you approve; scope targets explicitly—[ops/OPERATOR_IT_REQUIREMENTS.md](../ops/OPERATOR_IT_REQUIREMENTS.md) |
| **Evidence integrity** | Structured outputs (XLSX, optional manifest YAML, audit JSON) for repeatability—not silent mutation of findings |
| **Deterministic detection** | Regex + named patterns + supervised ML on configured terms—auditable stack vs generative drift—[COMPLIANCE_FRAMEWORKS.md](../COMPLIANCE_FRAMEWORKS.md#deterministic-detection-vs-generative-llm-hype) |
| **Biometric / special-category awareness** | Dedicated use-case narrative when enabled—[use-cases/USE_CASE_BIOMETRIC_DATA_PROTECTION.md](../use-cases/USE_CASE_BIOMETRIC_DATA_PROTECTION.md) |

## Integration posture

- **Deploy:** Docker images, compose samples, homelab validation paths—[DOCKER_SETUP.md](../DOCKER_SETUP.md), [deploy/DEPLOY.md](../deploy/DEPLOY.md).
- **Executive JSON:** [GRC_EXECUTIVE_REPORT_SCHEMA.md](../GRC_EXECUTIVE_REPORT_SCHEMA.md) for risk-matrix style dashboards (contract for downstream PDF/BI tools).
- **Open-core boundary:** core discovery and reporting in-repo; treat **enterprise-only** connectors and hardening as your procurement discussion—not assumed in public docs.

## Operating the tool safely

1. Run first in **non-production** or read-only accounts where possible.
2. Cap sampling and timeouts per target class—document bounds in the manifest.
3. Store credentials in vault/session env patterns—not in tracked config repos.
4. Pair outputs with your existing **ticketing** and **remediation** owners—storyboard: [use-cases/USE_CASE_SCAN_AND_REMEDIATE.md](../use-cases/USE_CASE_SCAN_AND_REMEDIATE.md).

## What to ask the DPO in the same room

- Which **norm profile** is authoritative for this business unit?
- Which findings require **legal** review before remediation tickets?
- Are **minor-related** columns in scope for this sprint?

## Next step

- **Board narrative:** [PITCH_STAKEHOLDER.md](PITCH_STAKEHOLDER.md)
- **Privacy narrative:** [PITCH_DPO.md](PITCH_DPO.md)
- **Technical reference:** [COMPLIANCE_TECHNICAL_REFERENCE.md](../COMPLIANCE_TECHNICAL_REFERENCE.md)
