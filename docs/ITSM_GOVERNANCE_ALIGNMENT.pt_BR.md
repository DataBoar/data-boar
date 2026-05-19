# Alinhamento de governança de TI e gerenciamento de serviços

**English:** [ITSM_GOVERNANCE_ALIGNMENT.md](ITSM_GOVERNANCE_ALIGNMENT.md)

**Audiência:** DPO, CISO, diretor de TI, auditor externo, consultor de GRC.

**Primer (conceitos):** [GOVERNANCE_SERVICE_MANAGEMENT_PRIMER.pt_BR.md](GOVERNANCE_SERVICE_MANAGEMENT_PRIMER.pt_BR.md) · **Rótulos regulatórios:** [COMPLIANCE_FRAMEWORKS.pt_BR.md](COMPLIANCE_FRAMEWORKS.pt_BR.md) · **Contrato JSON GRC:** [GRC_EXECUTIVE_REPORT_SCHEMA.pt_BR.md](GRC_EXECUTIVE_REPORT_SCHEMA.pt_BR.md)

**Posicionamento:** Referência conceitual apenas — **não** é auditoria certificada nem parecer jurídico.

---

## 1. Valor sustentável em termos ITSM

O [ITIL 4](https://www.axelos.com/certifications/itil-service-management) descreve valor como **co-criação** entre provedor e consumidor:

> **Valor** = **Utilidade** (*fit for purpose*) + **Garantia** (*fit for use*)

| Dimensão | Contribuição do Data Boar |
| -------- | ------------------------- |
| **Utilidade** | Mostra **onde** dados pessoais/sensíveis aparecem nos **targets** configurados |
| **Garantia** | Execuções repetíveis, amostragem delimitada, **Audit Trail** por sessão |
| **Co-criação** | Achados ganham sentido executivo quando mapeados a **controles** e frameworks **`norm_tag`** — **Governance Lens** opcional (Pro/Enterprise) |

**Ciclo de melhoria contínua:** Planejar escopo → Executar varredura (**Data Sniffing** / **Deep Boring** — [GLOSSARY.pt_BR.md](GLOSSARY.pt_BR.md)) → Medir (Excel, heatmap, JSON GRC) → Melhorar (`--diff`, remediação, re-varredura). Veja [GOVERNANCE_SERVICE_MANAGEMENT_PRIMER.pt_BR.md](GOVERNANCE_SERVICE_MANAGEMENT_PRIMER.pt_BR.md).

---

## 2. Alinhamento por framework (tabelas resumidas)

### 2.1 ISO/IEC 38500 — Princípios de governança de TI

| Princípio | Evidência que o produto ajuda a produzir |
| --------- | ---------------------------------------- |
| **Responsabilidade** | Achados ligados a **`target_name`** — destaca sistemas sem dono formal do dado |
| **Estratégia** | Heatmaps / tendências de linha de base para investimento em segurança |
| **Desempenho** | **`--diff`** entre sessões |
| **Conformidade** | Linhas **`norm_tag`** (LGPD, GDPR, amostras setoriais) |
| **Comportamento humano** | Achados em targets **não produtivos** quando a política exige paridade |

### 2.2 ISO/IEC 27014 — Governança da segurança da informação

| Processo | Contribuição |
| -------- | ------------ |
| **Avaliar** | Inventário automatizado de exposição de PII/dados sensíveis |
| **Dirigir** | Exportações GRC informam política de mascaramento/dados de teste |
| **Monitorar** | Varreduras recorrentes + comparação de sessões |
| **Comunicar** | Narrativa Governance Lens (roadmap por *tier*) |
| **Assegurar** | **Audit Trail** exportável para auditoria externa |

### 2.3 COBIT 2019 — Objetivos selecionados

| Objetivo | Contribuição |
| -------- | ------------ |
| **APO13** (Gerenciar segurança) | Achados de linha de base para escopo do SGSI; linhas de remediação em export GRC |
| **DSS05** (Gerenciar serviços de segurança) | Evidência de contextos fracos de autenticação, PII em não prod |
| **MEA03** (Monitorar conformidade) | **`norm_tag`** + [GRC_EXECUTIVE_REPORT_SCHEMA.pt_BR.md](GRC_EXECUTIVE_REPORT_SCHEMA.pt_BR.md) estável |

### 2.4 ITIL 4 — Prática de gerenciamento da segurança da informação

| Atividade | Contribuição |
| --------- | ------------ |
| Classificar ativos de informação | Inventário de targets com detalhamento de sensibilidade |
| Avaliar/tratar risco | Campos de matriz de risco no JSON GRC (estilo P0/P1/P2) |
| Melhoria contínua | `--diff` entre sessões |

**Service Value Chain (SVC):** **Engage** (`--validate-config`); **Design & Transition** (controles-alvo por tipo de achado — roadmap Lens); **Deliver & Support** (serviço operacional de varredura); **Improve** (tendência/diff).

### 2.5 ISO/IEC 20000-1 — Gerenciamento de serviços

| Tópico | Contribuição |
| ------ | ------------ |
| **Conhecimento** | Export de achados para BD corporativo (*findings sink* — *tier* Pro) |
| **Configuração** | Targets como itens de configuração sem atributos de segurança |
| **Mudança** | Diff de sessão antes/depois de mudança |

### 2.6 Resolução BACEN 4.893/2021 (fintech BR — enquadramento Enterprise)

Pareie descoberta técnica com [amostras de conformidade](compliance-samples/) e o jurídico sobre política de **cibersegurança** e **comunicação de incidentes**. O produto **não** certifica conformidade BACEN.

---

## 3. Posicionamento por audiência (frases curtas)

| Leitor | Mensagem |
| ------ | -------- |
| **Conselho / executivo (ISO 38500)** | Evidência técnica periódica para princípios de governança — **não** substitui programa formal de governança de TI |
| **DPO / CISO (ISO 27014 + LGPD)** | Saídas de sessão orientadas a GRC para processos avaliar/comunicar |
| **Auditor externo (COBIT MEA03)** | Audit Trail imutável + rastreabilidade de schema GRC |
| **Gerente ITSM (ITIL 4 / ISO 20000)** | Varredura recorrente fecha o ciclo medir→melhorar |

---

## 4. Outputs mapeados por audiência

| Output | Formato | Audiência principal | Gancho de framework |
| ------ | ------- | ------------------- | ------------------- |
| Excel + heatmap padrão | XLSX | Analista de segurança, ITSM | ISO 20000, ITIL 4 |
| Export executivo GRC | JSON (+ DOCX/PDF futuro via Lens) | DPO, CISO, auditor | ISO 27014, COBIT |
| Audit Trail | SQLite + export opcional | Auditor, jurídico | ISO 38500, COBIT MEA03 |
| Export DSAR | JSON | DPO | LGPD Art. 18, GDPR Art. 15 |
| Findings sink | Conector de BD (Pro) | Time CMDB/dados | Configuração ISO 20000 |

Detalhes: [REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md](REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md).

---

## 5. Documentação relacionada

- [GOVERNANCE_SERVICE_MANAGEMENT_PRIMER.pt_BR.md](GOVERNANCE_SERVICE_MANAGEMENT_PRIMER.pt_BR.md)
- [COMPLIANCE_AND_LEGAL.pt_BR.md](COMPLIANCE_AND_LEGAL.pt_BR.md)
- [DECISION_MAKER_VALUE_BRIEF.pt_BR.md](DECISION_MAKER_VALUE_BRIEF.md)
- [USAGE.pt_BR.md](USAGE.pt_BR.md) — CLI (`--diff`, `--validate-config`, `--export-dsar`)
- [GLOSSARY.pt_BR.md](GLOSSARY.pt_BR.md) — COBIT, ITIL 4, Governance Lens, ISO 38500 / 27014
