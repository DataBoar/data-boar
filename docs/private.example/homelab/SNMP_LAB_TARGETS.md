# SNMP targets in the lab — extra devices, `.env` files, Linux commands

**Português (Brasil):** [SNMP_LAB_TARGETS.pt_BR.md](SNMP_LAB_TARGETS.pt_BR.md)

**Purpose:** Decide whether to add **more SNMP-polled devices** (managed switch, NAS, firewall) beyond the gateway, and how to keep **one gitignored env file per target** under `docs/private/homelab/`.

---

## Is it worth it?

| Situation                                                               | Worth adding?                                                                                                          |
| ---------                                                               | -------------                                                                                                          |
| During **tests** you want **interface-level** counters (core vs switch) | Yes — light periodic IF-MIB polls or scheduled logs.                                                                   |
| **Production** monitoring, retention, dashboards                        | Prefer **Prometheus snmp_exporter** / Zabbix / vendor UI — this repo only provides **manual / Task Scheduler probes**. |
| Device is **SNMPv2c-only**                                              | Current script is **v3 SHA/AES**; use **manual `snmpwalk`** (examples in pt-BR doc and below).                         |

---

## File pattern (multiple devices)

**One file per target**, **same four keys** (`LAB_LAB-ROUTER-01_SNMP_*` — legacy name; valid for **any** SNMPv3 target):

| Example file             | Device                                                                     |
| ------------             | ------                                                                     |
| `.env.snmp.local`        | Gateway / LAB-ROUTER-01 (Windows script default)                                     |
| `.env.snmp.LAB-ROUTER-01-se.local` | **LAB-ROUTER-01 SE** (or another gateway with a dedicated env file — same key names) |
| `.env.snmp.switch.local` | Managed switch                                                             |
| `.env.snmp.nas.local`    | NAS (if it exposes SNMPv3 and useful OIDs)                                 |

## PowerShell (Windows + WSL):

```powershell
.\scripts\snmp-LAB-ROUTER-01-lab-probe.ps1 -EnvFile docs\private\homelab\.env.snmp.switch.local -WslDistro Debian
.\scripts\snmp-LAB-ROUTER-01-lab-probe-to-log.ps1 -EnvFile docs\private\homelab\.env.snmp.switch.local -WslDistro Debian -MaxLines 200
```

Tracked template with **synthetic** values: **`env.snmp.switch.local.example`**.

**Task Scheduler:** add **`-EnvFile "docs\private\homelab\.env.snmp.LAB-ROUTER-01-se.local"`** to the `powershell.exe` **Arguments** when you are not using the default `.env.snmp.local`.

### Lab observability (later)

Repo probes are **ad-hoc** (CLI + gitignored logs). For **retention, alerts, and dashboards**, consider a lab stack such as:

- **Prometheus** + **snmp_exporter**
- **Zabbix**
- **Uptime Colleague-Ma** (uptime-focused; SNMP support is limited)
- **Netdata**
- **Wazuh** (lab SIEM — vulns, hardening, centralized security reporting; **after** lab-op minimal stack — see [LAB_OP_MINIMAL_CONTAINER_STACK.md](../../ops/LAB_OP_MINIMAL_CONTAINER_STACK.md) §6)
- **Full observability sequence** (Grafana, Prometheus or InfluxDB, Loki or Graylog+OpenSearch): [PLAN_LAB_OP_OBSERVABILITY_STACK.md](../../plans/PLAN_LAB_OP_OBSERVABILITY_STACK.md)

The NMS becomes the **operational source of truth**; this repo stays useful for **debug** and **documented** OIDs/commands.

---

## Linux (lab-op hosts)

**Prerequisite:** `sudo apt install -y snmp` (or distro equivalent).

**Repo script** (from clone root):

```bash
bash scripts/snmp-lab-ifwalk.sh docs/private/homelab/.env.snmp.local
bash scripts/snmp-lab-ifwalk.sh docs/private/homelab/.env.snmp.switch.local
```

**Full manual walk** (synthetic values — replace with yours):

```bash
export LAB_LAB-ROUTER-01_SNMP_HOST=192.0.2.10
export LAB_LAB-ROUTER-01_SNMP_V3_USER=synth_oper
export LAB_LAB-ROUTER-01_SNMP_AUTH_PASS=Syn_Auth_7kQm9pL2vN4wR8xT1
export LAB_LAB-ROUTER-01_SNMP_PRIV_PASS=Syn_Priv_3mK8nQ5wZ2cV6hJ0

snmpwalk -v3 -l authPriv -u "$LAB_LAB-ROUTER-01_SNMP_V3_USER" \
  -a SHA -A "$LAB_LAB-ROUTER-01_SNMP_AUTH_PASS" \
  -x AES -X "$LAB_LAB-ROUTER-01_SNMP_PRIV_PASS" \
  "$LAB_LAB-ROUTER-01_SNMP_HOST" \
  1.3.6.1.2.1.2.2
```

**SNMPv2c** (treat community string as a password):

```bash
snmpwalk -v2c -c "SYN_COMMUNITY_STR" 192.0.2.20 1.3.6.1.2.1.2.2
```

**Firewall:** allow **UDP 161** from the polling host to the device **management** IP — do not expose SNMP to the WAN.

---

## CI (GitHub Actions) and “live” collection

**GitHub-hosted runners** have **no network path** to your LAN or your gateway management IP. **SNMP (UDP 161)** from a default workflow to your LAB-ROUTER-01 **will not work** — we do **not** add a standard repo workflow that runs `snmp-LAB-ROUTER-01-lab-probe` like on your dev PC.

| Approach                                                             | Works?                                                                             |
| --------                                                             | ------                                                                             |
| **Task Scheduler on your Windows PC** (e.g. every **30 minutes**)    | Yes — recommended for local log review.                                            |
| **Self-hosted runner** on a host **on the same LAN** as the firewall | Possible with ops overhead and security trade-offs — only with an explicit policy. |
| **Prometheus snmp_exporter** / NMS in the lab                        | Better for continuous metrics.                                                     |

We keep SNMP probes **operator-side** (gitignored logs + scheduler), not in default public CI.

---

## Privacy

Output may include **MAC addresses**, interface names, and **traffic counters** — keep under `docs/private/`, never commit.

**Related:** [CREDENTIALS_AND_LAB_SECRETS.md](CREDENTIALS_AND_LAB_SECRETS.md) · [HOMELAB_UNIFI_LAB-ROUTER-01_LAB_NETWORK.md](../../ops/HOMELAB_UNIFI_LAB-ROUTER-01_LAB_NETWORK.md) · [reports/README.md](reports/README.md)
