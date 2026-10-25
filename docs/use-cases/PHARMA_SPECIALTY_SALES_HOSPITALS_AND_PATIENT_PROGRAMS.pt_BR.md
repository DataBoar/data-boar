# Storyboard de caso de uso — representação farmacêutica especializada, hospitais/farmácias e programas próximos ao paciente

**English:** [PHARMA_SPECIALTY_SALES_HOSPITALS_AND_PATIENT_PROGRAMS.md](PHARMA_SPECIALTY_SALES_HOSPITALS_AND_PATIENT_PROGRAMS.md)

Este é um **storyboard em documentação** para oficinas em que um **representante ou distribuidor** comercializa medicamentos de **alta complexidade** (ex.: oncologia, doença rara) para **hospitais e farmácias**, às vezes com **programas de apoio** ou **acesso** que envolvem **paciente final**. **Não** é assessoria clínica, farmacovigilância ou regulatória setorial (obrigações no molde **FDA**, **EMA**, **ANVISA** ficam com equipes qualificadas).

## Elenco (papéis genéricos)

- **Organização:** **Força de campo** de médio porte + *inside sales* + **acesso ao mercado**; dados misturam pedidos **B2B** e planilhas **adjacentes a B2C** de programa.
- **Titulares:** Prescritores e compradores hospitalares, equipe de farmácia, **pacientes** ou acompanhantes quando o programa guarda contato ou janela de tratamento.
- **Sistemas:** CRM, exportações de **pedido/alocação**, planilhas de logística de amostra, **anotações de visita**, anexos de e-mail com papel timbrado do hospital, **workbooks** de programa (cadastro, envio ao paciente).

## Storyboard (fluxo)

1. **Pedido hospitalar** — itens de alto valor; identificadores de **instituição** misturados com nomes de prescritores na mesma linha.
2. **Rede de farmácias** — entregas recorrentes; fragmentos de **documento nacional** podem aparecer em comentários de “verificação”.
3. **Contexto oncológico ou raro** — SKUs de baixo volume; tabelas com **poucas linhas** aumentam a chance de **cada** linha ser altamente sensível quando há campos próximos ao paciente.
4. **Programa opcional ao paciente** — um *workbook* separado pode ter **telefone + endereço + janela de terapia**; equipes podem **aceitar** tratar esses dados sob política rígida — o Data Boar só vê **o que o escaneamento apontar**.
5. **Boar fareja (escopo estrito)** — os conectores sinalizam padrões **adjacentes à saúde** e **identificadores**; [detecção de menores](../MINOR_DETECTION.pt_BR.md) pode importar onde aparece contato de **responsável**.
6. **Momento humano** — **DPO + *medical affairs* + compliance** alinham base legal, contratos no estilo **operador/encarregado** ou **BA**/**DPA**, retenção e **se** campos de paciente podem entrar naquele ambiente. A ferramenta **não** classifica **PHI** sob **HIPAA** nem “categoria especial” sob **GDPR** — mostra **sinais** para governança.

## Como o Data Boar ajuda sem decidir

- **Mostra a concentração** de metadado **relacionado à saúde** e a **identificadores** no CRM, arquivos e planilhas ad hoc.
- **Apoia** decisões de **estreitar** raízes de varredura, **apagar** cópias de programa de compartilhamentos genéricos ou **mover** evidência para repositórios governados.
- **Não substitui** sistemas de **PV**, dados de **Hub**, **RIM** validado nem registros de comitê de ética.

## Oportunidade para parceiros

Consultorias de *life sciences* usam este storyboard para preparação de **data room** de força de campo e oficinas de **market access** onde CRM + *workbooks* de programa são a “sopa de dados” real.

## Alinhamento de produto (maintainers)

Estresse a sensibilidade **adjacente à saúde**, narrativas de tabelas com ***n* pequeno** e disciplina de **amostragem SQL**. Sequenciamento: [docs/README.pt_BR.md](../README.pt_BR.md) *Internal and reference*.

## Documentação relacionada

- [use-cases/README.pt_BR.md](README.pt_BR.md) ([EN](README.md))
- [COMPLIANCE_AND_LEGAL.pt_BR.md](../COMPLIANCE_AND_LEGAL.pt_BR.md) ([EN](../COMPLIANCE_AND_LEGAL.md)) — posicionamento adjacente à saúde
- [SENSITIVITY_DETECTION.pt_BR.md](../SENSITIVITY_DETECTION.pt_BR.md) ([EN](../SENSITIVITY_DETECTION.md)) — risco agregado, menores
- [GLOSSARY.pt_BR.md](../GLOSSARY.pt_BR.md) ([EN](../GLOSSARY.md)) — **VBA** (acordo baseado em valor; **não** é VBA do Office)
- [USAGE.pt_BR.md](../USAGE.pt_BR.md) ([EN](../USAGE.md)) — tetos de amostragem em banco e env opcional **`DATA_BOAR_SQL_SAMPLE_LIMIT`**
- [TOPOLOGY.pt_BR.md](../TOPOLOGY.pt_BR.md) ([EN](../TOPOLOGY.md)) — `connectors/sql_sampling.py` (forma do SQL de amostra)
