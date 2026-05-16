# Conformidade e jurídico — resumo para liderança jurídica e de compliance

**English:** [COMPLIANCE_AND_LEGAL.md](COMPLIANCE_AND_LEGAL.md)

**Público principal:** **Jurídico**, **liderança de conformidade** e **DPOs** avaliando aderência, risco e evidências — **não** a **operação diária de TI** nem a parametrização técnica cotidiana. Para **YAML, limites de API, codificações e timeouts**, veja [COMPLIANCE_TECHNICAL_REFERENCE.pt_BR.md](COMPLIANCE_TECHNICAL_REFERENCE.pt_BR.md); para **config completa e comandos**, [USAGE.pt_BR.md](USAGE.pt_BR.md). Para **módulos de verificação** e **prioridades de automação estilo ROPA** (ponte metodológica para curso e auditoria), veja [COMPLIANCE_METHODOLOGY.pt_BR.md](COMPLIANCE_METHODOLOGY.pt_BR.md).

Esta página descreve **o que o Data Boar revela**, **o que não faz**, **com quais enquadramentos regulatórios** pode alinhar, **quais artefatos** apoiam auditoria, e como **serviços profissionais** ajudam a mapear a **sopa de dados** antes do produto **ingerir e digerir**.

---

## O que trazemos à tona (e sob quais dispositivos)

- **Dados pessoais e sensíveis:** Detecção de PII comum (ex.: CPF, e-mail, telefone) e **categorias especiais** no sentido da **LGPD art. 5º, II** e **GDPR art. 9** (saúde, religião, opinião política, biométrico, genético e afins).
- **Quasi-identificadores e risco de reidentificação:** Combinações que podem contribuir para identificar pessoas, em linha com **LGPD art. 5º** e **Recital 26 do GDPR**.
- **Possíveis dados relativos a menores:** Indicadores alinhados ao **LGPD art. 14** e **GDPR art. 8** (revisão humana pode ser necessária).
- **Identificadores regionais e ambíguos:** Rótulos específicos de documentos e campos ambíguos sinalizados para **confirmação manual** quando a automação não pode afirmar certeza.
- **Visibilidade multi-fonte:** Uma visão coerente da **sopa de dados** que a organização configurar—bancos, arquivos, APIs, sistemas de BI e colaboração e outros **conectores** descritos em alto nível em [COMPLIANCE_FRAMEWORKS.pt_BR.md](COMPLIANCE_FRAMEWORKS.pt_BR.md) e [TECH_GUIDE.pt_BR.md](TECH_GUIDE.pt_BR.md)—sem afirmar completude de todo legado até que os alvos estejam no escopo.
- **Triagem em arquivos e mídia:** O motor pode **amostrar contexto suficiente** em arquivos textuais para aplicar critério—reduzindo fadiga de alertas onde o conteúdo parece **entretenimento ou texto repetitivo (*boilerplate*)**, mantendo **correspondências fortes por padrão** em destaque para remediação. Em alvos de arquivo, o tratamento **opcional** de mídia rica inclui **metadados** (ex.: EXIF, ID3, tags de container), **OCR opcional** em imagens e texto de **legendas** em arquivos sidecar quando configurado — dentro de limites de amostragem e dependências opcionais (veja [USAGE.pt_BR.md](USAGE.pt_BR.md) e [COMPLIANCE_TECHNICAL_REFERENCE.pt_BR.md](COMPLIANCE_TECHNICAL_REFERENCE.pt_BR.md)). **Esteganografia**, análise completa quadro a quadro de mídia, **heurísticas de rastreadores / web bugs** (incluindo padrões típicos de redes sociais e anúncios em material educacional de segurança) e detecção sistemática de **ocultação na camada de documento** (ex.: texto microscópico ou de baixo contraste, estrutura oculta, truques de Unicode, objetos embutidos muito aninhados) **não** são descritos como exaustivos hoje; ficam em **fases futuras opt-in** — veja [TECH_GUIDE.pt_BR.md](TECH_GUIDE.pt_BR.md) e [COMPLIANCE_TECHNICAL_REFERENCE.pt_BR.md](COMPLIANCE_TECHNICAL_REFERENCE.pt_BR.md) quanto ao que está disponível hoje — para manter relatórios proporcionados, limitar cópia de dados sensíveis e evitar CPU/I/O sem limite.
- ***Jurisdiction hints* opcionais (triagem DPO/assessoria):** Com opt-in, a planilha **Report info** pode incluir notas **heurísticas** quando **metadados do achado** (ex.: coluna/caminho/`norm_tag`) sugerem **possível** relevância a certos regimes (ex.: enquadramentos de privacidade do consumidor nos EUA por estado, APPI no Japão)—**não** determinação de incidência de lei, **não** substitui análise jurídica de jurisdição e **não** usa **cópias completas** dos valores das células armazenadas no SQLite. Operadores ativam por config, CLI, API ou dashboard; veja [USAGE.pt_BR.md](USAGE.pt_BR.md) e [ADR 0026](adr/ADR-0026-optional-jurisdiction-hints-dpo-facing-heuristic-metadata-only.md) (EN).

