# Operator facts — fill once and reuse (gitignored — never on GitHub)

**Português (Brasil):** [OPERATOR_RETEACH.pt_BR.md](OPERATOR_RETEACH.pt_BR.md)

**Purpose:** Single place to **add / edit** what you “re-teach” the assistant so it can **`read_file`** this path **without `@`** (repo default). **Do not commit** real facts — keep them under **`docs/private/homelab/`** only.

**Language:** This **tracked template** is **English**; your **private** copy may be **pt-BR only** or you may maintain both languages locally — either way, use **Brazilian Portuguese** if you write in Portuguese (see **`.cursor/rules/docs-pt-br-locale.mdc`**).

**Suggested agent read order:** `AGENT_LAB_ACCESS.md` → **`OPERATOR_SYSTEM_MAP.md`** → **`LAB_SOFTWARE_INVENTORY.md`** → **`OPERATOR_RETEACH.md`** (this file, private) → `HARDWARE_CATALOG.md` / `WHAT_TO_SHARE_WITH_AGENT.md` as needed.

---

## A. Already in other private files (do not repeat unless correcting)

- Host aliases, hardware nicknames, API ports, paths — see **`AGENT_LAB_ACCESS.md`**, **`HARDWARE_CATALOG.md`**, **`WHAT_TO_SHARE_WITH_AGENT.md`**.

---

## B. Fill in under each heading (private copy)

### B1 — Primary workstation (exact hardware)

- **MTM / product number:** …
- **BIOS / system firmware:** …
- **CPU (exact model):** …
- **RAM:** …
- **Main disk (size + rough % used):** …

### B2 — Electrical / HVAC (measured or nameplate)

- **Context (city / site):** …
- **Kill-A-Watt** (W) per device or “TBD”
- **UPS** nameplate (VA / W) if applicable
- **Split AC / cooling** (installed vs spare): use tables for **model**, **electrical**, **refrigerant** — **no** secrets

### B3 — UniFi / LAN (internal only)

- **WAN → LAN / NAT:** …
- **Site / console labels / versions:** …
- **VLANs / subnets:** …
- **Wi‑Fi SSIDs → network mapping (no passwords):** …
- **SNMP:** version, which host polls (role only)

### B4 — Solar (no API secrets here)

- **Inverter** make + model
- **Datalogger** model
- **App** name (optional)
- **Cloud portal** URL pattern (no passwords)
- **Logger IP / VLAN**
- **Stack** (vendor family)

### B5 — Secondary Linux runner (optional “burst” host)

- **Model / MTM / role**
- **OS:** e.g. Ubuntu LTS + Docker
- **After first session:** RAM/SSD/CPU note, hostname, IP range, SSH `Host` alias → update **`OPERATOR_SYSTEM_MAP`** + **`LAB_SOFTWARE_INVENTORY`**

### B6 — Chat context not yet on disk

- Pointers to **`LAB_SECURITY_POSTURE.md`**, **`LAB_SOFTWARE_INVENTORY.md`**, firewall dumps, etc.

#### Filling B1–B6 — next steps (operator)

| Block  | You do                                                        | Mirror into                                                    |
| -----  | ------                                                        | -------------                                                  |
| **B1** | Confirm BIOS/MTM from vendor tools                            | This section + optional **`WHAT_TO_SHARE_WITH_AGENT.md`**      |
| **B2** | Nameplates / optional measurements                            | **B2** bullets                                                 |
| **B3** | UniFi settings export (versions, SNMP role)                   | **B3** + **`LAB_SECURITY_POSTURE.md`**                         |
| **B4** | Inverter faceplate + app name                                 | **B4**                                                         |
| **B5** | Install OS + Docker; run **`scripts/homelab-host-report.sh`** | Map + inventory + **`HARDWARE_CATALOG`**                       |
| **B6** | Runtime versions per host                                     | **`LAB_SOFTWARE_INVENTORY.md`**, **`LAB_SECURITY_POSTURE.md`** |

---

## C. Last update (private)

**Date:** YYYY-MM-DD · **By:** operator

**Notes:** Free text — still **no passwords** or **API keys** in this file.

---

## Automation note (no lab hostnames in the repo)

To **POST `/scan`** and poll **`/status`** on any Data Boar base URL, use **`scripts/poll_dashboard_scan.py`** with **`--base`** or **`DATA_BOAR_BASE`** — not a one-off under **`.cursor/`** with a hardcoded hostname.
