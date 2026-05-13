# Lab-op — firewall / L3, acesso ao assistente, postura de segurança, observabilidade (sequenciado)

**Status:** Pending
**Date:** 2026-03-24
**Authors:** Fabio Leitao
**Priority:** H2

**English:** [PLAN_LAB_FIREWALL_ACCESS_AND_OBSERVABILITY.md](PLAN_LAB_FIREWALL_ACCESS_AND_OBSERVABILITY.md)

**Finalidade:** Uma **espinha dorsal ordenada** para o trabalho de homelab que começou com **ajuste de UniFi / firewall**: alinhar **L3 + DHCP + DNS** por VLAN, permitir **automação segura com Cursor** no PC do operador, registar **postura de segurança** (CyberSecure, IPS, honeypots, cadência) e depois **observabilidade** — **syslog → Loki** antes de **Wazuh** — sem assumir que tudo corre ao mesmo tempo num portátil pequeno.

**No âmbito:** Infraestrutura e fluxos do operador em **`docs/private/`** (verdade) e **`docs/private.example/homelab/`** (modelos). **Fora do âmbito:** código da aplicação Data Boar (ver planos de produto à parte).

## Relação com outros planos e docs

| Tema                                           | Referência canônica                                                                                                                       |
| ----                                           | -------------------                                                                                                                       |
| **Fases** de métricas/logs/SIEM (A–E)          | [PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md](PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md)                                                      |
| Checklist DHCP, DNS, honeypot CyberSecure      | [LAB_NETWORK_L3_DHCP_AND_CYBERSEC.pt_BR.md](../private.example/homelab/LAB_NETWORK_L3_DHCP_AND_CYBERSEC.pt_BR.md)                         |
| Capacidades do assistente + cadência blue team | [OPERATOR_AI_LAB_ACCESS_AND_BLUE_TEAM_RUNBOOK.pt_BR.md](../private.example/homelab/OPERATOR_AI_LAB_ACCESS_AND_BLUE_TEAM_RUNBOOK.pt_BR.md) |
| Checklist syslog e detecção                     | [OBSERVABILITY_SYSLOG_DETECTION_CHECKLIST.pt_BR.md](../private.example/homelab/OBSERVABILITY_SYSLOG_DETECTION_CHECKLIST.pt_BR.md)         |
| Stack mínima de contentores antes do pesado    | [LAB_OP_MINIMAL_CONTAINER_STACK.pt_BR.md](../ops/LAB_OP_MINIMAL_CONTAINER_STACK.pt_BR.md) §1–§7                                           |
| UniFi + SNMP                                   | [HOMELAB_UNIFI_LAB-ROUTER-01_LAB_NETWORK.pt_BR.md](../ops/HOMELAB_UNIFI_LAB-ROUTER-01_LAB_NETWORK.pt_BR.md)                                                   |

**Regra de hardware (inalterada):** Não planejar correr **Prometheus + Loki + Graylog/OpenSearch + Wazuh + k3s completo** em simultâneo num portátil **≤16 GB RAM**. Preferir **um** caminho de métricas, **um** de logs, **Wazuh** numa **VM/torre** quando estiver pronto.

---

## Sequência recomendada (fases 0–5)

Ordem **obrigatória** salvo hardware já existente para uma fase posterior (ex.: saltar métricas leves se só quiser logs — mantém sempre a **fase 0** primeiro).

