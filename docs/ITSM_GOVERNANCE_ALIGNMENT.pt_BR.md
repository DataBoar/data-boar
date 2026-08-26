# Alinhamento de governança de TI e gerenciamento de serviços

**English:** [ITSM_GOVERNANCE_ALIGNMENT.md](ITSM_GOVERNANCE_ALIGNMENT.md)

**Público-alvo:** DPO, CISO, diretor de TI, auditor externo, consultor de GRC.

**Versão técnica:** [COMPLIANCE_FRAMEWORKS.pt_BR.md](COMPLIANCE_FRAMEWORKS.pt_BR.md) ([EN](COMPLIANCE_FRAMEWORKS.md))

**Schema do relatório GRC:** [GRC_EXECUTIVE_REPORT_SCHEMA.pt_BR.md](GRC_EXECUTIVE_REPORT_SCHEMA.pt_BR.md) ([EN](GRC_EXECUTIVE_REPORT_SCHEMA.md))

**Nota:** Este documento é referência conceitual e de posicionamento. **Não** constitui auditoria certificada nem parecer jurídico.

---

## 1. Data Boar e a criação sustentável de valor em ITSM

### 1.1 O que é "valor" no contexto de gerenciamento de serviços

O ITIL 4 define valor como **cocriação** entre provedor e cliente:

> Valor = Utilidade (fit for purpose) + Garantia (fit for use)

No contexto Data Boar:

- **Utilidade:** detecta PII/dados sensíveis onde a organização não enxergava.
- **Garantia:** execução reproduzível, trilha de auditoria imutável, resultados rastreáveis por sessão.
- **Cocriação:** o achado técnico só tem valor quando traduzido para linguagem de negócio e ação de controle.

### 1.2 Criação de valor sustentável — o ciclo

```text
Planejar → Executar → Medir → Melhorar → (loop)
```

O scan pontual (auditoria anual) cria valor efêmero. O ciclo sustentável:

1. **Planejar:** definir escopo de targets, perfil de compliance, SLA de resposta.
1. **Executar:** Data Sniffing + Deep Boring (sessão de scan).
1. **Medir:** relatório GRC — achados × controles × frameworks.
1. **Melhorar:** comparar sessões (`--diff`), fechar gaps, re-escanear.
1. **Voltar ao 1** com escopo ampliado.

---

## 2. Alinhamento por framework

### 2.1 ABNT NBR ISO/IEC 38500 — Governança de TI

A norma estabelece **6 princípios** avaliados pelo conselho/diretoria. O Data Boar contribui com **evidência** nos seguintes (o produto **não** certifica conformidade do conselho):

| Princípio                | Como o Data Boar contribui                                                  | Artefato de evidência                            |
| ---------                | --------------------------                                                  | ---------------------                            |
| **Responsabilidade**     | Identifica targets sem responsável formal de dado (gap de CMDB)             | Findings com `target_name` sem owner documentado |
| **Estratégia**           | Baseline de exposição de PII para decisões de investimento em segurança     | Relatório GRC com heatmap e trend                |
| **Desempenho**           | Mede evolução da postura entre sessões (diff de findings)                   | `--diff session_a session_b`                     |
| **Conformidade**         | Evidência de achados em desacordo com LGPD Arts. 46–47 (quando configurado) | `norm_tag` por finding + Governance Lens         |
| **Comportamento humano** | Identifica dados pessoais em ambientes de dev/QA (gap de política)          | Findings em targets `nonprod`                    |

### 2.2 ABNT NBR ISO/IEC 27014 — Governança da segurança da informação

Os 5 processos de governança e onde o Data Boar atua:

| Processo      | Contribuição Data Boar                                                                     |
| --------      | ----------------------                                                                     |
| **Avaliar**   | Inventário automatizado de exposição de PII — baseline para avaliação de risco             |
| **Dirigir**   | Relatório GRC com gaps de controle → insumo para política de dados de teste e mascaramento |
| **Monitorar** | Scan contínuo (agendado) + comparação entre sessões                                        |
| **Comunicar** | Governance Lens: traduz achados técnicos para linguagem de DPO e diretoria                 |
| **Assegurar** | Trilha de auditoria imutável (Audit Trail) exportável como evidência para auditor externo  |

