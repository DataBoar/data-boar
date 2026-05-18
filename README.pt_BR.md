# Data Boar

**Data Boar** — descoberta de dados e governança de risco corporativa: mapeamento com consciência de conformidade na sua sopa de dados (motor de inteligência, não um “app de auditoria” de um só marco).

![Data Boar mascot](api/static/mascot/data_boar_mascote_color.svg)

**LGPD — relato-testemunho (visita de campo, Brasil):** [Português (Brasil)](docs/LGPD_WITNESS_REPORT_NIO_FIELD_VISIT_2026.pt_BR.md) · [English](docs/LGPD_WITNESS_REPORT_NIO_FIELD_VISIT_2026.md)

**English:** [README.md](README.md) · [docs/USAGE.md](docs/USAGE.md)

---

## Para gestores e líderes de conformidade

Sua organização precisa saber **onde** estão os dados pessoais e sensíveis — para cumprir **LGPD**, **GDPR**, **CCPA**, **GLBA** e outros marcos relevantes, e evitar surpresas custosas. O **Data Boar** é um motor **multi-dialeto**, amigável a **SRE**, para **descoberta de dados** e **conformidade acionável** (avaliação de risco e entregáveis orientados a governança — Excel, heatmaps, Markdown executivo, manifestos de evidência). Ajuda a construir **consciência de conformidade** e a trazer à tona **possíveis violações** sem custo fora de controle: um único motor configurável que varre seus dados e reporta o que encontra, para que TI, cibersegurança, conformidade e DPOs possam agir com base em informação.

