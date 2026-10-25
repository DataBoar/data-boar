# Stack de observabilidade no lab-op — métricas, logs, dashboards (só plano)

**Status:** Active (Fases **A** + **C** no ar no lab; Fase **F** parcial; Fase **D** não adotada; emit do produto = [#1500](https://github.com/DataBoar/data-boar/issues/1500) + [#1529](https://github.com/DataBoar/data-boar/issues/1529))
**Date:** 2026-08-12
**Authors:** Fabio Leitao
**Priority:** H2

**English:** [PLAN_LAB_OP_OBSERVABILITY_STACK.md](PLAN_LAB_OP_OBSERVABILITY_STACK.md)

**Emit do produto (código neste repo):** [PLAN_DATABOAR_OTEL_INSTRUMENTATION.md](completed/PLAN_DATABOAR_OTEL_INSTRUMENTATION.md) — OTLP opt-in FastAPI/SQLAlchemy (**traces + metrics + logs** via `LoggerProvider`, [#1529](https://github.com/DataBoar/data-boar/issues/1529)); não substitui o deploy do collector/Grafana no lado do operador.

**Objetivo:** Ordenar instrumentação **opcional** do homelab — **Grafana**, bases de séries temporais, **centralização de logs** — sem bloquear desenvolvimento do Data Boar nem a validação **–1L**. **Sem** implementação neste repositório; o operador instala via Compose, Helm no k3s ou appliance na **lab-op** (LAB-NODE-01, LAB-NODE-02, VMs Proxmox).

## Pré-requisitos (antes disto):

| Passo                                               | Documento                                                                                                                          |
| -----                                               | ---------                                                                                                                          |
| SO + baseline segura de dev no portátil             | [LMDE7_LAB-NODE-01_DEVELOPER_SETUP.pt_BR.md](../ops/LMDE7_LAB-NODE-01_DEVELOPER_SETUP.pt_BR.md) ([EN resumo](../ops/LMDE7_LAB-NODE-01_DEVELOPER_SETUP.md)) |
| Stack mínima de contentores (Podman + k3s opcional) | [LAB_OP_MINIMAL_CONTAINER_STACK.pt_BR.md](../ops/LAB_OP_MINIMAL_CONTAINER_STACK.pt_BR.md) §1–§3                                    |
| Probes SNMP / firewall (opcional)                   | [SNMP_LAB_TARGETS.pt_BR.md](../private.example/homelab/SNMP_LAB_TARGETS.pt_BR.md)                                                  |

**Realidade de hardware:** LAB-NODE-01 com **≤16 GB RAM** não deve rodar Prometheus + Loki + Graylog + OpenSearch + Wazuh + k3s **ao mesmo tempo**. Escolha **um** caminho de métricas e **um** de logs; stacks pesados no **torre/VM Proxmox** quando existir.

---

## 1. Sequência recomendada (leve → pesada)

| Fase  | Stack                                                              | Função                                          | Estado no lab (2026-08-12) / notas                                                                                                                                                                   |
| ----  | -----                                                              | ------                                          | -----                                                                                                                                                                                                |
| **A** | **Grafana** + **Prometheus** (+ `node_exporter` / `snmp_exporter`) | Métricas, dashboards, alertas (PromQL)          | **No ar** no lab (Grafana local + Grafana Cloud via PDC para Prom/Loki/Tempo/Pyroscope). Pilar de métricas padrão. Alinha com [SNMP_LAB_TARGETS.pt_BR.md](../private.example/homelab/SNMP_LAB_TARGETS.pt_BR.md). |
| **B** | **Grafana** + **InfluxDB** (+ **Telegraf**)                        | Métricas se preferir InfluxQL/Flux              | **Não** é o pilar ativo do lab. Alternativa válida ao TSDB do Prometheus; escolha **um** pilar TSDB (Prometheus **ou** Influx), salvo divisão explícita.                                              |
| **C** | **Loki** + **Grafana** (OTLP / collectors; Promtail opcional)      | Agregação de logs, pegada menor que ELK/Graylog | **No ar** — pilar principal de logs (LGTM / Grafana Cloud Loki). Syslog + filelog + logs OTLP do app exercitados ponta a ponta. Ver **§1.1**.                                                         |
| **D** | **Graylog** + **OpenSearch**                                       | Busca full-text, streams, pipelines             | **Não adotada.** Sem deploy de Graylog. OpenSearch no lab só como **alvo de validação** do receiver OTel `elasticsearch` (métrica de cluster), não como backend de busca de log — ver **§1.1**.         |
| **E** | **Wazuh**                                                          | Postura de segurança, vulns, hardening          | Ainda opcional / sequenciado depois. [LAB_OP_MINIMAL_CONTAINER_STACK.pt_BR.md](../ops/LAB_OP_MINIMAL_CONTAINER_STACK.pt_BR.md) §6. **NIST/CIS:** [WAZUH_NIST_CIS_LABOP_ALIGNMENT.pt_BR.md](../ops/inspirations/WAZUH_NIST_CIS_LABOP_ALIGNMENT.pt_BR.md). |
| **F** | **Traces / estilo APM** (escolher **um** de início)                | Fluxos de pedido, latência, dependências        | **Parcial:** caminho Tempo + collector OTel no ar; emit do produto shipped ([#1500](https://github.com/DataBoar/data-boar/issues/1500), [#1529](https://github.com/DataBoar/data-boar/issues/1529)). APM mais amplo ainda em backlog. |

**Evitar no mesmo LAB-NODE-01 ao mesmo tempo:** Graylog + OpenSearch + Prometheus completo + Loki + Wazuh + k3s + backend de traces. Escolha **A ou B**, **C ou D**, **E** quando houver recursos, **F** quando traces justificarem a RAM (muitas vezes **VM** à parte).

### 1.1 Snapshot de validação de ingestão no lab (2026-08-11→12)

Sessão de lab do operador validou **receivers nativos do OpenTelemetry Collector Contrib** com tráfego real. Fatos para este plano (não é mudança de arquitetura de produção):

| Receiver / caminho | Resultado | Interpretação |
| ---- | --------- | ------------- |
| `syslog`, `tcp_log`, `udp_log` | Exercitados ponta a ponta | Úteis para estilo SIEM / journald→rsyslog→remoto e protocolos de linha genéricos |
| `splunk_hec`, `webhook_event` | Exercitados ponta a ponta | Opções HTTP; webhook precisa de `path` explícito (`/` na raiz → 404) |
| `kafka` (Redpanda no Compose) | Exercitado ponta a ponta | **Redpanda é só alvo de validação do receiver** — não é adoção de Kafka de produção no lab-op |
| `elasticsearch` (OpenSearch no Compose) | Só scrape de cluster | O receiver expõe **métricas de saúde do cluster** (`elasticsearch_cluster_health`); **não** ingere documentos de log. **Não** é Fase **D** / Graylog |
| `gelf` | **Sem suporte** | Não há receiver nativo `gelf` no `otelcol-contrib` v0.158.0 — documentar como limitação; não inventar bridge aqui |
| Logs OTLP do produto → Loki | Provado | Evidência: `docs/ops/evidence/otel_1529_loggerprovider_loki_2026-08-12.json` |

**Não leia a presença de Redpanda ou OpenSearch no Compose como Fase D.** A Fase **C** (Loki) continua sendo o pilar de log; a Fase **D** segue opcional e **não** selecionada.

Acompanhamento da atualização do doc: [#1542](https://github.com/DataBoar/data-boar/issues/1542).

---

## 2. Notas de escolha de produto

- **Grafana** costuma ser o hub de **visualização**; liga a Prometheus, InfluxDB, Loki e muitos outros.
- **Elasticsearch** vs **OpenSearch:** para **Graylog**, siga o backend suportado pela versão; não assuma tutoriais “ELK” genéricos sem verificar versão. No lab atual, OpenSearch **não** implica Graylog.
- **InfluxDB** 3.x vs 2.x: confirma imagem/docs ao copiar Compose — há mudanças entre majors.

---

## 3. Documentação primária (nota mental — revisitar)

Marcadores **oficiais** para **Grafana, Prometheus, Loki, Graylog, OpenSearch, Elasticsearch, OpenTelemetry, backends de trace, Grafana Cloud (free tier) e comparação estilo Dynatrace:** [LAB_OP_OBSERVABILITY_LEARNING_LINKS.pt_BR.md](../ops/inspirations/LAB_OP_OBSERVABILITY_LEARNING_LINKS.pt_BR.md) ([EN](../ops/inspirations/LAB_OP_OBSERVABILITY_LEARNING_LINKS.md)). Não altera a ordem das fases em **§1**; serve ao escolher versões e ler how-tos upstream.

---

## 4. Documentação privada

URLs, retenção, LDAP e regras de firewall na LAN ficam em **`docs/private/homelab/`** (ex.: `OBSERVABILITY_RUNBOOK.md`) — **gitignored**.

---

## 5. Acompanhamento

- **PLANS_TODO.md** — linha LAB-OP observabilidade + bullet **H2**.
- **Sequenciamento (firewall → acesso → logs → Wazuh):** [PLAN_LAB_FIREWALL_ACCESS_AND_OBSERVABILITY.pt_BR.md](PLAN_LAB_FIREWALL_ACCESS_AND_OBSERVABILITY.pt_BR.md) ([EN](PLAN_LAB_FIREWALL_ACCESS_AND_OBSERVABILITY.md)) — usar quando o trabalho UniFi/L3 estiver ativo **antes** ou **em paralelo** com as fases A–F abaixo.
- **Links de aprendizado (Grafana / stack Elastic / traces):** [LAB_OP_OBSERVABILITY_LEARNING_LINKS.pt_BR.md](../ops/inspirations/LAB_OP_OBSERVABILITY_LEARNING_LINKS.pt_BR.md) ([EN](../ops/inspirations/LAB_OP_OBSERVABILITY_LEARNING_LINKS.md)).
- **LAB_OP_MINIMAL_CONTAINER_STACK.pt_BR.md** §7 — ponteiro para este plano.
- **Lembrete (quando houver hardware):** manter **syslog/logs** no caminho Loki (fase **C**) antes de adicionar **Wazuh** (fase **E**) numa **VM/torre** com RAM suficiente — checklist mínimo: [OBSERVABILITY_SYSLOG_DETECTION_CHECKLIST.pt_BR.md](../private.example/homelab/OBSERVABILITY_SYSLOG_DETECTION_CHECKLIST.pt_BR.md) ([EN](../private.example/homelab/OBSERVABILITY_SYSLOG_DETECTION_CHECKLIST.md)).
- **Atualização de status (2026-08-12):** [#1542](https://github.com/DataBoar/data-boar/issues/1542) — Fases **A**+**C** no ar; **F** parcial; **D** não adotada; inventário de receivers em **§1.1**.

**Estado:** Plano ativo (stack no lado do operador). Emit OTLP do produto em [PLAN_DATABOAR_OTEL_INSTRUMENTATION.md](completed/PLAN_DATABOAR_OTEL_INSTRUMENTATION.md). Runbooks privados em `docs/private/homelab/`.
