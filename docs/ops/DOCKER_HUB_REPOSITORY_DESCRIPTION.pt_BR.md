# Docker Hub — descrição do repositório (fonte para copiar/colar)

**English (canônico):** [DOCKER_HUB_REPOSITORY_DESCRIPTION.md](DOCKER_HUB_REPOSITORY_DESCRIPTION.md)

**Objetivo:** O texto curto e a descrição longa no [Docker Hub](https://hub.docker.com/r/fabioleitao/data_boar) **não** ficam versionados no Git. O documento em inglês [DOCKER_HUB_REPOSITORY_DESCRIPTION.md](DOCKER_HUB_REPOSITORY_DESCRIPTION.md) é a **fonte** para colar após cada release **estável** (**`X.Y.Z`** final), alinhada a **`pyproject.toml`** e a **`docs/releases/`**. Também use-o quando publicar **tags só de imagem** que clientes vão puxar (ex.: **`1.7.3`**) ou apagar tags no Hub — a UI **não** segue o Git; substitua a **Full description inteira** na mesma sessão do push.

**Quando atualizar:** Logo após **`docker push`** / ritual podman de **`fabioleitao/data_boar:<semver>`** e **`latest`** (inclui **`.postN`**). No Hub: **Repository → General → Edit** — cole **Short** + **Full** inteiro do documento em inglês (substitua a descrição longa por completo). Atualize a versão no EN **antes** de colar. Ritual: [DOCKER_IMAGE_RELEASE_ORDER.pt_BR.md](DOCKER_IMAGE_RELEASE_ORDER.pt_BR.md) **passo 9**.

**Checklist:** Veja **Maintainer checklist** no documento em inglês (inclui **copyright/mantenedor** no **Full** — link opcional ao **LinkedIn** no editor do Hub). **Pushes só de imagem `-beta` / `-rc`** não exigem atualizar o texto público do repositório salvo pedido explícito. Mantenha **[PUBLISHED_SYNC.md](today-mode/PUBLISHED_SYNC.md)** coerente com o que os clientes podem puxar do Hub.

**Versão em todos os artefatos:** [VERSIONING.md](../VERSIONING.md) (seção **6. Distribuição…**, EN) — Docker Hub, `PUBLISHED_SYNC`, TECH_GUIDE, rascunhos sociais.