### 2.3 COBIT 2019 — Objetivos de controle relevantes

#### APO13 — Gerenciar segurança

| Prática COBIT                         | Contribuição                                                   |
| -------------                         | ------------                                                   |
| APO13.01 Estabelecer SGSI             | Baseline de achados como ponto de partida formal para SGSI     |
| APO13.02 Plano de tratamento de risco | Roadmap de remediação no relatório GRC com prazo e responsável |
| APO13.03 Monitorar e revisar SGSI     | Scan recorrente + diff de sessões                              |

#### DSS05 — Gerenciar serviços de segurança

| Prática COBIT                              | Contribuição                                                          |
| -------------                              | ------------                                                          |
| DSS05.02 Segurança de rede e conectividade | Achados em APIs sem autenticação evidenciada (quando no escopo)       |
| DSS05.04 Identidade e acesso               | PII em ambientes não produtivos sem controle equivalente ao produtivo |
| DSS05.07 Monitorar eventos de segurança    | Integração do scan ao pipeline CI/CD                                  |

#### MEA03 — Monitorar, avaliar e assegurar conformidade

| Prática COBIT                                   | Contribuição                                                                         |
| -------------                                   | ------------                                                                         |
| MEA03.01 Identificar requisitos de conformidade | `norm_tag` mapeado por finding (LGPD, GDPR, CCPA, BACEN, PCI-DSS quando configurado) |
| MEA03.04 Obter garantia de conformidade         | Audit Trail + relatório GRC como artefato formal de evidência                        |

### 2.4 ITIL 4 — Prática de gerenciamento de segurança da informação

| Atividade ITIL 4                               | Contribuição Data Boar                                                                               |
| ----------------                               | ----------------------                                                                               |
| Identificar e classificar ativos de informação | Inventário de targets com achados por tipo de PII                                                    |
| Classificar e tratar riscos                    | Matriz de risco no relatório GRC (P0/P1/P2 + referência de framework)                                |
| Controlar acesso à informação                  | Gap: evidencia targets sem documentação de controle de acesso                                        |
| Responder a incidentes                         | Achados com LGPD Art. 48 (`norm_tag`, quando configurado) como pré-aviso de obrigação de notificação |
| Melhorar continuamente                         | Diff entre sessões (`--diff`) mostra evolução da postura                                             |

#### Mapeamento para a Service Value Chain (SVC)

| Atividade SVC       | Papel Data Boar                                                      |
| -------------       | ---------------                                                      |
| Engage              | `--validate-config` — o operador valida a configuração antes do scan |
| Design & Transition | Governance Lens define controles-alvo para cada tipo de achado       |
| Deliver & Support   | Scan contínuo como serviço gerenciado de monitoramento de PII        |
| Improve             | Diff de sessões + trending no relatório                              |

### 2.5 ABNT NBR ISO/IEC 20000-1 — Gerenciamento de serviços de TI

| Seção ISO 20000               | Contribuição                                                                    |
| ---------------               | ------------                                                                    |
| Gerenciamento do conhecimento | Findings exportados para CMDB/DB corporativo (findings sink, quando licenciado) |
| Gerenciamento de configuração | Identifica ICs (targets) sem atributos de segurança no CMDB                     |
| Gerenciamento de mudanças     | Diff de sessões antes/depois de mudanças em produção                            |

### 2.6 BACEN Resolução 4.893/2021 (Pro/Enterprise — fintech BR)

Referência: [SENSITIVITY_DETECTION.pt_BR.md](SENSITIVITY_DETECTION.pt_BR.md) e mapas Governance Lens **Enterprise** (curados; não são Open Core).

