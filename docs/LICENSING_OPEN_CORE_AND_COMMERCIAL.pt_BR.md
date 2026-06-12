# Open core e licenciamento comercial (política em rascunho)

**English:** [LICENSING_OPEN_CORE_AND_COMMERCIAL.md](LICENSING_OPEN_CORE_AND_COMMERCIAL.md)

Este documento descreve o **limite pretendido** do produto Data Boar: uma distribuição **open core** (confiança da comunidade, auditabilidade) mais capacidades **comerciais** com enforcement por licença criptográfica. É um **rascunho** para operadores e contribuidores; **termos finais exigem revisão jurídica** antes de alterar o `LICENSE` na raiz ou publicar builds pagos.

## Modelo (híbrido estilo Bitwarden)

| Camada | Intenção | Postura de licença típica |
| ----- | ----- | ----- |
| **Open core** | Varredura essencial, relatórios, dashboard, linha de base de conectores; compilável a partir de fontes públicas sem token pago | Permanece sob licença OSI permissiva ou copyleft forte (hoje: **BSD 3-Clause** em `LICENSE`; opção futura: **AGPL-3.0** no servidor se quiser “self-host deve compartilhar mudanças”) |
| **Comercial / módulos source-available** | Recursos enterprise, políticas avançadas, conectores premium ou comportamento controlado de trial/POC | Termos **source-available**: o código pode ser visível para auditoria, mas **uso em produção exige assinatura válida** e **token assinado** (veja [LICENSING_SPEC.md](LICENSING_SPEC.md)) |

Espelha o padrão de mercado de projetos como **Bitwarden**: núcleo sob termos estilo GPL/AGPL, com diretórios ou pacotes separados sob licença **comercial / source-available** para recursos pagos. Veja o `LICENSE_FAQ.md` do servidor Bitwarden e o layout `bitwarden_license/` para a ideia (não copie o texto da licença sem assessoria).

## O que permanece no repositório público

- Motor de varredura, conectores (linha de base), geração de relatórios, API/dashboard (dashBOARd), testes, documentação para **operadores** (USAGE, SECURITY, guias de deploy).
- **Somente verificação em tempo de execução**: **chave pública Ed25519** de verificação (não a chave de assinatura), formato de lista de revogação e o comportamento de `core/licensing/` quando o enforcement de licenciamento estiver ativo.

