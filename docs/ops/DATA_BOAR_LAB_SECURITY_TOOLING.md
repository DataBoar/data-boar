# Data Boar: lab testing vs host security tooling

**Português (Brasil):** [DATA_BOAR_LAB_SECURITY_TOOLING.pt_BR.md](DATA_BOAR_LAB_SECURITY_TOOLING.pt_BR.md)

## Purpose

Hardened **Linux**, **Windows**, and **network** stacks often run **firewalls**, **mandatory access control**, **intrusion-response daemons**, and **integrity monitors**. Those controls are correct for production; they can still **block or confuse** Data Boar **lab** validation (dashboard/API on the LAN, Docker bind mounts, repeated SSH from automation, database ports from [LAB_SMOKE_MULTI_HOST.md](LAB_SMOKE_MULTI_HOST.md)).

This runbook **names** common controls, **states what usually has to change** for a bounded test, **justifies** why, and points to **helper scripts** in `scripts/`. It is **generic** (no real hostnames, LAN IPs, or credentials). Record machine-specific outcomes under **gitignored** `docs/private/homelab/`.

**Related:** [HOMELAB_VALIDATION.md](HOMELAB_VALIDATION.md) §0.1 (LAN access) · [LAB_OP_FIREWALL_REVIEW_BASELINE.md](LAB_OP_FIREWALL_REVIEW_BASELINE.md) · [CURSOR_UBUNTU_APPARMOR.md](CURSOR_UBUNTU_APPARMOR.md) · [SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.md](SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.md) · [SECURITY.md](../SECURITY.md)

## Principles (lab vs production)

1. **Prefer narrow allow rules** (source subnet + destination port + time-bound change ticket) over **disabling whole products**.
2. **Bind and scope:** Data Boar should listen on **`0.0.0.0`** only when you **intend** LAN access; pair that with **host firewall allow** from **lab clients only**, not `0.0.0.0/0`.
3. **Revert:** After the test window, remove temporary allows or return jails/profiles to enforcement, per your policy.
4. **Customer value:** The same table helps **support** when a prospect’s IT says “nothing connects” — you can ask targeted questions instead of guessing.

## Default ports (recap)

| Surface | Default | Notes |
| ------- | ------- | ----- |
| HTTP API + dashboard | **TCP 8088** | [USAGE.md](../USAGE.md), `api.port` |
| Optional TLS in-app | same port | cert flags in [TECH_GUIDE.md](../TECH_GUIDE.md) |
| Reverse proxy | **443** (typical) | If TLS terminates on nginx/Caddy, open **443** to the proxy, not raw **8088** on the edge |
| Lab DB / compose | **5432**, **3306**, etc. | [HOMELAB_VALIDATION.md](HOMELAB_VALIDATION.md) §4, [LAB_SMOKE_MULTI_HOST.md](LAB_SMOKE_MULTI_HOST.md) |

Helper scripts (optional, operator-run):

- **Windows:** `scripts/lab-allow-data-boar-inbound.ps1` — inbound **8088/tcp** on **Private** profile (adjust profile/port as needed).
- **Linux:** `scripts/lab-allow-data-boar-inbound.sh` — **ufw** or **firewalld** allow from `LAB_LAN_CIDR` (default `10.0.0.0/16` — **change** to your LAN).

## Matrix: control, interference, lab adjustment, production note

