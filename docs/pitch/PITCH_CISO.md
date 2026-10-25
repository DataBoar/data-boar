# CISO pitch — security and GRC leadership

**Português (Brasil):** [PITCH_CISO.pt_BR.md](PITCH_CISO.pt_BR.md) · **Index:** [INDEX.md](INDEX.md)

**Audience:** CISOs, security architects, GRC leads integrating discovery into control programmes.

---

## Security value proposition

Data Boar reduces **unknown personal-data sprawl** before it becomes incident material. The **hero** for security leadership is **evidence automation**: repeatable, **session-bound** technical artefacts (XLSX, optional scan-manifest YAML, audit JSON, GRC executive JSON)—not a replacement for SIEM, DLP, IAM, or vulnerability management, and not a promise to auto-close tickets.

Public security posture: [SECURITY.md](../SECURITY.md).

## Language for the CFO in the same room

Do **not** hardcode vendor **cost-of-breach dollar** figures in a CISO briefing. Use **statutory shape**: administrative fines as a **percentage of revenue** (or turnover) **with a cap** — **LGPD Art. 52**, **GDPR Art. 83**. Public **IBM Cost of a Data Breach** reports are an **external** benchmark: name the source, skip year-locked USD. Shared responsibility: discovery evidence does **not** erase regulatory exposure. Finance-shaped deck: [PITCH_CFO.md](PITCH_CFO.md).

## KPIs the product already delivers

| KPI | What you can show today |
| --- | ----------------------- |
| Heatmap / findings | **By configured source and scan session** — not by team, sprint, or git repo until GitHub [#677](https://github.com/DataBoar/data-boar/issues/677) |
| Trend | Session-over-session on the **same** target set |
| Coverage | **Configured targets** in scope — not CMDB completeness |

## Emerging vector: repository / supply-chain discovery

Git and similar VCS targets are an **emerging** evidence path (connector dogfood tracked as GitHub [#677](https://github.com/DataBoar/data-boar/issues/677)). Brief it as a **future control conversation**, not a shipped heatmap-by-repo-sprint.

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
- **PMO cadence:** [PITCH_PMO.md](PITCH_PMO.md)
- **Finance exposure:** [PITCH_CFO.md](PITCH_CFO.md)
- **Counsel / CCO:** [PITCH_COMPLIANCE_OFFICER.md](PITCH_COMPLIANCE_OFFICER.md)
- **Technical reference:** [COMPLIANCE_TECHNICAL_REFERENCE.md](../COMPLIANCE_TECHNICAL_REFERENCE.md)
