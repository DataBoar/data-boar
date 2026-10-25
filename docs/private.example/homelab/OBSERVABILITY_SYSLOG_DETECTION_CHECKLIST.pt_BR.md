# Lab-op — syslog + detecção (checklist mínimo)

**Copie para `docs/private/homelab/`** ao implementar; IP do colector, portas e retenção só em notas privadas. **Nunca** faça commit de detalhes reais de LAN no repositório público.

**Trilha canônica:** [PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md](../../plans/PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md) — fases **A/B** (métricas), **C** (logs), **E** (Wazuh).

---

## Caminho recomendado (leve → pesado)

| Etapa                     | O quê                                                                                                        | Porquê                                                                                                                    |
| -----                     | -----                                                                                                        | ------                                                                                                                    |
| **1 — Syslog / logs**     | **Promtail + Loki + Grafana** (fase **C** do plano)                                                          | Menor pegada que Graylog+OpenSearch; combina com métricas/SNMP depois.                                                    |
| **2 — Deteção / postura** | **Wazuh** (manager + agentes em Linux) quando houver **VM ou torre** com **≥8 GB** para a stack (fase **E**) | IDS em host, FIM, sinais de vuln; **não** substitui logs centralizados — usar **junto com** Loki ou com divisão clara.    |
| **Evitar no mesmo LAB-NODE-01**   | Correr **Loki + Graylog + Wazuh + Prometheus completo** num **LAB-NODE-01 ≤16 GB**                                   | Risco de sobrecarga já documentado no plano — **um** pilar de métricas + **um** de logs + Wazuh quando o hardware deixar. |

**Alternativas:** Graylog + OpenSearch (mais pesado, boa pesquisa texto). **Security Onion** / SIEM completo: só com hardware e tempo dedicados.

---

## Checklist mínimo — syslog (UniFi + lab)

- [ ] **Host colector** com IP fixo na LAN (VM Proxmox / torre / futuro papel servidor no LAB-NODE-01).
- [ ] **Stack:** Loki + Promtail (+ Grafana para Explore/alertas); definir **retenção** (ex.: 7–30 dias).
- [ ] **LAB-ROUTER-01:** System / logging → **syslog remoto** → colector `:514` (UDP ou TCP); **firewall** só **LAB-ROUTER-01 → colector** nessa porta.
- [ ] **Tempo:** NTP ok no LAB-ROUTER-01 e no colector (correlação de logs).
- [ ] **Runbook privado:** uma página em `docs/private/homelab/` com URL, sem segredos no git.

---

## Checklist mínimo — detecção (“meu”)

- [ ] **Linha de base:** logs centralizados (acima) antes de caçar alertas estilo SIEM.
- [ ] **Wazuh (quando der):** VM **manager** dedicada; **agentes** nos Linux do lab que importam; **excluir** caminhos ruidosos no `ossec.conf`; começar com políticas de **vulnerability + rootcheck + syscheck** sustentáveis.
- [ ] **UniFi:** manter **IPS** + notificações; syslog duplica evidência fora da caixa.
- [ ] **Alertas:** alertas Grafana em cima do Loki (padrões de falha de auth, picos anómalos) **ou** regras Wazuh — escolher **um** canal principal para o telefone (ex.: Telegram/Slack) para não virar ruído.

---

## Quando executar este checklist

Quando **[LAB_OP_MINIMAL_CONTAINER_STACK](../ops/LAB_OP_MINIMAL_CONTAINER_STACK.pt_BR.md)** §1–§3 estiver estável **e** existir host **não só laptop** ou **RAM suficiente** para serviços 24/7 — ver [PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md](../../plans/PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md).
