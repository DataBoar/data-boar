# Homelab solar monitoring — what we can (and cannot) integrate

**Context you described:** ~**4 kWp** PV, commissioned **2021-11-02**, **datalogger** on a **separate VLAN**, data to **vendor cloud** + **mobile app**, inverter/datalogger branded around **“Shine”** (common naming).

## Hard limits:

- **This repository and AI sessions cannot** reach your **LAN**, your **VLAN**, or **vendor APIs** using **your** credentials. There is no secure way to “hand me” passwords for automated polling in chat.
- **You can** run scripts **on your PC or homelab** (secrets in **env** / Bitwarden only; **non-secret** field notes in **`docs/private/homelab/`**) and paste **redacted JSON samples** if you want help parsing or mapping fields.

---

## 1. Identify the vendor stack (pick one path)

The word **“Shine”** appears in **more than one** ecosystem. Use **hardware labels** and **app store ID** to disambiguate:

| Clue                                                                      | Likely stack       | Cloud / API direction                                                                                                                                                                                                                                                                                                          |
| ----                                                                      | ------------       | ---------------------                                                                                                                                                                                                                                                                                                          |
| Inverter label **Solis**; stick/logger **ShineWiFi** / **Solis**          | **Solis**          | **SolisCloud** — official [API documentation](https://doc.soliscloud.com/en/20.API%20documentation/01.SolisCloud%20Platform%20API%20Document.html); access via [API Management / support process](https://solis-service.solisinverters.com/en/support/solutions/articles/44002212561-api-access-soliscloud) (Key ID / Secret). |
| App **ShinePhone** / **Growatt** branding; logger **ShineLink** / similar | **Growatt-family** | **ShineMonitor** open HTTP API — docs at [api.shinemonitor.com](https://api.shinemonitor.com/) (GET + **SHA-1** signed auth, `company-key`, token lifetime).                                                                                                                                                                   |
| Other (WEG, Fronius, SMA, etc.)                                           | —                  | Use that vendor’s **portal API** or **Modbus** over LAN.                                                                                                                                                                                                                                                                       |

**Action:** Note **exact inverter model**, **logger model**, and **app name** in **`docs/private/homelab/`** (gitignored), not in GitHub-tracked files.

---

## 2. If it is **SolisCloud** (Solis + ShineWiFi class)

- Enable **API** in the Solis account per vendor instructions; store **Key ID** and **Key Secret** in **environment variables** or a **secrets manager** — **never** commit to git.
- Typical use: pull **plant / inverter** power, **daily energy**, alarms — suitable for **Grafana**, **Home Assistant**, or a **cron + curl** exporter on your **future monitoring VM**.
- **Rate limits** and **terms of use** apply — read current Solis docs.

---

## 3. If it is **ShineMonitor** (Growatt-family style)

Public documentation describes:

- Base URL pattern: `<http://api.shinemonitor.com/public>/` (confirm **HTTPS** variants in current docs before production).
- **Auth:** `action=auth` with `usr`, `pwd`, **`company-key`**, `source` (0=PV), plus `_app_id_`, `_app_version_`, `_app_client_`; **`sign`** = SHA-1 over salt + SHA-1(password) + parameter string (see [API usage help](https://api.shinemonitor.com/en/chapter1/apiHelp.html)).
- Subsequent calls use **`token`** + **`secret`** + new **`sign`** including `&action=...`.

**Security:** Treat **`company-key`**, password, **token**, and **secret** like **credentials**. Do not paste live tokens into public issues.

---

## 4. Local / LAN options (no cloud API)

Even with cloud reporting, you may optionally:

- **Read the datalogger or inverter on the IoT VLAN** via documented **Modbus TCP** / HTTP status page (depends on model — some Solis loggers expose **8899** / local web in community docs; **verify** against your firmware).
- **Mirror** traffic only inside your network — **do not** expose inverter web UI to **WAN**.

Use these for **low-latency** dashboards or **when cloud is down**; still keep **firewall rules** tight (management workstation → logger only).

---

## 5. Relating PV to the **homelab power** doc

- **4 kWp** is **DC nameplate**; **AC** output depends on irradiance, temperature, clipping, and inverter limit — **not** a constant 4000 W.
- **Night = 0 W generation** is normal; the **house** still draws **grid** (or battery if hybrid) — your **Attiv** load is **unchanged** by PV at night.
- Optional **personal** metric: correlate **mid-day kW** with **running heavy scans** on solar (operational note in **`docs/private/homelab/`**).

---

## 6. Local template (gitignored — not in GitHub)

Create a **local-only** note under **`docs/private/homelab/`** (see [PRIVATE_OPERATOR_NOTES.md](../PRIVATE_OPERATOR_NOTES.md)). Example fields to copy into your file:

```markdown
# Solar — local only
- kWp: (nameplate)
- Commissioned: (date)
- Inverter brand/model:
- Datalogger model:
- App name (store ID):
- Cloud portal URL:
- API type: SolisCloud | ShineMonitor | other
- API credentials: (never in repo — Bitwarden + env: SOLIS_KEY_ID, etc.)
- Logger VLAN / IP (internal):

```

**Tracked starter:** copy from [private.example/homelab/README.md](../private.example/homelab/README.md) into `docs/private/homelab/`.

---

## 7. See also

- [HOMELAB_POWER_AND_ELECTRICAL_PLANNING.md](HOMELAB_POWER_AND_ELECTRICAL_PLANNING.md) — **Solar / PV** subsection (bill vs breaker vs UPS).
- [HOMELAB_UNIFI_LAB-ROUTER-01_LAB_NETWORK.md](HOMELAB_UNIFI_LAB-ROUTER-01_LAB_NETWORK.md) — VLAN / firewall patterns.
- [PRIVATE_OPERATOR_NOTES.md](../PRIVATE_OPERATOR_NOTES.md) — where real homelab notes live vs public docs.

**Português (Brasil):** [HOMELAB_SOLAR_MONITORING_INTEGRATION.pt_BR.md](HOMELAB_SOLAR_MONITORING_INTEGRATION.pt_BR.md)
