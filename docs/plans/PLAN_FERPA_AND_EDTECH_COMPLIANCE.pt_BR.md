# PLANO: Vertical de Conformidade FERPA e EdTech

<!-- plans-hub-summary: Suporte de inventário técnico para FERPA (registros educacionais EUA) e verticais de conformidade EdTech. Cobre detecção de padrões, criação de amostra YAML e alinhamento de casos de uso para K-12, ensino superior e plataformas EAD/LMS. -->
<!-- plans-hub-related: PLAN_YAML_PLUGIN_SYSTEM.md, PLAN_COMPLIANCE_EXPANSION_GLOBAL_JURISDICTIONS.md -->

Status: Rascunho
Date: 2026-05-14
Authors: Fabio Leitao
Priority: H1
Tags: compliance, ferpa, edtech, education, ead, minors, usa, lms, privacy, use-case
Depends on: PLAN_YAML_PLUGIN_SYSTEM.md

---

## Motivação

O mercado de **EdTech** e **EAD (Ensino a Distância)** representa uma vertical em expansão para o Data Boar.
Uma conversa comercial ativa (Brazil, 2026) torna
visível uma necessidade concreta do cliente: **onde está o PII de estudantes no nosso LMS, integrações e backups?**

**FERPA (Family Educational Rights and Privacy Act, 20 U.S.C. § 1232g)** é a lei federal norte-americana
que rege registros educacionais em instituições que recebem financiamento federal. É o principal framework
de privacidade para:

- **Distritos escolares K-12** (EUA)
- **Universidades e faculdades** (EUA)
- **Fornecedores EdTech** que processam registros educacionais em nome de instituições (atuando como "school officials")
- **Plataformas EAD / ensino a distância** que operam ou se integram a instituições americanas

Mesmo para plataformas **EAD brasileiras** sem atuação nos EUA, o conhecimento de FERPA é relevante quando:
- Um cliente institucional mantém dados de estudantes sujeitos à FERPA (ex.: parceria com HEI americana)
- A plataforma está em **expansão internacional** (América do Norte)
- Investidores ou adquirentes aplicam padrões de **due diligence** alinhados à FERPA em data rooms

---

## Escopo Técnico da FERPA

### O que a FERPA regula

| Escopo | Coberto | Fora do escopo do scanner |
|---|---|---|
| **Registros educacionais** (qualquer registro diretamente relacionado a um estudante, mantido pela instituição ou agente) | Sim — inventário | Não é autoridade de escopo jurídico |
| **Componentes de PII**: nome, endereço, data de nascimento, ID de estudante, CPF/SSN, notas, histórico, matrícula | Sim — detecção | — |
| **Informações de diretório** (nome, e-mail, curso — podem ser divulgadas publicamente, salvo opt-out) | Sim — detectadas, sinalizadas | O scanner não avalia status de opt-out |
| **Quem pode acessar** (direitos de pais/estudantes elegíveis, liberação FERPA, exceção de school-official) | **Não** — auditoria de controle de acesso está fora do escopo do scanner | — |
| **Registros de consentimento dos pais** (formulários de liberação FERPA) | Parcial — pode sinalizar campos relacionados a consentimento via ML terms | Suficiência jurídica não avaliada |
| **Enforcement pelo FPCO** (Family Policy Compliance Office, Dept. de Educação dos EUA) | N/A | — |

### O que o Data Boar oferece

