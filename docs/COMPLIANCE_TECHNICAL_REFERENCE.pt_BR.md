# Referência técnica relacionada à conformidade (TI, segurança, integração)

**English:** [COMPLIANCE_TECHNICAL_REFERENCE.md](COMPLIANCE_TECHNICAL_REFERENCE.md)

**Público:** Equipes que **integram ou operam** o Data Boar em segurança, infraestrutura ou engenharia de conformidade. Para um resumo **não técnico** voltado a **jurídico, liderança de compliance e DPOs**, veja [COMPLIANCE_AND_LEGAL.pt_BR.md](COMPLIANCE_AND_LEGAL.pt_BR.md).

Aqui ficam detalhes que não pertencem ao resumo jurídico: validação, codificações, limites de API, timeouts e onde automatizar varreduras.

**Vocabulário de POC (uso em material técnico / deck):** **Data Sniffing** nomeia o passo de descoberta e amostragem; **Deep Boring** nomeia a profundidade do Excel / relatório estruturado — veja [GLOSSARY.pt_BR.md](GLOSSARY.pt_BR.md#1-identidade-do-produto-e-pano-de-dados) e [COMPLIANCE_FRAMEWORKS.pt_BR.md](COMPLIANCE_FRAMEWORKS.pt_BR.md#vocabulário-do-motor-poc-decks-e-docs-técnicos). O [README.md](../README.md) na parte para gestores permanece em linguagem mais direta e **não** exige esses rótulos.

---

## Controles de segurança que sustentam programas de conformidade

- **Validação de entradas** (ex.: campos tenant/technician quando aplicável).
- **Limite de tamanho do corpo** das requisições na API para reduzir risco de abuso.
- **Política de logs:** não registrar API keys, senhas nem connection strings.

Política completa e endurecimento: [SECURITY.pt_BR.md](SECURITY.pt_BR.md) ([EN](SECURITY.md)).

---

## Codificações de caractere e configs multilíngues

Arquivos de configuração e de padrões suportam **UTF-8** (recomendado), **UTF-8 com BOM** e **encodings legados** (ex.: ANSI Windows, Latin-1); o config principal usa **detecção automática** quando aplicável. Termos e idioma do relatório podem acompanhar a região (ex.: EN+FR no Canadá, PT-BR+EN no Brasil, **EN+RU na amostra 152-FZ**).

**Unicode nos dados varridos:** achados e Excel tratam texto como **Unicode** — **latim**, **cirílico**, **CJK** (ex.: japonês), **árabe** e corpus mistos entram no âmbito de caracteres. A **decodificação em bytes** das fontes depende de conectores e formatos; **sniffing e heurísticas** podem ser **afinados** por implantação. **Interface web do operador** e **documentação completa** em muitos idiomas adicionais **ainda não** estão todas entregues; a direção está no **roadmap** (curto a médio prazo), com **en** + **pt-BR** primeiro — veja [COMPLIANCE_FRAMEWORKS.pt_BR.md](COMPLIANCE_FRAMEWORKS.pt_BR.md#operação-multilíngue-multi-encoding-e-multirregional) e o parágrafo **Roadmap — internacionalização e profundidade regional** no **[README.pt_BR.md](../README.pt_BR.md)**. **Amostras YAML de compliance** precisam de **revisão periódica** conforme normas e redações mudam — [compliance-samples/README.pt_BR.md](compliance-samples/README.pt_BR.md#manutenção-das-amostras).

**Política (anti-overclaim):** “Qualquer encoding” significa config **ajustável pelo operador** e detecção ciente de Unicode onde implementada — não uma garantia de que todo conector decodifica da mesma forma toda representação em disco ou no fio, nem de que o motor faz **reparo universal de mojibake** ou normalização NFC/homóglifos em todos os caminhos. Trate ambiguidade residual de decode como **limitação de cobertura** (documente ou exponha via `scan_failures` / comportamento do conector), não como “limpo”.

Passo a passo: [USAGE.pt_BR.md — Encoding de arquivos, config e padrões](USAGE.pt_BR.md#file-encoding-config-and-pattern-files) ([EN](USAGE.md)).

---

## Desempenho e resiliência

**Timeouts configuráveis** (globais e por **alvo**) para que uma fonte lenta não trave a execução inteira. Chaves e comportamento: [USAGE.pt_BR.md](USAGE.pt_BR.md) e [TECH_GUIDE.pt_BR.md](TECH_GUIDE.pt_BR.md).

---

## Varreduras recorrentes / automatizadas

Execuções **agendáveis** via **API interna** permitem monitoramento contínuo ou periódico; **relatórios Excel** e **heatmaps** por sessão fazem parte do **rastro de auditoria**. API e dashboard: [USAGE.pt_BR.md](USAGE.pt_BR.md), [TECH_GUIDE.pt_BR.md](TECH_GUIDE.pt_BR.md).

---

## Notificações opcionais (webhooks)

Fora de banda, ao **fim da varredura**, a aplicação pode enviar um **resumo curto** (Slack, Teams, webhook genérico / ponte Signal ou campos Telegram legados), com suporte a **vários canais** e **cópia ao tenant** quando configurado — **desligado por padrão**; trate URLs e tokens como **segredos**. Política de canais: [OPERATOR_NOTIFICATION_CHANNELS.pt_BR.md](ops/OPERATOR_NOTIFICATION_CHANNELS.pt_BR.md). Não substitui relatórios nem política de rede/TLS. Ver [USAGE.pt_BR.md — Notificações ao operador](USAGE.pt_BR.md#notificações-ao-operador-opcional) e [SECURITY.pt_BR.md](SECURITY.pt_BR.md).

---

## Documentos relacionados

| Tema                                                | Documento                                                                      |
| ----                                                | ---------                                                                      |
| Resumo jurídico / compliance (tomadores de decisão) | [COMPLIANCE_AND_LEGAL.pt_BR.md](COMPLIANCE_AND_LEGAL.pt_BR.md)                 |
| Metodologia (descoberta, risco, estilo ROPA)        | [COMPLIANCE_METHODOLOGY.pt_BR.md](COMPLIANCE_METHODOLOGY.pt_BR.md)             |
| Frameworks, amostras, perfis YAML                   | [COMPLIANCE_FRAMEWORKS.pt_BR.md](COMPLIANCE_FRAMEWORKS.pt_BR.md)               |
| Esquema completo de config, credenciais, CLI        | [USAGE.pt_BR.md](USAGE.pt_BR.md)                                               |
| Conectores, arquitetura, deploy                     | [TECH_GUIDE.pt_BR.md](TECH_GUIDE.pt_BR.md)                                     |
| Padrões de detecção, ML/DL                          | [SENSITIVITY_DETECTION.pt_BR.md](SENSITIVITY_DETECTION.pt_BR.md)               |

Índice completo: [README.pt_BR.md](README.pt_BR.md) · [README.md](README.md).
