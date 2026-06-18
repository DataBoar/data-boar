# Opções de hospedagem: repositórios privados e site público

**English:** [HOSTING_AND_WEBSITE_OPTIONS.md](HOSTING_AND_WEBSITE_OPTIONS.md)

Este memorando apoia o programa de **Licenciamento, Enforcement e GTM**: onde hospedar o ferramental privado do emissor (issuer), os módulos comerciais e um site público de marketing. **Os custos são indicativos (2025–2026); confirme na página de preços de cada fornecedor.**

## Código-fonte privado (ferramental do emissor, módulos comerciais)

| Opção                                       | Controle de acesso                      | Custo indicativo                                                           | Observações                                                                                                    |
| ------                                      | --------------                          | ---------------                                                            | -----                                                                                                          |
| **Repo privado no GitHub** (pessoal ou org) | Só por convite; proteção de branch; 2FA | **Grátis** no pessoal; **Team ~US$ 4/usuário/mês** (org)                   | Serve para `tools/license-studio` copiado para um **repo privado separado**; nunca envie chaves de assinatura. |
| **GitHub Enterprise**                       | SSO, auditoria, IP allow                | **Preço Enterprise**                                                       | Quando você precisa de recursos de compliance enterprise.                                                      |
| **GitLab** (grupo privado no gitlab.com)    | Permissões por grupo                    | **Tier grátis** limitado; tiers **Premium** pagos para compliance avançado | Bom se você prefere o GitLab CI.                                                                               |
| **Forgejo / Gitea auto-hospedado**          | Você opera a ACL de rede                | **VPS ~US$ 5–25/mês** + tempo de operação                                  | Permite air-gap; você aplica os patches no servidor.                                                           |

**Recomendação:** Comece com **repositórios privados no GitHub** sob a sua organização atual; mantenha o repo do **emissor** fora da árvore pública `data-boar` e nunca faça commit de chaves ou blobs.

## Site público (pitch, contato, capturas de tela)

| Opção                              | Custo indicativo                                | Observações                                              |
| ------                             | ---------------                                 | -----                                                    |
| **Cloudflare Pages** + DNS         | **Tier grátis** costuma bastar; Pro ~US$ 20/mês | Site estático a partir do Git; CDN global.               |
| **GitHub Pages**                   | **Grátis** para repos públicos                  | Simples; vincule a um repo `www`.                        |
| **Netlify / Vercel**               | Tiers **grátis** de hobby                       | Similar ao Cloudflare Pages.                             |
| **WordPress gerenciado / Webflow** | ~US$ 10–30/mês+                                 | Menos amigável para engenharia no modelo "docs as code". |

**Recomendação:** **Cloudflare Pages** ou **GitHub Pages** para um site estático; mantenha a **verdade canônica do produto** no README/pitch do repo principal do app; espelhe um texto curto no site com um **formulário de contato** ou link `mailto:` / Calendly.

**Futuro (não agendado):** Um site **multilíngue** mais rico (pitch, casos de uso, how-tos, hub de documentação, links de release) e **idiomas extras de documentação** (por exemplo es, ja) ficam na trilha de **site / i18n de docs** do mantenedor sob `docs/plans/` (entrada via **Internal and reference** no [README.md](README.md)) — ative mais perto do estágio **pronto para produção** / GTM. **Importante:** a **profundidade técnica do site** (guias completos, cenários, releases, links de Hub/GitHub) é **intencionalmente mais densa** do que o **pitch para stakeholders** ou a **apresentação**. A **UX de locale** no site deve permanecer alinhada ao comportamento de idioma do **dashBOARd** descrito em [USAGE.md](USAGE.md) ([pt-BR](USAGE.pt_BR.md)) e [TECH_GUIDE.md](TECH_GUIDE.md) ([pt-BR](TECH_GUIDE.pt_BR.md)).

## Contato e vendas

- Coloque **um CTA claro** no site: e-mail de contato, formulário ou link de agendamento.
- **Não** embuta segredos de licenciamento nem URLs do emissor no site público.

## Relacionados

- [LICENSING_OPEN_CORE_AND_COMMERCIAL.md](LICENSING_OPEN_CORE_AND_COMMERCIAL.md) ([pt-BR](LICENSING_OPEN_CORE_AND_COMMERCIAL.pt_BR.md))
- [LICENSING_SPEC.md](LICENSING_SPEC.md) ([pt-BR](LICENSING_SPEC.pt_BR.md))
- [RELEASE_INTEGRITY.md](RELEASE_INTEGRITY.md) ([pt-BR](RELEASE_INTEGRITY.pt_BR.md))
