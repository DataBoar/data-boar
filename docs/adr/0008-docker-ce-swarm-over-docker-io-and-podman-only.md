# ADR 0008: Docker CE (official repo) + Compose plugin + Swarm as primary lab container runtime

**Status:** Accepted
**Date:** 2026-04-03
**Authors:** Fabio Leitao

---

## Context

The lab-op environment (ThinkPad LAB-NODE-01 running LMDE 7 / Debian Trixie) needs a container runtime to:

1. Build and run the **Data Boar** Docker image locally during development.
2. Test multi-service compositions (detector + database + dashboard) via `docker compose`.
3. Optionally test **Swarm stack deployments** (`docker stack deploy`) as a lightweight
   simulation of multi-node orchestration without full Kubernetes overhead.
4. Eventually hand off reproducible container procedures to collaborators (team members).

Three options were evaluated:

| Option | Pros | Cons |
|---|---|---|
| **`docker.io` (Debian apt)** | Simple install, no extra repo | Lags Docker Inc releases by months; no compose plugin |
| **`docker-ce` (official Docker repo)** | Latest stable, compose plugin included, buildx included | Extra GPG/repo step |
| **Podman only** | Rootless, daemon-free, OCI-compatible | `docker compose` compatibility requires `podman-compose` shim; some edge cases; team unfamiliar |
| **k3s / k8s** | Full orchestration | 300–500 MB RAM idle; heavy for a developer workstation; overkill for single-service testing |

The project team (small, mostly Linux + Docker background) already has existing `Dockerfile` and
`docker-compose.yml` infrastructure targeting Docker semantics. Swarm is used in the lab to test
`docker stack deploy` workflows and overlay networks without spinning up full Kubernetes.

## Decision

1. **Primary runtime:** install `docker-ce` from the **official Docker apt repository** (`download.docker.com/linux/debian`)
   with `docker-compose-plugin` and `docker-buildx-plugin` — not `docker.io` from Debian repositories.
2. **Compose:** use `docker compose` (plugin) as the canonical compose interface; `docker-compose` (v1 Python) is not used.
3. **Swarm:** **on by default** in **`lab-node-01-baseline.yml`** and **`lab-node-01_docker_ce`** defaults (`lab-node-01_docker_swarm_init: true`)
   so **`docker service`** / **`docker stack deploy`** work on a single-node manager without manual **`docker swarm init`**.
   Set **`lab-node-01_docker_swarm_init: false`** in inventory on hosts that must stay in non-Swarm mode only.
4. **Podman:** installed alongside Docker as a secondary, rootless alternative via the `lab-node-01_podman` Ansible role,
   but not aliased to `docker` by default — `lab-node-01_podman_docker_alias: false`.
5. **k3s:** opt-in only via `lab-node-01_k3s` Ansible role (`lab-node-01_install_k3s: false`). Not recommended on the LAB-NODE-01
   unless the goal is to test Kubernetes-specific workflows (Helm charts, NetworkPolicy, namespaces).
6. **daemon.json baseline:** `live-restore: true`, `overlay2` storage driver, custom address pool
   (`172.30.0.0/16`) to avoid collision with lab LAN (`10.0.x.x`), and log rotation (20 MB × 5 files).

## Consequences

- **Positive:** Consistent `docker compose` interface for all team members; latest engine features; compose-plugin
  replaces the deprecated Python `docker-compose` without a separate install step; Swarm initialized by default for service/stack workflows (opt-out per host).
- **Positive:** Podman provides an escape hatch for rootless scenarios (CI, restricted environments) without
  losing Docker compatibility for the main development loop.
- **Negative:** Requires adding the Docker GPG key and apt source — one extra step in fresh installs (automated
  by the `lab-node-01_docker_ce` Ansible role).
- **Negative:** Two container runtimes in parallel (Docker + Podman) could create confusion if a developer
  runs `podman` commands and then inspects with `docker ps`. Mitigated by not setting the `docker` alias.
- **Watch:** `docker.io` vs `docker-ce` package conflicts — if both are installed, the Ansible role should
  detect and prefer `docker-ce`. A future task may add an explicit conflict guard.
- **LMDE:** Mint/LMDE **release codenames** (**`gigi`**, **`faye`**) differ from **Debian** codenames; the **`lab-node-01_docker_ce`** role maps them when adding **`download.docker.com/linux/debian`** (see **`lab-node-01_docker_debian_codename_map`**).
- **Socket access:** Role **`lab-node-01_operator_supplementary_groups`** adds **`ansible_user`** to **`docker`** and other workstation groups (**`wireshark`**, **`dialout`**, **`plugdev`**, **`systemd-journal`**) after **`lab-node-01_docker_ce`**; install **`tshark`** for non-root capture (operator must refresh the session for groups to apply).

## References

- [docs/ops/LMDE7_LAB-NODE-01_DEVELOPER_SETUP.pt_BR.md](../ops/LMDE7_LAB-NODE-01_DEVELOPER_SETUP.pt_BR.md) §7.1–§7.3
- [ops/automation/ansible/roles/lab-node-01_docker_ce/](../../ops/automation/ansible/roles/lab-node-01_docker_ce/)
- [ops/automation/ansible/roles/lab-node-01_podman/](../../ops/automation/ansible/roles/lab-node-01_podman/)
- [ops/automation/ansible/roles/lab-node-01_k3s/](../../ops/automation/ansible/roles/lab-node-01_k3s/)
- [ops/automation/ansible/playbooks/lab-node-01-baseline.yml](../../ops/automation/ansible/playbooks/lab-node-01-baseline.yml)
