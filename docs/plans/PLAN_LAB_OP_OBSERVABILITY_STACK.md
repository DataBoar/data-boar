# Lab-op observability stack — metrics, logs, dashboards (plan only)

**Status:** Active (Phases **A** + **C** live in lab; Phase **F** partial; Phase **D** not adopted; product emit = [#1500](https://github.com/DataBoar/data-boar/issues/1500) + [#1529](https://github.com/DataBoar/data-boar/issues/1529))
**Date:** 2026-08-12
**Authors:** Fabio Leitao
**Priority:** H2

**Português (Brasil):** [PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md](PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md)

**Product emit (code in this repo):** [PLAN_DATABOAR_OTEL_INSTRUMENTATION.md](completed/PLAN_DATABOAR_OTEL_INSTRUMENTATION.md) — FastAPI/SQLAlchemy OTLP opt-in (**traces + metrics + logs** via `LoggerProvider`, [#1529](https://github.com/DataBoar/data-boar/issues/1529)); does not replace operator-side collector/Grafana deploy.

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

| Phase | Stack                                                                         | Role                                              | Lab status (2026-08-12) / notes                                                                                                                                                                                      |
| ----- | -----                                                                         | ----                                              | -----                                                                                                                                                                                                              |
| **A** | **Grafana** + **Prometheus** (+ `node_exporter` / `snmp_exporter` on targets) | Metrics, dashboards, alerts (PromQL)              | **Live** in lab (local Grafana + Grafana Cloud via PDC for Prom/Loki/Tempo/Pyroscope). Default homelab metrics pillar. Aligns with [SNMP_LAB_TARGETS.md](../private.example/homelab/SNMP_LAB_TARGETS.md).             |
| **B** | **Grafana** + **InfluxDB** (+ **Telegraf** collectors)                        | Metrics if you prefer InfluxQL/Flux               | **Not** the active lab pillar. Valid alternative to Prometheus TSDB; pick **one** TSDB (Prometheus **or** Influx) unless you have a clear split.                                                                   |
| **C** | **Loki** + **Grafana** (OTLP / collectors; Promtail optional)                 | Log aggregation, lower footprint than ELK/Graylog | **Live** — primary log pillar (LGTM / Grafana Cloud Loki). Syslog + filelog + OTLP app logs exercised end-to-end. See **§1.1**.                                                                                    |
| **D** | **Graylog** + **OpenSearch**                                                  | Full-text log search, streams, pipelines          | **Not adopted.** No Graylog deploy. OpenSearch may appear in lab **only** as an OTel `elasticsearch` **receiver validation target** (cluster **metrics**), not as a log-search backend — see **§1.1**.               |
| **E** | **Wazuh**                                                                     | Security posture, vulns, hardening                | Still optional / sequenced later. [LAB_OP_MINIMAL_CONTAINER_STACK.md](../ops/LAB_OP_MINIMAL_CONTAINER_STACK.md) §6. **NIST/CIS:** [WAZUH_NIST_CIS_LABOP_ALIGNMENT.md](../ops/inspirations/WAZUH_NIST_CIS_LABOP_ALIGNMENT.md). |
| **F** | **Traces / APM-class** (pick **one** initially)                               | Request flows, latency, service dependencies      | **Partial:** Tempo + OTel collector path live; product emit shipped ([#1500](https://github.com/DataBoar/data-boar/issues/1500), [#1529](https://github.com/DataBoar/data-boar/issues/1529)). Broader APM still backlog. |

**Not recommended on the same LAB-NODE-01 simultaneously:** Graylog + OpenSearch + full Prometheus + Loki + Wazuh + k3s + trace backend. Choose **A or B**, **C or D**, **E** when resources exist, **F** when traces justify the RAM (often a **separate** VM).

### 1.1 Lab ingest validation snapshot (2026-08-11→12)

Operator lab session validated **native OpenTelemetry Collector Contrib receivers** with real traffic. Facts for this plan (not a production architecture change):

| Receiver / path | Result | Interpretation |
| ---- | ------ | -------------- |
| `syslog`, `tcp_log`, `udp_log` | Exercised end-to-end | Useful for SIEM-style / journald→rsyslog→remote and generic line protocols |
| `splunk_hec`, `webhook_event` | Exercised end-to-end | HTTP ingest options; webhook needs an explicit `path` (root `/` → 404) |
| `kafka` (Redpanda in Compose) | Exercised end-to-end | **Redpanda is a receiver validation target only** — not a production Kafka adoption for lab-op |
| `elasticsearch` (OpenSearch in Compose) | Cluster scrape only | Receiver exposes **cluster health metrics** (`elasticsearch_cluster_health`); **does not** ingest log documents. **Not** Phase **D** / Graylog |
| `gelf` | **Unsupported** | No native `gelf` receiver in `otelcol-contrib` v0.158.0 — document as a limitation, do not invent a bridge here |
| Product OTLP logs → Loki | Proven | Evidence: `docs/ops/evidence/otel_1529_loggerprovider_loki_2026-08-12.json` |

**Do not read Compose presence of Redpanda or OpenSearch as Phase D.** Phase **C** (Loki) remains the log pillar; Phase **D** stays optional and **not** selected.

Doc refresh tracking: [#1542](https://github.com/DataBoar/data-boar/issues/1542).

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
- **Reminder (when hardware allows):** keep **syslog/logs** on the Loki path (phase **C**) before adding **Wazuh** (phase **E**) on a **VM/tower** with enough RAM — minimal operator checklist: [OBSERVABILITY_SYSLOG_DETECTION_CHECKLIST.md](../private.example/homelab/OBSERVABILITY_SYSLOG_DETECTION_CHECKLIST.md) ([pt-BR](../private.example/homelab/OBSERVABILITY_SYSLOG_DETECTION_CHECKLIST.pt_BR.md)).
- **Status refresh (2026-08-12):** [#1542](https://github.com/DataBoar/data-boar/issues/1542) — Phases **A**+**C** live; **F** partial; **D** not adopted; native receiver inventory in **§1.1**.

**State:** Active plan (operator-side stack). Product OTLP emit lives under [PLAN_DATABOAR_OTEL_INSTRUMENTATION.md](completed/PLAN_DATABOAR_OTEL_INSTRUMENTATION.md). Private runbooks stay in `docs/private/homelab/`.

