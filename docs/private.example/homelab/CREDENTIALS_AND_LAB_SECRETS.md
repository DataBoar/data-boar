# Lab credentials and secrets — safe handoff (no paste in chat)

**Português (Brasil):** [CREDENTIALS_AND_LAB_SECRETS.pt_BR.md](CREDENTIALS_AND_LAB_SECRETS.pt_BR.md)

**Purpose:** Let the operator and the assistant work with **SNMP, API keys, and passwords** for LAB-OP (e.g. UniFi LAB-ROUTER-01-SE) **without** pasting secrets into Cursor chat or into **tracked** repo files.

---

## Rules (non-negotiable)

1. **Never** paste passwords, community strings, API tokens, or private keys **into the chat**.
1. **Never** commit secrets to **`main`** — not in `.mdc` rules, not in `AGENTS.md`, not in skills, not in public `docs/`.
1. **OK** to store **operator-only** copies under **`docs/private/`** (gitignored) if you accept **disk** risk (backup, encryption, pCloud sync policy). Prefer **short-lived** or **vault** flows when possible.

---

## Recommended order (strongest first)

| Method                                                               | When to use                                                                                                                                                                                                                                                                     |
| ------                                                               | -----------                                                                                                                                                                                                                                                                     |
| **Bitwarden CLI (`bw`)**                                             | Already referenced in `homelab-host-report.sh`; good for “fetch secret at script run time” without a static file.                                                                                                                                                               |
| **OS credential store** (Windows Credential Manager, macOS Keychain) | For interactive or scheduled jobs on one machine.                                                                                                                                                                                                                               |
| **Session-only environment variables**                               | You set **`$env:VAR`** in the **integrated terminal** **before** asking the agent to run a script; the **same** shell session runs the command. **Do not** rely on “the AI clears the variable” as your only control — **close the terminal** or **end the session** when done. |
| **Gitignored file** e.g. **`docs/private/homelab/.env.snmp.local`**  | One file per machine; copy from **`.env.example`** pattern in this folder; **never** commit.                                                                                                                                                                                    |

---

## Environment variables (SNMP / UniFi-style example)

Define **names only** in tracked docs; **values** come from your head or vault.

Suggested names (customize per your comfort):

- `LAB_LAB-ROUTER-01_SNMP_HOST` — management IP (RFC1918; still treat as sensitive in some policies).
- `LAB_LAB-ROUTER-01_SNMP_V3_USER` / `LAB_LAB-ROUTER-01_SNMP_AUTH_PASS` / `LAB_LAB-ROUTER-01_SNMP_PRIV_PASS` — SNMPv3 (preferred over v2c community).

**SNMPv2c community** is effectively a password; **SNMPv3** is preferred on LAB-ROUTER-01-SE (see [HOMELAB_UNIFI_LAB-ROUTER-01_LAB_NETWORK.md](../../ops/HOMELAB_UNIFI_LAB-ROUTER-01_LAB_NETWORK.md)).

---

## What the assistant does

- Run **`read_file`** on **`docs/private/...`** only for **layout** or **redacted** inventories — **not** to broadcast secrets into **tracked** Markdown.
- Run **scripts** that **read** `$env:...` in **your** terminal when you have already exported variables in that session.
- **Refuse** to echo secret values back into chat or into committed files.

---

## Monitoring “metrics” (realistic path)

1. **Now:** one-shot **`snmpwalk`** / interface counters from a host on the LAN (script in `scripts/` reads env vars).
1. **Later:** Prometheus **SNMP exporter** + Grafana, or UniFi’s own UI — **not** required to “start” SNMP validation.

---

## Copy-me files (local only)

Create under **`docs/private/homelab/`** (not copied to GitHub):

- **`.env.snmp.local`** — `KEY=value` lines; chmod / ACLs as you prefer on Windows.
- **`LAB_SNMP_NOTES.md`** — **non-secret** only: which OIDs you poll, VLAN IDs, firewall rule names.

### SNMPv3 + `scripts/snmp-LAB-ROUTER-01-lab-probe.ps1` — concrete steps (English)

**Important:** The assistant **cannot** read environment variables on your PC. **Do not** paste SNMP passwords into chat. You supply secrets **only** on your machine (session vars or gitignored file), then run the script locally.

#### SNMP on Windows (PowerShell + WSL) — validated path

`snmpwalk` is **not** a native Windows tool. **`apt-get` runs inside Linux**, not in PowerShell. Do this:

