# Inspirações de craft de engenharia — como aprendemos, o que adotar, o que evitar

**English:** [ENGINEERING_CRAFT_INSPIRATION_ANALYSIS.md](ENGINEERING_CRAFT_INSPIRATION_ANALYSIS.md)

## Objetivo

Explicar como o projeto **consome** a [tabela de inspirações de craft](inspirations/ENGINEERING_CRAFT_INSPIRATIONS.pt_BR.md) (canais no YouTube, autores de ferramentas, educadores) como **insumo de ofício e narrativa** — não como requisitos, endosso de cada opinião ou substituto de testes e modelo de ameaças.

A tabela permanece **curta** (nomes, links, uma linha de “por que aqui”). Este arquivo guarda **análise transversal**: temas, hábitos a imitar, modos de falha e um checklist repetível.

**Nota índice curta na pasta:** [inspirations/ENGINEERING_CRAFT_ANALYSIS.pt_BR.md](inspirations/ENGINEERING_CRAFT_ANALYSIS.pt_BR.md).

## Fontes (contínuo)

- **Lista canônica:** [ENGINEERING_CRAFT_INSPIRATIONS.pt_BR.md](inspirations/ENGINEERING_CRAFT_INSPIRATIONS.pt_BR.md) — acrescentar ou remover linhas ali; atualizar os clusters abaixo só quando o *padrão* mudar.
- **Sobreposição com narrativa de segurança:** [SECURITY_INSPIRATION_GRC_SECURITY_NOW.pt_BR.md](SECURITY_INSPIRATION_GRC_SECURITY_NOW.pt_BR.md) e [inspirations/SECURITY_NOW.md](inspirations/SECURITY_NOW.md) — **Steve Gibson** / *Security Now* está detalhado ali; a tabela de craft aponta essa linha **só** pelo estilo explicativo, sem duplicar política GRC.

Este é um guia vivo. Amplie quando a mesma lição surgir de forma recorrente em criadores diferentes.

## Essa classe de fonte é boa para nós?

### Pontos fortes (por que sim)

- **Empatia com operador:** Muitas entradas mostram como pessoas instalam, quebram e recuperam sistemas — paralelo a CONTRIBUTING, docs de primeira execução e validação em homelab.
- **Hábitos de explicar a stack:** Modelo mental claro, “mostrar a falha” e benchmark honesto ajudam narrativas de privacidade/compliance a não mentir por omissão.
- **Calibragem de locale e audiência:** Linhas em pt-BR ancoram como operadores brasileiros consomem especificação, risco e tutorial — reduz prosa “só EUA” por acidente.
- **Narrativa de produto de longo prazo:** Ferramentas entregues e histórias retrô/debug reforçam documentar trade-offs e restrições legadas.

### Limites (por que não copiar cegamente)

- **Entretenimento e ritmo:** Formatos rápidos ou com meme ensinam **gancho e densidade**, não comportamento contratual; não substituem ADR, testes ou SECURITY.md.
- **Fornecedor e incentivo de canal:** Academias de vendor e educadores de uma única stack puxam para um ecossistema; docs neutros de produto ainda precisam de enquadre agnóstico de stack onde couber.
- **Jurisdição e domínio:** Aviação, reparo de consumidor ou hobbies retrô são **analogias** de disciplina narrativa — não autoridade jurídica, de segurança física nem de infosec para o Data Boar.
- **Risco parassociais:** “Gostamos deste criador” não pode virar “temos que concordar com o último vídeo”.

## Clusters temáticos (usar a tabela por tema)

Use estes clusters ao garimpar a tabela; um criador pode mentalmente cair em mais de um, mas a **linha da tabela** continua sendo o único alvo de link.

