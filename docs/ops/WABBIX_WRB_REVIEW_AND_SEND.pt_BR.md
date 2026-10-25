# WRB — revisão cruzada, texto pronto e WhatsApp

**Nome interno:** **WRB** (*Corporate-Entity-C Review Briefing*).

Este arquivo complementa o guia canônico [`Corporate-Entity-C_REVIEW_REQUEST_GUIDELINE.md`](Corporate-Entity-C_REVIEW_REQUEST_GUIDELINE.md): aqui está a **matriz de conformidade** (o que o guideline e o *long form* pedem vs o que o prompt PT-BR cobre), o **texto pronto para colar** no e-mail (espelho do bloco “Prompt mestre completo”) e uma **versão curta para WhatsApp**.

**Fonte de verdade do texto longo:** o bloco ` ```text ` em `Corporate-Entity-C_REVIEW_REQUEST_GUIDELINE.md` — se divergir, prevalece o guia; atualiza este espelho quando alterares o prompt mestre.

**Notas in-repo alinhadas ao último ciclo:** `docs/plans/Corporate-Entity-C_ANALISE_2026-03-18.md` e referências em `docs/plans/PLANS_TODO.md` (seção Corporate-Entity-C).

### Ao criar um pedido WRB no futuro

1. **Mostrar na tela** o texto completo (chat/IDE) para revisão antes de enviar à Corporate-Entity-C.
1. **Guardar no repositório** o mesmo conteúdo: atualizar o bloco “Prompt mestre completo” em [`Corporate-Entity-C_REVIEW_REQUEST_GUIDELINE.md`](Corporate-Entity-C_REVIEW_REQUEST_GUIDELINE.md) e, se usar este pacote, a seção §2 abaixo; fazer **`git commit`** para não perder o rascunho se a sessão ou o histórico sumirem.
1. **Validar** antes de commitar: **`uv run pytest tests/test_markdown_lint.py::test_markdown_lint_no_violations tests/test_docs_pt_br_locale.py -q`** — alinhado a **`.cursor/rules/docs-pt-br-locale.mdc`**, **`.cursor/rules/docs-policy.mdc`** e à barra de **`.cursor/rules/operator-chat-language-pt-br.mdc`** (pt-BR, não pt-PT; termos técnicos em inglês quando fizer sentido).

## (Espelha o workflow em inglês na seção “Workflow when drafting a new WRB request” do guideline.)

---

## 1. Revisão cruzada (guideline × long form × prompt PT-BR)

Legenda: **Sim** = coberto de forma clara; **Parcial** = coberto por implicação ou resumo; **Gap** = o *long form* ou o guideline são mais explícitos.

### 1.1 Bloco mínimo de contexto (“Persistent operator tip”)

| Pedido (guideline)                                  | Prompt PT-BR                                                           |
| ------------------                                  | ------------                                                           |
| Data / versão do último relatório                   | **Sim** (2026-03-18, 9,1/10)                                           |
| Caminho da nota de tracking                         | **Sim** (`Corporate-Entity-C_ANALISE_2026-03-18.md`)                               |
| Janela “desde o último relatório até agora”         | **Parcial** (implícito nas três camadas + retorno sobre recomendações) |
| Temas alterados (código vs docs vs planos)          | **Sim** (seção “Código, documentação e planos”)                        |
| Baseline de release vs estado atual (tag vs `main`) | **Sim** (terceira camada temporal)                                     |
| Baseline técnico no PDF (data + PR/commit)          | **Sim** (parágrafo + âncoras)                                          |

### 1.2 Três “since when” e o que pedir no output

| Pedido (guideline / tabela)                                                                | Prompt PT-BR                                                                                                                                        |
| ---------------------------                                                                | ------------                                                                                                                                        |
| Não confundir acumulado / último relatório Corporate-Entity-C / última release                         | **Sim**                                                                                                                                             |
| Inferir **qual release** o repo refletia “na altura” do último relatório deles             | **Parcial** — o guideline pede explicitamente; o PT foca delta temporal e recomendações, não essa inferência como linha dedicada                    |
| Última tag hoje vs `main` / trabalho não retagueado                                        | **Sim**                                                                                                                                             |
| Delta “última entrega mercado” vs só “desde o PDF”                                         | **Sim** (terceira camada)                                                                                                                           |
| Taxonomia de esforço no intervalo (security, integrity, features, docs, ops, refactor)     | **Parcial** — o resumo do formato menciona “taxonomia de tipo de trabalho”; o guideline lista categorias na seção “Ask for this explicit structure” |
| Estrutura explícita “o que foi enviado / melhorou vs regrediu / riscos novos” no intervalo | **Parcial** — espírito coberto; não é lista fechada como no guideline                                                                               |

### 1.3 Focos e checks (guideline + *long form* em inglês)

| Tema                                                                             | *Long form* (EN)                                                                   | Prompt PT-BR                                                                                                                 |
| ----                                                                             | ----------------                                                                   | ------------                                                                                                                 |
| Código / docs / planos em separado                                               | Listas **específicas** (runtime trust, tinted/draft, session seal, off-band, etc.) | **Parcial** — mesmas **famílias** e temas (confiança, auditoria, compliance, planos); não enumera cada bullet do *long form* |
| A–E (consistência, cadeia de custódia, severidade, MVP, wording)                 | Explícito                                                                          | **Parcial** — A/B/C/E cobertos em “Pontos de atenção” e drift; **MVP sequencing** não aparece com esse nome                  |
| F — modelo linguístico                                                           | Explícito                                                                          | **Sim** (seção dedicada)                                                                                                     |
| G — três lentes temporais                                                        | Explícito                                                                          | **Sim**                                                                                                                      |
| H — verificação de recomendações anteriores                                      | Explícito                                                                          | **Sim**                                                                                                                      |
| Agrupamento de achados: Critical/Important/Improvement × prazo × Code/Docs/Plans | Pedido no *long form*                                                              | **Parcial** — PT pede severidade, esforço, janela e tipo de esforço; **não** exige o agrupamento triaxial literal            |
| I — anexo opcional de roadmap                                                    | Explícito                                                                          | **Sim**                                                                                                                      |

### 1.4 Formato do PDF e linguística

| Pedido                                                              | Prompt PT-BR                                                                                                      |
| ------                                                              | ------------                                                                                                      |
| Um PDF (ou pacote mínimo)                                           | **Sim**                                                                                                           |
| Cap. 1 — executivo (≤2 páginas)                                     | **Sim**                                                                                                           |
| Cap. 2 — técnico profundo                                           | **Sim**                                                                                                           |
| Cap. 3 — DevSecOps / vulnerabilidades / deps / remediação           | **Sim**                                                                                                           |
| Tags preferidas (Critical/Important/Improvement × esforço × janela) | **Parcial** — espírito (severidade, esforço, janela); não repete as três dimensões do guideline palavra a palavra |
| Seção obrigatória “linguistic category model”                       | **Sim**                                                                                                           |
| Anexo opcional “roadmap tips”                                       | **Sim**                                                                                                           |

### 1.5 Síntese

- **Completude geral:** o prompt PT-BR está **alinhado** ao objetivo do guideline: contexto, três ângulos temporais, código/docs/planos, linguística, pontos de foco de confiança/evidência, verificação de recomendações anteriores, **três capítulos** + anexo opcional, baseline **data + PR/commit** na abertura.
- **Onde o *long form* EN é mais “checklist”:** listas fechadas de **artefatos** (itens de código/plano) e **agrupamento triaxial** de achados; o PT-BR privilegia **prosa + âncoras** — por desenho, não por omissão grave.
- **Se quiser paridade máxima com o EN** (opcional): acrescentar uma frase pedindo agrupamento por severidade × prazo × artefato, e/ou uma linha pedindo inferência da **release provável na data do último relatório**; ou remeter explicitamente ao *long form* no repositório.

---

## 2. Texto pronto para envio (e-mail)

Copiar o bloco abaixo. **Ajustar antes de enviar:** data/caminhos se mudarem; preencher **PR/commit** se já souber o marco técnico.

```text
Olá, equipe Corporate-Entity-C,

