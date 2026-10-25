# Primer: Infrastructure as Code and DevSecOps (Boar deployment context)

**Português (Brasil):** [IAC_AND_DEVSECOPS_PRIMER.pt_BR.md](IAC_AND_DEVSECOPS_PRIMER.pt_BR.md)

This primer is for **integrators and new maintainers** who need a shared vocabulary for
**Infrastructure as Code (IaC)** and for how **security checks** show up in this repository.
It is conceptual onboarding — not a runbook. Step-by-step commands live in the deploy READMEs
listed at the end.

**Related:** [docs/hubs/INDEX.md](../hubs/INDEX.md) · [GLOSSARY.md](../GLOSSARY.md) · [local primer index](INDEX.md)

---

## 1. IaC in brief

**Infrastructure as Code** means describing hosts, networks, containers, and related resources in
**version-controlled files** instead of only typing commands on a server once.

Two ideas often get mixed:

| Idea | Typical tool class | What it optimizes |
| ---- | ---------------- | ----------------- |
| **Provisioning** | OpenTofu, Terraform, cloud APIs | *Create or change* resources (VMs, DNS, containers, firewall rules) with **plan → apply** and recorded **state** |
| **Configuration management** | Ansible, Salt, Chef | *Converge* an already-existing machine to a declared shape (packages, services, files) with **idempotent** runs |

**Idempotency:** running the same automation again should leave the system in the desired state,
not keep piling duplicate side effects.

**Drift:** the live system no longer matches what the code says. Drift is detected by comparing
reality to declared intent (and, for OpenTofu/Terraform, to **state**).

**Plan / apply:** OpenTofu (and Terraform-compatible tools) show a **plan** of pending changes,
then **apply** only after an operator accepts that plan. Ansible uses **`--check`** (dry-run) on
playbooks for a similar “what would change?” pass before apply.

This repository does **not** ship a remote OpenTofu **backend** block: state for
`deploy/opentofu/` defaults to **local** files on the machine where you run `tofu apply`
(see `deploy/opentofu/versions.tf` — providers are pinned, no `backend { … }` stanza).

---

## 2. The Boar deployment paths (what is in the tree)

Product deployment automation under **`deploy/`** splits **infrastructure provisioning** and
**application deployment**, as decided in
[ADR-0016](../adr/ADR-0016-opentofu-corporate-iac-path-alongside-ansible.md). **Configuration
management** for installs is **Ansible-first** for reproducible host state, consistent with
[ADR-0009](../adr/ADR-0009-ansible-idempotent-roles-as-single-automation-source.md) (idempotent
roles as the automation source — in this repo that pattern applies to lab baselines under
`ops/automation/ansible/` as well as product roles under `deploy/ansible/`).

### 2.1 Ansible — `deploy/ansible/`

| Artifact | Role |
| -------- | ---- |
| [`site.yml`](../../deploy/ansible/site.yml) | **Path A:** standalone Data Boar via Docker Compose (`swarm_enabled: false`), role `data_boar` |
| [`site-full.yml`](../../deploy/ansible/site-full.yml) | **Path B:** Docker CE + Swarm init, then Swarm service — roles `docker`, then `data_boar` |
| [`site-poc-db.yml`](../../deploy/ansible/site-poc-db.yml) | POC database stack — role `poc_database` (synthetic PII lab data; see playbook vars) |
| [`roles/data_boar/`](../../deploy/ansible/roles/data_boar/) | Pull image, compose/stack deploy, ports, host paths |
| [`roles/docker/`](../../deploy/ansible/roles/docker/) | Docker CE install and Swarm when Path B is used |
| [`roles/poc_database/`](../../deploy/ansible/roles/poc_database/) | Optional POC DB container + seed path |
| [`group_vars/all.yml`](../../deploy/ansible/group_vars/all.yml) | Shared defaults (image tag, port `8088`, install dir, apt-listbugs env for unattended installs) |
| [`inventory/hosts.ini.example`](../../deploy/ansible/inventory/hosts.ini.example) | Example inventory — copy to `hosts.ini` locally (not committed with real hosts) |
| [`ansible.cfg`](../../deploy/ansible/ansible.cfg) | Ansible behaviour for this tree |
| [`README.md`](../../deploy/ansible/README.md) (+ [pt-BR](../../deploy/ansible/README.pt_BR.md)) | Operator entry: prerequisites, Path A/B, POC DB |

Playbooks set `environment: "{{ labop_debian_unattended_apt_environment }}"` so Debian/Ubuntu
`apt-listbugs` does not abort unattended installs — enforced in CI via
`tests/test_ansible_playbooks_unattended_apt.py` (see deploy README).

**Corporate two-step** (documented in both deploy READMEs): OpenTofu can write
`generated_inventory.ini`; Ansible then runs `site.yml` against that inventory.

### 2.2 OpenTofu — `deploy/opentofu/`

| File | Role |
| ---- | ---- |
| [`main.tf`](../../deploy/opentofu/main.tf) | Docker image pull, `docker_container` for Data Boar, optional POC Postgres container, healthcheck |
| [`variables.tf`](../../deploy/opentofu/variables.tf) | Inputs (image, port, host paths, `db_enabled`, `db_password` marked `sensitive`) |
| [`outputs.tf`](../../deploy/opentofu/outputs.tf) | Endpoints and generated Ansible inventory path |
| [`versions.tf`](../../deploy/opentofu/versions.tf) | `required_version >= 1.6.0`; pins `kreuzwerker/docker` and `hashicorp/local` providers |
| [`README.md`](../../deploy/opentofu/README.md) (+ [pt-BR](../../deploy/opentofu/README.pt_BR.md)) | `tofu init` / `plan` / `apply` and hand-off to Ansible |

