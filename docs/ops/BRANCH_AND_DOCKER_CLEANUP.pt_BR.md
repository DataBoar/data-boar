# Limpeza de branches Git e imagens Docker (fluxo seguro)

**English:** [BRANCH_AND_DOCKER_CLEANUP.md](BRANCH_AND_DOCKER_CLEANUP.md)

**Objetivo:** Liberar espaço e reduzir ruído **sem** perder histórico que já está no `main`, e sem apagar trabalho não integrado. **Apagar uma branch não apaga commits** que já foram mergeados no `main` — eles permanecem no histórico. Só há risco para commits **exclusivos** no topo de uma branch **não mergeada**, se você apagá-la sem backup.

**Repositórios:** O trabalho cotidiano é no **`DataBoar/data-boar`** (`origin`). O remote **`python3-lgpd-crawler-legacy-and-history-only`** é legado; trate as branches dele separadamente.

---

## 1. Git: atualizar e ver o que é seguro apagar localmente

Na raiz do repositório:

```powershell
git fetch origin --prune
git branch --show-current
git branch --merged origin/main
git branch --no-merged origin/main
```

## Regras:

- **Não apague** branches listadas em `--no-merged` sem revisar (work in progress ou abandonado de propósito).
- **Não apague** a branch em que você está; mude antes: `git checkout main`.
- Alinhe o `main` antes: `git pull origin main`.

## Apagar uma branch local mergeada:

```powershell
git branch -d nome-da-branch
```

**Forçar** (só se aceitar perder commits não mergeados):

```powershell
git branch -D nome-da-branch
```

**PR mergeado com squash:** Depois de um **squash merge** no `main`, a branch antiga pode continuar localmente com SHAs diferentes dos do `main` (`git branch --merged` pode não listá-la). Se o PR já está mergeado no GitHub e você não precisa do nome da branch, apague pelo nome (exemplo após o PR **#93**): `git branch -D pr/docker-scout-high-slice` — ver [MAINTENANCE_FRONT_OF_WORK.md](../plans/MAINTENANCE_FRONT_OF_WORK.md) § Slice S4 *Quick housekeeping*.

---

## 2. GitHub (`data-boar`): branches remotas obsoletas

```powershell
gh api repos/DataBoar/data-boar/branches --paginate -q ".[].name"
gh pr list --repo DataBoar/data-boar --state open
git fetch origin
git log origin/main..origin/NOME-DA-BRANCH
```

- Log **vazio** → em geral seguro apagar a branch remota (histórico já no `main`).
- Log **não vazio** → há commits únicos; faça merge ou cherry-pick antes, ou abandone de propósito.

## Apagar branch remota:

```powershell
git push origin --delete NOME-DA-BRANCH
```

---

## 3. Docker: política de retenção (Data Boar)

Manter cerca de **dois** **digests** de imagem localmente, por exemplo:

1. `fabioleitao/data_boar:latest` ou a tag semver em uso (ex.: `1.6.2`).
1. **Uma versão anterior** para comparação ou rollback rápido.

**Smokes / lab:** Testes de smoke **não** precisam de uma **tag nova a cada execução** (`data_boar:smoke-93`, …). Isso **ocupa disco** à toa. Prefira **uma** tag sobrescrita — **`docker build -t data_boar:lab .`** (igual ao passo 1.3 de [HOMELAB_VALIDATION.pt_BR.md](HOMELAB_VALIDATION.pt_BR.md)) — e apague tags experimentais antigas quando terminar.

Versões mais antigas podem ser removidas; use `docker pull` no Hub quando precisar de histórico.

**Automação:** Na raiz do repo, **`.\scripts\docker-hub-pull.ps1`**, **`.\scripts\docker-lab-build.ps1`**, **`.\scripts\docker-prune-local.ps1 -WhatIf`** — ver [scripts/docker/README.md](../../scripts/docker/README.md).

```powershell
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.CreatedSince}}\t{{.Size}}" | Select-String -Pattern "data_boar|fabioleitao/data_boar"
docker rmi fabioleitao/data_boar:TAG_ANTIGA
docker image prune -f
docker builder prune -f
```

---

## 4. Ordem recomendada

1. `git fetch origin --prune` e `git pull` no `main`.
1. Revisar `git branch --no-merged origin/main`.
1. Apagar branches **locais** já mergeadas (`git branch -d …`).
1. No GitHub, apagar branches **remotas** mergeadas e sem uso.
1. Docker: manter **latest + uma versão anterior** → `docker rmi` / `prune`.

---

## 5. Remote legado apenas (`python3-lgpd-crawler-legacy-and-history-only`)

**Backlog / não bloqueante.** Push cotidiano só em **`data-boar`** (`origin`). O remote extra ([REMOTES_AND_ORIGIN.md](REMOTES_AND_ORIGIN.md)) aponta para um repositório GitHub **arquivado** (só fetch, sem push).

### Objetivos

1. Branches **locais** que ainda apontam para o remote legado: `git branch -vv` e alinhar ou apagar.
1. **Não fazer push** para o remoto legado a partir deste clone (política intencional).
1. Repositório antigo no GitHub: opcional **arquivar** + README apontando para **data-boar**.

---

## 6. Documentos relacionados

- [COMMIT_AND_PR.md](COMMIT_AND_PR.md) · [REMOTES_AND_ORIGIN.md](REMOTES_AND_ORIGIN.md) · [DOCKER_SETUP.md](../DOCKER_SETUP.md) · [HOMELAB_VALIDATION.md](HOMELAB_VALIDATION.md) · [PLANS_TODO.md](../plans/PLANS_TODO.md)
- [OPERATOR_NOTIFICATION_CHANNELS.md](OPERATOR_NOTIFICATION_CHANNELS.md) — alertas multi-canal (GitHub, Slack, Telegram, Signal).
