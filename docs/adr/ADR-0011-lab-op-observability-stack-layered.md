# ADR 0011 — Layered observability stack for lab-op (Munin + Wazuh + Prometheus + Monit + rsyslog/GELF)

- **Status:** Accepted
- **Date (UTC):** 2026-04-03
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Context

The lab-op environment (LAB-NODE-01 + homelab servers) needs observability across two dimensions:

- **Local / real-time visibility:** CPU, memory, disk, network, process health — what is happening *now*.
- **Historical / centralised metrics and logs:** trends, anomaly detection, security events — what *happened*.

A single-vendor solution (e.g., only Grafana stack, only Wazuh, only Munin) would not satisfy both
dimensions without significant resource overhead on the LAB-NODE-01 developer workstation.

## Decision

Adopt a **layered** observability stack where each tool has a specific, non-overlapping role:

| Layer | Tool | Role | Where |
|---|---|---|---|
| **Process / I/O** | `iotop`, `iftop`, `nethogs`, `ctop` | Real-time interactive inspection | CLI / LAB-NODE-01 local |
| **Host metrics** | `prometheus-node-exporter` + Grafana | Time-series metrics, dashboards | Scrape from LAB-NODE-01; Grafana on lab server |
| **Host supervision** | `monit` | Process watchdog — restart services; alert on threshold | LAB-NODE-01 local |
| **SNMP / host history** | `munin-node` | RRD-based host metrics for Munin master | Existing lab master |
| **SIEM / EDR** | Wazuh agent → Wazuh manager | Security events, file integrity, log correlation | Agent on LAB-NODE-01; manager on lab server |
| **Syslog / GELF** | `rsyslog` → Graylog | Centralised log forwarding, GELF for containers | LAB-NODE-01 + Docker log-driver |
| **Hardware sensors** | `lm-sensors`, `smartmontools` | CPU temperature, fan, disk health | LAB-NODE-01 local CLI |

All services are **opt-in** via Ansible defaults (`lab-node-01_obs_*: false` for remote services) to keep
a fresh install safe. Local CLI tools are enabled by default.

## Why not a single stack?

- **Grafana + Loki + Prometheus alone:** covers metrics and logs well, but not security events (no EDR/SIEM).
- **Wazuh alone:** excellent SIEM/EDR, poor interactive real-time visibility; heavyweight manager.
- **Datadog / cloud APM:** cost and data sovereignty concerns for a homelab + LGPD-focused project.
- **ELK stack alone:** resource-intensive for a single developer workstation; Munin already covers
  RRD metrics for the existing lab infrastructure.

The layered approach allows each tool to be **enabled progressively** as the lab matures, without
committing to a full stack before the infrastructure is ready.

## Consequences

- **Positive:** Low resource overhead on the LAB-NODE-01 (only CLI tools + node_exporter run by default);
  remote services (Wazuh, Graylog, Grafana) run on lab servers, not the workstation.
- **Positive:** Each layer is independently replaceable — swapping Munin for Prometheus for host
  metrics does not affect the SIEM or log-forwarding layers.
- **Negative:** Multiple tools to learn and maintain; alert configuration is split across Monit
  (local), Wazuh (SIEM), and Grafana (metrics). A unified alert router (e.g., Alertmanager) is
  deferred until the lab matures.
- **Negative:** `ctop` is not in the Debian apt repository — installed as a binary from GitHub
  releases. This requires version pinning and manual updates (tracked in `lab-node-01_obs_ctop_version`
  Ansible variable).
- **Watch:** As the lab adds more hosts (primary Windows dev PC, servers), the Ansible role should extend to push
  the same observability stack to all managed hosts via group_vars rather than host-specific playbooks.

## References

- [docs/ops/LMDE7_LAB-NODE-01_DEVELOPER_SETUP.pt_BR.md](../ops/LMDE7_LAB-NODE-01_DEVELOPER_SETUP.pt_BR.md) §8
- [ops/automation/ansible/roles/lab-node-01_observability/](../../ops/automation/ansible/roles/lab-node-01_observability/)
- [docs/plans/PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md](../plans/PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md)
- [ADR 0009](ADR-0009-ansible-idempotent-roles-as-single-automation-source.md) — Ansible as automation source
