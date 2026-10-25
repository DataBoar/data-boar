# Operator runbook — AI assistant access, security rationale, and blue-team next steps

**Copy to `docs/private/homelab/`** and fill host-specific details. **Never commit** real IPs, keys, or tokens. This file is a **memory aid** for *why* decisions were made and *what* to enable next— not a substitute for change control.

**Related:** [CREDENTIALS_AND_LAB_SECRETS.md](CREDENTIALS_AND_LAB_SECRETS.md) · [LAB_NETWORK_L3_DHCP_AND_CYBERSEC.md](LAB_NETWORK_L3_DHCP_AND_CYBERSEC.md) · [OBSERVABILITY_SYSLOG_DETECTION_CHECKLIST.md](OBSERVABILITY_SYSLOG_DETECTION_CHECKLIST.md) · [PLAN_LAB_OP_OBSERVABILITY_STACK.md](../../plans/PLAN_LAB_OP_OBSERVABILITY_STACK.md)

---

## 1. Why this runbook exists

Homelab and UniFi choices accumulate fast. Without notes, it is easy to forget **intent** (why a rule or suppression exists) and to under-invest in **evidence** (logs, alerts, review cadence). This document ties together:

- **Operational security** (what to revisit and when).
- **Assistant (Cursor) access** (what the assistant can use *from your workstation*—never a separate cloud identity).
- **Blue-team maturity** (visibility, detection, response)—incremental, lab-realistic.

---

## 2. Decisions to remember (do not “clean up” blindly)

Record **your** live values in the private copy only.

| Topic                               | Typical intent                                                                                                           | Before changing                                                                                                                                                                |
| -----                               | --------------                                                                                                           | ----------------                                                                                                                                                               |
| **TLS / `unifi.local` vs IP**       | Certificate SAN matches **hostname**; using **HTTPS by IP** breaks validation (`WRONG_PRINCIPAL`).                       | Keep **`hosts`** / DNS mapping; API base URL = `<https://unifi.loca>l` in `.env`.                                                                                              |
| **API keys (UniFi Integrations)**   | **Owner** often required to **create/revoke** keys; automation accounts may **use** keys without seeing Integrations UI. | Rotate after paste/leak; name keys by purpose + date.                                                                                                                          |
| **IPS suppression (e.g. SSH scan)** | Reduce **false positives** or noise from known lab behaviour.                                                            | Document **signature ID + reason + date**; review yearly.                                                                                                                      |
| **Content filter policy names**     | Names like “Off” while filters are on confuse future you.                                                                | Rename to match reality (e.g. `Trusted-filtered`).                                                                                                                             |
| **Honeypot / subnet typos**         | Wrong prefix (e.g. `182.x` vs `192.x`) breaks coverage.                                                                  | Verify honeypot IP sits **inside** the intended VLAN; at low UI zoom, **0** vs **8** in an octet is easy to misread—confirm in your private inventory.                         |
| **Per-VLAN DHCP gateway + DNS**     | Clients must get the **LAB-ROUTER-01 `.1` (or chosen GW)** for **that** subnet, not another VLAN’s gateway.                        | UniFi **Networks → DHCP** + **WiFi → correct VLAN**; fill [LAB_NETWORK_L3_DHCP_AND_CYBERSEC.md](LAB_NETWORK_L3_DHCP_AND_CYBERSEC.md) private table; renew lease after changes. |
| **Double NAT on WAN**               | ISP CPE in front of LAB-ROUTER-01; acceptable but affects **port forward**, **VPN**, some games.                                   | Document “double NAT accepted” or plan bridge/public IP.                                                                                                                       |
| **IoT isolation + exceptions**      | Default **deny** IoT → internal; **allow** only documented paths (e.g. management from trusted VLAN).                    | Re-run review after any VLAN or IoT device change.                                                                                                                             |

---

## 3. What to give the assistant later (safe autonomy on *your* PC)

The assistant has **no** Ubiquiti account. It runs **only** in Cursor on **your** machine, using **your** shell and files.

| Capability                        | How                                                                                                                                        | Secrets                                                  |
| ----------                        | ---                                                                                                                                        | -------                                                  |
| **UniFi Network Integration API** | `.env` in `docs/private/homelab/` (e.g. `.env.api.LAB-ROUTER-01-se.local`), `LAB_LAB-ROUTER-01_API_BASE_URL=<https://unifi.loca>l`, verify TLS trust.          | API key **never** in git; rotate if exposed.             |
| **Smoke / inventory scripts**     | `scripts/LAB-ROUTER-01-api-smoke-from-env.ps1`, `scripts/LAB-ROUTER-01-api-inventory-from-env.ps1` (optional `-SaveJson` to private `reports/`).               | Same as above.                                           |
| **SSH to LAB-ROUTER-01 (optional)**         | Dedicated Linux user + **dedicated ed25519 key**; `~/.ssh/config` `Host` entry; restrict **management** to trusted source IPs if possible. | Private key only on **your** workstation; never in repo. |
| **SNMP probes**                   | `.env.snmp.*` gitignored; scripts under `scripts/snmp-*.ps1`.                                                                              | Community / v3 creds only in private env.                |

**Do not:** paste live API keys or passwords into chat. **Do:** revoke and rotate if exposure is suspected.

---

## 4. Operational security — ongoing

| Cadence                           | Action                                                                                                                           |
| -------                           | ------                                                                                                                           |
| **Monthly**                       | Skim **Alarm Manager** / ISP drops; confirm **IPS signature date** fresh; spot-check **firmware** drift on UniFi devices.        |
| **Quarterly**                     | **Firewall / IoT matrix** review: VLAN list vs rules; remove stale **allow** rules; confirm **DNS** path for IoT still intended. |
| **After any VLAN or SSID change** | Re-validate **guest isolation**, **management** access, and **exceptions** (document in private notes).                          |

---

## 5. Observability — next steps (lab consolidation)

Aligned with [PLAN_LAB_OP_OBSERVABILITY_STACK.md](../../plans/PLAN_LAB_OP_OBSERVABILITY_STACK.md):

1. **Phase C (logs):** **Promtail + Loki + Grafana** (or single VM) — point **LAB-ROUTER-01 Activity Logging / syslog** to collector; firewall **LAB-ROUTER-01 → collector** only.
1. **Retention + disk:** define days; avoid filling small disks on laptops.
1. **Optional Phase E:** **Wazuh** manager on a **VM with enough RAM**; agents on lab Linux hosts—**after** logs are centralized.

---

## 6. Blue-team capacity (realistic ladder)

| Level               | Focus                                                                                                       |
| -----               | -----                                                                                                       |
| **0 — Evidence**    | Centralized **logs** + correct **time** (NTP).                                                              |
| **1 — Detection**   | UniFi **IPS/IDS** + **notifications**; Grafana/Loki **alerts** on auth failures / spikes (when logs exist). |
| **2 — Correlation** | Same timestamp window across **gateway**, **hosts**, and **apps** (syslog + optional Wazuh).                |
| **3 — Response**    | Written **playbook** in private: “if WAN down”, “if IPS fires”, “if key leaked”.                            |

This repo’s Data Boar product is separate; **lab blue-team** stays in **private** runbooks and observability plans.

---

## 7. One-line reminder for next session

*“Private `.env` for UniFi API; `unifi.local` not IP; Owner rotates keys; expand syslog before Wazuh; quarterly IoT/firewall review.”*
