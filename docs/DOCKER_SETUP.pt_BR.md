# Docker Setup: MCP, build, push e deploy

**English:** [DOCKER_SETUP.md](DOCKER_SETUP.md)

Execute estes passos em um terminal onde o **Docker** esteja disponível (ex.: PowerShell ou CMD após iniciar o Docker Desktop).

**Imagem pré-construída:** A aplicação é publicada no Docker Hub como `fabioleitao/data_boar:latest` ([hub.docker.com/r/fabioleitao/data_boar](https://hub.docker.com/r/fabioleitao/data_boar)). Você pode usar `docker pull` e executar essa imagem em vez de construir a partir do código (veja [README](../README.md) e [deploy/DEPLOY.md](deploy/DEPLOY.md) ([pt-BR](deploy/DEPLOY.pt_BR.md))). A imagem inclui as funcionalidades atuais (detecção de sensibilidade híbrida regex + ML + DL opcional; termos de treino ML/DL configuráveis via `ml_patterns_file`, `dl_patterns_file` ou `sensitivity_detection` no config — veja [SENSITIVITY_DETECTION.pt_BR.md](SENSITIVITY_DETECTION.pt_BR.md)).

## Persistência de dados (volume `/data`)

A imagem padrão define **`CONFIG_PATH=/data/config.yaml`**. O **SQLite** da sessão, **relatórios Excel**, **heatmaps** e **logs de auditoria** seguem caminhos derivados dessa config (em geral sob `/data` quando os caminhos são relativos ao arquivo de config). **Sem bind mount**, esses arquivos ficam na camada do container e **se perdem** ao remover o container. Use sempre **`-v <pasta_host>:/data`** com a mesma pasta no host para config e saídas (os exemplos abaixo usam `${PWD}/data:/data`). No Compose, o override deve montar o mesmo caminho — veja [deploy/DEPLOY.pt_BR.md](deploy/DEPLOY.pt_BR.md).

**Atualizando sua imagem local:** Para atualizar o Docker Desktop com a versão atual do repositório, faça pull da imagem e reinicie o(s) container(es):

```powershell
docker pull fabioleitao/data_boar:latest
# Se você usa um único container
docker stop data-boar-audit
docker rm data-boar-audit
docker run -d --name data-boar-audit -p 8088:8088 -v "${PWD}/data:/data" -e CONFIG_PATH=/data/config.yaml fabioleitao/data_boar:latest

# Se usa Compose
docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.override.yml pull
docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.override.yml up -d
```

Repita sempre que quiser usar uma nova versão publicada no Docker Hub (ex.: após releases ou atualizações no repositório).

## Extras e licenciamento em pool (`/extras` + `DATA_BOAR_MACHINE_SEED`)

A imagem publicada é **enxuta de propósito**: instala só os grupos SQL base do `pyproject.toml` — **`sql-community`**, **`mssql`** (pyodbc) e **`oracle`**. **Não** embute todos os extras opcionais (sem fat image, sem matriz de imagens, sem exigir `FROM` da nossa imagem + rebuild por cliente).

| Na imagem (base) | Via montagem em runtime |
| ---------------- | ----------------------- |
| `sql-community`, `mssql`, `oracle` (e pacotes) | `nosql`, `shares`, `mssql-pymssql`, `compressed`, `dataformats`, `richmedia`, `dl`, `bigdata`, `grc-dashboard`, … |

**Extensão em runtime (sem shell, sem pip na imagem):**

1. Monte um pack de wheels ABI-compatível com o Python da imagem (ex.: **cp314** na imagem GIL, **cp314t** na `-nogil`) — tipicamente `pip install --target ./extras-pack 'data-boar[nosql,shares,…]'` ou wheels do canal wheelhouse do projeto.
2. Monte somente leitura: `-v /caminho/extras-pack:/extras:ro` (uid nonroot **65532**; sem `--user 0`).
3. A imagem define **`PYTHONPATH=/extras:/app`** (`/extras` primeiro, depois `/app`) e **`VOLUME ["/extras"]`**.

**Diagnóstico primeiro:** `python main.py --check-extras` lista cada extra × estado × origem (imagem vs `/extras`). O smoke pós-build (`scripts/docker/docker-image-smoke.sh`) **falha** se algum extra com `in_artifact: true` no `EXTRAS_MANIFEST.json` não importar.

**ABI incompatível:** pack da minor/variante errada falha **alto na inicialização** (fail-closed), não como conector ausente em silêncio.

**`DATA_BOAR_MACHINE_SEED`:** declarado na imagem (vazio por padrão). Defina um segredo estável para pools **Enterprise** para o fingerprint não mudar a cada `docker run`. Deixe vazio em **Pro / Pro+** (contagem por hostname). Veja [LICENSING_SPEC.pt_BR.md](LICENSING_SPEC.pt_BR.md).

Issues relacionadas: **#1400**, **#1401**, **#1399**, **#1402**.

---

## 1. Conectar o Cursor ao Docker Desktop MCP

### Opção A – MCP integrado do Docker Desktop (se disponível)

1. Abra **Docker Desktop** → **Settings** → **Features in development** (ou **Beta**).
1. Ative **MCP** / **MCP Toolkit** se estiver presente.
1. Anote o endpoint MCP (ex.: `npipe://...` no Windows).
1. Em **Cursor** → **Settings** → **MCP** → **Add server**:
   - Name: `docker`
   - Command / URL: use o endpoint do Docker Desktop (ou `docker-mcp` se ele fornecer um CLI).

### Opção B – Instalador MCP do Cursor

```powershell
npm install -g @cursor/mcp-installer
cursor-mcp init
cursor-mcp install docker
cursor-mcp list
```

Depois adicione o servidor Docker MCP em Cursor Settings → MCP usando o caminho exibido por `cursor-mcp list`.

### Opção C – Docker MCP manual

Se você usa um MCP Docker da comunidade (ex.: `cursor-docker-mcp`), adicione-o em Cursor Settings → MCP com o command/args do servidor.

### Docker Hub MCP (recomendado para checagens “pré-push”, sem navegação manual)

Se você já criou um **Personal Access Token (PAT)** dedicado no Docker Hub (com expiração, ex.: 90 dias), dá para usar um MCP de **Docker Hub** para checar rapidamente:

- quais **namespaces** você tem acesso,
- se um **repositório** existe,
- quais **tags** existem (e em quais arquiteturas/OS),
- metadados de um tag (digest, last pushed, etc.).

Isso é útil para automações humanas “token-aware” (menos cliques e menos copy/paste): antes de um push, você confirma se a tag esperada já existe, e depois do push você valida que ela apareceu.

**Importante (segurança):**

- **Não** salve o PAT em arquivos rastreados (`docs/`, `scripts/`, `.env` versionado). Use o storage de **secrets do MCP** (Cursor/Docker Desktop) ou variáveis de ambiente locais.
- Rotacione o PAT na cadência definida (ex.: 90 dias) e mantenha o escopo mínimo (somente o que o MCP precisa).
- **Least privilege recomendado:** `read/write` costuma ser suficiente para checagens e publicação; **evite `delete`** (você já fez isso) para reduzir risco de remoção acidental.

Se você estiver usando o catálogo MCP do Docker, o servidor costuma se chamar **`dockerhub`** e pede:

- `dockerhub.username` (público, ex.: seu usuário Docker Hub)
- secret `dockerhub.pat_token` (o PAT — **nunca** comitar)

**Formato do secret:** em algumas integrações, o `dockerhub.pat_token` precisa vir como `namespace:PAT` (ex.: `fabioleitao:<pat>`). Se a checagem do namespace falhar com erro “missing part #2”, é forte indício de que o MCP está recebendo apenas uma das partes.

---

## 2. Construir a imagem (modo API web)

O Dockerfile usa build multi-stage (imagem de runtime mínima; ferramentas de build apenas no estágio de build). A partir da **raiz do projeto**:

```powershell
cd c:\Users\<username>\Documents\dev\data-boar

docker build -t data_boar:latest .
```

Padrão: API web + frontend. O CLI continua disponível via override de `--entrypoint` (veja [deploy/DEPLOY.md](deploy/DEPLOY.md) ([pt-BR](deploy/DEPLOY.pt_BR.md))).

---

## 3. Tag e push para o Docker Hub (fabioleitao)

Use suas credenciais do Docker Hub (usuário `fabioleitao` e senha ou Access Token).

```powershell
# Tag para Docker Hub
docker tag data_boar:latest fabioleitao/data_boar:latest

# Login (use seu usuário Docker Hub e Access Token como senha)
docker login
# Username: fabioleitao
# Password: <sua senha ou Access Token>

# Push
docker push fabioleitao/data_boar:latest
```

Opcional: enviar uma tag de versão (ex.: 1.7.3):

```powershell
docker tag data_boar:latest fabioleitao/data_boar:1.7.3
docker push fabioleitao/data_boar:1.7.3
```

Login não interativo com token:

```powershell
echo YOUR_ACCESS_TOKEN | docker login -u fabioleitao --password-stdin
docker push fabioleitao/data_boar:latest
```

---

## 4. Implantar um container local (API web)

O config fica em `data/config.yaml`. Execute:

```powershell
cd c:\Users\<username>\Documents\dev\data-boar

docker run -d --name data-boar-audit `
  -p 8088:8088 `
  -v "${PWD}/data:/data" `
  -e CONFIG_PATH=/data/config.yaml `
  data_boar:latest
```

Ou com **Docker Compose** (alternativa ao run com container único):

```powershell
copy deploy\docker-compose.override.example.yml deploy\docker-compose.override.yml
docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.override.yml up -d
```

(Garanta que `./data/config.yaml` exista; o override monta `./data` em `/data`.) Para **Docker Swarm** ou **Kubernetes**, veja [deploy/DEPLOY.md](deploy/DEPLOY.md) ([pt-BR](deploy/DEPLOY.pt_BR.md)).

---

## 5. Acesso

- **Dashboard:** <http://localhost:8088/>
- **Documentação da API:** <http://localhost:8088/docs>
- **Health:** <http://localhost:8088/health>

---

## 6. Parar e remover

```powershell
docker stop data-boar-audit
docker rm data-boar-audit
```

Ou com Compose: `docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.override.yml down`

---

## 7. Smoke local: higiene de containers (manter poucos)

Execuções repetidas de `docker run` / `docker build` em testes de smoke ou no homelab deixam **vários containers parados** no Docker Desktop. Isso atrapalha portas, volumes e saber qual imagem está “ativa”.

## Convenção do projeto

1. Preferir **um** container principal local (ex.: `--name data-boar-audit`) ou **uma** stack Compose.
1. No máximo **dois** containers com nome **só** quando houver **A/B** explícito (ex.: `fabioleitao/data_boar:latest` vs `data_boar:lab` construída localmente). Evitar containers anônimos “soltos”.
1. Ao terminar um teste descartável, **parar e remover** os extras: `docker rm -f <nome>` (após confirmar que essa instância não é mais necessária).

## Listar candidatos a remoção

```powershell
docker ps -a --filter "name=data-boar"
```

1. **Tags de imagem (evitar explosão):** **Não** é necessário criar **uma tag nova a cada smoke** (ex.: `data_boar:smoke-post93`). Cada tag extra dificulta ver o que importa e pode manter **muitas camadas grandes** até você fazer prune. Prefira **uma tag local mutável** que você **sobrescreve** a cada build, ex.: **`docker build -t data_boar:lab .`** — alinhado ao passo 1.3 de [HOMELAB_VALIDATION.pt_BR.md](ops/HOMELAB_VALIDATION.pt_BR.md). Só use **segunda** tag para A/B de verdade (ex.: `data_boar:lab-a` vs `data_boar:lab-b`, ou `fabioleitao/data_boar:latest` **pulled** vs `data_boar:lab` local).
1. **Disco / retenção:** Depois do smoke, mantenha cerca de **duas** imagens úteis localmente (ex.: Hub **`latest`** + **`data_boar:lab`**, ou `latest` + um semver anterior). **Remova** tags de smoke antigas e use **`docker image prune`** / **`docker builder prune`** quando precisar — ver [BRANCH_AND_DOCKER_CLEANUP.pt_BR.md](ops/BRANCH_AND_DOCKER_CLEANUP.pt_BR.md) §3.

1. **Automação (Windows):** Na raiz do repo, **`.\scripts\docker-hub-pull.ps1`** (pull `latest` + semver + patch anterior), **`.\scripts\docker-lab-build.ps1`** (build **`data_boar:lab`**, opcional **`lab-prev`** / **`smoke`**), **`.\scripts\docker-prune-local.ps1 -WhatIf`** e depois sem `-WhatIf` para remover tags extra. Detalhes: [scripts/docker/README.md](../scripts/docker/README.md).

Orientação para agentes/automação: **`.cursor/rules/docker-local-smoke-cleanup.mdc`** e **`.cursor/skills/docker-smoke-container-hygiene/SKILL.md`** (opcional para quem usa Cursor).

Ver também: [HOMELAB_VALIDATION.pt_BR.md](ops/HOMELAB_VALIDATION.pt_BR.md) (baseline do lab usa `docker run --rm` quando possível).