Esperamos que se encontrem bem. Viemos por este meio solicitar, com o máximo de apreço pelo trabalho que vocês já nos dedicaram, um novo relatório de revisão e recomendações sobre o projeto Data Boar (repositório no GitHub e imagens publicadas no Docker Hub, quando aplicável).

O texto abaixo funciona como um briefing único: pode orientar a própria análise de vocês ou servir de base para quem estruture o relatório (incluindo assistentes de IA), sempre com o rigor e a educação que o assunto merece. Nada aqui pretende ser uma ordem; são pedidos e sugestões de foco, que vocês podem adaptar conforme a metodologia de vocês.

Resumo (âncora rápida):

- Novo relatório de revisão e recomendações sobre o Data Boar.
- Briefing único; sugestões adaptáveis à metodologia de vocês (não instruções rígidas).

---

Contexto e fonte de verdade

Sabemos que conversas e e-mails não preservam todo o contexto. Por isso, seria muito valioso para nós que a análise se apoie, sempre que possível, nos artefatos do repositório — código, documentação, planos, notas de release, tags no GitHub, configuração de imagem e CI — e não apenas na memória do último contato. Como referência não exaustiva, mencionamos README, docs/releases, docs/plans/PLANS_TODO.md, tags e releases no GitHub, Dockerfile e documentação de deploy, pyproject.toml, SECURITY.md e os fluxos de trabalho de integração contínua. Se algo no repositório estiver mais atualizado do que este e-mail, pedimos que prevaleça o que estiver no repo.

