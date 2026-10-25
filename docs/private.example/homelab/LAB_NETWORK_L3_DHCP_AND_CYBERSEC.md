# Lab L3 — DHCP default gateway, DNS, and CyberSecure (UniFi / LAB-ROUTER-01)

**Purpose:** Capture **why** each VLAN should hand clients the **correct L3 gateway and DNS** (from that VLAN’s perspective), how that ties to **CyberSecure** (encrypted DNS, IPS, honeypots), and **how to verify** from a workstation or device. **Do not** put your live subnet table in git—copy this file to `docs/private/homelab/` and fill the inventory table with **your** RFC1918 values.

**Related:** [OPERATOR_AI_LAB_ACCESS_AND_BLUE_TEAM_RUNBOOK.md](OPERATOR_AI_LAB_ACCESS_AND_BLUE_TEAM_RUNBOOK.md) · [CREDENTIALS_AND_LAB_SECRETS.md](CREDENTIALS_AND_LAB_SECRETS.md) · [HOMELAB_UNIFI_LAB-ROUTER-01_LAB_NETWORK.md](../../ops/HOMELAB_UNIFI_LAB-ROUTER-01_LAB_NETWORK.md) · [PLAN_LAB_OP_OBSERVABILITY_STACK.md](../../plans/PLAN_LAB_OP_OBSERVABILITY_STACK.md)

---

## 1. Mental model (what “correct” means)

- On each **VLAN**, the **default gateway** for hosts is almost always the **LAB-ROUTER-01 interface IP in that subnet** (commonly **`.1`** in a `/24`).
- **DHCP** should advertise that address as the **default router** (DHCP option **3**) so clients do not inherit a gateway from another VLAN.
- **DNS** (option **6**) may be the **same** IP (LAB-ROUTER-01 as forwarder/recursor), **Pi-hole**, **split DNS**, or upstream resolvers—**per policy**; the important part is that it is **intentional** for that VLAN (IoT vs trusted, etc.).
- A **naming convention** such as “third octet = VLAN ID” helps humans and runbooks; **routing does not depend on it**—only **subnet ↔ gateway on-wire** matters.

---

## 2. UniFi — concrete checklist (per network)

Repeat for **each** VLAN/network (e.g. Default, IoT, office/work, guest):

1. **Settings → Networks** → select the network.
1. Confirm **VLAN ID** matches what you expect on switches and SSIDs.
1. Confirm **gateway / router** for that network is the **LAB-ROUTER-01 IP on that subnet** (typically **`.1`**).
1. Under **DHCP**:
   - Range stays **inside** the subnet.
   - **Router / default gateway** in DHCP = same as step 3.
   - **DNS servers** = what you want for **this** VLAN (often the LAB-ROUTER-01 `.1` if it resolves for clients; adjust if you use another resolver).
1. **Settings → WiFi** → each SSID → **network / VLAN** points to the **intended** network (e.g. IoT SSID → IoT network only).

**After changes:** renew DHCP on a test client (disconnect/reconnect Wi‑Fi or `ipconfig /release` + `/renew` on Windows).

---

## 3. CyberSecure (high level — aligns with lab notes)

These are **controller-wide or per-network** features; exact menu labels move slightly with UniFi OS versions.

| Area                           | What to record in private notes                                                           | Why it matters                                                                 |                    |                                                                                                         |
| ----                           | --------------------------------                                                          | --------------                                                                 |                    |                                                                                                         |
| **Encrypted DNS**              | Whether you use **Predefined** providers and which list (e.g. Quad9, Cloudflare variants) | Clients may bypass local policy if DNS is inconsistent—align with DHCP DNS.    |                    |                                                                                                         |
| **Intrusion Prevention (IPS)** | On/off; **which networks** are in scope; signature update date                            | Detection surface; note suppressions with **signature ID + reason** elsewhere. |                    |                                                                                                         |
| **Honeypot**                   | Table **Network                                                                           | Subnet                                                                         | Honeypot address** | Honeypot IP must sit **inside** the listed subnet; many designs use **`.2`** while gateway is **`.1`**. |

