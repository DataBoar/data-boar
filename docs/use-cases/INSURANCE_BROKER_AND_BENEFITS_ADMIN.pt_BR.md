# Storyboard de caso de uso — corretora de seguros e administradora de benefícios (médio porte)

**English:** [INSURANCE_BROKER_AND_BENEFITS_ADMIN.md](INSURANCE_BROKER_AND_BENEFITS_ADMIN.md)

Storyboard para dados de **sinistros**, **apólice** e **beneficiários** em formatos mistos. **Não** é conselho atuarial, **não** é entrega perante regulador e **não** substitui parecer jurídico setorial (saúde suplementar, resseguro etc. variam por jurisdição).

## Elenco (papéis genéricos)

- **Organização:** Corretora ou administradora em estilo **TPA** que trata **grupos** de vidas seguradas; uso intenso de planilhas e anexos PDF.
- **Titulares:** Segurados, dependentes, prestadores (clínicas, farmácias), contatos de RH das empresas.
- **Sistemas:** Objetos de apólice no CRM, pastas de **sinistros**, planilhas de comissão, exportações REST de sistemas legados de núcleo (onde existirem extratos somente leitura).

## Storyboard (fluxo)

1. **Abertura de vigência / remessa de adesão** — CSVs em massa e anexos de e-mail caem em drives compartilhados; arquivos **duplicados** “corrigidos” se acumulam.
2. **Pico de sinistros** — campos de texto livre misturam tokens **adjacentes a diagnóstico** com endereços e documentos nacionais.
3. **Boar fareja (alvos com escopo)** — vias columnares e documento; *hints* de jurisdição opcionais permanecem **só metadados** (sem decisão médica).
4. **Alinhamento com DPO** — o relatório mostra **densidade** e **colisão** de categorias sensíveis; assessoria define retenção e narrativas de base legal.
5. **Momento humano** — **Segregação de funções** entre comercial e sinistros; o produto **não** pontua sinistro nem prêmio.

## Como o Data Boar ajuda sem decidir

- **Acelera** inventário antes de oficina estilo **DPIA** ou preparação para auditoria externa.
- **Mostra** exportações **achatadas** arriscadas (planilhas largas com dezenas de colunas sensíveis).
- **Não substitui** sistemas de administração de apólice, *underwriting* nem portais regulatórios.

## Oportunidade para parceiros

Parceiros anexam um **pacote de evidência de uma semana** (varredura com escopo + mapa de calor) a **respostas a RFP** ou conversas de renovação; depois dimensionam remediação ( cofre, acesso a nível de campo) à parte.

## Alinhamento de produto (maintainers)

Se compradores pedirem repetidamente redação **adjacente a saúde** e padrões de **beneficiário**, estenda **amostras de compliance** e *hints* de **sensibilidade** de forma **documentada e opt-in** — evite implicar completude clínica ou regulatória de seguros. Prefira [COMPLIANCE_FRAMEWORKS.pt_BR.md](../COMPLIANCE_FRAMEWORKS.pt_BR.md), [SENSITIVITY_DETECTION.pt_BR.md](../SENSITIVITY_DETECTION.pt_BR.md) e [JURISDICTION_COLLISION_HANDLING.pt_BR.md](../JURISDICTION_COLLISION_HANDLING.pt_BR.md). Sequenciamento para maintainers: [docs/README.pt_BR.md](../README.pt_BR.md) **Internal and reference**.

**Sinais fortes:** *hints* de jurisdição (opt-in), *recommendation overrides*, JSON estilo GRC para painéis executivos ([GRC_EXECUTIVE_REPORT_SCHEMA.pt_BR.md](../GRC_EXECUTIVE_REPORT_SCHEMA.pt_BR.md)).

## Documentação relacionada

- [use-cases/README.pt_BR.md](README.pt_BR.md) ([EN](README.md))
- [COMPLIANCE_AND_LEGAL.pt_BR.md](../COMPLIANCE_AND_LEGAL.pt_BR.md) ([EN](../COMPLIANCE_AND_LEGAL.md))
- [REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md](../REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md) ([EN](../REPORTS_AND_COMPLIANCE_OUTPUTS.md))
- [USAGE.pt_BR.md](../USAGE.pt_BR.md) ([EN](../USAGE.md))