---

## O que não fazemos

- **Não armazenamos nem exfiltramos conteúdo de PII** para fins de relatório: a ferramenta retém **metadados** (local, tipo de padrão, nível de sensibilidade, tags de framework) para **visibilidade e remediação** sem copiar dados pessoais para outro repositório. As planilhas descrevem **achados e recomendações**, não campos pessoais em bruto.

---

<a id="regulatory-alignment-built-in-and-configuration-led"></a>

## Alinhamento regulatório: embutido e por configuração

- **Já presentes em linguagem de detecção e relatórios:** **LGPD**, **GDPR**, **CCPA**, **HIPAA**, **GLBA** (referências de norma e texto de recomendação).
- **Outras jurisdições e políticas internas:** Muitos frameworks adicionais (ex. UK GDPR, PIPEDA, POPIA, APPI, PCI-DSS e perfis regionais) podem ser refletidos por **perfis de configuração**—ajustando conjuntos de padrões, rótulos e texto de relatório—**sem fork do produto**. O que “ajuste pequeno” significa na prática (arquivos, mesclagem) está documentado para times de implementação em [COMPLIANCE_FRAMEWORKS.pt_BR.md](COMPLIANCE_FRAMEWORKS.pt_BR.md). Itens de **roadmap** seguem ampliando cobertura ao longo do tempo.
- **Idiomas (resumo):** **Dados** já podem trazer muitos **scripts** nos achados e relatórios (**Unicode**); **localizações** do **dashboard** e da **documentação** para além de **inglês** e **português do Brasil** **vão sendo entregues em fases**, conforme **demanda**, junto com **amostras regionais de compliance** quando fizer sentido — uma lista **não técnica** de **direção** (sem promessa de release), mais o **tom executivo** do roadmap (diretoria e auditoria), está no parágrafo **Roadmap** do [README.pt_BR.md](../README.pt_BR.md).

**EUA — privacidade de crianças e menores (apenas mapeamento técnico):** Amostras YAML opcionais apoiam trabalho de inventário **técnico** e **operacional** (ex.: revisão do DPO, preparação para auditoria ou delimitação de escopo com assessoria jurídica)—incluindo enquadramentos associados à **COPPA federal (regra FTC)**, à **Califórnia AB 2273** e às regras do **Colorado CPA** que afetam consumidores com menos de 18 anos. **Não** é aconselhamento jurídico, **não** é verificação de idade nem prova de consentimento parental e **não** determina se determinada lei se aplica. Nomes de arquivos e passos de mesclagem: [COMPLIANCE_FRAMEWORKS.pt_BR.md](COMPLIANCE_FRAMEWORKS.pt_BR.md) e [compliance-samples/](compliance-samples/).

**EUA — HIPAA, HITECH e informações de saúde protegidas (apenas inventário técnico):** Tags de norma **HIPAA** e textos de recomendação embutidos apoiam **descoberta e mapeamento** de padrões de saúde e identificadores nas fontes configuradas — o mesmo modelo de relatório **só com metadados** do restante do produto. A **HITECH Act** reforçou a **aplicação** do HIPAA e as expectativas de notificação de incidentes; o Data Boar **não** determina se houve **violação de dados (breach HIPAA)**, **não** dimensiona **quantidade de pessoas afetadas** para fins de notificação, **não** substitui **análise de risco** formal sob a Security Rule nem redige respostas a **inquéritos HHS/OCR** (Office for Civil Rights). **Sim** ajuda a **localizar** possível exposição de **PHI/ePHI** para **priorização, remediação e artefatos repetíveis de varredura** que podem apoiar **governança e trabalho com assessoria jurídica**. Alinhe rótulos e redação via [COMPLIANCE_FRAMEWORKS.pt_BR.md](COMPLIANCE_FRAMEWORKS.pt_BR.md), [compliance-samples/](compliance-samples/), **overrides de regex e recomendação** e **serviços profissionais** opcionais acima.