OpenTofu here targets the **Docker provider** on a host that already runs Docker; it does not
by itself replace Ansible for package installation or application YAML on the host.

---

## 3. DevSecOps signals in *this* repository

Below is what exists **in tracked files today**, with pointers you can verify. Items **not**
listed are **not** claimed.

| Practice | Where it shows up in the repo |
| -------- | ------------------------------ |
| **Python SAST (Bandit)** | `[tool.bandit]` in `pyproject.toml`; CI job **Bandit (strict)** in `.github/workflows/ci.yml`; default tier in `scripts/check-all-security-scans.sh` |
| **Semgrep** | Workflow `.github/workflows/semgrep.yml`; optional **`check-all.sh --enforced`** runs Semgrep with version read from that workflow (`scripts/check-all-security-scans.sh`) |
| **CodeQL** | Workflow `.github/workflows/codeql.yml` |
| **Secret scanning (Gitleaks)** | `security/gitleaks.toml`, workflow `.github/workflows/gitleaks.yml`, `scripts/run-gitleaks-strict.sh`; pre-commit / `check-all` via kombi tests; CI installs a **pinned** gitleaks binary (SHA256 check in `ci.yml`) |
| **Workflow static analysis (Zizmor)** | Workflow `.github/workflows/zizmor.yml`; `scripts/check-all-security-scans.sh` runs `uvx zizmor` on `.github/workflows/` |
| **SBOM generation** | Workflow `.github/workflows/sbom.yml`; roadmap in [ADR-0003](../adr/ADR-0003-sbom-roadmap-cyclonedx-then-syft.md) |
| **Dependency / OSV scan** | `scripts/run-osv-scanner.sh`; **`check-all --enforced`** tier (`scripts/check-all-security-scans.sh`) |
| **Shell script lint** | `shellcheck --severity=error` on tracked `*.sh` in `scripts/check-all.sh` / `check-all.ps1` and CI step **Shellcheck (severity=error)** in `ci.yml` |
| **Gate tripwire (PII / gate files)** | `scripts/gate_change_tripwire.py` at start of `check-all.sh`; protected file set in that script and `.github/CODEOWNERS` |
| **Signed commits / attestation** | Operator policy in `CONTRIBUTING.md` and ADR inventory attestation ([ADR-0056](../adr/ADR-0056-cryptographic-adr-inventory-inv-adr-ssh-attestation.md)); PR guard workflow `.github/workflows/operator-gated-pr-guard.yml` |

**Not in this repository (state honestly):**

- No **dedicated IaC scanner** workflow (e.g. Checkov, tfsec, Trivy-for-Terraform) in tracked automation — grep the tree if you need to re-verify.
- No **remote OpenTofu/Terraform backend** configuration under `deploy/opentofu/`.
- **Bats** for shell helpers is an **optional local** step in `check-all.sh`, not a CI job (`scripts/check-all.sh`, comment block `#1926`).

---

## 4. Securing the automation itself

What the **deploy** trees show:

- **Secrets in Ansible:** defaults in `group_vars/all.yml` and role `defaults/` use public image
  names and paths — no committed vault passwords. Real host inventory and overrides belong in
  operator-controlled `inventory/hosts.ini` (from the example) or `-e` extra vars, not in git.
- **Secrets in OpenTofu:** `db_password` is a `sensitive` variable; README examples use CLI
  `-var` for POC passwords — operators must not commit tfvars with production secrets.
- **Provider pinning:** `deploy/opentofu/versions.tf` pins provider versions; Ansible expects
  `community.docker` collection install per deploy README.
- **Operator responsibility:** firewall exposure of port `8088`, Docker socket access, TLS in
  front of the app, and classification of config files mounted into containers remain **outside**
  what these modules enforce — see [DEPLOY.md](../deploy/DEPLOY.md) and dashboard hardening docs.

---

## 5. Where to go next

| Need | Start here |
| ---- | ---------- |
| Ansible paths A/B and POC DB | [`deploy/ansible/README.md`](../../deploy/ansible/README.md) |
| OpenTofu module and two-step flow | [`deploy/opentofu/README.md`](../../deploy/opentofu/README.md) |
| Why Ansible is the CM source of truth | [ADR-0009](../adr/ADR-0009-ansible-idempotent-roles-as-single-automation-source.md) |
| Why OpenTofu sits beside Ansible | [ADR-0016](../adr/ADR-0016-opentofu-corporate-iac-path-alongside-ansible.md) |
| Primer taxonomy and hub ritual | [ADR-0070](../adr/ADR-0070-primer-taxonomy-and-home.md), [ADR-0058](../adr/ADR-0058-primer-hub-registration-ritual.md) |
| Full ADR index | [`docs/adr/README.md`](../adr/README.md) |
| Map of documentation hubs | [`docs/hubs/INDEX.md`](../hubs/INDEX.md) |

---

*Governance:* technical primers live under `docs/primers/` per [ADR-0070](../adr/ADR-0070-primer-taxonomy-and-home.md).
