# Storyboard de caso de uso — RPO, people ops e bureau de folha (B2B)

**English:** [RPO_PEOPLE_OPS_AND_PAYROLL_BUREAU.md](RPO_PEOPLE_OPS_AND_PAYROLL_BUREAU.md)

Storyboard para **arquivos de RH em volume** em **vários clientes empregadores**. **Não** é orientação trabalhista nem certificação de cálculo de folha.

## Elenco (papéis genéricos)

- **Organização:** RPO, RH terceirizado ou bureau de folha que atende **PME a médio porte**.
- **Titulares:** Candidatos, empregados, ex-empregados, dependentes quando aparecem em arquivos de benefícios.
- **Sistemas:** Exportações ATS, pacotes PDF de admissão, handoffs de folha em **CSV/SQL**, árvores compartilhadas de “RH do cliente”, planilhas de avaliação.

## Storyboard (fluxo)

1. **Pico de recrutamento** — currículos e notas de entrevista ficam ao lado de planilhas de **contratação final**; nomes misturam códigos de cliente e razões sociais.
2. **Handoff de folha** — arquivos mensais trazem **documentos nacionais**, tokens bancários e campos de texto livre “observações”.
3. **Mistura entre clientes** — o mesmo workspace do consultor cobre **vários** empregadores; disciplina de pastas fraca.
4. **Boar fareja (alvos com escopo)** — filesystem + SQL opcional; campos **adjacentes a menores** podem surgir em formulários (encaminhar a revisão humana conforme [MINOR_DETECTION.pt_BR.md](../MINOR_DETECTION.pt_BR.md)).
5. **Momento humano** — **Retenção** de CVs; **assessoria** para normas de *background check*. O produto **não** decide contratação.

## Como o Data Boar ajuda sem decidir

- **Gera** um **primeiro mapa** de densidade de PII antes de um trabalho formal de ROPA/DPIA.
- **Sinaliza** varreduras largas que acidentalmente cobrem **demasiados** subtrees de cliente.
- **Não substitui** ATS, HRIS nem motores certificados de folha.

## Oportunidade para parceiros

Parceiros produtizam uma **varredura fixa de “superfície de dados de RH”** como SKU de entrada; depois vendem trabalho de política e mudança de ferramenta à parte.

## Alinhamento de produto (maintainers)

A demanda aqui costuma sobrepor-se ao storyboard de **contabilidade** (IDs fiscais) mais *hints* fortes de **menores**. Priorize: heurísticas estáveis de **CPF** quando configuradas, **limites de amostra** e **RBAC claro** em exportações. Sequenciamento: [docs/README.pt_BR.md](../README.pt_BR.md) **Internal and reference**.

**Sinais fortes:** colunas com cara de folha, arquivos compactados, [MINOR_DETECTION.pt_BR.md](../MINOR_DETECTION.pt_BR.md), [COMPLIANCE_METHODOLOGY.pt_BR.md](../COMPLIANCE_METHODOLOGY.pt_BR.md).

## Documentação relacionada

- [use-cases/README.pt_BR.md](README.pt_BR.md) ([EN](README.md))
- [ACCOUNTING_FIRM_PAYROLL_TAX_AND_LEDGER.pt_BR.md](ACCOUNTING_FIRM_PAYROLL_TAX_AND_LEDGER.pt_BR.md) ([EN](ACCOUNTING_FIRM_PAYROLL_TAX_AND_LEDGER.md))
- [REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md](../REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md) ([EN](../REPORTS_AND_COMPLIANCE_OUTPUTS.md))
- [USAGE.pt_BR.md](../USAGE.pt_BR.md) ([EN](../USAGE.md))
