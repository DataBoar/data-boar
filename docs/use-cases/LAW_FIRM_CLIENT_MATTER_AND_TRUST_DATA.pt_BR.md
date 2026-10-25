# Storyboard de caso de uso — escritório de advocacia, processos de clientes e dados em confiança (médio porte)

**English:** [LAW_FIRM_CLIENT_MATTER_AND_TRUST_DATA.md](LAW_FIRM_CLIENT_MATTER_AND_TRUST_DATA.md)

Este é um **storyboard em documentação** para oficinas e POCs voltados a **escritórios de pequeno e médio porte** (boutique a regional). **Não** é análise jurídica de privilégio, conflitos ou sigilo profissional em qualquer ordem jurídica.

## Elenco (papéis genéricos)

- **Organização:** Sociedade de advogados ou sociedade simples com **vários processos** simultâneos (cível, trabalhista, tributário, família).
- **Titulares:** Clientes, partes contrárias, testemunhas, menores em direito de família, dirigentes em M&A.
- **Sistemas:** Exportações de gestão documental, **PST/mbox** de e-mail, pastas compartilhadas nomeadas por cliente ou processo, bases de CRM ou de gestão de escritório, PDFs de peticionamento, exportações de **faturamento**.

## Storyboard (fluxo)

1. **Abertura de caso** — o *intake* cria pastas, números de processo e cadastros de contato no DMS + e-mail + faturamento.
2. **Acúmulo de trabalho** — minutas, dossiês, planilhas com listas de partes; **convenções de nome** vazam estrutura (codinomes vs razões sociais literais).
3. **Risco entre processos** — a mesma pessoa ou entidade pode aparecer em **papéis conflitantes**; limites de **privilégio** são organizacionais (quem pode ver o quê), não algo que o scanner “saiba”.
4. **Boar fareja (escopo aprovado na governança)** — os conectores mostram padrões **tipo PII** (telefone, documentos nacionais onde o regex se aplica, endereços) e identificadores **ambíguos** (`doc_id`, `party_ref`).
5. **Planilha de agregação** — o risco de [cruzamento](../SENSITIVITY_DETECTION.pt_BR.md) pode sinalizar **combinações** de quasi-identificadores num mesmo export; continua sendo inventário **só de metadados**.
6. **Momento humano** — **Assessoria** define base legal, retenção e quem acessa cada repositório; **TI** reforça compartilhamentos e MFA. A ferramenta **não** classifica conteúdo “privilegiado” vs “não privilegiado”.

## Como o Data Boar ajuda sem decidir

- **Mapeia** onde se concentram **identificadores de partes** e **metadados de processo** (caminhos, nomes de coluna, amostras).
- **Apoia** oficinas de **minimização** e **segmentação de acesso** (quais compartilhamentos deveriam existir).
- **Não substitui** software de conflitos, plataformas de *e-discovery* ou orientação de conselho da OAB (ou equivalente).

## Oportunidade para parceiros

Legal-tech e consultorias **presenciais** anexam um **inventário de metadados delimitado** a projetos de triagem de processo ou higiene **pós-fusão** — explicitamente **sem** rotular privilégio na ferramenta.

## Alinhamento de produto (maintainers)

A demanda costuma empurrar **agregação de sensibilidade**, colunas de **PII ambíguo** e narrativas **dependentes de caminho**. Sequenciamento: [docs/README.pt_BR.md](../README.pt_BR.md) *Internal and reference*.

## Documentação relacionada

- [use-cases/README.pt_BR.md](README.pt_BR.md) ([EN](README.md)) — hub de storyboards.
- [COMPLIANCE_AND_LEGAL.pt_BR.md](../COMPLIANCE_AND_LEGAL.pt_BR.md) ([EN](../COMPLIANCE_AND_LEGAL.md))
- [SENSITIVITY_DETECTION.pt_BR.md](../SENSITIVITY_DETECTION.pt_BR.md) ([EN](../SENSITIVITY_DETECTION.md)) — identificação agregada, `PII_AMBIGUOUS`
- [MINOR_DETECTION.pt_BR.md](../MINOR_DETECTION.pt_BR.md) ([EN](../MINOR_DETECTION.md))
- [MAP.pt_BR.md](../MAP.pt_BR.md) ([EN](../MAP.md))
