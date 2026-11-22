# Domínios Funcionais — Data Boar

**English:** [FUNCTIONAL_DOMAINS.md](FUNCTIONAL_DOMAINS.md)

## Objetivo e terminologia

Mapa canônico dos domínios funcionais do Data Boar. Conecta responsabilidades estáveis do produto às capacidades, use cases, storyboards setoriais, referências de governança e investigações rastreadas. É um documento de navegação/classificação, não especificação de implementação, compromisso de feature, parecer jurídico ou prova de que toda capacidade mapeada esteja entregue.

- **Domínio funcional:** responsabilidade/área de problema estável que o operador investiga ou evidencia.
- **Capacidade:** comportamento do produto ou fluxo documentado que apoia um ou mais domínios.
- **Vertical / setor:** contexto industrial ou operacional que combina vários domínios.
- **Use case:** fluxo ou cenário concreto.
- **Domínio/framework GRC:** lente externa de governança/controle; não define a arquitetura do produto.

## Limite do produto

Data Boar é um instrumento determinístico de discovery de dados, mapeamento de sensibilidade e produção de evidências. O resultado de detecção é insumo para avaliação humana; não estabelece sozinho papéis jurídicos, base legal, finalidade, obrigações contratuais, conformidade regulatória ou cobertura completa.

Organize o produto por capacidades e seus contratos, não por setores, frameworks legais ou taxonomia comercial. Vertical packs podem compor capacidades existentes, configuração validada, fixtures sintéticas e exemplos de evidência. Não devem criar forks do produto nem sugerir comportamentos não suportados.

## Domínios funcionais canônicos