**H.R. 7898 (P.L. 116-321) e “safe harbor” / porto seguro (práticas de segurança reconhecidas):** Essa lei federal **alterou a HITECH Act** para que o **HHS** **considere** se **covered entities** e **business associates** implementaram **recognized security practices** (por lei: ex. **NIST** e **Cybersecurity Act of 2015** §405(d), inclusive **HICP**, e outros programas federais reconhecidos) por **pelo menos 12 meses** ao decidir **investigações**, **auditorias** e **penalidades** — em materiais em inglês costuma aparecer como **“HIPAA safe harbor”** (em português às vezes **porto seguro** da HIPAA), como **fator mitigante**, **não** imunidade frente ao enforcement. O Data Boar **não** avalia controles da **Security Rule**, **não** certifica **recognized security practices** nem estabelece elegibilidade a **safe harbor**; **sim** apoia **evidência repetível de inventário** (onde **PHI/ePHI** pode estar) que a organização pode combinar com **documentação** de segurança sob **assessoria jurídica** e **liderança de segurança**.

---

## Gestão de risco (ISO 31000 — apenas enquadramento)

A **ISO 31000** trata da **gestão de risco na organização**—não de uma lista de funcionalidades de software. O Data Boar **não** executa sua avaliação de risco corporativo nem substitui DPO ou assessoria jurídica. Ele aumenta a **visibilidade** sobre dados pessoais e sensíveis para **priorizar** remediação técnica e produzir **evidências**; **quais** riscos tratar, aceitar ou transferir permanece **processo da organização**. **Não** reproduzimos a norma nesta página. O mesmo enquadramento em linguagem voltada à implementação (incluindo a relação com **SBOM** como prática de **cadeia de suprimentos / resposta a incidentes**) está em [ISO 31000 (enquadramento)](COMPLIANCE_FRAMEWORKS.pt_BR.md#iso-31000-enquadramento) em [COMPLIANCE_FRAMEWORKS.pt_BR.md](COMPLIANCE_FRAMEWORKS.pt_BR.md).

Quando a empresa adota a **ISO 31000** como **referência de gestão de risco**, o **inventário de dados e os relatórios de varredura** alimentam o **ciclo de tratamento de risco**: indicam **onde** se concentram dados pessoais e sensíveis, apoiam a **priorização** de controles e remediação e geram **artefatos repetíveis** para monitoração e revisão. Isso costuma ser útil para **DPO e área de compras** alinharem visibilidade técnica ao **processo de risco da organização**—sem o produto definir apetite de risco nem substituir a decisão sobre tratamento.

---

## ISO/IEC, ABNT NBR e IoC (posicionamento para DPO e segurança)

**Normas ISO/IEC e ABNT NBR no Brasil:** Organizações que buscam ou mantêm certificações costumam precisar de visibilidade **documentada** sobre **onde** dados **pessoais** e **categorias especiais** são tratados. As normas internacionais são publicadas como **ISO/IEC**; no **Brasil** o mesmo conteúdo técnico é adotado como **ABNT NBR ISO/IEC …** (títulos e referências: [GLOSSARY.pt_BR.md](GLOSSARY.pt_BR.md), seção **Normas ISO/IEC de sistemas de gestão**). O Data Boar **não** certifica, audita nem substitui avaliação de organismo acreditado; oferece **evidência técnica de inventário** — **achados só com metadados** e **varreduras repetíveis** — para uso junto de registros de **ativos** e **tratamentos**.

- **ISO/IEC 27001** (**SGSI**): ajuda a indicar **quais** alvos configurados podem concentrar informações relevantes ao **escopo** e ao **tratamento de risco** — local e categorias, **não** matriz completa de controles.
- **ISO/IEC 27701** (**PIMS**): extensão de privacidade alinhada às regulamentações declaradas (ex.: **LGPD**, **GDPR**); detalhe voltado ao produto em [Normas auditáveis e de gestão (papel de suporte)](COMPLIANCE_FRAMEWORKS.pt_BR.md#normas-auditáveis-e-de-gestão-papel-de-suporte) em [COMPLIANCE_FRAMEWORKS.pt_BR.md](COMPLIANCE_FRAMEWORKS.pt_BR.md).
- **ISO/IEC 27005** (orientações de **risco** em segurança da informação): descoberta e mapeamento **informam** decisões de tratamento sobre **dados em repouso** nas fontes configuradas; **não** substituem metodologia nem registro de risco da organização.

**Indicadores de comprometimento (IoC):** Em **operação de segurança** e **resposta a incidentes**, **IoCs** são observáveis usados para detectar ou caçar ameaças — ex.: *hash* de arquivo, domínios ou endereços IP maliciosos, assinaturas no estilo YARA — em geral aplicados a **logs**, **endpoints** e **telemetria de rede**. O Data Boar **não** é SIEM, EDR nem plataforma de *threat intelligence*: **não** ingere fluxos de firewall nem correlaciona **IoCs de rede** em todo o parque. **Sim** pode complementar **governança e preparação para IR** ao localizar **dados armazenados** onde possam existir **credenciais, tokens ou outros artefatos de segurança** (veja [Categorias sensíveis estendidas](#extended-sensitive-categories-configuration-and-services)) e ao apoiar **inventário repetível** após um evento — **só metadados** para dado pessoal, **sem** análise de malware ou imagem forense. **Não confunda** heurísticas opcionais de **rastreadores / pixels** em exportações (sinais de **governança** de privacidade) com **IoCs** — veja *tracking references (embedded)* em [GLOSSARY.pt_BR.md](GLOSSARY.pt_BR.md).

---

## Evidência e saídas (para auditoria e governança)

**Postura para stakeholders (PoC e comitês):** o **Markdown executivo** (`POC_SUMMARY_*.md`) e o **`scan_manifest_*.yaml`** associado são artefatos **adjacentes a GRC**: consolidam **status da sessão**, **achados agregados por sensibilidade**, **como as leituras foram delimitadas** (amostragem, timeouts, postura por dialeto quando relevante) e **prioridades de remediação** (incluindo **inventário por padrão** com ação técnica), mantendo o corpo do Markdown **sem dados pessoais em bruto**. Apoiam conversas de **risco e conformidade** e materiais para **DPO/CISO**; **não** substituem **suite GRC** corporativa completa, **certificado** regulatório nem **substituição** de parecer jurídico ou atestações conduzidas por assessoria. O operador pode **regenerar** o Markdown **só a partir do SQLite local** com **`data-boar-report`** (sem novas leituras ao vivo nos alvos). Detalhe operacional: [USAGE.pt_BR.md](USAGE.pt_BR.md) (seção 5); mapa de saídas: [REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md](REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md).

- **Relatórios Excel** por **sessão** de varredura: achados por fonte, campo/caminho, tipo de padrão, sensibilidade e texto de recomendação orientado a framework (base legal, risco, ação sugerida, prioridade quando configurado).
- **Heatmaps** e **visões de tendência** entre sessões para mostrar **evolução**, não só um instantâneo.
- **Execuções repetíveis** (incluindo automação via API) para alinhar ao **modelo operacional**; detalhe técnico de agendamento e limites: [COMPLIANCE_TECHNICAL_REFERENCE.pt_BR.md](COMPLIANCE_TECHNICAL_REFERENCE.pt_BR.md).
- **Sinais ao operador (opcional, webhooks):** Com `notifications` habilitado na configuração, a aplicação pode enviar um **resumo curto** ao concluir uma varredura (ex.: Slack, Teams, URL genérica / ponte Signal, ou campos Telegram legados), inclusive **vários canais** ou **cópia ao tenant** quando configurado — **padrão desligado**; é conveniência operacional e **não substitui** os relatórios Excel nem constitui prova jurídica por si só. Política de canais: [OPERATOR_NOTIFICATION_CHANNELS.pt_BR.md](ops/OPERATOR_NOTIFICATION_CHANNELS.pt_BR.md). Detalhes: [USAGE.pt_BR.md — Notificações ao operador](USAGE.pt_BR.md#notificações-ao-operador-opcional).
- **Identidade de build e postura de runtime (operadores):** os relatórios registram a **versão da aplicação** na folha “Report info”; há plano para exibir de forma explícita **release vs desenvolvimento** e, opcionalmente, **sinais de integridade** para ambientes enterprise (sem alteração do alcance jurídico até implementar). Para **checagens operacionais** de implantação (não prova jurídica por si só), a API **`GET /status`** inclui um snapshot **`runtime_trust`** que resume se a configuração/ambiente em execução está aderente ao esperado (ex.: overrides locais inesperados).

---

## Serviços profissionais: mapear a sopa de dados

Raramente a organização tem um inventário único e limpo de cada **ingrediente** da **sopa de dados**—cópias sombra, exportações legadas, modelos de BI e compartilhamentos ad hoc são frequentes. O **Data Boar** **ingere e digere** o que você apontar; **descobrir e priorizar** fontes, **afinar** tags de norma e linguagem de recomendação e **alinhar** expectativa jurídica ao escopo técnico costuma ser exercício **conjunto**.

Há **serviços contratados** (consultoria e ajustes finos) para apoiar: escopo de alvos, alinhamento de configuração ao **mix regulatório** e redução do tempo até confiança operacional—**sem substituir** DPO ou assessoria jurídica. Limites comerciais e de licenciamento: [LICENSING_OPEN_CORE_AND_COMMERCIAL.md](LICENSING_OPEN_CORE_AND_COMMERCIAL.md). **Contato** pelos canais que já utiliza com o mantenedor (ex.: GitHub, e-mail profissional)—sem obrigação.

---

<a id="extended-sensitive-categories-configuration-and-services"></a>

## Categorias sensíveis estendidas (configuração e serviços)

Além dos **enquadramentos já embutidos** (ex.: LGPD, GDPR, HIPAA, dados de cartão no sentido PCI), organizações podem precisar de **descoberta e mapeamento** para:

- **Dados de saúde / registros clínicos** (prontuário longitudinal, tipos de formulário, codificação de diagnóstico—além de um único rótulo HIPAA no relatório);
- **Indicadores ligados a propriedade intelectual** (nomes de colunas ou conteúdo que sugiram marcas, registros ou ativos proprietários—**sem** determinar titularidade jurídica);
- **Artefatos de segurança** em dados armazenados (credenciais, tokens, material criptográfico—**diferente da** **redação em logs** do produto, que só protege logs operacionais);
- **Dados de onboarding e adjacentes a PLD/AML (PEP, KYC, CDD, EDD):** **Onde** podem aparecer dados pessoais de **cliente**, **beneficiário final** ou **processo** em **legado**, **exportações** e **colaboração** — incluindo **colunas ou documentos** com **antecedentes criminais**, **resultado de background check** ou **certidão de antecedentes** (quando vinculados a pessoa **identificável**: **dado pessoal**; enquadramento jurídico — **GDPR** art. **10** e regras **contextuais** na **LGPD** com **assessoria** — **não** é automaticamente o mesmo rol do art. **5º, II**, em todos os casos) — **não** é **matching** com listas de **sanções** ou **PEP**, **não** é **verificação de identidade** nem **monitoramento transacional** (isso permanece em plataformas **KYC/AML** especializadas).

**Posicionamento PEP / KYC / CDD / EDD:** Na prática, programas de **KYC**, **CDD**, **EDD** e **PEP** combinam **screening** em listas, checagem documental e **monitoramento** com **fornecedores dedicados**; o Data Boar **não** confronta indivíduos com listas **OFAC**, **ONU**, **UE** ou bases comerciais de **PEP** nem **determina** status de PEP. **Sim** pode ajudar a **achar possível PII** e **artefatos de onboarding** retidos em excesso na **sopa de dados** para equipes de **privacidade** e **risco operacional** **priorizarem remediação** e **higiene de evidências** — com **regex**, termos **ML/DL**, **overrides** de recomendação, **[compliance-samples/](compliance-samples/)** e **consultoria** opcional para alinhar **léxico de política** e **locale**. **Sem** certificação **AML**; achados **só com metadados**.

**Como isso é atendido:** o mesmo **motor** já suporta **regex overrides**, **termos de treinamento ML/DL** e **overrides de texto de recomendação** (veja [SENSITIVITY_DETECTION.pt_BR.md](SENSITIVITY_DETECTION.pt_BR.md) e [COMPLIANCE_FRAMEWORKS.pt_BR.md](COMPLIANCE_FRAMEWORKS.pt_BR.md)). Afinar **ruído**, **idioma/região** (formato de dados e vocabulário) e **léxico setorial** costuma beneficiar de **consultoria** para alinhar alvos e padrões à **sopa de dados** e ao apetite de risco. O produto **não** certifica categorias legais por sigla; produz **achados só com metadados** para **governança e remediação**.

**Roadmap interno:** amostras de perfil opcionais e posicionamento mais detalhado podem constar na árvore de **planos** do repositório (mantenedores: **docs/README** — *Internal and reference*). **Decisão de posicionamento (arquitetura):** [ADR 0025 — Compliance positioning: evidence and inventory, not a legal-conclusion engine](adr/ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md) (texto canônico em inglês).

---

## Posicionamento flexível: entrega conjunta sem eliminar risco jurídico

O produto é **feito para se adaptar**: **perfis de configuração**, **overrides** de **regex** e de **recomendação**, **[compliance-samples/](compliance-samples/)** e **serviços profissionais** podem afinar a descoberta e a redação dos relatórios ao **mix regulatório** e à **sopa de dados** — **sem** fork do motor principal.

**Papel de apoio (como ajudamos):** o Data Boar **levanta indicadores técnicos** (correspondências de padrão, sensibilidade, etiquetas orientadas a normas, localizações) para **jurídico**, **DPO**, **analistas de compliance** e **consultoria** **priorizarem análise**. **Não** substitui **conclusões jurídicas** do tipo “isto é ilícito” ou “há obrigação de notificar”; isso depende de **julgamento humano** sobre **fatos**, **finalidade**, **base legal** e **processo** interno. Em documentação e conversas comerciais, prefira **exposição possível**, **indicadores para revisão especializada** e **evidência para governança** — **não** **determinações** de **ilicitude**.

**Valor em conjunto:** as organizações ganham **artefatos repetíveis de inventário**, relatórios **só com metadados** e recomendações voltadas à **remediação**; **consultoria jurídica** e **especialistas** aplicam **direito** e **política**; a **consultoria** do projeto faz a ponte entre **escopo** e **configuração**. Esse modelo de **entrega conjunta** é **intencional** — veja [ADR 0025](adr/ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md).

**Onde isto fica registrado:** esta página, [COMPLIANCE_FRAMEWORKS.pt_BR.md](COMPLIANCE_FRAMEWORKS.pt_BR.md) e **ADR 0025**. Orientação de mantenedores e *backlog* setorial: plano interno **`PLAN_COMPLIANCE_EVIDENCE_MAPPING.md`** (navegação via [docs/README.pt_BR.md](README.pt_BR.md) — *Interno e referência*; sem link direto para `docs/plans/` em docs de audiência externa, conforme [ADR 0004](adr/ADR-0004-external-docs-no-markdown-links-to-plans.md)). **Não** há documento de **“journal QA”** separado para este posicionamento no repositório; detalhes **só do operador** podem continuar em **`docs/private/`** (gitignored), conforme [PRIVATE_OPERATOR_NOTES.md](PRIVATE_OPERATOR_NOTES.md).

---

## Próximos passos

| Necessidade                                               | Documento                                                                                                                    |
| -----------                                               | ---------                                                                                                                    |
| **Resumo jurídico / compliance (esta página)**            | Você está aqui                                                                                                               |
| **TI: codificações, limites de API, timeouts, automação** | [COMPLIANCE_TECHNICAL_REFERENCE.pt_BR.md](COMPLIANCE_TECHNICAL_REFERENCE.pt_BR.md) ([EN](COMPLIANCE_TECHNICAL_REFERENCE.md)) |
| **Lista de frameworks e perfis de exemplo**               | [COMPLIANCE_FRAMEWORKS.pt_BR.md](COMPLIANCE_FRAMEWORKS.pt_BR.md) · [COMPLIANCE_FRAMEWORKS.md](COMPLIANCE_FRAMEWORKS.md)      |
| **Esquema de config, credenciais, CLI/API**               | [USAGE.pt_BR.md](USAGE.pt_BR.md) · [USAGE.md](USAGE.md)                                                                      |
| **Política de segurança**                                 | [SECURITY.pt_BR.md](SECURITY.pt_BR.md) · [SECURITY.md](SECURITY.md)                                                          |
| **Instalação, conectores, deploy**                        | [TECH_GUIDE.pt_BR.md](TECH_GUIDE.pt_BR.md) · [TECH_GUIDE.md](TECH_GUIDE.md)                                                  |
| **Glossário**                                             | [GLOSSARY.pt_BR.md](GLOSSARY.pt_BR.md) · [GLOSSARY.md](GLOSSARY.md)                                                          |
| **Índice completo da documentação**                       | [README.pt_BR.md](README.pt_BR.md) · [README.md](README.md)                                                                  |
