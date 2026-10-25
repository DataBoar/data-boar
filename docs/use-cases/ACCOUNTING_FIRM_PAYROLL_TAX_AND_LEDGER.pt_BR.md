# Storyboard de caso de uso — escritório de contabilidade, folha, identificadores fiscais e razão (médio porte)

**English:** [ACCOUNTING_FIRM_PAYROLL_TAX_AND_LEDGER.md](ACCOUNTING_FIRM_PAYROLL_TAX_AND_LEDGER.md)

Este é um **storyboard em documentação** para oficinas e POCs em **PMEs e médias** contábeis (e periferia de auditoria). **Não** é orientação tributária nem trabalhista.

## Elenco (papéis genéricos)

- **Organização:** Escritório que atende **dezenas a centenas** de empregadores; folha e obrigações acessórias são recorrentes.
- **Titulares:** Empregados dos clientes (nomes, dados bancários quando aparecem em exportações), sócios e signatários dos clientes.
- **Sistemas:** CSV/SQL de folha, exportações de **nota fiscal** / faturamento (onde couber a jurisdição), planilhas de razão, arquivos no estilo **eSocial** (exemplos com forma brasileira), árvores de “pasta do cliente” em compartilhamento.

## Storyboard (fluxo)

1. **Ciclo de folha** — arquivos mensais caem em caminhos previsíveis; colunas em **forma de CPF/CNPJ** podem coexistir com campos de texto livre “observação”.
2. **Picos de obrigações** — mais envios ad hoc, arquivos **compactados**, cópias duplicadas com nomes “final” e “final2”.
3. **Risco de mistura entre clientes** — o mesmo notebook ou *share* do contador pode conter **várias** árvores de cliente; nome de pasta é separador fraco.
4. **Boar fareja (alvos com escopo)** — filesystem + SQL opcional mostram sequências **tipo documento nacional**, tokens “bancários” e colunas numéricas **ambíguas**.
5. **Relatório ao DPO ou sócio** — os achados priorizam **onde** se concentra metadado denso pessoal + financeiro; **recomendações** de [compliance-samples](../compliance-samples/) podem localizar a redação (amostras LGPD, GDPR etc.).
6. **Momento humano** — **Retenção** e **menor privilégio** em compartilhamentos; **assessoria** onde couber sigilo fiscal ou trabalhista. O produto **não** calcula imposto nem valida folha.

## Como o Data Boar ajuda sem decidir

- **Acelera** o “primeiro mapa” de colunas **PII + adjacência financeira** antes de um trabalho de auditoria mais profundo.
- **Destaca** exposição **entre diretórios** se a mesma varredura cobre uma raiz ampla demais.
- **Não substitui** sistemas contábeis oficiais, portais governamentais nem ferramentas certificadas de folha.

## Oportunidade para parceiros

Redes contábeis regionais e boutiques **LGPD/GDPR** produtizam uma **varredura da superfície folha + razão** como primeira semana de um engajamento maior.

## Alinhamento de produto (maintainers)

Sinal forte para colunas em **forma de documento nacional**, picos de arquivos **compactados** e avisos **entre diretórios**. Sequenciamento: [docs/README.pt_BR.md](../README.pt_BR.md) *Internal and reference*.

## Documentação relacionada

- [use-cases/README.pt_BR.md](README.pt_BR.md) ([EN](README.md))
- [COMPLIANCE_FRAMEWORKS.pt_BR.md](../COMPLIANCE_FRAMEWORKS.pt_BR.md) ([EN](../COMPLIANCE_FRAMEWORKS.md))
- [REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md](../REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md) ([EN](../REPORTS_AND_COMPLIANCE_OUTPUTS.md))
- [USAGE.pt_BR.md](../USAGE.pt_BR.md) ([EN](../USAGE.md)) — `file_scan`, arquivos compactados, `sample_limit`
