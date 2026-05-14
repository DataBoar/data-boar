# Amostras de conformidade

**English:** [README.md](README.md)

Arquivos de configuração de exemplo para habilitar **frameworks de conformidade adicionais** com o mesmo fluxo de varredura e relatório. Copie os blocos relevantes para seu config principal ou defina `regex_overrides_file` / `ml_patterns_file` e mescle os `report.recommendation_overrides` do sample. O conjunto inclui **Rússia (Lei federal 152-FZ)** junto com LGPD, família GDPR, PIPEDA, APPI e outras — veja a tabela abaixo e [COMPLIANCE_FRAMEWORKS.pt_BR.md](../COMPLIANCE_FRAMEWORKS.pt_BR.md#lista-de-amostras-e-links) ([EN](../COMPLIANCE_FRAMEWORKS.md#list-of-samples-and-links)). Para como usar e como cada framework mapeia para o config, veja [COMPLIANCE_FRAMEWORKS.pt_BR.md](../COMPLIANCE_FRAMEWORKS.pt_BR.md) ([EN](../COMPLIANCE_FRAMEWORKS.md)).

Para governança operacional (escopo, minimização, retenção e rastreabilidade), use [OPERATOR_GOVERNANCE_CHECKLIST.pt_BR.md](OPERATOR_GOVERNANCE_CHECKLIST.pt_BR.md) ([EN](OPERATOR_GOVERNANCE_CHECKLIST.md)).

## Arquivos de amostra (um por regulamento)

| Arquivo                                        | Finalidade                                                                                                                                                                                          |
| ---------                                      | ------------                                                                                                                                                                                        |
| **compliance-sample-lgpd.yaml**                | LGPD (Brasil): termos bilíngues PT-BR + EN (ex.: documento oficial / official document, RG, CNH / Driver License); regex RG/CEP; regex de **geolocalização precisa** (mesma geometria das amostras VCDPA / RGPD UE); para implantações brasileiras.                                     |
| **compliance-sample-br_insurance_lgpd_anchor.yaml** | Setor segurador (Brasil): amostra **esqueleto** (cabeçalho EN) com termos genéricos e **`norm_tag`** de inventário ancorada na LGPD; **não** certifica SUSEP/CNSP — ver [COMPLIANCE_FRAMEWORKS.pt_BR.md](../COMPLIANCE_FRAMEWORKS.pt_BR.md#setor-segurador-brasil-lgpd-referencias-prudenciais). |
| **compliance-sample-uk_gdpr.yaml**             | UK GDPR (Reino Unido pós-Brexit + semelhante à UE): norm_tag e recommendation overrides alinhados à ICO e disposições britânicas; regex de **geolocalização precisa** (mesma geometria das amostras VCDPA / RGPD UE).                                                                   |
| **compliance-sample-eu_gdpr.yaml**             | EU GDPR (EEE): Art. 4(1) Reg. UE 2016/679, EDPB, autoridades nacionais; termos opcionais EN + DE/FR.                                                                                                |
| **compliance-sample-benelux.yaml**             | Benelux (BE, NL, LU): base EU GDPR + IDs nacionais (BSN, NISS, ID Luxemburgo) e overrides para DPAs nacionais; termos EN + NL/FR.                                                                   |
| **compliance-sample-pipeda.yaml**              | PIPEDA (Canadá, setor privado federal): informação pessoal, consentimento e identificadores canadenses (ex.: SIN); regex de **geolocalização precisa** (mesma geometria das amostras VCDPA / RGPD UE); EN + FR.                                                                                  |
| **compliance-sample-popia.yaml**               | POPIA (África do Sul): responsável pelo tratamento, informação pessoal e identificadores sul-africanos.                                                                                             |
| **compliance-sample-appi.yaml**                | APPI (Japão): informação pessoal e informação pessoal sensível (要配慮個人情報); My Number; regex de **geolocalização precisa** (位置情報; mesma geometria que VCDPA / EU GDPR); termos EN + japonês; alinhamento PPC.                                                                                                      |
| **compliance-sample-singapore_pdpa.yaml**      | Singapura PDPA 2012 (alterada 2020/2021): PDPC; regex NRIC/FIN/UEN; regex de **geolocalização precisa** (mesma geometria VCDPA / EU GDPR); DNC, notificação obrigatória de violação; EN.                                                                                                      |
| **compliance-sample-india_dpdp.yaml**          | Índia DPDP Act 2023: DPBI, data fiduciary; regex Aadhaar/PAN; **geolocalização precisa** (mesma geometria VCDPA / EU GDPR); termos ML SDF, transferência internacional, dados de crianças; EN; regras em evolução — revalidar.                                                                                    |
| **compliance-sample-pci_dss.yaml**             | PCI-DSS (dados de cartão de pagamento): padrões de cartão/financeiro e recommendation overrides para comerciantes e avaliadores.                                                                    |
| **compliance-sample-us_ftc_coppa.yaml**        | EUA FTC COPPA (privacidade online de crianças): termos e overrides de **mapeamento técnico**; sem verificação de idade nem aconselhamento jurídico.                                                 |
| **compliance-sample-us_ca_ab2273_caadca.yaml** | Califórnia AB 2273 (Age-Appropriate Design): **rotulagem** para escopo voluntário; aplicabilidade exige assessoria jurídica; regex de **geolocalização precisa** (mesma geometria das amostras VCDPA / RGPD UE) para sinais de inventário em contexto de menores.                                                                        |
| **compliance-sample-us_co_cpa_minors.yaml**    | Colorado CPA — contextos com menores de 18 anos: **norm tags técnicos**; não estabelece “menor conhecido” no sentido jurídico.                                                                      |
| **compliance-sample-us_va_vcdpa.yaml**         | Virgínia VCDPA: termos de categorias sensíveis; regexes de **geolocalização precisa** (4+ decimais + palavra-chave/JSON); escopo B2B/emprego **não** classificado automaticamente — ver cabeçalho do arquivo. |
| **compliance-sample-us_ca_cpra.yaml**          | Califórnia CPRA / CCPA (alterada): exporta `CCPA_SSN` do core + identificadores SPI da CPRA (CNH-CA, ITIN); regex de **geolocalização precisa** (§ 1798.140(ae)(1)(H)); termos ML de privacidade do consumidor.                                                              |
| **compliance-sample-us_fcpa_internal_policy_pack.yaml** | EUA **FCPA** + **política anticorrupção** interna (empregador) — **inventário**; não detecção de suborno nem aconselhamento jurídico.                                                               |
| **compliance-sample-australia_privacy.yaml**   | Austrália Privacy Act 1988 (Cth; Emenda 2024); OAIC, APPs; regex TFN/Medicare/ABN/Passaporte; **geolocalização precisa** (mesma geometria VCDPA / EU GDPR); esquema NDB; informação sensível (s.6); EN.                                                                                               |
| **compliance-sample-russia_152_fz.yaml**       | Rússia Lei federal 152-FZ (emendas 266-FZ 2022); Roskomnadzor; **geolocalização precisa**; regex SNILS / INN heurístico (risco de FP — ver cabeçalho); categorias especiais (Art. 10); notificação de violação (72 h); localização (Art. 22.1); termos EN + RU; **revisar com frequência**. |

**Lista completa** de amostras por região, nomes de arquivo e como mesclar no `config.yaml`: [COMPLIANCE_FRAMEWORKS.pt_BR.md](../COMPLIANCE_FRAMEWORKS.pt_BR.md#amostras-de-conformidade) ([EN](../COMPLIANCE_FRAMEWORKS.md#compliance-samples)). Cada amostra é autocontida (regex overrides, termos ML, recommendation overrides); novas regiões seguem o mesmo formato.

### Manutenção das amostras

**Todas** as amostras de conformidade são **pontos de partida técnicos**, não substituto de revisão jurídica. Mesmo quando o texto da lei é estável, **orientações de autoridade**, **jurisprudência e linhas de fiscalização**, **normas setoriais** (ex.: revisões do PCI-DSS), **formatos de identificadores** nos dados reais e **reformulações ou consolidações do texto legal oficial** mudam — então regex, termos de ML e `recommendation_overrides` merecem **revisão periódica** para qualquer framework em que você dependa do arquivo (ex.: **antes de um release minor** ou em cadência **trimestral** para perfis de alto risco).

Entre os regulamentos que já amostramos, costumam ser **especialmente dinâmicos**: leis de privacidade **estaduais nos EUA** e projetos ligados a **menores** (ex.: Califórnia, Colorado); **UE / Reino Unido** (legislação e guias em evolução, inclusive EDPB e ICO); **DPDP na Índia** (lei nova, regras e prática da autoridade ainda em consolidação); **PDPLs no Oriente Médio** (EAU, Arábia Saudita); e **152-FZ na Rússia** (alterações frequentes na lei e em atos secundários — veja o cabeçalho de `compliance-sample-russia_152_fz.yaml` como exemplo de documentar esse risco no próprio arquivo). **Revalide com assessoria jurídica** quando o fato ou a linha de base legal mudar.

### Idioma e público-alvo

Ao escolher ou criar uma amostra, considere o(s) **idioma(s)** da região alvo para que nomes de colunas e rótulos nos dados sejam detectados:

| Regulamento / região             | Idioma(s) recomendado(s) para termos e rótulos                                                             |
| --------------------             | ------------------------------------------------                                                           |
| **LGPD (Brasil)**                | Português (BR) e inglês (ex.: "documento oficial" e "official document", "CNH" e "Driver License").        |
| **Brasil (seguros — esqueleto LGPD)** | Português (BR) e inglês para nomes de colunas de apólice/sinistro/corretagem; mescle com a amostra LGPD completa para identificadores nacionais. |
| **PIPEDA (Canadá)**              | Inglês e francês (ex.: "personal information" e "renseignements personnels") ao varrer dados canadenses.   |
| **UK GDPR**                      | Inglês.                                                                                                    |
| **EU GDPR (EEE)**                | Inglês; opcional alemão/francês para dados multilingues na UE.                                             |
| **Benelux (BE, NL, LU)**         | Inglês mais holandês e/ou francês (ex.: BSN, NISS, nomes de coluna de ID nacional).                        |
| **POPIA (África do Sul)**        | Inglês; adicione idiomas locais nos termos se seus dados usarem.                                           |
| **APPI (Japão)**                 | Japonês e/ou inglês conforme os nomes de colunas.                                                          |
| **PCI-DSS**                      | Inglês.                                                                                                    |
| **Filipinas (DPA)**              | Inglês.                                                                                                    |
| **Austrália / NZ**               | Inglês.                                                                                                    |
| **Singapura (PDPA)**             | Inglês.                                                                                                    |
| **UAE / Arábia Saudita (PDPL)**  | Inglês; opcional árabe para nomes de colunas.                                                              |
| **Argentina / Colômbia / Chile** | Espanhol e inglês (ex.: datos personales / personal data).                                                 |
| **Quênia / Nigéria**             | Inglês.                                                                                                    |
| **Marrocos**                     | Francês e/ou árabe conforme relevante.                                                                     |
| **Índia (DPDP)**                 | Inglês.                                                                                                    |
| **Turquia (KVKK)**               | Turco e inglês (ex.: kişisel veri / personal data).                                                        |
| **Rússia (152-FZ)**              | Russo e inglês (ex.: персональные данные / personal data); rever termos quando houver alteração normativa. |
| **Suíça (FADP)**                 | Inglês; opcional DE/FR/IT.                                                                                 |
| **EUA (COPPA, AB 2273, CO CPA, VCDPA, CPRA/CCPA)** | Inglês (implantações e programas de privacidade nos EUA).                                                  |

Documente no cabeçalho da amostra ou em [COMPLIANCE_FRAMEWORKS](../COMPLIANCE_FRAMEWORKS.pt_BR.md) quando uma amostra incluir termos em mais de um idioma. Veja também a regra **.cursor/rules/compliance-samples-language.mdc**.

**Para autores:** Use YAML em **aspas duplas** nos valores de `pattern` em regex com **barras invertidas escapadas** (ex.: `pattern: "\\b[A-Z]{2}\\s?\\d{6}\\s?[A-D]\\b"`). Isso evita erros de linter "Invalid escape sequence" e carrega corretamente; o valor passado ao motor de regex é `\b`, `\s`, `\d` como desejado. Não use aspas simples nem `\d`/`\s` sem escape em aspas duplas. Os testes em `tests/test_compliance_samples.py` validam a estrutura e que o detector carrega cada amostra.

**Encoding:** Salve amostras em **UTF-8** para termos multilíngues (japonês, árabe, francês, **cirílico russo**, etc.). O config principal usa auto-detecção (UTF-8, UTF-8-sig, cp1252, latin_1); arquivos de padrões usam **`pattern_files_encoding`** (padrão `utf-8`). Dados varridos seguem **Unicode** no pipeline (latim, cirílico, CJK, árabe…); **sniffing** pode ser afinado por implantação — [COMPLIANCE_FRAMEWORKS.pt_BR.md](../COMPLIANCE_FRAMEWORKS.pt_BR.md#operação-multilíngue-multi-encoding-e-multirregional). **Interface do dashBOARd e traduções completas de docs** em muitos locales estão no **roadmap**, ainda não todas entregues — visão geral no parágrafo **Roadmap — internacionalização** do **[README.pt_BR.md](../../README.pt_BR.md)**. Detalhes de chaves: [USAGE.pt_BR.md](../USAGE.pt_BR.md#file-encoding-config-and-pattern-files) · [USAGE.md](../USAGE.md#file-encoding-config-and-pattern-files) (EN).
