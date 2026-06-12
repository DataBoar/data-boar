# FAQ de licença — Data Boar

**English:** [LICENSE_FAQ.md](LICENSE_FAQ.md)

Este FAQ explica o modelo de **licenciamento open-core** do Data Boar em linguagem simples. Ele complementa — e nunca substitui — o arquivo [`LICENSE`](../LICENSE), os [Termos de Uso](../TERMS_OF_USE.pt_BR.md) e os documentos comerciais ([SUBSCRIPTION_TIERS.pt_BR.md](SUBSCRIPTION_TIERS.pt_BR.md), [LICENSING_SPEC.md](LICENSING_SPEC.md), [LICENSING_OPEN_CORE_AND_COMMERCIAL.pt_BR.md](LICENSING_OPEN_CORE_AND_COMMERCIAL.pt_BR.md)).

> **Status do modelo (2026-06):** Hoje o repositório inteiro segue a licença do arquivo `LICENSE` (BSD 3-Clause). A divisão em **módulos comerciais source-available** descrita abaixo é o **modelo-alvo ratificado**; a divisão física (`databoar_license/`) e o texto da "Data Boar Commercial License" aguardam um passo deliberado do mantenedor com revisão jurídica. Este FAQ documenta o modelo para que compradores e contribuidores nunca sejam surpreendidos.

## 1. Qual licença o Data Boar usa?

Uma **estrutura dupla em um único repositório público e auditável** (o padrão Bitwarden / Elastic):

- **Core — BSD 3-Clause (open source):** engine de varredura, detectores, interface de plugin, CLI/API/dashboard base, material de pesquisa e tese.
- **Módulos comerciais — source-available (modelo-alvo):** funcionalidades corporativas (conectores corporativos, RBAC custom, push SIEM/RoPA, deploy packs, arquitetura partner/white-label). O código fica **visível** para todos; **uso comercial em produção exige assinatura paga**.

## 2. O que posso usar de graça?

Tudo no **core**, para qualquer propósito que a BSD 3-Clause permita — incluindo **uso interno em organização comercial** sem custo (veja [Termos de Uso §2](../TERMS_OF_USE.pt_BR.md)). Varrer sistemas que você está autorizado a varrer, montar relatórios para o seu próprio programa de conformidade, modificar e estender o código: tudo livre.

## 3. O que exige assinatura paga?

- **Entregar resultados de varredura a terceiros como serviço pago** (consultoria, auditoria, MSSP) — Pro ou superior (veja [Termos de Uso §4](../TERMS_OF_USE.pt_BR.md)).
- **Uso comercial em produção dos módulos comerciais** (conectores corporativos, RBAC custom, push SIEM/RoPA, deploy packs) — conforme a escada de camadas em [SUBSCRIPTION_TIERS.pt_BR.md](SUBSCRIPTION_TIERS.pt_BR.md).
- A assinatura também inclui **suporte padrão, assistência de configuração e customização produtizada** — não é só feature gate.

## 4. O core vai fechar algum dia?

**Não — por definição.** O core open-source (scanner, detectores, interface de plugin, superfícies base, material de pesquisa) **nunca fecha**. O modelo comercial financia o projeto justamente para o core continuar aberto e auditável.

## 5. Posso forkar o Data Boar?

Sim. O core BSD 3-Clause é forkável nos termos da licença. Duas fronteiras:

- **Marca:** nome, mascote, narrativa e experiência de produto **não** são licenciados pela licença de código — forks não podem sugerir endosso nem confundir origem (veja o inventário de propriedade intelectual da marca em [LICENSING_OPEN_CORE_AND_COMMERCIAL.pt_BR.md](LICENSING_OPEN_CORE_AND_COMMERCIAL.pt_BR.md)).
- **Módulos comerciais:** no modelo-alvo, código source-available segue visível para auditoria/dev/teste, mas uso comercial em produção continua exigindo assinatura, com fork ou sem fork.

## 6. Se o código é visível, o que impede abuso?

**Defesa em camadas, não segredo de código:**

1. **Licenças JWT assinadas com Ed25519** — enforcement fail-closed (`licensing.mode: enforced`).
2. **Binding por fingerprint de máquina** (`dbmfp`, deployment packs) — contagem de deploys aplicada na emissão.
3. **Integridade de release** — verificação de digest de build e âncora de integridade com evidência de adulteração (marcação TINTED/`-alpha`).
4. **Marca e contrato** — camada jurídica para uso comercial indevido.

Um ator determinado consegue alterar qualquer coisa localmente; o ponto é que **builds adulterados ficam evidentes**, sem suporte e comercialmente inutilizáveis em escala.

## 7. Quais são as camadas?

Community (grátis) → Pro → Pro+ → Enterprise, mais a família **Partner** customizada. **Tier = capacidade, claim = quantidade.** Escada completa, tabela de capacidades e claims de workers/deployments: [SUBSCRIPTION_TIERS.pt_BR.md](SUBSCRIPTION_TIERS.pt_BR.md).

## 8. Posso escrever e distribuir plugins?

A **interface de plugin é core (BSD-3)** — escrever plugins contra ela é livre. A **arquitetura de plugin/partner** para distribuição comercial (catálogos de parceiros, empacotamento white-label) é capacidade **Enterprise/Partner**. Plugins open-source independentes continuam sendo seus, sob a licença que você escolher.

## 9. Posso usar o Data Boar em trabalho acadêmico?

Sim — pesquisa, teses, trabalhos de curso e artigos são casos de uso do core (o próprio projeto carrega material de pesquisa). Cite o projeto, respeite os [Termos de Uso](../TERMS_OF_USE.pt_BR.md) (varra apenas o que você está autorizado a varrer) e lembre que resultados de varredura são probabilísticos — não são certificação jurídica de conformidade.

---

*Dúvidas não cobertas aqui: abra uma issue ou contate o mantenedor. Para os limites de uso aceitável (o que você nunca pode fazer com a ferramenta, em qualquer camada), leia os [Termos de Uso](../TERMS_OF_USE.pt_BR.md).*
