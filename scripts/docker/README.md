# Docker helper scripts (Data Boar)

PowerShell automation for **local lab builds**, **Docker Hub pulls**, and **tag pruning** — aligned with [docs/DOCKER_SETUP.md](../../docs/DOCKER_SETUP.md) §7 and [docs/ops/BRANCH_AND_DOCKER_CLEANUP.md](../../docs/ops/BRANCH_AND_DOCKER_CLEANUP.md) §4.

All scripts assume the **repository root** is the parent of `scripts/` (run them as `.\scripts\<name>.ps1` from the repo root, or `cd` to root first).

| Script                                                                 | Purpose                                                                                                                                             |
| ------                                                                 | -------                                                                                                                                             |
| [../docker-hub-pull.ps1](../docker-hub-pull.ps1)                       | `docker pull` **fabioleitao/data_boar:latest**, **:\<semver from pyproject.toml\>**, and **previous patch** (e.g. 1.7.3 → 1.7.2+safe) for cache and A/B. |
| [../docker-lab-build.ps1](../docker-lab-build.ps1)                     | `docker build -t data_boar:lab`; optionally re-tags old **lab** → **lab-prev** before rebuild; optional **-TagSmoke** for A/B.                      |
| [../docker-prune-local.ps1](../docker-prune-local.ps1)                 | `docker rmi` extra tags on **fabioleitao/data_boar** and **data_boar** repos; keeps a small allowlist. Use **-WhatIf** first.                       |
| [../docker-scout-critical-gate.ps1](../docker-scout-critical-gate.ps1) | Scout CRITICAL gate: fails only when a **fixed** CRITICAL exists; warns/pass on upstream **not fixed** CVEs.                                        |
| [../grype-image-gate.sh](../grype-image-gate.sh) / [../grype-image-gate.ps1](../grype-image-gate.ps1) | Grype gate (#1028): **`--fail-on high --only-fixed`** + repo [`.grype.yaml`](../../.grype.yaml) VEX; actionable High/Critical only. |
| [docker-image-smoke.sh](docker-image-smoke.sh) / [docker-image-smoke.ps1](docker-image-smoke.ps1) | Post-build smoke (#1028): public version, no octet leak, `boar_fast_filter` import, **TLS** probe (`httpx` → `https://example.com`). |
| [collect-runtime-rootfs.sh](collect-runtime-rootfs.sh) | Bundle `/usr/local`, DB/TLS `.so`, CA certs for distroless runtime (#1028). |
| [DataBoarDockerCommon.ps1](DataBoarDockerCommon.ps1)                   | Shared helpers (dot-sourced only).                                                                                                                  |

## Typical flows

### After merging Dockerfile / before publishing

1. `.\scripts\docker-lab-build.ps1` — refresh **data_boar:lab**; smoke with `docker run --rm` (see DOCKER_SETUP).
1. `.\scripts\docker-image-smoke.ps1` (or `docker-image-smoke.sh`) — version/octet/TLS/PyO3 smoke (#1028).
1. `.\scripts\grype-image-gate.ps1 -Image data_boar:lab` — **grype** actionable High+ only (`--only-fixed` + `.grype.yaml`).
1. When satisfied, build and push to Hub (manual or CI) with your release tags.
1. `.\scripts\docker-scout-critical-gate.ps1 -Image fabioleitao/data_boar:latest` — detect CRITICALs with fix available vs "not fixed" upstream.
1. `.\scripts\docker-hub-pull.ps1` — refresh local copies of **latest** + semver + previous patch.
1. `.\scripts\docker-prune-local.ps1 -WhatIf` then `.\scripts\docker-prune-local.ps1` — drop stray **maint-***, **scout-***, etc.

### A/B (Hub vs local)

1. `.\scripts\docker-hub-pull.ps1`
1. `.\scripts\docker-lab-build.ps1 -TagSmoke` — produces **data_boar:lab** and **data_boar:smoke** (same digest); or compare **fabioleitao/data_boar:latest** vs **data_boar:lab** on different ports.

### Parameters

- **docker-hub-pull:** `-SkipPrevious`, `-PreviousVersion "1.6.1"` if auto patch−1 is wrong.
- **docker-lab-build:** `-NoCache`, `-SkipLabPrev`, `-TagSmoke`.
- **docker-prune-local:** `-WhatIf`, `-KeepSmoke:$false`, `-KeepLabPrev:$false`.
- **docker-scout-critical-gate:** `-Image <repo:tag>`, `-FailOnAnyCritical` (strict mode).

### Builder cache

Large, separate from image tags: `docker builder prune -f` — not wrapped here; use when disk is tight.
