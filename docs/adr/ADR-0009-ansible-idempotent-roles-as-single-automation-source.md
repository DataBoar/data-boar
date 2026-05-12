# ADR 0009 — Ansible idempotent roles as single automation source for LAB-NODE-01 lab baseline

- **Status:** Accepted
- **Date (UTC):** 2026-04-03
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Context

The ThinkPad LAB-NODE-01 running LMDE 7 is the primary developer workstation and lab-op node. Over time,
configuration has been applied through a combination of ad-hoc shell commands (documented in
`LMDE7_LAB-NODE-01_DEVELOPER_SETUP.pt_BR.md`) and one-off script execution. This created drift between
what the documentation described and what was actually installed — a problem that grew as the
baseline expanded from security hardening to include containers and observability tooling.

When a collaborator (or the operator after a fresh install) needs to reproduce the environment,
they face the question: "which commands are still valid? which were superseded?"

Two automation approaches were considered:

| Approach | Pros | Cons |
|---|---|---|
| **Shell scripts / manual steps** | Simple, readable | Not idempotent; hard to know if already applied; no state |
| **Ansible roles (idempotent)** | Re-runnable; state is declared; roles composable; variables override | Requires Ansible install; YAML verbosity |
| **OpenTofu/Terraform** | Declarative infra state; plan/apply | Needs a provider; not native for local OS config |

The operator had already adopted Ansible for the hardening baseline (`lab-node-01_baseline_packages`,
`lab-node-01_ufw`, `lab-node-01_fail2ban`, etc.). The natural extension is to cover **all** reproducible
configuration — not just hardening — within the same Ansible role model.

## Decision

1. **All reproducible configuration** of the LAB-NODE-01 lab baseline is expressed as **Ansible roles**
   under `ops/automation/ansible/roles/`. New configuration areas get new roles, not new shell scripts.
2. **Roles are opt-in by default** (`false`) for anything that may have side effects
   (Docker CE, Podman, k3s, Wazuh agent, Swarm init, syslog forwarding). This keeps the baseline
   safe for a fresh install without requiring all flags to be set.
3. **Playbook `lab-node-01-baseline.yml`** is the single entry point — it documents all available knobs
   in its `vars:` block with explicit defaults. The operator or collaborator overrides what they need.
4. **OpenTofu** is retained as a complementary tool for provider-based infrastructure (DNS, GitHub,
   cloud resources) — it is **not** used for local OS configuration, where Ansible already suffices.
5. **The manual doc (`LMDE7_LAB-NODE-01_DEVELOPER_SETUP.pt_BR.md`)** remains as narrative, troubleshooting
   guide, and explanation of *why* — it is **not** the source of truth for *what* is installed
   (the Ansible roles are). Commands in the doc are reproduced in roles; if they diverge, the
   role wins.
6. **Idempotency gate:** each role must be safe to re-run (`changed_when` and `failed_when` are
   set explicitly where commands are used instead of modules). A future CI job may enforce this
   with `ansible-lint`.

## Role taxonomy added in this decision

| Role | Purpose | Default |
|---|---|---|
| `lab-node-01_docker_ce` | Docker CE from official repo + Compose plugin + Swarm opt-in | off |
| `lab-node-01_podman` | Podman rootless + buildah + skopeo + podman-compose + uidmap/slirp4netns/fuse-overlayfs | on (role default; override in inventory to skip) |
| `lab-node-01_k3s` | k3s lightweight Kubernetes (installs from get.k3s.io) | off |
| `lab-node-01_observability` | iotop, iftop, ctop, munin-node, monit, node_exporter, rsyslog forwarding, Wazuh agent | CLI tools on; services opt-in |

## Consequences

- **Positive:** A collaborator arriving at the project can reproduce the full LAB-NODE-01 environment by running
  one playbook with the appropriate `-e` overrides, without reading the full installation doc.
- **Positive:** Drift detection: if a role is re-run and reports `changed`, it signals unexpected
  state on the host.
- **Negative:** Ansible must be installed (`apt install ansible`) before the playbook runs — a
  chicken-and-egg problem for a bare install. Mitigated by §1 of `LMDE7_LAB-NODE-01_DEVELOPER_SETUP.pt_BR.md`
  (Ansible install is the first automation step).
- **Negative:** Role YAML is more verbose than a shell one-liner. Mitigated by keeping roles
  small and single-purpose.
- **Watch:** As the lab grows to multiple hosts (primary Windows dev PC, servers), the same roles should be extended
  or parameterised rather than duplicated. An `inventory.ini` with multiple hosts and group_vars
  is the expected next step.

## References

- [docs/ops/LMDE7_LAB-NODE-01_DEVELOPER_SETUP.pt_BR.md](../ops/LMDE7_LAB-NODE-01_DEVELOPER_SETUP.pt_BR.md) §7.1.1
- [ops/automation/ansible/playbooks/lab-node-01-baseline.yml](../../ops/automation/ansible/playbooks/lab-node-01-baseline.yml)
- [ops/automation/ansible/roles/](../../ops/automation/ansible/roles/) — all roles
- [ADR 0008](ADR-0008-docker-ce-swarm-over-docker-io-and-podman-only.md) — container runtime choice
- [ADR 0011](ADR-0011-lab-op-observability-stack-layered.md) — observability stack rationale