**Nota:** Licenciamento **open source** do **código** sob BSD (ou AGPL futuro) **não** renuncia a **marca**, **trade dress** ou **boa vontade comercial** no **nome, mascote, narrativa e experiência do produto** abaixo. Forks podem redistribuir código conforme os termos da licença, mas não devem implicar endosso ou confundir origem, salvo permissão. A assessoria deve alinhar `LICENSE`, `NOTICE`, política de marca e SKUs de **parceiro / white-label** (veja [Produtos futuros: parceiros vs clientes finais](#produtos-futuros-parceiros-vs-clientes-finais-lembrete-de-planejamento)) a este inventário.

## Marca, narrativa e IP da experiência (inventário para assessoria e política comercial)

Ao endurecer **proteção de IP**, ofertas **comerciais** ou programas de **parceiros**, trate o seguinte como **checklist** explícito junto com patentes/segredos comerciais (se houver) e licenciamento criptográfico. **Não é assessoria jurídica**; use para briefing com assessoria e para definir o que contratos e enforcement devem cobrir.

| Camada | O que proteger (exemplos) | Onde está documentado / incorporado |
| ----- | ----- | ----- |
| **Nome e submarcas** | **Data Boar** como nome do produto; **dashBOARd** como submarca do dashboard web; ortografia e capitalização consistentes na UI, README, metadados Docker | README na raiz, `core/about.py`, API/templates, [MASCOT.md](MASCOT.md) |
| **Mascote e identidade visual** | Arte do javali (SVG/PNG), favicon, uso no dashboard/About/help, relatório **Excel** (aba Report info), marca d’água do **heatmap**; variantes cor vs P&B | [MASCOT.md](MASCOT.md), `api/static/mascot/`, `NOTICE`, `report/generator.py` |
| **“Sopa de dados” e metáfora de escopo** | **Escopo heterogêneo de auditoria** (bancos, filesystems, APIs, shares, arquivos, formatos futuros) descrito como **sopa de dados** ou narrativa equivalente; **taxonomia** de conectores e posicionamento “uma auditoria em várias fontes” | [USAGE.md](USAGE.md), [TECH_GUIDE.md](TECH_GUIDE.md), [TOPOLOGY.md](TOPOLOGY.md), docs de deploy, [COMPLIANCE_TECHNICAL_REFERENCE.md](COMPLIANCE_TECHNICAL_REFERENCE.md) |
| **Mito, tom e metáforas** | Linguagem **javali / trilha / auditoria**; enquadramento de conformidade (LGPD/GDPR/CCPA e amostras); **heatmap de risco** como metáfora visual; “sensibilidade”, “achados”, “quasi-identificadores” como voz do produto | README, docs COMPLIANCE, texto do relatório, copy do dashboard |
| **Aparência geral (próxima de trade dress)** | **Layout** do dashboard (cards, status, gráfico), rótulos de navegação, padrões claro/escuro; **estrutura** das planilhas Excel, convenções de colunas, blocos de atribuição; títulos **OpenAPI** da API onde houver marca | `api/templates/`, CSS estático, código de layout do relatório |
| **Operação e “como funciona”** | **CLI one-shot** vs **API + dashboard** vs comando padrão **Docker**; ciclo de vida de sessão/relatório; estados de licenciamento em About/health — a **história documentada do operador** é **expressão protegível por direitos autorais**; know-how **secreto** **não** publicado pode ser tema separado de segredo industrial | [USAGE.md](USAGE.md), [TECH_GUIDE.md](TECH_GUIDE.md), [deploy/DEPLOY.md](deploy/DEPLOY.md), [LICENSING_SPEC.md](LICENSING_SPEC.md) |
| **Recursos complementares e apps adjacentes** | Nomenclatura no **Docker Hub** (`fabioleitao/data_boar`, tags); futuro **site** público; ferramenta **privada** de emissão de licença (`tools/license-studio` — repositório separado); outros repositórios citados no portfólio (ex.: demos de infra) — esclarecer o que é **família de produto** vs **pessoal** | [DOCKER_SETUP.md](DOCKER_SETUP.md), [HOSTING_AND_WEBSITE_OPTIONS.md](HOSTING_AND_WEBSITE_OPTIONS.md); ponteiros do mantenedor na seção *Internal and reference* do [README.md](README.md); runbooks privados |

**Ângulo parceiro / enterprise:** Se parceiros entregam auditorias para **seus** clientes, os contratos devem dizer se podem **co-marca**, devem **manter** atribuição Data Boar ou **white-label** (e em quais SKUs). Isso interage com marca e **mascote** nas exportações de relatórios.

**Passos práticos (com assessoria):** (1) Busca/registro de **marca nominativa** e opcionalmente **logo/mascote** em jurisdições e classes relevantes (ex.: software, SaaS). (2) Acrescentar ou reforçar parágrafo de **uso de marca** em `NOTICE` ou `TRADEMARK.md` se necessário. (3) Garantir que a licença **comercial / source-available** reserve **cláusulas de marca** (sem sugerir filiação). (4) Alinhar **integridade de release** e **claims JWT** de licença se um dia codificar **tier** ou **programa** (veja extensões futuras em [LICENSING_SPEC.md](LICENSING_SPEC.md)).

Para noções básicas de copyright vs marca e ponteiros de registro, veja [COPYRIGHT_AND_TRADEMARK.md](COPYRIGHT_AND_TRADEMARK.md) ([pt-BR](COPYRIGHT_AND_TRADEMARK.pt_BR.md)).

## O que nunca pode estar no repositório público

- **Chaves privadas de assinatura**, segredos “blob” do operador ou qualquer material que permita forjar JWTs de licença válidos.
- O código-fonte ou binários da **ferramenta de emissão** de licença destinados só à sua equipe (manter em **repositório privado separado**; veja `tools/license-studio/README.md`).

## Comportamento padrão (desenvolvimento e CI)

Sem **enforcement** (padrão), a aplicação roda em modo **open**: não é obrigatório arquivo de licença e todos os recursos se comportam como hoje. Isso preserva forks, testes e uso acadêmico até você habilitar enforcement explicitamente em config ou ambiente (veja [LICENSING_SPEC.md](LICENSING_SPEC.md)).

## Próximos passos (jurídico)

1. Escolher **BSD 3-Clause vs AGPL-3.0** para o open core (AGPL aumenta copyleft no uso em rede; BSD maximiza adoção — troca com assessoria).
1. Redigir licença **comercial / source-available** para módulos pagos (ou adaptar modelo auditado).
1. Acrescentar arquivos **NOTICE** / **THIRD_PARTY** se redistribuir criptografia ou outras pilhas sob licenças variadas.

## Assinatura comercial: Pro vs Enterprise (modelo de trabalho)

**Status:** Modelo de trabalho para **produto e conversas comerciais** — **não** é redação contratual final. **Precificação ainda não está definida.** Nomes de tier (`Pro`, `Enterprise`, `Partner`) podem mudar; **claims JWT e gates em tempo de execução** em [LICENSING_SPEC.md](LICENSING_SPEC.md) ainda não estão totalmente implementados. A **matriz recurso a recurso** fica no plano de mantenedor `docs/plans/PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md` (caminho em texto — planejamento interno, não é alvo de link para compradores).

**Por que tiers pagos:** O **open core** já é capaz (motor de varredura, dashboard, conectores de base, amostras de conformidade, notas heurísticas de jurisdição opcionais, e mais). **Assinatura** serve para **empacotamento enterprise**: clareza de entitlement, limites de suporte e responsabilidade, pacotes de conectores e detecção premium conforme forem entregues, e recursos de governança que grandes compradores esperam. A divisão abaixo é **o que reservar para SKUs pagos** vs o que permanece como **confiança e adoção** na árvore pública.

### Open core (sem assinatura obrigatória)

- **Intenção:** **Self-host** com recursos completos para transparência, pesquisa e adoção; mesmo código que contribuidores e CI exercitam.
- **Limite:** Alinhado ao `LICENSE` **público** (hoje BSD 3-Clause). Enforcement comercial **desligado** (`licensing.mode: open`), salvo se o operador optar pelo contrário.

### Escala e concorrência (modelo de trabalho — workers, targets, ingredientes premium)

**Status:** Tetos de workers **ratificados (2026-06-11, #853) e implementados no modo `enforced`** (#551 — claim `dbmax_workers` + padrões por camada em `core/licensing/guard.py`). **Workers ≈ ALVOS simultâneos** varridos em paralelo — essa é a leitura para o comprador. Tetos de contagem de alvos (`dbmax_targets`) seguem como **alvo de política**; feche com produto + assessoria.

| Tier | Workers (≈ alvos varridos simultaneamente) | Targets (alvos configurados por sessão ou envelope de deploy) | Ingredientes “premium” na sopa de dados |
| ---- | -------------------------------------------- | -------------------------------------------------------------- | ---------------------------------------- |
| **Open core / Community** | **2** (ratificado) | **Teto generoso mas limitado** (teto exato TBD — ex.: grande o bastante para pilotos reais, não inventário ilimitado em frota) | Conjunto **público** de hoje; quando houver recursos gated, open core fica no pacote **baseline**, salvo experimentos comunitários explícitos. |
| **Pro** | **4** (ratificado) | **Teto maior** que o open | Conectores/heurísticas **premium curados** — **nem** todo ingrediente caro (ver Enterprise). |
| **Pro+** | **8** (ratificado — claim-driven: tokens emitidos carregam `dbmax_workers: 8`) | **Teto maior** que o Pro | Pro **mais** roles RBAC custom, push SARIF/SIEM, export RoPA, deploy pack — veja [SUBSCRIPTION_TIERS.md](SUBSCRIPTION_TIERS.md). |
| **Enterprise** | **Ilimitado** no entitlement (vazão real = **CPU/RAM/IO** do host e tuning do operador) | **Ilimitado** no entitlement (mesmos limites práticos) | **Entitlement mais amplo:** ingredientes **caros, arriscados ou de nicho** podem ser **só Enterprise** (ex.: certas sondas orientadas a rede, tier completo de conectores enterprise, caminhos de relatório white-label) — **lista exata TBD**; alinhar a `docs/plans/PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md`. |
| **Partner** | Em geral envelope **tipo Pro** ou **tipo Enterprise** por contrato | Uso **multi-cliente** pode ter **outros** tetos — não é o mesmo problema que open core single-tenant | Regras de co-marca / programa no contrato, não só contagem de workers. |

**Por que limitar o open core:** Mantém o tier **gratuito** honesto (não um produto batch ilimitado de graça), reduz **abuso** como carregador paralelo sem custo e preserva **upsell** claro para quem precisa de escala em frota. Forks sob a licença podem rodar sem teto até adotarem **seus** builds com enforcement — alinhar com assessoria se endurecer **AGPL** ou **marca** depois.

**Implementação:** `dbmax_workers` está **implementado** (#551 — clamp no modo enforced, fail-soft, auditado); `dbmax_targets` segue como claim assinado futuro — veja [LICENSING_SPEC.md](LICENSING_SPEC.md); `LicenseGuard` + resolução em config quando `licensing.mode: enforced`.

### Cópias, deployments e sites (Pro vs Enterprise)

**Status:** Modelo **comercial + técnico** de trabalho — **ainda não** há enforcement no código. Alinhar contratos ao que for possível **verificar** (binding por máquina, allowlists opcionais — veja [LICENSING_SPEC.md](LICENSING_SPEC.md)).

| Tier | **Cópias** / **sites** licenciados (uso em produção) | Figura típica |
| ---- | ------------------------------------------------------ | ------------- |
| **Pro** | **Duas** implantações por licença (ratificado pelo operador em 2026-06-11 — `DEFAULT_PRO_DEPLOYMENTS = 2`): a figura típica é **um footprint on-prem + um cloud/filial** para o **mesmo** contexto organizacional, **ou** o **laptop do consultor + um servidor de engajamento**. Não é direito para frota. Mesma narrativa de SKU: **um** contexto organizacional **ou** **um** consultor; packs **Pro+** estendem para **5** (conveniência de administração, preço ~linear). |
| **Enterprise** | **Mais de um** deployment autorizado por licença (e **preço** maior). Exemplos de empacotamento (combinar no contrato): **pacotes de cinco** sites (filiais, datacenters ou **tenants** de nuvem **nomeados**), **cobertura parcial** (parte das filiais ou parte dos tenants — não o estate inteiro), ou **ilimitado** para contas globais (ainda com **suporte** e trilhas **anti-abuso** no contrato). Caso de uso: organizações com **muitas** unidades e **vários** diretórios/tenants na nuvem precisam de **contagens flexíveis** sem “uma licença por VM”. |

**Grupos federados (silos por filial, CISO único, P&L local):** Em operadores **distribuídos** (ex.: **portos, terminais, logística ou industriais multi-país**), cada **unidade** costuma ser um **silo** de conhecimento, dados e sistemas: conformidade e regulação **locais**, **orçamento** e capex/opex **locais**, prioridades da gestão local — enquanto a **direção** de grupo define **ferramentas** de segurança **comuns**, padrões e **contratos em volume** estratégicos (EDR, plataformas de vulnerabilidade, pacotes de produtividade, baseline de firewall, padronização de hardware). Esse desenho **não** cabe em **uma** licença **Pro** para **todo** o grupo: cobertura **em nível de grupo**, governança e contagem de deployments são SKUs **Enterprise**. **Cabe** em **uma ou mais** licenças **Pro por unidade** quando **um único site** contrata **footprints distintos** — por exemplo **uma Pro** para um **tenant** em nuvem e **outra Pro** para **on-prem** **naquele** site — **sem** imposição da sede e **sem** obrigar outras filiais a espelharem. **Sim, isso é coerente** com Pro = entitlement **por deployment**; **roll-out em todo o grupo** e precificação **volume** ficam em contrato **Enterprise**.

**Controle via JWT (e adjacências):** Um único **`dbmfp`** já fixa **um** fingerprint de host. Para **Pro**, isso casa com **um** slot. Para **Enterprise**, faz falta **política + estrutura de dados** que escale:

- **Claims:** `dbmax_deployments` (inteiro — **2** no Pro, ratificado; **5** no pack Pro+; **5, 10, 25** ou **0** = ilimitado no Enterprise, decisão de produto); opcional **`dbmfp_allowlist`** ou **arquivo companheiro assinado** (lista de *seeds* ou IDs de deployment) se o JWT ficar grande demais — **refil** de token ou **pacotes add-on** quando o cliente compra **+5 sites** ou inclui tenants.
- **Operação:** Emissão/refil (renovação, **pacotes**) deve ficar na ferramenta **privada** de emissão com **log de auditoria** (`dbcid`, quem assinou, contagem de slots) — contratos grandes podem exigir **revisão humana**; automação pode ajudar no rascunho, mas **assessoria + produto** mandam no modelo.

**Partner / consultor:** ainda é comum **um** laptop estilo Pro; acordos **Partner Enterprise** podem usar **pacotes de deployment** ligados a claims de **programa** (`dbprogram`) — veja extensões futuras em [LICENSING_SPEC.md](LICENSING_SPEC.md).

### Assinatura Pro (uma organização ou consultoria)

**Comprador típico:** Uma empresa **ou** consultor independente / integrador pequeno atendendo **um contexto de cliente** por entitlement (medição exata TBD com assessoria).

**Reservar para SKUs classe Pro (ilustrativo — o produto pode entregar partes antes no open core):**

- **Entitlement comercial**, canal de **suporte padrão** (SLA mais leve que Enterprise), **assistência de configuração** e **customização produtizada** (perfis, formato de relatório, configuração de conectores como serviços empacotados) — assinatura **não é só feature gate**; veja [SUBSCRIPTION_TIERS.md](SUBSCRIPTION_TIERS.md) §O que a assinatura inclui.
- **Duas implantações licenciadas em produção** por licença (ratificado pelo operador em 2026-06-11 — ex.: on-prem + 1 cloud/filial; veja [Cópias, deployments e sites](#cópias-deployments-e-sites-pro-vs-enterprise)) — sem direito multi-site de frota. A **mesma** pessoa jurídica pode ter **várias Pro** para **footprints diferentes** (ex.: **nuvem vs on-prem** em **um** site); isso **não** substitui **Enterprise** quando o **grupo inteiro** precisa de cobertura.
- **Tetos de workers e targets acima do open core** — mas **nem tudo**: alguns **ingredientes premium** podem ser **só Enterprise** se custo ou risco forem altos demais para Pro (veja a tabela acima).
- **Cobertura de detecção e formatos premium** onde o custo de servir é alto: por exemplo pilhas completas assistidas por ML/DL quando houver gate, superfícies mais fortes de content-type / “disfarce”, formatos legados ou de nicho — alinhado à matriz interna de recursos.
- **Licença amarrada à máquina** e limites de **deploy nomeados** como em [LICENSING_SPEC.md](LICENSING_SPEC.md) (`dbmfp`, limites de trial).
- **Prioridade** na triagem de issues — não é o mesmo que 24/7 ou CSM dedicado (isso pende mais para Enterprise).

**Não é o principal diferencial Enterprise:** SSO em toda a org, relatórios white-label, pacote completo de conectores cloud/RH, ou programa MSP multi-inquilino — isso mapeia mais para **Partner** ou **Enterprise** (veja o plano).

### Assinatura Enterprise (contas reguladas, globais ou estratégicas)

**Comprador típico:** Grande organização, setor regulado ou comprador que precisa de governança e roadmap **nível fornecedor**.

**Reservar para SKUs classe Enterprise (ilustrativo):**

- **Workers e targets ilimitados** no **entitlement** (hardware manda — veja [Escala e concorrência](#escala-e-concorrência-modelo-de-trabalho--workers-targets-ingredientes-premium)); ingredientes premium **só Enterprise** que não entram no Pro.
- **Vários deployments autorizados por licença** (sites / tenants / filiais) — **pacotes**, cobertura **parcial** do estate ou **ilimitado** — precificado em conformidade; veja [Cópias, deployments e sites](#cópias-deployments-e-sites-pro-vs-enterprise).
- **Tudo o que o contrato definir como incluso em Pro**, mais **termos comerciais mais fortes**: SLA, suporte **dedicado** ou nomeado quando oferecido, indenizações e teto de responsabilidade conforme assessoria.
- **Governança e identidade:** por exemplo SSO/SAML, **RBAC** em relatórios, trilhas de auditoria imutáveis, exportações de evidência voltadas a fluxos **GRC / auditoria** — conforme o produto amadurecer.
- **Maior entitlement de conectores e formatos:** SaaS enterprise (ex.: object storage, M365/Graph em escala, caminhos HR/ERP), capacidades opcionais **orientadas a rede**, **white-label** ou regras rígidas de **co-marca** — conforme [Marca, narrativa e IP da experiência](#marca-narrativa-e-ip-da-experiência-inventário-para-assessoria-e-política-comercial).
- **Integração customizada** ou **serviços profissionais** podem ser **atrelados** a Enterprise (ou vendidos à parte); veja o fluxo comercial do mantenedor, não este documento.

### Partner (muitas vezes um SKU separado)

Programas de **consultoria / MSP / revenda** — uso **multi-cliente**, co-marca vs white-label e **custo de servir diferente** — **não** são o mesmo problema que Pro single-tenant ou Enterprise global. Trate **Partner** como família de entitlement própria nos contratos; tecnicamente pode mapear para claims como `dbtier: partner` (veja extensões futuras em [LICENSING_SPEC.md](LICENSING_SPEC.md)). **Não** colapse Partner em “só Pro com mais licenças” sem revisão de precificação e jurídico.

### Precificação e enforcement

- **Precificação:** Não fixada neste repositório; ao publicar SKUs, faça em **materiais comerciais** após revisão jurídica.
- **Enforcement:** Quando implementado, **JWT** assinado (ex.: `dbtier`, `dbmax_workers`, `dbmax_targets`, `dbmax_deployments`, `dbfeatures` opcional) deve refletir o que foi vendido — veja [LICENSING_SPEC.md](LICENSING_SPEC.md), seção de extensões futuras e rascunho de política operacional.

## Produtos futuros: parceiros vs clientes finais (lembrete de planejamento)

**Lembrete para uma rodada futura de licenciamento** (proteção de IP, comercialização, rentabilidade): considere **vários SKUs comerciais** com **objetivos, entitlements e faixas de preço** diferentes — como fornecedores de banco segmentam **Express**, **Standard**, **Enterprise**, **Enterprise + opções**, **RAC / add-ons**, etc. Os **limites Pro vs Enterprise** para posicionamento estão em [Assinatura comercial: Pro vs Enterprise (modelo de trabalho)](#assinatura-comercial-pro-vs-enterprise-modelo-de-trabalho) acima.

**Caso de uso a preservar explicitamente:** **Parceiros de consultoria / integração** que mantêm assinatura **nível parceiro** (ou **pro** / **enterprise** — nomes TBD) e usam o Data Boar para entregar auditorias ou implementações para **seus clientes** (terceiros), sob **o** contrato e entitlement **deles**, distinto de:

- Um SKU **comercial regular** voltado a **organizações que consomem o produto diretamente** (DPO / TI interno), e
- Posturas opcionais de **trial / POC** ou **acadêmicas** que você já separa na política.

**Por que importa:** Entrega liderada por parceiro muda **risco, suporte, responsabilidade, medição e expectativa de marca**. A precificação deve refletir **custo de servir diferente** (ex.: uso multi-cliente, carga de suporte maior, possível white-label ou regras de co-marca). **Nomes finais de tier, texto contratual e enforcement técnico** exigem decisões **jurídicas + de produto** antes da implementação.

**Direção técnica (depois):** codificar tier/programa em tokens assinados (veja [LICENSING_SPEC.md](LICENSING_SPEC.md), “Future extensions”) e fazer enforcement em `LicenseGuard` / relatórios só depois que claims e contratos estiverem fixos.

## Documentos relacionados

- [LICENSING_SPEC.md](LICENSING_SPEC.md) — formato do token, estados, binding de máquina, revogação.
- `docs/plans/PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md` — **matriz de recursos por tier** (Community / Pro / Partner / Enterprise); roadmap de enforcement; o que proteger como IP (plano interno de mantenedor — veja a seção *Internal and reference* em docs/README.md).
- [RELEASE_INTEGRITY.md](RELEASE_INTEGRITY.md) ([pt-BR](RELEASE_INTEGRITY.pt_BR.md)) — manifesto de release assinado opcional.
- [HOSTING_AND_WEBSITE_OPTIONS.md](HOSTING_AND_WEBSITE_OPTIONS.md) — repositórios privados e opções de site público.
- [ACADEMIC_USE_AND_THESIS.md](ACADEMIC_USE_AND_THESIS.md) ([pt-BR](ACADEMIC_USE_AND_THESIS.pt_BR.md)) — uso em tese / dissertação de docs e código públicos (não é assessoria jurídica).
