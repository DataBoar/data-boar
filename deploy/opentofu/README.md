# Data Boar — OpenTofu Module

Deploy Data Boar infrastructure using [OpenTofu](https://opentofu.org/) (open-source Terraform fork).

This module provisions the **infrastructure layer** (container runtime, ports, volumes). For
**application configuration** (scan targets, database credentials, schedule), use the Ansible
playbooks in `deploy/ansible/` as a second step.

---

## Who should use this

Use this module when your team already manages infrastructure via OpenTofu or Terraform 1.5.x.
If you want a simpler one-command deployment without an existing IaC workflow, see
`deploy/ansible/README.md` instead (Paths A and B).

---

## Prerequisites

- **OpenTofu >= 1.6** or **Terraform >= 1.5** installed.
- **Docker** running on the target host.
- A Data Boar `config.yaml` already on disk at the path you will pass via `data_boar_config_path`.
- A report output directory created on the host.

Install OpenTofu: <https://opentofu.org/docs/intro/install/>

---

## Quick start

```bash
# 1. Enter this directory
cd deploy/opentofu

# 2. Initialize providers
tofu init

# 3. Preview what will be created
tofu plan

# 4. Apply (deploys container on the local Docker daemon)
tofu apply

# 5. Open Data Boar
open http://localhost:8088
```

---

## Two-step corporate workflow (OpenTofu + Ansible)

OpenTofu provisions infrastructure; Ansible configures the application.

```bash
# Step 1: provision infra
cd deploy/opentofu
tofu apply

# Step 2: configure and deploy app
#   OpenTofu wrote a generated_inventory.ini for you:
cd ../..
ansible-playbook -i deploy/opentofu/generated_inventory.ini deploy/ansible/site.yml
```

---

## With POC database (PostgreSQL)

To spin up a local PostgreSQL container alongside Data Boar for POC testing:

```bash
tofu apply -var="db_enabled=true" -var="db_password=poc-test-123"
```

Then populate the database with synthetic PII:

```bash
uv run python scripts/populate_poc_database.py \
  --db-type postgres \
  --host localhost \
  --port 5432 \
  --write-config
```

---

## Variables

| Name | Default | Description |
|---|---|---|
| `data_boar_image` | `fabioleitao/data-boar:latest` | Docker image to pull |
| `data_boar_port` | `8088` | Host port for the web interface |
| `data_boar_config_path` | `/etc/data-boar/config.yaml` | Path to config.yaml on host |
| `data_boar_output_dir` | `/var/data-boar/reports` | Path to report output dir on host |
| `container_name` | `data-boar` | Docker container name |
| `restart_policy` | `unless-stopped` | Docker restart policy |
| `db_enabled` | `false` | Spin up a local PostgreSQL POC database |
| `db_password` | `""` (sensitive) | Password for the POC PostgreSQL database |

---

## Outputs

| Output | Description |
|---|---|
| `data_boar_url` | URL to the Data Boar web interface |
| `data_boar_port` | Host port the container is bound to |
| `container_name` | Name of the running container |
| `ansible_inventory_path` | Path to the generated Ansible inventory |
| `poc_db_host` | PostgreSQL host (when `db_enabled = true`) |
| `poc_db_port` | PostgreSQL port (when `db_enabled = true`) |

---

## Cloud / remote providers

The default module uses the Docker provider (local daemon). To target a remote host or a cloud
provider, override the provider configuration in a `provider_override.tf` file in your working
directory. Examples:

**AWS ECS:**

```hcl
# Replace docker_container with aws_ecs_service / aws_ecs_task_definition
# and use the aws provider from hashicorp/aws
```

**Remote Docker host via SSH:**

```hcl
provider "docker" {
  host     = "ssh://<ssh-user>@myserver.example.com"
  ssh_opts = ["-i", "~/.ssh/id_ed25519"]
}
```

---

## State backend (recommended for corporate use)

Store state remotely so the team shares the same infrastructure view:

```hcl
# backend.tf (create in deploy/opentofu/ before tofu init)
terraform {
  backend "s3" {
    bucket = "my-company-tf-state"
    key    = "data-boar/terraform.tfstate"
    region = "us-east-1"
  }
}
```

Compatible backends: S3, GCS, Azure Blob, MinIO (self-hosted S3-compatible).

---

## Compatibility

This module uses only HCL features compatible with both **OpenTofu >= 1.6** and **Terraform >= 1.5**.
If your team has already migrated to OpenTofu, use `tofu`; if still on Terraform BSL, `terraform`
commands work identically.

---

## Related

- `deploy/ansible/README.md` — Path A (Docker Compose) and Path B (full stack) Ansible playbooks
- `deploy/kubernetes/` — Kubernetes manifests
- `docs/adr/ADR-0016-opentofu-corporate-iac-path-alongside-ansible.md` — Design rationale
- `docs/USAGE.md` — Full deployment documentation