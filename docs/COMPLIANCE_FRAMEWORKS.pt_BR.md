# Frameworks de conformidade e extensibilidade

**English:** [COMPLIANCE_FRAMEWORKS.md](COMPLIANCE_FRAMEWORKS.md)

A aplicação auxilia times de DPO, segurança e **conformidade** a descobrir e mapear dados pessoais ou sensíveis com rótulos regulatórios e texto de recomendação configuráveis. Este documento descreve quais frameworks são referenciados explicitamente hoje, onde encontrar exemplos de configuração e como estender o suporte a outros (ex.: UK GDPR, PIPEDA, APPI, POPIA) sem alterar código.

**Tomadores de decisão (jurídico / compliance):** Para visão executiva, evidências de relatório e serviços opcionais, veja primeiro [COMPLIANCE_AND_LEGAL.pt_BR.md](COMPLIANCE_AND_LEGAL.pt_BR.md). Detalhes técnicos (codificações, limites de API, timeouts) estão em [COMPLIANCE_TECHNICAL_REFERENCE.pt_BR.md](COMPLIANCE_TECHNICAL_REFERENCE.pt_BR.md).

### Saídas “prontas para comitê” (briefings vs profundidade de config)

**`norm_tag`**, **overrides de recomendação** e o **Excel** continuam sendo o **eixo principal** para alinhar **detecção e texto de relatório** a cada **perfil de framework** que você mescla a partir de [compliance-samples/](compliance-samples/). Para **leitura DPO/CISO** de uma varredura **já concluída**, o produto pode também emitir **Markdown executivo** e **`scan_manifest_*.yaml`** junto do XLSX: resumem **postura de execução** (amostragem, timeouts, notas de dialeto quando couber) e **priorização de remediação** sem colar literais sensíveis — útil quando a **assessoria** pergunta *o quê* foi rotulado e *como* as leituras foram limitadas. São artefatos **adjacentes à governança**, **não** substituto de **suite GRC** de programa nem de **chancela** jurídica — veja a seção **Evidência e saídas** em [COMPLIANCE_AND_LEGAL.pt_BR.md](COMPLIANCE_AND_LEGAL.pt_BR.md) e [REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md](REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md).

### Vocabulário do motor (POC, decks e docs técnicos)

O [README.md](../README.md) na seção **“Para gestores e líderes de conformidade”** permanece em **linguagem executiva acessível** (por exemplo **farejando com critério** na metáfora da **sopa de dados**). **Não** é obrigatório usar os rótulos internos abaixo nesse bloco.

