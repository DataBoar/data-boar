# ADR 0016 — OpenTofu as Corporate IaC Path (Alongside Ansible)

**Date:** 2026-04-05
**Status:** Accepted
**Author:** Fabio Leitao

---

## Context

Data Boar's deployment automation initially targeted two audiences:

- **Self-hosted operators and small teams:** Ansible playbooks under `deploy/ansible/` (Paths A and B).
- **Kubernetes environments:** Kubernetes manifests under `deploy/kubernetes/`.

However, corporate and enterprise clients increasingly use **Terraform-compatible Infrastructure as Code** tools — specifically **OpenTofu** (the open-source Terraform fork) — to manage cloud and on-premise infrastructure. These clients have:

- Existing Terraform/OpenTofu state backends (S3, GCS, Azure Blob).
- Internal modules and provider configurations.
- CI/CD pipelines built around `tofu plan` / `tofu apply` workflows.
- Operators trained on the HCL DSL rather than Ansible YAML.

Ansible remains the correct tool for **configuration management and application deployment** (idempotent package installation, service management, file templates). OpenTofu is the correct tool for **infrastructure provisioning** (cloud VMs, managed databases, networking, DNS records).

## Decision

Add a minimal OpenTofu module under `deploy/opentofu/` that provisions the infrastructure layer for a Data Boar deployment. The module is not a replacement for Ansible but a **complementary first step** in environments where infra is managed as code:

```
OpenTofu (infra provisioning)  →  Ansible (app deployment + configuration)
```

The module covers the **most common corporate deployment target**: a Linux VM (or equivalent) with Docker, exposing port 8088, with optional managed database provisioning.

### Module design (`deploy/opentofu/`)

```
deploy/opentofu/
  main.tf          # Core resources: VM/container host, firewall rules
  variables.tf     # Input variables (image, port, db_type, env)
  outputs.tf       # Useful outputs (host IP, endpoint URL)
  versions.tf      # Provider pinning (docker, local providers)
  README.md        # Usage instructions + integration with Ansible
```

The module uses the **Kreuzwerker Docker provider** by default (no cloud account required for local/lab use), with documented extension points for AWS, GCP, Azure, and bare-metal providers.

### Why OpenTofu and not Terraform?

- OpenTofu is **OSI-approved open source** (MPL 2.0) and drop-in compatible with the Terraform DSL.
- Data Boar is itself an open-source product — using a proprietary infrastructure tool in the reference deployment would be incongruent.
- Corporate clients may already have a BSL Terraform license, but offering the OpenTofu path removes licensing friction for clients who have already migrated.
- The module is syntactically identical between OpenTofu and Terraform 1.5.x — clients on either tool can use it.

### Integration with Ansible

After `tofu apply`, the module emits the target host IP as an output. Clients then run:

```bash
tofu output -raw data_boar_host > inventory/hosts.ini  # or use the generated inventory
ansible-playbook -i inventory/ deploy/ansible/site.yml
```

The `deploy/opentofu/README.md` documents this two-step workflow explicitly.

## Alternatives Considered

| Alternative | Reason not chosen |
|---|---|
| Extend Ansible to manage infra (dynamic inventory) | Ansible is not designed as an infra provisioner; state management is fragile |
| Provide Pulumi module | Much smaller adoption in the corporate on-premise segment; Python DSL preferred only for SRE audiences already in Python |
| Provide Terraform modules only | BSL license creates friction for open-source and SME clients; OpenTofu is compatible |
| Kubernetes Helm chart | `deploy/kubernetes/` already covers this; not all corporate clients have Kubernetes |

## Consequences

**Positive:**
- Corporate clients with existing OpenTofu/Terraform workflows can integrate Data Boar without switching tools.
- Two-step path (OpenTofu infra → Ansible app) is idiomatic and matches enterprise IaC maturity.
- The module is provider-agnostic (Docker, AWS, GCP modules can be swapped via variable overrides).
- OpenTofu's open license aligns with Data Boar's open-core positioning.

**Negative / Trade-offs:**
- OpenTofu adds a new technology surface for documentation and support.
- The module is intentionally minimal (Docker provider); cloud-provider extensions require client-side work.
- State backend configuration (S3, etc.) is left to the client — not opinionated in the module.

## Related

- `deploy/opentofu/` (new module)
- `deploy/ansible/` (Paths A and B)
- `deploy/kubernetes/` (existing K8s manifests)
- ADR 0015: POC test infrastructure
- `docs/USAGE.md` — Automated deployment with Ansible section
