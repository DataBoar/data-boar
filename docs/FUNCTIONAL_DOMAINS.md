# Functional Domains — Data Boar

**Português (Brasil):** [FUNCTIONAL_DOMAINS.pt_BR.md](FUNCTIONAL_DOMAINS.pt_BR.md)

## Purpose and terminology

Canonical map of Data Boar's functional domains. It connects stable product responsibilities to capabilities, use cases, sector storyboards, governance references, and tracked discovery work. It is a navigation/classification document, not an implementation specification, feature commitment, legal opinion, or proof that every mapped capability is shipped.

- **Functional domain:** stable responsibility/problem area the operator investigates or evidences.
- **Capability:** product behavior or documented workflow supporting one or more domains.
- **Vertical / sector:** industry or operating context combining several domains.
- **Use case:** concrete workflow or scenario.
- **GRC domain/framework:** external governance/control lens; it does not define product architecture.

## Product boundary

Data Boar is a deterministic data-discovery, sensitivity-mapping, and evidence instrument. Detection output is an input to human assessment; it does not independently establish legal roles, lawful basis, purpose, contractual obligations, regulatory compliance, or complete coverage.

Organize the product around capabilities and their contracts, not industries, legal frameworks, or sales taxonomy. Vertical packs may compose existing capabilities, validated configuration, synthetic fixtures, and evidence examples. They must not create product forks or imply unsupported behavior.

## Canonical functional domains

