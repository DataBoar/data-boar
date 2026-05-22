---
# ADR-0061 — U-axis issue sub-order and cross-milestone gate
**Status:** Accepted
**Date:** 2026-05-22
**Relates to:** ADR-0055 (anti-collision contract)

## Contexto
ADR-0055 estabelece que os eixos de priorização são ortogonais e não devem ser colapsados. Ele NÃO define como um agente deve usar o eixo U para ordenar issues quando múltiplos issues têm o mesmo P label e milestone. Resultado sem esta ADR: agente pode escolher qualquer P2/v1.7.5-beta em qualquer ordem.
A rule `.cursor/rules/execution-priority-and-pr-batching.mdc` implementa o comportamento; esta ADR é o contrato formal que lhe dá status de lei no repositório.

## Decisão
### Sub-ordenação por U dentro do mesmo P+milestone
| U | Descrição | Comportamento do agente |
|---|---|---|
| U0 | security/safety now | Bloqueia todo o restante da sessão até resolver |
| U1 | high-value / chain blocker / deadline externo | Executa antes de U2/U3/sem-U |
| U2 | valioso, sem deadline hard | Executa antes de U3/sem-U |
| U3 | explicitamente diferido | Executa após U0/U1/U2 |
| sem U | ausência de tag U no body | Tratado como U3 — menor sub-prioridade dentro do milestone |

### Gate cross-milestone
- Issues de milestone posterior (v1.7.5-beta) NÃO iniciam antes do milestone anterior (v1.7.4) ser fechado
- Marcação `**NÃO INICIAR ANTES DE #N FECHADA**` no body é hard constraint — não advisory
- Reprioritização cross-milestone requer instrução explícita do operador no início da sessão

## Consequências
- **Positivo:** Cursor não pode improvisar ordem dentro de P2/v1.7.5-beta; sequenciamento é determinístico
- **Negativo:** Issues novos sem U são automaticamente U3 — criador deve ser explícito se quiser U1/U2
- **Watch:** Manter U atualizado quando pressão externa de um issue mudar (ex: parceiro confirma deadline)

## Referências
- ADR-0055 — anti-collision contract
- `.cursor/rules/execution-priority-and-pr-batching.mdc` — implementação da rule
- Issue #655 — origem desta ADR
- Issue #654 — `docs/ops/ISSUE_QUEUE_SEQUENCING_MAP.md` (Mermaid queue map)
---
