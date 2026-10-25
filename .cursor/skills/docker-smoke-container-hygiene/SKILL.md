---
name: docker-smoke-container-hygiene
description: >-
  After local Data Boar Docker smoke tests, keep at most one or two named containers,
  reuse one local image tag (e.g. data_boar:lab) instead of many smoke-* tags, prune old
  images, and document cleanup. Use when creating containers, running lab validation,
  or closing a session that used docker run/compose/build for data_boar.
---

# Docker smoke container hygiene (Data Boar)

## Stable release publish (Hub) — non-optional pieces

When the operator (or **`release-ritual`**) is cutting a **published** **`X.Y.Z`** image for **Docker Hub**:

1. **Disk:** Confirm free space on the volume Docker uses on the **primary dev PC** before **`docker-lab-build.ps1`** (full disk ⇒ broken builds).
2. **Smoke before push:** After **`.\scripts\docker-lab-build.ps1`**, run at least one **`docker run --rm`** against **`data_boar:lab`** — **`python main.py --version`** or **`/health`** per **`docs/DOCKER_SETUP.md`** §7. **Do not** advise **`docker push`** to **`fabioleitao/data_boar`** if smoke failed (unless CI-only waiver is explicit).
3. **After push:** **`.\scripts\docker-prune-local.ps1 -WhatIf`** then without **`-WhatIf`** on the **same** machine — see **`docs/ops/DOCKER_IMAGE_RELEASE_ORDER.md`**.

Authoritative order: **`.cursor/rules/release-publish-sequencing.mdc`** (**situational** — **`release-ritual`** / **`@release-publish-sequencing.mdc`**); this skill and **`docker-local-smoke-cleanup.mdc`** stay **always-on** for hygiene.

## When to use

- You (or the operator) ran `docker build`, `docker run`, or `docker compose` for **Data Boar** (`data_boar` image, `data-boar-*` names).
- The session is ending or you are about to open a PR after smoke verification.
- Docker Desktop is accumulating stopped containers from repeated tests, **or** many local `data_boar:*` / `fabioleitao/data_boar:*` image tags after smoke runs.

## Instructions — containers

1. **Inventory** local Data Boar-related containers (name filter is enough for most cases):
   - `docker ps -a` and look for `data-boar`, `data_boar`, or compose project service names from `deploy/`.
1. **Retention policy**
   - **Normal:** keep **one** container (or one compose stack) for day-to-day dev.
   - **A/B or regression:** keep **at most two** intentionally named containers (e.g. different tags or configs). Anything else is **throwaway**.
1. **Cleanup suggestion** (confirm with the operator before `rm -f`):
   - Stop: `docker stop <name>`
   - Remove: `docker rm <name>`
   - Compose: `docker compose -f deploy/docker-compose.yml … down` (add override file if used).
1. **Document** in the session or PR description if smoke was run and **which** container name/tag was kept, so the next run does not spawn duplicates.
1. **Agents:** do not delete containers autonomously; **propose** commands and remind the operator to keep only 1–2 instances unless A/B is required.

## Instructions — images and disk (homelab)

Smoke tests **do not** require a **new Docker tag every time**. Tags like `data_boar:smoke-post93`, `data_boar:smoke-foo` accumulate and waste **disk** (many digests/layers stay referenced until pruned).

1. **Default build command for local smoke:** `docker build -t data_boar:lab -f Dockerfile .` — **reuse `data_boar:lab`** and overwrite it on each build (same idea as [docs/ops/HOMELAB_VALIDATION.md](../../../docs/ops/HOMELAB_VALIDATION.md) step 1.3).
1. **Second tag only when needed:** e.g. true A/B (`data_boar:lab-a` vs `data_boar:lab-b`) or compare **pulled** `fabioleitao/data_boar:latest` vs local `data_boar:lab`.
1. **Retention:** keep roughly **two** useful lines locally (e.g. Hub `latest` + `data_boar:lab`, or `latest` + one older semver). Remove stale tags: `docker rmi data_boar:OLD_TAG`, then `docker image prune -f` and optionally `docker builder prune -f` — see [docs/ops/BRANCH_AND_DOCKER_CLEANUP.md](../../../docs/ops/BRANCH_AND_DOCKER_CLEANUP.md) §4.
1. **Scripts (Windows, repo root):** [scripts/docker-hub-pull.ps1](../../../scripts/docker-hub-pull.ps1) (pull Hub tags), [scripts/docker-lab-build.ps1](../../../scripts/docker-lab-build.ps1) (build `data_boar:lab` + optional `lab-prev`/`smoke`), [scripts/docker-prune-local.ps1](../../../scripts/docker-prune-local.ps1) `-WhatIf` first — see [scripts/docker/README.md](../../../scripts/docker/README.md).
1. **Agents:** propose list/prune commands; do not run destructive `docker rmi` / `prune` without operator confirmation.

## Rationale

Stale containers confuse port mappings (`8088`), volume mounts, and Scout/quickview workflows; **too many image tags** waste disk on homelab hosts. Policy matches [docs/DOCKER_SETUP.md](../../../docs/DOCKER_SETUP.md) §7, [docs/ops/BRANCH_AND_DOCKER_CLEANUP.md](../../../docs/ops/BRANCH_AND_DOCKER_CLEANUP.md) §4, and [docs/ops/HOMELAB_VALIDATION.md](../../../docs/ops/HOMELAB_VALIDATION.md).
