# Remotes e origin (data-boar)

**English:** [REMOTES_AND_ORIGIN.md](REMOTES_AND_ORIGIN.md)

Este repositório usa **data-boar** como único destino de push e PR. **Nome do produto:** **Data Boar**. Um segundo remote opcional pode ainda usar um **rótulo histórico longo** no `.git/config` apontando para URL arquivada no GitHub — é **conveniência Git** (fetch só de histórico), não identidade pública do produto.

Nota: o path antigo do GitHub `FabioLeitao/data-boar` ainda redireciona para o canônico `DataBoar/data-boar`.

O que segue fica no `.git/config` local e pode ser conferido ou alterado pelo terminal.

## Verificar os remotes atuais

Na raiz do repositório:

```bash
# Listar todos os remotes e suas URLs (fetch e push)
git remote -v
```

Você deve ver:

- **origin** → `git@github.com:DataBoar/data-boar.git` (fetch e push)
- **python3-lgpd-crawler-legacy-and-history-only** → `git@github.com:FabioLeitao/python3-lgpd-crawler.git` (apenas fetch); a URL de push é `no-push`, então o push está desabilitado

## Alterar para onde o `origin` aponta (manual)

Se precisar definir ou mudar a URL de destino pelo terminal:

```bash
# Definir origin para data-boar (SSH)
git remote set-url origin git@github.com:DataBoar/data-boar.git

# Ou com HTTPS:
# git remote set-url origin https://github.com/DataBoar/data-boar.git

# Confirmar
git remote -v
```

Não existe `git switch` para remotes; use `git remote set-url origin <url>` para mudar o destino.

## Comportamento de push e PR

- **Push padrão:** `git push` usa o **remote de rastreamento** do branch atual. O branch que você usa para trabalho novo (ex.: `2026-03-14-3i1y`) está configurado com `remote = origin`, então `git push` vai para **data-boar**.
- **Push explícito:** Para sempre enviar um branch para data-boar, independente do remote configurado:

  `git push origin <nome-do-branch>`

- **python3-lgpd-crawler-legacy-and-history-only:** O antigo repositório python3-lgpd-crawler; mantido só como histórico legado e para fetch. Não faça push para ele; o push está desabilitado via `pushurl = no-push`.

## Upstream dos branches

Alguns branches antigos podem ainda ter `remote = python3-lgpd-crawler-legacy-and-history-only` como upstream (de antes da mudança para data-boar). Isso só afeta `git push` / `git pull` quando você está nesses branches e roda sem especificar o remote. Para enviar um desses branches para data-boar:

```bash
git push origin <nome-do-branch>
```

Para definir o upstream do branch como origin (para que `git push` use data-boar no futuro):

```bash
git branch --set-upstream-to=origin/<nome-do-branch> <nome-do-branch>
```

## Verificar se o remote legado tem commits que não estão em data-boar

Para saber se algum commit foi enviado só para o repositório antigo (e está faltando no data-boar):

```bash
git fetch origin
git fetch python3-lgpd-crawler-legacy-and-history-only

# Commits no main do repositório antigo que NÃO estão no main do data-boar
git log origin/main..python3-lgpd-crawler-legacy-and-history-only/main --oneline

# Commits no main do data-boar que NÃO estão no repositório antigo (esperado: seu trabalho mais recente)
git log python3-lgpd-crawler-legacy-and-history-only/main..origin/main --oneline
```

Se o primeiro comando listar commits, eles existem apenas no repositório antigo. Você pode deixá-los só como histórico legado ou trazer alterações específicas para o data-boar (ex.: cherry-pick ou merge) se precisar.

**Ver também:** [espelho só leitura do GitHub no GitLab](GITLAB_GITHUB_MIRROR.pt_BR.md) — o GitLab **não** é um segundo `origin` para PR; espelha o repositório canônico no GitHub.

**Índice da documentação:** [README.md](../README.md) · [README.pt_BR.md](../README.pt_BR.md).
