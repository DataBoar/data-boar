# Storyboard de caso de uso — imobiliária e gestão condominial / locação (PME)

**English:** [REAL_ESTATE_AND_CONDOMINIUM_MANAGEMENT.md](REAL_ESTATE_AND_CONDOMINIUM_MANAGEMENT.md)

Storyboard para dados imobiliários **em volume na PME**: inquilinos, proprietários, contratos e consumos. **Não** é assessoria de registro de imóveis nem direito imobiliário.

## Elenco (papéis genéricos)

- **Organização:** Imobiliária, administradora **condominial** ou gestora de locação com **muitas unidades pequenas** e fluxo documental recorrente.
- **Titulares:** Inquilinos, proprietários, fiadores, contactos de emergência, fornecedores.
- **Sistemas:** Árvores “pasta da unidade”, PDFs de contrato, planilhas de **consumo**, exportações de WhatsApp (onde a política permitir), exportações simples de CRM.

## Storyboard (fluxo)

1. **Ciclo de locação** — scans de documento e comprovantes de renda acumulam por unidade; nomes de arquivo são **opacos**.
2. **Rotatividade** — pastas de ex-inquilino **não** arquivadas de forma consistente; duplicados permanecem.
3. **Boar fareja (alvos com escopo)** — sequências tipo documento nacional, padrões de telefone, *strings* com cara de endereço em CSVs mistos.
4. **Conselho do condomínio** — o relatório apoia discussão de **retenção** (quanto tempo guardar cópia de documento) sem conclusão jurídica.
5. **Momento humano** — registos físicos de acesso e chaves ficam **fora** do escopo do scanner; **assessoria** em direito locatício.

## Como o Data Boar ajuda sem decidir

- **Revela** PII **denso** em subtrees esquecidos (comum em compartilhamentos PME).
- **Apoia** reestruturação de **menor privilégio** em servidores de arquivos.
- **Não pontua** inquilinos nem substitui software de gestão predial.

## Oportunidade para parceiros

Consultorias regionais e **TI gerida para PME** usam o storyboard para vender higiene de compliance **sem glamour** mas frequente, onde suites GRC enterprise são pesadas demais.

## Alinhamento de produto (maintainers)

Este vertical estressa **filesystem simples** em escala, anexos **PDF** e CSV com **encoding** bagunçado — não conectores exóticos. Melhorias em **throughput**, **limites de memória** e **clareza para operador** em [USAGE.pt_BR.md](../USAGE.pt_BR.md) ajudam aqui primeiro. Sequenciamento: [docs/README.pt_BR.md](../README.pt_BR.md) **Internal and reference**.

**Sinais fortes:** `file_scan`, `sample_limit`, saídas de mapa de calor, [TOPOLOGY.pt_BR.md](../TOPOLOGY.pt_BR.md) para formato de deploy.

## Documentação relacionada

- [use-cases/README.pt_BR.md](README.pt_BR.md) ([EN](README.md))
- [COMPLIANCE_FRAMEWORKS.pt_BR.md](../COMPLIANCE_FRAMEWORKS.pt_BR.md) ([EN](../COMPLIANCE_FRAMEWORKS.md))
- [USAGE.pt_BR.md](../USAGE.pt_BR.md) ([EN](../USAGE.md))
- [TOPOLOGY.pt_BR.md](../TOPOLOGY.pt_BR.md) ([EN](../TOPOLOGY.md))
