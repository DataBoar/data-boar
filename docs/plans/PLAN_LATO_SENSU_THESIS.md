# Plan: Lato sensu thesis – Data Boar as applied artifact

**Status:** Deferred
**Date:** 2026-03-17
**Authors:** Fabio Leitao
**Priority:** H3

**Synced with:** `long-term-product-and-academic-roadmap` (conceptual) and [PLANS_TODO.md](PLANS_TODO.md) (execution order)

This plan turns the existing application and its plans into a **professionally oriented lato sensu thesis**. It does not change runtime behaviour; scope is framing, documentation, and small glue pieces (tables, diagrams, examples).

---

## 1. Framing and objectives

**Goal:** Define a clear, defensible thesis framing around **data discovery/mapping and compliance support** for LGPD + ISO/IEC 27xxx, using this codebase as the main artifact.

### To-dos (Framing and objectives)

| #   | To-do                                                                                                                                                                                            | Status    |
| -   | -----                                                                                                                                                                                            | ------    |
| 1.1 | Draft 2–3 candidate titles (PT-BR) and one-paragraph abstracts; choose one that best matches the program’s emphasis (more jurídico/compliance vs. mais técnico).                                 | ⬜ Pending |
| 1.2 | Write a 1–2 page “Projeto de TCC” style outline: problem statement, objectives (geral/específicos), justification, and expected contributions (for organizations and for you as a professional). | ⬜ Pending |

#### Candidate titles and abstracts (rascunho)

- **Título 1 (mais jurídico/compliance):**

  *Mapeamento de dados e evidências de conformidade para LGPD e normas ISO/IEC 27xxx: projeto e avaliação de uma plataforma de descoberta de dados corporativos.*
  **Resumo (rascunho):** O trabalho descreve o desenho e a implementação de uma aplicação de descoberta de dados (“Data Boar”) voltada a apoiar organizações na identificação de dados pessoais/sensíveis em múltiplas fontes (arquivos, bancos de dados, APIs, compartilhamentos) e na geração de evidências para LGPD, GDPR e normas ISO/IEC 27xxx. A partir de cenários inspirados em ambientes corporativos reais, avalia-se como os relatórios produzidos (inventário, menores, cripto/transporte, risco de identificação agregada) podem ser utilizados por DPOs e equipes de compliance como insumo para registros de operações, avaliações de risco e prestação de contas perante reguladores.

- **Título 2 (mais técnico/engenharia):**

  *Uma arquitetura configurável para descoberta de dados e apoio à conformidade em ambientes legados sob LGPD e ISO/IEC 27xxx.*
  **Resumo (rascunho):** Este trabalho apresenta uma arquitetura configurável, baseada em detecção híbrida (regex + ML/DL) e conectores para múltiplas fontes de dados, destinada a apoiar a conformidade com LGPD, GDPR e normas ISO/IEC 27xxx em ambientes corporativos heterogêneos. Detalham-se as decisões de projeto (metadados-only, on-premises, relatórios em Excel) e avalia-se, por meio de estudos de caso, em que medida a solução facilita o mapeamento de dados, a identificação de dados de menores, a visibilidade de criptografia/transporte e a geração de evidências para auditorias e avaliações de risco.

---

## 2. Background and regulatory/standards mapping

**Goal:** Show that the system is grounded in real requirements: LGPD, GDPR, FELCA, ISO/IEC 27701, ISO/IEC 27001/27002/27005, SOC 2.

### To-dos (Background and regulatory mapping)

