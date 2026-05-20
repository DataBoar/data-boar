# Pitch para stakeholders — liderança e compras

**English:** [PITCH_STAKEHOLDER.md](PITCH_STAKEHOLDER.md) · **Índice:** [INDEX.pt_BR.md](INDEX.pt_BR.md)

**Público:** Conselho, diretoria, COO, patrocinadores de compra que avaliam ferramentas de governança de dados.

---

## O problema (30 segundos)

Organizações guardam dados pessoais e sensíveis em arquivos, bancos, compartilhamentos e exportações de SaaS — muitas vezes **sem inventário atual**. Incidentes, perguntas de reguladores e confiança do cliente dependem de **saber o que existe** e **priorizar correção** mais rápido do que amostragem manual.

## O que é o Data Boar

Plataforma **configurável** de descoberta e **apoio a evidências** que localiza e classifica **possível** exposição de dados pessoais e sensíveis em fontes heterogêneas e produz saídas **com tags de norma** para triagem por DPO, segurança e jurídico.

- **É:** descoberta técnica, mapeamento, contexto de tendência, evidência para workshops.
- **Não é:** assessoria jurídica, certificação nem substituto do DPO ou auditor externo.

Posicionamento completo: [DECISION_MAKER_VALUE_BRIEF.pt_BR.md](../DECISION_MAKER_VALUE_BRIEF.pt_BR.md).

## Responsabilidade compartilhada (um slide)

| Parte | Responsabilidade |
| ----- | ---------------- |
| **Sua organização** | Escopo lícito, base legal, credenciais, retenção, interpretação dos achados |
| **Data Boar** | Varreduras configuradas, achados técnicos, artefatos repetíveis de sessão |

## Resultados realistas em 30 / 60 / 90 dias

| Horizonte | Marco |
| --------- | ----- |
| **30 dias** | Primeira varredura delimitada; mapa de calor de padrões de alto risco; donos de remediação definidos |
| **60 dias** | Cadência repetível; comparação de tendência entre sessões; vocabulário alinhado entre DPO e segurança |
| **90 dias** | Pacote de evidência útil para **preparação** de auditoria (não prova de conformidade por si só) |

## Por que agora (sem hype)

- **Detecção determinística** (regex, padrões nomeados, ML supervisionado com **seus** termos) — não um chatbot que muda a resposta a cada execução. Ver [COMPLIANCE_FRAMEWORKS.pt_BR.md](../COMPLIANCE_FRAMEWORKS.pt_BR.md).
- **Dados de crianças** como trilha de primeira classe quando configurado — ver [MINOR_DETECTION.pt_BR.md](../MINOR_DETECTION.pt_BR.md).
- **Implante onde precisar:** Docker, validação em laboratório, guias de integrador — [DOCKER_SETUP.pt_BR.md](../DOCKER_SETUP.pt_BR.md), [USAGE.pt_BR.md](../USAGE.pt_BR.md).

## Checklist mínimo de compra

1. Quais sistemas e domínios entram no **escopo da fase um**?
2. Quem consome o primeiro pacote de evidência (TI, DPO, jurídico, conselho)?
3. Qual métrica define sucesso no dia 30?
4. Quais controles ficam **fora** da ferramenta (identidade, DLP, SIEM, sign-off jurídico)?

## Próximo passo

- **Profundidade DPO / jurídico:** [PITCH_DPO.pt_BR.md](PITCH_DPO.pt_BR.md)
- **Profundidade segurança:** [PITCH_CISO.pt_BR.md](PITCH_CISO.pt_BR.md)
- **Storyboards por setor:** [use-cases/USE_CASES_HUB.pt_BR.md](../use-cases/USE_CASES_HUB.pt_BR.md)
