# Primer: Cloud deployment models (and how Data Boar ships today)

**Português (Brasil):** [CLOUD_DEPLOYMENT_MODELS_PRIMER.pt_BR.md](CLOUD_DEPLOYMENT_MODELS_PRIMER.pt_BR.md)

Conceptual primer for integrators comparing **where** software runs (on your metal, in a VM, in containers, or across cloud APIs). It maps vocabulary to **what this repository actually versions** under `deploy/` — not a cloud-vendor sales guide.

**Related:** [IAC_AND_DEVSECOPS_PRIMER.md](IAC_AND_DEVSECOPS_PRIMER.md) · [docs/deploy/DEPLOY.md](../deploy/DEPLOY.md) · [local INDEX](INDEX.md)

---

## 1. Models in one table

| Model | Idea | Typical artifacts |
| ----- | ---- | ----------------- |
| **Bare metal / VM** | OS you control; packages installed on the host | Ansible playbooks, systemd, firewall on the host |
| **Container on a host** | App in an image; host runs a container engine | `docker pull`, `docker compose`, Swarm service |
| **IaC provisioning** | Declare infrastructure; plan/apply with state | OpenTofu/Terraform modules (here: Docker provider on an existing engine) |
| **Multicloud** | Same patterns repeated per provider/account | Not a single shipped module in this repo — operators compose per site |

**Multicloud** in the wild means different accounts, regions, and compliance boundaries. Data Boar’s **product** posture is **customer-controlled deployment** (on-prem, VPC, or consultant laptop) per [LICENSING_OPEN_CORE_AND_COMMERCIAL.md](../LICENSING_OPEN_CORE_AND_COMMERCIAL.md) — not a multi-tenant SaaS control plane in this tree.

---

## 2. What Data Boar versions under `deploy/`

| Path | Role |
| ---- | ---- |
| [`deploy/ansible/`](../deploy/ansible/README.md) | **Path A:** Compose on host (`site.yml`). **Path B:** Docker CE + Swarm then stack (`site-full.yml`). Optional POC DB (`site-poc-db.yml`). |
| [`deploy/opentofu/`](../deploy/opentofu/README.md) | Pull image, run `docker_container`, optional POC Postgres; can emit `generated_inventory.ini` for Ansible |
| [`deploy/docker-compose.yml`](../../deploy/docker-compose.yml) | Reference compose for local/lab-style runs (see [DEPLOY.md](../deploy/DEPLOY.md)) |
| [`Dockerfile`](../../Dockerfile) | Image build for `data_boar` releases |

There is **no** checked-in Terraform module for AWS/GCP/Azure networking in this repository. Cloud-shaped installs usually mean **you** provide the VM or Kubernetes/Docker host, then run the Ansible or OpenTofu paths above.

---

## 3. Honest limits

- **No** managed “Data Boar Cloud” endpoint is defined in tracked deploy docs.
- **No** remote OpenTofu backend — state stays local unless you add one outside this repo ([`deploy/opentofu/versions.tf`](../../deploy/opentofu/versions.tf)).
- Connectors can target **cloud-adjacent** exports (S3-style paths appear in product docs) — that is **scan configuration**, not a hosted scanner SaaS.

---

## 4. Where to go next

| Need | Start here |
| ---- | ---------- |
| Ansible paths A/B | [`deploy/ansible/README.md`](../../deploy/ansible/README.md) |
| OpenTofu two-step flow | [`deploy/opentofu/README.md`](../../deploy/opentofu/README.md) |
| IaC + DevSecOps vocabulary | [IAC_AND_DEVSECOPS_PRIMER.md](IAC_AND_DEVSECOPS_PRIMER.md) |
| Licensing / deployment count | [LICENSING_SPEC.md](../LICENSING_SPEC.md) (`dbmax_deployments`) |
