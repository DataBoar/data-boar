# Plano do projeto Data Boar

**Atualizado:** 2026-11-26 (só a fila do v1.8.1). O restante é de 2026-11-18 (base: `origin/main` 87e169fa, após o merge da PR #2271)
**Fontes:** milestones e issues do GitHub (`DataBoar/data-boar`), `docs/plans/PLANS_TODO.md` e `docs/plans/PLAN_M365_GRAPH_CONNECTORS.md`.
**Papel deste arquivo:** visão de gestão por entregável (milestone). O detalhe de cada plano técnico continua em `docs/plans/PLAN_*.md`, e `PLANS_TODO.md` segue como espelho de execução. Este arquivo não os substitui.

Legenda: [V] verificado (GitHub ou execução) · [H] hipótese ou não verificado. As contagens são de **issues, sem pull requests**, lidas com `gh` em 2026-11-18. Os totais por milestone que o GitHub mostra (238, 25, 9, 7 e 336) incluem também PRs ligadas ao milestone, por isso diferem destes. Milestones sem data de entrega não têm prazo registrado.

## 1. Indicadores [V]

### 1.1 Projeto inteiro, desde o início

- **Issues:** 757 fechadas de 1.072 (71%); 315 abertas.
- **Pull requests:** 949 mescladas; 1 aberta (#2257).
- **PLANS_TODO** (painel gerado por script): 189 de 308 linhas concluídas (61%), 119 incompletas, sendo 24 no horizonte H0 e 28 no H1. O painel não foi validado linha a linha: de 6 linhas H0 listadas como pendentes, 5 já estavam fechadas no GitHub (a #756 segue aberta).

### 1.2 Já entregue (milestones fechados)

| Milestone | Issues fechadas | Itens com PRs (GitHub) |
|---|---:|---:|
| v1.7.4 | 16 | 25 |
| 1.7.4.post9 | 9 | 9 |
| v1.8.0-beta | 2 | 7 |
| v1.8.0 | 222 | 238 |
| **Total entregue** | **249 (100%)** | 279 |

### 1.3 Fase atual (v1.8.1 a v1.8.5): 31 de 334 issues fechadas (9%)

| Milestone | Fechadas | Abertas | Pronto | Foco |
|---|---:|---:|---:|---|
| v1.8.1 | 21 | 19 | 52,5% | Release 1.8.1 e demo na VPS; a imagem 1.8.1 já roda na demo |
| v1.8.2 | 4 | 113 | 3% | Conector Microsoft 365, empacotamento e segurança de integridade |
| v1.8.3 | 4 | 37 | 10% | Desempenho do estágio Rust e licenciamento |
| v1.8.4 | 0 | 58 | 0% | SDK de plugins |
| v1.8.5 | 2 | 76 | 3% | Observabilidade, portabilidade (wheelhouse) e autoauditoria |

### 1.4 Fora de versão

- **Sem milestone:** 467 fechadas, 1 aberta. É a maior parte do que já foi feito sem estar ligado a uma versão do roadmap.
- **Milestone `backlog`:** 10 fechadas, 11 abertas.

Conferência: 249 + 31 + 10 + 467 = 757 fechadas; 303 + 11 + 1 = 315 abertas; total 1.072.

## Fila atual do v1.8.1: recorte tático (26/nov/2026)

Recorte operacional, subordinado a `docs/plans/PLANS_TODO.md` (fonte única de situação e sequência dos planos); se divergirem, vale o `PLANS_TODO` e este arquivo se corrige. A ordem abaixo ainda não foi confrontada linha a linha com ele. Estados conferidos no GitHub em 26/nov [V]: 33 issues fechadas e 34 abertas no v1.8.1 (49%; uma das abertas é a de registro, #2224). Os indicadores da seção 1 e as seções 2 a 6 seguem com a foto de 18/nov.

| Ordem | Entrega | Issues e PRs | Estado | Quem |
|---:|---|---|---|---|
| 1 | Guia de integração (EN e pt-BR, linha 43) ainda diz que Azure Blob e GCS são Pro; são Enterprise. Conferir `docs/desenho/2306.md` e a ADR-0064. Na mesma PR: este plano, `operacao.md`, auditorias, visão e custos | #2306 (Refs) | Revisão pós-merge da #2381: corrigir | opencode; branch, commit e push com o operador |
| 2 | Paridade do prefiltro: corrigir o estágio Rust sem estreitar o Python; teto de testes pulados sem subir; conferir 5 achados da segunda opinião | PR #2378 (#2186, #2246) | CI vermelho em `697e9a57` | opencode; Hermes revisa |
| 3 | Correções de segurança (detalhe reservado): CI vermelho e revisão a refazer no SHA certo | PR #2379 (#2239, #2259, #2253) | CI vermelho em `cc287fa5` | opencode; Hermes revisa; merge do operador |
| 4 | Dependências numa PR própria, com selo; Python 3.15 (#2314) vai para o v1.8.2 | PRs #2315 a #2318 | Não iniciada | operador autoriza |
| 5 | Faxina de SMB, testes e CI; o que tocar gate vai em PR separada, com selo | #2238, #2305, #2249, #2267, #2295 | Não iniciada | opencode |
| 6 | Invariantes do produto (P0); parte depende de decisão do operador | #2364 | Não iniciada | arquiteto, depois dev |
| 7 | Limite por varredura; depois fechar o épico de object storage | #2313, #2306 | Não entregue | dev |
| 8 | Empacotamento | #2189, #2156 | Não iniciada | dev |

**Depois do v1.8.1:** autenticação do Azure (#2369, #2368), logo depois de a demo ir para a VPS (estado não conferido [H]); arquitetura #2366, #2367, #2365; #2371; PostgreSQL e pgvector (#1731, #1732, #1734) e #2297.

**Decisões do operador em aberto:** tirar do v1.8.1 os itens de pesquisa, comerciais e de processo (#2321 a #2325, #2297 a #2299, #1731, #1732, #1734, #1446, #2140, #2303, #2276); destino de #2376, #2273 e #2183; repin do benchmark (#2186); subpacotes da #2185; alvo do delta do wheelhouse; branches e stashes antigos (backup antes de remover).

## 2. Épico em andamento: leitor Microsoft 365 via Graph (#2206, milestone v1.8.2)

| ID | Entrega | Estado |
|---|---|---|
| 2206.0 (#2260) | Fase 0: prova real em modo delegado contra OneDrive pessoal | Provada na máquina de desenvolvimento e na VPS [V]; a issue ainda está aberta e deve ser fechada com a evidência |
| 2206.1 (#2261) | Fase 1: leitor `sharepoint_online`, modo delegado, Enterprise | Concluída: PR #2265 mesclada em 17/nov [V] |
| 2206.7 (#2269) | Correção do cache do token (só toca arquivo com marcador do Boar) | Concluída: PR #2271 mesclada em 18/nov [V] |
| 2206.2 (#2262) | Fase 1c: app-only para tenant de trabalho | Desenho local (`design/m365-app-only`); decisões O-1 a O-7 do operador pendentes; sem prova real, por falta de tenant [H] |
| 2206.3 (#2263) | ADR das decisões DEC-1 a DEC-8 | Pendente; precisa do selo do operador |
| 2206.4 (#2264) | Ocultar Bearer e URLs pré-autenticadas nos logs | Pendente; dev externo: opencode (plano B: pi), depois do desenho e dos testes do QA |
| 2206.5 (#2266) | Documentação de governança, pitches CISO e DPO | Branch `docs/m365-governance` (03f1ecf7), local; falta o `check-all` completo e a decisão sobre uma PR só |
| 2206.10 (a criar) | Raiz do OneDrive por chave explícita no config (sem default) | Proposta; aguarda a confirmação do operador (P3). Já destinada ao dev normal (backend-dev-senior) |
| 2206.9 (#2272) | Rótulo de origem do conector nos achados e relatórios | Pendente |
| #2273 | Inventário de fontes inclui filesystem, SMB e Graph | Pendente |
| #2270 | Sugestões S1 a S8 da revisão | Pendente; dev externo: opencode (plano B: pi), depois do desenho e dos testes do QA |
| Fase 1b | Varredura incremental por delta do Graph | Pendente |
| Fase 2 | Exchange Online (e-mail) | Pendente |
| Fase 3 | Guia de permissão e consentimento para o DPO e a TI do cliente | Pendente |

Limites conhecidos [V]: itens na raiz do OneDrive (2 arquivos e o "Cofre Pessoal") não são alcançados, porque o conector recusa a raiz do drive. Decisão do operador (18/nov), em duas etapas: primeiro, subpastas bastam e a raiz só por encomenda; depois, pediu para completar a raiz também. A tarefa 2206.10 (chave explícita para a raiz, código, nova imagem e nova assinatura) está proposta e aguarda a confirmação dele. A pasta vazia "Microsoft Copilot Chat Files" não é coberta.

## 3. Demo na VPS (reunião de 18/nov, 11h)

| Item | Estado |
|---|---|
| Imagem `1.8.1-demo-m365b` (SHA 91ef3005) rodando como `apresentacao` | No ar [V] |
| Config principal único com 9 alvos (7 anteriores + 2 de Microsoft 365) | No ar; scan completo de 587 achados, 73 do OneDrive [V] |
| Check de estado da VPS (`check_reboot.sh`) | `TUDO OK` em 18/nov 11:50 UTC [V] |
| Teste real de reboot da VPS (runbook §7) | **Não cumprido**: a VPS não reiniciou (uptime 3d10h); decisão do operador [V] |
| Container `dashboard` | Segue na imagem antiga (45fc2ee1e41c), sem alteração [V] |
| Bloco WebAuthn comentado no config | Entregue, desligado [V] |
| Isolamento por token expirado (falha só no alvo M365) | Coberto por testes, não exercitado ao vivo [H] |

## 4. Próximo: v1.8.2 além do Microsoft 365

Itens P1 abertos [V]:

- **#2218:** wheelhouse x86-64-v1 defasado em relação ao `requirements.txt` do 1.8.0.
- **#2184:** assinatura de pacotes nativos (cerimônia de chaves e repositório).
- **#2168:** a raiz de confiança da âncora de integridade tem de ser a assinatura do release.
- **#1467:** MSI e winget com cp314/cp314t (ADR-0084).
- Épicos: **#2217** (matriz de plataformas honesta) e **#2013** (conectores de CRM além do HubSpot).

## 5. v1.8.3 a v1.8.5 (resumo)

- **v1.8.3:** #2181 (licença verificada também no lado Rust), #1746 (conectores de APIs públicas brasileiras). #2182 e #2202 (desempenho do estágio Rust) estão fechadas.
- **v1.8.4:** #865 (formalizar o SDK de plugins).
- **v1.8.5:** #1477 (autoauditoria), #1462 (criptografia ágil e PQC), #1458 (observabilidade), #1366, #1182 e #1171 (wheelhouse e compatibilidade mínima), #1197 e #1196 (sobreposição de múltiplos frameworks e `validate-profile`), #989 (cadeia de suprimentos).

## 6. Pendências de decisão do operador [V]

1. **PR #2257** (docs): reassinar o commit 6ea907f2 (`unknown_key`) se quiser mesclar; a linha da INTEGRITY_HUB deve apontar para `core/integrity_anchor.py` e `core/integrity_signed_manifest.py`.
2. **Reboot da VPS** antes ou depois da reunião; hoje o §7 do runbook está pendente.
3. **App-only (#2262):** decisões O-1 a O-7 e o ADR.
4. **Raiz do OneDrive (P3, tarefa 2206.10):** o operador pediu para completar a raiz; falta ele confirmar a proposta (chave explícita, fluxo normal, imagem nova só quando ele mandar).
5. **Entra:** remover `Files.Read.All` do app registrado.
6. **Docs de governança:** uma PR só, ou junto do épico #2262.
7. **FAQ do site (3 perguntas):** uma PR depois da demo de 18/nov.
8. **Issues abertas sem decisão:** #2267 (Galaxy no CI), #2253 (módulo de persistência fora do manifesto de integridade), #2241 (grype da imagem).

## 7. Riscos e limites

- O fluxo é supervisionado: só o operador mescla e sela; o `main` exige commit assinado e PR.
- O app-only não tem prova real: depende de um tenant de trabalho [H].
- O desempenho do pool de arquivos na VPS (1 vCPU) não mostra paralelismo de CPU; ensaiar na máquina de desenvolvimento [V].
- `core/database.py` está fora do manifesto de integridade (#2253) e não deve ser alegado como coberto [V].

## 8. Perguntas ao cliente

### Respondidas (18/nov/2026, pelo operador, no chat; aceitou a suposição padrão)

| ID | Pergunta | Resposta |
|---|---|---|
| P1 | A visão deve ter datas por versão? | Não: só ordem e andamento. |
| P2 | Ordem das etapas: 1.8.1, depois 1.8.2, 1.8.3, e 1.8.4 e 1.8.5 em paralelo? | Sim (a ordem veio da numeração das versões). |
| P4 | Há tenant de trabalho para provar o app-only (#2262)? | Não: segue como roadmap, sem prova, com O-1 a O-7 pendentes. |
| P5 | E-mail (Exchange Online): escopo por caixa postal ou por grupo? | Por caixa ou grupo, só depois do app-only. |
| P6 | Mostrar "Microsoft 365" como origem nos achados e relatórios (#2272)? | Sim. |
| P7 | Documentação de governança do M365 (CISO e DPO): uma PR só ou junto do app-only? | Uma PR só, junto da épica. |
| P8 | FAQ do site (3 perguntas): depois da demo? | Sim: uma PR depois de 18/nov. |

### Em aberto

| ID | Pergunta | Suposição adotada | Depende |
|---|---|---|---|
| P3 | O alvo do OneDrive deve ler o drive inteiro, incluindo a raiz? Hoje o conector recusa a raiz (2 arquivos e o "Cofre Pessoal" ficam de fora). | O operador respondeu primeiro "subpastas bastam, a raiz por encomenda" e depois "completa a raiz também". Suposição: ler a raiz por chave explícita no config, na tarefa 2206.10, sem default; só vira imagem nova quando ele mandar. | Seção 2, limites conhecidos |
| P9 | Os scripts da demo (`apply_config.py`, `check_reboot.sh`, build, sondas M365) entram no repositório (e onde) ou ficam em `~/.cache/claude-pm`? | Ficam onde estão, até a decisão. O operador já mandou não versionar o `smoke-demo.sh`. | Seção 3 |

— project-manager
