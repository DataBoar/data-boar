# Storyboard de caso de uso — EdTech, exportações LMS e menores (due diligence e higiene)

**English:** [EDTECH_LMS_EXPORTS_AND_MINORS.md](EDTECH_LMS_EXPORTS_AND_MINORS.md)

Storyboard para **plataformas de ensino** que exportam **listas**, **notas** e campos de **contacto de responsáveis**. **Não** é avaliação pedagógica, **não** é moderação de chat em tempo real e **não** é “certificado” COPPA/LGPD.

## Elenco (papéis genéricos)

- **Organização:** Fornecedor EdTech ou TI de rede escolar que gere backups de **LMS** e CSVs de integração.
- **Titulares:** Estudantes (incluindo **menores**), pais/responsáveis, docentes.
- **Sistemas:** Exportações CSV/JSON do LMS, arquivos de tickets de suporte, réplicas SQL opcionais de tabelas de lista.

## Storyboard (fluxo)

1. **Exportação semestral** — planilhas largas misturam **IDs de aluno**, **telefones de responsáveis** e notas de texto livre.
2. **Integrações espalhadas** — apps de terceiros deixam cópias **duplicadas** sob árvores `/integrations/`.
3. **Boar fareja (alvos com escopo)** — *hints* de classificação em [MINOR_DETECTION.pt_BR.md](../MINOR_DETECTION.pt_BR.md) aparecem como **sinais** para triagem humana, não bloqueio automático.
4. **Revisão de investidor / rede** — o mapa de calor apoia **listas de perguntas** para subprocessadores e retenção.
5. **Momento humano** — registos de **consentimento parental** são documentos jurídicos formais; a assessoria decide se bastam.

## Como o Data Boar ajuda sem decidir

- **Apoia** pacotes de **due diligence técnica** para compradores ou redes (inventário de metadados).
- **Alinha** engenharia e DPO sobre **onde** se concentram dados de menores antes de refatorações arquitetónicas.
- **Não substitui** LMS, SIS nem sistemas legais de relatório escolar.

## Oportunidade para parceiros

Consultorias agregam uma **passagem Boar com escopo** ao desenho de **programa de privacidade** para EdTech em Series A–B ou para higiene de RFP de **rede escolar**. Para instituições EUA e fornecedores com papel de *school official*, combine a passagem com texto de `norm_tag` focado em FERPA via [compliance-sample-us_ferpa.yaml](../compliance-samples/compliance-sample-us_ferpa.yaml).

## Alinhamento de produto (maintainers)

Sobreposição forte com **alinhamento técnico a privacidade infantil nos EUA** e com temas de roadmap de **deteção de menores** — entregue comportamento **documentado e conservador** e **limites claros** em [MINOR_DETECTION.pt_BR.md](../MINOR_DETECTION.pt_BR.md) e [USAGE.pt_BR.md](../USAGE.pt_BR.md). Sequenciamento: [docs/README.pt_BR.md](../README.pt_BR.md) **Internal and reference**.

**FERPA (registros escolares EUA):** Use [compliance-sample-us_ferpa.yaml](../compliance-samples/compliance-sample-us_ferpa.yaml) para `norm_tag` **FERPA** (valores em formato SSN, IDs de aluno com contexto, rótulos de data de nascimento, vocabulário LMS/SIS, geolocalização em 4 padrões). Use em conjunto [compliance-sample-us_ftc_coppa.yaml](../compliance-samples/compliance-sample-us_ftc_coppa.yaml) quando houver recolha online para menores de 13 anos. Índice: [COMPLIANCE_FRAMEWORKS.pt_BR.md](../COMPLIANCE_FRAMEWORKS.pt_BR.md#lista-de-amostras-e-links) ([EN](../COMPLIANCE_FRAMEWORKS.md#list-of-samples-and-links)).

**Sinais fortes:** *hints* de menor, amostras de jurisdição, JSON de auditoria / JSON GRC para *data room* de aquisição ([GRC_EXECUTIVE_REPORT_SCHEMA.pt_BR.md](../GRC_EXECUTIVE_REPORT_SCHEMA.pt_BR.md)).

## Documentação relacionada

- [use-cases/README.pt_BR.md](README.pt_BR.md) ([EN](README.md))
- [MINOR_DETECTION.pt_BR.md](../MINOR_DETECTION.pt_BR.md) ([EN](../MINOR_DETECTION.md))
- [COMPLIANCE_FRAMEWORKS.pt_BR.md](../COMPLIANCE_FRAMEWORKS.pt_BR.md) ([EN](../COMPLIANCE_FRAMEWORKS.md))
- [USAGE.pt_BR.md](../USAGE.pt_BR.md) ([EN](../USAGE.md))
