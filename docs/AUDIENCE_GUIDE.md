# Audience guide — what to read first

**Português (Brasil):** [AUDIENCE_GUIDE.pt_BR.md](AUDIENCE_GUIDE.pt_BR.md)

Navigation map for **thirteen** reader types. Full doc index: [README.md](README.md). Executive decks: [pitch/INDEX.md](pitch/INDEX.md).

---

## Executive / stakeholder

| | |
| - | - |
| **Entry** | [pitch/PITCH_STAKEHOLDER.md](pitch/PITCH_STAKEHOLDER.md) |
| **Trail** | [DECISION_MAKER_VALUE_BRIEF.md](DECISION_MAKER_VALUE_BRIEF.md) → [COMPLIANCE_AND_LEGAL.md](COMPLIANCE_AND_LEGAL.md) → [MAP.md](MAP.md) → [releases/](releases/) (shipped vs roadmap) |
| **Skip** | [USAGE.md](USAGE.md) flags, ADR index, maintainer ops runbooks |
| **Overlap** | DPO (legal summary); procurement (same brief) |

## DPO / privacy officer

| | |
| - | - |
| **Entry** | [pitch/PITCH_DPO.md](pitch/PITCH_DPO.md) |
| **Trail** | [COMPLIANCE_AND_LEGAL.md](COMPLIANCE_AND_LEGAL.md) → [COMPLIANCE_FRAMEWORKS.md](COMPLIANCE_FRAMEWORKS.md) → [MINOR_DETECTION.md](MINOR_DETECTION.md) → [JURISDICTION_COLLISION_HANDLING.md](JURISDICTION_COLLISION_HANDLING.md) |
| **Skip** | [TECH_GUIDE.md](TECH_GUIDE.md) unless integrating; engineering ADRs |
| **Overlap** | CISO ([SECURITY.md](SECURITY.md)); compliance engineer (framework samples) |

## CISO / security architect

| | |
| - | - |
| **Entry** | [pitch/PITCH_CISO.md](pitch/PITCH_CISO.md) |
| **Trail** | [SECURITY.md](SECURITY.md) → [COMPLIANCE_TECHNICAL_REFERENCE.md](COMPLIANCE_TECHNICAL_REFERENCE.md) → [GRC_EXECUTIVE_REPORT_SCHEMA.md](GRC_EXECUTIVE_REPORT_SCHEMA.md) → [adr/ADR-0039-retention-evidence-posture-bonded-customs-adjacent-contexts.md](adr/ADR-0039-retention-evidence-posture-bonded-customs-adjacent-contexts.md) |
| **Skip** | Academic primers; stakeholder-only pitch tone |
| **Overlap** | DPO (legal framing); developer (deploy hardening) |

## CDO / data steward / senior data engineer

| | |
| - | - |
| **Entry** | [pitch/PITCH_DATA_OFFICER.md](pitch/PITCH_DATA_OFFICER.md) |
| **Trail** | [GLOSSARY.md](GLOSSARY.md) (DMBOK §12) → [REPORTS_AND_COMPLIANCE_OUTPUTS.md](REPORTS_AND_COMPLIANCE_OUTPUTS.md) → [USAGE.md](USAGE.md) (targets) |
| **Skip** | Maintainer ops runbooks; board-only tone unless briefing executives |
| **Overlap** | CISO (evidence); DPO (sensitive-data classes); developer (connectors) |

## CIO / IT governance lead

| | |
| - | - |
| **Entry** | [pitch/PITCH_IT_GOVERNANCE.md](pitch/PITCH_IT_GOVERNANCE.md) |
| **Trail** | [DECISION_MAKER_VALUE_BRIEF.md](DECISION_MAKER_VALUE_BRIEF.md) → [GRC_EXECUTIVE_REPORT_SCHEMA.md](GRC_EXECUTIVE_REPORT_SCHEMA.md) → [COMPLIANCE_FRAMEWORKS.md](COMPLIANCE_FRAMEWORKS.md) |
| **Skip** | Detector internals unless the CIO is also the integrator |
| **Overlap** | CISO (controls); Executive (value brief); CDO (inventory) |

