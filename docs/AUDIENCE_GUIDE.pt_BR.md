# Guia de audiências — o que ler primeiro

**English:** [AUDIENCE_GUIDE.md](AUDIENCE_GUIDE.md)

Mapa de navegação para **onze** perfis de leitor. Índice completo: [README.md](README.md). Decks executivos: [pitch/INDEX.pt_BR.md](pitch/INDEX.pt_BR.md).

---

## Executivo / stakeholder

| | |
| - | - |
| **Entrada** | [pitch/PITCH_STAKEHOLDER.pt_BR.md](pitch/PITCH_STAKEHOLDER.pt_BR.md) |
| **Trilha** | [DECISION_MAKER_VALUE_BRIEF.pt_BR.md](DECISION_MAKER_VALUE_BRIEF.pt_BR.md) → [COMPLIANCE_AND_LEGAL.pt_BR.md](COMPLIANCE_AND_LEGAL.pt_BR.md) → [MAP.pt_BR.md](MAP.pt_BR.md) → [releases/](releases/) |
| **Evitar** | Flags de [USAGE.pt_BR.md](USAGE.pt_BR.md), índice de ADRs, runbooks de ops |
| **Sobreposição** | DPO (resumo jurídico); compras (mesmo brief) |

## DPO / encarregado de privacidade

| | |
| - | - |
| **Entrada** | [pitch/PITCH_DPO.pt_BR.md](pitch/PITCH_DPO.pt_BR.md) |
| **Trilha** | [COMPLIANCE_AND_LEGAL.pt_BR.md](COMPLIANCE_AND_LEGAL.pt_BR.md) → [COMPLIANCE_FRAMEWORKS.pt_BR.md](COMPLIANCE_FRAMEWORKS.pt_BR.md) → [MINOR_DETECTION.pt_BR.md](MINOR_DETECTION.pt_BR.md) → [JURISDICTION_COLLISION_HANDLING.pt_BR.md](JURISDICTION_COLLISION_HANDLING.pt_BR.md) |
| **Evitar** | [TECH_GUIDE.pt_BR.md](TECH_GUIDE.pt_BR.md) salvo integração; ADRs de engenharia |
| **Sobreposição** | CISO ([SECURITY.pt_BR.md](SECURITY.pt_BR.md)); engenheiro de compliance (amostras) |

## CISO / arquiteto de segurança

| | |
| - | - |
| **Entrada** | [pitch/PITCH_CISO.pt_BR.md](pitch/PITCH_CISO.pt_BR.md) |
| **Trilha** | [SECURITY.pt_BR.md](SECURITY.pt_BR.md) → [COMPLIANCE_TECHNICAL_REFERENCE.pt_BR.md](COMPLIANCE_TECHNICAL_REFERENCE.pt_BR.md) → [GRC_EXECUTIVE_REPORT_SCHEMA.pt_BR.md](GRC_EXECUTIVE_REPORT_SCHEMA.pt_BR.md) → [adr/ADR-0039-retention-evidence-posture-bonded-customs-adjacent-contexts.md](adr/ADR-0039-retention-evidence-posture-bonded-customs-adjacent-contexts.md) |
| **Evitar** | Primers acadêmicos; tom de pitch para conselho |
| **Sobreposição** | DPO (enquadramento legal); desenvolvedor (hardening de deploy) |

## PMO / líder de projeto

