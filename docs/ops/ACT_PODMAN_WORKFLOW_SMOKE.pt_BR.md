# Smoke opcional de GitHub Actions com act + Podman

**English:** [ACT_PODMAN_WORKFLOW_SMOKE.md](ACT_PODMAN_WORKFLOW_SMOKE.md)

**Relacionado:** [QUALITY_WORKFLOW_RECOMMENDATIONS.pt_BR.md](../QUALITY_WORKFLOW_RECOMMENDATIONS.pt_BR.md) · [TOKEN_AWARE_SCRIPTS_HUB.pt_BR.md](TOKEN_AWARE_SCRIPTS_HUB.pt_BR.md) · [SCRIPTS_CROSS_PLATFORM_PAIRING.pt_BR.md](SCRIPTS_CROSS_PLATFORM_PAIRING.pt_BR.md)

Use isto quando um PR altera **`.github/workflows/*.yml`** e você quer exercitar um **job real** na estação **antes** do push. **Não** substitui o guard estático de `run:` folded (#1918) e **não** entra em **`./scripts/check-all.sh`** / **`.\scripts\check-all.ps1`**.

## Camada 1 (sempre — barata)

`uv run python scripts/workflow_run_scalar_guard.py` percorre **`.github/workflows/`** e falha se um `run:` usa estilo folded do YAML (`>` / `>-` / `>+`) **e** contém barra invertida. Essa combinação colapsa `pip … --require-hashes \` + `-r arquivo` em `Invalid requirement: '-r'` (#1904, #1906). O hook de pre-commit **`workflow-run-scalar-guard`** e o **`check-all`** já o executam. Prefira bloco literal (`|`) para continuação de linha no shell.

## Camada 2 (manual — [nektos/act](https://github.com/nektos/act))

A estação Linux primary pode ter **Podman** sem daemon Docker. O `act` fala com o motor via **`DOCKER_HOST`**.

1. Ative o socket Podman do usuário (uma vez por sessão / linger, conforme a política local):

   ```bash
   systemctl --user enable --now podman.socket
   export DOCKER_HOST="unix:///run/user/$(id -u)/podman/podman.sock"
   ```

1. Instale o `act` pela distro ou pela documentação upstream (não pinamos o nome do pacote do host aqui).

1. Na **raiz do repositório**, rode um job (exemplo — troque o workflow e o nome do job):

   ```bash
   act pull_request -W .github/workflows/ci.yml -j ansible-syntax
   ```

O `act` baixa uma **imagem de runner compatível com o GitHub**. É mais lento e pesado que o guard em Python. Use em **PR que toca workflow**, não em todo commit.

**Não** coloque `act` no pre-commit, no **`check-all`** nem no CI. O GitHub Actions continua sendo a prova de merge para jobs que precisam de runner hospedado, secrets ou matriz de SO.
