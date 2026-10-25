# Lab-op — syslog + detection (minimal checklist)

**Copy to `docs/private/homelab/`** when you implement; add collector IP, ports, and retention only in private notes. **Never commit** real LAN details to the public repo.

**Canonical stack guidance:** [PLAN_LAB_OP_OBSERVABILITY_STACK.md](../../plans/PLAN_LAB_OP_OBSERVABILITY_STACK.md) — phases **A/B** (metrics), **C** (logs), **E** (Wazuh).

---

## Recommended path (light → heavy)

| Stage                           | What                                                                                                              | Why                                                                                                                             |
| -----                           | ----                                                                                                              | ---                                                                                                                             |
| **1 — Syslog / logs**           | **Promtail + Loki + Grafana** (“LGTM”, plan phase **C**)                                                          | Lower footprint than Graylog+OpenSearch; fits homelab; pairs with SNMP/metrics later.                                           |
| **2 — Detection / posture**     | **Wazuh** (manager + agents on Linux hosts) when a **VM or tower** has **≥8 GB** for the stack (plan phase **E**) | Host IDS, FIM, vuln signals; **not** a substitute for centralized logs — use **with** Loki or a clear split.                    |
| **Defer / avoid on one laptop** | Running **Loki + Graylog + Wazuh + full Prometheus** all on a **≤16 GB LAB-NODE-01**                                      | Documented overload risk in the observability plan — **one** metrics pillar + **one** logs pillar + Wazuh when hardware allows. |

**Alternatives:** Graylog + OpenSearch (heavier, full-text power). **Security Onion** / full SIEM: overkill until you have dedicated hardware and time.

---

## Minimal checklist — syslog (UniFi + lab)

- [ ] **Collector host** with static LAN IP (VM on Proxmox / tower / future LAB-NODE-01 server role).
- [ ] **Stack:** Loki + Promtail (+ Grafana for Explore/alerts); define **retention** (e.g. 7–30 days).
- [ ] **LAB-ROUTER-01:** System / logging → **remote syslog** → collector `:514` (UDP or TCP); **firewall** allow **only** LAB-ROUTER-01 → collector on that port.
- [ ] **Time sync:** NTP OK on LAB-ROUTER-01 and collector (log correlation).
- [ ] **Private runbook:** one page in `docs/private/homelab/` with URL, no secrets in git.

---

## Minimal checklist — detection (“meu”)

- [ ] **Baseline:** centralized logs (above) before chasing SIEM-style alerts.
- [ ] **Wazuh (when ready):** dedicated **manager** VM; **agents** on lab Linux hosts you care about; **exclude** noisy paths in `ossec.conf`; start with **vulnerability + rootcheck + syscheck** policies you can sustain.
- [ ] **UniFi:** keep **IPS** + notifications; syslog duplicates evidence off-box.
- [ ] **Alerting:** Grafana alerts on Loki (failed auth patterns, new outbound spikes) **or** Wazuh rules — pick **one** primary channel to your phone (e.g. Telegram/Slack) to avoid noise.

---

## Reminder trigger

Schedule this checklist when **LAB_OP_MINIMAL_CONTAINER_STACK** §1–§3 is stable **and** a **non-laptop** or **RAM-upgraded** host is available for 24/7 services — see [PLAN_LAB_OP_OBSERVABILITY_STACK.md](../../plans/PLAN_LAB_OP_OBSERVABILITY_STACK.md).
