# Lab-op: minimal container stack — single official line

**Português (Brasil):** [LAB_OP_MINIMAL_CONTAINER_STACK.pt_BR.md](LAB_OP_MINIMAL_CONTAINER_STACK.pt_BR.md)

**Purpose:** Avoid **rework** and **stack sprawl** on the **lab-op** host by locking **one** minimal combination first. **Other** orchestrators (Nomad, additional Kubernetes distros, duplicate compose paths) stay **out of scope** until this baseline is **stable** and documented in **`docs/private/homelab/`** (gitignored).

**Scope:** Linux server / workstation used as **integration lab** (SSH from operator). **Docker Desktop + Kubernetes** on a **Windows dev laptop** is a **separate** dev convenience — see §4.

---

## 1. Official minimal combination (lab-op)

| Layer                        | Choice     | Role                                                                                                                                                                     |
| -----                        | ------     | ----                                                                                                                                                                     |
| **OCI runtime / build**      | **Podman** | Rootless-friendly builds, `podman run`, optional `podman play kube`; aligns with security posture (no root daemon required for local runs).                              |
| **Kubernetes (single-node)** | **k3s**    | Lightweight, one binary, **kubectl** included, enough to validate **`deploy/kubernetes/`**-style manifests and ingress patterns without operating a full distro cluster. |

**Do not add** a second cluster manager on the same host (e.g. kind + k3s + minikube) until one path is **smoke-tested** with this repo’s deploy assets.

---

## 2. Concrete install order (Debian / Ubuntu / LMDE — use `sudo` as needed)

### 2.1 Podman

```bash
sudo apt-get update
sudo apt-get install -y podman
podman --version
podman info
```

Optional (rootless default for user): follow **Podman** upstream docs for `subuid`/`subgid` if you want fully rootless images; for lab speed, the distro package defaults are often enough.

### 2.2 k3s (single-node)

```bash
curl -sfL https://get.k3s.io | sh -
sudo k3s kubectl get nodes
```

Copy kubeconfig for your user (adjust server URL if you access API from another host on the LAN):

```bash
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown "$USER:" ~/.kube/config
# If kubectl complains about server: edit ~/.kube/config — server: https://127.0.0.1:6443
```

Install **kubectl** client if you prefer the standalone binary; k3s bundles `k3s kubectl`.

**Firewall:** allow **6443/tcp** (Kubernetes API) from trusted admin subnets only; **do not** expose k3s to the public Internet without TLS hardening and auth.

### 2.3 Smoke with this repo

1. Clone / pull **data-boar** on the lab-op host.
1. Build image with **Podman**: `podman build -t data_boar:lab -f Dockerfile .`
1. Optionally load into k3s: `sudo k3s ctr images import` from `podman save` **or** use a private registry later — keep **one** image workflow documented in private notes.
1. Apply manifests under **`deploy/kubernetes/`** (edit ConfigMap/Secrets paths to match your lab; **no secrets in git**).

---

## 3. Policy: defer “spreading” to other stacks

**Until** the baseline above is **green** (Podman build + k3s deploy + Data Boar `/health`):

- Do **not** standardise **Nomad**, **Docker Swarm**, or a **second** Kubernetes distribution on lab-op.
- **Podman Desktop** on Windows is optional and unrelated to lab-op’s server baseline.
- When you add a second stack, open a **short ADR** or update this file’s §1 table — avoid silent parallel conventions.

---

## 4. Docker Desktop Kubernetes (Windows dev machine)

**Separate** from lab-op: enabling **Kubernetes** in **Docker Desktop** is valid for **local manifest checks** and **kubectl** practice. It does **not** replace validating **`deploy/kubernetes/`** on **k3s** (or your production-like target). Treat Desktop K8s as **dev-only**.

---

## 5. Future: HP tower, Alpine / AlmaLinux, and simulated “cluster” labs

**When the x86 tower (e.g. HP ML310e-class) + Proxmox is online**, you can add **guest VMs** with **appropriate flavors**—e.g. **Alpine** (minimal footprint, musl) and **AlmaLinux** (RHEL-compatible, glibc)—to extend the **OS matrix** (see [OS_COMPATIBILITY_TESTING_MATRIX.md](OS_COMPATIBILITY_TESTING_MATRIX.md)) **without** discarding the **§1–§3** anchor: keep **one** “golden” guest that still runs **Podman + k3s** as the reference path; use extra guests for **distro-specific** smoke and connector checks.

