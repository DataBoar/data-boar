# Sync do `requirements.txt` do Dependabot sob `required_signatures`

**English:** [DEPENDABOT_REQUIREMENTS_SYNC.md](DEPENDABOT_REQUIREMENTS_SYNC.md)

Issue GitHub [#1419](https://github.com/DataBoar/data-boar/issues/1419). Relacionado: [ADR 0044](../adr/ADR-0044-dependabot-uv-ecosystem-for-pyproject-lock-closure.md), [BRANCH_PROTECTION.pt_BR.md](BRANCH_PROTECTION.pt_BR.md).

## Problema

PRs do Dependabot atualizam `uv.lock` (e às vezes `pyproject.toml`). O [ADR 0030](../adr/ADR-0030-python-dependency-update-closure-single-pass.md) exige `requirements.txt` alinhado (`uv export --frozen --no-emit-project`). O `pylock.toml` também precisa ficar alinhado (`uv export --format pylock.toml --frozen --all-extras --all-groups --output-file pylock.toml`): o OSV scanner do CI lê esse arquivo, então um export desatualizado varre versões que o projeto não instala mais ([#1937](https://github.com/DataBoar/data-boar/issues/1937)). O `tests/test_dependency_artifacts_sync.py` falha quando qualquer um dos dois fica desalinhado.

O workflow [`.github/workflows/dependabot-sync.yml`](../../.github/workflows/dependabot-sync.yml) regenera o export nesses PRs. O ruleset **`restriction baseline`** impõe **`required_signatures`** **sem bypass** para o bot do GitHub Actions. `git push` **sem assinatura** a partir do Actions é **rejeitado** — comportamento esperado.

## Comportamento atual do workflow

| Condição | Comportamento |
| --- | --- |
| Sem drift em `requirements.txt` / `pylock.toml` | Job verde (no-op). |
| Drift, **sem** secrets de assinatura | **Comentário** no PR com ritual de commit assinado, **artifact** (`requirements-txt-pr-<N>`, com os dois exports), job **falha** (Slack se configurado). **Sem push unsigned.** |
| Drift, secrets configurados | Abre **PR filho assinado** na branch do Dependabot (`ci/requirements-sync-pr-<N>`). Operador mergeia o filho na branch do Dependabot e depois o bump. |

Script: [`scripts/ci_dependabot_requirements_sync.sh`](../../scripts/ci_dependabot_requirements_sync.sh).

**Anti pwn-request:** o workflow faz checkout do script na **ref base confiável** (`pull_request.base.ref`) e só `uv.lock` / `pyproject.toml` / `requirements.txt` / `pylock.toml` no **head não confiável** da PR. O job exige `head.ref` no padrão `dependabot/*`. Nunca executar scripts do branch do Dependabot com `contents: write`, `pull-requests: write` ou secrets de assinatura.

## Handoff do operador (padrão — sem secrets)

Quando o job de sync falha num PR do Dependabot:

1. Leia o comentário do bot (comandos `git` exatos).
2. Opcional: baixe `requirements.txt` e `pylock.toml` do artifact da run que falhou.
3. Na workstation: fetch da branch do Dependabot, `uv export --frozen --no-emit-project -o requirements.txt` e `uv export --format pylock.toml --frozen --all-extras --all-groups --output-file pylock.toml`, **`git commit -S`**, push.
4. Ou supersedea o PR do Dependabot com branch assinada do mantenedor ([CONTRIBUTING.pt_BR.md](../../CONTRIBUTING.pt_BR.md)).

## Automação opcional — assinatura SSH (barra alta)

Para o caminho de **PR filho assinado** sem afrouxar o ruleset:

1. Usuário **máquina** no GitHub (não bypass de ruleset).
2. Chave **SSH de assinatura** registrada nesse usuário.
3. **Secrets** do repositório: `DEPENDABOT_SYNC_SSH_SIGNING_KEY`, `DEPENDABOT_SYNC_SSH_ALLOWED_SIGNERS` (linha `allowed_signers`).
4. **Variáveis** opcionais: `DEPENDABOT_SYNC_GIT_USER_NAME`, `DEPENDABOT_SYNC_GIT_USER_EMAIL`.
5. Validar num PR de teste do Dependabot.

**Fora de escopo:** bypass de ruleset, desligar `required_signatures`, push unsigned “temporário”.
