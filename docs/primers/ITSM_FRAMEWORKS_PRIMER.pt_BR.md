# Primer: gerenciamento de serviços de TI (ITIL 4, ISO/IEC 20000)

<!-- plans-hub-summary: ITIL 4 SVS e ISO/IEC 20000 — práticas selecionadas vs evidência Data Boar, não service desk -->

**Status:** Active
**Date:** 2026-08-29
**Authors:** Fabio Leitao
**Priority:** H2
**Depends on:** ADR-0004, ADR-0035, ADR-0050, ADR-0058, ADR-0070
**GitHub:** [#630](https://github.com/DataBoar/data-boar/issues/630)

**English:** [ITSM_FRAMEWORKS_PRIMER.md](ITSM_FRAMEWORKS_PRIMER.md)

**Audiência:** engenheiros de compliance, times de TI e governança que falam a língua de **gerenciamento de serviços** e precisam posicionar varreduras de descoberta nesse vocabulário.

**Tom:** técnico. Sem mascote. Sem reprodução de tabelas AXELOS ou ISO — adquira [ITIL 4](https://www.axelos.com/certifications/itil-service-management) e [ISO/IEC 20000](https://www.iso.org/standard/70636.html) (Brasil: ABNT NBR ISO/IEC 20000) para o texto oficial.

Este primer é o **companion de execução** do GitHub **#629** (governança de TI / EDM). A governança dirige; o ITSM entrega e melhora.

---

## Gerenciamento de serviços como elo entre estratégia e entrega

A estratégia define intenção (valor, risco, responsabilização). O **gerenciamento de serviços de TI** transforma isso em formas repetíveis de planejar, entregar, suportar e melhorar serviços. O Data Boar fica **dentro da entrega e da melhoria**: produz **evidência de onde dados sensíveis apareceram** nos alvos configurados. Não opera a central de serviços, não é dono de SLA e não certifica um SGS.

Linguagem SRE: [OBSERVABILITY_SRE.pt_BR.md](../OBSERVABILITY_SRE.pt_BR.md). Metodologia: [COMPLIANCE_METHODOLOGY.pt_BR.md](../COMPLIANCE_METHODOLOGY.pt_BR.md).

---

## ITIL 4 — Service Value System (SVS)

O ITIL 4 descreve um **sistema de valor de serviço**: como os componentes da organização trabalham juntos para que serviços gerem valor (princípios, governança, cadeia de valor, práticas, melhoria contínua). Visão pública: [Axelos — ITIL](https://www.axelos.com/certifications/itil-service-management).

Cada **sessão** Data Boar é um **insumo** desse sistema (achados, manifest, relatório). **Não** é o SVS.

SVG (diagrama inspirado, não figura oficial ITIL): [databoar_svs_inspirado.svg](../assets/diagrams/databoar_svs_inspirado.svg).

---

## ISO/IEC 20000 — sistema de gestão de serviços

A ISO/IEC 20000 é norma de **sistema de gestão** para serviços de TI. Catálogo: [ISO/IEC 20000](https://www.iso.org/standard/70636.html). O Data Boar pode **apoiar evidência** (scans repetíveis, amostragem delimitada no manifest) que o time anexa ao **SGS da organização**; **não** implementa controles 20000 cláusula a cláusula.

---

## Quatro dimensões do ITSM (atravessamento do produto)

O ITIL 4 fala em quatro dimensões. No **wording deste produto** (não é tabela normativa):

| Dimensão (linguagem simples) | Como a varredura de descoberta atravessa |
| ---------------------------- | ---------------------------------------- |
| **Pessoas e organização** | Quem dispara scans, quem lê relatórios (API key, RBAC opcional) — IAM/ITSM continua seu |
| **Informação e tecnologia** | Alvos, conectores, amostragem, pilha de detecção |
| **Parceiros e fornecedores** | Conectores SaaS/CRM/API; a DPA do fornecedor continua sua |
| **Fluxos de valor e processos** | Scan como passo em mudança, incidente ou cadência de compliance — você desenha o fluxo |

---

## Práticas ITIL selecionadas — contribuição do produto (não catálogo)

| Prática (rótulo ITIL comum) | Como o Data Boar pode contribuir |
| --------------------------- | -------------------------------- |
| Gestão de incidentes | PII em produção é **superfície de incidente de dados**. O scan pode mostrar exposição **antes** do ticket de vazamento. |
| Gestão de problemas | PII recorrente em logs ou homologação costuma ser **sistêmico**. O histórico entre sessões mostra padrões que limpezas pontuais não resolveram. |
| Controle de mudanças | Scan pré/pós-deploy pode marcar **nova** exposição introduzida pela mudança. Gate opcional no **seu** CI/CD — o motor não é dono do pipeline. |
| Capacidade e desempenho | Amostragem configurável, timeouts por alvo, orçamento de caracteres. O **scan manifest** documenta cobertura e profundidade — transparência sobre limites. |
| Continuidade de serviços | Manifest + achados de metadados podem entrar no **pacote de diligência pós-incidente**: o que existia, onde, quando foi verificado — não é orquestrador de DR. |

---

## O que este produto não é

- Não é **service desk** nem sistema de tickets.
- Não é **plataforma ITSM** (CMDB não é fonte da verdade aqui; não há motor de SLA).
- Não é **certificação** ISO/IEC 20000 ou ITIL.

---

## Docs relacionados

- [COMPLIANCE_METHODOLOGY.pt_BR.md](../COMPLIANCE_METHODOLOGY.pt_BR.md)
- [OBSERVABILITY_SRE.pt_BR.md](../OBSERVABILITY_SRE.pt_BR.md)
- [ITSM_GOVERNANCE_ALIGNMENT.pt_BR.md](../ITSM_GOVERNANCE_ALIGNMENT.pt_BR.md)
- [GRC_EXECUTIVE_REPORT_SCHEMA.pt_BR.md](../GRC_EXECUTIVE_REPORT_SCHEMA.pt_BR.md)
- Companion de governança: GitHub [#629](https://github.com/DataBoar/data-boar/issues/629)
