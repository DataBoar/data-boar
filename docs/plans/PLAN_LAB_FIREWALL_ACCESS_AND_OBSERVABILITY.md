# Lab-op — firewall / L3 baseline, assistant access, security posture, observability (sequenced)

**Status:** Pending
**Date:** 2026-03-24
**Authors:** Fabio Leitao
**Priority:** H2

**Português (Brasil):** [PLAN_LAB_FIREWALL_ACCESS_AND_OBSERVABILITY.pt_BR.md](PLAN_LAB_FIREWALL_ACCESS_AND_OBSERVABILITY.pt_BR.md)

**Purpose:** One **ordered spine** for homelab work that started with **UniFi / firewall tuning**: align **L3 + DHCP + DNS** per VLAN, enable **safe Cursor/assistant automation** on the operator PC, capture **security posture** (CyberSecure, IPS, honeypots, cadence), then layer **observability** — **syslog → Loki** before **Wazuh** — without pretending all stacks run on one small laptop at once.

**In scope:** Infrastructure and operator workflows under **`docs/private/`** (truth) and **`docs/private.example/homelab/`** (templates). **Out of scope:** Data Boar application code paths (see product plans separately).

## Relationship to other plans and docs

| Topic                                                | Canonical reference                                                                                                           |
| -----                                                | -------------------                                                                                                           |
| Metrics/logs/SIEM **phase letters** (A–E)            | [PLAN_LAB_OP_OBSERVABILITY_STACK.md](PLAN_LAB_OP_OBSERVABILITY_STACK.md)                                                      |
| DHCP gateway, DNS, CyberSecure honeypot UI checklist | [LAB_NETWORK_L3_DHCP_AND_CYBERSEC.md](../private.example/homelab/LAB_NETWORK_L3_DHCP_AND_CYBERSEC.md)                         |
| Assistant capabilities + blue-team cadence           | [OPERATOR_AI_LAB_ACCESS_AND_BLUE_TEAM_RUNBOOK.md](../private.example/homelab/OPERATOR_AI_LAB_ACCESS_AND_BLUE_TEAM_RUNBOOK.md) |
| Syslog forwarding and detection checklist            | [OBSERVABILITY_SYSLOG_DETECTION_CHECKLIST.md](../private.example/homelab/OBSERVABILITY_SYSLOG_DETECTION_CHECKLIST.md)         |
| Container anchor before heavy stacks                 | [LAB_OP_MINIMAL_CONTAINER_STACK.md](../ops/LAB_OP_MINIMAL_CONTAINER_STACK.md) §1–§7                                           |
| UniFi + SNMP narrative                               | [HOMELAB_UNIFI_LAB-ROUTER-01_LAB_NETWORK.md](../ops/HOMELAB_UNIFI_LAB-ROUTER-01_LAB_NETWORK.md)                                                   |

**Hardware rule (unchanged):** Do **not** target running **Prometheus + Loki + Graylog/OpenSearch + Wazuh + full k3s** simultaneously on a **≤16 GB** laptop. Prefer **one** metrics path, **one** logs path, **Wazuh** on a **VM/tower** when ready.

---

## Recommended sequence (phases 0–5)

Execute in order **unless** a later phase’s hardware is already available (e.g. skip light metrics if you only want logs first—still do **phase 0** first).

