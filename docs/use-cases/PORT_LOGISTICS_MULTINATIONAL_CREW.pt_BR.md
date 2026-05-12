# Storyboard de caso de uso — logística portuária, tripulação multinacional (tensão de metadados)

**English:** [PORT_LOGISTICS_MULTINATIONAL_CREW.md](PORT_LOGISTICS_MULTINATIONAL_CREW.md)

Este é um **storyboard em documentação** para oficinas e narrativas de POC. **Não** é análise jurídica exaustiva nem garantia de que cada implantação reproduz o cenário.

## Elenco (papéis genéricos)

- **Estado anfitrião:** Brasil — operações em área portuária ou sob lógica de controle aduaneiro (LGPD sobre tratamento local; regras setoriais de segurança podem coexistir).
- **Titulares:** Tripulantes e visitantes com **documentos de várias nacionalidades** (passaporte, livro marítimo, visto).
- **Sistemas:** Logs de acesso, fotos de gate, manifestos, listas — muitas vezes **um** registro liga **várias** jurisdições por **tipo de documento**, **prefixo de telefone**, **fragmentos de endereço** e identificadores de **RH** armador.

## Storyboard (fluxo)

1. **Navio atraca** — a operação portuária gera registros estruturados e semiestruturados.
2. **Tripulante desembarca** — eventos de identidade e acesso são logados (nomes, números de documento, fotos quando a política exige).
3. **Log cai em repositórios corporativos** — bancos, shares ou tickets; vira **alvo** do Data Boar sob escopo aprovado na governança.
4. **Boar fareja (varredura configurada)** — regex/ML trazem **identificadores** e **categorias sensíveis**; **norm tags** refletem linguagem de inventário.
5. **Dicas de jurisdição opcionais** — metadados podem disparar **zero, uma ou várias** linhas na **Report info** (ex.: tokens estilo EUA vs JP no mesmo texto de coluna/caminho — **heurística**).
6. **Momento de “colisão” (humano)** — o DPO vê **tensão**: várias pistas ou sinais fortes de documento estrangeiro numa operação **ancorada** no Brasil; o **tool não escolhe** lei aplicável.
7. **Ação (organizacional)** — **Assessoria** mapeia base legal, minimização, retenção e fluxo transfronteiro; **CISO** alinha controles de acesso e evidência. O Data Boar entrega **evidência de inventário**, não a ordem de protocolos perante reguladores.

## Como o Data Boar ajuda sem decidir

- **Mostra** onde **identificadores multinacionais** e **tokens regionais** coexistem nas mesmas tabelas/arquivos.
- **Sinaliza** possível relevância de regime via **hints** (quando habilitadas) — sempre com ressalvas de **falso positivo/negativo**.
- **Não substitui** normas de segurança/aduana nem um DMS completo de fluxo jurídico.

## Oportunidade para parceiros

Integradores e consultorias de compliance usam esta narrativa para compradores **adjacentes a porto** ou **hub logístico** que já falam em “manifesto + lista de tripulação” e precisam de um **primeiro mapa de colisão** antes de financiar um programa GRC multi-anual.

## Alinhamento de produto (maintainers)

Teste de carga para **hints de jurisdição**, texto de **colisão** nos relatórios e superfícies **multilíngues** — sem implicar completude para alfândega. Sequenciamento: [docs/README.pt_BR.md](../README.pt_BR.md) *Internal and reference*.

## Documentação relacionada

- [use-cases/README.pt_BR.md](README.pt_BR.md) ([EN](README.md)) — hub com outros storyboards de médio porte (advocacia, contabilidade, pharma).
- [THE_WHY.pt_BR.md](../philosophy/THE_WHY.pt_BR.md) ([EN](../philosophy/THE_WHY.md)) — posicionamento evidência em vez de teatro (seguro para público).
- [ADR 0039](../adr/ADR-0039-retention-evidence-posture-bonded-customs-adjacent-contexts.md) — limite de retenção/evidência em contextos adjacentes à alfândega.
- [JURISDICTION_COLLISION_HANDLING.pt_BR.md](../JURISDICTION_COLLISION_HANDLING.pt_BR.md) ([EN](../JURISDICTION_COLLISION_HANDLING.md))
- [MINOR_DETECTION.pt_BR.md](../MINOR_DETECTION.pt_BR.md) ([EN](../MINOR_DETECTION.md)) — quando metadados de tripulantes/visitantes podem envolver menores
- [MAP.pt_BR.md](../MAP.pt_BR.md) ([EN](../MAP.md))
- [ADR 0038](../adr/ADR-0038-jurisdictional-ambiguity-alert-dont-decide.md)
