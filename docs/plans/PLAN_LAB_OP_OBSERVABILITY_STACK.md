# Lab-op observability stack — metrics, logs, dashboards (plan only)

**Status:** Pending
**Date:** 2026-03-24
**Authors:** Fabio Leitao
**Priority:** H2

**Português (Brasil):** [PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md](PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md)

**Purpose:** Sequence **optional** homelab instrumentation—**Grafana**, time-series DBs, **centralized logs**—without blocking Data Boar development or **–1L** validation. **No** implementation in this repo; operator deploys via Compose, k3s Helm, or vendor appliances on **lab-op** hosts (ThinkPad LAB-NODE-01, LAB-NODE-02, Proxmox guests).

## Prerequisites (must be green first):

| Step                                             | Doc                                                                                                                                           |
| ----                                             | ---                                                                                                                                           |
| OS + secure dev baseline on the laptop           | [LMDE7_LAB-NODE-01_DEVELOPER_SETUP.pt_BR.md](../ops/LMDE7_LAB-NODE-01_DEVELOPER_SETUP.pt_BR.md) ([EN summary](../ops/LMDE7_LAB-NODE-01_DEVELOPER_SETUP.md))           |
| Minimal container anchor (Podman + optional k3s) | [LAB_OP_MINIMAL_CONTAINER_STACK.md](../ops/LAB_OP_MINIMAL_CONTAINER_STACK.md) §1–§3 ([pt-BR](../ops/LAB_OP_MINIMAL_CONTAINER_STACK.pt_BR.md)) |
| SNMP / firewall probes (optional)                | [SNMP_LAB_TARGETS.md](../private.example/homelab/SNMP_LAB_TARGETS.md)                                                                         |

**Hardware reality:** A **LAB-NODE-01** with **≤16 GB RAM** should **not** run Prometheus + Loki + Graylog + OpenSearch + Wazuh + k3s **all at once**. Prefer **one** metrics path and **one** logs path; offload heavy stacks to a **tower/Proxmox VM** when available.

---

## 1. Recommended sequence (light → heavy)

| Phase | Stack                                                                         | Role                                              | Notes                                                                                                                                                                                                              |
| ----- | -----                                                                         | ----                                              | -----                                                                                                                                                                                                              |
| **A** | **Grafana** + **Prometheus** (+ `node_exporter` / `snmp_exporter` on targets) | Metrics, dashboards, alerts (PromQL)              | **Default** recommendation for homelab. Aligns with [SNMP_LAB_TARGETS.md](../private.example/homelab/SNMP_LAB_TARGETS.md) “production monitoring” narrative.                                                       |
| **B** | **Grafana** + **InfluxDB** (+ **Telegraf** collectors)                        | Metrics if you prefer InfluxQL/Flux               | Valid alternative to Prometheus TSDB; slightly different ops model. Pick **one** TSDB pillar (Prometheus **or** Influx), not both, unless you have a clear split (e.g. SNMP in Prometheus, app metrics in Influx). |
| **C** | **Promtail** + **Loki** + **Grafana**                                         | Log aggregation, lower footprint than ELK/Graylog | “LGTM” family; good for **JSON/syslog** shipping and Grafana Explore.                                                                                                                                              |
| **D** | **Graylog** + **OpenSearch**                                                  | Full-text log search, streams, pipelines          | **Graylog 5+** uses **OpenSearch** (not Elasticsearch) as default backend—check current Graylog docs. **Heavy:** plan **≥8 GB** for OpenSearch alone on small labs; prefer a **dedicated VM**.                     |
| **E** | **Wazuh**                                                                     | Security posture, vulns, hardening                | [LAB_OP_MINIMAL_CONTAINER_STACK.md](../ops/LAB_OP_MINIMAL_CONTAINER_STACK.md) §6 — complements metrics/logs; does not replace them. **NIST/CIS buyer vocabulary:** [WAZUH_NIST_CIS_LABOP_ALIGNMENT.md](../ops/inspirations/WAZUH_NIST_CIS_LABOP_ALIGNMENT.md). |
| **F** | **Traces / APM-class** (pick **one** initially)                               | Request flows, latency, service dependencies      | **Dynatrace**-class depth without default SaaS spend: **SigNoz**, **Grafana Tempo** + **OpenTelemetry**, **Jaeger**, or light **Netdata**; **Dynatrace** itself = trial/enterprise SaaS — see **§3** links. Run on a **VM** after **A** + **C** are stable. |

**Not recommended on the same LAB-NODE-01 simultaneously:** Graylog + OpenSearch + full Prometheus + Loki + Wazuh + k3s + trace backend. Choose **A or B**, **C or D**, **E** when resources exist, **F** when traces justify the RAM (often a **separate** VM).

---

## 2. Product notes (operator choice)

- **Grafana** is almost always the **visualization** hub; it connects to Prometheus, InfluxDB, Loki, and many datasources.
- **Elasticsearch** vs **OpenSearch:** for **Graylog**, follow Graylog’s supported backend; do not assume a generic “ELK” tutorial without checking versions.
- **InfluxDB** 3.x vs 2.x: confirm image/docs when copying Compose snippets—breaking changes exist between major lines.

---

## 3. Primary documentation (mental note — revisit)

Curated **official** bookmarks for **Grafana, Prometheus, Loki, Graylog, OpenSearch, Elasticsearch, OpenTelemetry, trace backends, Grafana Cloud free tier, and Dynatrace-style comparisons:** [LAB_OP_OBSERVABILITY_LEARNING_LINKS.md](../ops/inspirations/LAB_OP_OBSERVABILITY_LEARNING_LINKS.md) ([pt-BR](../ops/inspirations/LAB_OP_OBSERVABILITY_LEARNING_LINKS.pt_BR.md)). Does not change phase order in **§1**; use when picking versions and reading upstream how-tos.

---

## 4. Private documentation

URLs, retention, LDAP, and LAN firewall rules belong in **`docs/private/homelab/`** (e.g. `OBSERVABILITY_RUNBOOK.md`) — **gitignored**.

---

## 5. Tracking

- **PLANS_TODO.md** — LAB-OP observability row + **H2** deferred bullet.
- **Sequencing spine (firewall → access → logs → Wazuh):** [PLAN_LAB_FIREWALL_ACCESS_AND_OBSERVABILITY.md](PLAN_LAB_FIREWALL_ACCESS_AND_OBSERVABILITY.md) ([pt-BR](PLAN_LAB_FIREWALL_ACCESS_AND_OBSERVABILITY.pt_BR.md)) — use when UniFi/L3 work is active **before** or **alongside** phases A–F below.
- **Learning links (Grafana / Elastic stack / traces):** [LAB_OP_OBSERVABILITY_LEARNING_LINKS.md](../ops/inspirations/LAB_OP_OBSERVABILITY_LEARNING_LINKS.md) ([pt-BR](../ops/inspirations/LAB_OP_OBSERVABILITY_LEARNING_LINKS.pt_BR.md)).
- **LAB_OP_MINIMAL_CONTAINER_STACK.md** §7 — short pointer here.
- **Reminder (when hardware allows):** deploy **syslog/logs** first (**Promtail + Loki + Grafana**, phase **C**); add **Wazuh** (phase **E**) on a **VM/tower** with enough RAM — minimal operator checklist: [OBSERVABILITY_SYSLOG_DETECTION_CHECKLIST.md](../private.example/homelab/OBSERVABILITY_SYSLOG_DETECTION_CHECKLIST.md) ([pt-BR](../private.example/homelab/OBSERVABILITY_SYSLOG_DETECTION_CHECKLIST.pt_BR.md)).

