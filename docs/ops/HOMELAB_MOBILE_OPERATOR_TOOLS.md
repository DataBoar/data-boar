# Mobile devices as homelab operator tools (iOS + Android)

**Purpose:** Practical ways to use **phones and tablets** (e.g. **iPhone**, **Android tablet**, **older iPad**) alongside your **homelab** and **Data Boar** workflow. These devices are **operator consoles**—they are **not** required to run the app; the product is still **Linux/Docker/server**-oriented.

**Related:** [OPERATOR_NOTIFICATION_CHANNELS.md](OPERATOR_NOTIFICATION_CHANNELS.md) (GitHub push on phone) · [OPERATOR_SECRETS_BITWARDEN.md](OPERATOR_SECRETS_BITWARDEN.md) · [HOMELAB_UNIFI_LAB-ROUTER-01_LAB_NETWORK.md](HOMELAB_UNIFI_LAB-ROUTER-01_LAB_NETWORK.md) · [HOMELAB_SOLAR_MONITORING_INTEGRATION.md](HOMELAB_SOLAR_MONITORING_INTEGRATION.md)

---

## 1. Network and UniFi (LAB-ROUTER-01-SE)

- **UniFi Network** (official app): quick checks on **clients**, **Wi‑Fi**, **alerts**, and **firmware** without opening the laptop.
- **Wi‑Fi validation:** From phone/tablet, confirm **lab VLAN SSIDs** (if you use them), **guest isolation**, and that **only** intended devices appear on the lab segment.
- **Caution:** Prefer **local management** on LAN or **secure remote** (e.g. **VPN** to home)—avoid exposing the **controller UI** raw to the internet.

---

## 2. GitHub and CI (already aligned with your setup)

- **GitHub mobile app:** **failed Actions**, **Dependabot**, **review requests**—see [OPERATOR_NOTIFICATION_CHANNELS.md](OPERATOR_NOTIFICATION_CHANNELS.md).
- **Optional:** Watch **critical** workflows only so notifications stay **actionable**, not noisy.

---

## 3. Secrets and identity

- **Bitwarden** (or your vault of choice) on **both** iOS and Android: **TOTP**, **secure notes** (e.g. “where is the solar API doc”), **no** plaintext secrets in **iCloud Notes** / random sync folders for production creds. See [OPERATOR_SECRETS_BITWARDEN.md](OPERATOR_SECRETS_BITWARDEN.md).

---

## 4. Solar and vendor apps

- **Manufacturer / Shine-class app** you already use: **current power**, **history**, **alerts**—complements (does not replace) anything you script later per [HOMELAB_SOLAR_MONITORING_INTEGRATION.md](HOMELAB_SOLAR_MONITORING_INTEGRATION.md).

---

## 5. SSH and “fix it from the couch”

- **SSH clients** (e.g. Termius, Blink, similar on Android): useful for **quick** checks on a **VM/LXC** or **Raspberry Pi** on the **LAN**.
- **Security:** Use **key-based** auth, **strong** passphrases or **hardware-backed** keys where supported; prefer **Tailscale / WireGuard VPN** if you ever reach homelab from **outside**—**do not** rely on **SSH open on WAN** without hardening.
- **Tablet** is nicer than phone for **reading logs** and **small** edits; still treat mobile sessions as **short** and **audited** (no long-lived root shells).

---

## 6. Data Boar web UI (LAN smoke)

- If the **dashboard** is reachable on your lab network (e.g. host **port 8088** per [DOCKER_SETUP.md](../DOCKER_SETUP.md)), a **phone or tablet** is a good **smoke test** for **responsive layout**, **touch**, and **“works from another device”**—not a substitute for **desktop** dev tools.

---

## 7. Documentation and inventory (photos, not secrets)

- **Camera:** Photograph **model plates** (UPS, HVAC, PDU, switch), **rack layout**, **cable labeling**—then transcribe **model numbers** into **`docs/private/homelab/`** (gitignored); **do not** commit photos that show **serials**, **Wi‑Fi PSKs**, or **QR codes** for pairing ([PRIVATE_OPERATOR_NOTES.md](../PRIVATE_OPERATOR_NOTES.md)).
- **OCR / Notes:** On **recent** iOS/iPadOS, **Live Text** helps turn label photos into text; on **very old** iPads (see §9), type or transcribe manually—**Live Text** is not available there.

---

## 8. After you add monitoring (later stage)

- **Grafana** (mobile), **UniFi** alerts, or **push** channels (**ntfy**, **Pushover**, **Apprise**-backed hooks) can reach **phone/tablet** when a **Proxmox** or **monitoring** VM is up—design **alert fatigue** carefully (severity + routing).

---

## 9. Older iOS tablet (e.g. **iPad mini 2**)

**Context:** Tablets like the **iPad mini 2** are usually **stuck on an old iOS** (around **12.x**). The **App Store** often **no longer** offers current builds of **GitHub**, **UniFi**, **Bitwarden**, **Termius**, etc.—or they require a **newer OS** than the device supports.

## Still useful for homelab “operator” work:

| Task                         | Fit                                                                                                                                                                                                                    |
| ----                         | ---                                                                                                                                                                                                                    |
| **Safari → LAN URLs**        | Open **`http://<host>:8088`** (Data Boar dashboard) or **simple** status pages on the LAN. If the UI uses **very new** JavaScript only, the old browser may **break**—then use **iPhone 11** or **PC** for that check. |
| **Wi‑Fi checks**             | Join **lab / guest SSIDs** and confirm **connectivity** and **captive portal** behaviour.                                                                                                                              |
| **Photos**                   | **Camera** for **rack / label** documentation (same rules as §7—transcribe to **`docs/private/homelab/`**, no secrets in public repo).                                                                                 |
| **Dedicated “wall” display** | Optional **kiosk-style** browser pointed at a **simple** Grafana **or** static status page (keep dashboards **light** if you target old WebKit).                                                                       |

**Treat as untrusted for secrets:** Prefer **iPhone 11** (current app updates, OS patches) for **Bitwarden**, **TOTP**, and **primary** GitHub notifications. Use the old iPad as a **secondary** screen or **photo** tool, not the **only** place you store credentials.

---

## 10. What *not* to expect from these devices

- **Building** Docker images, running **`uv sync`**, or **full** pytest suites: keep that on **x86_64 Linux** / **WSL** / **CI**.
- **Primary** log analysis: laptop or server; mobile is for **paging** and **triage**.

---

## 11. See also

- [HOMELAB_VALIDATION.md](HOMELAB_VALIDATION.md) — main lab playbook.
- [SECURITY.md](../../SECURITY.md) — secrets and public repo hygiene.

**Português (Brasil):** [HOMELAB_MOBILE_OPERATOR_TOOLS.pt_BR.md](HOMELAB_MOBILE_OPERATOR_TOOLS.pt_BR.md)