| Control | Typical interference with Data Boar lab work | What to change (lab) | Why | Production / customer note |
| ------- | -------------------------------------------- | -------------------- | --- | --------------------------- |
| **Windows Defender Firewall** | Blocks **inbound** **8088** from other LAN hosts | Add allow rule for **TCP 8088** from **private** network profile or scoped remote IPs; use `lab-allow-data-boar-inbound.ps1` or **Windows Defender Firewall with Advanced Security** GUI | Dashboard/API must be reachable across the lab subnet | Prefer **scope by subnet**, not “any”; document rule owner |
| **Linux host firewall (ufw / firewalld / nftables)** | Same as Windows for **8088** and DB ports | **Allow** from LAN CIDR to **8088/tcp**; for DB smoke, allow client host to DB port on DB host | Default-deny is normal; explicit allow is the smallest fix | Keep **stateful** rules; avoid opening **8088** to WAN |
| **Router / UniFi / VLAN ACLs** | Client VLAN cannot reach server **8088** | **L3 allow** + correct **DNS** if using names; see [HOMELAB_VALIDATION.md](HOMELAB_VALIDATION.md) §0.1 | Segmentation is intentional; tests need an explicit exception path | Same pattern for **customers** with DMZ or GUEST isolation |
| **AppArmor** | **DENIED** on `docker` / `containerd` / app paths, bind mounts, or Python under snap | Check `journalctl` / `dmesg` for **apparmor="DENIED"**; use **complain** mode for a narrow profile during diagnosis, or **local overrides** (see [CURSOR_UBUNTU_APPARMOR.md](CURSOR_UBUNTU_APPARMOR.md) patterns) | MAC is path-based; unusual mount paths can trip profiles | Prefer **tuned profile** over global **disabled** |
| **SELinux (Enforcing)** | Container volume labels, network binding | Use **boolean** (e.g. `httpd_can_network_connect` patterns) or **container file context** per distro doc | SELinux denies by default on RHEL-family | Document **context** for support runbooks |
| **fail2ban / SSHGuard** | **SSH** lockout after repeated connections; HTTP jails if proxy logs 401/404 storms | **Whitelist** lab scanner IPs in `jail.local` / firewall **ignoreip**; avoid hammering **SSH** with bad keys from scripts | Automated tests can look like brute force | Customers may need **allowlist** for CI or scanner hosts |
| **USBGuard** | Blocks **USB** devices | **No impact** on network Data Boar | Irrelevant unless you attach storage via USB for a connector test | — |
| **AIDE / Tripwire / Wazuh FIM** | **Alerts** on files under repo clone, `uv` cache, Docker layers | Expect **noise** during `git pull`, `docker build`; tune **exclusions** for build dirs or accept alerts in lab | Integrity tools flag churn | **Do not** “turn off” silently — **scope** excludes |
| **auditd / Linux Audit** | Heavy **syscall** logging; possible **backpressure** | Usually **no change**; if policies deny `exec`, adjust **audit rules** only with security team | Rare conflict unless overly strict **exec** deny | Compliance customers may require **retain** logs |
| **EDR / antivirus (Windows)** | Scanning **Python** / **Docker** paths; rare **bind** interference | **Exclusions** for dev clone and Docker data root **only** if policy allows | Performance and false positives | Align with IT; mirror **customer** EDR pain |
| **CrowdSec / similar** | HTTP bouncer blocking **8088** | **Whitelist** lab sources or disable bouncer for test **vhost** | Same class as fail2ban | Document **API** + dashboard as internal-only |

## SSH automation and sudo (expectations)

Operators sometimes use **SSH** from the dev PC to lab hosts (`lab-op` scripts, Ansible, manual `git pull`). **Passwordless SSH** and **`sudo -n`** are **not** guaranteed in every environment; the assistant **cannot** safely assume **NOPASSWD** sudo on your machines. Non-interactive remoting **cannot** complete **`sudo ufw …`** when the account requires a **password** on every invocation—use an **interactive SSH session**, **Ansible** with a vault/become strategy, or **console** access.

- If **`sudo -n ufw status`** fails, run the **ufw**/**firewalld** commands **on the console** as root or with normal sudo.
- **Document** in private notes: which host received which rule, date, and rollback.

## Customer-facing checklist (support handoff)

When a deployment “works locally” but not in the customer network, ask:

1. **Inbound path:** Is **8088** (or **443** via proxy) allowed from the **operator workstation** or **scanner subnet** to the **app host**?
2. **Bind:** Is the process on **`0.0.0.0`** (or the correct interface), not **loopback only**?
3. **L3 path:** Any **VLAN ACL**, **NSG**, or **host firewall** in between?
4. **IDS/IPS:** Any **rate limit** or **WAF** on the same path?
5. **Integrity / EDR:** Is scanning delaying **Docker** or **Python** startup?

Capture answers in the ticket — same structure as internal lab debugging.