| Fase  | Nome                               | Objetivo                                                                                                                                        | Entregas principais                                                                                                                                                                            |
| ----  | ----                               | --------                                                                                                                                        | -------------------                                                                                                                                                                            |
| **0** | **L3 + baseline de firewall**      | Por VLAN: DHCP **router padrão** = LAB-ROUTER-01 nessa subnet; DNS intencional; SSID ↔ rede certa; regras de firewall alinhadas (isolamento IoT, gestão). | Tabela privada a partir de [LAB_NETWORK_L3_DHCP_AND_CYBERSEC.pt_BR.md](../private.example/homelab/LAB_NETWORK_L3_DHCP_AND_CYBERSEC.pt_BR.md); opcional **`LAB_SECURITY_POSTURE.md`** (privado) |
| **1** | **Acesso seguro ao assistente**    | `.env` API (gitignored), confiança TLS para `<https://unifi.loca>l` (ou hostname), scripts smoke + inventário OK no terminal do Cursor.         | `scripts/LAB-ROUTER-01-api-smoke-from-env.ps1`, `LAB-ROUTER-01-api-inventory-from-env.ps1` (opcional `-SaveJson` em `reports/` privado); sem chaves no git nem no chat                                             |
| **2** | **Perfil de segurança + cadência** | CyberSecure: DNS encriptado documentado; âmbito IPS e frescura de assinaturas; honeypots **dentro** das subnets; supressões com ID + motivo.    | [OPERATOR_AI_LAB_ACCESS_AND_BLUE_TEAM_RUNBOOK.pt_BR.md](../private.example/homelab/OPERATOR_AI_LAB_ACCESS_AND_BLUE_TEAM_RUNBOOK.pt_BR.md) §2–§4; revisões trimestrais/anuais                   |
| **3** | **Métricas (opcional)**            | Grafana + **Prometheus** *ou* **InfluxDB** — escolher **um** pilar TSDB.                                                                        | Fase **A** ou **B** do plano de observabilidade                                                                                                                                                |
| **4** | **Syslog + Loki**                  | LAB-ROUTER-01 (e opcionalmente hosts Linux) enviam logs para **Promtail + Loki + Grafana**; firewall só o necessário **coletor ← LAB-ROUTER-01**.                   | Fase **C** + [OBSERVABILITY_SYSLOG_DETECTION_CHECKLIST.pt_BR.md](../private.example/homelab/OBSERVABILITY_SYSLOG_DETECTION_CHECKLIST.pt_BR.md)                                                 |
| **5** | **Wazuh (opcional)**               | SIEM/agentes para correlação **depois** dos logs úteis; manager em VM com **RAM** adequada.                                                     | Fase **E**; [LAB_OP_MINIMAL_CONTAINER_STACK.pt_BR.md](../ops/LAB_OP_MINIMAL_CONTAINER_STACK.pt_BR.md) §6                                                                                       |

**Dependência:** **Fase 4** (logs centralizados) antes da **5** (Wazuh) reduz ruído e melhora correlação.

---

## To-dos tipo sprint (checklist do operador)

| # | Tarefa                                                                                               | Fase |
| - | ------                                                                                               | ---- |
| 1 | Copiar modelos **LAB_NETWORK** + **OPERATOR_AI** para `docs/private/homelab/` se ainda não existirem | 0–2  |
| 2 | Por rede UniFi: gateway DHCP + DNS coerentes com a VLAN; mapeamento Wi‑Fi ↔ VLAN verificado          | 0    |
| 3 | Renovar DHCP num cliente por VLAN; correr comandos de verificação do LAB_NETWORK                     | 0    |
| 4 | Criar **`.env`** da API; correr **smoke** e **inventário**; JSON só em `reports/` privado            | 1    |
| 5 | (Opcional) **`.env`** SNMP + `scripts/snmp-LAB-ROUTER-01-lab-probe.ps1` a partir de host confiável             | 1    |
| 6 | Documentar supressões IPS + linhas honeypot + DNS encriptado nas notas privadas                      | 2    |
| 7 | (Opcional) Subir **Grafana + Prometheus** ou **Influx** no host ou VM do lab                         | 3    |
| 8 | Apontar **syslog** do LAB-ROUTER-01 para Promtail; confirmar linhas no **Loki** / Grafana Explore              | 4    |
| 9 | (Opcional) **Wazuh** manager + agentes                                                               | 5    |

---

## Comandos e scripts (referência — sem segredos no repositório)

| Ação                               | Comando / script                                                         |
| ----                               | ----------------                                                         |
| Smoke API (com `.env` na sessão)   | `.\scripts\LAB-ROUTER-01-api-smoke-from-env.ps1`                                   |
| Inventário API                     | `.\scripts\LAB-ROUTER-01-api-inventory-from-env.ps1` (opcional `-SaveJson`)        |
| Probe SNMP (variáveis de ambiente) | `.\scripts\snmp-LAB-ROUTER-01-lab-probe.ps1`                                       |
| Relatórios hosts                   | `.\scripts\lab-op-sync-and-collect.ps1` (manifest em `homelab/` privado) |
| Windows: gateway/DNS               | `Get-NetIPConfiguration` (ver doc LAB_NETWORK)                           |

---

## Acompanhamento

- **Lista central:** [PLANS_TODO.md](PLANS_TODO.md) — subseção *LAB-OP — firewall, acesso, observabilidade*.
- **Detalhe de observabilidade:** [PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md](PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md).
- **Estado:** 🔄 Plano de sequenciamento ativo — progresso nas notas privadas e opcionalmente marcas na checklist deste arquivo.

**Sincronizado com:** [PLANS_TODO.md](PLANS_TODO.md).