| Cluster                                   | Intenção para o Data Boar                                      | Linhas de exemplo (não exaustivo)                                            |
| -------                                   | -------------------------                                      | -----------------------------------                                          |
| **Onboarding inclusivo**                  | Linguagem simples, menos medo de CLI e primeira execução       | Veronica Explains, Savvy Nik, Diolinux Labs, *You Suck at Programming*       |
| **Gancho vs profundidade**                | README e “em que caixa isso cai?” sem falsa precisão           | Fireship (combinar com docs lentos)                                          |
| **Homelab e infraestrutura**              | Runbooks, realidade de LAN/armazenamento, falhas de operador   | Level1Techs, UniFi Academy (caveat de vendor), Gary H Tech, SafeSourceTVs    |
| **Legado e paciência**                    | Encodings esquisitos, exportações antigas, “o que tentamos”    | Michael MJD, Nostalgia Nerd, The 8-Bit Guy, Cathode Ray Dude, Usagi Electric |
| **Ciência e matemática explicadas**       | Ideias contraintuitivas, incerteza honesta, visual             | Veritasium, 3Blue1Brown, Steve Mould, Stand-up Maths                         |
| **Entrega e profundidade de sistemas**    | Narrativa de ferramenta confiável, honestidade em escala de SO | Mark Russinovich, Dave Plummer, GitHub (canal oficial)                       |
| **Padrões de doc portátil**               | Pequenas peças reutilizáveis, wiki num arquivo                 | Linhagem TiddlyWiki                                                          |
| **Realidade do operador pt-BR**           | Tom, custo/benefício, alfabetização em segurança local         | Diolinux Labs, Clube do Hardware, Colleague-Q Colleague-Kentel, Aviões e Músicas         |
| **Baixo nível e engenharia de segurança** | Primeiros princípios para desempenho e limites de confiança    | Low Level Academy / StackSmash / LowLevelTV                                  |

## O que vale tentar imitar

- **Nomear o modo de falha** antes do conserto (ou antes de só mostrar o caminho feliz).
- **Mostrar o trabalho:** o que foi medido, o que mudou, o que ainda quebrou — principalmente em homelab e benchmark.
- **Separar gancho de marketing do contrato:** explicações curtas encaminham para comportamento exequível (código, config, testes).
- **Avisos de segurança e escopo** onde houver risco físico, alta tensão ou domínio regulado — mesmo quando a analogia for só de narrativa.
- **Ligar à verdade do repositório:** inspiração → plano, ADR, teste ou runbook de operador — não admiração solta.

## O que evitar imitar

- Tratar opinião de criador como **política implícita de produto** sem artefato no repositório.
- **Captura por vendor** em seção de arquitetura ou compliance que deveria ser neutra.
- **Falsa precisão:** meme, comédia ou edição confiante não substituem certeza de detecção nem alegação jurídica.
- **Esconder o limite:** se o scanner ou o modelo são incertos, o doc precisa dizer — não importa o quão polido seja o explicador externo.

## Fluxo prático (token-aware)

1. **Amostrar por cluster** (tabela acima), não maratonar catálogo inteiro de uma vez.
1. Para cada hábito candidato, rotular **Adotar agora**, **Backlog com justificativa** ou **Rejeitar (não encaixa)**.
1. Amarrar o resultado a um **artefato** (plano, ADR, trecho de doc, teste, guarda de workflow).
1. Se uma linha ficar obsoleta ou fora de missão, **podar a tabela**; alinhar os exemplos de cluster neste arquivo.

## Checklist de avaliação (por hábito ou formato externo)

- Melhora **clareza para operador** ou **onboarding de contribuidor**, não só entretenimento?
- Dá para **verificar** o comportamento que nos importa (testes, logs, passos reproduzíveis)?
- Conflita com **secure-by-default** ou postura de compliance documentada em outro lugar?
- O **custo de manutenção** é aceitável (dívida de doc, carga de suporte)?
- Se a fonte é **específica de vendor**, o texto neutro está preservado onde o produto precisa ser agnóstico de stack?

## Recorte de decisão atual

- **Qualidade da inspiração:** Varia muito por canal; **temas** pesam mais que uma personalidade só.
- **Postura de adoção:** Seletiva; tabela + esta análise são **insumos**, não ordens.
- **Uso imediato:** tom de onboarding, limites honestos em docs de operador, notas de homelab/realismo, garimpo por cluster.

## Documentos relacionados

- [ENGINEERING_CRAFT_INSPIRATIONS.pt_BR.md](inspirations/ENGINEERING_CRAFT_INSPIRATIONS.pt_BR.md)
- [inspirations/README.pt_BR.md](inspirations/README.pt_BR.md) / [inspirations/INSPIRATIONS_HUB.pt_BR.md](inspirations/INSPIRATIONS_HUB.pt_BR.md)
- [SECURITY_INSPIRATION_GRC_SECURITY_NOW.pt_BR.md](SECURITY_INSPIRATION_GRC_SECURITY_NOW.pt_BR.md) (segurança; sobreposição parcial)
- [CONTRIBUTING.md](../CONTRIBUTING.md)
- [AGENTS.md](../../AGENTS.md)