**O que trazemos à tona:** Além de PII óbvio (CPF, CNPJ — incluindo o novo formato alfanumérico, e-mail, telefone), usamos **IA** (ML e DL opcional) para detectar **categorias sensíveis** (saúde, religião, opinião política, biométrico, genético—LGPD Art. 5 II, GDPR Art. 9), **combinações de campos com risco de reidentificação no contexto** (LGPD Art. 5, GDPR Recital 26) e **possíveis dados de menores** (LGPD Art. 14, GDPR Art. 8). Reconhecemos nomes regionais de documentos e sinalizamos identificadores ambíguos para confirmação manual, e revelamos exposição em **colunas legadas**, **exportações**, **dashboards** e **múltiplas fontes** em uma visão—para você enxergar lacunas que checagens manuais ou ferramentas só de regras costumam perder. Os achados trazem **`norm_tag`** e o mesmo vocabulário de risco do Excel; quando o jargão acumula (**quasi-identificador**, categorias, matizes entre jurisdições), o [Glossário](docs/GLOSSARY.pt_BR.md#glossary-stakeholder-jargon) alinha TI, jurídico e compras na mesma língua.

**Dados de crianças e adolescentes — prioridade de produto, não rodapé:** Colunas e valores de **possível menor** têm **detector dedicado**, tratamento elevado no relatório (incluindo **re-amostragem** opcional mais profunda em banco e **cruzamento** com identificadores ou sinais de saúde na mesma tabela ou caminho) e **YAML de amostras** com vocabulário para contextos de privacidade infantil nos EUA — sempre como **sinais de inventário e triagem**, nunca como verificação legal de idade. É uma **categoria linguística** explícita no produto: o mesmo javali que abre a sopa de dados corporativa está preparado para **trazer cedo** exposição ligada a menores para revisão de DPO e segurança. Limites técnicos e chaves de config: [MINOR_DETECTION.pt_BR.md](docs/MINOR_DETECTION.pt_BR.md) ([EN](docs/MINOR_DETECTION.md)); mapa por preocupação: [MAP.pt_BR.md](docs/MAP.pt_BR.md) ([EN](docs/MAP.md)).

O risco real—**shadow IT** e além—costuma estar escondido em planilhas paralelas, pastas esquecidas, bancos legados, falta de padronização, fluxos confusos, aplicações mal documentadas, exceções e coleta excessiva de dados. O Data Boar segue farejando sua sopa de dados para trazer à tona esses ingredientes ocultos—incluindo arquivos renomeados ou mascarados e transporte ou armazenamento mais frágeis—para que conformidade e jurídico vejam o que de fato está lá, e não só a aparência. **Mídia rica hoje:** varreduras **opcionais de metadados**, **OCR em imagens** e arquivos de **legenda** ajudam a achar o que busca full-text simples costuma perder. **Horizonte (por fases, muitas vezes opt-in):** sinais mais fortes para **rastreadores embutidos**, **esteganografia** e **truques em documento** (microtexto, Unicode, objetos aninhados)—sem prometer detecção exaustiva até cada fatia existir no produto.

**Faminto pela sua sopa de dados:** Como um **javali**, aprofundamos em várias fontes e não paramos na superfície. Sejam quais forem os ingredientes—**arquivos**, **SQL**, **NoSQL**, **APIs**, **Power BI**, **Dataverse**, **SharePoint**, **SMB/NFS** e outros—estamos prontos para ingerir e digerir. **Não armazenamos nem exfiltramos** PII, apenas **metadados** (onde foi encontrado, tipo de padrão, sensibilidade), para você obter visibilidade para remediação sem mover dados.

**Por que sustenta:** Um único motor, **via configuração** (regex, termos ML/DL, norm tags, overrides de recomendação) — sem mudar código para alinhar a diferentes frameworks. **Relatórios Excel**, **heatmaps** e **tendências** entre sessões; varreduras **agendáveis** via API. Padrões de base cobrem **LGPD**, **GDPR**, **CCPA**, **GLBA**; **amostras de config** estendem para **UK GDPR**, **EU GDPR**, **Benelux**, **PIPEDA**, **POPIA**, **APPI**, **PCI-DSS**, vocabulário de saúde nos EUA e mais — cada uma com **orientação de frameworks** em **compliance-samples** (tabela abaixo). **Posicionamento regulatório**, limites de inventário por setor (incluindo saúde nos EUA) e **serviços profissionais** opcionais estão resumidos em [Conformidade e jurídico](docs/COMPLIANCE_AND_LEGAL.pt_BR.md).

Idiomas e encodings legados são suportados; **timeouts configuráveis** e **endurecimento de segurança** (validação, headers, auditoria) estão em vigor. **Arquivos compactados:** varredura dentro de zip, tar, gz, 7z via config, CLI ou dashboard — detalhes e avisos de I/O estão em **USAGE** (tabela abaixo). A detecção opcional de **content-type** ajuda a encontrar arquivos renomeados ou mascarados (ex.: PDF salvo com **extensão enganosa** que não é de texto, como `.mp3` — os *magic bytes* ainda revelam o formato real); visibilidade inicial de **cripto/transporte** (ex.: TLS vs texto puro) é coletada para bancos e APIs.

**Farejando com critério:** Leituras de texto plano usam um **orçamento configurável de caracteres** para que o motor veja estrutura de verdade — não só um pedaço inútil — antes de decidir; conteúdo em **formato de entretenimento** (ex.: cifras, letras, trechos típicos de README de projeto aberto) encaminha **sugestões ruidosas de ML** para uma **faixa de revisão**, em vez de lotar o relatório com falsos alarmes “certos”, enquanto **achados fortes por padrão** (documentos, dados de pagamento, PII clara) seguem prioritários para triagem.

**Roadmap:** Seguimos ampliando a **descoberta** (arquivos e mídia mais ricos, conectores em **nuvem** e **enterprise**), melhorando **alertas** ao fim da varredura e mantendo **segurança e dependências** em dia. **CLI do operador (em andamento):** **validação de config** antes das varreduras, **diff entre sessões** para evidência de regressão e auxiliares de **exportação orientada a DSAR** com padrão **metadados primeiro** — mantenedores acompanham fatias na árvore de planos do repositório (ver **docs/README.md** *Internal and reference*). A **cobertura de idiomas** na interface e na documentação, e as **amostras regionais** de conformidade, crescem **aos poucos**, conforme a demanda — não todos os mercados de uma vez. **Já entregue (opt-in):** **notas heurísticas de jurisdição** na planilha **Report info** — a partir de **metadados** dos achados (**não** conclusão jurídica), para equipes multinacionais **priorizarem revisão com assessoria**. Ative em config, CLI, dashboard ou API; detalhes: [USAGE.pt_BR](docs/USAGE.pt_BR.md). **Para diretoria e auditoria:** dá para apresentar **prioridades e evidências objetivas** — visibilidade de dados e postura de conformidade — **sem** fazer da apresentação um mergulho em roadmap técnico. **Lista de frameworks**, **normas com foco em auditoria** (ex.: ISO 27701, SOC 2), amostras sobre **menores**, SBOM e sinais da API: [COMPLIANCE_FRAMEWORKS.pt_BR.md](docs/COMPLIANCE_FRAMEWORKS.pt_BR.md). **O que já está entregue** vs **roadmap em fases:** [docs/releases/](docs/releases/).

**Convidamos você a entrar em contato** para ver como o Data Boar pode apoiar sua jornada de conformidade.

**Cenários típicos:** Preparação para auditoria ou pedido do regulador; mapeamento de dados antes de migração ou implantação de DLP; conscientização de conformidade sem war room completo.

> **Release atual:** **1.7.3**. **Docker Hub:** **`fabioleitao/data_boar:1.7.3`** ou **`latest`**. Resumo: [CHANGELOG.md](CHANGELOG.md). Notas: [docs/releases/1.7.3.md](docs/releases/1.7.3.md) e [Releases no GitHub](https://github.com/FabioLeitao/data-boar/releases). Golden anterior: **`v1.7.2-safe`** / **`1.7.2+safe`** — [docs/releases/1.7.2-safe.md](docs/releases/1.7.2-safe.md).
> **Pré-release em `main`:** **`1.7.4-rc`** — rascunho de **pré-release** no GitHub: [docs/releases/1.7.4-rc.md](docs/releases/1.7.4-rc.md) (**não** move o **`latest`** do Docker; o estável continua **1.7.3** até **`1.7.4`** final).
> **Documentação:** Este README e o `docs/USAGE.pt_BR.md` são as referências em português. Quando funcionalidades ou opções mudarem, atualize **ambos** os idiomas para mantê-los sincronizados.

**Blog do produto** (atualizações em formato narrativo, posts mais curtos): [databoar.wordpress.com](https://databoar.wordpress.com) — a documentação técnica canônica continua neste repositório (`docs/`).

---

## The Architect's Vault (cofre do arquiteto)

Investidores, parceiros de integração e revisores técnicos seniores costumam ler o README e perguntar: **onde está o rastro de decisões?** Esta seção é a **porta de entrada** deliberada para narrativa, posicionamento e registros de arquitetura que ficam ao lado do código — para o repositório soar como **produto governado**, e não “só mais um script”. Backlogs de execução e tabelas de PMO ficam a **um clique** em [docs/README.pt_BR.md](docs/README.pt_BR.md) (*Interno e referência*); conforme [ADR 0004](docs/adr/ADR-0004-external-docs-no-markdown-links-to-plans.md) (inglês), este README evita links Markdown diretos da superfície de pitch para a subárvore **plans** dentro de **docs**.

| Se você precisa de… | Comece aqui |
| ------------------- | ----------- |
| **Proposta de valor** (diretoria, jurídico, conformidade, compras — briefing curto) | [DECISION_MAKER_VALUE_BRIEF.pt_BR.md](docs/DECISION_MAKER_VALUE_BRIEF.pt_BR.md) · [EN](docs/DECISION_MAKER_VALUE_BRIEF.md) |
| **ADRs** (*Architecture Decision Records* — contexto, decisão, consequências) | [docs/adr/README.pt_BR.md](docs/adr/README.pt_BR.md) · [índice EN](docs/adr/README.md) |
| **Histórico de narrativa e arquitetura** (história do produto e evolução da stack — placeholder até expandir) | [NARRATIVE_AND_ARCHITECTURE_HISTORY.pt_BR.md](docs/NARRATIVE_AND_ARCHITECTURE_HISTORY.pt_BR.md) · [EN](docs/NARRATIVE_AND_ARCHITECTURE_HISTORY.md) |
| **Governança do auditor** (o que o app comprova hoje sobre varreduras, exportações e evidência operacional) | [ADR 0037](docs/adr/ADR-0037-data-boar-self-audit-log-governance.md) · enquadramento SRE: [OBSERVABILITY_SRE.pt_BR.md](docs/OBSERVABILITY_SRE.pt_BR.md) ([EN](docs/OBSERVABILITY_SRE.md)) |
| **Navegação por preocupação** (menores, notas de jurisdição, caminhos estilo CISO) | [MAP.pt_BR.md](docs/MAP.pt_BR.md) · [EN](docs/MAP.md) |
| **Dados de menores / crianças** (limiares, cruzamento, amostras — guia do operador) | [MINOR_DETECTION.pt_BR.md](docs/MINOR_DETECTION.pt_BR.md) · [EN](docs/MINOR_DETECTION.md) |
| **Índice completo da documentação** (todos os tópicos; entrada para referência interna num só lugar) | [docs/README.pt_BR.md](docs/README.pt_BR.md) · [EN](docs/README.md) |
| **Por que evidência primeiro** (filosofia pública — sem história pessoal) | [THE_WHY.pt_BR.md](docs/philosophy/THE_WHY.pt_BR.md) · [EN](docs/philosophy/THE_WHY.md) |

---

## Metodologia de compliance

O Data Boar está posicionado como **inventário técnico e triagem**: ele indica **onde** categorias de dados pessoais e sensíveis podem estar, atribui **severidade técnica** e pistas orientadas a normas, e deixa **base legal, finalidade e prazo de retenção** com **DPO / assessoria**. Para **disciplinas (ex.: índices de adequação à LGPD)**, publicamos um **mapa de módulos de verificação** e uma **priorização de colunas estilo ROPA** (o que automatizar primeiro vs o que permanece humano)—para o README não ser só lista de recurso, mas **ponte com método de compliance**. Detalhe: [COMPLIANCE_METHODOLOGY.pt_BR.md](docs/COMPLIANCE_METHODOLOGY.pt_BR.md) · [EN](docs/COMPLIANCE_METHODOLOGY.md).

---

## Visão técnica

O Data Boar roda como auditoria **CLI de execução única** ou como **API REST** (porta padrão 8088) com dashboard web. Você configura **alvos** (bancos, filesystems, APIs, shares, Power BI, Dataverse) e **detecção de sensibilidade** (regex + ML, DL opcional) em um único arquivo de config **YAML ou JSON**. Ele grava achados e metadados de sessão em um banco **SQLite** local e gera **relatórios Excel** e um **heatmap PNG** por sessão.

Se você precisa de:

- **Open core vs assinatura Pro / Enterprise (rascunho de escopo; preço ainda indefinido):** [LICENSING_OPEN_CORE_AND_COMMERCIAL.pt_BR.md](docs/LICENSING_OPEN_CORE_AND_COMMERCIAL.pt_BR.md) · [EN](docs/LICENSING_OPEN_CORE_AND_COMMERCIAL.md) · detalhes técnicos de token: [LICENSING_SPEC.md](docs/LICENSING_SPEC.md) (inglês)
- **Frameworks de conformidade, amostras, resumo jurídico (DPOs, compras):** [COMPLIANCE_FRAMEWORKS.pt_BR.md](docs/COMPLIANCE_FRAMEWORKS.pt_BR.md) · [COMPLIANCE_AND_LEGAL.pt_BR.md](docs/COMPLIANCE_AND_LEGAL.pt_BR.md) · [compliance-samples/](docs/compliance-samples/) ([índice de amostras](docs/COMPLIANCE_FRAMEWORKS.pt_BR.md#amostras-de-conformidade))
- **Metodologia de compliance (módulos de verificação, prioridades estilo ROPA):** [COMPLIANCE_METHODOLOGY.pt_BR.md](docs/COMPLIANCE_METHODOLOGY.pt_BR.md) · [EN](docs/COMPLIANCE_METHODOLOGY.md)
- **Relatórios e saídas de compliance (XLSX, heatmap, JSON de auditoria, export de maturidade; roadmap PDF):** [REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md](docs/REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md) · [EN](docs/REPORTS_AND_COMPLIANCE_OUTPUTS.md)
- **Direção do produto e cadência de releases:** [docs/releases/](docs/releases/) · [GitHub Releases](https://github.com/FabioLeitao/data-boar/releases)
- **Instalação, execução, referência CLI/API, conectores, deploy:** [Guia técnico (pt-BR)](docs/TECH_GUIDE.pt_BR.md) · [Technical guide (EN)](docs/TECH_GUIDE.md)
- **Esquema de configuração, credenciais, exemplos:** [USAGE.pt_BR.md](docs/USAGE.pt_BR.md) · [USAGE.md](docs/USAGE.md)
- **Deploy (Docker, Compose, Kubernetes):** [deploy/DEPLOY.pt_BR.md](docs/deploy/DEPLOY.pt_BR.md) · [deploy/DEPLOY.md](docs/deploy/DEPLOY.md)
- **Detecção de sensibilidade (termos ML/DL):** [SENSITIVITY_DETECTION.pt_BR.md](docs/SENSITIVITY_DETECTION.pt_BR.md) · [SENSITIVITY_DETECTION.md](docs/SENSITIVITY_DETECTION.md)
- **Dados de menores / crianças (limiar, varredura opcional ampliada, cruzamento, amostras):** [MINOR_DETECTION.pt_BR.md](docs/MINOR_DETECTION.pt_BR.md) · [MINOR_DETECTION.md](docs/MINOR_DETECTION.md)
- **Testes, segurança, contribuição:** [docs/TESTING.pt_BR.md](docs/TESTING.pt_BR.md) · [SECURITY.pt_BR.md](SECURITY.pt_BR.md) · [CONTRIBUTING.pt_BR.md](CONTRIBUTING.pt_BR.md)
- **pip via PyPI:** **`pip install data-boar`** quando publicado; até lá **git clone** + **`uv sync`** — veja [CONTRIBUTING.pt_BR.md — Repositório e identidade](CONTRIBUTING.pt_BR.md#repositório-e-identidade-de-instalação-data-boar).

**Início rápido (na raiz do repositório):** Em **Linux nativo (sem Docker)**, instale as bibliotecas de sistema **antes** de `uv sync` — veja [Guia técnico — Requisitos e preparação do ambiente](docs/TECH_GUIDE.pt_BR.md#requisitos-e-preparação-do-ambiente) (o exemplo com `apt` inclui `libpq-dev`, `unixodbc-dev` e cabeçalhos relacionados; acrescente `default-libmysqlclient-dev` se for compilar **mysqlclient**). Depois `uv sync` → prepare `config.yaml` (veja `deploy/config.example.yaml` e [USAGE](docs/USAGE.pt_BR.md)) → `uv run python main.py --config config.yaml` para execução única, ou `uv run python main.py --config config.yaml --web --allow-insecure-http` para API/dashboard em HTTP texto plano (bind padrão `127.0.0.1`, ex. <http://127.0.0.1:8088/>; para TLS use `--https-cert-file` / `--https-key-file`; use `--host 0.0.0.0` só com controles de rede). Lista de flags: `uv run python main.py --help`. **Não commite** o `config.yaml` da raiz (`.gitignore`); pode conter caminhos da LAN e segredos—veja a seção **Higiene do repositório público** em [CONTRIBUTING.pt_BR.md](CONTRIBUTING.pt_BR.md).

**Índice completo da documentação** (todos os tópicos e idiomas): [docs/README.md](docs/README.md) · [docs/README.pt_BR.md](docs/README.pt_BR.md).

**Glossário** (termos e linguagem de domínio): [docs/GLOSSARY.pt_BR.md](docs/GLOSSARY.pt_BR.md) · [docs/GLOSSARY.md](docs/GLOSSARY.md).

**Jurídico:** [TERMS_OF_USE.pt_BR.md](TERMS_OF_USE.pt_BR.md) ([EN](TERMS_OF_USE.md)) · [PRIVACY_POLICY.pt_BR.md](PRIVACY_POLICY.pt_BR.md) ([EN](PRIVACY_POLICY.md)).

**Licença e direitos autorais:** [LICENSE](LICENSE) ([pt-BR](LICENSE.pt_BR.md)) · [NOTICE](NOTICE) ([pt-BR](NOTICE.pt_BR.md)) · [docs/COPYRIGHT_AND_TRADEMARK.pt_BR.md](docs/COPYRIGHT_AND_TRADEMARK.pt_BR.md) ([EN](docs/COPYRIGHT_AND_TRADEMARK.md)).

**Mantenedor:** [Fabio Leitao no GitHub](https://github.com/FabioLeitao) — namespace `fabioleitao` no Docker Hub. O link do **blog do produto** está acima; outras redes sociais profissionais pessoais não ficam embutidas neste README — ver o perfil no GitHub (política: **`tests/test_pii_guard.py`**, **`docs/ops/COMMIT_AND_PR.md`**). No GitHub, use o campo **Website** do perfil com `https://databoar.wordpress.com` se quiser um atalho ao blog.