## PMO / project lead

| | |
| - | - |
| **Entry** | [pitch/PITCH_PMO.md](pitch/PITCH_PMO.md) |
| **Trail** | [GRC_EXECUTIVE_REPORT_SCHEMA.md](GRC_EXECUTIVE_REPORT_SCHEMA.md) → reports by **configured source/session** → [releases/](releases/) (shipped vs roadmap) |
| **Skip** | Engineering ADRs, [TECH_GUIDE.md](TECH_GUIDE.md) |
| **Overlap** | Executive (value brief); CISO (GRC schema) |

## CFO / financial C-level

| | |
| - | - |
| **Entry** | [pitch/PITCH_CFO.md](pitch/PITCH_CFO.md) |
| **Trail** | [DECISION_MAKER_VALUE_BRIEF.md](DECISION_MAKER_VALUE_BRIEF.md) → [SUBSCRIPTION_TIERS.md](SUBSCRIPTION_TIERS.md) → [LICENSING_OPEN_CORE_AND_COMMERCIAL.md](LICENSING_OPEN_CORE_AND_COMMERCIAL.md) → [releases/](releases/) |
| **Skip** | [TECH_GUIDE.md](TECH_GUIDE.md), technical compliance frameworks |
| **Overlap** | Executive (value brief); PMO (delivery vs cost) |

## CCO / General Counsel

| | |
| - | - |
| **Entry** | [pitch/PITCH_COMPLIANCE_OFFICER.md](pitch/PITCH_COMPLIANCE_OFFICER.md) |
| **Trail** | [COMPLIANCE_AND_LEGAL.md](COMPLIANCE_AND_LEGAL.md) → [COMPLIANCE_FRAMEWORKS.md](COMPLIANCE_FRAMEWORKS.md) |
| **Skip** | [TECH_GUIDE.md](TECH_GUIDE.md); do not confuse with DPO (operational LGPD) |
| **Overlap** | DPO (legal summary, distinct role); Executive (compliance posture) |

## Compliance engineer