**UI tip:** At low browser zoom, **0** and **8** in the **third octet** (e.g. `…40…` vs `…48…`) are easy to misread—**zoom in** or copy values into your private inventory table.

---

## 4. Common failure modes (when “combinations” look wrong)

| Symptom                          | Likely cause                                                                             |
| -------                          | --------------                                                                           |
| Right IP range, wrong gateway    | Static IP or old DHCP lease; SSID mapped to wrong network.                               |
| DNS leaks or unexpected resolver | Client manual DNS; encrypted DNS + different DHCP DNS—**decide** authoritative behavior. |
| Honeypot “does nothing”          | Honeypot IP not in subnet; typo `192` vs `182`; wrong network row in CyberSecure.        |

---

## 5. Verification commands (no secrets)

## Windows (PowerShell):

```powershell
Get-NetIPConfiguration | Where-Object { $_.IPv4DefaultGateway -ne $null } | Format-List InterfaceAlias,IPv4Address,IPv4DefaultGateway,DnsServer
Test-NetConnection -ComputerName <gateway-ip> -Port 443
```

**Windows:** show DNS cache entries (debugging):

```powershell
Get-DnsClientCache
```

## Linux:

```bash
ip -4 route show default
resolvectl status 2>/dev/null || grep -E '^nameserver' /etc/resolv.conf
ping -c 2 <gateway-ip>
```

**Optional:** from a host that should reach the LAB-ROUTER-01 API by name:

```powershell
Resolve-DnsName unifi.local
```

(Requires split DNS or `hosts`—see runbook on **`unifi.local`** vs raw IP for TLS.)

---

## 6. Private inventory table (copy to `docs/private/homelab/` and fill)

| Network name (UniFi)  | VLAN ID | Subnet (CIDR)    | LAB-ROUTER-01 gateway | DHCP DNS (intended) | Honeypot (if any) | SSID(s) |
| --------------------- | ------- | -------------    | ----------- | ------------------- | ----------------- | ------- |
| *example: Default*    | *…*     | *10.0.x.0/24* | *.1*        | *.1 or …*           | *.2*              | *…*     |
| *example: IoT*        | *…*     | *10.0.x.0/24* | *.1*        | *…*                 | *.2*              | *…*     |

Replace `x` with **your** octets only in the **private** copy.

---

## 7. Assistant (Cursor) — capabilities tied to this topic

## Today (on your PC, same LAN):

- Read **this runbook** and private inventory when present under `docs/private/homelab/`.
- Run **UniFi Network Integration** scripts if `.env` is set: `scripts/LAB-ROUTER-01-api-smoke-from-env.ps1`, `scripts/LAB-ROUTER-01-api-inventory-from-env.ps1` (optional `-SaveJson` to private `reports/`).
- Run **SNMP** probes when `LAB_LAB-ROUTER-01_SNMP_*` (or your env file) is loaded: `scripts/snmp-LAB-ROUTER-01-lab-probe.ps1`, etc.

**Not automatic:** the assistant does **not** log into `unifi.ui.com` for you—**you** apply UI changes; it can help turn outcomes into **checklists** and **commands**.

## After more setup (future):

- **Syslog** from LAB-ROUTER-01 to **Loki** / central logs → correlate gateway events with host logs ([PLAN_LAB_OP_OBSERVABILITY_STACK.md](../../plans/PLAN_LAB_OP_OBSERVABILITY_STACK.md)).
- **Wazuh** (optional) after log pipeline is stable.
- **SSH** to LAB-ROUTER-01 or Linux hop with **dedicated key**—never store keys in the repo ([CREDENTIALS_AND_LAB_SECRETS.md](CREDENTIALS_AND_LAB_SECRETS.md)).

---

## 8. One-line reminder

*Per-VLAN DHCP gateway = LAB-ROUTER-01 `.1` on that subnet; DNS policy explicit; CyberSecure honeypot IP inside subnet; zoom UI to verify octets; private table is source of truth.*
