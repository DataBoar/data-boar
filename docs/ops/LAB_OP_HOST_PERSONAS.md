# LAB-OP host personas — Ansible, completão, and evidence map

**Português (Brasil):** [LAB_OP_HOST_PERSONAS.pt_BR.md](LAB_OP_HOST_PERSONAS.pt_BR.md)

## Purpose

Give a **single mental map** between:

- **Lab fiction** (“ENT-like server”, “PRO partner laptop”, “edge soup sink”, “bridge”) — **coverage intent**, not product SKUs (see [SERVICE_TIERS_SCOPE_TEMPLATE.md](SERVICE_TIERS_SCOPE_TEMPLATE.md) for customer-facing tier language).
- **Concrete knobs:** Ansible playbooks, **`lab-node-01-ansible-labop-podman-apply.sh`**, **`.labop-skip-lab-node-01-podman`**, and **completão** manifest fields (`**completaoEngineMode**`, **`completaoSkipEngineImport**`, **`completaoHealthUrl**`, **`completaoHardwareProfile**`).
- **Evidence:** what to capture under **`docs/private/homelab/reports/`** and session notes so weak hosts are not misread as product defects.

## Persona table (align your private inventory)

| Persona | Intent | Metal **`uv` / Python** for the product | OCI / orchestration | Ansible / scripts (typical) | Completão hints |
| --------- | ------ | ---------------------------------------- | ------------------- | ----------------------------- | ---------------- |
| **ENT-like server** | “Server room” laptop: full OCI, **no** consultant-style toolchain on metal | **No** — validate Data Boar **inside** containers / bind-mounted config; synthetic DBs in stack | **Podman** (rootful/rootless per policy) | **`playbooks/lab-node-01-podman.yml`** via **`scripts/lab-node-01-ansible-labop-podman-apply.sh`** — **omit** **`.labop-skip-lab-node-01-podman`** when you want packages installed; **`playbooks/lab-node-01-baseline.yml`** for wider baseline when needed | **`completaoEngineMode`:** **`container`** and/or **`completaoSkipEngineImport`:** **`true`**; **`completaoHealthUrl`** to published **`/health`** |
| **PRO / partner workstation** | “Consultant laptop”: local iteration + Swarm | **Yes** — **`uv sync`**, extras per [TECH_GUIDE.md](../TECH_GUIDE.md) | **Docker CE + Swarm** | **`lab-node-01-baseline.yml`**, **`deploy/lab-smoke-stack`**, DB compose with **synthetic** data only in tracked examples | Native engine import expected on smoke unless you deliberately mark container-only |
| **Edge / soup sink** | Smallest ARM / SD: **resilience** and **data soup** as a **target path**, not a build farm | **Optional** — measure **`python3 -m databoar --help`** / minimal CLI to see “how bad” it is | **None** on metal (or read-only NFS export) | **`.labop-skip-lab-node-01-podman`**; **no** Swarm manager rôle; scans driven **from** LAB-NODE-02/LAB-NODE-01 | **`completaoHardwareProfile`** prefix **`LAB-NODE-04`** (or **`sshHost`** alias); passive smoke path per [LAB_COMPLETAO_RUNBOOK.md](LAB_COMPLETAO_RUNBOOK.md) |
| **Bridge** | Between edge and PRO: **latency** + **API/dashboard** viability on a weak but online box | **Light** — occasional **`main.py --web`** smoke, not full dev loop | **Optional** Podman (or skip install with marker) | **`scripts/labop-share-client-install.sh`** for client mounts; **`lab-node-01-ansible-labop-podman-apply.sh`** **with** **`.labop-skip-lab-node-01-podman`** if you keep metal thin | **`completaoHealthUrl`** + **`curl`** / browser from another LAN host; log **TTFB** and CPU steal |

## Ansible “by role”, not by unknown distro

- **Debian family** vs **Void** is already split **inside** role **`lab-node-01_podman`** (see [ops/automation/ansible/README.md](../../ops/automation/ansible/README.md)).
- **Personas** decide **whether** to run Podman installs at all (**`.labop-skip-lab-node-01-podman`** on edge/bridge when you standardize on “metal = Python only”).
- Do **not** add playbooks for distros you do not operate; extend **`lab-node-01_podman`** (or a new role) when a **new** family appears on the manifest.

## Synthetic databases and “full” tests

- **ENT / PRO:** keep **synthetic** SQL/CSV and compose definitions in **tracked examples** only; real connection strings stay **`docs/private/`** — [LAB_SMOKE_MULTI_HOST.md](LAB_SMOKE_MULTI_HOST.md), [LAB_EXTERNAL_CONNECTIVITY_EVAL.md](LAB_EXTERNAL_CONNECTIVITY_EVAL.md).
- **Edge:** validate **read paths** and **noise** (logs, binaries) that **other** hosts mount or export — do not require Swarm on the Pi for product truth.

## Evidence pack (private)

Per session, append under **`docs/private/homelab/`** (template [COMPLETAO_SESSION_TEMPLATE.pt_BR.md](../private/homelab/COMPLETAO_SESSION_TEMPLATE.pt_BR.md) when present):

- Wall-clock for **`lab-completao-orchestrate.ps1`**, Ansible **`--check`**, and **`curl`** to **`completaoHealthUrl`**.
- **TTFB** / retries for weak bridge hosts.
- **`iostat`**, **SoC temp**, **pressure stall** on Pi-class nodes ([LAB_COMPLETAO_RUNBOOK.md](LAB_COMPLETAO_RUNBOOK.md) *Performance monitoring*).

## Cross-links

- **Fresh agent / token-aware ladder:** [OPERATOR_AGENT_COLD_START_LADDER.md](OPERATOR_AGENT_COLD_START_LADDER.md) ([pt-BR](OPERATOR_AGENT_COLD_START_LADDER.pt_BR.md)).
- **Completão contracts:** [LAB_COMPLETAO_RUNBOOK.md](LAB_COMPLETAO_RUNBOOK.md) ([pt-BR](LAB_COMPLETAO_RUNBOOK.pt_BR.md)), [LAB_COMPLETAO_FRESH_AGENT_BRIEF.md](LAB_COMPLETAO_FRESH_AGENT_BRIEF.md).
- **Narrow sudo + wrappers:** [LAB_OP_PRIVILEGED_COLLECTION.md](LAB_OP_PRIVILEGED_COLLECTION.md).
- **Script index:** [TOKEN_AWARE_SCRIPTS_HUB.md](TOKEN_AWARE_SCRIPTS_HUB.md).
- **Manifest example (copy to private):** [../private.example/homelab/lab-op-hosts.manifest.example.json](../private.example/homelab/lab-op-hosts.manifest.example.json).