| Artigo BACEN (como citado em workshops)         | Contribuição                                                  |
| ---------------------------------------         | ------------                                                  |
| Art. 4º — Política de segurança cibernética     | Baseline de achados como insumo para política                 |
| Art. 6º — Plano de ação e resposta a incidentes | Achados com PII em API/DB não produtivo como gatilho de plano |
| Art. 11º — Comunicação de incidentes ao BACEN   | Audit Trail como evidência de detecção e resposta             |

---

## 3. Posicionamento para cada audiência

### Para o conselho / diretoria (ISO 38500)

> O Data Boar fornece evidência técnica periódica de conformidade com os princípios de governança de TI — especificamente Responsabilidade, Conformidade e Desempenho — sem substituir o programa formal de governança.

### Para o DPO / CISO (ISO 27014 + LGPD)

> Cada sessão de scan produz um relatório GRC com gaps de controle mapeados para ISO 27014, COBIT DSS05 e artigos LGPD relevantes (quando rotulados) — insumo direto para o processo de Avaliar e Comunicar da governança de SI.

### Para o auditor externo (COBIT MEA03)

> A Audit Trail imutável e o schema GRC estável ([GRC_EXECUTIVE_REPORT_SCHEMA.pt_BR.md](GRC_EXECUTIVE_REPORT_SCHEMA.pt_BR.md)) permitem que o auditor rastreie achados até controles COBIT e artigos regulatórios — sem dependência de interpretação manual de logs.

### Para o gerente de TI / ITSM (ITIL 4 + ISO 20000)

> O scan recorrente fecha o ciclo ITIL 4 de melhoria contínua: Entregar → Medir (relatório GRC) → Melhorar (fechar gaps) → re-Entregar com postura aprimorada.

---

## 4. Outputs do Data Boar mapeados por audiência

| Output                          | Formato              | Audiência principal                  | Framework de referência      |
| ------                          | -------              | -------------------                  | -----------------------      |
| Relatório GRC (Governance Lens) | DOCX / ODT / PDF     | DPO, CISO, auditor                   | ISO 27014, COBIT APO13/DSS05 |
| Excel com heatmap               | XLSX / ODS           | Gerente de TI, analista de segurança | ISO 20000, ITIL 4            |
| Audit Trail exportável          | JSON / YAML          | Auditor externo, jurídico            | ISO 38500, COBIT MEA03       |
| Findings sink (DB corporativo)  | PostgreSQL / MongoDB | Equipe de dados, time de CMDB        | ISO 20000 — configuração     |
| Export DSAR                     | JSON estruturado     | DPO, jurídico                        | LGPD Art. 18, GDPR Art. 15   |

---

## 5. Recursos relacionados

- [COMPLIANCE_FRAMEWORKS.pt_BR.md](COMPLIANCE_FRAMEWORKS.pt_BR.md) — frameworks regulatórios (LGPD, GDPR, CCPA)
- [COMPLIANCE_AND_LEGAL.pt_BR.md](COMPLIANCE_AND_LEGAL.pt_BR.md) — postura legal (não é aconselhamento jurídico)
- [GRC_EXECUTIVE_REPORT_SCHEMA.pt_BR.md](GRC_EXECUTIVE_REPORT_SCHEMA.pt_BR.md) — schema JSON do relatório GRC
- [DECISION_MAKER_VALUE_BRIEF.pt_BR.md](DECISION_MAKER_VALUE_BRIEF.pt_BR.md) — briefing para decisores
- [REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md](REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md) — saídas do pipeline
- [SENSITIVITY_DETECTION.pt_BR.md](SENSITIVITY_DETECTION.pt_BR.md) — padrões de detecção e `norm_tag`
- [GLOSSARY.pt_BR.md](GLOSSARY.pt_BR.md) — termos ITSM / SGSI (EDM, SVS, SLA, Governance Lens)
- A **sequência de implementação** da Governance Lens fica no índice PMO do mantenedor ([README.pt_BR.md](README.pt_BR.md) *Interno e referência*) — sem link markdown para `docs/plans/` neste doc ([ADR 0004](adr/ADR-0004-external-docs-no-markdown-links-to-plans.md)).
