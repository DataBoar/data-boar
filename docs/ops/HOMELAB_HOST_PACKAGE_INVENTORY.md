# Homelab host package inventory (Data Boar)

**Purpose:** We **cannot** see what is installed on your machines from this repository or from the AI environment—no SSH to your LAN. This page lists what **Data Boar’s docs assume** on Linux, and gives **commands + a script** so **you** can capture inventory and (optionally) paste **redacted** output for a gap review.

**Related:** [HOMELAB_VALIDATION.md](HOMELAB_VALIDATION.md) · [TECH_GUIDE.md](../TECH_GUIDE.md) (install + connectors) · [SECURITY.md](../../SECURITY.md) (runtime prerequisites)

---

## 1. What the repo expects (baseline, not “what you have”)

These are **recommended** system packages for **Debian/Ubuntu / Zorin / Proxmox guests** when building native wheels and using common SQL drivers (from [TECH_GUIDE.md](../TECH_GUIDE.md) and [SECURITY.md](../../SECURITY.md)):

| Purpose                                 | Debian/Ubuntu packages (examples)                      |
| -------                                 | -----------------------------------                    |
| Python 3.12 + venv + headers            | `python3.12`, `python3.12-venv`, `python3.12-dev`      |
| Compiling some Python deps              | `build-essential`                                      |
| PostgreSQL client libs (psycopg2 build) | `libpq-dev`                                            |
| Generic TLS / FFI                       | `libssl-dev`, `libffi-dev`                             |
| ODBC (SQL Server and others via pyodbc) | `unixodbc-dev` (+ vendor ODBC driver where applicable) |

**Application Python deps** come from **`uv sync`** / `pyproject.toml` + **`uv.lock`**—not from `apt`. Optional extras:

- **NoSQL:** `uv pip install -e ".[nosql]"` (MongoDB, Redis)
- **Shares, compressed archives, big data, ML/DL, etc.:** see [TECH_GUIDE.md](../TECH_GUIDE.md) and `pyproject.toml` `[project.optional-dependencies]`

**Docker (lab §1.3–1.5):** `docker-ce` (or distro package), `containerd`; Swarm/Kubernetes are **your** choice—Data Boar only needs `docker build` / `docker run` (or equivalent in VM).

**Not in repo as hard deps:** Ansible, OpenTofu, Terraform, Prometheus, Grafana, InfluxDB, Loki, Graylog/OpenSearch (optional observability — see [PLAN_LAB_OP_OBSERVABILITY_STACK.md](../plans/PLAN_LAB_OP_OBSERVABILITY_STACK.md)), **Wazuh** (optional SIEM — [LAB_OP_MINIMAL_CONTAINER_STACK.md](LAB_OP_MINIMAL_CONTAINER_STACK.md) §6), SonarQube, Lynis—these are **operator tools** you install when you run those workflows.

---

## 2. Optional system bits by connector (install only if you use that target)

| Connector                  | Typical extra system setup                                                                                                                  |
| ---------                  | --------------------------                                                                                                                  |
| **Oracle**                 | Oracle Instant Client + env (`LD_LIBRARY_PATH`) per Oracle docs                                                                             |
| **SQL Server**             | Microsoft ODBC Driver for Linux + `unixodbc`                                                                                                |
| **Snowflake / other ODBC** | Vendor ODBC driver + `unixodbc`                                                                                                             |
| **Void / Alpine (musl)**   | Same logical deps; package names differ (`xbps-install` / `apk add`); you may need more **build** packages for `cryptography`, `lxml`, etc. |

If you tell us **which connectors** you actually scan in lab, we can narrow the list.

---

## 2.5 Optional developer toolchains (Go, Rust, Zig, Odin, Homebrew)

**Data Boar itself is Python 3.12+** (`pyproject.toml` / `uv`). **Go, Rust, Zig, Odin, and Linuxbrew do not** need to be installed for **§1.1–1.2**, **Docker** builds, or normal connector tests. They are **nice for you** as a developer and for **adjacent** repos or experiments.