Resumo (âncora rápida):

- Priorizar evidência no repositório (código, docs, releases, CI) em relação a este e-mail.
- Lista de caminhos acima é exemplificativa, não fechada.

---

Referência ao último relatório de vocês

Para não perder o fio da meada, lembramos o relatório anterior de vocês com data de referência em 18 de março de 2026, com nota global de 9,1 em dez na nossa anotação interna. O acompanhamento no repositório está em docs/plans/Corporate-Entity-C_ANALISE_2026-03-18.md. O PDF correspondente, quando existir no ambiente do operador, costuma estar na pasta de feedbacks e revisões com nome semelhante a analise_evolucao_data_boar_2026-03-18.pdf.

Seria extremamente útil que, neste novo ciclo, vocês retomassem as recomendações daquele relatório e nos ajudassem a perceber o que já foi plenamente atendido, o que ficou em parte, ou o que ainda permanece em aberto — tema que desenvolvemos mais adiante neste pedido.

Se possível, pedimos também que indiquem logo na abertura do novo relatório qual foi o marco técnico de comparação que vocês adotaram (por exemplo PR principal e/ou commit-base), junto da data do último relatório, para facilitar a consciência de contexto e rastreabilidade da análise.

Resumo (âncora rápida):

- Último relatório Corporate-Entity-C: 2026-03-18; tracking em Corporate-Entity-C_ANALISE_2026-03-18.md.
- Pedido: retomar recomendações daquele ciclo e distinguir atendido / parcial / aberto.
- Na abertura do novo PDF: explicitar data de referência + PR/commit-base usado na comparação.

---

Três ângulos temporais que pedimos para não confundir

Três perguntas diferentes pedem três camadas de narrativa distintas no relatório de vocês. Pedimos gentilmente que não as misturem, porque cada uma responde a um público e a uma decisão de produto diferente.

Primeiro, a visão histórica acumulada: como vocês enxergam a maturidade do produto, a tendência de risco e a narrativa de longo prazo, como já costumam fazer.

Segundo, o que mudou desde o último relatório de vocês: o que já tratamos, o que planejamos explicitamente, o que deixamos pendente; e, sobretudo, se as recomendações anteriores foram corrigidas de forma eficaz ou apenas formalmente.

Terceiro, o que mudou desde a última release pública que identificarem no GitHub (tag de versão) e na imagem Docker correspondente, até o estado atual do branch principal. Se ainda houver commits no branch principal após a última tag, esse trabalho ainda não foi “entregue” como nova versão nomeada a testadores, parceiros ou mercado; pedimos que isso fique explícito, para que ninguém confunda o que o mercado instala com o que o repositório já contém hoje.