| | |
| - | - |
| **Entrada** | `pitch/PITCH_PMO.md` *(pitch planejado — #682)* |
| **Trilha** | [GRC_EXECUTIVE_REPORT_SCHEMA.pt_BR.md](GRC_EXECUTIVE_REPORT_SCHEMA.pt_BR.md) → heatmap / acompanhamento de sprint → [releases/](releases/) (entregue vs roadmap) |
| **Evitar** | ADRs de engenharia, [TECH_GUIDE.pt_BR.md](TECH_GUIDE.pt_BR.md) |
| **Sobreposição** | Executivo (value brief); CISO (schema GRC) |

## CFO / C-level financeiro

| | |
| - | - |
| **Entrada** | `pitch/PITCH_CFO.md` *(pitch planejado — #683)* |
| **Trilha** | [DECISION_MAKER_VALUE_BRIEF.pt_BR.md](DECISION_MAKER_VALUE_BRIEF.pt_BR.md) → [LICENSING_OPEN_CORE_AND_COMMERCIAL.pt_BR.md](LICENSING_OPEN_CORE_AND_COMMERCIAL.pt_BR.md) → [releases/](releases/) |
| **Evitar** | [TECH_GUIDE.pt_BR.md](TECH_GUIDE.pt_BR.md), frameworks técnicos de compliance |
| **Sobreposição** | Executivo (value brief); PMO (entrega vs custo) |

## CCO / jurídico (General Counsel)

| | |
| - | - |
| **Entrada** | `pitch/PITCH_COMPLIANCE_OFFICER.md` *(pitch planejado — #684)* |
| **Trilha** | [COMPLIANCE_AND_LEGAL.pt_BR.md](COMPLIANCE_AND_LEGAL.pt_BR.md) → [COMPLIANCE_FRAMEWORKS.pt_BR.md](COMPLIANCE_FRAMEWORKS.pt_BR.md) |
| **Evitar** | [TECH_GUIDE.pt_BR.md](TECH_GUIDE.pt_BR.md); não confundir com DPO (LGPD operacional) |
| **Sobreposição** | DPO (resumo jurídico, papel distinto); Executivo (postura de compliance) |

## Engenheiro de compliance

| | |
| - | - |
| **Entrada** | [COMPLIANCE_FRAMEWORKS.pt_BR.md](COMPLIANCE_FRAMEWORKS.pt_BR.md) |
| **Trilha** | [compliance-samples/README.md](compliance-samples/README.md) → [COMPLIANCE_METHODOLOGY.pt_BR.md](COMPLIANCE_METHODOLOGY.pt_BR.md) → [REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md](REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md) → [use-cases/USE_CASES_HUB.pt_BR.md](use-cases/USE_CASES_HUB.pt_BR.md) |
| **Evitar** | Bloco de marketing do README raiz |
| **Sobreposição** | DPO (tags de norma); CISO (controles) |
| **Planejado** | Primer de padrões de privacidade (**#589**); hub de primers (**#593**) |

## Desenvolvedor / integrador

| | |
| - | - |
| **Entrada** | [USAGE.pt_BR.md](USAGE.pt_BR.md) |
| **Trilha** | [TECH_GUIDE.pt_BR.md](TECH_GUIDE.pt_BR.md) → [DOCKER_SETUP.pt_BR.md](DOCKER_SETUP.pt_BR.md) → [deploy/DEPLOY.pt_BR.md](deploy/DEPLOY.pt_BR.md) → [SENSITIVITY_DETECTION.pt_BR.md](SENSITIVITY_DETECTION.pt_BR.md) |
| **Evitar** | Pasta pitch; brief de conselho salvo escopo de POC |
| **Sobreposição** | Compliance (perfis YAML); operador (smoke em homelab) |

## Acadêmico / pesquisador

| | |
| - | - |
| **Entrada** | [AI_EVOLUTION_PRIMER.pt_BR.md](primers/AI_EVOLUTION_PRIMER.pt_BR.md) |
| **Trilha** | [philosophy/THE_WHY.pt_BR.md](philosophy/THE_WHY.pt_BR.md) → [TESTING_POC_GUIDE.pt_BR.md](TESTING_POC_GUIDE.pt_BR.md) → [COMPLIANCE_FRAMEWORKS.pt_BR.md](COMPLIANCE_FRAMEWORKS.pt_BR.md) → [GLOSSARY.pt_BR.md](GLOSSARY.pt_BR.md) |
| **Evitar** | Pitch comercial; runbooks do dia a dia |
| **Sobreposição** | Compliance (metodologia); desenvolvedor (corpus de teste) |

## Agente interno (Cursor / automação)

| | |
| - | - |
| **Entrada** | [../AGENTS.md](../AGENTS.md) |
| **Trilha** | [ops/OPERATOR_AGENT_COLD_START_LADDER.pt_BR.md](ops/OPERATOR_AGENT_COLD_START_LADDER.pt_BR.md) → [ops/CURSOR_AGENT_POLICY_HUB.pt_BR.md](ops/CURSOR_AGENT_POLICY_HUB.pt_BR.md) → [ops/TOKEN_AWARE_SCRIPTS_HUB.pt_BR.md](ops/TOKEN_AWARE_SCRIPTS_HUB.pt_BR.md) → [ops/COMMIT_AND_PR.pt_BR.md](ops/COMMIT_AND_PR.pt_BR.md) |
| **Evitar** | Pitch salvo sessão GTM; `docs/private/` permanece fora do GitHub |
| **Sobreposição** | Operador (rituais); planos via [README.md](README.md) *Internal and reference* |

## Operador (mantenedor / SRE)

| | |
| - | - |
| **Entrada** | [ops/README.md](ops/README.md) |
| **Trilha** | [ops/today-mode/README.md](ops/today-mode/README.md) → [TESTING.pt_BR.md](TESTING.pt_BR.md) → [ops/HOMELAB_VALIDATION.pt_BR.md](ops/HOMELAB_VALIDATION.pt_BR.md) → [VERSIONING.md](VERSIONING.md) |
| **Evitar** | Pitch executivo salvo briefing a terceiros |
| **Sobreposição** | Desenvolvedor (CLI); agente (mesmos guardrails) |

---

## Matriz de sobreposição

| Doc | Executivo | DPO | CISO | Compliance | Dev | Acadêmico | Agente | Operador | PMO | CFO | CCO |
| --- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| [DECISION_MAKER_VALUE_BRIEF.pt_BR.md](DECISION_MAKER_VALUE_BRIEF.pt_BR.md) | ● | ○ | ○ | ○ | | | | | ○ | ● | |
| [COMPLIANCE_FRAMEWORKS.pt_BR.md](COMPLIANCE_FRAMEWORKS.pt_BR.md) | ○ | ● | ○ | ● | ○ | ○ | | | | | ● |
| [SECURITY.pt_BR.md](SECURITY.pt_BR.md) | | ○ | ● | ○ | ● | | | ○ | | | |
| [USAGE.pt_BR.md](USAGE.pt_BR.md) | | ○ | ○ | ○ | ● | | ○ | ● | | | |
| [pitch/INDEX.pt_BR.md](pitch/INDEX.pt_BR.md) | ● | ● | ● | | | | | | ● | ● | ● |
| [GRC_EXECUTIVE_REPORT_SCHEMA.pt_BR.md](GRC_EXECUTIVE_REPORT_SCHEMA.pt_BR.md) | | | ○ | | | | | | ● | | |
| [LICENSING_OPEN_CORE_AND_COMMERCIAL.pt_BR.md](LICENSING_OPEN_CORE_AND_COMMERCIAL.pt_BR.md) | ○ | | | | | | | | | ● | |
| [COMPLIANCE_AND_LEGAL.pt_BR.md](COMPLIANCE_AND_LEGAL.pt_BR.md) | ○ | ● | | ○ | | | | | | | ● |

● = trilha principal · ○ = sobreposição opcional

---

## Índice de hubs

O **mapa de mapas** consolidado fica em [hubs/INDEX.md](hubs/INDEX.md). Também úteis: [README.md](README.md), [pitch/INDEX.pt_BR.md](pitch/INDEX.pt_BR.md) e [use-cases/USE_CASES_HUB.pt_BR.md](use-cases/USE_CASES_HUB.pt_BR.md).
