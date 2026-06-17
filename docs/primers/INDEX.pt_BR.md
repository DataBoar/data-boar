# Primers — técnicos e de onboarding

**English:** [INDEX.md](INDEX.md)

Esta pasta reúne os **primers técnicos e de onboarding**: transferência de conhecimento (KT)
temática e neutra face a fornecedores, para integradores, mantenedores e novos colaboradores.
**Não** são guias de configuração do produto (esses ficam na documentação de produto) e **não**
são primers de compliance/frameworks (esses ficam no hub central — veja abaixo).

**Taxonomia (ver [ADR-0070](../adr/ADR-0070-primer-taxonomy-and-home.md), que emenda [ADR-0058](../adr/ADR-0058-primer-hub-registration-ritual.md)):**

- **Primers técnicos / de onboarding → esta pasta (`docs/primers/`).** KT, primeira leitura, modelo mental.
- **Primers de compliance / frameworks → `docs/plans/` (camada de entregável),** indexados pelo hub
  central de primers `docs/plans/PRIMERS_HUB.md` (referenciado como caminho para manter a fronteira
  de público nas docs external-tier — ver [ADR-0004](../adr/ADR-0004-external-docs-no-markdown-links-to-plans.md)).

## Índice

| Primer | O que ancora |
| ------ | ------------ |
| [AI_EVOLUTION_PRIMER.pt_BR.md](AI_EVOLUTION_PRIMER.pt_BR.md) ([EN](AI_EVOLUTION_PRIMER.md)) | História da IA (invernos, sistemas especialistas, ML/DL, LLMs) — sem hype, contexto de integrador |
| [DECISION_RECORDS_PRIMER.pt_BR.md](DECISION_RECORDS_PRIMER.pt_BR.md) ([EN](DECISION_RECORDS_PRIMER.md)) | ADR → MADR → UMADR: por que decisões são registradas e o padrão deste repositório |

## Navegação

- **Mapa de mapas:** [docs/hubs/INDEX.md](../hubs/INDEX.md)
- **Glossário:** [GLOSSARY.pt_BR.md](../GLOSSARY.pt_BR.md)
- **Primers de compliance/frameworks:** hub central em `docs/plans/PRIMERS_HUB.md`

## Ritual de atualização

1. Adicione o arquivo do primer em `docs/primers/` (EN + espelho pt-BR).
1. Adicione uma linha neste índice **e** no espelho `.pt_BR`.
1. Registre o índice local em `docs/hubs/INDEX.md` (já feito) — mantenha o caminho da linha válido.
1. Rode `./scripts/check-hubs.sh` (ou `.\scripts\check-hubs.ps1`) e `./scripts/check-all.sh`.