Resumo (âncora rápida):

- Camada 1 — acumulado histórico (maturidade e tendência).
- Camada 2 — desde o último relatório Corporate-Entity-C (tratamento das recomendações deles).
- Camada 3 — desde última tag GitHub/Docker até o tip do branch (inclui trabalho ainda não “retagueado”).

---

Código, documentação e planos

Pedimos que considerem, onde fizer sentido para vocês, uma leitura articulada em três famílias de artefatos. No código, interessa-nos qualidade, clareza, cobertura de testes, possíveis regressões, riscos de segurança e consistência de comportamento entre CLI, API e relatórios. No nosso roadmap recente, temos atenção a temas de confiança de runtime, Rastro de Auditoria (Audit Trail) exportável e integração com licenciamento e integridade, quando aplicável.

Na documentação, agradecemos qualquer observação sobre operação (USAGE, deploy, SECURITY), material de compliance e jurídico, e pitch ou material privado se for referenciado. Onde existir par inglês e português, a sincronização e a clareza para o operador são importantes; e, no texto jurídico ou de compliance, evitar overclaim em relação ao que o produto já garante de fato.

Nos planos, em docs/plans e em PLANS_TODO.md, interessa-nos a coerência entre roadmap, dependências entre iniciativas e distinção clara entre o que já está entregue e o que ainda é intenção futura, para que o leitor não confunda planejamento com produto disponível.

Resumo (âncora rápida):

- Código: qualidade, testes, segurança, consistência CLI/API/relatório; temas de confiança e auditoria quando relevante.
- Documentação: operação, compliance, i18n; sem overclaim.
- Planos: roadmap vs entregue; dependências entre iniciativas.

---

Modelo linguístico e níveis de abstração

Ficaríamos gratos se, no capítulo técnico, pudessem dedicar um espaço ao que chamamos de modelo linguistic category: ou seja, se o nível de abstração está adequado a cada tipo de documento e audiência. Em linhas gerais, os planos tendem a ser mais estruturais; a documentação operacional, mais concreta; o material de compliance e pitch, uma abstração controlada em valor e risco, sem prometer o que ainda não está implementado. Sempre que possível, apontar trechos abstratos demais para serem verificáveis, trechos concretos demais no lugar errado, ou ambiguidade entre estado atual e roadmap seria uma contribuição enorme.

Resumo (âncora rápida):

- Avaliar abstração por tipo de documento e audiência.
- Sinalizar trechos demasiado abstratos, demasiado concretos no lugar errado, ou ambíguos (atual vs roadmap).

---

Pontos de atenção que nos preocupam além do habitual

Além da maturidade geral, segurança e vulnerabilidades que vocês já costumam cobrir, pedimos atenção especial, se o tempo de vocês permitir, a: cadeia de confiança e evidência do runtime ao SQLite, exportação e relatório; clareza de severidade para operador e cliente; linguagem adequada entre tamper-evident e tamper-proof; encaixe futuro de observabilidade e alertas off-band; e drift entre código, documentação e planos, incluindo regressões que não apareçam como falhas de teste.

Resumo (âncora rápida):

- Além do “checklist” habitual: evidência ponta a ponta, severidade, wording jurídico defensável.
- Observabilidade/alertas (futuro) e drift código/docs/planos.

---

Retorno sobre as recomendações do relatório anterior

Para cada recomendação relevante do relatório de 18 de março de 2026 que vocês retomarem, seria muito útil receber um estado resumido (por exemplo não iniciado, parcial, concluído ou validado), uma nota de progresso em que façam sentido, e um comentário honesto se a correção parece efetiva ou apenas formal — incluindo o caso em que a sensação de “feito” não corresponde ao efeito real.

Resumo (âncora rápida):

- Por recomendação retomada: estado, nota de progresso, comentário “efetivo vs formal”.
- Chamar atenção para falso “feito” quando o problema persistir.

