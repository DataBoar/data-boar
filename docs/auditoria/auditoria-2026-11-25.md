# Auditoria do projeto Data Boar, 25/nov/2026

Relatório interno, não vai ao cliente. Fonte: `eventos.py` e `custos.py` da skill `auditar-projeto`, mais o GitHub. O relatório fica fora do repositório porque o Claude não escreve no `data-boar`. Os dados brutos estão nesta mesma pasta.

## Resumo

- **Eventos:** 100 tarefas lidas. 31 têm eventos registrados; as demais são do fluxo antigo e entram sem violação.
- **Violações:** 13 apontadas pelo script, de 5 tipos. A principal é estrutural: o projeto opera supervisionado e sem QA dedicado. Não há PR de testes de aceitação nem evento `desenho-pronto` nas tarefas.
- **Gargalo:** as decisões e o merge do operador, normais no modo supervisionado, e as rodadas de revisão. A 2280.2 teve 4 rodadas; a 2306.8 e a #2370 tiveram 2 cada.
- **Custo, desde o início do registro:** US$ 1.006,70 pela estimativa da API (registrado pelo Claude Code: US$ 899,92). O project-manager responde por 62% (US$ 627,83).

## Violações (conferidas)

| Tarefa | Violação | Leitura |
|---|---|---|
| 2306.8 (#2360), 2306.2 (#2310), 2306.1 (#2309), #2228, #1990, #2232, 2280.2, 2280.3 | liberada sem `desenho-pronto`; sem PR de testes | No supervisionado, o desenho vai no brief e os testes vêm junto no PR do dev. É um desvio de processo recorrente, não um acidente. |
| 2206.1 | sem PR de testes | Idem. |
| 2306.1, #1820, #1322, 2269 | `tarefa-iniciada` antes de `pronta-para-dev` | O dev externo começou pelo despacho direto do PM, sem o evento de liberação. |
| #2228 (PR #2231) | **mesclado com veredito `corrigir`** | Grave. É anterior ao fix forward como prática; registrar o motivo na issue. |
| #1990 (PR #2229) | **mesclado sem revisão do último commit** | Grave. Repete o padrão da #2361 (merge com `corrigir` depois, resolvido em fix forward pela #2373). |

**O que o script não vê:**
- A revisão de segurança (KP) não rodou na #2361 (sem orçamento) e deu `inconclusivo` na #2379 (gitleaks com timeout, keen-platypus#520).
- O wrapper do Hermes não publicou a revisão da #2379.
- Os eventos das PRs #2377, #2378 e #2379 ainda não foram registrados nas issues.

## Custo

### Por agente (US$)

| Agente | Custo |
|---|---:|
| project-manager | 627,83 |
| backend-dev-senior | 205,95 |
| arquiteto-senior | 93,12 |
| revisor-senior | 45,17 |
| general-purpose | 13,62 |
| qa-senior | 12,90 |
| outros | 8,11 |

**Por modelo (US$):** sonnet 519,65 · opus 485,82 · haiku 1,23.

**Tokens:**
- leitura de cache: 3,17 bilhões
- escrita de cache: 58 milhões
- saída: 9,4 milhões
- chamadas: 10.066

**Por tarefa:** 99% está em "coordenação" (627,83) e "sem tarefa identificada" (365,33). As issues e os commits não carregam o ID `[x.y]` no título, então o custo não se liga às tarefas.

**Leitura:** a leitura de cache domina o custo. São sessões longas de PM, com o contexto inteiro relido a cada passo. Esta sessão, por exemplo, foi compactada várias vezes. O backend-dev rodou em opus e em sonnet, e o PM em opus e em sonnet.

## Recomendações

1. **Sessões de PM mais curtas.** Fechar a rodada e fazer `/clear` a cada épica. É a maior alavanca de custo.
2. **Tarefas com o ID `[x.y]` no título** da issue e do PR, para o `custos.py` ligar o custo à tarefa.
3. **Merge só com revisão do SHA final.** Duas violações graves e um caso de fix forward (#2361). Sugestão ao operador: o `merge-green` recusar quando o último veredito for `corrigir` ou anterior ao HEAD.
4. **Registrar os eventos do despacho a dev externo** (`pronta-para-dev` antes de `tarefa-iniciada`) e os eventos de PR das #2377, #2378 e #2379.
5. **Decidir o QA no supervisionado.** Ou o desenho declara "aceitação: não se aplica (testes no PR do dev)", ou volta o PR de testes. Hoje é violação permanente. A decisão é do operador.
6. **Trocar harness externo antes de subagente Claude.** Já é ordem do operador; o efeito deve aparecer na próxima auditoria (custo do backend-dev menor).
7. **Defeitos de ferramenta para o framework:**
   - o wrapper do Hermes perde o relatório;
   - o KP fica `inconclusivo` quando o gitleaks dá timeout (keen-platypus#520).

Primeira auditoria registrada. Não há números anteriores para comparar, só o histórico de rodadas em `docs/custos.md`, iniciado em 11/nov.