**Multiple VMs, each running Docker Engine and/or Podman**, can **simulate** a **cluster-style** environment: several **independent** nodes, each hosting containers, to exercise **plans** that need **more than one machine**—e.g. **ingress + multiple app replicas**, **split workers**, **network isolation** between “tenant” subnets. **Horizontal scale** (more replicas of **stateless** pieces) matters when the **bottleneck** is CPU/RAM on a single node or when you must **prove** scaling and **failure isolation** to a stakeholder. This setup is **lab simulation**; it is **not** the same as a **production** multi-AZ story or full **Kubernetes HA** (etcd quorum, redundant control planes) unless you deliberately build that stack.

## When to prioritize resilience / horizontal scale (rough order):

| Stage                                                                                                                                                                                                                                                                                                                                                                    | Focus                                                                                                                                                                   |
| -----                                                                                                                                                                                                                                                                                                                                                                    | -----                                                                                                                                                                   |
| **Now**                                                                                                                                                                                                                                                                                                                                                                  | **§1–§3** + [HOMELAB_VALIDATION](HOMELAB_VALIDATION.md) **–1L**: single-node k3s, one replica, `/health` green.                                                         |
| **Next**                                                                                                                                                                                                                                                                                                                                                                 | Add **Alpine / AlmaLinux** guests on Proxmox for **matrix** coverage; optional **multi-VM** Docker/Podman to rehearse **multi-node** deploy docs and **load** sketches. |
| **Worry about HA / scale “for real”** when: a **customer or partner** asks for **SLA / HA**; **load tests** show saturation on one node; the **product** adds **worker pools**, **queues**, or **multi-tenant** isolation that **requires** N nodes; **Kubernetes** production guidance needs **Ingress + PDB + multiple replicas**; or **DR / multi-site** is in scope. |                                                                                                                                                                         |

**Caveat:** Three VMs each running Docker **simulates** three **nodes**; it does **not** automatically prove **Kubernetes control-plane** HA or **split-brain** safety—name what you are testing (app replicas vs etcd).

---

## 6. Deferred optional: Wazuh (SIEM / security posture) on lab-op

**Not part of the minimal stack.** When lab-op (or a **Proxmox guest**) has **enough RAM and CPU**, consider **[Wazuh](https://wazuh.com/)** (open-source SIEM/XDR) to:

- Centralize **vulnerability** visibility and **hardening** guidance (e.g. CIS-oriented checks, MITRE mapping in the UI).
- Correlate **host** and **container** telemetry with a single **manager** + **agents** (or agentless where applicable).

## Sequence (do not reorder without reason):

| Order | Gate                                                                                                                               |
| ----- | ----                                                                                                                               |
| 1     | **§1–§3** baseline is **green** (Podman + k3s + Data Boar `/health` on lab-op).                                                    |
| 2     | Prefer a **dedicated VM or LXC** for the Wazuh **manager** (avoid starving k3s on the same box if RAM is tight).                   |
| 3     | Enroll **lab-op** and other **homelab** hosts as **agents**; tune noise and retention in **`docs/private/homelab/`** (gitignored). |

**Scope boundary:** Wazuh complements **metrics** stacks (Prometheus, Zabbix, Netdata) and **manual** probes (e.g. SNMP logs under `docs/private.example/homelab/`); it does **not** replace application-level tests in this repo. Tracking: [PLANS_TODO.md](../plans/PLANS_TODO.md) (LAB-OP + H2 deferred).

---

## 7. Deferred optional: metrics + logs + Grafana (observability plan)

**Not part of the minimal stack.** When you want **dashboards**, **central metrics**, and **central logs** (e.g. **Grafana** + **Prometheus** or **InfluxDB**; **Loki** or **Graylog** + **OpenSearch**), follow the sequenced plan—includes RAM guidance for **ThinkPad LAB-NODE-01** vs **tower/VM**:

- **[PLAN_LAB_OP_OBSERVABILITY_STACK.md](../plans/PLAN_LAB_OP_OBSERVABILITY_STACK.md)** ([pt-BR](../plans/PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md))

**Order:** finish **§1–§3** here first, then phases **A–E** in that plan (pick **one** metrics pillar and **one** log stack unless resources allow more).

---

## Related

- [HOMELAB_VALIDATION.md](HOMELAB_VALIDATION.md) — full playbook (§9 multi-host; §9.3 cluster simulation pointer).
- [LMDE7_LAB-NODE-01_DEVELOPER_SETUP.md](LMDE7_LAB-NODE-01_DEVELOPER_SETUP.md) — ThinkPad LAB-NODE-01 + LMDE 7 concrete steps ([pt-BR](LMDE7_LAB-NODE-01_DEVELOPER_SETUP.pt_BR.md)).
- [deploy/DEPLOY.md](../deploy/DEPLOY.md) — deployment narrative.
- [Corporate-Entity-C_IN_REPO_BASELINE.md](Corporate-Entity-C_IN_REPO_BASELINE.md) — reviewer paths (Corporate-Entity-C).