| | |
| - | - |
| **Entry** | [COMPLIANCE_FRAMEWORKS.md](COMPLIANCE_FRAMEWORKS.md) |
| **Trail** | [compliance-samples/README.md](compliance-samples/README.md) → [COMPLIANCE_METHODOLOGY.md](COMPLIANCE_METHODOLOGY.md) → [REPORTS_AND_COMPLIANCE_OUTPUTS.md](REPORTS_AND_COMPLIANCE_OUTPUTS.md) → [use-cases/USE_CASES_HUB.md](use-cases/USE_CASES_HUB.md) |
| **Skip** | Root README marketing block (use frameworks doc instead) |
| **Overlap** | DPO (norm tags); CISO (security controls) |
| **Shipped** | Privacy management standards primer and primers hub — start at [hubs/INDEX.md](hubs/INDEX.md) (#589 and #593 closed) |

## Developer / integrator

| | |
| - | - |
| **Entry** | [USAGE.md](USAGE.md) |
| **Trail** | [ENTERPRISE_INTEGRATION_GUIDE.md](ENTERPRISE_INTEGRATION_GUIDE.md) → [TECH_GUIDE.md](TECH_GUIDE.md) → [DOCKER_SETUP.md](DOCKER_SETUP.md) → [deploy/DEPLOY.md](deploy/DEPLOY.md) → [SENSITIVITY_DETECTION.md](SENSITIVITY_DETECTION.md) → [PLUGIN_AUTHOR_GUIDE.md](PLUGIN_AUTHOR_GUIDE.md) |
| **Skip** | Pitch decks; board brief unless scoping a POC |
| **Overlap** | Compliance engineer (YAML profiles); operator (homelab smoke) |

## Academic / researcher

| | |
| - | - |
| **Entry** | [AI_EVOLUTION_PRIMER.md](primers/AI_EVOLUTION_PRIMER.md) |
| **Trail** | [philosophy/THE_WHY.md](philosophy/THE_WHY.md) → [TESTING_POC_GUIDE.md](TESTING_POC_GUIDE.md) → [COMPLIANCE_FRAMEWORKS.md](COMPLIANCE_FRAMEWORKS.md) (deterministic vs LLM section) → [GLOSSARY.md](GLOSSARY.md) |
| **Skip** | Sales pitch folder; day-to-day ops runbooks |
| **Overlap** | Compliance engineer (methodology); developer (test corpus) |

## Internal agent (Cursor / automation)

| | |
| - | - |
| **Entry** | [../AGENTS.md](../AGENTS.md) |
| **Trail** | [ops/OPERATOR_AGENT_COLD_START_LADDER.md](ops/OPERATOR_AGENT_COLD_START_LADDER.md) → [ops/CURSOR_AGENT_POLICY_HUB.md](ops/CURSOR_AGENT_POLICY_HUB.md) → [ops/TOKEN_AWARE_SCRIPTS_HUB.md](ops/TOKEN_AWARE_SCRIPTS_HUB.md) → [ops/COMMIT_AND_PR.md](ops/COMMIT_AND_PR.md) |
| **Skip** | Pitch decks unless the session is GTM; private paths stay gitignored |
| **Overlap** | Operator (rituals); maintainer plans via [README.md](README.md) *Internal and reference* |

## Operator (maintainer / SRE)

| | |
| - | - |
| **Entry** | [ops/README.md](ops/README.md) |
| **Trail** | [ops/today-mode/README.md](ops/today-mode/README.md) → [TESTING.md](TESTING.md) → [ops/HOMELAB_VALIDATION.md](ops/HOMELAB_VALIDATION.md) → [VERSIONING.md](VERSIONING.md) |
| **Skip** | Stakeholder pitch unless briefing someone else |
| **Overlap** | Developer (CLI); internal agent (same guardrails) |

---

## Overlap matrix (shared reads)

| Doc | Executive | DPO | CISO | CDO | CIO | Compliance | Developer | Academic | Agent | Operator | PMO | CFO | CCO |
| --- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| [DECISION_MAKER_VALUE_BRIEF.md](DECISION_MAKER_VALUE_BRIEF.md) | ● | ○ | ○ | ○ | ● | ○ | | | | | ○ | ● | |
| [COMPLIANCE_FRAMEWORKS.md](COMPLIANCE_FRAMEWORKS.md) | ○ | ● | ○ | ○ | ● | ● | ○ | ○ | | | | | ● |
| [SECURITY.md](SECURITY.md) | | ○ | ● | ○ | ○ | ○ | ● | | | ○ | | | |
| [USAGE.md](USAGE.md) | | ○ | ○ | ● | ○ | ○ | ● | | ○ | ● | | | |
| [ENTERPRISE_INTEGRATION_GUIDE.md](ENTERPRISE_INTEGRATION_GUIDE.md) | | | ○ | | ● | | ● | | ○ | ● | | | |
| [pitch/INDEX.md](pitch/INDEX.md) | ● | ● | ● | ● | ● | | | | | | ● | ● | ● |
| [GRC_EXECUTIVE_REPORT_SCHEMA.md](GRC_EXECUTIVE_REPORT_SCHEMA.md) | | | ○ | | ● | | | | | | ● | | |
| [LICENSING_OPEN_CORE_AND_COMMERCIAL.md](LICENSING_OPEN_CORE_AND_COMMERCIAL.md) | ○ | | | | | | | | | | | ● | |
| [COMPLIANCE_AND_LEGAL.md](COMPLIANCE_AND_LEGAL.md) | ○ | ● | | | | ○ | | | | | | | ● |
| [GLOSSARY.md](GLOSSARY.md) | | ○ | | ● | ○ | ○ | | ○ | | | | | |

● = primary trail · ○ = optional overlap

---

## Hubs index

The consolidated **map of maps** lives at [hubs/INDEX.md](hubs/INDEX.md). Also useful: [README.md](README.md), [pitch/INDEX.md](pitch/INDEX.md), and [use-cases/USE_CASES_HUB.md](use-cases/USE_CASES_HUB.md).
