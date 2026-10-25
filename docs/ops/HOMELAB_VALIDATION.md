# Home lab: deployment checks and target validation (manual playbook)

**Português (Brasil):** [HOMELAB_VALIDATION.pt_BR.md](HOMELAB_VALIDATION.pt_BR.md)

**Purpose:** Run **concrete checks** on a **second machine** (VM or container host) to prove **deployability**, **smoke behaviour**, and **connector coverage** using **synthetic** and optionally **small real** datasets—without relying on CI or the dev laptop alone.

**Operator-specific facts** (real hostnames, LAN IPs, serials, measured watts, inventory dumps) belong in the **gitignored** tree **`docs/private/homelab/`**, not in this file. Public view stays **generic**; layout and safety: [PRIVATE_OPERATOR_NOTES.md](../PRIVATE_OPERATOR_NOTES.md).

**Not legal advice.** For **real** personal data, use **lawful basis**, **minimisation**, and **read-only** technical accounts; prefer **synthetic** or **public sample** data when unsure.

**Multi-host “completão” (full lab round):** This file is the **single-machine** baseline (clone, `check-all`, Docker smoke, synthetic FS). For **ordered E2E across several lab hosts**—Postgres/MariaDB stack, compressed fixtures, optional SMB/NFS/**SSHFS**/WebDAV/**iSCSI-backed** filesystem paths—follow **[LAB_SMOKE_MULTI_HOST.md](LAB_SMOKE_MULTI_HOST.md)** (host order, pass/fail checklist **A–M**, definition of *completão*). **PII / publishing:** do not put real mount lines, credentials, LAN addresses, or home paths in tracked docs or public issues; see [ADR 0018](../adr/ADR-0018-pii-anti-recurrence-guardrails-for-tracked-files-and-branch-history.md) and [ADR 0019](../adr/ADR-0019-pii-verification-cadence-and-manual-review-gate.md). Operator-specific evidence stays under **gitignored** `docs/private/homelab/`.

**Related:** [deploy/DEPLOY.md](../deploy/DEPLOY.md) · [SONARQUBE_HOME_LAB.md](SONARQUBE_HOME_LAB.md) (optional quality server) · [OPERATOR_IT_REQUIREMENTS.md](OPERATOR_IT_REQUIREMENTS.md) · [TESTING.md](../TESTING.md) · [SECURITY.md](../SECURITY.md) · **Lab-op minimal stack (Podman + k3s):** [LAB_OP_MINIMAL_CONTAINER_STACK.md](LAB_OP_MINIMAL_CONTAINER_STACK.md) · **ThinkPad LAB-NODE-01 + LMDE 7:** [LMDE7_LAB-NODE-01_DEVELOPER_SETUP.pt_BR.md](LMDE7_LAB-NODE-01_DEVELOPER_SETUP.pt_BR.md) · **Optional observability:** [PLAN_LAB_OP_OBSERVABILITY_STACK.md](../plans/PLAN_LAB_OP_OBSERVABILITY_STACK.md) · **Optional SIEM (Wazuh):** [LAB_OP_MINIMAL_CONTAINER_STACK.md](LAB_OP_MINIMAL_CONTAINER_STACK.md) §6

---

## 0. Principles

1. **Automate locally first (any machine):** from repo root, `.\scripts\check-all.ps1` (Windows) or equivalent pre-commit + `uv run pytest -v -W error` (Linux/macOS). Fix reds before spending time on lab networking.
1. **Lab is for integration:** OS paths, Docker volumes, real DB ports, firewall, and “does this config actually run here?”
1. **Synthetic by default:** hand-made `.txt` / `.csv` with **fake** CPF/email patterns (see project tests for valid-format examples—do not use real people’s data).
1. **Real data only when allowed:** copies of non-production DBs, anonymised extracts, or documents you own/have permission to scan.
1. **Docker container churn:** Prefer `docker run --rm` for one-shot checks. If you keep a named **Data Boar** container between runs, aim for **one** primary instance—or **two** only for explicit **A/B** (image or config). Remove throwaway containers when done so ports (`8088`) and volumes stay predictable. See [DOCKER_SETUP.md](../DOCKER_SETUP.md) §7.
1. **Docker CE + Swarm already active:** On a **Swarm manager** (including **single-node** homelab swarms), `docker build` and `docker run -p …` still work for §1.3–1.5—same CLI, published ports bind on the host unless something else already owns `8088`. If you standardise on **stacks** (`docker stack deploy`), translate the playbook’s `docker run` into a small Compose file with a `ports:` mapping and a bind mount for `/data`; overlay networks use **service names** as DNS (like the §4 `lab-net` example). Keep **service names and node roles** in private notes, not in this repo.

### 0.1 LAN access from another lab host (dashboard / API)

To hit the Data Boar **HTTP** dashboard and REST API from **another machine on the lab LAN** (browser on a second box, `curl` from a test VM, etc.):

| What | Detail |
| ---- | ------ |
| **Port** | **TCP 8088** by default (same for native `uv run` and Docker `-p 8088:8088`). |
| **Bind address** | The process must listen on **`0.0.0.0`**, not only **`127.0.0.1`**. Use `--web --host 0.0.0.0 --port 8088` (plus `--allow-insecure-http` if you are not terminating TLS in-app). Docker images that already bind all interfaces are fine; still confirm with `ss -tlnp` / `curl` from the other host. |
| **Host firewall (Linux)** | Allow **inbound** **8088/tcp** from **your LAN subnet only** (example pattern, adjust CIDR: `sudo ufw allow from 10.0.0.0/16 to any port 8088 proto tcp comment 'Data Boar lab LAN'`). More context: [LMDE7_LAB-NODE-01_DEVELOPER_SETUP.pt_BR.md](LMDE7_LAB-NODE-01_DEVELOPER_SETUP.pt_BR.md). |
| **Router / UniFi (VLANs, Wi‑Fi, guest)** | If the client is not on the same L2 segment as the server, add an **allow** rule so the client network can reach **server:8088** (and DNS if you use names). Record **real** IPs/VLAN IDs only in **gitignored** notes. |
| **WAN** | Do **not** open **8088** on the internet for casual lab tests; use VPN or SSH tunnel if you need remote access. |
| **TLS / reverse proxy** | If you front the app with nginx/Caddy on **443**, open **443** to the proxy instead of exposing raw **8088** at the edge. |

**Dependencies on the lab host:** `uv sync` (and any **system** packages from [TECH_GUIDE.md](../TECH_GUIDE.md) for your distro) before §1.1; no extra Python package is required **only** to listen on the LAN.

**Host security stack (firewall, AppArmor, fail2ban, EDR, integrity tools):** Layered controls can block ports or add noise during lab runs. See **[DATA_BOAR_LAB_SECURITY_TOOLING.md](DATA_BOAR_LAB_SECURITY_TOOLING.md)** for what to adjust, why, and helper scripts (`scripts/lab-allow-data-boar-inbound.ps1`, `scripts/lab-allow-data-boar-inbound.sh`).

---

## 1. Lab baseline checklist (copy/paste)

| Step | Action                                                                                               | Pass criteria                                                                                                                      |
| ---- | ------                                                                                               | -------------                                                                                                                      |
| 1.1  | Clone repo on lab (or `git pull`); `uv sync`                                                         | Dependencies install                                                                                                               |
| 1.2  | `uv run pytest -v -W error` or project check script                                                  | All tests green                                                                                                                    |
| 1.3  | `docker build -t data_boar:lab .`                                                                    | Build completes (reuse this tag for every lab smoke — do not mint a new tag per run; see [DOCKER_SETUP.md](../DOCKER_SETUP.md) §7) |
| 1.4  | Create `./data/config.yaml` from [deploy/config.example.yaml](../../deploy/config.example.yaml)      | File valid YAML                                                                                                                    |
| 1.5  | `docker run --rm -p 8088:8088 -v "$(pwd)/data:/data" -e CONFIG_PATH=/data/config.yaml data_boar:lab` | Dashboard loads at `:8088`, `/health` OK                                                                                           |
| 1.6  | **Start scan** (dashboard or `POST /scan`) with `targets: []`                                        | Completes idle run; no crash                                                                                                       |
| 1.7  | *(Optional)* Open the dashboard in **more than one** desktop browser                                 | Core pages load; check **DevTools console** for errors on **Start scan** / **Config** if something feels off                       |

**Swarm mode:** If the host is already a Swarm **manager**, the steps above are still valid. Prefer a **free** host port if `8088` is taken by another stack; resolve port conflicts in your private runbook.

**§1.7 — Browser engines (optional):** You do **not** need every browser on Earth. Aim for **one solid check per engine family** that matters to **your** users:

| Family              | Examples (illustrative)                                                                      | Why                                                                                                                                                  |
| ------              | -----------------------                                                                      | ---                                                                                                                                                  |
| **Chromium**        | **Microsoft Edge**, **Google Chrome**, **Vivaldi**, **Brave**, many “privacy” Chromium forks | Largest share of desktop users; Data Boar’s dashboard is tested primarily on **Chromium-class** browsers in practice.                                |
| **Gecko (Firefox)** | **Mozilla Firefox**, **Floorp**                                                              | Second major engine; catches CSS/JS quirks Chromium misses.                                                                                          |
| **WebKit**          | **Safari** (macOS/iOS)                                                                       | Relevant if you demo on **Apple** devices; **iPhone/iPad** smoke is already in [HOMELAB_MOBILE_OPERATOR_TOOLS.md](HOMELAB_MOBILE_OPERATOR_TOOLS.md). |

**Helium** and other niche builds: treat as **extra Chromium variants** if they are Chromium-based; if unsure, one **Edge** + one **Firefox/Floorp** + **Safari** when available is enough for lab confidence. **Playwright** / **Selenium** (planned QA) can automate multi-browser runs later — see [PLANS_TODO.md](../plans/PLANS_TODO.md) (Selenium QA).

---

## 1.5 VMs on the **primary laptop** (GNOME Boxes / virt-manager) — smoke **before** Proxmox

**Purpose:** If the **x86 tower + Proxmox** is not ready yet, you can still run **isolated guests** on the **same** machine you use as **primary lab** (e.g. **14" business laptop**, Ubuntu-family desktop, often **≤ 8 GB RAM** ceiling on older units) using **GNOME Boxes** (simple) or **virt-manager** / **libvirt** + **KVM** (more control). This is **not** a substitute for a **dedicated** hypervisor row in §9, but it **de-risks** “second OS” checks early. **Exact make/model** → `docs/private/homelab/`.

**Resource reality (typical older primary lab laptop):** Total **RAM** is often **≤ 8 GB**; the **host OS + browser** already consumes a large share. Give each VM **1.5–3 GB** only if you accept swapping; **full Docker + ML/DL** inside the guest may be **tight**—prefer **§1.1–1.2** (clone + `uv sync` + **pytest**) and **§2** filesystem smoke, not heavy DL extras.

| Guest type                                       | Fit for Data Boar playbook                                 | Notes                                                                                                                                                                                                                                                                                                       |
| ----------                                       | --------------------------                                 | -----                                                                                                                                                                                                                                                                                                       |
| **Linux** (Debian, Ubuntu, Fedora, Alpine, …)    | **Yes** — same §1 / §2 steps **inside** the guest          | Use **NAT** (default) for simple outbound `git`/`uv`; for **LAN-visible** dashboard tests like bare-metal `0.0.0.0:8088`, configure **bridged** networking in virt-manager / advanced Boxes settings if your Wi‑Fi/Ethernet driver allows it.                                                               |
| **FreeBSD** (e.g. **15.x**)                      | **Exploratory** — not the same as the **Linux** matrix row | Install **Python 3.12+** and deps via **pkg**; `uv`/wheels may differ from Linux. Treat success as **documentation** of gaps, not a supported CI target unless you add it explicitly.                                                                                                                       |
| **Haiku**                                        | **Not** a practical target for this repo today             | Interesting for personal OS exploration; **do not** expect `uv sync` / full connector stack without major porting.                                                                                                                                                                                          |
| **IBM OS/2** (Warp, etc.)                        | **No** — **museum / hobby** only                           | No **Python 3.12+**, **`uv`**, or modern stack path for Data Boar. Fine for **preservation** or **driver archive** VMs; **zero** impact on compatibility planning.                                                                                                                                          |
| **OpenSolaris / illumos** (e.g. **OpenIndiana**) | **Exploratory** — **not** Linux                            | **OpenSolaris** (project discontinued) is **legacy**; prefer **illumos** distros today. **No** Linux wheels; Python **3.12+** and **`uv`** are **uncertain** — see [OS_COMPATIBILITY_TESTING_MATRIX.md](OS_COMPATIBILITY_TESTING_MATRIX.md) **Tier 4**. VM on **Proxmox** or spare host when you have time. |

**Hygiene:** Snapshots before risky package experiments; keep **VM disk images** off tiny partitions; list **guest names and disk paths** only under **gitignored** `docs/private/homelab/` (see [PRIVATE_OPERATOR_NOTES.md](../PRIVATE_OPERATOR_NOTES.md)).

---

## 2. Synthetic filesystem target (fastest real connector test)

1. On the lab host, create a directory, e.g. `~/lab-scan/fs-sample/`.
1. Add files:
   - `notes.txt` — a line with a **synthetic** CPF in valid format (e.g. use a known test pattern from `tests/test_audit.py` commentary—**not** a real person).
   - `sheet.csv` — header `email` and one row with `test@example.invalid`.
1. In `config.yaml`, set:

```yaml
targets:

- name: lab-fs

    type: filesystem
    path: /data/fs-sample   # inside container: mount host dir to /data/fs-sample
    recursive: false
file_scan:
  extensions: [.txt, .csv]
  recursive: false
  scan_sqlite_as_db: false
  sample_limit: 5
```

1. Mount: `-v ~/lab-scan/fs-sample:/data/fs-sample` (adjust host path).
1. Run CLI one-shot or dashboard scan.
1. **Pass:** findings appear in SQLite/report; filesystem findings &gt; 0 for obvious patterns.

**Optional:** enable `use_content_type: true` or dashboard **content-type** checkbox; add a file `disguised.txt` whose bytes start with `%PDF-1.` to confirm magic-byte path (see [USAGE.md](../USAGE.md)).

---

## 3. SQLite as a “database” file (single file, no server)

1. Create or copy a small `.db` with one table and a few text columns (or use Python `sqlite3` once to insert synthetic rows).
1. Target type **filesystem** with `scan_sqlite_as_db: true` **or** a **database** target pointing at SQLite connection string—follow [USAGE.md](USAGE.md) for your chosen shape.
1. **Pass:** session completes; database findings or filesystem path shows SQLite was read.

---

## 4. PostgreSQL or MySQL/MariaDB in Docker (lab SQL)

1. Start a throwaway DB container on the lab (same Docker network as the app, or publish port to host).

```bash
# Example: Postgres
docker network create lab-net
docker run -d --name lab-pg --network lab-net -e POSTGRES_PASSWORD=labpass -e POSTGRES_DB=labdb postgres:16-alpine
```

1. Create a table `customers (id serial, full_name text, doc_id text)`; insert **synthetic** rows.
1. Add a **database** target in `config.yaml` with host `lab-pg` (if app container on `lab-net`) or `host.docker.internal` / LAN IP from host networking docs.
1. Use **read-only** user if possible.
1. **Pass:** scan connects; findings or empty result without connection errors; check `scan_failures` in session.

**MySQL/MariaDB:** same idea; install connector deps per [TECH_GUIDE.md](../TECH_GUIDE.md).

**Bundled compose + seeds:** For a **ready-made** two-DB stack (Postgres + MariaDB) with synthetic `lab_customers` / `lab_notes` tables and example `config.lab-smoke.example.yaml`, use **`deploy/lab-smoke-stack/`** and follow **[LAB_SMOKE_MULTI_HOST.md](LAB_SMOKE_MULTI_HOST.md)** (ordering hosts, firewall, compressed fixtures, shares).

---

## 5. NoSQL (optional extras)

- **MongoDB:** requires `uv sync --extra nosql` (or equivalent); small collection with synthetic documents.
- **Redis:** string values with synthetic emails; respect memory and TTL in lab.

**Pass:** connector runs; document any `ModuleNotFoundError` as “install extra” in your runbook.

---

## 6. REST API target (optional)

- Point at a **mock** or trivial JSON API in the lab (e.g. small Flask container returning static JSON with synthetic fields).
- **Pass:** API connector completes; findings or logged skip reasons are understandable.

---

## 7. Compressed archives (`scan_compressed`)

1. Add a `.zip` containing one `.txt` with synthetic PII pattern.
1. Set `file_scan.scan_compressed: true` or CLI `--scan-compressed` / dashboard checkbox.
1. Install **compressed** extra if using `.7z` (`uv sync --extra compressed`).
1. **Pass:** inner file contributes findings.

---

## 8. Licensing smoke (optional, enforced mode)

1. With `licensing.mode: enforced` and **no** valid `.lic`, expect CLI/API **block** (see [LICENSING_SPEC.md](LICENSING_SPEC.md)).
1. Return to `open` for general lab testing unless you are explicitly validating commercial packaging.

---

## 9. Multi-host Linux (optional matrix: DNS, SSH, different distros)

**Purpose:** The “accidental homelab” often grows to **several boxes** (e.g. daily driver laptop, mini-PC, Raspberry Pi, later a **hypervisor + VMs**). Same playbook as §1, but **repeat a minimal slice** on each OS class to catch **glibc vs musl**, **ARM vs x86_64**, **package manager**, **RAM**, and **virtual vs bare-metal** surprises.

**Policy (operator + agent):** Do **not** install OS packages (`apt`, `xbps`, `apk`, …) from automation without the operator approving. If `uv` or Python headers are missing, note it and let the operator install; then re-run §1.1–1.2.

| Host role (example)                                                                                                                                                          | Suggested checks                                                                                                                                                          | Notes                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| -------------------                                                                                                                                                          | ----------------                                                                                                                                                          | -----                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| **Primary lab / dashboard** (e.g. Debian/Ubuntu or **Ubuntu-based desktop**—Linux Mint, **Zorin OS**, Pop!_OS, etc.—with Docker CE; internal DNS name only in private notes) | §1.1–1.2; `uv run python main.py --web --host 0.0.0.0 --port 8088`; `/health`; one dashboard scan; optional §2                                                            | Proves **LAN bind**, firewall, real `config.yaml` (gitignored). Treat like Ubuntu for `apt` packages and Docker docs. **Swarm mode** on the same host does not block §1.3–1.5; watch port clashes. Docker §1.3–1.5 optional if you already run from venv.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| **Second x86_64 Linux** (e.g. Void, Alpine, musl-based)                                                                                                                      | §1.1–1.2 minimum; same **filesystem synthetic** §2 if paths differ                                                                                                        | Watch **wheel / native deps** (e.g. `cryptography`, `lxml`); may need build tools—**operator** installs per distro docs. **Void rolling** can ship **Python 3.14+** while docs still cite **3.12–3.13** examples—still meets **`requires-python >=3.12`**; confirm with **`uv sync`** + **`pytest`** on that host (private **`LAB_SOFTWARE_INVENTORY.md`** §3.3).                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| **RHEL/Fedora/AlmaLinux** (enterprise family)                                                                                                                                | §1.1–1.2 + §2; use **`dnf`** for system deps (see [OS_COMPATIBILITY_TESTING_MATRIX.md](OS_COMPATIBILITY_TESTING_MATRIX.md) Tier 1)                                        | **AlmaLinux 9** or **Fedora 40+** recommended; **RHEL 8** may need **SCL** for Python 3.12. Document **package name** differences (e.g. `python3.12-devel` vs `python3.12-dev`) in private notes or public troubleshooting.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| **Arch/Manjaro/BigLinux** (rolling, `pacman`)                                                                                                                                | §1.1–1.2 + §2; see [OS_COMPATIBILITY_TESTING_MATRIX.md](OS_COMPATIBILITY_TESTING_MATRIX.md) Tier 2                                                                        | **Arch** or **Manjaro** first; **BigLinux** likely similar. **Rolling** can expose **new** dependency issues early.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| **Gentoo** (source-based, `emerge`)                                                                                                                                          | §1.1–1.2 only if time allows; see [OS_COMPATIBILITY_TESTING_MATRIX.md](OS_COMPATIBILITY_TESTING_MATRIX.md) Tier 3                                                         | **Slow** to install; **USE flags** matter; test for **compile-time** edge cases, not first smoke.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| **illumos** (OpenIndiana, OmniOS, …) / legacy **OpenSolaris** media                                                                                                          | **Exploratory** — [OS_COMPATIBILITY_TESTING_MATRIX.md](OS_COMPATIBILITY_TESTING_MATRIX.md) **Tier 4**                                                                     | **Not** glibc Linux; expect **build/pip** pain. Prefer **current illumos** over unmaintained **OpenSolaris** ISOs for anything connected to a network.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| **ARM SBC** (e.g. Raspberry Pi 3)                                                                                                                                            | §1.1–1.2; **CLI one-shot** on tiny FS target; avoid full **DL** extra unless experimenting                                                                                | Prefer `scan.max_workers: 1`, skip sentence-transformers unless RAM allows; document “Pi profile” in private notes.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| **Hypervisor “main server”** (e.g. **Proxmox VE** — Debian-based — on a **x86_64** tower with plenty of RAM/disk)                                                            | Run §1–§2 (and optional §4 DB lab) **inside a Linux VM or LXC**, not on the hypervisor root unless you deliberately choose that                                           | **Guest:** Debian/Ubuntu (or derivative) matches most docs and Docker examples. **Networking:** vmbr/bridge or VLAN so the guest can reach DB containers or LAN targets per your design; use **guest DNS names** in `config.yaml` for §4. **Storage:** give the guest enough disk for repo + `uv` cache + Docker layers. Record Proxmox node name, VMID, and bridges only in private notes.                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| **Legacy Intel Mac** (e.g. older **Mac mini** era, out of service until repaired)                                                                                            | **Defer** entire row until the machine **POSTs** and you can install a **supported** Python (3.12+); then §1.1–1.2 and optional Docker (**Docker Desktop** or **Colima**) | **Lowest priority** in the matrix—does not block other hosts. Very old macOS may not support current Python; document ceiling in private notes when live.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| **Spare commodity x86_64 desktop** (e.g. older **Core i3**–class tower, unbranded/OEM—**optional**, only if you need more metal)                                             | **§1.1–1.2** + **§2** CLI or thin dashboard; avoid heavy **DL** / large parallel scans unless RAM (≥8 GB) and disk are comfortable                                        | **Not required** for the plan. Use when: primary is busy, you want a **dedicated** long-running scan box, or you need an extra **glibc** Linux without touching the Proxmox tower. Prefer **lightweight distro** + SSD if available; SSD + RAM upgrade cheaply improves `uv`/Docker more than CPU. Record model/RAM/disk only in private notes.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| **Secondary x86_64 laptop (modern business class — e.g. ThinkPad LAB-NODE-01 Gen 3–4 or similar)**                                                                                   | **§1.1–1.2** + **§2** + optional **§1.3–1.6**; see **§9.2** for **parallel** Docker / pytest ideas                                                                        | Often **much faster** and **more RAM** than an **older** primary lab laptop—**enable early** if you want a **dedicated** “burst” box: multiple **`docker run`** smokes, **`pytest -n`** (`pytest-xdist`), or **Compose** stacks **without** loading your daily driver. **Bare Linux + Docker CE** is usually better than **Proxmox on a laptop** (Wi‑Fi, sleep, GPU passthrough pain). **Orchestration:** **Docker Compose** or **single-node Swarm** first; **k3s** only if you explicitly want Kubernetes practice—reserve **Proxmox + many VMs** for the **tower**. **Corporate IT** can publish **mirrored base images** to a **local registry** on this host; your job is still **§1.5** smoke per image tag. **OS:** native **Ubuntu/Zorin**-family or **Win11+WSL2**; exact **MTM/RAM** in **`docs/private/homelab/`** only. |
| **Windows 11 dev laptop — extra WSL2 distros** (same physical machine as **primary dev**)                                                                                    | **§1.1–1.2** + **§2** **inside each** distro you care about (clone repo on **ext4**, not `/mnt/c/…`)                                                                      | **Optional** matrix expansion: e.g. **Debian** (default) + **Ubuntu 24.04** for Ubuntu-line parity—**only** if **`C:`** free space and **RAM** allow ([WINDOWS_WSL_MULTI_DISTRO_LAB.md](WINDOWS_WSL_MULTI_DISTRO_LAB.md)). Does **not** count as a separate physical laptop; see **three-laptop** picture below.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |

**Three laptops (operator hardware, generic roles):** **(1)** **Windows + WSL** dev, **(2)** **native Linux** primary lab (e.g. Ubuntu derivative with Docker), **(3)** **secondary** laptop (often **newer** silicon—good for **parallel** lab work; see row above). **WSL guests** on **(1)** add **software** diversity, not a fourth **chassis**.

### 9.2 Parallel testing rig (optional — secondary laptop or tower guest)

**Goal:** Run **many** short **Docker** or **pytest** jobs **concurrently** to save time and keep **CPU/RAM** off the primary dev machine.

| Approach                                              | Complexity       | When                                                                                         |
| --------                                              | ----------       | ----                                                                                         |
| **Shell loop / `GNU parallel`** + `docker run --rm …` | **Low**          | N images or N config stubs; good on a **fresh** Linux install with Docker.                   |
| **Docker Compose** `profiles` or multiple services    | **Low**          | Few fixed stacks (e.g. app + fake Postgres) side by side on different ports.                 |
| **Single-node Docker Swarm** + stacks                 | **Medium**       | You already use Swarm elsewhere—same mental model; **overlay** DNS for multi-service smokes. |
| **pytest-xdist** (`-n auto`) on cloned repo           | **Low**          | Unit/integration **CPU** parallelism; not a substitute for **multi-container** §4 checks.    |
| **k3s / k0s** on the laptop                           | **Higher**       | Learning / prod-like deploy only; **not** required for Data Boar validation.                 |
| **Full hypervisor on the laptop** (Proxmox, etc.)     | **Usually skip** | Prefer **tower + Proxmox** for 24/7 VMs; laptops add **power/network** friction.             |

**IT-built images:** If **IT** supplies **hardened** or **air-gapped** base images, point **`docker pull`** at their **registry**, then run the same **§1.3–1.5** smoke—no need for them to run Data Boar themselves unless policy requires it.

**SSH:** `you@<hostname>` (your lab user) with keys is ideal for **read-only** checks (`git rev-parse HEAD`, `uv run pytest -q`, `ls report.output_dir`). Use **internal DNS names** you assign (e.g. `audit-laptop`, `mini-pc`, `arm-sbc`)—**do not put real hostnames, LAN IPs, or home paths in the public GitHub repo**; record those only under **gitignored** `docs/private/homelab/` or your wiki ([PRIVATE_OPERATOR_NOTES.md](../PRIVATE_OPERATOR_NOTES.md)).

### 9.3 Cluster simulation, Alpine / AlmaLinux, and when horizontal scale matters

**After** the **x86 tower + Proxmox** (e.g. HP ML310e-class) is available, you may run **several Linux guests**—**Alpine**, **AlmaLinux**, or other **matrix** rows from [OS_COMPATIBILITY_TESTING_MATRIX.md](OS_COMPATIBILITY_TESTING_MATRIX.md)—each with **Docker** and/or **Podman**, to **simulate** a **multi-node** environment (independent VMs ≈ independent “nodes”) for **plan-driven** work: ingress + replicas, worker splits, resilience drills. **Horizontal scale** and **HA** become **plan priorities** when stakeholders need **SLA stories**, load tests show **single-node saturation**, or the product/docs assume **N replicas**—not for the initial **–1L** pass. Full detail and a **when-to-worry** table: [LAB_OP_MINIMAL_CONTAINER_STACK.md §5](LAB_OP_MINIMAL_CONTAINER_STACK.md#5-future-hp-tower-alpine--almalinux-and-simulated-cluster-labs).

### 9.1 When to have hardware ready (operator; sync with PLANS_TODO order –1L)

These are **your** manual tasks; the repo plan only needs you **ready enough** before a focused validation session.

| Gate                                                                                              | Have this ready before you block time for **–1L / §9** on that target                                                                                                                                                                                                                                                                                                                                                               |
| ----                                                                                              | ----------------------------------------------------------------------                                                                                                                                                                                                                                                                                                                                                              |
| **Keep going now**                                                                                | Nothing waits on the future tower or the broken Mac. Continue **primary** + **second x86_64** (e.g. musl) + **ARM** as already listed in [PLANS_TODO § H1 item 0](../plans/PLANS_TODO.md#h1u1-a-near-term-focus-current-billing-cycle).                                                                                                                                                                                             |
| **Proxmox / x86 “main lab server”** (e.g. tower class with **Xeon**, hypervisor **Debian-based**) | **Proxmox installed**; **≥1 Linux VM or privileged LXC** with enough CPU/RAM/disk; **network** (bridge/VLAN) so that guest matches how you will run Data Boar and §4 DB containers; **guest** has `git` + **`uv`** and/or **Docker**. Then run **full §1 + §2** on the **guest** (treat the guest like any other Linux row in the table). Optional: migrate long-lived **§4** Postgres/MySQL labs off a laptop once this is stable. |
| **Intel Mac mini (or similar), currently not working**                                            | **No** prep for this plan until hardware is **fixed and boots**; then re-read the **Legacy Intel Mac** row and check Python/Docker support for that macOS version.                                                                                                                                                                                                                                                                  |
| **Spare i3-class desktop** (optional)                                                             | **No** deadline. Bring online only if you want **extra x86_64 capacity** (see §9 table row). Before a session: clean install or wipe **Linux** (Debian/Ubuntu family keeps parity with docs), **≥8 GB RAM** if possible, SSD recommended; then same **§1.1–1.2 + §2** as any other Linux row.                                                                                                                                       |
| **Secondary laptop (modern business class — e.g. LAB-NODE-01 Gen 3–4–class)**                             | **Prioritise soon** if it beats older lab laptops on **CPU/RAM**: bare **Linux + Docker** or **Win11+WSL2**; then **§1.1–1.2 + §2** and optional **§9.2** parallel smokes. Record **MTM/RAM** in **`docs/private/homelab/`**.                                                                                                                                                                                                       |

**When to update PLANS_TODO:** After **each** host completes §1.1–1.2 + **either** §1.3–1.6 **or** §2, add a **dated one-line** note in **`docs/private/homelab/`** (gitignored) and optionally ping **order –1L** as *Tracked (partially done)* in the central list—not **Done** until §12 criteria match.

---

## 10. SonarQube (optional)

If you run a lab SonarQube server, follow [SONARQUBE_HOME_LAB.md](SONARQUBE_HOME_LAB.md). Validation there is **code quality**, not data connectivity.

---

## 11. Record results (lightweight)

Keep a **dated note** (e.g. in **`docs/private/homelab/`** or a personal wiki): date, hostnames tried, image tag, targets tried, pass/fail, and **one** lesson (e.g. “Postgres needed `host` = service name on lab-net”). Updates **PLANS_TODO** only when you change supported behaviour or find a doc gap worth fixing in-repo.

### 11.1 Lockfile and published image (keep –1L aligned with –1 / –1b)

When **`uv.lock`**, **`requirements.txt`**, or **`Dockerfile`** change on **`main`**, keep **Docker Hub** and **lab** on the same rhythm: refresh a **local** image with **`scripts/docker-lab-build.ps1`**, **publish** per **[DOCKER_IMAGE_RELEASE_ORDER.md](DOCKER_IMAGE_RELEASE_ORDER.md)** (semver in `pyproject.toml`, Scout gate, Hub description when needed), then run **§1.3–1.6** on a lab host using **`fabioleitao/data_boar:latest`** or the same **semver** tag so the digest you smoke-test matches what pullers get. Record **`git` HEAD**, **`uv.lock`** hash, and **image ID** only under **`docs/private/homelab/`**—not in this file.

---

## 12. When you are “done” with a lab pass

- Image builds; default **open** licensing; **at least one** filesystem synthetic run; **optional** one SQL container run.
- **Production** still needs your org’s backup, secrets, TLS, rate limits, and legal review—this playbook is **technical confidence**, not a prod sign-off.

---

## See also

- [LAB_SMOKE_MULTI_HOST.md](LAB_SMOKE_MULTI_HOST.md) — **multi-host** DB + filesystem lab, optional **SSHFS / WebDAV / iSCSI→FS**, checklist **A–M**, and what “**completão**” means vs this file’s §1 baseline.
- [OS_COMPATIBILITY_TESTING_MATRIX.md](OS_COMPATIBILITY_TESTING_MATRIX.md) — **which Linux distros** to test (RHEL/Fedora/AlmaLinux, Arch/Manjaro/BigLinux, Gentoo, musl) prioritized by **production relevance** and **Python 3.12+** availability.
- [LAB_OP_MINIMAL_CONTAINER_STACK.md](LAB_OP_MINIMAL_CONTAINER_STACK.md) §5 — **tower / Alpine / AlmaLinux**, multi-VM “cluster” simulation, **when** to prioritize **HA / horizontal scale** (vs **–1L** baseline).
- [HOMELAB_LOCAL_REPOSITORIES.md](HOMELAB_LOCAL_REPOSITORIES.md) — **local Docker registry** and **apt repository** on Proxmox **after** the server is ready; enables **offline** validation, **faster** pulls, and **testing** `.deb` builds before public release.
- [HOMELAB_HOST_PACKAGE_INVENTORY.md](HOMELAB_HOST_PACKAGE_INVENTORY.md) — what the repo **expects** on Linux vs **your** installed packages (inventory script; no remote visibility from GitHub/CI).
- [HOMELAB_POWER_AND_ELECTRICAL_PLANNING.md](HOMELAB_POWER_AND_ELECTRICAL_PLANNING.md) — calculate **power draw**, **UPS sizing**, and **circuit breaker** capacity before you run out of outlets or trip breakers.
- [HOMELAB_UNIFI_LAB-ROUTER-01_LAB_NETWORK.md](HOMELAB_UNIFI_LAB-ROUTER-01_LAB_NETWORK.md) — **UniFi Dream Machine SE**: lab **VLANs/firewall** patterns and **SNMP** polling from a laptop **before** a monitoring server exists.
- [HOMELAB_MOBILE_OPERATOR_TOOLS.md](HOMELAB_MOBILE_OPERATOR_TOOLS.md) — **iPhone / Android tablet** as operator tools: UniFi app, GitHub notifications, Bitwarden, LAN SSH, web UI smoke tests, **photo** inventory (private notes only).
- [WINDOWS_WSL_MULTI_DISTRO_LAB.md](WINDOWS_WSL_MULTI_DISTRO_LAB.md) — **Windows dev laptop:** add **extra WSL2** distros for §9 matrix if **disk/RAM** allow; **`windows-dev-report.ps1`** inventory.
- [PRIVATE_OPERATOR_NOTES.md](../PRIVATE_OPERATOR_NOTES.md) — **real** homelab facts vs **public** docs (`docs/private/homelab/`; no Markdown links to private paths on GitHub).
- [TOKEN_AWARE_USAGE.md](../plans/TOKEN_AWARE_USAGE.md) — after lab validation, return to one-row-per-session feature work ([PLANS_TODO.md](../plans/PLANS_TODO.md)).
- [CODE_PROTECTION_OPERATOR_PLAYBOOK.md](../CODE_PROTECTION_OPERATOR_PLAYBOOK.md) — Priority band A (deps, Scout, Hub) before heavy feature bursts when urgent.
