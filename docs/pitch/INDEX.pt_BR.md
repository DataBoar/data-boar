# Pitch e decks executivos — índice

**English:** [INDEX.md](INDEX.md)

Narrativas **de duas páginas** por público para workshops, compras e briefings de liderança. Complementam o índice em [docs/README.md](../README.md) e o mapa de papéis em [AUDIENCE_GUIDE.pt_BR.md](../AUDIENCE_GUIDE.pt_BR.md). **Não** linkam planos internos (ver [ADR 0004](../adr/ADR-0004-external-docs-no-markdown-links-to-plans.md)).

## Decks (por papel)

| Papel | Deck | Quando usar |
| ----- | ---- | ----------- |
| Conselho, diretoria, patrocinador de compra | [PITCH_STAKEHOLDER.pt_BR.md](PITCH_STAKEHOLDER.pt_BR.md) | Primeira conversa: valor, responsabilidade compartilhada, resultados 30/60/90 |
| DPO, jurídico de privacidade, compliance | [PITCH_DPO.pt_BR.md](PITCH_DPO.pt_BR.md) | Base legal, apoio a DSAR, menores, sinais multinacionais |
| DPO (incidente), litigante, sócio de escritório | [PITCH_DPO_AND_LEGAL.pt_BR.md](PITCH_DPO_AND_LEGAL.pt_BR.md) | Cadeia de custódia, ponteiros CPP arts. 158-A–F, teto do *laudo* — **não** duplica o deck operacional do DPO |
| CISO, arquiteto de segurança, GRC | [PITCH_CISO.pt_BR.md](PITCH_CISO.pt_BR.md) | Controles, **automação de evidência**, postura de integração; faixas para o CFO; KPIs por fonte/sessão |
| CDO, Data Steward, engenheiro de dados sênior | [PITCH_DATA_OFFICER.pt_BR.md](PITCH_DATA_OFFICER.pt_BR.md) | Inventário antes do GGD: armazenar/utilizar no DMBOK, maturidade de PII existente |
| CIO, gerente de TI, governança de TI | [PITCH_IT_GOVERNANCE.pt_BR.md](PITCH_IT_GOVERNANCE.pt_BR.md) | Avaliar–Dirigir–Monitorar com evidência, não só política |
| PMO, líder de programa / projeto | [PITCH_PMO.pt_BR.md](PITCH_PMO.pt_BR.md) | Cadência de entrega; risco por **fonte/sessão configurada**; heatmap de sprint/repositório é o GitHub [#677](https://github.com/DataBoar/data-boar/issues/677) |
| CFO, financeiro, patrocinador de compra | [PITCH_CFO.pt_BR.md](PITCH_CFO.pt_BR.md) | Exposição financeira; % legal + teto; responsabilidade compartilhada; sem USD de fornecedor |
| CCO, General Counsel | [PITCH_COMPLIANCE_OFFICER.pt_BR.md](PITCH_COMPLIANCE_OFFICER.pt_BR.md) | Responsabilidade, rastro de auditoria, inventário multi-regime, DD de M&A — distinto do DPO |

## Decks planejados (issues ainda abertas)

Governança de TI ([#631](https://github.com/DataBoar/data-boar/issues/631)) e CDO ([#639](https://github.com/DataBoar/data-boar/issues/639)) já têm decks na tabela acima; feche essas issues quando o AC restante estiver verificado. **DPO + jurídico / CPP** ([#688](https://github.com/DataBoar/data-boar/issues/688)) está publicado em [PITCH_DPO_AND_LEGAL.pt_BR.md](PITCH_DPO_AND_LEGAL.pt_BR.md).

## Documentação relacionada (mais profunda que um deck)

| Tema | Link |
| ---- | ---- |
| Brief de valor (uma página) | [DECISION_MAKER_VALUE_BRIEF.pt_BR.md](../DECISION_MAKER_VALUE_BRIEF.pt_BR.md) |
| Resumo jurídico / DPO | [COMPLIANCE_AND_LEGAL.pt_BR.md](../COMPLIANCE_AND_LEGAL.pt_BR.md) |
| Forense digital vs inventário (primer) | [FORENSICS_AND_EVIDENCE_PRIMER.pt_BR.md](../primers/FORENSICS_AND_EVIDENCE_PRIMER.pt_BR.md) |
| Perfis e amostras de conformidade | [COMPLIANCE_FRAMEWORKS.pt_BR.md](../COMPLIANCE_FRAMEWORKS.pt_BR.md) |
| Postura de segurança (público) | [SECURITY.pt_BR.md](../SECURITY.pt_BR.md) |
| Storyboards de casos de uso | [use-cases/USE_CASES_HUB.pt_BR.md](../use-cases/USE_CASES_HUB.pt_BR.md) |
| Navegação por preocupação | [MAP.pt_BR.md](../MAP.pt_BR.md) |

## Idioma

- Arquivos **em inglês** nesta pasta são canônicos para integradores e compradores internacionais.
- Espelhos **pt-BR** usam o sufixo `*.pt_BR.md`.

## Manutenção

Quando o README ou as amostras de conformidade mudarem, atualize as **afirmações** dos decks para alinhar com [COMPLIANCE_FRAMEWORKS.pt_BR.md](../COMPLIANCE_FRAMEWORKS.pt_BR.md) e o bloco *Para decisores* do [README](../README.md) — sem promessas jurídicas exclusivas do deck.
