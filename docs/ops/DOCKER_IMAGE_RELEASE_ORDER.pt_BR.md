# Ordem de release da imagem Docker: merge → build → bump → push

**English:** [DOCKER_IMAGE_RELEASE_ORDER.md](DOCKER_IMAGE_RELEASE_ORDER.md)

**Contexto:** Após o **PR #99**, o repo usa **`python:3.13-slim`** no Dockerfile. Os operadores ainda precisam de uma **sequência repetível** para manter tags do Hub, versão do app e Scout alinhados. Esta doc define a sequência padrão e as variantes.

**Relacionado:** [scripts/docker/README.md](../../scripts/docker/README.md), [VERSIONING.md](../VERSIONING.md), [PLANS_TODO.md](../plans/PLANS_TODO.md) (ordens **–1**, **–1b**), [HOMELAB_VALIDATION.md](HOMELAB_VALIDATION.md) (ordem **–1L** para segundo ambiente), [DOCKER_HUB_REPOSITORY_DESCRIPTION.md](DOCKER_HUB_REPOSITORY_DESCRIPTION.md) (texto do Hub — colar após publicar).

---

## Padrão recomendado (amigável a PRs, menor confusão)

Use quando quiser **uma imagem publicada** correspondendo a **uma versão do app** (página About, rodapé do relatório, `fabioleitao/data_boar:1.6.x`). Após o push, cole **Short** + **Full** de **[DOCKER_HUB_REPOSITORY_DESCRIPTION.md](DOCKER_HUB_REPOSITORY_DESCRIPTION.md)** no Docker Hub para que a descrição reflita o semver atual (anti-defasagem).

| Passo          | Ação                                                                                                                                                                                           |
| ----           | ------                                                                                                                                                                                         |
| 1. **Merge**   | Todos os PRs de **código** no `main` (Dockerfile, correções, etc.) — ex.: **#99** ✅                                                                                                           |
| 2. **Merge**   | **PR de bump de versão** (build → **`1.6.8`** conforme [VERSIONING.md](../VERSIONING.md)) para que `pyproject.toml` no `main` seja a versão que vai ser publicada                              |
| 3. **Pull**    | `git checkout main && git pull origin main`                                                                                                                                                    |
| 3b. **Disco**  | No **PC dev principal** (ex.: Docker Desktop no Windows): verifique **espaço livre** no volume usado pelo Docker antes de um build pesado (`Get-PSDrive` ou Docker **Configurações → Recursos**). Disco cheio → builds com falha ou corrompidos. |
| 4. **Build**   | `.\scripts\docker-lab-build.ps1` (da raiz do repo)                                                                                                                                            |
| 5. **Smoke**   | **Obrigatório antes do push para o Hub:** `docker run --rm` curto contra **`data_boar:lab`** (ex.: `python main.py --version` ou `/health`) — veja [DOCKER_SETUP.md](../DOCKER_SETUP.md) §7 / [DEPLOY.md](../deploy/DEPLOY.md). **Não fazer push** se o smoke falhar. |
| 6. **Push**    | `.\scripts\docker-hub-publish.ps1 -SkipBuild` (após `docker login`) — cria tags **`:latest`** e **`:<semver do pyproject>`**, executa **`scout quickview`** + **`scout recommendations`** |
| 7. **Gate**    | `.\scripts\docker-scout-critical-gate.ps1 -Image fabioleitao/data_boar:latest` (falha apenas para **CRITICALs acionáveis** com versão corrigida disponível)                                   |
| 8. **Prune**   | `.\scripts\docker-prune-local.ps1 -WhatIf` e depois sem `-WhatIf` na **mesma máquina** — evita acúmulo de tags obsoletas **`fabioleitao/data_boar:*`** / **`data_boar:*`** no Docker Desktop  |
| 9. **Hub UI**  | **Docker Hub → Repositório → Editar:** cole **Short** + **Full** de [DOCKER_HUB_REPOSITORY_DESCRIPTION.md](DOCKER_HUB_REPOSITORY_DESCRIPTION.md); atualize [today-mode/PUBLISHED_SYNC.md](today-mode/PUBLISHED_SYNC.md) |

**Por que fazer o bump antes do build/push:** A imagem usa `COPY . .`, que inclui `pyproject.toml`. Fazer o build *depois* do bump garante que o app *dentro do contêiner* reporta a mesma versão que a tag semver publicada no Hub.

---

## Variantes (prós / contras)

### A — Bump de versão **antes** do push (recomendado acima)

- **Prós:** `fabioleitao/data_boar:1.6.8` (exemplo) bate com **About / relatórios**; operadores podem confiar que tag = versão do app; um único contexto para suporte.
- **Contras:** Dois PRs (ou dois merges) antes de publicar se Dockerfile e versão forem em PRs separados; leve cerimônia adicional.

### B — Push da imagem **primeiro**, bump de versão **depois**

- **Prós:** Validação rápida no Hub (Scout no novo digest) antes de "carimbar" um número de release.
- **Contras:** Janela curta em que **`:latest`** foi construído a partir do `main` ainda na versão anterior (ex.: **1.6.3**) — confuso se alguém comparar **About** com a tag do Hub no mesmo dia. Mitigação: fazer o bump **na mesma sessão** ou documentar "digest pré-release".

### C — PR único: Dockerfile + bump de versão juntos

- **Prós:** Um merge, um build, um push — overhead mínimo.
- **Contras:** Mistura "infra" e "release"; revisores podem preferir separação; nem sempre viável se o bump aguarda QA.

### D — Bump sem publicar imagem (apenas docs / pyproject)

- **Prós:** Raro; para instalações via pip/git sem Docker.
- **Contras:** **Não usar** se Docker é a entrega principal — o Hub ficaria defasado em relação à versão declarada.

---

## Alinhamento A1 / A2 / S4 (não paranoico, apenas ordenado)

- **A1 (Dependabot / –1):** Manter **`pyproject.toml`**, **`uv.lock`**, **`requirements.txt`** sincronizados; executar **`.\scripts\check-all.ps1`** antes do merge. Use **`.\scripts\maintenance-check.ps1`** para um snapshot rápido de Dependabot + Scout.
- **A2 (Scout / –1b):** Após cada **publicação**, use **`docker-hub-publish.ps1`** (inclui recomendações) ou a UI do Hub. O **#99** corrigiu a imagem base; contagens residuais geralmente precisam de **A1** (pacotes) + tempo.
- **Gate CRITICAL do Scout:** Use **`scripts/docker-scout-critical-gate.ps1`** para separar (a) CRITICALs acionáveis com versão corrigida disponível (**falhar + tratar agora**) de (b) CRITICALs sem correção upstream (**documentar + monitorar + cadência de rebuild**).
- **S4:** Com **#98** e **#99** no `main`, a próxima fatia **S4** é **`pr/deps-security-refresh`** (ou equivalente –1 PR).
- **–1L (segundo ambiente):** Execute **[HOMELAB_VALIDATION.md](HOMELAB_VALIDATION.md)** quando a segunda máquina estiver pronta — **após** –1/–1b estarem aceitáveis; não é necessário bloquear **merge/publicação** por causa disso.

---

*Última atualização: após merge do **PR #99** (`python:3.13-slim` no `main`).*
