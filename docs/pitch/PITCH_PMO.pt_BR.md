# Pitch PMO — entrega, risco e cadência de evidência

**English:** [PITCH_PMO.md](PITCH_PMO.md) · **Índice:** [INDEX.pt_BR.md](INDEX.pt_BR.md)

**Público:** líderes de PMO, gerentes de programa/projeto e de entrega que precisam de evidência de varredura sem operar o detector.

---

## Por que esta conversa não é o deck do CISO

O PMO pergunta **quando**, **quem está bloqueado** e **qual evidência existe neste incremento** — não substituição de SIEM nem catálogo de controles. O Data Boar produz artefatos de descoberta **limitados à sessão** para o programa mostrar progresso contra **alvos configurados**, sem prometer heatmap por sprint ou repositório.

## O que o PMO costuma perguntar

| Pergunta | Resposta honesta hoje |
| -------- | --------------------- |
| Dá para ver risco por **fonte** nesta semana? | Sim: achados e heatmaps **por fonte e sessão configuradas** — [REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md](../REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md) |
| Dá para ver risco por **time / sprint / repositório git**? | **Ainda não.** Essa granularidade está no GitHub [#677](https://github.com/DataBoar/data-boar/issues/677). Não briefar o conselho como se já tivesse sido entregue. |
| Dá para ver tendência? | Sim: **tendência** sessão a sessão no mesmo conjunto de alvos |
| Varredura verde significa incremento “pronto”? | **Não.** A varredura é evidência técnica para triagem, não substitui revisão de código, UAT nem parecer jurídico |

## Cadência ágil (como usar a ferramenta)

1. **Escopo do incremento:** liste sistemas no YAML de `targets` deste sprint — cobertura é **escopo configurado**, não o CMDB.
2. **Rode uma sessão limitada** (timeouts, amostragem, não produção primeiro).
3. **Exporte** XLSX / heatmap / YAML de manifesto opcional para a daily ou revisão de risco.
4. **Abra tickets** para os donos — [use-cases/USE_CASE_SCAN_AND_REMEDIATE.pt_BR.md](../use-cases/USE_CASE_SCAN_AND_REMEDIATE.pt_BR.md).
5. **Revarra** os mesmos alvos para mostrar tendência, não um universo novo de ativos.

JSON executivo para GRC/BI: [GRC_EXECUTIVE_REPORT_SCHEMA.pt_BR.md](../GRC_EXECUTIVE_REPORT_SCHEMA.pt_BR.md).

## O que isto não é

- Não substitui **revisão de código** nem SAST.
- Não é relatório de **culpa** — achados são coordenadas e categorias, não nomes de culpados.
- Não é motor de **risco de entrega** (cronograma, orçamento, RAID ficam na ferramenta do PMO).
- Não é **completude** de ativos da organização — só o que você configurou.

## Responsabilidade compartilhada

O PMO é dono do escopo do incremento, das partes interessadas e da aceitação. O Data Boar é dono das leituras técnicas configuradas e das saídas estruturadas. Brief de liderança: [DECISION_MAKER_VALUE_BRIEF.pt_BR.md](../DECISION_MAKER_VALUE_BRIEF.pt_BR.md).

## Próximo passo

- **Conselho:** [PITCH_STAKEHOLDER.pt_BR.md](PITCH_STAKEHOLDER.pt_BR.md)
- **Controles de segurança:** [PITCH_CISO.pt_BR.md](PITCH_CISO.pt_BR.md)
- **Exposição financeira:** [PITCH_CFO.pt_BR.md](PITCH_CFO.pt_BR.md)
