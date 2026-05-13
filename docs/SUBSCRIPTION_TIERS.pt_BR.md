# Camadas de assinatura do Data Boar

**English:** [SUBSCRIPTION_TIERS.md](SUBSCRIPTION_TIERS.md)

O Data Boar segue o modelo **open-core**, inspirado em projetos como [Bitwarden](https://bitwarden.com/pricing/) e [NetSpot](https://www.netspotapp.com/pt/netspotpro.html):
um núcleo totalmente funcional disponível a todos, com camadas comerciais que desbloqueiam capacidades avançadas e direitos de uso comercial.

> **Nota:** Preços exatos, datas de disponibilidade e atribuição de funcionalidades por camada são definidos pela equipe de produto.
> Esta página é apenas uma visão estrutural. Para preços atuais, entre em contato com o mantenedor ou consulte o site (quando disponível).

## Visão geral das camadas

| Camada | Público-alvo | Token de licença | Diferencial principal |
|---|---|---|---|
| **Community** | DPOs internos, pesquisadores, estudantes, uso individual | Não exigido (modo open) | Funcionalidade completa do open-core; sem custo |
| **Trial / POC** | Avaliações pré-vendas, prova de conceito | Token assinado com prazo | Relatório com limite de linhas; marca d'água; converte para Pro/Partner |
| **Pro / Consultor** | Consultores independentes, MSSPs individuais | Token anual assinado | Entrega comercial para **um cliente por engajamento** |
| **Partner** | Integradores, MSPs, revendedores multi-cliente | Token anual organizacional | Entrega a múltiplos clientes; direitos de co-marca; portal de parceiros (futuro) |
| **Enterprise** | Grandes organizações, setores regulados, OEM | Acordo empresarial personalizado | Todos os recursos + SLA + white-label + SSO/LDAP |

## O que muda entre as camadas

- **Profundidade de detecção:** Heurísticas ML/DL, calibração de confiança e redução avançada de falsos negativos são funcionalidades Pro+
- **Conectores:** Cloud (O365, Google Drive, S3-class), SAP, conectores ERP empresariais são Pro/Partner+
- **Formatos de arquivo:** Suites de escritório legadas (WordPerfect, Access, OneNote), extração de strings binárias e artefatos de browser são Pro+
- **Relatórios:** RBAC no dashboard, trilha de auditoria, mapeamento de evidências de compliance (GRC-ready) são Partner+
- **Direitos comerciais:** Entregar auditorias como serviço pago a terceiros exige no mínimo uma licença Pro

## Modelo de aplicação

As camadas são aplicadas via **tokens de licença JWT assinados com Ed25519** (veja [`LICENSING_SPEC.md`](LICENSING_SPEC.md)).
A camada Community de open-core funciona sem token (`licensing.mode: open`).

## Contato

Para avaliar um Trial ou consultar preços Pro/Partner/Enterprise, abra uma issue ou entre em contato diretamente com o mantenedor.

---

*Veja também: [`LICENSING_OPEN_CORE_AND_COMMERCIAL.md`](LICENSING_OPEN_CORE_AND_COMMERCIAL.md) para a política open-core e inventário de propriedade intelectual da marca.*
