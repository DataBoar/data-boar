# Stack de observabilidade no lab-op — métricas, logs, dashboards (só plano)

**Status:** Pending
**Date:** 2026-03-24
**Authors:** Fabio Leitao
**Priority:** H2

**English:** [PLAN_LAB_OP_OBSERVABILITY_STACK.md](PLAN_LAB_OP_OBSERVABILITY_STACK.md)

**Objetivo:** Ordenar instrumentação **opcional** do homelab — **Grafana**, bases de séries temporais, **centralização de logs** — sem bloquear desenvolvimento do Data Boar nem a validação **–1L**. **Sem** implementação neste repositório; o operador instala via Compose, Helm no k3s ou appliance na **lab-op** (LAB-NODE-01, LAB-NODE-02, VMs Proxmox).

## Pré-requisitos (antes disto):

| Passo                                               | Documento                                                                                                                          |
| -----                                               | ---------                                                                                                                          |
| SO + baseline segura de dev no portátil             | [LMDE7_LAB-NODE-01_DEVELOPER_SETUP.pt_BR.md](../ops/LMDE7_LAB-NODE-01_DEVELOPER_SETUP.pt_BR.md) ([EN resumo](../ops/LMDE7_LAB-NODE-01_DEVELOPER_SETUP.md)) |
| Stack mínima de contentores (Podman + k3s opcional) | [LAB_OP_MINIMAL_CONTAINER_STACK.pt_BR.md](../ops/LAB_OP_MINIMAL_CONTAINER_STACK.pt_BR.md) §1–§3                                    |
| Probes SNMP / firewall (opcional)                   | [SNMP_LAB_TARGETS.pt_BR.md](../private.example/homelab/SNMP_LAB_TARGETS.pt_BR.md)                                                  |

**Realidade de hardware:** LAB-NODE-01 com **≤16 GB RAM** não deve correr Prometheus + Loki + Graylog + OpenSearch + Wazuh + k3s **em simultâneo**. Escolha **um** caminho de métricas e **um** de logs; stacks pesados no **torre/VM Proxmox** quando existir.

---

## 1. Sequência recomendada (leve → pesada)

| Fase  | Stack                                                              | Função                                          | Notas                                                                                                                                                                                                                |
| ----  | -----                                                              | ------                                          | -----                                                                                                                                                                                                                |
| **A** | **Grafana** + **Prometheus** (+ `node_exporter` / `snmp_exporter`) | Métricas, dashboards, alertas (PromQL)          | **Recomendação predefinida** para homelab. Alinha com a narrativa de monitorização em [SNMP_LAB_TARGETS.pt_BR.md](../private.example/homelab/SNMP_LAB_TARGETS.pt_BR.md).                                             |
| **B** | **Grafana** + **InfluxDB** (+ **Telegraf**)                        | Métricas se preferir InfluxQL/Flux            | Alternativa válida ao TSDB do Prometheus; escolha **um** pilar TSDB (Prometheus **ou** Influx), salvo divisão explícita (ex.: SNMP no Prometheus, métricas de app no Influx).                                        |
| **C** | **Promtail** + **Loki** + **Grafana**                              | Agregação de logs, pegada menor que ELK/Graylog | Família “LGTM”; bom para envio de **JSON/syslog** e Explore no Grafana.                                                                                                                                              |
| **D** | **Graylog** + **OpenSearch**                                       | Busca full-text, streams, pipelines             | **Graylog 5+** usa **OpenSearch** por padrão — ver documentação atual; **Elasticsearch** já não é o default universal. **Pesado:** reserva **≥8 GB** só para OpenSearch em labs pequenos; preferir **VM dedicada**. |
| **E** | **Wazuh**                                                          | Postura de segurança, vulns, hardening          | [LAB_OP_MINIMAL_CONTAINER_STACK.pt_BR.md](../ops/LAB_OP_MINIMAL_CONTAINER_STACK.pt_BR.md) §6 — complementa métricas/logs; não os substitui. **NIST/CIS:** [WAZUH_NIST_CIS_LABOP_ALIGNMENT.pt_BR.md](../ops/inspirations/WAZUH_NIST_CIS_LABOP_ALIGNMENT.pt_BR.md). |
| **F** | **Traces / estilo APM** (escolher **um** de início)                | Fluxos de pedido, latência, dependências        | Profundidade estilo **Dynatrace** sem SaaS por padrão: **SigNoz**, **Grafana Tempo** + **OpenTelemetry**, **Jaeger** ou **Netdata** leve; **Dynatrace** = trial/enterprise — ver **§3**. VM depois de **A** + **C** estáveis. |

**Evitar no mesmo LAB-NODE-01 em simultâneo:** Graylog + OpenSearch + Prometheus completo + Loki + Wazuh + k3s + backend de traces. Escolha **A ou B**, **C ou D**, **E** quando houver recursos, **F** quando traces justificarem a RAM (muitas vezes **VM** à parte).

---

## 2. Notas de escolha de produto

- **Grafana** costuma ser o hub de **visualização**; liga a Prometheus, InfluxDB, Loki e muitos outros.
- **Elasticsearch** vs **OpenSearch:** para **Graylog**, siga o backend suportado pela versão; não assuma tutoriais “ELK” genéricos sem verificar versão.
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
- **Lembrete (quando houver hardware):** primeiro **syslog/logs** (**Promtail + Loki + Grafana**, fase **C**); depois **Wazuh** (fase **E**) numa **VM/torre** com RAM suficiente — checklist mínimo: [OBSERVABILITY_SYSLOG_DETECTION_CHECKLIST.pt_BR.md](../private.example/homelab/OBSERVABILITY_SYSLOG_DETECTION_CHECKLIST.pt_BR.md) ([EN](../private.example/homelab/OBSERVABILITY_SYSLOG_DETECTION_CHECKLIST.md)).

**Estado:** ⬜ Só plano — sem código no repo até um runbook do operador justificar um PR pequeno (ex.: Compose de exemplo **sem segredos** em `docs/private.example/`).
