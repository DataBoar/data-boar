# Deploy folder

This folder contains **deploy-time assets** (Compose files, Kubernetes manifests, config examples). The **deploy documentation** has been centralized under `docs/`:

- **Deploy guide (English):** [docs/deploy/DEPLOY.md](../docs/deploy/DEPLOY.md)
- **Guia de implantação (Português):** [docs/deploy/DEPLOY.pt_BR.md](../docs/deploy/DEPLOY.pt_BR.md)

Contents of this folder:

- `config.example.yaml` — Example config; copy to `/data/config.yaml` (or `./data/config.yaml` for bind mount).
- `docker-compose.yml` — Docker Compose stack (web API + frontend).
- `docker-compose.override.example.yml` — Example override for bind-mounting `./data`; copy to `docker-compose.override.yml`.
- `kubernetes/` — Kubernetes manifests (Deployment, Service, ConfigMap) and optional examples (NetworkPolicy, PDB).
- `ansible/` — Ansible playbooks for Debian/Ubuntu hosts (Docker Compose stack or full install); see `ansible/README.md`.
- `opentofu/` — OpenTofu/Terraform module for container runtime, ports, and volumes (application config via Ansible).
- `lab-smoke-stack/` — Docker Compose bundle for LAN-only multi-DB lab smoke tests (PostgreSQL, MariaDB, optional MongoDB).
- `samples/` — Tracked starter configs for evaluators (LGPD starter YAML and scope-import pointers); see `samples/README.md`.

All paths in the deploy guides assume you run commands from the **repository root** or from this folder as indicated.