| ID | Domain | Operator question | Relevant product surfaces |
| --- | --- | --- | --- |
| FD-01 | **Data discovery & inventory** | What data-bearing assets and sources exist within the authorized scope? | Supported file/database/connectors, target and scope configuration, scan manifests, [USAGE.md](USAGE.md) |
| FD-02 | **Sensitivity detection & classification signals** | Which locations may contain personal, sensitive, confidential, or security-relevant data? | Deterministic patterns and supported detection stages, sensitivity findings, [SENSITIVITY_DETECTION.md](SENSITIVITY_DETECTION.md), [MINOR_DETECTION.md](MINOR_DETECTION.md) |
| FD-03 | **Context, provenance & custody** | Where did a finding come from, under what scope, and what custody context is known? | Session/target metadata, manifests, source attribution, report provenance; custody categories are not automatically inferred |
| FD-04 | **Risk & compliance evidence mapping** | Which findings may be relevant to a risk, obligation, framework, or review question? | Findings, calibrated risk-state vocabulary, framework overlays and evidence references; no automatic compliance verdict |
| FD-05 | **Evidence, reporting & controlled disclosure** | What can be demonstrated and safely shared with an auditor, customer, DPO, or security reviewer? | Reports, manifests, tokenized findings, metadata-only summaries, [REPORTS_AND_COMPLIANCE_OUTPUTS.md](REPORTS_AND_COMPLIANCE_OUTPUTS.md) |
| FD-06 | **Remediation prioritization & hand-off** | What should a responsible operator review or remediate, and how can hand-off be evidenced? | Remediation-oriented priorities, action inventory, plugin/interface work; Data Boar does not silently modify source systems |
| FD-07 | **Processing governance & authorization boundaries** | Who authorized this activity, for which scope, and which parties/systems may access resulting artifacts? | Operator-declared scope, service/deployment boundaries, RBAC where implemented, non-transitive consent guardrail (#16); engagement-context model under investigation in [#2323](https://github.com/DataBoar/data-boar/issues/2323) |
| FD-08 | **Deployment, integration & operational assurance** | Where does the scanner run, which systems can it reach, and what data crosses each boundary? | On-prem and supported deployment modes, connectors/plugins, logs/telemetry/support boundaries, release and operational evidence; [ENTERPRISE_INTEGRATION_GUIDE.md](ENTERPRISE_INTEGRATION_GUIDE.md), [#2324](https://github.com/DataBoar/data-boar/issues/2324) |

Domains intentionally overlap. One scan can contribute to discovery, classification, provenance, risk review, reporting, and remediation hand-off. They are not mandatory sequential modules.

## Sector / operating-context crosswalk

A vertical is a composition of functional domains, not a new architecture. This crosswalk is a navigation aid; it does not assert that every sector-specific detector, connector, legal control, or workflow is implemented.

| Vertical / context | Primary domains | Existing storyboard |
| --- | --- | --- |
| Port, logistics & multinational workforce | FD-01, FD-02, FD-03, FD-04, FD-05 | [Port logistics](use-cases/PORT_LOGISTICS_MULTINATIONAL_CREW.md) |
| Law firms & client matters | FD-01, FD-02, FD-03, FD-05, FD-07 | [Law firms](use-cases/LAW_FIRM_CLIENT_MATTER_AND_TRUST_DATA.md) |
| Accounting, payroll, tax & ledger | FD-01, FD-02, FD-04, FD-05, FD-06 | [Accounting](use-cases/ACCOUNTING_FIRM_PAYROLL_TAX_AND_LEDGER.md) |
| Pharma, hospitals & patient programs | FD-01, FD-02, FD-03, FD-04, FD-05 | [Pharma](use-cases/PHARMA_SPECIALTY_SALES_HOSPITALS_AND_PATIENT_PROGRAMS.md) |
| MSP / MSSP / IT consultancy | FD-01, FD-03, FD-05, FD-07, FD-08 | [MSP](use-cases/MSP_IT_CONSULTANCY_MULTI_TENANT_SMB.md) |
| Insurance broker & benefits administration | FD-01, FD-02, FD-03, FD-04, FD-05 | [Insurance](use-cases/INSURANCE_BROKER_AND_BENEFITS_ADMIN.md) |
| RPO, HR operations & payroll bureau | FD-01, FD-02, FD-03, FD-04, FD-05, FD-07 | [RPO](use-cases/RPO_PEOPLE_OPS_AND_PAYROLL_BUREAU.md) |
| Real estate & condominium management | FD-01, FD-02, FD-04, FD-05, FD-06 | [Real estate](use-cases/REAL_ESTATE_AND_CONDOMINIUM_MANAGEMENT.md) |
| NGOs & humanitarian records | FD-01, FD-02, FD-03, FD-04, FD-05, FD-07 | [NGO](use-cases/NGO_MIGRANT_WELCOME_AND_HUMANITARIAN_FILES.md) |
| EdTech, LMS & minors | FD-01, FD-02, FD-03, FD-04, FD-05, FD-07 | [EdTech](use-cases/EDTECH_LMS_EXPORTS_AND_MINORS.md) |
| Backup & data-protection estate | FD-01, FD-03, FD-04, FD-05, FD-08 | [Backup](use-cases/BACKUP_AND_DATA_PROTECTION_ESTATE_CRITICALITY.md) |
| Providers processing entrusted client data | FD-01, FD-02, FD-03, FD-04, FD-05, FD-07, FD-08 | [Entrusted Client Data Governance](use-cases/USE_CASE_ENTRUSTED_CLIENT_DATA_GOVERNANCE.md), tracked by [#2321](https://github.com/DataBoar/data-boar/issues/2321) |

Biometrics is a sensitive-data category/cross-cutting concern, not an industry vertical: [biometric data use case](use-cases/USE_CASE_BIOMETRIC_DATA_PROTECTION.md). Scan → remediate → prove and tokenized findings are horizontal workflows applicable across verticals: [scan and remediate](use-cases/USE_CASE_SCAN_AND_REMEDIATE.md), [tokenized findings](use-cases/USE_CASE_TOKENIZED_FINDINGS.md).

## GRC taxonomy relationship

Use external GRC domains/frameworks as a coverage lens to identify stakeholder questions, evidence gaps, partner research, and vertical opportunities. Do not use a GRC domain list as internal product decomposition, feature hierarchy, or Bestial/agent architecture. Map framework overlays to the functional domains above. A finding may support an assessment; it is not itself a control test, legal conclusion, audit opinion, or certification.

## Service-provider custody: cross-cutting scenario

**Entrusted Client Data Governance** describes providers whose own operational environment receives, stores, accesses, transforms, transmits, or analyzes client data. It is distinct from an MSP scanning client-controlled environments, managed/SaaS deployment, and the generic scan → remediation workflow.

Related tracked work:
- [#2321](https://github.com/DataBoar/data-boar/issues/2321) — use-case documentation.
- [#2322](https://github.com/DataBoar/data-boar/issues/2322) — service-provider commercial positioning.
- [#2323](https://github.com/DataBoar/data-boar/issues/2323) — engagement context, provenance, and evidence-boundary research.
- [#2324](https://github.com/DataBoar/data-boar/issues/2324) — NDA/DPA readiness and processing posture.
- [#2325](https://github.com/DataBoar/data-boar/issues/2325) — Trust Overview & Assurance Index.

Custody labels (provider-owned, entrusted-client, subprocessor, unknown/unclassified) are contextual and declarative. Do not infer legal roles from business label, tenant name, vertical, or deployment mode. Do not treat tenant_name as tenant isolation, or consent to Data Boar as consent for other Bestials.

## Capability and claim discipline

For every domain/vertical distinguish: **implemented and evidenced** (code/tests/release/operational evidence); **configurable today** (accepted by current schema and validated); **documented workflow** (operator process, not necessarily enforced); **research/proposal** (unvalidated); and **not determined by Data Boar** (legal roles, lawful basis, purpose, retention obligations, completeness, regulatory compliance, independent assurance conclusions).

Never turn a storyboard, pitch, plan, ADR, issue, or sample into proof of implementation. Executable config samples must validate against the current schema. Use synthetic data only.

## Navigation and maintenance

- This file is the canonical functional-domain map.
- [USE_CASES_HUB.md](use-cases/USE_CASES_HUB.md) indexes product workflows.
- [Use-case storyboards](use-cases/README.md) index sector narratives.
- [Pitch index](pitch/INDEX.md) contains audience-facing positioning.
- [Compliance and legal](COMPLIANCE_AND_LEGAL.md) and [framework coverage](COMPLIANCE_FRAMEWORKS.md) describe external governance context.
- [Navigation hubs](hubs/INDEX.md) are the agent-oriented map of maps.

When adding a vertical/use case, map it to existing FD IDs first. Propose a new domain only when a stable product responsibility cannot fit the current set. Update EN and pt-BR together and run documentation link/hub checks.