| #   | To-do                                                                                                                                                                                                                                                                                                                                                                                                  | Status    |
| -   | -----                                                                                                                                                                                                                                                                                                                                                                                                  | ------    |
| 2.1 | From `docs/COMPLIANCE_FRAMEWORKS*.md` and plan files, build a table “Regra/controle → funcionalidade/relatório do sistema” for LGPD and GDPR.                                                                                                                                                                                                                                                          | ⬜ Pending |
| 2.2 | Extend the table to include ISO/IEC 27701, ISO/IEC 27001/27002/27005, SOC 2, FELCA, focusing on how reports and inventories act as **evidence** rather than full ISMS tooling.                                                                                                                                                                                                                         | ⬜ Pending |
| 2.3 | Turn this mapping into prose for a “Fundamentação teórica” chapter: brief sections on each norm + how tools like this help in practice.                                                                                                                                                                                                                                                                | ⬜ Pending |
| 2.4 | Optional **PUCRS extension** courses: align chosen certificate(s) with thesis chapters (e.g. **Gestão do Conhecimento e Transformação Digital** for governance/KM; **Compliance Criminal** for legal accountability; **A Escuta dos Excessos** for ethics/proportionality). Planning table: [PORTFOLIO_AND_EVIDENCE_SOURCES.md](PORTFOLIO_AND_EVIDENCE_SOURCES.md) §3.3 (PUCRS extension supplements). | ⬜ Pending |

---

## 3. System design and implementation (chapters)

**Goal:** Reuse existing architecture and plan docs as the backbone of “System Design” and “Implementation” chapters.

### To-dos (System design and implementation)

| #   | To-do                                                                                                                                                                 | Status    |
| -   | -----                                                                                                                                                                 | ------    |
| 3.1 | Extract and normalise 1–2 architecture diagrams (high-level components; scan pipeline; connectors vs engine vs reports) for use in the thesis.                        | ⬜ Pending |
| 3.2 | Summarise key design choices from plans (metadata-only, on-prem focus, config-driven detection, reports as evidence) in a narrative suitable for an academic chapter. | ⬜ Pending |

---

## 4. Case-study design and evaluation

**Goal:** Design 1–3 realistic case studies to evaluate the system in the style expected for a lato sensu specialization (applied, not purely theoretical).

### To-dos (Case-study design and evaluation)

| #   | To-do                                                                                                                                                                                  | Status    |
| -   | -----                                                                                                                                                                                  | ------    |
| 4.1 | Define 1–3 scenarios (e.g. médio porte BR empresa; multinacional LGPD+GDPR; plataforma afetada por FELCA) and, for each, specify which connectors and configs will be used.            | ⬜ Pending |
| 4.2 | Define what data/outputs will be collected in each case (reports, inventory sheets, crypto & controls sheet, minors’ data flags, cross-ref risk sheet).                                | ⬜ Pending |
| 4.3 | Draft an evaluation section outline: how results will be interpreted against each norm (e.g. “ajuda a cumprir LGPD Art. 37…”, “apoia evidência para controle A.8.x da ISO/IEC 27001”). | ⬜ Pending |

---

## 5. Methodology and write-up

**Goal:** Ensure the thesis has a clear methodology and is easy to defend.

### To-dos (Methodology and write-up)

| #   | To-do                                                                                                                                                               | Status    |
| -   | -----                                                                                                                                                               | ------    |
| 5.1 | Choose and document an overall method style (e.g. design science / engenharia aplicada: problema → artefato → avaliação por estudos de caso).                       | ⬜ Pending |
| 5.2 | Define the chapter structure explicitly (Introdução, Fundamentação, Desenho do sistema, Implementação, Estudos de caso, Discussão, Limitações e trabalhos futuros). | ⬜ Pending |
| 5.3 | Create a short checklist for defense preparation (slides, demo scenario, key risks/limitations you will acknowledge up front).                                      | ⬜ Pending |

---

## 6. Artifacts and evidence sources

For the thesis narrative and case studies, use:

- **Main artifact:** This repo (Data Boar) and Docker image `fabioleitao/data_boar`.
- **Portfolio context:** `docs/private/From Docker hub list of repositories.md` (data_boar, wildfly_t1r, uptk) for infra/SRE/compliance narrative.
- **Personal/academic:** CV, TCC, LinkedIn PDFs in `docs/private/` (git-ignored); reference by filename only. See [TOKEN_AWARE_USAGE.md](TOKEN_AWARE_USAGE.md) §3.

---

## 7. Sync notes

- This plan is purely **documentation and academic framing**; it does not add runtime features.
- When you complete a to-do, update this file and, if relevant, cross-link from `long-term-product-and-academic-roadmap`. No need to mention this plan in the public README roadmap.
