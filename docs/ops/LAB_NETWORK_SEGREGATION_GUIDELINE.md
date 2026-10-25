# Lab network segregation — generic guideline (public)

**Português (Brasil):** [LAB_NETWORK_SEGREGATION_GUIDELINE.pt_BR.md](LAB_NETWORK_SEGREGATION_GUIDELINE.pt_BR.md)

**Status:** **Stub** — expand when maintainers have time. This page is intentionally **generic**: it helps **collaborators** reason about **VLAN segregation** and **firewall rule order** without copying **site-specific** facts into Git.

**Private counterpart:** A **concrete** UniFi runbook with real subnets, hostnames, and operator policy belongs only under **`docs/private/homelab/`** (gitignored). Do **not** paste RFC1918 LAN maps, third-party corporate ranges, or **named** commercial security/SaaS endpoints into **tracked** Markdown.

---

## 1. Audience and scope

| In scope here | Out of scope here |
| --------------- | ----------------- |
| **Logical** pattern: lab VLAN vs trusted LAN vs untrusted internal ranges | Your **actual** VLAN IDs, IPs, SSIDs, or company names |
| **Rule ordering** ideas (deny specific paths before permit WAN) | Product-specific blocklists that change often |
| Reminder to keep **DNS/DHCP** intentional per VLAN | Step-by-step for a **specific** controller UI build |

---

## 2. Threat model (one paragraph)

A **lab laptop** may need **Internet** access for **OS and firmware updates** while **not** initiating sessions toward **third-party networks** you do not trust (consulting LANs, client VPNs, shared office Wi‑Fi ranges, etc.). **Segmentation** on the gateway (e.g. UniFi **Traffic Rules**) plus **DNS policy** reduces **accidental** cross-talk more than “same SSID, hope for the best.”

---

## 3. Generic pattern (no vendor-specific blocklists)

1. **Dedicated VLAN (and usually SSID)** for **lab-only** devices — separate from “daily driver” or **guest/IoT** networks.
1. **Address groups** on the gateway: (a) **lab servers** you still need (SSH, app ports), (b) **untrusted internal prefixes** to block — **filled only in private notes**, not here.
1. **Firewall / traffic rules — suggested order:**
   - **Block** → untrusted internal groups (from §3.1b).
   - **Allow** → trusted lab server group (minimal ports if the UI supports it).
   - **Allow** → **Internet** / WAN for updates and normal HTTPS.
   - Optional: **block** management VLAN access from the lab laptop if you always administer the gateway from another station.
1. **DNS:** serve **consistent** resolvers per VLAN; avoid silently sending lab DNS to a **corporate** resolver you do not control unless that is an explicit decision.
1. **Verification:** from the lab host, confirm **default gateway**, **DNS**, **HTTPS to a well-known test host**, and **expected failure** toward a **documented-private** test IP in an untrusted range.

---

## 4. What never belongs in this public doc

- **Real** hostnames or **RFC1918** addresses from your LAN.
- **Customer**, **consulting**, or **employer** identifiers.
- **Enumerations** of specific commercial **EDR**, **vulnerability scanning**, or **SOC** SaaS hostnames/IP ranges (they churn; policy belongs in **private** runbooks or internal ticketing).

---

## 5. Expanding this stub later

When promoting content from a **private** runbook:

1. Replace every literal IP with **`10.0.0.0/24`**-style **examples** or placeholders.
2. Remove **named** third-party tools; keep wording like “**untrusted internal prefixes**” and “**optional cloud deny lists** (maintained privately).”
3. Add **one** worked example using **only** placeholder subnets (**VLAN 100**, **10.0.100.0/24**, etc.).
4. Cross-link back to **[HOMELAB_UNIFI_LAB-ROUTER-01_LAB_NETWORK.md](HOMELAB_UNIFI_LAB-ROUTER-01_LAB_NETWORK.md)** for SNMP/VLAN context.

---

## 6. See also

- [HOMELAB_UNIFI_LAB-ROUTER-01_LAB_NETWORK.md](HOMELAB_UNIFI_LAB-ROUTER-01_LAB_NETWORK.md) — LAB-ROUTER-01-SE lab VLANs, firewall patterns, SNMP (before a monitoring server).
- [HOMELAB_VALIDATION.md](HOMELAB_VALIDATION.md) — multi-host matrix; keep LAN specifics private.
- [PRIVATE_OPERATOR_NOTES.md](../PRIVATE_OPERATOR_NOTES.md) — where **`docs/private/`** inventory lives.

**Last updated:** 2026-03-31 (stub creation).
