# O porquê — evidência em vez de teatro

**English:** [THE_WHY.md](THE_WHY.md)

Esta página fixa só a **filosofia pública do produto**: por que o Data Boar prioriza **evidência técnica**, relatório **só com metadados** e **limites honestos**. **Não** substitui [COMPLIANCE_AND_LEGAL.pt_BR.md](../COMPLIANCE_AND_LEGAL.pt_BR.md), o [ADR 0025](../adr/ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md) nem a assessoria.

## Em que otimizamos

- **Inventário defensável:** conectores, amostragem, achados e relatórios que ajudam **CISO**, **DPO** e **operadores** a ver onde estão dados pessoais e sensíveis — não um deck que finge cobertura.
- **Verdade operacional:** o mesmo rigor de cultura **SRE** (timeouts, rate limit, sinais de saúde, higiene de logs) aplicado ao trabalho de **descoberta** — varreduras delimitadas, falhas claras, logs redigidos quando erros poderiam vazar contexto ([ADR 0036](../adr/ADR-0036-exception-and-log-pii-redaction-pipeline.md)).
- **Complexidade de campo:** ambientes de alta fricção — **logística**, fluxos **adjacentes à alfândega**, tripulação multinacional — em que um mesmo conjunto carrega **vários** sinais jurisdicionais. O produto **mostra a tensão** para humanos decidirem ([JURISDICTION_COLLISION_HANDLING.pt_BR.md](../JURISDICTION_COLLISION_HANDLING.pt_BR.md), [ADR 0038](../adr/ADR-0038-jurisdictional-ambiguity-alert-dont-decide.md)); **não** escolhe lei aplicável.

## O que nos recusamos a ser

- **Substituto de compliance de papel:** não troca **assessoria**, dono de **RoPA/RIPD** nem decisão de **retenção**.
- **Caixa-pretita** que inventa resultado jurídico: *jurisdiction hints* são **heurísticas**; sensibilidade é classificação **técnica**, não veredito legal.

## Onde está o storyboard

Fluxo **genérico** estilo porto / tripulação multinacional (oficinas, POC): [use-cases/PORT_LOGISTICS_MULTINATIONAL_CREW.pt_BR.md](../use-cases/PORT_LOGISTICS_MULTINATIONAL_CREW.pt_BR.md) ([EN](../use-cases/PORT_LOGISTICS_MULTINATIONAL_CREW.md)).

## Relacionados

- [ADR 0039](../adr/ADR-0039-retention-evidence-posture-bonded-customs-adjacent-contexts.md) — limite de retenção/evidência em contextos adjacentes à alfândega (sem tags automáticas de base legal).
- [MAP.pt_BR.md](../MAP.pt_BR.md) — índice por preocupação ([EN](../MAP.md))
- [README.pt_BR.md](../../README.pt_BR.md) — **The Architect's Vault** (ADRs, briefs, placeholders de narrativa)
