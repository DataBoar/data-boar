# Primer: Data Boar no ecossistema de governança de dados (DMBOK, ISO/IEC 38505, gestão vs governança)

<!-- plans-hub-summary: Posicionamento do Data Boar para profissionais de governança de dados (GGD, DPOs, revisores de TCC); gestão vs governança, áreas DMBOK, âncoras normativas, Data Governance Act, dados abertos -->

**Status:** Active
**Date:** 2026-11-10
**Authors:** Fabio Leitao
**Priority:** H2
**Depends on:** ADR-0004, ADR-0035, ADR-0050, ADR-0058, ADR-0070
**GitHub:** [#752](https://github.com/DataBoar/data-boar/issues/752)

**English:** [DATA_GOVERNANCE_PRIMER.md](DATA_GOVERNANCE_PRIMER.md)

**Audiência:** Profissionais de governança de dados (GGD), DPOs com background DMBOK, revisores acadêmicos (TCC na PUC-Rio) e consultores de governança de dados. Estes leitores chegam da disciplina de governança de dados — não da cibersegurança — e conhecem DMBOK, ISO/IEC 38505 e a distinção entre governança e gestão.

**Tom:** Profissional, orientado a evidência. Sem mascote. Sem roda DAMA verbatim, sem dump de cláusulas ISO. Pontos oficiais: [DAMA Body of Knowledge](https://www.dama.org/cpages/body-of-knowledge), [ISO/IEC 38505](https://www.iso.org/standard/56639.html), [Data Governance Act EU 2022/868](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32022R0868).

---

## 1. Gestão × Governança de dados — distinção

Baseado na DAMA International (DMBOK, 2.ed, 2017) e ISO/IEC 38505:

- **Gestão de dados**: controle operacional das atividades de dados do dia a dia (backup, disponibilidade, execução de qualidade, pipelines). Responsável: gerentes de dados e equipes técnicas.
- **Governança de dados**: monitoramento periódico para assegurar que as atividades de dados estão alinhadas à estratégia organizacional, operando em risco aceitável e contribuindo para os objetivos. Responsável: alta direção, DPO, conselho. Definida pela DAMA como "o exercício de autoridade, controle (planejamento, monitoramento, supervisão) sobre a gestão de ativos de dados."

O Data Boar atende a ambos os níveis:

- **Gestão**: o próprio scan — coleta, amostragem, achados no nível operacional.
- **Governança**: relatório executivo + compliance grade report + APG entregues à alta direção como indicadores de governança.

| Dimensão | Governança | Gestão |
| -------- | ---------- | ------ |
| Nível | Estratégico / periódico | Operacional / contínuo |
| Pergunta central | A área está alinhada à estratégia? | As atividades estão sendo executadas? |
| Frequência | Reuniões periódicas · indicadores-chave | Dia a dia |
| Responsável | Alta direção · conselho | Gerentes e equipes técnicas |
| Papel do Data Boar | Evidência para o ciclo EDM | Visibilidade operacional de dados |

**SVG** (hierarquia — A governa B): [data_boar_governance_vs_management.svg](../assets/diagrams/data_boar_governance_vs_management.svg) (companheiro, opcional).

---

## 2. Data Boar nas 11 áreas de conhecimento do DMBOK

De [databoar-dmbok-diagrams.md](../assets/diagrams/databoar-dmbok-diagrams.md) seção 1. Três zonas:

| Zona | Área de conhecimento | Papel do Data Boar |
| ---- | -------------------- | ------------------ |
| **Núcleo** | Governança de dados | `scan_manifest`, relatório orientado a GRC, metadados de sessão auditáveis |
| **Núcleo** | Segurança de dados | Descoberta de PII/sensíveis; exposição por fonte e tipo de padrão |
| **Núcleo** | Gestão de metadados | `norm_tag`, schema de plugin, perfil de sensibilidade nos achados |
| Contribui | Arquitetura de dados | Inventário das origens configuradas como insumo à arquitetura |
| Contribui | Armazenamento e operação | Scans de bancos, arquivos e alvos adjacentes a stream que você configurar |
| Contribui | Integração e interoperabilidade | Conectores e plugins por fonte |
| Contribui | Qualidade de dados | Perfil de sensibilidade como **uma** dimensão de qualidade/risco — não scorecard de DQ |
| Contexto | Modelagem e projeto | — |
| Contexto | Documentos e conteúdo | — (exceto se apontar filesystem/API para esses acervos) |
| Contexto | Dados de referência e mestre | — |
| Contexto | Data warehouse e BI | Conectores de BI opcionais quando configurados; não é plataforma de DW |

*Rótulos acima são agrupamento deste repositório (núcleo / contribui / contexto). **Não** reproduzem nomes ou diagramas publicados pela DAMA.*

---

## 3. Âncoras normativas

- **ISO/IEC 38505** (governança de dados): estende os princípios da ISO/IEC 38500 ao domínio de dados. Catálogo: [ISO/IEC 38505](https://www.iso.org/standard/56639.html).
- **ISO/IEC 27701:2019** (gestão de informação de privacidade — PIMS): estende a ISO/IEC 27001 para governança de PII. Catálogo: [ISO/IEC 27701:2019](https://www.iso.org/standard/71670.html).
- **ISO/IEC 25012** (modelo de qualidade de dados): qualidade como dimensão de governança. Catálogo: [ISO/IEC 25012](https://www.iso.org/standard/35736.html).
- **DAMA DMBOK 2.ed (2017)**: framework canônico. [DAMA Body of Knowledge](https://www.dama.org/cpages/body-of-knowledge).
- **LGPD** (Lei 13.709/2018), **GDPR** (EU 2016/679): contexto regulatório.

---

## 4. Data Governance Act (UE, Regulation 2022/868)

Regulamento (EU) 2022/868. Regula **serviços de intermediação de dados**, **doação de dados (data altruism)** e **reutilização de dados do setor público**. Complementa o GDPR ao nível do ecossistema. Relevante para organizações que operam simultaneamente na UE e no Brasil.

A capacidade de descoberta do Data Boar apoia os requisitos de **auditabilidade** dessa regulamentação.

Referência: [Regulation (EU) 2022/868](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32022R0868).

---

## 5. Dados abertos — enquadramento breve

Dados abertos como conceito de governança: dados disponibilizados sem restrições. Relevante para o modelo open-core do Data Boar (scanner aberto, camada de relatório proprietária). Âncora normativa: [W3C Data on the Web Best Practices](https://www.w3.org/TR/dwbp/).

---

## 6. Posicionamento do Data Boar para esta audiência

> "O Data Boar é a camada de descoberta e evidência que torna a governança de dados verificável. Não substitui uma função GGD — fornece o inventário, a linha de base de exposição e o rastro de auditoria que uma função GGD precisa para exercer a supervisão com evidência."

---

## Referências cruzadas

- [databoar-dmbok-diagrams.md](../assets/diagrams/databoar-dmbok-diagrams.md) — zonas DMBOK e diagrama gestão vs governança
- [databoar-governance-diagrams.md](../assets/diagrams/databoar-governance-diagrams.md) — pilha de governança de TI e mapeamento do ciclo EDM
- [COMPLIANCE_AND_LEGAL.pt_BR.md](../COMPLIANCE_AND_LEGAL.pt_BR.md) — alinhamento regulatório, ISO/IEC 27701, 25012, Data Governance Act
- [DECISION_MAKER_VALUE_BRIEF.pt_BR.md](../DECISION_MAKER_VALUE_BRIEF.pt_BR.md) — posicionamento executivo
- [ADR-0025](../adr/ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md) — postura "evidência e inventário, não conclusão jurídica"

---

*Wording original — não reproduz texto DAMA ou ISO. Todas as referências normativas com ano e URL.*