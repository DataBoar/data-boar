# Local repositories in the homelab (Docker registry + Debian apt)

**Purpose:** Plan **local Docker image registry** and **local Debian package repository** for the homelab, sequenced **after** the **Proxmox server** is ready. This enables **air-gapped** testing, **faster** pulls, **version pinning**, and **offline** validation without relying on **Docker Hub** or **public apt mirrors** for every lab run.

**Related:** [HOMELAB_VALIDATION.md](HOMELAB_VALIDATION.md) (when Proxmox is ready) · [PLAN_SELF_UPGRADE_AND_VERSION_CHECK.md](../plans/PLAN_SELF_UPGRADE_AND_VERSION_CHECK.md) (public .deb/apt repo Phase 9) · [HOMELAB_POWER_AND_ELECTRICAL_PLANNING.md](HOMELAB_POWER_AND_ELECTRICAL_PLANNING.md) (storage/disk planning)

---

## 1. When to set this up (sequencing)

**Prerequisites (from [HOMELAB_VALIDATION.md §9.1](HOMELAB_VALIDATION.md#91-when-to-have-hardware-ready-operator-sync-with-planstodo-order-1l)):**

- **Proxmox** installed on the **x86 tower** (e.g. ML310e Gen8).
- **≥1 Linux VM or LXC** with enough **disk** for images/packages (see storage estimates below).
- **Network** (bridge/VLAN) so guests can reach the repo services.
- **Basic** homelab validation (§1–§2) already passing on **at least one** host.

**Why not earlier:** Until the **tower** is ready, you can still **pull from Docker Hub** and **apt from public mirrors** — local repos are **convenience** and **offline capability**, not a blocker for §1 smoke tests.

---

## 2. Local Docker registry

### 2.1 Options

| Solution                                    | Complexity                    | Features                                                                                                                                          |
| --------                                    | ----------                    | --------                                                                                                                                          |
| **Docker Registry** (official `registry:2`) | **Lowest** — single container | Basic **push/pull**; **no** UI; **no** scanning; **no** RBAC. Good for **simple** homelab.                                                        |
| **Harbor**                                  | **Medium** — full stack       | **Web UI**, **vulnerability scanning**, **RBAC**, **replication** to upstream. **Overkill** for solo lab unless you want **enterprise** practice. |
| **Portus** (SUSE)                           | **Medium**                    | **Web UI**, **auth**, **namespace** management. Less common than Harbor.                                                                          |
| **Nexus Repository OSS**                    | **Medium–high**               | **Multi-format** (Docker, apt, npm, etc.) in **one** service. Useful if you also want **apt** in the same stack.                                  |

**Recommendation for homelab:** Start with **`registry:2`** (simple, low resource). Add **Harbor** later if you want **scanning** or **UI** for browsing images.

### 2.2 Storage estimate

- **Data Boar image** (`fabioleitao/data_boar:latest`): often **~180–200 MB** compressed.
- **Base images** (`python:3.13-slim`, etc.): **~50–150 MB** each.
- **DB lab containers** (Postgres, MySQL): **~50–200 MB** each.

**Rough total for a small lab:** **~1–3 GB** for **Data Boar** + **bases** + **a few** DB images. Plan **≥10 GB** free on the repo VM/LXC for **growth** and **version history** (multiple tags).

### 2.3 Setup (registry:2 example)

**On a Proxmox guest** (Debian/Ubuntu):

```bash
# Create volume for registry data
mkdir -p /data/docker-registry

# Run registry (port 5000, or use reverse proxy)
docker run -d --name registry \
  -p 5000:5000 \
  -v /data/docker-registry:/var/lib/registry \
  --restart unless-stopped \
  registry:2
```

## Push/pull:

```bash
# Tag for local registry
docker tag fabioleitao/data_boar:latest localhost:5000/data-boar:1.7.3
docker push localhost:5000/data-boar:1.7.3

# On other lab hosts, configure insecure registry (or use TLS) and pull
docker pull <repo-host-ip>:5000/data-boar:1.7.3
```

**Security:** For **production-like** practice, add **TLS** (certificates) and **auth** (Harbor or registry with htpasswd). For **lab-only**, **insecure registry** on a **trusted VLAN** is acceptable.

---

## 3. Local Debian apt repository

### 3.1 Options

| Solution                                       | Complexity | Use case                                                                                                                                                                                                                                  |
| --------                                       | ---------- | --------                                                                                                                                                                                                                                  |
| **apt-mirror**                                 | **Low**    | **Mirror** public Debian/Ubuntu repos (full or subset). Good for **offline** lab or **faster** local pulls.                                                                                                                               |
| **reprepro**                                   | **Medium** | **Custom** repo for **your** `.deb` packages (e.g. future Data Boar `.deb` from [PLAN_SELF_UPGRADE §9](../plans/PLAN_SELF_UPGRADE_AND_VERSION_CHECK.md#9-alternative-delivery-package-manager-and-signed-artifacts-winget-like-deb-apt)). |
| **aptly**                                      | **Medium** | **Advanced** snapshotting, **multiple** repos, **publishing** workflows.                                                                                                                                                                  |
| **Simple static** (nginx + `dists/` + `pool/`) | **Lowest** | **Manual** `.deb` hosting; no mirroring. Good for **testing** your own packages before public release.                                                                                                                                    |

**Recommendation:** Start with **reprepro** or **simple static** if you want to **test** Data Boar `.deb` builds **locally** (Phase 9). Add **apt-mirror** if you want to **mirror** Debian/Ubuntu for **offline** lab hosts.

### 3.2 Storage estimate

- **Full Debian** mirror: **~100+ GB** (not recommended for homelab).
- **Subset** (security updates + main): **~10–30 GB** depending on releases.
- **Your own `.deb`** (Data Boar + deps): **< 100 MB** per version.

**Rough total:** **~5–20 GB** for a **subset mirror** + **custom packages**; **≥50 GB** if you mirror **multiple** Debian/Ubuntu releases.

### 3.3 Setup (reprepro example for custom .deb)

## On a Proxmox guest:

```bash
# Install reprepro
sudo apt install -y reprepro nginx

# Create repo structure
sudo mkdir -p /srv/apt-repo/{conf,dists,pool}
cd /srv/apt-repo/conf

# Create distributions file (example)
cat > distributions <<EOF
Codename: stable
Components: main
Architectures: amd64
SignWith: YOUR_GPG_KEY_ID
EOF

# Add your .deb
reprepro includedeb stable /path/to/data-boar_1.7.3_amd64.deb

# Serve via nginx (or Apache)
# Configure /srv/apt-repo as web root
```

## On lab hosts:

```bash
# Add repo
echo "deb http://<repo-host-ip>/ stable main" | sudo tee /etc/apt/sources.list.d/data-boar.list
sudo apt update
sudo apt install data-boar
```

**Security:** **GPG signing** is recommended; publish **public key** so `apt` verifies packages.

---

## 4. Relationship to public plans

| Plan                                                                                                                                                        | Public vs local                                                                                                                        |
| ----                                                                                                                                                        | ---------------                                                                                                                        |
| **[PLAN_SELF_UPGRADE §9](../plans/PLAN_SELF_UPGRADE_AND_VERSION_CHECK.md#9-alternative-delivery-package-manager-and-signed-artifacts-winget-like-deb-apt)** | **Public** apt repo (GitHub Pages or minimal server) for **end users**.                                                                |
| **This doc**                                                                                                                                                | **Local** homelab repo for **testing** `.deb` builds **before** public release, **air-gapped** validation, or **faster** pulls in lab. |

**Workflow:** Build `.deb` locally → test in **local apt repo** → if stable, publish to **public** repo (Phase 9).

---

## 5. When it makes sense

## Do set up local repos if:

- You want **offline** homelab validation (no internet during scans).
- You want to **test** `.deb` packaging **before** public release.
- You want **faster** pulls (LAN vs Docker Hub / apt mirrors).
- You want **version pinning** (keep `data-boar:1.7.3` even if `:latest` updates).

## Skip if:

- You are **still** validating **basic** §1–§2 on **first** host (use **public** sources first).
- **Disk** is tight on the Proxmox guest (repos need **GBs**).
- You **never** plan to build `.deb` (stick to Docker Hub + `uv`/pip).

---

## 6. Integration with homelab playbook

- **After Proxmox ready** (§9.1): Create **one VM or LXC** for **repo services** (registry + apt).
- **Storage:** Allocate **≥20 GB** for Docker registry + apt subset; **≥50 GB** if mirroring full Debian.
- **Network:** Expose registry on **port 5000** (or reverse proxy); apt repo on **port 80/443** (nginx).
- **Firewall:** Restrict to **lab VLAN** only; **do not** expose to **WAN** unless you add **auth** + **TLS**.

**Record** repo host **IP**, **ports**, and **insecure-registry** config in **`docs/private/homelab/`** only ([PRIVATE_OPERATOR_NOTES.md](../PRIVATE_OPERATOR_NOTES.md)).

---

## 7. See also

- [HOMELAB_VALIDATION.md](HOMELAB_VALIDATION.md) — Proxmox readiness gates.
- [PLAN_SELF_UPGRADE_AND_VERSION_CHECK.md](../plans/PLAN_SELF_UPGRADE_AND_VERSION_CHECK.md) — public `.deb`/apt repo (Phase 9).
- [HOMELAB_POWER_AND_ELECTRICAL_PLANNING.md](HOMELAB_POWER_AND_ELECTRICAL_PLANNING.md) — disk/storage planning.

**Português (Brasil):** [HOMELAB_LOCAL_REPOSITORIES.pt_BR.md](HOMELAB_LOCAL_REPOSITORIES.pt_BR.md)
