# Docker CE + AIDE + auditd baseline (LAB-OP friendly)

**pt-BR:** [DOCKER_AIDE_AUDITD_BASELINE.pt_BR.md](DOCKER_AIDE_AUDITD_BASELINE.pt_BR.md)

## What we learned from LAB-OP hosts

- The **primary lab-op x86_64 host** runs **Docker Engine (CE)** with **Swarm active** (single-node manager).
- A **secondary ARM SBC lab host** has **AIDE** configured under `/etc/aide/` and **auditd rules** under `/etc/audit/rules.d/`. (Host-specific names belong in **`docs/private/homelab/`** only.)

## Automation

- Docker CE: `ops/automation/ansible/roles/lab_node_01_docker_ce`
  - `playbooks/lab-node-01-baseline.yml` sets `lab_node_01_install_docker_ce: true` and `lab_node_01_docker_swarm_init: true` by default (set either to `false` in inventory to opt out)
  - optional: write `/etc/docker/daemon.json`
  - Swarm: `docker swarm init` when the node is not already in Swarm (single-node manager)
- AIDE: `ops/automation/ansible/roles/lab_node_01_aide`
- auditd: `ops/automation/ansible/roles/lab_node_01_auditd`

## Policy for exceptions

Keep allowlists/ignores **commented** until confirmed, and store host-specific details in `docs/private/homelab/`.