| Phase | Name                                     | Goal                                                                                                                                                               | Primary outputs                                                                                                                                                                          |
| ----- | ----                                     | ----                                                                                                                                                               | ---------------                                                                                                                                                                          |
| **0** | **L3 + firewall baseline**               | Each VLAN: DHCP **default router** = LAB-ROUTER-01 on that subnet; DNS intentional; SSID ↔ correct network; firewall rules match intent (IoT isolation, management paths).   | Private table filled from [LAB_NETWORK_L3_DHCP_AND_CYBERSEC.md](../private.example/homelab/LAB_NETWORK_L3_DHCP_AND_CYBERSEC.md); optional update **`LAB_SECURITY_POSTURE.md`** (private) |
| **1** | **Assistant-safe access**                | API Integration **`.env`** (gitignored), TLS trust for `<https://unifi.loca>l` (or your hostname), smoke + inventory scripts succeed from Cursor terminal.         | `scripts/LAB-ROUTER-01-api-smoke-from-env.ps1`, `scripts/LAB-ROUTER-01-api-inventory-from-env.ps1` (optional `-SaveJson` to private `reports/`); no keys in git or chat                                      |
| **2** | **Security profile + hardening cadence** | CyberSecure: encrypted DNS choice documented; IPS scope and signature freshness; honeypot IPs **inside** listed subnets; suppressions documented with ID + reason. | [OPERATOR_AI_LAB_ACCESS_AND_BLUE_TEAM_RUNBOOK.md](../private.example/homelab/OPERATOR_AI_LAB_ACCESS_AND_BLUE_TEAM_RUNBOOK.md) §2–§4; quarterly/annual review slots                       |
| **3** | **Metrics (optional)**                   | Grafana + **Prometheus** *or* **InfluxDB** — pick **one** TSDB pillar.                                                                                             | [PLAN_LAB_OP_OBSERVABILITY_STACK.md](PLAN_LAB_OP_OBSERVABILITY_STACK.md) phase **A** or **B**                                                                                            |
| **4** | **Syslog + Loki**                        | LAB-ROUTER-01 (and optionally Linux hosts) ship logs to **Promtail + Loki + Grafana**; firewall allows **collector ← LAB-ROUTER-01** only as needed.                                   | Phase **C** in observability plan + [OBSERVABILITY_SYSLOG_DETECTION_CHECKLIST.md](../private.example/homelab/OBSERVABILITY_SYSLOG_DETECTION_CHECKLIST.md)                                |
| **5** | **Wazuh (optional)**                     | SIEM/agents for posture and correlation **after** logs are usable; manager on **RAM-sized** VM.                                                                    | Phase **E**; [LAB_OP_MINIMAL_CONTAINER_STACK.md](../ops/LAB_OP_MINIMAL_CONTAINER_STACK.md) §6                                                                                            |

**Dependency rule:** **Phase 4** (centralized logs) should precede **phase 5** (Wazuh) for sensible correlation and less noise.

---

## Sprint-sized to-dos (operator checklist)

Copy rows into a private note or tick here when done.

| # | Task                                                                                                            | Phase |
| - | ----                                                                                                            | ----- |
| 1 | Copy **LAB_NETWORK** + **OPERATOR_AI** templates to `docs/private/homelab/` if not already present              | 0–2   |
| 2 | For each UniFi network: DHCP gateway + DNS match VLAN; Wi‑Fi VLAN mapping verified                              | 0     |
| 3 | Renew DHCP lease on one client per VLAN; run verification commands from LAB_NETWORK (PowerShell / Linux)        | 0     |
| 4 | Create **`.env`** for API; run **smoke** then **inventory**; store JSON only under private `reports/` if needed | 1     |
| 5 | (Optional) SNMP **`.env`** + `scripts/snmp-LAB-ROUTER-01-lab-probe.ps1` from trusted host                                 | 1     |
| 6 | Document IPS suppressions + honeypot rows + encrypted DNS choice in private notes                               | 2     |
| 7 | (Optional) Deploy **Grafana + Prometheus** *or* **Influx** on lab host or VM                                    | 3     |
| 8 | Point LAB-ROUTER-01 **syslog** at Promtail; confirm lines in **Loki** / Grafana Explore                                   | 4     |
| 9 | (Optional) Deploy **Wazuh** manager + enroll agents                                                             | 5     |

---

## Commands and scripts (reference — no secrets in repo)

| Action                                     | Command / script                                                         |
| ------                                     | ----------------                                                         |
| API smoke (after `.env` loaded in session) | `.\scripts\LAB-ROUTER-01-api-smoke-from-env.ps1`                                   |
| API inventory                              | `.\scripts\LAB-ROUTER-01-api-inventory-from-env.ps1` (optional `-SaveJson` path)   |
| SNMP probe (env vars set)                  | `.\scripts\snmp-LAB-ROUTER-01-lab-probe.ps1`                                       |
| Lab host reports                           | `.\scripts\lab-op-sync-and-collect.ps1` (manifest in private `homelab/`) |
| Windows: verify gateway/DNS                | `Get-NetIPConfiguration` (see LAB_NETWORK doc)                           |

---

## Tracking

- **Central list:** [PLANS_TODO.md](PLANS_TODO.md) — subsection *LAB-OP — firewall, access, observability*.
- **Observability detail:** [PLAN_LAB_OP_OBSERVABILITY_STACK.md](PLAN_LAB_OP_OBSERVABILITY_STACK.md).
- **Status:** 🔄 Active sequencing plan — operator progress lives in private notes + optional ticks in this file’s checklist when you want a single markdown anchor.

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md).
