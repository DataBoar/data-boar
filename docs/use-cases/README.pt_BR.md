# Storyboards de caso de uso (fluxos para oficina)

**English:** [README.md](README.md)

Narrativas **curtas** para POCs, oficinas com pré-vendas técnico e alinhamento DPO/TI. São **ilustrativas** apenas: **não** substituem assessoria jurídica nem garantem que uma implantação reproduza o cenário ou atenda a normas setoriais (saúde, sigilo profissional, sigilo fiscal etc.).

Cada storyboard inclui **Oportunidade para parceiros** (como qualificar um lead) e **Alinhamento de produto (maintainers)** (quais superfícies já entregues priorizar primeiro — sem link para `docs/plans/` a partir de docs voltados a compradores; ver [docs/README.pt_BR.md](../README.pt_BR.md) *Internal and reference*).

**Use cases de produto** (escanear → remediar → provar, export tokenizado, biometria): [USE_CASES_HUB.pt_BR.md](USE_CASES_HUB.pt_BR.md) ([EN](USE_CASES_HUB.md)).

## Índice

| Storyboard | Foco | Alvos típicos do Data Boar |
| ---------- | ----- | -------------------------- |
| [PORT_LOGISTICS_MULTINATIONAL_CREW.pt_BR.md](PORT_LOGISTICS_MULTINATIONAL_CREW.pt_BR.md) | Tripulação multinacional, tensão de metadados portuários | Bancos, compartilhamentos, exportações de tickets |
| [LAW_FIRM_CLIENT_MATTER_AND_TRUST_DATA.pt_BR.md](LAW_FIRM_CLIENT_MATTER_AND_TRUST_DATA.pt_BR.md) | Processos de clientes, higiene de privilégio, conflitos | Pastas de documentos, arquivos de e-mail, exportações de DMS, bases de processo |
| [ACCOUNTING_FIRM_PAYROLL_TAX_AND_LEDGER.pt_BR.md](ACCOUNTING_FIRM_PAYROLL_TAX_AND_LEDGER.pt_BR.md) | Folha, identificadores fiscais, razão contábil | Exportações ERP/CSV, SQL de folha, drives compartilhados |
| [PHARMA_SPECIALTY_SALES_HOSPITALS_AND_PATIENT_PROGRAMS.pt_BR.md](PHARMA_SPECIALTY_SALES_HOSPITALS_AND_PATIENT_PROGRAMS.pt_BR.md) | Distribuição especializada a hospitais/farmácias; trilhas opcionais de apoio ao paciente | CRM, histórico de pedidos, planilhas de programa, exportações REST |
| [MSP_IT_CONSULTANCY_MULTI_TENANT_SMB.pt_BR.md](MSP_IT_CONSULTANCY_MULTI_TENANT_SMB.pt_BR.md) | MSP / consultoria de TI, muitas PME, varreduras repetíveis | Shares por cliente, exportações RMM, dumps M365/Google, cópias SQL somente leitura |
| [INSURANCE_BROKER_AND_BENEFITS_ADMIN.pt_BR.md](INSURANCE_BROKER_AND_BENEFITS_ADMIN.pt_BR.md) | Sinistros, apólices, beneficiários; texto adjacente a saúde | CRM, pastas de sinistros, planilhas, extratos REST |
| [RPO_PEOPLE_OPS_AND_PAYROLL_BUREAU.pt_BR.md](RPO_PEOPLE_OPS_AND_PAYROLL_BUREAU.pt_BR.md) | RPO / RH terceirizado / bureau de folha entre empregadores | Exportações ATS, pacotes de admissão, CSV/SQL de folha, shares de RH |
| [REAL_ESTATE_AND_CONDOMINIUM_MANAGEMENT.pt_BR.md](REAL_ESTATE_AND_CONDOMINIUM_MANAGEMENT.pt_BR.md) | Locação / condomínio / gestão predial PME, alto fluxo documental | Pastas por unidade, contratos, registos de consumo, exportações simples de CRM |
| [NGO_MIGRANT_WELCOME_AND_HUMANITARIAN_FILES.pt_BR.md](NGO_MIGRANT_WELCOME_AND_HUMANITARIAN_FILES.pt_BR.md) | Triagem humanitária; minimização ética em primeiro lugar | Planilhas de triagem, digitalizações (onde permitido), exportações de mensagens |
| [EDTECH_LMS_EXPORTS_AND_MINORS.pt_BR.md](EDTECH_LMS_EXPORTS_AND_MINORS.pt_BR.md) | Listas LMS, responsáveis, menores; higiene para due diligence | CSV/JSON do LMS, tickets, SQL opcional de listas |
| [BACKUP_AND_DATA_PROTECTION_ESTATE_CRITICALITY.pt_BR.md](BACKUP_AND_DATA_PROTECTION_ESTATE_CRITICALITY.pt_BR.md) | Parque de backup / proteção de dados; camada de criticidade sobre a base instalada | Cópias restauradas/montadas somente leitura, compartilhamentos/bancos de origem, catálogos de exportação |

## Incluir novos storyboards no futuro

1. Criar um novo arquivo **em inglês** em `docs/use-cases/` com a mesma estrutura dos existentes: **Elenco**, **Storyboard (fluxo)**, **Como o Data Boar ajuda sem decidir**, **Partner opportunity**, **Product alignment (maintainers)**, **Related docs** (no espelho pt-BR: **Oportunidade para parceiros** e **Alinhamento de produto (maintainers)**).
1. Criar o espelho **pt-BR** (`*.pt_BR.md`) com as mesmas seções.
1. Registrar o par na tabela acima (e manter [docs/README.pt_BR.md](../README.pt_BR.md) apontando para este hub).
1. Quando um vertical gerar **sinais de receita repetíveis**, os maintainers registram a sequência no ponto de entrada de planeamento ligado em [docs/README.pt_BR.md](../README.pt_BR.md) (*Internal and reference*) — não via novos links para `docs/plans/` a partir deste hub (guarda de CI).

## Referências transversais

- [DECISION_MAKER_VALUE_BRIEF.pt_BR.md](../DECISION_MAKER_VALUE_BRIEF.pt_BR.md) ([EN](../DECISION_MAKER_VALUE_BRIEF.md))
- [SERVICE_TIERS_SCOPE_TEMPLATE.pt_BR.md](../ops/SERVICE_TIERS_SCOPE_TEMPLATE.pt_BR.md) ([EN](../ops/SERVICE_TIERS_SCOPE_TEMPLATE.md))
- [COMPLIANCE_AND_LEGAL.pt_BR.md](../COMPLIANCE_AND_LEGAL.pt_BR.md) ([EN](../COMPLIANCE_AND_LEGAL.md))