Para **decks**, **apostilas de workshop** e **documentação técnica estruturada** de conformidade (esta página, [COMPLIANCE_TECHNICAL_REFERENCE.pt_BR.md](COMPLIANCE_TECHNICAL_REFERENCE.pt_BR.md), [GLOSSARY.pt_BR.md](GLOSSARY.pt_BR.md)), rótulos opcionais pareados — **Data Sniffing** (**passo de descoberta e amostragem**: conectores, leituras delimitadas, detecção de sensibilidade) e **Deep Boring** (**profundidade do artefato de relatório**: pastas Excel, alinhamento de **norm_tag**, **recommendation overrides**, heatmaps) — estabilizam o vocabulário. São **duas metades da mesma sessão**, não recursos concorrentes. Planos internos podem ainda dizer *“deep sniffing”* ou *“farejar mais”*; ao subir texto para **deck** ou **material técnico** para compras/DPO, você pode padronizar em **Data Sniffing** / **Deep Boring** conforme [GLOSSARY.pt_BR.md](GLOSSARY.pt_BR.md#1-identidade-do-produto-e-pano-de-dados) — **sem** tratar o pitch executivo do README como lugar para esses nomes.

<a id="detecção-determinística-vs-hype-de-llm-generativo"></a>

### Detecção determinística vs hype de LLM generativo (postura do produto)

**Evidência descoberta vs narrativa de “IA”.** O motor produz **achados repetíveis** a partir de **regex**, **padrões nomeados** e **ML/DL supervisionado** com **seus** termos de treino — além de sinais estruturados como **agregação de quasi-identificadores**, colunas ligadas a **menores** e **dicas de jurisdição / tensão** (sempre **heurística**, nunca “lei aplicável” no software). Esse contrato difere de **LLMs generativos**, que otimizam texto fluente e podem variar entre execuções. Arquitetura e expectativa de auditoria: [TECH_GUIDE.pt_BR.md](TECH_GUIDE.pt_BR.md#detection-stack-vs-generative-llms); vocabulário (**LLM**, **pilha de detecção determinística**, **Google Gemini** como ferramenta de manutenção): [GLOSSARY.pt_BR.md](GLOSSARY.pt_BR.md) §8–9 e [docs/ops/LLM_AGENT_EDITING_CAUTION.pt_BR.md](ops/LLM_AGENT_EDITING_CAUTION.pt_BR.md). Linha do tempo **neutra face a fornecedores** (anos 1950 → **invernos da IA** → **sistemas especialistas** → ML estatístico → **DL** → **LLMs**): [AI_EVOLUTION_PRIMER.pt_BR.md](AI_EVOLUTION_PRIMER.pt_BR.md) ([EN](AI_EVOLUTION_PRIMER.md)).

## Regulamentações que já suportamos (embutidas e exemplos de config)

**Embutidas (prontas para uso):** O detector e os relatórios referenciam explicitamente **LGPD** (Brasil), **GDPR** (UE), **CCPA** (Califórnia), **HIPAA** (saúde EUA) e **GLBA** (financeiro EUA). Os achados usam essas norm tags e textos de recomendação por padrão.

**Exemplos de configuração:** Fornecemos exemplos de arquivos de config para alinhar a mais regulamentações sem mudar código (incluindo amostras YAML por região em **`compliance-samples/`**, como **152-FZ (Rússia)** — ver [lista de amostras e links](#lista-de-amostras-e-links)):

- **[regex_overrides.example.yaml](regex_overrides.example.yaml)** – padrões regex customizados com `norm_tag` (ex.: LGPD Art. 5, CCPA). Copie e estenda para outros identificadores (ex.: NIN UK, SIN canadense) e defina `norm_tag` para seu framework.
- **Overrides de recomendação** – em [USAGE.pt_BR.md](USAGE.pt_BR.md) (seção de relatório) há `report.recommendation_overrides`: lista de `norm_tag_pattern`, `base_legal`, `risk`, `recommendation`, `priority`, `relevant_for`. Use para adaptar o texto do relatório a qualquer regulamentação (UK GDPR, PIPEDA, POPIA, APPI, PCI-DSS ou normas internas).
- **Termos ML/DL** – [SENSITIVITY_DETECTION.pt_BR.md](SENSITIVITY_DETECTION.pt_BR.md) e o config principal suportam `ml_patterns_file`, `dl_patterns_file` ou inline `sensitivity_detection.ml_terms` / `dl_terms` para adicionar termos por framework (ex.: “personal information”, “data subject”, “responsible party”) e melhorar detecção e rotulagem.

**Amostras de conformidade (um perfil por regulamento):** Amostras de config para **UK GDPR**, **EU GDPR**, **Benelux**, **PIPEDA**, **POPIA**, **APPI**, **PCI-DSS**, **Rússia (Lei federal 152-FZ)** e outras regiões estão em [compliance-samples/](compliance-samples/). Cada amostra é um único arquivo YAML com padrões regex, termos ML e recommendation overrides para esse framework. Veja a seção [Amostras de conformidade](#amostras-de-conformidade) abaixo para a lista completa, o que vai em cada arquivo e como usar. Para **idioma e público-alvo** (ex.: PIPEDA → EN + FR no Canadá; **152-FZ** → termos **EN + RU** na amostra russa), veja o [README de compliance-samples](compliance-samples/README.pt_BR.md).

---

## Setor segurador no Brasil (ancoragem LGPD + referências prudenciais) {#setor-segurador-brasil-lgpd-referencias-prudenciais}

**Não é aconselhamento jurídico.** Este trecho orienta leitores técnicos e de **conformidade** que atuam em **seguros privados** no Brasil (sociedades supervisionadas pela **SUSEP**, corretores e prestadores). **Não** substitui assessoria jurídica, orientações da **ANPD** ou prática perante o supervisor prudencial.

**O que o produto faz aqui:** o Data Boar apoia **descoberta, amostragem e relatórios orientados a metadados** (incluindo texto configurável de **`norm_tag`**). **Não** certifica **conformidade** com a **LGPD**, com regras **SUSEP/CNSP**, com solvência, licenciamento ou qualquer resultado supervisionado.

**LGPD como âncora principal de proteção de dados:** dados pessoais e sensíveis tratados em fluxos de seguro continuam sujeitos à **Lei Geral de Proteção de Dados**. Texto oficial: [Planalto — Lei nº 13.709/2018](https://www.planalto.gov.br/ccivil_03/leis/2018/l13709.htm). A **ANPD** publica orientações aplicáveis em setores cruzados: [gov.br — ANPD](https://www.gov.br/anpd/pt-br).

**Camada prudencial e de conduta de mercado (setor, sem substituir a LGPD):** a **SUSEP** supervisiona os seguros privados no Brasil; o **CNSP** integra o arcabouço normativo com resoluções que as sociedades precisam operacionalizar **em conjunto** com a LGPD quando houver dados pessoais. Ponto de entrada oficial para instrumentos e comunicações: [gov.br — SUSEP](https://www.gov.br/susep/pt-br). **Circulares** e normas do **CNSP** aparecem nos canais oficiais de **legislação / normativos** do mesmo portal; use sempre o **texto consolidado atual** em **gov.br** antes de depender de qualquer link profundo.

**Esqueleto YAML opcional:** para vocabulário **genérico** de colunas e documentos do **setor segurador** com strings de **`norm_tag`** orientadas a **inventário sob a LGPD** (ainda **sem** certificação regulatória), veja [compliance-sample-br_insurance_lgpd_anchor.yaml](compliance-samples/compliance-sample-br_insurance_lgpd_anchor.yaml) na tabela abaixo. Combine com o perfil completo **[compliance-sample-lgpd.yaml](compliance-samples/compliance-sample-lgpd.yaml)** quando precisar de cobertura de identificadores brasileiros (CPF, CNPJ, etc.).

---

## Amostras de conformidade

Arquivos de configuração de amostra para **UK GDPR**, **EU GDPR**, **Benelux**, **PIPEDA**, **POPIA**, **APPI**, **PCI-DSS**, **Rússia (152-FZ)** e frameworks regionais opcionais estão em [compliance-samples/](compliance-samples/). Cada arquivo é autocontido (regex overrides, termos ML, recommendation overrides) para você habilitar um framework apontando o config para esse arquivo e mesclando os overrides.

Lei, orientações de autoridade e o uso real de identificadores evoluem em muitas jurisdições que já amostramos — não só nas de mudança legislativa mais rápida. **O texto legal e os atos oficiais também são reescritos ou substituídos com o tempo**, então um YAML que “batia no ano passado” pode precisar de ajuste mesmo com cenário político estável. Vale **atualizar periodicamente** as amostras das quais você depende (regex, termos, overrides), num ritmo alinhado ao risco — **trimestralmente ou antes de um release minor** é um padrão razoável para perfis de alto risco; veja [Manutenção das amostras](compliance-samples/README.pt_BR.md#manutenção-das-amostras) no README das amostras. O cabeçalho da amostra **152-FZ** destaca churn normativo frequente; use como modelo para documentar risco de revisão em outras jurisdições.

### Lista de amostras e links

| Regulamento / região            | Arquivo                                                                                                     | Finalidade                                                                                                                          |
| --------------------            | -------                                                                                                     | ----------                                                                                                                          |
| **LGPD (Brasil)**               | [compliance-sample-lgpd.yaml](compliance-samples/compliance-sample-lgpd.yaml)                               | Termos PT-BR + EN; regex RG/CEP; regex de **geolocalização precisa** (mesma geometria que as amostras VCDPA / RGPD UE); implantações brasileiras.                                                                          |
| **Brasil (setor segurador — esqueleto inventário LGPD)** | [compliance-sample-br_insurance_lgpd_anchor.yaml](compliance-samples/compliance-sample-br_insurance_lgpd_anchor.yaml) | Léxico genérico de seguros + **`norm_tag`** ancorada em inventário LGPD; **não** é certificação SUSEP/CNSP (ver [subseção setor segurador](#setor-segurador-brasil-lgpd-referencias-prudenciais)). |
| **UK GDPR**                     | [compliance-sample-uk_gdpr.yaml](compliance-samples/compliance-sample-uk_gdpr.yaml)                         | Pós-Brexit, ICO; norm_tag e recommendation overrides; regex de **geolocalização precisa** (mesma geometria VCDPA / RGPD UE).                                                                               |
| **EU GDPR (EEE)**               | [compliance-sample-eu_gdpr.yaml](compliance-samples/compliance-sample-eu_gdpr.yaml)                         | Regulamento 2016/679 Art. 4(1), EDPB, DPAs nacionais; EN + DE/FR opcionais.                                                         |
| **Benelux (BE, NL, LU)**        | [compliance-sample-benelux.yaml](compliance-samples/compliance-sample-benelux.yaml)                         | Base EU GDPR + IDs nacionais (BSN, NISS, LU); overrides DPA nacionais; EN + NL/FR.                                                  |
| **PIPEDA (Canadá)**             | [compliance-sample-pipeda.yaml](compliance-samples/compliance-sample-pipeda.yaml)                           | Informação pessoal, consentimento; identificadores canadenses (ex.: SIN); regex de **geolocalização precisa** (mesma geometria VCDPA / RGPD UE); EN + FR.                                                  |
| **POPIA (África do Sul)**       | [compliance-sample-popia.yaml](compliance-samples/compliance-sample-popia.yaml)                             | POPIA Lei 4/2013; Regulador de Informação; regex ID sul-africano; **geolocalização precisa** (mesma geometria VCDPA / EU GDPR); informação pessoal especial (s.26), dados de crianças (s.34), transferências transfronteiriças (s.72); EN. |
| **APPI (Japão)**                | [compliance-sample-appi.yaml](compliance-samples/compliance-sample-appi.yaml)                               | Informação pessoal e sensível (要配慮個人情報); My Number; regex de **geolocalização precisa** (位置情報; mesma geometria VCDPA / EU GDPR); termos EN + japonês; alinhamento PPC; revisão 2022.                    |
| **PCI-DSS**                     | [compliance-sample-pci_dss.yaml](compliance-samples/compliance-sample-pci_dss.yaml)                         | Padrões de cartão de pagamento e recommendation overrides para comerciantes/avaliadores.                                            |
| **Filipinas (DPA)**             | [compliance-sample-philippines_dpa.yaml](compliance-samples/compliance-sample-philippines_dpa.yaml)         | RA 10173, NPC; informação pessoal/sensível.                                                                                         |
| **Austrália (Privacy Act)**     | [compliance-sample-australia_privacy.yaml](compliance-samples/compliance-sample-australia_privacy.yaml)     | Privacy Act 1988 (Cth; Emenda 2024), OAIC, APPs; regex TFN/Medicare/ABN/Passaporte; **geolocalização precisa** (mesma geometria VCDPA / EU GDPR); esquema NDB; informação sensível (s.6); EN. |
| **Singapura (PDPA)**            | [compliance-sample-singapore_pdpa.yaml](compliance-samples/compliance-sample-singapore_pdpa.yaml)           | PDPA 2012 (alterada 2020/2021), PDPC; regex NRIC/FIN/UEN; **geolocalização precisa** (mesma geometria VCDPA / EU GDPR); DNC, notificação obrigatória de violação; EN. |
| **UAE (PDPL)**                  | [compliance-sample-uae_pdpl.yaml](compliance-samples/compliance-sample-uae_pdpl.yaml)                       | Decreto-Lei 45/2021; dados pessoais/sensíveis; EN + AR opcional.                                                                    |
| **Argentina (PDPA)**            | [compliance-sample-argentina_pdpa.yaml](compliance-samples/compliance-sample-argentina_pdpa.yaml)           | Ley 25.326, DNPDP; datos personales; ES + EN; regex CUIT/CUIL/DNI.                                                                  |
| **Quênia (DPA)**                | [compliance-sample-kenya_dpa.yaml](compliance-samples/compliance-sample-kenya_dpa.yaml)                     | Data Protection Act 2019, ODPC; dados pessoais, controlador.                                                                        |
| **Índia (DPDP)**                | [compliance-sample-india_dpdp.yaml](compliance-samples/compliance-sample-india_dpdp.yaml)                   | DPDP Act 2023, DPBI; regex Aadhaar/PAN; **geolocalização precisa** (mesma geometria VCDPA / EU GDPR); termos ML SDF / transferência internacional / dados de crianças; EN; regras em evolução — revalidar. |
| **Turquia (KVKK)**              | [compliance-sample-turkey_kvkk.yaml](compliance-samples/compliance-sample-turkey_kvkk.yaml)                 | Lei 6698, Conselho KVKK; kişisel veri; EN + TR; regex TC Kimlik.                                                                    |
| **Nova Zelândia (Privacy Act)** | [compliance-sample-new_zealand_privacy.yaml](compliance-samples/compliance-sample-new_zealand_privacy.yaml) | Privacy Act 2020, OPC; informação pessoal, IPPs.                                                                                    |
| **Rússia (152-FZ)**             | [compliance-sample-russia_152_fz.yaml](compliance-samples/compliance-sample-russia_152_fz.yaml)             | Lei federal 152-FZ (266-FZ 2022), Roskomnadzor; **geolocalização precisa**; regex SNILS e INN heurístico; categorias especiais (Art. 10); notificação obrigatória (72 h); localização (Art. 22.1); termos EN + RU; **revisar com frequência**. |
| **Arábia Saudita (PDPL)**       | [compliance-sample-saudi_pdpl.yaml](compliance-samples/compliance-sample-saudi_pdpl.yaml)                   | Royal Decree M/19, SDAIA; dados pessoais/sensíveis.                                                                                 |
| **Israel (PPL)**                | [compliance-sample-israel_ppl.yaml](compliance-samples/compliance-sample-israel_ppl.yaml)                   | Privacy Protection Law, PPA; informação pessoal, registrador de base.                                                               |
| **Colômbia (Lei 1581)**         | [compliance-sample-colombia_1581.yaml](compliance-samples/compliance-sample-colombia_1581.yaml)             | Ley 1581/2012, SIC; datos personales; ES + EN; regex CC/NIT.                                                                        |
| **Chile (Privacidade)**         | [compliance-sample-chile_privacy.yaml](compliance-samples/compliance-sample-chile_privacy.yaml)             | Lei 19.628; datos personales; ES + EN; regex RUT.                                                                                   |
| **Nigéria (NDPR)**              | [compliance-sample-nigeria_ndpr.yaml](compliance-samples/compliance-sample-nigeria_ndpr.yaml)               | NDPR 2019, NITDA; dados pessoais, controlador.                                                                                      |
| **Marrocos (Lei 09-08)**        | [compliance-sample-morocco_09_08.yaml](compliance-samples/compliance-sample-morocco_09_08.yaml)             | Lei 09-08, CNDP; données à caractère personnel; FR + EN; regex CIN.                                                                 |
| **Suíça (FADP)**                | [compliance-sample-switzerland_fadp.yaml](compliance-samples/compliance-sample-switzerland_fadp.yaml)       | FADP revisada, FDPIC; dados pessoais; EN + DE/FR/IT opcionais; regex AHV/UID.                                                       |
| **EUA (FTC COPPA)**             | [compliance-sample-us_ftc_coppa.yaml](compliance-samples/compliance-sample-us_ftc_coppa.yaml)               | Privacidade online de crianças (âmbito federal EUA) — **mapeamento técnico**; sem verificação de idade nem aconselhamento jurídico. |
| **EUA (CA AB 2273)**            | [compliance-sample-us_ca_ab2273_caadca.yaml](compliance-samples/compliance-sample-us_ca_ab2273_caadca.yaml) | Califórnia, código de desenho apropriado à idade — **rotulagem**; aplicabilidade depende de fatos e assessoria jurídica; regex de **geolocalização precisa** (mesma geometria VCDPA / RGPD UE) para inventário.            |
| **EUA (CO CPA — menores)**      | [compliance-sample-us_co_cpa_minors.yaml](compliance-samples/compliance-sample-us_co_cpa_minors.yaml)       | Colorado CPA / contextos com menores de 18 anos — **mapeamento técnico**; não detecta “menor conhecido” de forma jurídica.          |
| **EUA (Virgínia — VCDPA)**      | [compliance-sample-us_va_vcdpa.yaml](compliance-samples/compliance-sample-us_va_vcdpa.yaml)                 | Virginia Consumer Data Protection Act: léxico sensível + regexes de **geolocalização precisa**; **sem** análise automática de isenções B2B/emprego — ver cabeçalho da amostra. |
| **EUA (Califórnia — CPRA/CCPA)** | [compliance-sample-us_ca_cpra.yaml](compliance-samples/compliance-sample-us_ca_cpra.yaml)              | CCPA alterada pela CPRA: exporta `CCPA_SSN` do core + CNH-CA / ITIN; regex de **geolocalização precisa** SPI (§ 1798.140(ae)(1)(H)); termos ML de privacidade do consumidor; enquadramento CPPA. |
| **EUA (FCPA / pacote política interna)** | [compliance-sample-us_fcpa_internal_policy_pack.yaml](compliance-samples/compliance-sample-us_fcpa_internal_policy_pack.yaml) | Léxico **FCPA** e **política anticorrupção** interna (empregador); **inventário** — não detecção de suborno nem conclusão jurídica. |

### O que vai em cada arquivo

Cada amostra pode fornecer até três tipos de conteúdo. Seu **config principal** referencia ou mescla assim:

| Chave de config / arquivo                                     | Finalidade                                                                                                     | O que a amostra fornece                                                                                                                                                  |
| -------------------------                                     | ----------                                                                                                     | -----------------------                                                                                                                                                  |
| **`regex_overrides_file`**                                    | Padrões regex customizados; match → achado HIGH com `norm_tag` dado.                                           | Lista de `{ name, pattern, norm_tag }` (ex.: NIN UK, SIN canadense, ID SA). Amostras podem usar chave `regex` ou `patterns`.                                             |
| **`ml_patterns_file`** / **`sensitivity_detection.ml_terms`** | Termos de treinamento ML (e DL); nomes de coluna e texto amostrado classificados como sensitive/non_sensitive. | Lista de `{ text, label }` com termos por framework (ex.: “data subject”, “personal information”, “responsible party”). Amostras podem usar chave `terms` ou `ml_terms`. |
| **`report.recommendation_overrides`**                         | Override de “Base legal”, “Risco”, “Recomendação”, “Prioridade”, “Relevante para” por `norm_tag`.              | Lista de `{ norm_tag_pattern, base_legal, risk, recommendation, priority, relevant_for }` para mesclar no config.                                                        |

O mesmo arquivo YAML pode conter **regex**, **terms** e **recommendation_overrides**; defina `regex_overrides_file` e `ml_patterns_file` com o caminho desse arquivo e copie o bloco **recommendation_overrides** para o config principal em `report.recommendation_overrides`.

### Como usar uma amostra

1. **Escolha a amostra** do seu regulamento na tabela acima (ou em [compliance-samples/README.pt_BR.md](compliance-samples/README.pt_BR.md)).
1. **Defina os caminhos no config principal** (ex.: `config.yaml`):

   ```yaml
   regex_overrides_file: docs/compliance-samples/compliance-sample-pipeda.yaml
   ml_patterns_file: docs/compliance-samples/compliance-sample-pipeda.yaml
   ```

   Use o mesmo arquivo para ambos se a amostra tiver `regex` e `terms`.

1. **Mescle os recommendation overrides:** Copie a lista `recommendation_overrides` do arquivo da amostra para o config em `report.recommendation_overrides` (mescle com overrides que você já tiver). Veja [USAGE.pt_BR.md](USAGE.pt_BR.md) (seção de relatório) para a estrutura.
1. **Execute a varredura** (CLI ou API). Os achados usarão as norm tags e o texto de recomendação da amostra; o relatório Excel exibirá Base legal, Risco, Recomendação e Prioridade do framework.

---

## Operação multilíngue, multi-encoding e multirregional {#operação-multilíngue-multi-encoding-e-multirregional}

Seja qual for o **idioma**, **encoding** ou **região** da sua sopa de dados, a aplicação foi pensada para lidar com isso: você pode rodar varreduras e relatórios de conformidade no idioma e encoding da sua região sem quebrar em produção.

### O que é suportado

- **Múltiplos idiomas em termos e relatórios:** As amostras de conformidade podem incluir termos no(s) idioma(s) da região alvo (ex.: EN+FR para PIPEDA/Canadá, PT-BR+EN para LGPD/Brasil, japonês ou árabe para APAC/MENA, **EN+RU para 152-FZ na Rússia**). O relatório Excel e o texto de recomendação suportam **Unicode** (ex.: base_legal e recommendation em japonês, árabe, **cirílico** ou caracteres acentuados).
- **Scripts e charset nos dados:** O pipeline de varredura e relatório é **Unicode-first**. Conteúdo real costuma misturar **latim**, **cirílico** (ex.: russo), **CJK** (ex.: kanji/kana em japonês) e **árabe** (incluindo apresentação RTL quando o visualizador suporta). **Encodings legados em bytes** para configs e arquivos de padrões são tratados com **auto-detecção** (config principal) e **`pattern_files_encoding`** (arquivos de padrões); **sniffing e heurísticas de encoding** para corpus específicos podem ser **afinados** (config, padrões, conectores) quando a implantação exige comportamento mais rígido — fale conosco para **consultoria** se times de TI, segurança, compliance ou DPO precisarem de um **perfil customizado de idioma/encoding**.
- **Múltiplos encodings para config e arquivos de padrões:** O **arquivo de config principal** é lido com **auto-detecção** (UTF-8, UTF-8 com BOM, ANSI Windows/cp1252, Latin-1), carregando mesmo quando salvo em encoding legado. Os **arquivos de padrões** (regex overrides, termos ML/DL) usam o encoding definido por **`pattern_files_encoding`** no seu config (padrão **`utf-8`**). Defina como `cp1252` ou `latin_1` apenas quando seus arquivos de padrões ou amostras estiverem salvos nesse encoding.
- **Múltiplas regiões:** Use a amostra de conformidade que corresponda à sua região ou regulamento (LGPD, UK GDPR, EU GDPR, Benelux, PIPEDA, POPIA, APPI, PCI-DSS, **152-FZ** ou amostras regionais opcionais). Cada amostra é um único arquivo YAML; você aponta o config para ela e mescla os recommendation overrides.

### Interface web, documentação e locales extras (roadmap curto a médio prazo)

Hoje, a documentação de produto **versionada** está em **inglês + pt-BR**; a interface web do **dashBOARd** segue em grande parte **inglês** nos templates. **Vários** locales que clientes pedem **ainda não** existem no produto — **superfícies completas** do painel e da documentação em idiomas e scripts adicionais (ex.: **es**, **fr**, **ja**, **ru**, **ar**, além de **mandarim / cantonês**, **indonésio**, **coreano**, **tailandês**, **vietnamita**, **hindi** e outros **scripts índicos**, **etíope / amárico**, **âmbitos africanos** mais amplos, **catalão**, **basco**, **galego** e outros) entram num **roadmap curto a médio prazo**, **orientado à demanda**, **junto com** **amostras de compliance** quando a jurisdição justificar. Aceitamos **sugestões públicas** (issues ou discussões) sobre **lacunas de locale ou encoding**; **consultoria comercial** pode acelerar **textos, amostras ou integrações sob medida** quando o padrão aberto não bastar. Um resumo **público** dessa direção (sem nomes de arquivos de planejamento interno) está no parágrafo **Roadmap — internacionalização e profundidade regional** do **[README.pt_BR.md](../README.pt_BR.md)** ([EN](../README.md)).

### Como habilitar e operar

1. **Escolha a amostra certa para sua região**

   Veja a tabela no [README de compliance-samples](compliance-samples/README.pt_BR.md) e a seção “Idioma e público-alvo”. Exemplos: Brasil → LGPD (PT-BR+EN); Canadá → PIPEDA (EN+FR); Reino Unido → UK GDPR; EEE → EU GDPR; Benelux → amostra Benelux; Japão → APPI; África do Sul → POPIA; **Rússia → 152-FZ** (termos EN+RU; **revisar com frequência**).

1. **Salve config e amostras em UTF-8 (recomendado)**

   Salvar tudo em **UTF-8** evita problemas de encoding com termos multilíngues. O config principal ainda será carregado se estiver em outro encoding (auto-detecção).

1. **Defina os caminhos e o encoding no config**

   No seu `config.yaml` (ou `config.json`) principal:

   ```yaml
   # Opcional: só se seus arquivos de padrões/amostras NÃO estiverem em UTF-8 (ex.: legado cp1252)
   pattern_files_encoding: utf-8

   regex_overrides_file: docs/compliance-samples/compliance-sample-pipeda.yaml
   ml_patterns_file: docs/compliance-samples/compliance-sample-pipeda.yaml
   ```

   Depois mescle os **`recommendation_overrides`** da amostra no seu config em `report.recommendation_overrides` (veja [USAGE.pt_BR](USAGE.pt_BR.md) seção de relatório).

1. **Execute a varredura**

   Use o CLI ou a API como de costume. Os achados usarão as norm tags e o texto de recomendação da amostra; o relatório Excel exibirá Unicode corretamente.

Para todas as opções de encoding e exemplos, veja [USAGE – File encoding](USAGE.md#file-encoding-config-and-pattern-files) (EN) e [USAGE.pt_BR – Encoding de arquivos](USAGE.pt_BR.md#file-encoding-config-and-pattern-files) (pt-BR).

---

**Ajuda com ajuste fino:** Se sua organização precisar de **maior ou melhor compatibilidade** com uma regulamentação ou escopo de conformidade específico (ex.: VCDPA, CPA, regras setoriais), podemos ajudar—**criando arquivos de configuração sob medida** ou fazendo **pequenos ajustes no código**—quando você entrar em contato. Isso permite que potenciais clientes adotem a ferramenta para sua jurisdição ou expectativas de auditoria sem começar do zero.

## Normas auditáveis e de gestão (papel de suporte)

A aplicação **não** certifica organizações. Ela oferece **descoberta e mapeamento** de dados pessoais e sensíveis e relatórios **apenas de metadados**, o que apoia a prestação de contas baseada em evidências e a preparação para auditorias.

### ISO 31000 (enquadramento)

A **ISO 31000** é uma **diretriz de gestão de risco da organização** (contexto, avaliação, tratamento, monitoramento)—não um catálogo de controles de produto, e **não** é resumida aqui. **Enquadramento:** o **processo de gestão de risco** da organização deve **orientar a priorização** de quais sistemas varrer, quais remediações tratar primeiro e quais perfis regulatórios habilitar. O Data Boar **apoia evidências** (descoberta, mapeamento, relatórios só de metadados) e **não substitui** sua análise de risco, aceitação de risco ou decisões de governança. **Cadeia de suprimentos de software** e inventário para **resposta a incidentes** (SBOM de dependências e de imagem) estão documentados à parte como prática de **segurança / release**—veja [SECURITY.pt_BR.md](../SECURITY.pt_BR.md), [RELEASE_INTEGRITY.pt_BR.md](RELEASE_INTEGRITY.pt_BR.md) e [ADR 0003](adr/ADR-0003-sbom-roadmap-cyclonedx-then-syft.md) (EN)—e **não** equivalem à ISO 31000.

- **ISO/IEC 27701 (Colleague-KS):** A ISO/IEC 27701 exige que controladores e operadores de PII saibam onde os PII estão e documentem o escopo do tratamento. Nossas varreduras e relatórios (achados, norm tags, saída Excel) ajudam a produzir essa evidência e a alinhar com as regulamentações que você declara sob a ISO/IEC 27701 (ex.: LGPD, GDPR, CCPA). **Escopo técnico:** [COMPLIANCE_TECHNICAL_REFERENCE.pt_BR.md](COMPLIANCE_TECHNICAL_REFERENCE.pt_BR.md).
- **SOC 2:** **Demanda recorrente** em corporações e fornecedores B2B; o SOC 2 (Tipo I/II) pressupõe controles documentados sobre segurança, disponibilidade e confidencialidade dos sistemas que processam dados sensíveis. Não realizamos auditorias SOC 2. Nossa **descoberta e mapeamento** de onde dados pessoais ou sensíveis estão, com relatórios apenas de metadados, apoiam o desenho de controles e a preparação para auditoria (ex.: evidência de inventário e escopo de dados). Norm tags e overrides de recomendação podem ser alinhados aos princípios e critérios de confiança que você utiliza.
- **FELCA (Lei 15.211/2025 – Estatuto Digital da Criança e do Adolescente):** Em vigor a partir de 17 de março de 2026, a FELCA se aplica a plataformas digitais dirigidas ou acessíveis por menores no Brasil. Não implementamos verificação de idade nem controles de plataforma. Nossa **detecção de dados de menores** (ex.: colunas de data de nascimento e idade, flags de “possível menor”) e os relatórios ajudam a mapear onde dados relativos a menores são processados e a apoiar transparência e prestação de contas (ex.: perante a ANPD). **Notas técnicas:** [MINOR_DETECTION.pt_BR.md](MINOR_DETECTION.pt_BR.md).

**Outras conformidades a acompanhar:** Leis regionais de proteção à criança ou a plataformas (além da FELCA), regras setoriais (ex.: saúde, financeiro) e novas exigências de localização ou transferência internacional de dados podem afetar seu escopo. Ampliamos o suporte via config e [compliance-samples](compliance-samples/) conforme as normas se tornem relevantes; não é necessário alterar código para adicionar novos norm tags ou textos de recomendação.

**Categorias sensíveis estendidas (adjacência clínica, indicadores de PI, artefatos de segurança em dados armazenados):** O mesmo motor pode ser afinado para léxicos adicionais e formas de regex—muitas vezes com **consultoria** para delimitar alvos e reduzir falsos positivos. Posicionamento para compradores e DPOs (sem ligação a PMO interno): [COMPLIANCE_AND_LEGAL.pt_BR.md](COMPLIANCE_AND_LEGAL.pt_BR.md) (seção **Categorias sensíveis estendidas (configuração e serviços)**).

**Privacidade de crianças e menores nos EUA (apenas técnico):** Amostras opcionais ([enquadramento FTC COPPA](compliance-samples/compliance-sample-us_ftc_coppa.yaml), [Califórnia AB 2273](compliance-samples/compliance-sample-us_ca_ab2273_caadca.yaml), [Colorado CPA — contexto de menores](compliance-samples/compliance-sample-us_co_cpa_minors.yaml)) acrescentam **norm tags e texto de relatório** para preparação de auditoria, revisão do DPO e escopo operacional. **Não** constituem aconselhamento jurídico, verificação de consentimento parental nem prova de conformidade. **Avisos e intenção das amostras:** [COMPLIANCE_TECHNICAL_REFERENCE.pt_BR.md](COMPLIANCE_TECHNICAL_REFERENCE.pt_BR.md) e comentários de cabeçalho em cada YAML em [compliance-samples/](compliance-samples/).

Outras normas auditáveis ou regionais podem ser atendidas via norm tags configuráveis e [compliance-samples](compliance-samples/); seguimos estendendo documentação e amostras conforme novos padrões se tornem relevantes.

## Referenciados explicitamente hoje (rótulos embutidos)

Os padrões regex embutidos e rótulos do relatório referem-se a estes frameworks (com valores de exemplo de `norm_tag`):

| Framework | Escopo                                      | Exemplo norm_tag (nos relatórios)   |
| --------- | ------------------------------------------- | ---------------------------------   |
| **LGPD**  | Brasil – Lei Geral de Proteção de Dados     | `LGPD Art. 5`                       |
| **GDPR**  | UE – General Data Protection Regulation     | `GDPR Art. 4(1)`                    |
| **CCPA**  | Califórnia – Consumer Privacy Act           | `CCPA`                              |
| **HIPAA** | EUA – Dados de saúde                        | Contexto saúde/seguros              |
| **GLBA**  | EUA – Serviços financeiros                  | `PCI/GLBA` (ex.: cartão de crédito) |

Os achados são armazenados com **`norm_tag`** e **`pattern_detected`** em formato livre; o relatório Excel os utiliza na aba **Recomendações** (Base legal, Risco, Recomendação, Prioridade, Relevante para).

## Extensibilidade

- **`norm_tag`** e **`pattern_detected`** são abertos: você pode defini-los para qualquer framework ou rótulo interno.
- **Overrides de regex:** Use [regex_overrides_file](SENSITIVITY_DETECTION.pt_BR.md) para adicionar padrões e definir `norm_tag` para ex. `"UK GDPR"`, `"PIPEDA s. 2"`, `"APPI"`, `"POPIA"` para que apareçam nos relatórios e recomendações.
- **Overrides de recomendação (config):** Use `report.recommendation_overrides` no config para personalizar "Base legal", "Relevante para" e demais textos de recomendação por padrão de `norm_tag` — assim UK GDPR, PIPEDA, APPI, POPIA ou normas customizadas recebem os rótulos e textos corretos sem mudar código. Veja [USAGE.pt_BR.md](USAGE.pt_BR.md) (seção de relatório) para um exemplo.
- **Conectores customizados:** Novas fontes de dados podem emitir achados com qualquer `norm_tag`; relatórios e recomendações usarão os overrides de config quando fornecidos, caso contrário os fallbacks embutidos.

Nenhuma alteração na lógica ou limiares do detector é necessária; a extensibilidade é via config e arquivos de override opcionais.

**Índice da documentação** (todos os tópicos, ambos os idiomas): [README.md](README.md) · [README.pt_BR.md](README.pt_BR.md). Para esquema de configuração e opções de relatório, veja [USAGE.pt_BR.md](USAGE.pt_BR.md) ([EN](USAGE.md)) e [TECH_GUIDE.pt_BR.md](TECH_GUIDE.pt_BR.md) ([EN](TECH_GUIDE.md)).