| Toolchain                    | Role vs this repo                                                                                                                                                                                                                                       |
| ---------                    | -----------------                                                                                                                                                                                                                                       |
| **Go**                       | Useful for **sidecars**, small CLIs, or infra tools; **no** Go source in Data Boar today.                                                                                                                                                               |
| **Rust**                     | Same; **only** becomes relevant here if we ever ship a **Rust extension** for Python (**PyO3** / **maturin**)—**not** on the current critical path. Some **Python wheels** ship prebuilt binaries; you rarely need `rustc` unless building from source. |
| **Zig / Odin**               | Great for **systems learning** and personal tools; **no** expectation for Data Boar operators.                                                                                                                                                          |
| **Homebrew** (**linuxbrew**) | Parallel to **`apt`**/**`xbps`**; can install **newer** dev tools on distros with stale packages—keep mental track of **two** package worlds (`brew` vs distro) to avoid PATH confusion.                                                                |

**When extra languages *would* make sense for the product:** a **proven** bottleneck (e.g. a hot path measured in prod), a **security** boundary (small audited binary), or a **mandatory** integration SDK only available in native code—until then, **stay Python-first** to match CI, docs, and onboarding.

**Quick capture (optional):** `go version`, `rustc --version`, `zig version`, `odin version`, `brew --version` — reported by `homelab-host-report.sh` in the **optional toolchains** block.

---

## 3. Capture inventory on each host (manual one-liners)

Run on **each** machine (Proxmox **node**, each **VM**, laptop, Pi, etc.). **Redact** IPs, hostnames, and user paths before sharing in chat.

## OS / kernel

```bash
cat /etc/os-release 2>/dev/null; uname -a
```

## CPU / memory (rough capacity planning)

```bash
nproc 2>/dev/null; free -h 2>/dev/null
```

## Python / uv

```bash
command -v python3 && python3 --version
command -v uv && uv --version
```

## Docker

```bash
command -v docker && docker version
docker info 2>/dev/null | head -30   # optional; may show swarm — redact if needed
```

## Bitwarden CLI (optional)

```bash
command -v bw && bw --version
```

## Claude Code CLI (optional)

```bash
command -v claude && claude --version
```

**Install (vendor-recommended, glibc Linux / macOS / WSL):** per [Claude Code setup](https://docs.anthropic.com/en/docs/claude-code/setup):

```bash
curl -fsSL https://claude.ai/install.sh | bash
# Ensure ~/.local/bin is on PATH, then:
claude --version
```

**musl hosts (Void Linux, Alpine):** the same installer may need extra packages and settings analogous to Anthropic’s **Alpine** notes (**`libgcc`**, **`libstdc++`**, **`ripgrep`**, and sometimes **`USE_BUILTIN_RIPGREP=0`** in `settings.json`) — see **Advanced setup** in the doc above. **RAM:** vendor specifies **4 GB+** (fine on **<lab-host-2>**; **not** on **Pi 3B** class hardware).

## Ollama (optional — local LLM runtime)

```bash
command -v ollama && ollama --version
ollama list
```

**Lab note:** pulled models live under Ollama’s store (often **`~/.ollama`** or distro package path) and can consume **many GiB** — include them in disk planning next to Docker layers and ISOs. Default API port is **11434**; bind to **localhost** or **LAN** only; do **not** expose to the public Internet without a deliberate reverse proxy + auth.

**WSL2 vs another Linux host:** each distro’s **ext4 VHD** has its **own** **`~/.ollama`** (and **`ollama list`**). Same **semver** (**`ollama --version`**) on **WSL** and a **lab-op** host does **not** imply shared weights — **`ollama pull`** must be run where you want the model to run.

## Debian/Ubuntu: installed packages (filtered)

```bash
dpkg-query -W -f='${Package}\t${Version}\n' \
  python3.12 python3.12-venv python3.12-dev build-essential \
  libpq-dev libssl-dev libffi-dev libmariadb-dev unixodbc-dev \
  docker-ce docker.io containerd lynis bitwarden-cli 2>/dev/null || true
# Full list (large): dpkg -l > dpkg-l.txt
```

**`uv sync` / PyPI `mariadb` + `mysqlclient` (Debian, Ubuntu, Raspberry Pi OS):** if the build fails with **`mariadb_config: not found`** / **`MariaDB Connector/C … not found`**, install the C connector **development** package (provides **`mariadb_config`** and headers):

```bash
sudo apt install -y libmariadb-dev pkg-config build-essential
command -v mariadb_config   # expect /usr/bin/mariadb_config on trixie/bookworm
```

Then **`uv sync`** again from the repo root. On **aarch64** (e.g. **Pi 3/4**) wheels may be missing — expect **compile** + **RAM** use; **`scan.max_workers: 1`** already recommended for the Pi. If the utility lives elsewhere, set **`MARIADB_CONFIG=/path/to/mariadb_config`**.

## Void Linux

```bash
xbps-query -l | grep -E 'python3|docker|uv|build-essential|openssl|lynis' || xbps-query -l
```

**Native wheels / `uv sync` (e.g. `mysqlclient`):** the linker error **`cannot find -lz`** means **`zlib-devel`** is missing (Debian/Ubuntu call it `zlib1g-dev`). For **`mysqlclient`** you also need MariaDB/MySQL **C client headers** and **`pkg-config`** files so the build can find `mysqlclient` / `mariadb`:

```bash
sudo xbps-install -S zlib-devel pkg-config
# MariaDB C headers + libs for mysqlclient (name on Void is usually mariadb-devel):
sudo xbps-install -S mariadb-devel
# If unsure: xbps-query -Rs mariadb | grep -i devel
```

Then **`uv sync`** again from the repo root. **`uv`** may use its own **CPython 3.13.x** even when **`python3` on PATH** is **3.14** — that is normal unless you pin **`UV_PYTHON`** / **`.python-version`**.

**No Docker/Podman on host:** use **`uv sync`** on the metal (with the packages above) or run tests in a **Linux/glibc** environment (e.g. a **lab-op** host or the published **Docker** image) when **musl** builds are too painful.

## Alpine

```bash
apk info -e python3 py3-pip docker docker-cli 2>/dev/null; apk list -I 2>/dev/null | head -80
```

---

## 4. Automated bundle script (Linux)

From the **repo root** on a machine that has the repo (or copy the script only):

```bash
bash scripts/homelab-host-report.sh
```

The script prints **`bw` (Bitwarden CLI)** when it is on **`PATH`** (path + `bw --version`). It does **not** run `bw status` (that can include your **email** in JSON—run manually if needed, redact before sharing).

It also captures a **read-only sample** of **sysctl** (`vm.*` dirty ratios / swappiness), **`lsblk`**, **block I/O queue** (`scheduler`, `rotational`, `nr_requests`), and **cpufreq** governor when present — useful after you tune **`/sys`** or kernel parameters for tests.

Save stdout to a file, **redact**, then share if you want a structured review.

**Extended security posture snapshot:** see [HOMELAB_HOST_REPORT_EXTENDED.md](HOMELAB_HOST_REPORT_EXTENDED.md).

### 4.1 Lynis line looks wrong (`db/languages/.../data-boar` or `lynis: not in PATH`)

**Cause (common on Debian/Ubuntu/Zorin):** the real binary is **`/usr/sbin/lynis`**, but **non-login** environments sometimes omit **`/usr/sbin`** from **`PATH`**, so **`command -v lynis`** fails. Running **`lynis`** from the repo directory can also confuse some builds that resolve paths relative to **cwd**.

**What the script does:** resolve **`/usr/sbin/lynis`** (or **`dpkg-query -L lynis`**) first, **`cd /tmp`**, then run **`lynis show version`** with a minimal **`env -i`** **`PATH`**.

**Manual check:** `( cd /tmp && /usr/sbin/lynis show version )` — if that works, the script should match after you **`git pull`** the updated **`scripts/homelab-host-report.sh`**.

### 4.2 Remote capture from Windows (SSH)

The AI environment **cannot** open your LAN. From the **Cursor terminal** on your dev PC (OpenSSH + `Host` entries in `~/.ssh/config`):

```powershell
.\scripts\collect-homelab-report-remote.ps1 -SshHost your-lab-alias
```

This runs `homelab-host-report.sh` on the remote host and writes **`docs/private/homelab/reports/<alias>_<timestamp>_homelab_host_report.log`** (create the `reports` folder under your gitignored `docs/private/homelab/` if needed; see **`docs/private.example/homelab/reports/README.md`**).

**Batch (multi-host + `git pull`):** **`scripts/lab-op-sync-and-collect.ps1`** — see **`docs/private.example/homelab/reports/README.md`** and **[LAB_OP_SYNC_RUNBOOK.md](../private.example/homelab/LAB_OP_SYNC_RUNBOOK.md)**.

### 4.3 When `git pull` fails (local changes on the clone)

**Not the usual cause:** local **SQLite** DBs and typical **logs** are listed in **`.gitignore`** (e.g. `db.sqlite3`, `audit_results.db`) — Git **ignores** them, so they **do not** block `git pull`. If pull still fails, run **`git status`** on the host: Git will list **tracked** files with local edits (often **`scripts/homelab-host-report.sh`** after a session or a partial merge).

If **`lab-op-sync-and-collect.ps1`** logs show `Your local changes … would be overwritten by merge`, either:

1. **On that host:** `cd` to the repo, **`git stash`** (or **`git checkout -- scripts/homelab-host-report.sh`** if you only want upstream), then re-run the collect script; or **commit** intentional local edits and merge/rebase consciously.
1. **Report only (no pull):** `.\scripts\lab-op-sync-and-collect.ps1 -SkipGitPull` — still captures inventory; does not advance `main`.

Validate **`lab-op-hosts.manifest.json`** is valid JSON (commas between `hosts[]` objects). See **[LAB_OP_SYNC_RUNBOOK.md](../private.example/homelab/LAB_OP_SYNC_RUNBOOK.md)** (copy to `docs/private/homelab/` for dated notes).

---

## 5. What to send back (if you want “do I miss anything?”)

1. **Host role** (e.g. primary Zorin, musl mini-PC, Pi, Proxmox guest Debian 12).
1. **Output** of `homelab-host-report.sh` (redacted) **or** the one-liners above.
1. **Which Data Boar features you use** on that host: filesystem only / Postgres / MSSQL / Docker image only / ML / DL / etc.

Then we can say “install X” or “optional Y for connector Z”—without guessing.

---

## 6. Proxmox-specific note

- **Hypervisor (pve):** inventory the **node** separately from each **VM/LXC**.
- **Guests:** treat each Linux guest like any other row in [HOMELAB_VALIDATION §9](HOMELAB_VALIDATION.md#9-multi-host-linux-optional-matrix-dns-ssh-different-distros)—Python/`uv`/Docker are installed **inside** the guest unless you deliberately run from the host.

---

**Português (Brasil):** [HOMELAB_HOST_PACKAGE_INVENTORY.pt_BR.md](HOMELAB_HOST_PACKAGE_INVENTORY.pt_BR.md)