1. **Install WSL** (once): in an **elevated** PowerShell: `wsl --install` (installs Ubuntu by default on many setups). Restart if Windows asks. See [Microsoft: Install WSL](https://learn.microsoft.com/en-us/windows/wsl/install).
1. **Open your Linux distro** (Start menu → Ubuntu, or run `wsl` in a terminal).
1. **Inside the same distro you pass to `-WslDistro`** (e.g. open **Debian** if you use `-WslDistro "Debian"`), install Net-SNMP **once**:

   ```bash
   sudo apt update
   sudo apt install -y snmp
   command -v snmpwalk
   ```

   You should see a path such as **`/usr/bin/snmpwalk`**. If empty, the install did not apply to that distro (common mistake: installing only in Ubuntu while the script uses Debian).

   **Debian 13 (trixie) / LMDE 7:** do **not** require **`snmp-mibs-downloader`** — it may show “no installation candidate” unless **`non-free`** is enabled; it is **optional** (MIB file names). This repository’s probe uses **numeric OIDs** only; **`snmp`** alone is enough.

1. **Back in PowerShell** (repo root, same machine), set `LAB_LAB-ROUTER-01_SNMP_*` and run:

   ```powershell
   .\scripts\snmp-LAB-ROUTER-01-lab-probe.ps1
   ```

   The script will use **`wsl.exe`** and forward your PowerShell env vars into WSL via **`WSLENV`** (no need for `snmpwalk` on Windows PATH).

If `wsl -l -v` shows several distros and the wrong one is default, either **`wsl --set-default <Name>`** or run:
`.\scripts\snmp-LAB-ROUTER-01-lab-probe.ps1 -WslDistro "Ubuntu-22.04"` (use the exact **Name** column).

**Alternative:** Skip Windows entirely — run `snmpwalk` on a **Linux host on the LAN** (e.g. lab laptop) using the same OID and v3 flags; see [HOMELAB_UNIFI_LAB-ROUTER-01_LAB_NETWORK.md](../../ops/HOMELAB_UNIFI_LAB-ROUTER-01_LAB_NETWORK.md).

**Not recommended here:** hunting for unofficial `snmpwalk.exe` for Windows; WSL is the supported developer path in this repo.

**Variable names** (must match what the script expects):

| Variable                 | Meaning                                                |
| --------                 | -------                                                |
| `LAB_LAB-ROUTER-01_SNMP_HOST`      | Target IP (e.g. gateway / switch management IP on LAN) |
| `LAB_LAB-ROUTER-01_SNMP_V3_USER`   | SNMPv3 username                                        |
| `LAB_LAB-ROUTER-01_SNMP_AUTH_PASS` | SNMPv3 **authentication** password                     |
| `LAB_LAB-ROUTER-01_SNMP_PRIV_PASS` | SNMPv3 **privacy** password                            |

## A) Session-only (PowerShell, same window as the script):

```powershell
$env:LAB_LAB-ROUTER-01_SNMP_HOST = "192.0.2.10"
$env:LAB_LAB-ROUTER-01_SNMP_V3_USER = "your_v3_user"
$env:LAB_LAB-ROUTER-01_SNMP_AUTH_PASS = "your_auth_secret"
$env:LAB_LAB-ROUTER-01_SNMP_PRIV_PASS = "your_priv_secret"
.\scripts\snmp-LAB-ROUTER-01-lab-probe.ps1
```

**B) Gitignored file** `docs/private/homelab/.env.snmp.local` — **exact path and name** (leading dot). Tracked template to copy: **`docs/private.example/homelab/env.snmp.local.example`** →
`Copy-Item docs\private.example\homelab\env.snmp.local.example docs\private\homelab\.env.snmp.local` then edit with real values.

Format: one `KEY=value` per line, no spaces around `=`; lines starting with `#` ignored:

```text
LAB_LAB-ROUTER-01_SNMP_HOST=192.0.2.10
LAB_LAB-ROUTER-01_SNMP_V3_USER=your_v3_user
LAB_LAB-ROUTER-01_SNMP_AUTH_PASS=your_auth_secret
LAB_LAB-ROUTER-01_SNMP_PRIV_PASS=your_priv_secret
```

Load into the **current process** then run the probe:

```powershell
$envPath = "docs\private\homelab\.env.snmp.local"
Get-Content $envPath | Where-Object { $_ -and $_ -notmatch '^\s*#' } | ForEach-Object {
  $pair = $_ -split '=', 2
  if ($pair.Count -eq 2) {
    Set-Item -Path "Env:$($pair[0].Trim())" -Value $pair[1].Trim().Trim('"')
  }
}
.\scripts\snmp-LAB-ROUTER-01-lab-probe.ps1
```

**Prerequisites:** On **Windows**, install **`snmp`** inside **WSL** (see **“SNMP on Windows (PowerShell + WSL)”** above); the script calls `wsl.exe` automatically. On **Linux**, `snmpwalk` on `PATH` is enough. The script uses **SHA** + **AES**; if your device uses different algorithms, adjust the script or call `snmpwalk` manually with matching flags.

**Several devices:** use one env file per target (same four keys) and **`-EnvFile`** on `snmp-LAB-ROUTER-01-lab-probe.ps1` / `snmp-LAB-ROUTER-01-lab-probe-to-log.ps1`. See **[SNMP_LAB_TARGETS.md](SNMP_LAB_TARGETS.md)** and **`env.snmp.switch.local.example`**.

**Sharing results with the assistant:** Paste only **redacted** output (interface OIDs / counters). Never paste env values or passwords.

---

**Multiple SNMP devices (switch, etc.):** [SNMP_LAB_TARGETS.md](SNMP_LAB_TARGETS.md) — per-target `.env` files, `-EnvFile`, Linux `snmp-lab-ifwalk.sh`, optional v2c `snmpwalk`.

**Related:** [PRIVATE_OPERATOR_NOTES.md](../../PRIVATE_OPERATOR_NOTES.md) · [HOMELAB_UNIFI_LAB-ROUTER-01_LAB_NETWORK.md](../../ops/HOMELAB_UNIFI_LAB-ROUTER-01_LAB_NETWORK.md) · [AGENT_LAB_ACCESS.md](AGENT_LAB_ACCESS.md) (if present).
