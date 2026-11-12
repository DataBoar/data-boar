# Histórico de custos por rodada

Estimativa do consumo de tokens do fluxo de agentes, para a auditoria interna. Os valores vêm de
`custos.py --desde <início UTC>` (skill `auditar-projeto`), que lê as sessões do projeto e aplica os
preços da API. Em plano por assinatura, leia-os como proporção do limite de uso, não como cobrança.

Cada rodada tem uma linha aqui e um evento `custo` na issue `[registro] Eventos do projeto` (#2224),
que traz o detalhe por agente e por tarefa. O registro começou em 2026-11-11, sem retroativo.

| Rodada (início UTC) | Total (US$) | Por agente | Por tarefa | Observação |
|---|---:|---|---|---|
| 2026-11-11T20:30 | 71,94 | project-manager 48,73 · backend-dev-senior 16,02 · revisor-senior 7,12 · sessão sem agente 0,08 | coordenação 48,73 · sem tarefa identificada 18,87 · #2228 2,84 · #1990 1,51 | Acumulado desde o início (a medição parcial de 10,41 feita no meio da rodada está incluída). Apt #2223 e reaberturas das #2222/#2221/#2219, registro ligado (#2224), pins #2227, man 7 #2229, hermeticidade #2231, uv pinado e paridade `.ps1`/`.sh` na #2233 (CI inteiro verde, incluindo Windows). Estimativa do `custos.py` com a sessão do PM e os subagentes dele; subagentes de outras sessões não entram. |
