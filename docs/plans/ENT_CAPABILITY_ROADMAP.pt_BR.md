# Roadmap de capacidades da assinatura Enterprise (ENT)

<!-- plans-hub-summary: Backlog canônico ENT (relatórios por persona, multi-entidade, maturidade, evidência de auditoria, PSI/DGA, ITSM/IAM); só doc até ADR por capacidade -->

**English:** [ENT_CAPABILITY_ROADMAP.md](ENT_CAPABILITY_ROADMAP.md)

**Status:** Roadmap (somente documentação — sem implementação de produto sem ADR aprovado pelo operador)
**Data:** 2026-08-17
**Prioridade:** H1 / U1 (framework de comercialização)
**Issue:** [#643](https://github.com/DataBoar/data-boar/issues/643)

**Relacionados:** [ADR-0035](../adr/ADR-0035-readme-stakeholder-pitch-vs-deck-vocabulary.md) · [PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md](PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md) · [SPRINTS_AND_MILESTONES.md](SPRINTS_AND_MILESTONES.md) §4.1 / **M-ACCESS** · [ACTIONABLE_GOVERNANCE_AND_TRUST.md](../ops/inspirations/ACTIONABLE_GOVERNANCE_AND_TRUST.md) · entrada no hub [PLAN_ENT_CAPABILITY_ROADMAP.md](PLAN_ENT_CAPABILITY_ROADMAP.md)

---

## 1. Propósito

Este arquivo é o backlog **canônico** das capacidades da **assinatura Enterprise (ENT)**: funcionalidades que transformam a utilidade de scan em **processo organizacional verificado** para boards, DPOs, auditores e comitês de segurança.

Ele **não** substitui:

| Doc | Responsabilidade |
| --- | ---------------- |
| [PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md](PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md) | Matriz de tiers, narrativa JWT `dbtier`, o que entra em Community/Trial/Pro/Partner/Enterprise |
| [SPRINTS_AND_MILESTONES.md](SPRINTS_AND_MILESTONES.md) §4.1 | Entitlement comercial, ativação, acesso dashBOARd/API, **M-ACCESS** |
| [LICENSING_SPEC.md](../LICENSING_SPEC.md) | Claims e fases de enforcement em runtime |

Mantenha esses docs com ponteiros para este roadmap nas *capacidades* ENT; mantenha matrizes de feature e trabalho de SKU/JWT lá.

---

## 2. Open-core vs ENT

| Camada | Entrega | Audiência |
| ------ | ------- | --------- |
| **Open-core** | **Utilidade** técnica: motor de scan, `norm_tags`, findings, manifest de scan, relatório GRC básico, CLI + API, scans de org única, dashBOARd técnico | Operadores, engenheiros, pesquisadores |
| **Assinatura ENT** | Artefatos e fluxos de **processo organizacional** que boards, DPOs, auditores e comitês precisam para governança, conformidade e diligência | Orgs reguladas com obrigações reais (LGPD / GDPR / DGA / ISO 27001 / auditoria externa) |

**Quem paga o ENT:** organizações com deveres legais, regulatórios ou de governança no board — não hobbyistas individuais.

**Enquadramento de produto:** o open-core torna tangível a entrega técnica; o ENT torna tangível a **entrega de governança e conformidade** para quem carrega risco e atestação.

---

## 3. Fronteira — o que *não* é ENT (permanece open-core)

Estes itens permanecem Community / open-core (sujeitos à matriz de tiers no plano de product tiers):

- Motor de scan core
- `norm_tags` + `plugin_schema.yaml`
- Manifest de scan (baseline)
- Relatório GRC básico
- CLI + API
- Scans de organização única
- Visões técnicas do dashBOARd

---

## 4. Backlog de capacidades (somente roadmap)

Checkboxes registram **intenção de produto**, não código entregue. Não implemente um item sem **ADR aprovado pelo operador** para aquela capacidade (ou sub-issue explícita aberta pelo operador).

### P0 — Destravar vendas

- [ ] **Geração de relatório por persona** — Mesmo scan, visões diferentes (DPO, CISO, CDO, board). O objeto de valor muda com a audiência. Alinha-se a Evaluate–Direct–Monitor (estilo COBIT) e à tangibilização de serviço (estilo ITIL) para stakeholders não técnicos.
- [ ] **Multi-entidade / subsidiárias** — Um tenant central gerencia scans de N BUs ou empresas do grupo. Alinha-se a pirâmides de governança corporativa → TI.

### P1 — Retenção e expansão

- [ ] **Scorer de maturidade DMBOK** — Pontua maturidade de segurança de dados (e áreas DMBOK relacionadas) a partir da evidência de scan; níveis 1–5; tendência no tempo. Superfície relacionada: [PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md](completed/PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md) (POC de questionário — complementar, não idêntico). Narrativa pitch/CDO: [#639](https://github.com/DataBoar/data-boar/issues/639); trilha primer DMBOK: [#637](https://github.com/DataBoar/data-boar/issues/637).
- [ ] **Relatório para comitê de segurança** — Artefato de pauta: resumo executivo, exposições/incidentes relevantes, decisões necessárias para reunião periódica.
- [ ] **Cadeia de evidência auditável** — Manifest assinado, cadeia de custódia, hashes de integridade para uso jurídico e auditoria externa. Diferencia de scanners OSS típicos. Complementa o vocabulário de trust/audit-trail em [PLAN_GRC_INSPIRED_ENTERPRISE_TRUST_ACCELERATORS.md](PLAN_GRC_INSPIRED_ENTERPRISE_TRUST_ACCELERATORS.md); não substitui o `--export-audit-trail` open-core até haver gate.

### P2 — Novos segmentos / ICP

- [ ] **Builder de PSI** — Esboço de política de segurança da informação a partir dos achados (quais classes de dados aparecem onde → checklist de cobertura). Não é aconselhamento jurídico; auxílio de template para clientes.
- [ ] **Avaliação de compartilhamento DGA** — Checagem pré-compartilhamento no espírito do Data Governance Act da UE (Reg. 2022/868): pode compartilhar / precisa anonimizar / não pode compartilhar.
- [ ] **Validador de qualidade de anonimização** — Detecta PII residual ou combinações reidentificáveis em datasets alegadamente anonimizados (ex.: falhas estilo k-anonimato).

### P3 — Integração de ecossistema

- [ ] **Conector ITSM** (ServiceNow / Jira) — Exposição de PII → ticket de incidente com prioridade baseada em risco (padrão de gestão de incidentes ITIL).
- [ ] **Recomendador IAM** — Sugere políticas RBAC / least-privilege a partir dos achados (quais roles não deveriam ver quais tabelas/campos).

---

## 5. Sequenciamento vs enforcement já planejado

Capacidades ENT **não** são o mesmo que gates JWT `dbtier` / `dbfeatures` já listados em [PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md](PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md) (fases 1–5) nem as fatias de entitlement em [SPRINTS_AND_MILESTONES.md](SPRINTS_AND_MILESTONES.md) §4.1.

| Pré-requisito | Por quê |
| ------------- | ------- |
| Plano de tiers **fases 1–2** (`dbtier` + `LicenseGuard.check_feature`) | Gatear packs ENT pagos sem vazamento soft-fail |
| **M-ACCESS** (caminho de identidade documentado + smoke) | Não prometer ENT multi-usuário em host alcançável sem auth |
| Trilha open-core / auditabilidade Pro ([#811](https://github.com/DataBoar/data-boar/issues/811)) | Onboarding de parceiro e modelo de auditoria least-privilege do Pro — só cross-ref; decisões naquela issue/ADR |

Entregue primeiro trust e acesso open-core; promova capacidades ENT só quando a história comercial e de acesso for honesta.

---

## 6. Gate de implementação (rígido)

1. **Sem código de produto** para itens da §4 sem **ADR aprovado pelo operador** para aquela capacidade.
2. **Sub-issues** por capacidade somente quando o operador pedir.
3. **Preço, contratos e linguagem legal de SKU** ficam com assessoria / Priority band A (A7) — fora do escopo deste arquivo além de ponteiros para [LICENSING_OPEN_CORE_AND_COMMERCIAL.md](../LICENSING_OPEN_CORE_AND_COMMERCIAL.md).
4. Exemplos nomeados de parceiro e valores comerciais só em **`docs/private/`** (gitignored) — nunca neste roadmap público.

---

## 7. Índice relacionado

| Tipo | Link |
| ---- | ---- |
| Issue de tracking | [#643](https://github.com/DataBoar/data-boar/issues/643) |
| ADR de pitch / vocabulário | [ADR-0035](../adr/ADR-0035-readme-stakeholder-pitch-vs-deck-vocabulary.md) |
| Fronteiras de tier | [PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md](PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md) · [ADR-0027](../adr/ADR-0027-commercial-tier-boundaries-licensing-docs-and-future-jwt-claims.md) |
| Acesso / superfícies de assinatura | [SPRINTS_AND_MILESTONES.md](SPRINTS_AND_MILESTONES.md) §4.1 · **M-ACCESS** |
| Aceleradores de trust | [PLAN_GRC_INSPIRED_ENTERPRISE_TRUST_ACCELERATORS.md](PLAN_GRC_INSPIRED_ENTERPRISE_TRUST_ACCELERATORS.md) |
| POC de questionário de maturidade | [PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md](completed/PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md) |
| Inspiração de governança | [ACTIONABLE_GOVERNANCE_AND_TRUST.md](../ops/inspirations/ACTIONABLE_GOVERNANCE_AND_TRUST.md) |
| Governança open-core / plugin (próximo P1) | [#811](https://github.com/DataBoar/data-boar/issues/811) |
| Relacionados DMBOK / CDO | [#637](https://github.com/DataBoar/data-boar/issues/637) · [#639](https://github.com/DataBoar/data-boar/issues/639) |

---

## Changelog

| Data | Mudança |
| ---- | ------- |
| 2026-08-17 | Consolidação inicial a partir de [#643](https://github.com/DataBoar/data-boar/issues/643) (foco em produto; sem enquadramento pessoal/acadêmico). |
