# Observabilidade no lab-op — links de aprendizado (nota mental)

**English:** [LAB_OP_OBSERVABILITY_LEARNING_LINKS.md](LAB_OP_OBSERVABILITY_LEARNING_LINKS.md)

**Finalidade:** **Revisitar** ao escolher stacks para **LAB-OP** / homelab. Só **pontos de entrada oficiais** — não é runbook nem política de produto. **Sequência e avisos de RAM** ficam em [PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md](../../plans/PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md); **Wazuh + NIST/CIS** em [WAZUH_NIST_CIS_LABOP_ALIGNMENT.pt_BR.md](WAZUH_NIST_CIS_LABOP_ALIGNMENT.pt_BR.md).

---

## Encaixe rápido

| Necessidade | Caminho predefinido no plano | Mais pesado / alternativo |
| ----------- | ---------------------------- | ------------------------- |
| Métricas + dashboards | [Grafana](https://grafana.com/docs/grafana/latest/) + [Prometheus](https://prometheus.io/docs/introduction/overview/) | [InfluxDB](https://docs.influxdata.com/influxdb/) + [Telegraf](https://docs.influxdata.com/telegraf/) |
| Logs centralizados (mais leve) | [Loki](https://grafana.com/docs/loki/latest/) + [Promtail](https://grafana.com/docs/loki/latest/send-data/promtail/) + Grafana | — |
| Logs (busca / pipelines) | — | [Graylog](https://docs.graylog.org/docs) + [OpenSearch](https://opensearch.org/docs/latest/) ([matriz de compatibilidade](https://docs.graylog.org/downloading_and_installing_graylog/compatibility_matrix.htm)) |
| Postura / estilo SIEM | [Wazuh](https://documentation.wazuh.com/current/index.html) | Complementa métricas/logs; ver nota Wazuh |
| Traces / APM | [OpenTelemetry](https://opentelemetry.io/docs/) + **um** backend abaixo | APM comercial (trial / pago) |

**Profundidade estilo Dynatrace sem assumir custo:** priorizar **OSS/self-host** — [SigNoz](https://signoz.io/docs/) (métricas + logs + traces), [Jaeger](https://www.jaegertracing.io/docs/) (traces), [Grafana Tempo](https://grafana.com/docs/tempo/latest/) (traces, casa bem com Grafana), ou visibilidade leve com [Netdata](https://learn.netdata.cloud/). **Dynatrace** é **SaaS-first** com **trial** limitado / preço enterprise — útil para **comparar**, não como padrão assumido do lab; ver [documentação Dynatrace](https://docs.dynatrace.com/) e termos atuais de **free tier** antes de enviar dados do lab para fora da LAN.

**Grafana Cloud** tem **free tier** (com limites) se quiser Grafana/Loki/tempo hospedados sem rodar tudo em casa — rever **residência de dados** vs syslog sensível.

---

## Documentação oficial (lista para favoritar)

### Visualização / métricas / logs (stack Grafana)

- [Documentação Grafana](https://grafana.com/docs/grafana/latest/)
- [Prometheus — primeiros passos](https://prometheus.io/docs/introduction/first_steps/)
- [Loki](https://grafana.com/docs/loki/latest/)
- [Promtail](https://grafana.com/docs/loki/latest/send-data/promtail/)

### Trilha Influx (métricas alternativas)

- [InfluxDB](https://docs.influxdata.com/influxdb/)
- [Telegraf](https://docs.influxdata.com/telegraf/)

### Graylog + backend de busca

- [Graylog](https://docs.graylog.org/docs) — instalação, Docker, **matriz de compatibilidade** (OpenSearch vs Elasticsearch por versão)
- [OpenSearch](https://opensearch.org/docs/latest/)

### Elasticsearch (só se a stack que instalares suportar explicitamente — muitos guias de homelab estão desatualizados vs Graylog 5 + OpenSearch)

- [Guia Elasticsearch](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)

### Segurança (detalhe em outro arquivo)

- [Wazuh](https://documentation.wazuh.com/current/index.html) — e [WAZUH_NIST_CIS_LABOP_ALIGNMENT.pt_BR.md](WAZUH_NIST_CIS_LABOP_ALIGNMENT.pt_BR.md)

### Traces / APM / OTel

- [OpenTelemetry](https://opentelemetry.io/docs/)
- [Jaeger](https://www.jaegertracing.io/docs/)
- [Grafana Tempo](https://grafana.com/docs/tempo/latest/)
- [SigNoz](https://signoz.io/docs/)

### Métricas de host leves (opcional)

- [Netdata](https://learn.netdata.cloud/)

### Escala do Prometheus (opcional)

- [VictoriaMetrics](https://docs.victoriametrics.com/) — armazenamento de longo prazo; não é obrigatório para começar

---

## Notas mentais (rever por trimestre)

- **Um** pilar TSDB (Prometheus **ou** Influx) e **um** de logs (Loki **ou** Graylog+OpenSearch), salvo RAM e justificativa.
- **Fase F (traces)** depois de **A** + **C** estáveis; volume de traces explode — amostragem ou retenção curta no lab.
- **Não** enviar syslog/traces do lab para SaaS sem **classificar** o que pode conter dados pessoais ou strings sensíveis da LAN.
- **Elastic** (empresa) ≠ **OpenSearch** (projeto) — licença e suporte diferem; usa a doc que corresponde ao **binário** instalado.

---

## Relacionado no repositório

- [PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md](../../plans/PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md) — fases A–F, hardware
- [PLAN_LAB_FIREWALL_ACCESS_AND_OBSERVABILITY.pt_BR.md](../../plans/PLAN_LAB_FIREWALL_ACCESS_AND_OBSERVABILITY.pt_BR.md) — espinha antes/em paralelo
- [WAZUH_NIST_CIS_LABOP_ALIGNMENT.pt_BR.md](WAZUH_NIST_CIS_LABOP_ALIGNMENT.pt_BR.md)
- [WORKFLOW_DEFERRED_FOLLOWUPS.pt_BR.md](../WORKFLOW_DEFERRED_FOLLOWUPS.pt_BR.md)
