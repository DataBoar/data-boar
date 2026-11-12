# Histórico de custos por rodada

Estimativa do consumo de tokens do fluxo de agentes, para a auditoria interna. Os valores vêm de
`custos.py --desde <início UTC>` (skill `auditar-projeto`), que lê as sessões do projeto e aplica os
preços da API. Em plano por assinatura, leia-os como proporção do limite de uso, não como cobrança.

Cada rodada tem uma linha aqui e um evento `custo` na issue `[registro] Eventos do projeto` (#2224),
que traz o detalhe por agente e por tarefa. O registro começou em 2026-11-11, sem retroativo.

| Rodada (início UTC) | Total (US$) | Por agente | Por tarefa | Observação |
|---|---:|---|---|---|
| 2026-11-11T20:30 | 10,25 | project-manager 10,19 · sessão sem agente 0,06 | coordenação 10,19 · sem tarefa identificada 0,06 | Apt #2223 (rerun e reabertura das #2222/#2221/#2219), registro ligado (#2224), PR de pins #2227, issue #2226, leitura da #1990, triagem do #data-boar-ops. Sessão do PM apenas; subagentes de outras sessões não entram. |
