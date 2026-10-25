# Pitch CISO — liderança de segurança e GRC

**English:** [PITCH_CISO.md](PITCH_CISO.md) · **Índice:** [INDEX.pt_BR.md](INDEX.pt_BR.md)

**Público:** CISOs, arquitetos de segurança, líderes de GRC que integram descoberta a programas de controle.

---

## Proposta de valor para segurança

O Data Boar reduz **sprawl desconhecido** de dados pessoais antes de virar material de incidente. O **herói** para liderança de segurança é a **automação de evidência**: artefatos técnicos **repetíveis e limitados à sessão** (XLSX, YAML de manifesto opcional, JSON de auditoria, JSON executivo GRC) — não substitui SIEM, DLP, IAM nem gestão de vulnerabilidades, e não promete fechar tickets sozinho.

Postura pública de segurança: [SECURITY.pt_BR.md](../SECURITY.pt_BR.md).

## Linguagem para o CFO na mesma sala

**Não** fixe no briefing do CISO valores em dólar de **custo de incidente** de fornecedor. Use a **forma legal**: multas administrativas como **percentual do faturamento** **com teto** — **LGPD art. 52**, **GDPR art. 83**. Relatórios públicos **IBM Cost of a Data Breach** são **referência externa**: nomeie a fonte, sem USD amarrado a um ano. Responsabilidade compartilhada: evidência de descoberta **não** apaga exposição regulatória. Deck financeiro: [PITCH_CFO.pt_BR.md](PITCH_CFO.pt_BR.md).

## KPIs que o produto já entrega

| KPI | O que você mostra hoje |
| --- | ---------------------- |
| Heatmap / achados | **Por fonte e sessão configuradas** — não por time, sprint ou repositório git até o GitHub [#677](https://github.com/DataBoar/data-boar/issues/677) |
| Tendência | Sessão a sessão no **mesmo** conjunto de alvos |
| Cobertura | **Alvos configurados** no escopo — não completude de CMDB |

## Vetor emergente: descoberta em repositório / supply chain

Git e VCS semelhantes são um caminho de evidência **emergente** (dogfood do conector no GitHub [#677](https://github.com/DataBoar/data-boar/issues/677)). Trate como **conversa de controle futuro**, não heatmap por sprint/repositório já entregue.

## Controles que importam

| Tema | Como o produto apoia |
| ---- | -------------------- |
| **Menor privilégio** | Conectores usam credenciais que você aprova; escopo explícito — [ops/OPERATOR_IT_REQUIREMENTS.pt_BR.md](../ops/OPERATOR_IT_REQUIREMENTS.pt_BR.md) |
| **Integridade da evidência** | Saídas estruturadas (XLSX, YAML de manifesto opcional, JSON de auditoria) para repetibilidade |
| **Detecção determinística** | Regex + padrões + ML supervisionado em termos configurados — pilha auditável vs deriva generativa — [COMPLIANCE_FRAMEWORKS.pt_BR.md](../COMPLIANCE_FRAMEWORKS.pt_BR.md) |
| **Biometria / categorias especiais** | Narrativa de caso de uso quando habilitada — [use-cases/USE_CASE_BIOMETRIC_DATA_PROTECTION.pt_BR.md](../use-cases/USE_CASE_BIOMETRIC_DATA_PROTECTION.pt_BR.md) |

## Postura de integração

- **Deploy:** imagens Docker, amostras compose, validação em laboratório — [DOCKER_SETUP.pt_BR.md](../DOCKER_SETUP.pt_BR.md), [deploy/DEPLOY.pt_BR.md](../deploy/DEPLOY.pt_BR.md).
- **JSON executivo:** [GRC_EXECUTIVE_REPORT_SCHEMA.pt_BR.md](../GRC_EXECUTIVE_REPORT_SCHEMA.pt_BR.md) para dashboards estilo matriz de risco.
- **Limite open-core:** descoberta e relatório no repositório; conectores e hardening **enterprise** entram na conversa de compra — não assumidos na documentação pública.

## Operar com segurança

1. Comece em **não produção** ou contas somente leitura quando possível.
2. Limite amostragem e timeouts por classe de alvo — documente no manifesto.
3. Guarde credenciais em cofre/variáveis de sessão — não em repositórios rastreados.
4. Encadeie saídas com **ticketing** e donos de remediação — [use-cases/USE_CASE_SCAN_AND_REMEDIATE.pt_BR.md](../use-cases/USE_CASE_SCAN_AND_REMEDIATE.pt_BR.md).

## Perguntas para o DPO na mesma sala

- Qual **perfil de norma** é autoritativo para esta unidade?
- Quais achados exigem revisão **jurídica** antes do ticket?
- Colunas relacionadas a **menores** entram neste sprint?

## Próximo passo

- **Narrativa para conselho:** [PITCH_STAKEHOLDER.pt_BR.md](PITCH_STAKEHOLDER.pt_BR.md)
- **Narrativa de privacidade:** [PITCH_DPO.pt_BR.md](PITCH_DPO.pt_BR.md)
- **Cadência de PMO:** [PITCH_PMO.pt_BR.md](PITCH_PMO.pt_BR.md)
- **Exposição financeira:** [PITCH_CFO.pt_BR.md](PITCH_CFO.pt_BR.md)
- **Jurídico / CCO:** [PITCH_COMPLIANCE_OFFICER.pt_BR.md](PITCH_COMPLIANCE_OFFICER.pt_BR.md)
- **Referência técnica:** [COMPLIANCE_TECHNICAL_REFERENCE.pt_BR.md](../COMPLIANCE_TECHNICAL_REFERENCE.pt_BR.md)