| ID | Domínio | Pergunta do operador | Superfícies relevantes |
| --- | --- | --- | --- |
| FD-01 | **Discovery e inventário de dados** | Quais ativos e fontes com dados existem dentro do escopo autorizado? | Arquivos/bancos/conectores suportados, configuração de alvos e escopo, scan manifests, [USAGE.pt_BR.md](USAGE.pt_BR.md) |
| FD-02 | **Detecção de sensibilidade e sinais de classificação** | Quais locais podem conter dados pessoais, sensíveis, confidenciais ou relevantes à segurança? | Padrões determinísticos e etapas de detecção suportadas, findings de sensibilidade, [SENSITIVITY_DETECTION.pt_BR.md](SENSITIVITY_DETECTION.pt_BR.md), [MINOR_DETECTION.pt_BR.md](MINOR_DETECTION.pt_BR.md) |
| FD-03 | **Contexto, proveniência e custódia** | De onde veio o finding, sob qual escopo e qual contexto de custódia é conhecido? | Metadados de sessão/alvo, manifests, atribuição de origem e proveniência de relatórios; categorias de custódia não são inferidas automaticamente |
| FD-04 | **Mapeamento de risco e evidência de compliance** | Quais findings podem ser relevantes para risco, obrigação, framework ou pergunta de revisão? | Findings, vocabulário calibrado de estados de risco, overlays de frameworks e referências de evidência; sem veredito automático de compliance |
| FD-05 | **Evidências, relatórios e divulgação controlada** | O que pode ser demonstrado e compartilhado com segurança com auditor, cliente, DPO ou revisor de segurança? | Relatórios, manifests, findings tokenizados, sumários só de metadados; [REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md](REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md) |
| FD-06 | **Priorização de remediação e hand-off** | O que o operador responsável deve revisar/remediar e como evidenciar o hand-off? | Prioridades orientadas à remediação, inventário de ações e trabalho de interface/plugin; Data Boar não altera silenciosamente sistemas de origem |
| FD-07 | **Governança do processamento e limites de autorização** | Quem autorizou a atividade, para qual escopo e quais partes/sistemas podem acessar os artefatos resultantes? | Escopo declarado pelo operador, limites de serviço/deployment, RBAC onde implementado, guarda de consentimento não transitivo (#16); modelo de contexto de engagement em investigação na [#2323](https://github.com/DataBoar/data-boar/issues/2323) |
| FD-08 | **Deployment, integração e garantia operacional** | Onde o scanner executa, quais sistemas pode alcançar e quais dados atravessam cada limite? | On-prem e modos suportados, conectores/plugins, limites de logs/telemetria/suporte, evidências de release/operação; [ENTERPRISE_INTEGRATION_GUIDE.pt_BR.md](ENTERPRISE_INTEGRATION_GUIDE.pt_BR.md), [#2324](https://github.com/DataBoar/data-boar/issues/2324) |

Os domínios se sobrepõem intencionalmente. Uma varredura pode contribuir para discovery, classificação, proveniência, revisão de risco, relatórios e hand-off de remediação. Não são módulos obrigatórios em sequência.

## Cruzamento com setores e contextos operacionais

Uma vertical é composição de domínios funcionais, não uma nova arquitetura. O cruzamento é auxílio de navegação; não afirma que todo detector setorial, conector, controle jurídico ou fluxo esteja implementado.

| Vertical / contexto | Domínios primários | Storyboard existente |
| --- | --- | --- |
| Portos, logística e força de trabalho multinacional | FD-01, FD-02, FD-03, FD-04, FD-05 | [Portos e logística](use-cases/PORT_LOGISTICS_MULTINATIONAL_CREW.pt_BR.md) |
| Escritórios de advocacia e processos de clientes | FD-01, FD-02, FD-03, FD-05, FD-07 | [Jurídico](use-cases/LAW_FIRM_CLIENT_MATTER_AND_TRUST_DATA.pt_BR.md) |
| Contabilidade, folha, fiscal e razão | FD-01, FD-02, FD-04, FD-05, FD-06 | [Contabilidade](use-cases/ACCOUNTING_FIRM_PAYROLL_TAX_AND_LEDGER.pt_BR.md) |
| Pharma, hospitais e programas de pacientes | FD-01, FD-02, FD-03, FD-04, FD-05 | [Pharma](use-cases/PHARMA_SPECIALTY_SALES_HOSPITALS_AND_PATIENT_PROGRAMS.pt_BR.md) |
| MSP / MSSP / consultoria de TI | FD-01, FD-03, FD-05, FD-07, FD-08 | [MSP](use-cases/MSP_IT_CONSULTANCY_MULTI_TENANT_SMB.pt_BR.md) |
| Corretoras de seguros e administração de benefícios | FD-01, FD-02, FD-03, FD-04, FD-05 | [Seguros](use-cases/INSURANCE_BROKER_AND_BENEFITS_ADMIN.pt_BR.md) |
| RPO, operações de RH e bureau de folha | FD-01, FD-02, FD-03, FD-04, FD-05, FD-07 | [RPO](use-cases/RPO_PEOPLE_OPS_AND_PAYROLL_BUREAU.pt_BR.md) |
| Imobiliárias e gestão de condomínios | FD-01, FD-02, FD-04, FD-05, FD-06 | [Imobiliário](use-cases/REAL_ESTATE_AND_CONDOMINIUM_MANAGEMENT.pt_BR.md) |
| ONGs e registros humanitários | FD-01, FD-02, FD-03, FD-04, FD-05, FD-07 | [ONG](use-cases/NGO_MIGRANT_WELCOME_AND_HUMANITARIAN_FILES.pt_BR.md) |
| EdTech, LMS e menores | FD-01, FD-02, FD-03, FD-04, FD-05, FD-07 | [EdTech](use-cases/EDTECH_LMS_EXPORTS_AND_MINORS.pt_BR.md) |
| Backup e parque de proteção de dados | FD-01, FD-03, FD-04, FD-05, FD-08 | [Backup](use-cases/BACKUP_AND_DATA_PROTECTION_ESTATE_CRITICALITY.pt_BR.md) |
| Prestadores que processam dados confiados por clientes | FD-01, FD-02, FD-03, FD-04, FD-05, FD-07, FD-08 | [Entrusted Client Data Governance](use-cases/USE_CASE_ENTRUSTED_CLIENT_DATA_GOVERNANCE.pt_BR.md), rastreado pela [#2321](https://github.com/DataBoar/data-boar/issues/2321) |

Biometria é categoria de dado sensível/preocupação transversal, não vertical: [use case de biometria](use-cases/USE_CASE_BIOMETRIC_DATA_PROTECTION.pt_BR.md). Scan → remediate → prove e findings tokenizados são fluxos horizontais aplicáveis a várias verticais: [scan and remediate](use-cases/USE_CASE_SCAN_AND_REMEDIATE.pt_BR.md), [findings tokenizados](use-cases/USE_CASE_TOKENIZED_FINDINGS.pt_BR.md).

## Relação com a taxonomia GRC

Use domínios/frameworks GRC externos como lente de cobertura para identificar perguntas de stakeholders, lacunas de evidência, pesquisa com parceiros e oportunidades verticais. Não use uma lista de domínios GRC como decomposição interna do produto, hierarquia de features ou arquitetura de agentes/Bestials. Mapeie overlays de frameworks aos domínios funcionais acima. Um finding pode apoiar uma avaliação; não é, por si só, teste de controle, conclusão jurídica, opinião de auditoria ou certificação.

## Custódia de dados confiados a prestadores: cenário transversal

**Entrusted Client Data Governance** descreve prestadores cujo próprio ambiente operacional recebe, armazena, acessa, transforma, transmite ou analisa dados de clientes. É distinto de MSP que varre ambientes controlados pelos clientes, deployment gerenciado/SaaS e fluxo genérico scan → remediação.

Trabalho relacionado:
- [#2321](https://github.com/DataBoar/data-boar/issues/2321) — documentação do use case.
- [#2322](https://github.com/DataBoar/data-boar/issues/2322) — posicionamento comercial para prestadores.
- [#2323](https://github.com/DataBoar/data-boar/issues/2323) — contexto de engagement, proveniência e limites de evidência.
- [#2324](https://github.com/DataBoar/data-boar/issues/2324) — preparação NDA/DPA e postura de processamento.
- [#2325](https://github.com/DataBoar/data-boar/issues/2325) — Trust Overview & Assurance Index.

Rótulos de custódia (dados próprios do prestador, dados de clientes confiados, dados de suboperadores, origem/custódia desconhecida) são contextuais e declarativos. Não infira papéis jurídicos a partir de rótulo comercial, nome de tenant, vertical ou modo de deployment. Não trate tenant_name como isolamento de tenant, nem consentimento para Data Boar como consentimento para outras Bestials.

## Disciplina de capacidades e claims

Para cada domínio/vertical, diferencie: **implementado e evidenciado** (código/testes/release/evidência operacional); **configurável hoje** (aceito pelo schema atual e validado); **fluxo documentado** (processo do operador, não necessariamente imposto pela aplicação); **pesquisa/proposta** (não validado); e **não determinado pelo Data Boar** (papéis jurídicos, base legal, finalidade, obrigações de retenção, completude, conformidade regulatória e conclusões independentes de assurance).

Nunca transforme storyboard, pitch, plano, ADR, issue ou sample em prova de implementação. Samples executáveis devem validar contra o schema atual. Use somente dados sintéticos.

## Navegação e manutenção

- Este arquivo é o mapa canônico de domínios funcionais.
- [USE_CASES_HUB.pt_BR.md](use-cases/USE_CASES_HUB.pt_BR.md) indexa fluxos de produto.
- [Storyboards de use cases](use-cases/README.pt_BR.md) indexam narrativas setoriais.
- [Índice de pitches](pitch/INDEX.pt_BR.md) contém posicionamento por audiência.
- [Compliance e legal](COMPLIANCE_AND_LEGAL.pt_BR.md) e [frameworks de compliance](COMPLIANCE_FRAMEWORKS.pt_BR.md) descrevem o contexto externo de governança.
- [Hubs de navegação](hubs/INDEX.pt_BR.md) são o mapa dos mapas para agentes.

Ao adicionar vertical/use case, mapeie primeiro para IDs FD existentes. Proponha novo domínio somente quando uma responsabilidade estável do produto não couber nos atuais. Atualize EN e pt-BR juntos e rode as verificações de links/hubs da documentação.
