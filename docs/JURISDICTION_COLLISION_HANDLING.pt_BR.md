# Tratamento de colisão de jurisdição (voltado ao DPO)

**English:** [JURISDICTION_COLLISION_HANDLING.md](JURISDICTION_COLLISION_HANDLING.md)

Este guia explica como **ler** as **dicas de jurisdição** opcionais quando os metadados sugerem **mais de um** regime de privacidade em jogo — sem tratar o produto como motor jurídico.

## O que o Data Boar faz e não faz

- **Faz:** Expor texto **heurístico** de “possível relevância” na planilha **Report info** do Excel (quando as dicas estão habilitadas), usando **apenas metadados dos achados** (nomes de coluna/tabela/arquivo/caminho, `pattern_detected`, `norm_tag`, etc.) — ver [ADR 0026](adr/ADR-0026-optional-jurisdiction-hints-dpo-facing-heuristic-metadata-only.md) e [ADR 0038](adr/ADR-0038-jurisdictional-ambiguity-alert-dont-decide.md).
- **Não faz:** Determinar **qual lei se aplica**, **qual formulário preencher primeiro**, **jurisdição mais restritiva** como resultado jurídico automático, nem **base legal** (incluindo LGPD Art. 7 II ou exceções de segurança/aduana). **Assessoria jurídica** e o **DPO** detêm essas decisões.

## A “tempestade perfeita” (por que este doc existe)

Operações multinacionais — logística, portos, aviação, folha compartilhada — costumam ter **um perfil** de dados em que **sinais apontam para lados diferentes**: tipo de documento ou prefixo de telefone sugerem um país, empregador ou hospedeiro outro, auditoria ou regime aduaneiro outro. Isso é risco de **paralisia operacional** para times de privacidade, não só problema de regex.

**Adjacência alfandegária / recinto:** programas de fronteira ou estilo **recinto** podem **exigir** coleta que parece “pesada” sob um olhar só de minimização de privacidade. O Data Boar continua entregando só **evidência de inventário** e **hints**; **não** rotula linhas como “obrigação legal cumprida” nem escolhe prazo de retenção — ver [ADR 0039](adr/ADR-0039-retention-evidence-posture-bonded-customs-adjacent-contexts.md) e [THE_WHY.pt_BR.md](philosophy/THE_WHY.pt_BR.md).

A oportunidade do Data Boar é **visualizar o emaranhado** (linguagem de inventário e triagem) para o **DPO** e o **CISO** priorizarem **revisão com assessoria** — não desatar o nó no software.

## Origem do faro (*Scent origin*, metáfora)

**Origem do faro** é um rótulo narrativo neste repositório (ver [GLOSSARY.pt_BR.md](GLOSSARY.pt_BR.md#glossary-stakeholder-jargon)): dicas de jurisdição são **sinais probabilísticos de incidência** inferidos a partir de metadados **incompletos** — como captar **vários** cheiros ao mesmo tempo. Cheiro forte **não** é certeza jurídica.

## Camadas de pista (lente analítica)

Use esta lente ao ler relatórios e desenhar playbooks:

| Camada | Significado (documentação) | Entradas típicas (exemplos) |
| ------ | --------------------------- | ---------------------------- |
| **Primária (âncora)** | **Âncora operacional**: onde o **scanner roda** e onde ficam os **sistemas do controlador sob varredura** (contrato, escopo RoPA/SOX, país anfitrião). Costuma dominar **política interna** e retenção. | Região de implantação, rótulos de alvo na config, política corporativa escolhida (fora do produto). |
| **Secundária (natureza do dado)** | **Sinais de formato**: identificadores e norm tags que **sugerem** regimes que o time deve **considerar** (ex.: CPF → vocabulário Brasil, SSN → EUA). | `norm_tag`, `pattern_detected`, ganchos de compliance sample. |
| **Contextual (deriva em metadados)** | **Tokens geográficos fracos** em nomes/caminhos (DDD, UF, prefixos tipo CEP) que podem **sobrepor** regiões ou **falso positivo**. | Strings de coluna/caminho pontuadas em `report/jurisdiction_hints.py` (US-CA, US-CO, JP hoje). |

**Âncora vs deriva:** **Âncora** é a base operacional/jurídica daquela rodada de inventário; **deriva** são dados “de passagem” ou de **outros** contextos (manifesto de tripulação, formato de ID estrangeiro, RH multinacional). O produto **não** classifica automaticamente âncora vs deriva; o time aplica isso em oficinas.

## “Colisão de jurisdição” hoje vs roadmap

**Hoje (entregue):** Quando várias heurísticas regionais disparam, a planilha **Report info** pode mostrar **mais de uma** linha de dica de jurisdição (ex.: US-CA e US-CO acima do limiar). Isso é um **sinal visível de sobreposição** para humanos — ainda **sem** “score de colisão” numérico e **sem** tabela por achado.

**Roadmap / inteligência de produto (não prometido neste release):** Um **resumo de colisão** consolidado (contagens, faixa de severidade, flag opcional por sessão) seria desenho **separado**: revisão de privacidade, UX no Excel/API e atualização de ADR. Ver [ADR 0038](adr/ADR-0038-jurisdictional-ambiguity-alert-dont-decide.md).

## Frase sugerida para assessoria (pode copiar em slides)

> **O Data Boar não emite parecer jurídico.** Ele pode trazer à tona **dicas de jurisdição sobrepostas** a partir de **metadados** para o time ver **onde há tensão**. Quando várias pistas se aplicam, as organizações costumam adotar as **salvaguardas mais exigentes na prática** até a assessoria — mas essa **escolha** **não** vem codificada como veredito automático no produto.

## Documentação relacionada

- [USAGE.pt_BR.md](USAGE.pt_BR.md) — `report.jurisdiction_hints`, `--jurisdiction-hint`, API/painel ([EN](USAGE.md))
- [COMPLIANCE_AND_LEGAL.pt_BR.md](COMPLIANCE_AND_LEGAL.pt_BR.md) — teto de linguagem ([EN](COMPLIANCE_AND_LEGAL.md))
- [MAP.pt_BR.md](MAP.pt_BR.md) — índice por preocupação ([EN](MAP.md))
- [use-cases/PORT_LOGISTICS_MULTINATIONAL_CREW.pt_BR.md](use-cases/PORT_LOGISTICS_MULTINATIONAL_CREW.pt_BR.md) — storyboard (cenário não exaustivo)
- [ADR 0025](adr/ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md), [ADR 0026](adr/ADR-0026-optional-jurisdiction-hints-dpo-facing-heuristic-metadata-only.md), [ADR 0038](adr/ADR-0038-jurisdictional-ambiguity-alert-dont-decide.md), [ADR 0039](adr/ADR-0039-retention-evidence-posture-bonded-customs-adjacent-contexts.md)
- [THE_WHY.pt_BR.md](philosophy/THE_WHY.pt_BR.md) ([EN](philosophy/THE_WHY.md))
