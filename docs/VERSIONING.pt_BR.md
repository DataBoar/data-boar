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

## Octeto-maturidade do build + roadmap de linha (#971 / ADR-0073)

**Decisão canônica:** [ADR-0073](adr/ADR-0073-version-scheme-octet-maturity-and-roadmap.md) (EN). Complementa [ADR-0072](adr/ADR-0072-commit-gate-vs-release-gate-distinct-criteria.md) (commit gate ≠ release gate).

Disciplina **estilo Gibson DNS-beacon**, antes interna; após a promoção não autorizada de **`1.7.4`** (#970) o **número público** também expõe maturidade.

### Faixas do terceiro octeto (build numérico com maturidade)

| Faixa build | Significado | Exemplos |
| --- | --- | --- |
| **0–127** | faixa beta | fatias experimentais |
| **128–199** | faixa rc | maturidade release-candidate |
| **200–255** | faixa release | **`.200` = GA**, **`.201` = fix-1**, **`.202` = fix-2**, … |

Sufixos (`-beta`, `-rc`, `-rc-N`) continuam válidos em `main` enquanto o **release gate** (GitHub #406) estiver aberto. **Commit gate** verde (`check-all`) **não** autoriza removê-los — ver ADR-0072.

### Linha 1.7.4 atual (pós-#970)

| Rótulo | Status |
| --- | --- |
| **`1.7.4` / build `.200` (GA)** | **VOID** — nunca lançada; promovida sem gate (#970, PR #840) |
| **Working tree `main`** | **`1.7.4-rc-2`** no `pyproject.toml` até fechar **#406** |
| **Stable real pós-gate** | começa em **`1.7.4.201`** (fix-1 pós-GA queimada) — não `1.7.4` |

Escada: `1.7.4-beta` → `1.7.4-rc` → **`1.7.4-rc-2`** (hoje) → **`1.7.4.201`** (pós-gate).

### Roadmap de linha (intenção — sem incremento ingênuo)

| Linha | Escopo |
| --- | --- |
| **`1.7.4.x`** | Maturidade open-core + proteção comercial JWT (**linha de fix** pós-gate) |
| **`1.8.x`** | Capacidades corporativas aumentadas (re-ID, sidecars, plugins/Clojure — **nova arquitetura**) |
| **`1.7.5`** | **Não existe** — agentes não inventam (#772). Próximo milestone dev: **`1.8.0-beta`**. |
| **`1.9.x`** | Horizonte (expansão compliance — triagem #772) |

Lifecycle DNS-beacon / heartbeat / kill-switch (#717) fica no roadmap **1.8.x** (`docs/plans/PLAN_SELF_UPGRADE_AND_VERSION_CHECK.md`, índice interno em `docs/README.md`).

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
- **Versão publicada:** última tag Git + GitHub Release + tag do Docker Hub disponível para uso externo.
- Não assuma que são iguais; informe as duas explicitamente em release notes e pedidos de revisão.

### Assistente / automação (ordem obrigatória)

**Cursor / agentes:** seguir **`.cursor/rules/release-publish-sequencing.mdc`** (**situacional** — sessão **`release-ritual`** ou **`@release-publish-sequencing.mdc`** quando os **globs** não carregam; **`docker-local-smoke-cleanup.mdc`** continua **sempre ligada** para smoke/prune) — criar tag Git **`vX.Y.Z`**, GitHub Release e passos de publicação no Docker Hub **antes** de avançar o `main` para o próximo bump **`-beta`** (ou próximo dev). A palavra de sessão **`release-ritual`** significa **`read_file`** nessa regra (ou **`@`**) e neste arquivo antes de editar semver ou notas de release.

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
| **`docs/data_boar.5`** | Idem: atualize a versão na linha `.TH`. (Legado: `lgpd_crawler` é symlink de compatibilidade.) |

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
| **`docs/ops/today-mode/PUBLISHED_SYNC.md`** (+ **`.pt_BR.md`**) | Linhas da tabela: **GitHub Latest**, **Docker Hub** e “próxima” patch — devem refletir o que o cliente consegue instalar. |
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