---

Formato do entregável que imaginamos

Se for viável para o fluxo de vocês, imaginamos um único PDF, ou um pacote mínimo equivalente, com três capítulos principais e um anexo opcional.

O primeiro capítulo seria uma visão gerencial ou executiva, idealmente nas primeiras duas páginas, dirigida a direção de TI, jurídico ou compliance e parceiros de negócio, com progresso, riscos-chave, impacto e prioridades de decisão, sem mergulho técnico profundo.

O segundo capítulo seria a visão técnica detalhada, integrando os três ângulos temporais que descrevemos, o tratamento de código, documentação e planos, o modelo linguístico, os pontos de atenção, a verificação das recomendações anteriores, tendências, regressões e qualidade de código e testes onde aplicável.

O terceiro capítulo seria dedicado a DevSecOps e hardening: vulnerabilidades, dependências, orientações de atualização de pacotes e uma sequência de remediação que possamos alinhar a sprints ou backlog de segurança.

Sempre que possível, agradeceríamos que as recomendações viessem acompanhadas de uma indicação de severidade, esforço aproximado e janela de tempo sugerida, e, quando fizer sentido, uma classificação do tipo de esforço (por exemplo segurança, integridade e evidência, funcionalidades, documentação e governança, operações e observabilidade, ou refatoração e dívida técnica).

Resumo (âncora rápida):

- Cap. 1 — executivo (≤2 páginas): TI, jurídico, parceiros.
- Cap. 2 — técnico: integra tudo o que pedimos acima.
- Cap. 3 — DevSecOps: vulnerabilidades, deps, priorização para sprint/backlog.
- Opcional: severidade, esforço, janela, taxonomia de tipo de trabalho.
- No início do PDF: registrar baseline de contexto (data do último relatório + PR/commit-base).

---

Anexo opcional de ideias de roadmap

Se a metodologia e o tempo de vocês permitirem, um anexo separado com ideias especulativas de lacunas de capacidade e caminhos para um produto production-ready e competitivo nos mercados que visamos seria bem-vindo. Pedimos que esse anexo fique claramente identificado como opcional e especulativo, separado dos achados que vocês fundamentam diretamente no código e na documentação atual.

Resumo (âncora rápida):

- Anexo separado, claramente opcional e especulativo.
- Ideias de lacunas e production-ready; não misturar com achados evidenciados no repo.

---

Encerramento

Agradecemos de antemão a paciência e o rigor de sempre. Qualquer ajuste deste briefing ao que for mais natural para o processo de vocês é bem-vindo. Permanecemos à disposição para esclarecimentos.

Com estima,
Fabio Leitao
Equipe Data Boar
```

---

## 3. Versão resumida (WhatsApp)

Use quando o canal for curto; o pedido completo continua no repositório (`Corporate-Entity-C_REVIEW_REQUEST_GUIDELINE.md`, seção “Prompt mestre completo”). Você pode anexar o PDF local ou colar o texto longo numa mensagem de seguimento.

```text
Olá! Pedido WRB — Data Boar: novo relatório de revisão, por favor.

Contexto rápido: último relatório de vocês 2026-03-18 (9,1/10 nas nossas notas); tracking em docs/plans/Corporate-Entity-C_ANALISE_2026-03-18.md. No início do PDF: por favor indiquem data de referência + PR/commit-base que usaram na comparação.

Pedimos 3 camadas de tempo separadas (não misturar): (1) visão acumulada; (2) desde esse relatório + retorno sobre recomendações anteriores; (3) desde última tag GitHub/Docker até o estado atual do branch (main pode estar à frente do tag).

Entregável: 1 PDF com cap.1 executivo (≤2p), cap.2 técnico profundo, cap.3 DevSecOps/hardening; mais anexo opcional de ideias de roadmap (bem separado, especulativo).

O briefing completo em prosa está em docs/ops/Corporate-Entity-C_REVIEW_REQUEST_GUIDELINE.md — podem seguir esse arquivo como fonte.

Obrigado!
— Fabio Leitao, Equipe Data Boar
```
