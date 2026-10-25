# Lab-op observability — learning links (mental note)

**Português (Brasil):** [LAB_OP_OBSERVABILITY_LEARNING_LINKS.pt_BR.md](LAB_OP_OBSERVABILITY_LEARNING_LINKS.pt_BR.md)

**Purpose:** **Revisit** when choosing stacks for **LAB-OP** / homelab. Curated **official** entry points only — not a runbook, not product policy. **Sequencing and RAM warnings** stay in [PLAN_LAB_OP_OBSERVABILITY_STACK.md](../../plans/PLAN_LAB_OP_OBSERVABILITY_STACK.md); **Wazuh + NIST/CIS** in [WAZUH_NIST_CIS_LABOP_ALIGNMENT.md](WAZUH_NIST_CIS_LABOP_ALIGNMENT.md).

---

## How this fits (one glance)

| Need | Default lab-op path (from plan) | Heavier / alternate |
| ---- | ------------------------------- | --------------------- |
| Metrics + dashboards | [Grafana](https://grafana.com/docs/grafana/latest/) + [Prometheus](https://prometheus.io/docs/introduction/overview/) | [InfluxDB](https://docs.influxdata.com/influxdb/) + [Telegraf](https://docs.influxdata.com/telegraf/) |
| Central logs (lighter) | [Loki](https://grafana.com/docs/loki/latest/) + [Promtail](https://grafana.com/docs/loki/latest/send-data/promtail/) + Grafana | — |
| Central logs (search / pipelines) | — | [Graylog](https://docs.graylog.org/docs) + [OpenSearch](https://opensearch.org/docs/latest/) ([compatibility matrix](https://docs.graylog.org/downloading_and_installing_graylog/compatibility_matrix.htm)) |
| Security posture / SIEM-style | [Wazuh](https://documentation.wazuh.com/current/index.html) | Complements metrics/logs; see Wazuh alignment note |
| Traces / APM-ish | [OpenTelemetry](https://opentelemetry.io/docs/) + pick **one** backend below | Commercial APM (trial / paid) |

**Dynatrace-class depth without default spend:** prefer **OSS/self-host** first — [SigNoz](https://signoz.io/docs/) (metrics + logs + traces), [Jaeger](https://www.jaegertracing.io/docs/) (traces), [Grafana Tempo](https://grafana.com/docs/tempo/latest/) (traces, pairs with Grafana), or light host visibility with [Netdata](https://learn.netdata.cloud/). **Dynatrace** itself is **SaaS-first** with **time-limited trial** / enterprise pricing — fine for **comparison**, not assumed lab default; read [Dynatrace documentation](https://docs.dynatrace.com/) and current **free tier** terms before sending lab data off-LAN.

**Grafana Cloud** offers a **free tier** (limits apply) if you want hosted Grafana/Loki/tempo-style pieces without running everything at home — still review **data residency** vs sensitive syslog.

---

## Official docs (bookmark list)

### Visualization / metrics / logs (Grafana stack)

- [Grafana documentation](https://grafana.com/docs/grafana/latest/)
- [Prometheus — getting started](https://prometheus.io/docs/introduction/first_steps/)
- [Loki documentation](https://grafana.com/docs/loki/latest/)
- [Promtail](https://grafana.com/docs/loki/latest/send-data/promtail/)

### Influx path (alternate metrics pillar)

- [InfluxDB documentation](https://docs.influxdata.com/influxdb/)
- [Telegraf documentation](https://docs.influxdata.com/telegraf/)

### Graylog + search backend

- [Graylog documentation](https://docs.graylog.org/docs) — install, Docker, **compatibility matrix** (OpenSearch vs Elasticsearch per version)
- [OpenSearch documentation](https://opensearch.org/docs/latest/)

### Elasticsearch (only when your chosen stack explicitly supports it — many homelab guides are outdated vs Graylog 5 + OpenSearch)

- [Elasticsearch guide](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)

### Security (already detailed elsewhere)

- [Wazuh documentation](https://documentation.wazuh.com/current/index.html) — plus [WAZUH_NIST_CIS_LABOP_ALIGNMENT.md](WAZUH_NIST_CIS_LABOP_ALIGNMENT.md)

### Traces / APM / OTel

- [OpenTelemetry docs](https://opentelemetry.io/docs/)
- [Jaeger documentation](https://www.jaegertracing.io/docs/)
- [Grafana Tempo documentation](https://grafana.com/docs/tempo/latest/)
- [SigNoz documentation](https://signoz.io/docs/)

### Lightweight host metrics (optional)

- [Netdata documentation](https://learn.netdata.cloud/)

### Prometheus scaling (optional, if Prometheus grows)

- [VictoriaMetrics documentation](https://docs.victoriametrics.com/) — long-term storage / compaction patterns; not required to start

---

## Mental notes (revisit quarterly)

- **One TSDB pillar** (Prometheus **or** Influx) and **one log pillar** (Loki **or** Graylog+OpenSearch) unless you have RAM and a reason.
- **Phase F (traces)** after **A** + **C** stable; trace volume explodes — sample or short retention in lab.
- **Do not** ship lab syslog/traces to SaaS without **classification** of what might contain personal or LAN-sensitive strings.
- **Elastic** the company ≠ **OpenSearch** the project — licensing and support paths differ; pick docs that match the **binary** you install.

---

## Related in-repo

- [PLAN_LAB_OP_OBSERVABILITY_STACK.md](../../plans/PLAN_LAB_OP_OBSERVABILITY_STACK.md) — phases A–F, hardware reality
- [PLAN_LAB_FIREWALL_ACCESS_AND_OBSERVABILITY.md](../../plans/PLAN_LAB_FIREWALL_ACCESS_AND_OBSERVABILITY.md) — spine before/alongside heavy stacks
- [WAZUH_NIST_CIS_LABOP_ALIGNMENT.md](WAZUH_NIST_CIS_LABOP_ALIGNMENT.md)
- [WORKFLOW_DEFERRED_FOLLOWUPS.md](../WORKFLOW_DEFERRED_FOLLOWUPS.md)
