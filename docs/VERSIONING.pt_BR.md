# Convenção de versão e checklist de bump

**English:** [VERSIONING.md](VERSIONING.md)

Este projeto usa o esquema **major.minor.build** (maior.menor.build), com **sufixos de pré-release** opcionais enquanto o trabalho ainda está em preparação:

- **major** – primeiro número (ex.: mudanças incompatíveis ou release maior)
- **minor** – segundo número (ex.: novas funcionalidades, compatível)
- **build** – terceiro número (ex.: correções, documentação, sem mudança de comportamento)
- **sufixo** (opcional) – marcador de estágio em minúsculo: `-beta` ou `-rc`

Exemplos:

- `1.3.2` significa major 1, minor 3, build 2 (número final publicável).
- `1.3.3-beta` significa trabalho de pré-release em andamento para o próximo build.
- `1.3.3-rc` significa release candidate (feature/código/docs/testes conectados; faltam os passos finais de publish).

---

## Regras de bump

| Tipo de bump | Regra                                                | Exemplo             |
| ---          | ---                                                  | ---                 |
| **Major**    | Aumentar o primeiro número; zerar minor e build      | `1.3.2` → **2.0.0** |
| **Minor**    | Manter major; aumentar o segundo número; zerar build | `1.3.2` → **1.4.0** |
| **Build**    | Manter major e minor; apenas aumentar o build        | `1.3.2` → **1.3.3** |

---

## Octeto-maturidade (side-channel) + roadmap de linha (ADR-0073 — Accepted)

**Rascunho canônico:** [ADR-0073](adr/ADR-0073-version-scheme-octet-maturity-and-roadmap.md) (EN, **Accepted**). Complementa [ADR-0072](adr/ADR-0072-commit-gate-vs-release-gate-distinct-criteria.md) (commit gate ≠ release gate).

### Versão pública vs octeto de maturidade (não misturar)

