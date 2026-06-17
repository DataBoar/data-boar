# Primário sobre a evolução da IA (sem hype)

**English:** [AI_EVOLUTION_PRIMER.md](AI_EVOLUTION_PRIMER.md)

Esta nota é para **integradores**, **leitores de conformidade** e **mantenedores** que ouvem “IA” usada de forma intercambiável para **regex**, **florestas aleatórias**, **chatbots** e **modelos com bilhões de parâmetros**. **Não** é uma história completa do campo; décadas e rótulos ficam **aproximados** de propósito. Para profundidade de manual, use uma referência geral de IA/ML (ex.: Russell & Norvig, *Artificial Intelligence: A Modern Approach*) — aqui só **ancoramos vocabulário** para a postura **determinística + supervisionada** do Data Boar fazer sentido.

**Documentação de produto relacionada:** [TECH_GUIDE.pt_BR.md](TECH_GUIDE.pt_BR.md#detection-stack-vs-generative-llms) · [SENSITIVITY_DETECTION.pt_BR.md](SENSITIVITY_DETECTION.pt_BR.md) · [GLOSSARY.pt_BR.md](GLOSSARY.pt_BR.md) (§8 e **§8b**).

---

## 1. Por que isto existe (e o que **não** é)

- **Por quê:** Fornecedores misturam **recuperação**, **classificação**, **regras** e **texto generativo** na mesma marca, “IA”. O Data Boar precisa de uma **linha do tempo compartilhada** para que “usamos ML” **não** signifique “enviamos um LLM dentro do scanner”.
- **O que não é:** Promessa de que qualquer técnica é “segura”; cada camada tem **falsos positivos/negativos** ou **vias de uso incorreto**. **Não** é assessoria jurídica.

---

## 2. Cronologia em resumo (nível alto)

| Época (aprox.) | Ideia dominante | O que funcionou | O que quebrou a confiança |
| -------------- | ---------------- | ---------------- | ------------------------- |
| **1950–1960** | Raciocínio **simbólico**, **cibernética** inicial, primeiros modelos **neurais** (ex.: perceptron) | Provas de conceito, jogos, otimismo | Problemas difíceis continuaram difíceis; **pouco compute** |
| **Fim dos 1960–1970** | Continuidade do simbólico; **primeira contração** de financiamento (sou “**inverno da IA**” em muitas narrativas) | Demos especializados | **Custo vs resultado**; limites conhecidos de classificadores lineares simples em tarefas não lineares |
| **1980** | **Sistemas especialistas**, **bases de conhecimento**, **Lisp machines** (estações para linguagens de IA) | Domínios **estreitos** (config, diagnóstico **se** regras estáveis) | **Fragilidade**, gargalo de **aquisição de conhecimento**, **manutenção** cara → **segundo busto** / queda de financiamento (**fim dos 1980–1990** em muitos relatos) |
| **1990–2000** | **ML como estatística**: árvores, **SVM**, *kernels*, **random forests**; mais **dados** e **disco** | **Classificação** tabular e textual com dados **rotulados** | Escolhas más ainda geram **lixo**; **viés** nos dados reflete-se nos modelos |
| **2010 em diante** | **Deep learning**: **GPU**, momento **ImageNet** (~2012) em visão; **RNN/LSTM** depois **Transformers** (~2017) em sequências | **Aprendizagem de representações** em escala quando **rótulos** ou **autossupervisão** alinham | **Fome de dados**, erros **opacos**, **mudança de ambiente**; custo operacional |
| **2020** | Modelos **transformer** **muito grandes**; **LLMs** como categoria de produto | Rascunhos, assistentes de pesquisa, **sugestões** de código | **Alucinação**, **não determinismo**, **privacidade** ao enviar texto do **cliente** para fora |

---

## 3. Famílias de método — encaixe, limites, cautela

| Família | Uso típico | Força | Limite / cautela |
| ------- | ---------- | ----- | ------------------ |
| **Simbólico / regras** | Lógica, normas como **se-então**, *parsers* | **Auditável**, repetível | Falhas de **cobertura**; peritos mantêm regras |
| **Sistemas especialistas (estilo 1980)** | Heurísticas de domínio codificadas | Transparente **se** regras honestas | Conhecimento **desatualizado**; regras em conflito |
| **ML clássico** (árvores, SVMs, modelos lineares, **TF-IDF** + floresta) | Fatias **tabular/textual** **rotuladas** | **Reprodutível** com sementes fixas e *features* versionadas | Precisa de **rótulos** de qualidade; **mudança de domínio** |
| **Deep learning** (CNNs, *transformers* como **encoders**) | Visão, *features* de fala, *embeddings* | Representações ricas | **Compute**, afinação, comportamento **caixa-preta** em partes |
| **Aprendizagem por reforço (RL)** | Jogos, **políticas** em robótica, **simulação** de recomendação | Forte quando o **ambiente** é barato de amostrar | **Ineficiência amostral**; **segurança** e **verificação** em produção são difíceis |
| **Deep RL (DRL)** | **RL** com políticas ou redes de **valor profundas** (ex.: DQN, PPO em *pixels*) | Lida com estado **de alta dimensão**; mesmo ciclo orientado a recompensa do RL tabular | **Não** use **“RDL”** como sigla canônica—o usual em inglês é **DRL** (*deep reinforcement learning*). Herda riscos de **RL + DL** (*reward hacking*, falhas pouco transparentes) |
| **Modelos de linguagem (LM)—clássicos a “grandes”** | *Ranking*, completar, *rescoring* de **ASR**, assistentes | **Fluência**, priores amplos quando os **pesos** cabem em **RAM/GPU** | Risco de **confabulação** com *prompts* abertos; **PII** nos *prompts* |
| **LLM (generativo, estilo chat)** | Rascunhos, *brainstorm*, assistência no **IDE** | Iteração rápida em **linguagem** | **Não** substitui **git/CI** em artefatos regulamentados |

**Assistentes de voz (produtos estilo Siri):** Historicamente um **pipeline** — **reconhecimento de fala**, **detecção de intenção**, **preenchimento de slots**, **política de diálogo**, **síntese de fala** — misturando **PLN clássico**, **LMs** estatísticos ou neurais **menores** e **regras**. Isso **não é o mesmo** que colocar um único **LLM de escala fronteira** no mesmo lugar; o marketing costuma **comprimir** a pilha.

---

## 4. Co-evolução de *hardware* e *software* (porque “grande” agora)

- **CPU → GPU → TPU / grandes *clusters*:** *Throughput* e **largura de banda de memória** definem o **tamanho prático** do modelo e o *batch size*.
- ***Frameworks*** (diferenciação automática, **CUDA**, bibliotecas DL de alto nível): Reduziram o custo **de engenharia** para treinar e implantar redes.
- **Dados + corpora + texto da web:** Pré-treino **autossupervisionado** tornou **LMs** gerais viáveis antes do *fine-tuning* por tarefa.
- **Implicação:** “**Grande**” é em parte uma afirmação de **engenharia** (o que cabe no **seu** orçamento de **VRAM** e **latência**), não um juízo moral sobre qualidade.

---

## 5. Alinhamento com o Data Boar (evidência primeiro)

- **Detecção no produto:** **Regex** + **padrões nomeados** + **ML/DL supervisionado** com **os seus** termos e **as suas** amostras, com pontuação **reprodutível** — ver [SENSITIVITY_DETECTION.pt_BR.md](SENSITIVITY_DETECTION.pt_BR.md). Isso fica na coluna **ML clássico / DL controlado**, não na coluna **LLM generativo aberto**.
- **Saídas de conformidade:** **Achados com foco em metadados**, **norm tags**, agregação de **quasi-identificadores**, sinais de **menores**, **dicas de jurisdição** — artefatos estruturados para revisão **humana**, não prosa generativa que inventa **fontes**.
- **À volta do repositório:** **LLMs** (agentes no IDE, chat do fornecedor) podem ajudar a **rascunhar** documentação ou **explorar** ideias — tratar a saída como **não verificada** até **testes** e **diff** confirmarem; ver [docs/ops/LLM_AGENT_EDITING_CAUTION.pt_BR.md](ops/LLM_AGENT_EDITING_CAUTION.pt_BR.md).

---

## 6. Leitura adicional (independente deste repositório)

- Russell, S. & Norvig, P., *Artificial Intelligence: A Modern Approach* — panorama geral, neutro face a fornecedores.
- Goodfellow, Bengio, Courville, *Deep Learning* — bases de **DL**.
- Histórias oficiais de **DARPA**, **ACM**, cursos universitários — preferir **fontes primárias** ao citar **datas** em material externo.

---

**Veja também:** [COMPLIANCE_FRAMEWORKS.pt_BR.md](COMPLIANCE_FRAMEWORKS.pt_BR.md#detecção-determinística-vs-hype-de-llm-generativo) · [docs/ops/LLM_AGENT_EDITING_CAUTION.pt_BR.md](ops/LLM_AGENT_EDITING_CAUTION.pt_BR.md)