1. **Inventário**: descobre onde o PII de estudantes se concentra em arquivos, bancos de dados, APIs e exportações de LMS.
2. **Evidência para due diligence**: heatmaps e GRC JSON para planejamento de programa de conformidade ou data rooms.
3. **Amostra YAML** (`compliance-sample-us_ferpa.yaml` — veja Fase 1 abaixo): regex customizado, termos ML, `recommendation_overrides` com `norm_tag: "FERPA"`.
4. **Alinhamento com detecção de menores**: `MINOR_DETECTION.md` existente e o caso de uso `EDTECH_LMS_EXPORTS_AND_MINORS` complementam os sinais FERPA.
5. **Ponte com COPPA**: FERPA e COPPA (Children's Online Privacy Protection Act) frequentemente se aplicam juntas; `compliance-sample-us_ftc_coppa.yaml` (A8) cobrirá a camada COPPA.

---

## Fases

### Fase 1 — Amostra YAML: `compliance-sample-us_ferpa.yaml`

**Entregável**: amostra de conformidade YAML seguindo a geometria estabelecida em `compliance-sample-us_va_vcdpa.yaml`.

| Componente | Conteúdo |
|---|---|
| **Regex** | `FERPA_SSN` (espelha core), `FERPA_STUDENT_ID` (heurístico: 6–10 alfanumérico com nome de campo contextual), `FERPA_DOB`, + quatro padrões de geolocalização precisos |
| **Termos ML** (~30) | `education record`, `transcript`, `gpa`, `grade report`, `enrollment status`, `student id`, `directory information`, `non-directory information`, `eligible student`, `school official`, `legitimate educational interest`, `FERPA consent`, `FERPA release`, `parent rights`, `guardian`, `minor student`, `lms`, `sis`, `roster`, `gradebook`, `course completion`, `disability accommodation`, `iep`, `504 plan`, `financial aid`, `fafsa`, `student loan` |
| **`recommendation_overrides`** | `base_legal`: "FERPA (20 U.S.C. § 1232g); FPCO — Family Policy Compliance Office, US Dept of Education"; `risk`: "Registros educacionais contendo PII de estudantes sujeitos à FERPA..."; `relevant_for`: "FERPA Compliance Officer, DPO, Jurídico, Registros de Estudantes" |

**Critérios de aceite:**
- `uv run pytest tests/test_compliance_samples.py -k ferpa` passa (≥2 itens)
- Quatro padrões de geolocalização presentes
- Pelo menos 25 termos ML

### Fase 2 — Alinhamento com caso de uso

Atualizar **`docs/use-cases/EDTECH_LMS_EXPORTS_AND_MINORS.md`** (e `.pt_BR.md`) para:
- Referenciar `compliance-sample-us_ferpa.yaml` e `norm_tag: FERPA` explicitamente
- Adicionar FERPA nas seções "oportunidade de parceria" e "frameworks de conformidade"
- Linkar para a linha FERPA em `COMPLIANCE_FRAMEWORKS.md` quando existir

### Fase 3 — Linha na tabela de COMPLIANCE_FRAMEWORKS.md + README

Adicionar linha FERPA em `docs/COMPLIANCE_FRAMEWORKS.md` e `compliance-samples/README.md`.
Atualizar espelhos pt-BR.

### Fase 4 — Alinhamento com PLANS_TODO.md e sprint

- Adicionar FERPA ao tema de sprint da vertical de conformidade
- Linkar ao caso de uso `EDTECH_LMS_EXPORTS_AND_MINORS` para visibilidade comercial

---

## Contexto: Mercado EAD brasileiro (conversa RS, 2026-05)

**Perfil**: Plataformas EAD brasileiras crescentemente processam dados de estudantes regulados pela **LGPD** (não FERPA por padrão), mas vários fatores tornam o conhecimento de FERPA um diferencial:

- **Parcerias internacionais** com HEIs americanas acreditadas expõem a plataforma a obrigações FERPA
- **Processos MEC/INEP** de credenciamento exigem cada vez mais evidências de LGPD + privacy-by-design, para as quais o sinal de inventário do Data Boar é diretamente aplicável
- **Due diligence de investidores** em EAD brasileiro com VC segue padrões internacionais; linguagem alinhada à FERPA no data room é reconhecida como sinal de maturidade

O entregável imediato para esta conversa é demonstrar que o Data Boar pode **encontrar e marcar PII de estudantes** (IDs de estudante, datas de nascimento, contatos de responsáveis, registros de notas) em exportações de LMS e artefatos de integração — e que uma **amostra YAML FERPA** permite personalizar a linguagem de recomendação para instituições em escopo.

---

## Critérios de aceite (plano geral)

- [ ] `compliance-sample-us_ferpa.yaml` commitado e testes passando
- [ ] `EDTECH_LMS_EXPORTS_AND_MINORS.md` atualizado com referência FERPA
- [ ] Linha FERPA na tabela `COMPLIANCE_FRAMEWORKS.md`
- [ ] `PLANS_TODO.md` atualizado com status da vertical de conformidade FERPA
- [ ] Espelhos pt-BR atualizados

---

## Documentos relacionados

- [`docs/use-cases/EDTECH_LMS_EXPORTS_AND_MINORS.md`](../use-cases/EDTECH_LMS_EXPORTS_AND_MINORS.md) ([pt-BR](../use-cases/EDTECH_LMS_EXPORTS_AND_MINORS.pt_BR.md))
- [`docs/MINOR_DETECTION.md`](../MINOR_DETECTION.md)
- [`docs/COMPLIANCE_FRAMEWORKS.md`](../COMPLIANCE_FRAMEWORKS.md)
- [`docs/plans/PLAN_COMPLIANCE_EXPANSION_GLOBAL_JURISDICTIONS.md`](PLAN_COMPLIANCE_EXPANSION_GLOBAL_JURISDICTIONS.md)
- [`docs/compliance-samples/compliance-sample-us_ftc_coppa.yaml`](../compliance-samples/compliance-sample-us_ftc_coppa.yaml) (A8 — pendente)