| Superfície | Formato | Regra |
| --- | --- | --- |
| **Versão pública** (`[project] version`, About, tags, Docker, README) | `major.minor.build` + sufixo PEP 440 opcional (`-beta[.N]` / `-rc[.N]`) ou nada | **Só três segmentos** — nunca `1.7.4.201` nem quarto segmento |
| **Octeto de maturidade** (faixas Gibson DNS-beacon) | `[tool.databoar] maturity_build` (derivado, side-channel) | **Nunca** em `[project] version` nem no About |
| **Sufixo `-alpha`** | Tamper-detection (#856) | **Não** é faixa de maturidade |

Faixas do octeto quando `maturity_build` estiver em uso (ferramentas operador/beacon — **não** o dígito build do semver público, salvo política explícita do operador):

| Faixa octeto | Significado |
| --- | --- |
| **1–126** | maturidade beta (contador começa em **1** — primeiro beta = `.1`; teto forgiving) |
| **127–199** | maturidade rc |
| **200–254** | release / GA + fix (`.200` = GA na linha, `.201` = primeiro fix pós-GA, …) |
| **255** | sentinela de overflow — consultar TXT beacon |

**A contagem começa em 1** (nada é `.0`) por clareza para não técnicos. Os tetos de faixa são **forgiving** — o TXT do beacon absorve overflow; não trate o topo da faixa como limite rígido.

### Nova linha pública — reset da faixa de maturidade

Ao abrir uma **nova linha semver** (ex.: **`1.8.0`** após **`1.7.4`**), **`maturity_build` não continua** a partir de `.208` na linha antiga. **Reinicia na faixa Gibson** que corresponde ao **sufixo pre-release** em `[project] version`:

| `[project] version` na nova linha | Faixa `maturity_build` | Âncora típica |
| --- | --- | --- |
| **`X.Y.Z-beta`** (ou `-beta.N`) | **1–126** | Reinício em **`1`** (primeiro beta = `.1`) — registrar nas release notes |
| **`X.Y.Z-rc`** (ou `-rc.N`) | **127–199** | Reinício baixo na faixa (ex.: **`127`** ou **`128`**) |
| **`X.Y.Z`** stable (GA) | **200–254** | **`.200`** = GA na linha; **`.201`** = primeiro fix, … |

**`.postN` no PyPI** aplica-se só na faixa **release** (republicação fix-line na **mesma** linha pública, ex. `1.7.4.post2`). **Não** carrega para **`1.8.0-beta`**.

Sufixos (`-beta`, `-rc`, `-rc-N`) são obrigatórios em `main` enquanto um issue de **release gate** (ex.: GitHub #406) estiver **aberto**. **Commit gate** verde (`check-all`) **não** autoriza removê-los — ver ADR-0072. Gate **#406** fechado com **1.7.4** stable (PR **#1024**).

### Linha 1.7.4 atual

| Rótulo | Status |
| --- | --- |
| **Working tree `main`** | **`1.7.4`** no `pyproject.toml` na branch **`release/1.7.4`** (PR **#1024**); publish (tag/Hub) após merge do operador + **release-ritual** |
| **#970** | Bump/tag stable prematuro sem release gate — corrigido por **ADR-0072** + gate **#406**; **`1.7.4` não é VOID** |
| **Numeração pública pós-GA** | **Resolvido** (#977) — linha pública permanece **`1.7.4`**; octeto **`maturity_build`** distingue fixes; próxima linha pública **`1.8.0`** |

Escada (histórico): `1.7.4-beta` → `1.7.4-rc` → `1.7.4-rc-2` → **`1.7.4`** (stable alvo, PR **#1024**).

### Roadmap de linha (intenção — sem incremento ingênuo)

| Linha | Escopo |
| --- | --- |
| **Linha `1.7.4`** | Maturidade open-core + proteção comercial JWT |
| **`1.8.x`** | Capacidades corporativas aumentadas (re-ID, sidecars, plugins/Clojure — **nova arquitetura**) |
| **`1.7.5`** | **Não existe** — agentes não inventam (#772). Próximo milestone dev: **`1.8.0-beta`**. |
| **`1.9.x`** | Horizonte (expansão compliance — triagem #772) |

Lifecycle DNS-beacon / heartbeat / kill-switch (#717) fica no roadmap **1.8.x** (`docs/plans/PLAN_SELF_UPGRADE_AND_VERSION_CHECK.md`, índice interno em `docs/README.md`).

### PyPI post-releases + dois contadores (ADR-0073 — ratificado 2026-06-27)

Quando **`1.7.4`** já está no PyPI e um fix de empacotamento precisa sair sem nova linha pública:

| Contador | Campo | Regra |
| --- | --- | --- |
| **Publicação** | `[project] version` **`.postN`**, About, PyPI | Um incremento por **upload PyPI** (não por fix em `main`) |
| **Maturidade** | `[tool.databoar] maturity_build` | Octeto side-channel; +1 por **fix discreto** no comportamento instalado/runtime (pode correr à frente do `postN`) |

**Linha pública** permanece **`1.7.4`** (README, man); **linha de build** é **`1.7.4.postN`**. Manter o **mapa `postN ↔ maturity_build`** em [`docs/releases/`](releases/) — ex.: [`1.7.4.post1.md`](releases/1.7.4.post1.md): `1.7.4=.201 · 1.7.4.post1=.202`.

Para cada nota nova `X.Y.Z.postN`, deixe o intervalo unpublished explícito: inclua uma linha por `maturity_build` intermediário como `*(fix, unpublished on PyPI)*` entre `post(N-1)` e `postN`. Não comprima esse intervalo em uma linha única de “N fixes”.
Nesse mapa, mantenha a coluna **Notes** em prosa curta de efeito (com `#issue` quando houver), não em subject cru de commit. A prova git-literal (`fix(...)` + hash) fica apenas no **Appendix — Fix set (N=...)**.

---

## Fluxo de pré-release (`-beta` / `-rc`) antes do publish final

Use sufixos em minúsculo de forma consistente:

| Estágio                | Uso recomendado                                                                                                                                  | Exemplo      |
| ---                    | ---                                                                                                                                              | ---          |
| **`-beta`**            | Mudanças relevantes de código/comportamento já começaram e estão rastreadas, mas ainda não são candidatas finais de release.                     | `1.7.1-beta` |
| **`-rc`**              | Candidato pronto para validação final/coreografia de publish (testes verdes, docs sincronizados, release notes prontas, faltando merge/release). | `1.7.1-rc`   |
| **final (sem sufixo)** | Número de release público (tag Git + GitHub Release + publish no Docker Hub).                                                                    | `1.7.1`      |

### Política prática

- Se uma fatia altera comportamento de forma relevante (API, lógica de detecção, saída de relatório, operação em runtime, postura de segurança), prefira mover a versão de trabalho para `X.Y.Z-beta`.
- Quando o pacote estiver materialmente pronto (código + testes + docs/release notes em forma), promova para `X.Y.Z-rc`.
- Remova o sufixo e publique `X.Y.Z` apenas no ciclo de release real (merge + tag + GitHub Release + publish Docker).
- Para escopo maior (ou quando solicitado explicitamente), publique com **minor bump**: `X.(Y+1).0` (sem sufixo no publish final).

---

## Versão de trabalho vs versão publicada (evitar confusão)

- **Versão de trabalho:** valor atual no `pyproject.toml` no branch (pode estar em `-beta`/`-rc` ou ainda sem release).
- **Versão publicada:** última tag Git + GitHub Release + tag Docker Hub + versão **`data-boar`** no PyPI disponíveis para uso externo.
- Não assuma que são iguais; informe as duas explicitamente em release notes e pedidos de revisão.

### Assistente / automação (ordem obrigatória)

**Cursor / agentes:** seguir **`.cursor/rules/release-publish-sequencing.mdc`** (**situacional** — sessão **`release-ritual`** ou **`@release-publish-sequencing.mdc`** quando os **globs** não carregam; **`docker-local-smoke-cleanup.mdc`** continua **sempre ligada** para smoke/prune) — criar tag Git **`vX.Y.Z`**, GitHub Release e passos de publicação no Docker Hub **antes** de avançar o `main` para o próximo bump **`-beta`** (ou próximo dev). A palavra de sessão **`release-ritual`** significa **`read_file`** nessa regra (ou **`@`**) e neste arquivo antes de editar semver ou notas de release.

---

## Canais de distribuição (artefatos publicados)

| Canal | Instalação (consumidor) | Publicação (maintainer, estável) |
| --- | --- | --- |
| **Git** | `git clone` / tarball de release | Tag **`vX.Y.Z`** + **`gh release create`** |
| **PyPI** | `pip install data-boar` / `pipx install data-boar` | Dispatch OIDC: **`scripts/pypi-publish.ps1`** / **`pypi-publish.sh`** → **`.github/workflows/publish-pypi.yml`** — **TestPyPI primeiro**, depois **pypi** (#1046). **Sem** token de API na estação. Empacotamento: [ADR-0031](adr/ADR-0031-pypi-packaging-hatchling-flat-layout.md); pins do workflow: [ADR-0005](adr/ADR-0005-ci-github-actions-supply-chain-pins.md). |
| **Docker Hub** | `docker pull fabioleitao/data_boar:X.Y.Z` | Smoke local + ritual **`docker-hub-publish`** — ver **`docs/ops/DOCKER_IMAGE_RELEASE_ORDER.md`** |

Builds **`-beta`** / **`-rc`** permanecem **só no Git** para consumidores externos no PyPI e Docker Hub (índices estáveis sem sufixo). Ordem completa: **`.cursor/rules/release-publish-sequencing.mdc`** (GitHub Release → PyPI → Docker).

---

## Onde a versão aparece (checklist ao dar bump)

Ao dar bump na versão, atualize **todos** os itens abaixo para manter o número consistente:

### 1. Fonte de verdade (obrigatório)

| Local                | O que alterar                                                                                                                                                                                                                                                                                     |
| ---                  | ---                                                                                                                                                                                                                                                                                               |
| **`pyproject.toml`** | Atualize a linha `version = "X.Y.Z"`. Ela é a **única fonte de verdade** do pacote instalado. A aplicação (página About, aba Report info, rodapé do heatmap, API `/about/json`) lê a versão dos metadados do pacote; atualizar o `pyproject.toml` e reinstalar é suficiente em tempo de execução. |

### 2. Fallback quando os metadados não estão disponíveis

| Local               | O que alterar                                                                                                                                                                          |
| ---                 | ---                                                                                                                                                                                    |
| **`core/about.py`** | Atualize a string de fallback em `get_about_info()` quando `importlib.metadata.version(...)` falhar (ex.: execução direta do código sem instalar). Ex.: `ver = "1.3.0"` → nova versão. |

### 3. Páginas de manual (man)

| Local                  | O que alterar                                                                                  |
| ---                    | ---                                                                                            |
| **`docs/data_boar.1`** | Na linha `.TH` (ex.: `"Data Boar 1.5.4"`), defina a versão para a nova.                        |
| **`docs/data_boar.5`** | Idem: atualize a versão na linha `.TH`.                                                         |

**Comando vs nome da man:** O CLI empacotado é **`data-boar`** (hífen). As man pages primárias instaladas são **`data-boar`** (seções 1 e 5). Os arquivos-fonte no repositório continuam **`docs/data_boar.{1,5}`**; na instalação copie como `data-boar.{1,5}` com symlinks opcionais **`data_boar`** e **`lgpd_crawler`** (aliases legados). Veja a seção **INSTALLATION OF THIS MAN PAGE** em `docs/data_boar.1`.

### 4. Deploy e Docker

| Local                       | O que alterar                                                                                                                 |
| ---                         | ---                                                                                                                           |
| **`docs/deploy/DEPLOY.md`** | Atualize os **exemplos** de tags de versão nos comandos de tag/push do Docker (ex.: `1.3.0` nos exemplos) para a nova versão. |

### 5. Documentação (EN e PT-BR)

| Local                          | O que alterar                                                                                                                                          |
| ---                            | ---                                                                                                                                                    |
| **`README.md`**                | Se o texto citar o número da versão atual (ex.: em exemplo de tag de imagem), atualize.                                                                |
| **`README.pt_BR.md`**          | Idem ao README.md para qualquer menção explícita à versão.                                                                                             |
| **`docs/USAGE.md`**            | Atualize qualquer referência explícita à versão, se houver.                                                                                            |
| **`docs/USAGE.pt_BR.md`**      | Idem ao USAGE.md.                                                                                                                                      |
| **`docs/plans/PLANS_TODO.md`** | Se houver nota de “versão atual” ou “app version” no “Current state” ou passo de publish de um plano, atualize ao lançar.                              |
| **Outros docs**                | Pesquise no repositório pela string da versão antiga (ex.: `1.3.0`) e atualize referências restantes em SECURITY.md, CONTRIBUTING.md ou release notes. |

### 6. Distribuição, Docker Hub e texto voltado ao cliente

Mantenha a história do **semver publicado** alinhada para quem faz pull da imagem ou lê material de marketing (não só o `pyproject.toml`):

| Local | O que alterar |
| --- | --- |
| **`docs/ops/DOCKER_HUB_REPOSITORY_DESCRIPTION.md`** | Blocos **Short** + **Full** para a UI do Docker Hub: **Current release**, **Supported tags** (semver), **copyright/mantenedor**, CLI (`python main.py`). **Colagem manual** no Hub após cada push de imagem **estável** — o site **não** puxa do Git; se aparecer versão antiga (ex.: **1.6.5** num bloco **Tags**), alguém pulou este passo. Para pushes só **`-beta`** / **`-rc`**, não é obrigatório atualizar o texto público do repositório salvo pedido explícito. |
| **`docs/ops/today-mode/PUBLISHED_SYNC.md`** (+ **`.pt_BR.md`**) | Linhas da tabela: **GitHub Latest**, **Docker Hub**, **PyPI** e “próxima” patch — devem refletir o que o cliente consegue instalar. |
| **`docs/TECH_GUIDE.md`** (+ **`.pt_BR.md`**) | Tag de exemplo do Hub na subseção Docker (se fixar semver). |
| **Social / marcos (operador)** (ex.: **`docs/private/social_drafts/`**, gitignored) | Se o texto citar “release atual”, “último no Docker Hub” ou número de versão, alinhar ao **`README.md`** (**Release atual**) e ao **`PUBLISHED_SYNC`** — não celebrar versão que ainda não está no GitHub + Hub sem marcar como **em breve**. |

### 7. Interface e relatórios (não é preciso editar se 1–2 forem feitos)

Estes exibem a versão **dinamicamente** a partir dos metadados do pacote (via `core/about.py`), portanto **não** precisam de edição manual ao dar bump:

- **Página About** (`api/templates/about.html`) – usa `{{ about.version }}`
- **Dashboard / Reports** – usam `{{ about.version }}`
- **Aba “Report info” do Excel** – `report/generator.py` usa `about["version"]`
- **Rodapé do heatmap PNG** – mesmo dicionário `about`
- **API `/about/json`** – mesmo dicionário `about`

Depois de atualizar o `pyproject.toml` (e opcionalmente `core/about.py`), reinstale o pacote (ex.: `uv sync` ou `pip install -e .`) para que a nova versão entre nos metadados; a interface e os relatórios passarão a exibi-la automaticamente.

---

## Resumo rápido

- **Formato:** `major.minor.build`
- **Sufixos de pré-release:** `-beta`, `-rc` em minúsculo (apenas estados de trabalho)
- **Bump major:** `X.Y.Z` → `(X+1).0.0`
- **Bump minor:** `X.Y.Z` → `X.(Y+1).0`
- **Bump build:** `X.Y.Z` → `X.Y.(Z+1)`
- **Fluxo de promoção:** `X.Y.Z-beta` → `X.Y.Z-rc` → `X.Y.Z` (publish final)
- **Checklist:** pyproject.toml → core/about.py → docs/data_boar.1, data_boar.5 → docs/deploy/DEPLOY.md → README (EN/PT-BR), USAGE (EN/PT-BR), PLANS_TODO → **DOCKER_HUB_REPOSITORY_DESCRIPTION** + **PUBLISHED_SYNC** → exemplo Docker no TECH_GUIDE → rascunhos sociais opcionais → buscar no repositório pela string da versão antiga.

**English:** [VERSIONING.md](VERSIONING.md)
