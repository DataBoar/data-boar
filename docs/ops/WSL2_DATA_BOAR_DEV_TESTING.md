# Windows WSL2 — Data Boar dev and lab testing

**Português (Brasil):** [WSL2_DATA_BOAR_DEV_TESTING.pt_BR.md](WSL2_DATA_BOAR_DEV_TESTING.pt_BR.md)

**Purpose:** Treat **WSL2** on the primary Windows dev machine (typical ThinkPad-class laptop) as an **optional second execution surface** alongside native Windows and alongside Linux laptops (LAB-NODE-01, lab-node-02). This does **not** replace CI or homelab hosts; it reduces the risk of assuming a single OS or a single container runtime for how customers or integrators run Data Boar.

---

## 1. Why WSL2 shows up in this project

- **Execution diversity:** Integrators may run `uv run python main.py` on Windows, in WSL, in a container, or on a bare-metal Linux server. The product must not silently assume one layout.
- **Path and newline differences:** YAML paths, bind mounts, and `file_scan` roots behave differently under `C:\...`, `\\wsl$\...`, and `/home/...` inside WSL.
- **Networking:** TCP targets for lab databases (see [LAB_SMOKE_MULTI_HOST.md](LAB_SMOKE_MULTI_HOST.md)) must use the **LAN IPv4** of the hub host (LAB-NODE-01 or lab-node-02), not `localhost`, unless Data Boar and the DB containers share one machine and published ports.

---

## 2. Minimal setup (WSL2 Ubuntu or Debian-based)

1. Install **WSL2** and a distro from Microsoft’s docs (same major Python as [TECH_GUIDE.md](../TECH_GUIDE.md): **≥3.12**, **3.13** when available).
1. Clone the repo into the WSL filesystem (avoid heavy I/O on `/mnt/c/...` for `uv sync` and pytest).
1. Install **`uv`**, then from the repo root: `uv sync` (add `--extra nosql`, `--extra compressed` when matching full lab smoke).
1. Point scan config at lab DBs using the **hub host LAN IP** and ports **55432** / **33306** (from [LAB_SMOKE_MULTI_HOST.md](LAB_SMOKE_MULTI_HOST.md)).

**Docker inside WSL:** Optional. If you use **Docker Desktop** with WSL integration, published ports on Windows may differ from raw Linux; prefer explicit LAN IPs for cross-host smoke. A second **Docker CE** hub on **LAB-NODE-01** and **lab-node-02** is enough for lab policy (no requirement to run compose on LAB-NODE-03 or LAB-NODE-04).

---

## 3. What to record after a WSL2 pass

- Distro name/version, `python --version`, and whether the run used **native venv** only or **Docker Desktop** integration.
- Any **firewall** or **Windows Defender** prompt that blocked outbound TCP to the lab subnet (document for your operator notes under `docs/private/`, not in git-tracked inventory).

---

## 4. Related docs

- [LMDE7_LAB-NODE-01_DEVELOPER_SETUP.md](LMDE7_LAB-NODE-01_DEVELOPER_SETUP.md) — ThinkPad LAB-NODE-01 + Docker CE via Ansible baseline.
- [LAB_SMOKE_MULTI_HOST.md](LAB_SMOKE_MULTI_HOST.md) — DB stack, checklist, two-hub policy.
- [HOMELAB_VALIDATION.md](HOMELAB_VALIDATION.md) — Broader lab playbook.
- [ops/automation/ansible/README.md](../../ops/automation/ansible/README.md) — `lab-node-01-baseline.yml`, Docker CE, operator `docker` group.

**Last review:** 2026-04 — aligns with multi-host lab smoke and LAB-NODE-01 baseline automation.
