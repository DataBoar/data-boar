# Storyboard de caso de uso — MSP / consultoria de TI, multi-inquilino PME

**English:** [MSP_IT_CONSULTANCY_MULTI_TENANT_SMB.md](MSP_IT_CONSULTANCY_MULTI_TENANT_SMB.md)

Storyboard em documentação para descoberta **repetível** em **vários pequenos clientes** (compartilhamentos, árvores de backup, exportações). **Não** substitui contrato de SOC/MDR nem certificação de fornecedor.

## Elenco (papéis genéricos)

- **Organização:** MSP regional ou consultoria de TI com **playbooks padrão** por cliente (AD/M365, Google Workspace, SQL de linha de negócio, replicação em NAS).
- **Titulares:** Funcionários dos clientes e clientes desses clientes (nomes, identificadores, corpo de tickets, exportações).
- **Sistemas:** Raízes de pasta por cliente, CSV de exportação RMM, dumps **M365/Google** onde a política permitir, backups SQL, árvores de config VPN (muitas vezes **adjacentes a credenciais**).

## Storyboard (fluxo)

1. **Onboarding** — o consultor copia um pacote de “inventário de dados” para uma raiz de varredura com escopo; nomes são inconsistentes (`ClienteA`, `client_a_final`).
2. **Risco entre inquilinos** — o mesmo notebook ou ferramenta de sync tocou **vários** clientes; ZIPs aninham cópias antigas.
3. **Boar fareja (alvos com escopo)** — filesystem + amostragem SQL opcional em cópias **somente leitura**; colunas densas em PII e sequências tipo documento nacional aparecem no mapa de calor do relatório.
4. **Oficina com parceiro** — os achados priorizam **onde** apertar retenção e permissões de compartilhamento; **recomendações** localizam linguagem para DPO quando configuradas.
5. **Momento humano** — **menor privilégio** em contas de RMM e backup; **assessoria** para escopo contratual de DPA. O produto **não** declara “MSP seguro” nem substitui SIEM.

## Como o Data Boar ajuda sem decidir

- **Reutiliza** a mesma receita de varredura entre clientes (**repetibilidade** de “cinto de utilidades” para a consultoria).
- **Destaca** raízes **amplas demais** (mistura entre clientes) antes de gastar com pentest formal ou auditoria profunda.
- **Não substitui** proteção de endpoint, gestão de patches nem SLAs contratuais.

## Oportunidade para parceiros

Parceiros vendem um **primeiro mapa rápido** (“onde a nossa sopa de dados fica densa?”) como **oficina de escopo fixo** ou adendo de retainer; depois repassam remediação ao TI do cliente ou a escritórios de compliance mais pesados.

## Alinhamento de produto (maintainers)

Quando a demanda de MSP sobe, priorize capacidades que **multipliquem entre inquilinos**: caminhos documentados de **importação de escopo**, tratamento de arquivos **compactados**, limites de **amostragem SQL** e **RBAC claro** em exportações do dashboard. **Não** coloque links de páginas voltadas a compradores para `docs/plans/`; use a seção **Internal and reference** do [docs/README.pt_BR.md](../README.pt_BR.md) como entrada para maintainers.

**Sinais fortes neste vertical:** `file_scan`, conectores SQL opcionais, mapa de calor / saídas de compliance, [REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md](../REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md), [ADDING_CONNECTORS.pt_BR.md](../ADDING_CONNECTORS.pt_BR.md).

## Documentação relacionada

- [use-cases/README.pt_BR.md](README.pt_BR.md) ([EN](README.md))
- [SERVICE_TIERS_SCOPE_TEMPLATE.pt_BR.md](../ops/SERVICE_TIERS_SCOPE_TEMPLATE.pt_BR.md) ([EN](../ops/SERVICE_TIERS_SCOPE_TEMPLATE.md))
- [DECISION_MAKER_VALUE_BRIEF.pt_BR.md](../DECISION_MAKER_VALUE_BRIEF.pt_BR.md) ([EN](../DECISION_MAKER_VALUE_BRIEF.md))
- [USAGE.pt_BR.md](../USAGE.pt_BR.md) ([EN](../USAGE.md))
