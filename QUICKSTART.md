# Data Boar — Quick start (about 5 minutes)

**Português (Brasil):** [QUICKSTART.pt_BR.md](QUICKSTART.pt_BR.md)

**Audience:** DPO, legal, compliance, or an IT sponsor who wants to **see a result** before reading the full manual.

**Go deeper later:** [docs/USAGE.md](docs/USAGE.md) (operator) · [docs/TECH_GUIDE.md](docs/TECH_GUIDE.md) (integrator) · [docs/pitch/INDEX.md](docs/pitch/INDEX.md) (narrative by role)

---

## What you will have

At the end of this walkthrough you will have:

1. The engine running (Docker **or** local Python).
2. A demo scan against a test folder in the repository.
3. **dashBOARd** in the browser with findings and a heatmap.

Data Boar **does not replace** legal advice; it produces **technical signals** for triage.

---

## Prerequisites (minimum)

| Path | You need |
| ---- | -------- |
| **A — Docker (recommended with IT)** | [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running |
| **B — Local Python (IT on the same PC)** | [uv](https://docs.astral.sh/uv/) + Git; Python **3.12+** (`uv sync` resolves the rest) |

**No YAML from scratch:** copy a [sample config](deploy/samples/config.starter-lgpd-eval.yaml) **or** generate targets from a spreadsheet — [docs/ops/SCOPE_IMPORT_QUICKSTART.md](docs/ops/SCOPE_IMPORT_QUICKSTART.md).

---

## Path 0 — Zero-config (`pip` / `pipx` + `--demo`)

> **Windows and never used a terminal/Python?** Use the full **no-Docker** walkthrough (step by step): **[docs/QUICKSTART_WINDOWS.md](docs/QUICKSTART_WINDOWS.md)** (written in pt-BR).

No `config.yaml`, no Docker, no YAML — built-in **synthetic** corpus (shortcut if Python is already on PATH):

```powershell
pip install data-boar
data-boar --demo
```

On Windows, the **recommended** flow for non-technical users is **pipx** — see the [Windows guide](docs/QUICKSTART_WINDOWS.md).

**Linux via pipx:** on Debian/Ubuntu and Fedora with Python >=3.12 available, `pipx install data-boar` is usually direct. On the RHEL9 family and Alpine/musl there is one onboarding pre-step — see [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) before `pipx install`.

Open [http://127.0.0.1:8088/en/](http://127.0.0.1:8088/en/) — demo findings already loaded (or `/pt-br/`).

**In the clone (development):** `uv sync` at the repo root, then `uv run python main.py --demo` or `.\scripts\demo.sh`.

---

## Path A — Docker (less friction for non-developers)

Run from the **clone root** (adjust the repository path):

```powershell
cd C:\path\to\data-boar
mkdir -Force data | Out-Null
Copy-Item deploy\samples\config.starter-lgpd-eval.yaml data\config.yaml
docker pull fabioleitao/data_boar:latest
docker run -d --name data-boar-quickstart -p 8088:8088 `
  -v "${PWD}/data:/data" `
  -e CONFIG_PATH=/data/config.yaml `
  fabioleitao/data_boar:latest
```

<details>
<summary>Linux / macOS (bash)</summary>

```bash
cd /path/to/data-boar
mkdir -p data
cp deploy/samples/config.starter-lgpd-eval.yaml data/config.yaml
docker pull fabioleitao/data_boar:latest
docker run -d --name data-boar-quickstart -p 8088:8088 \
  -v "$PWD/data:/data" \
  -e CONFIG_PATH=/data/config.yaml \
  fabioleitao/data_boar:latest
```

</details>

1. Ask IT to adjust the paths in `data\config.yaml` (real folders **or** use [Path B](#path-b--local-python-for-developers--technical-it) with the demo folder).
2. Open in the browser: [http://localhost:8088/en/](http://localhost:8088/en/) (or `/pt-br/`).
3. In dashBOARd, start a scan (scan button) or follow the built-in help under **Help / Ajuda**.

Volume and persistence details: [docs/DOCKER_SETUP.md](docs/DOCKER_SETUP.md).

---

## Path B — Local Python (for developers / technical IT)

Best for validating the product **without** exposing real data: we use the synthetic folder `tests/data/homelab_synthetic/`.

```powershell
cd C:\path\to\data-boar
uv sync
```

Create `quickstart.config.yaml` at the clone root with:

```yaml
targets:
  - name: demo-lab
    type: filesystem
    path: tests/data/homelab_synthetic
    recursive: true
```

Start dashBOARd and accept explicit HTTP in the lab (do not use in production without TLS):

```powershell
uv run python main.py --web --config quickstart.config.yaml --allow-insecure-http
```

1. Open [http://127.0.0.1:8088/en/](http://127.0.0.1:8088/en/).
2. Start a scan from the UI.
3. Check the Excel report / heatmap in the configured output folder (default is relative to the config — see [docs/USAGE.md](docs/USAGE.md)).

**Success:** sample findings appear (fictional document patterns). If the list is empty, confirm that `path` points to the correct folder and that the scan finished without an error in the terminal log.

---

## Next steps (5–30 minutes)

| Goal | Where to go |
| ---- | ----------- |
| Real scope (folders, databases, shares) | [deploy/samples/README.md](deploy/samples/README.md) + CSV import in [docs/ops/SCOPE_IMPORT_QUICKSTART.md](docs/ops/SCOPE_IMPORT_QUICKSTART.md) |
| Map of “who reads what” | [docs/AUDIENCE_GUIDE.md](docs/AUDIENCE_GUIDE.md) |
| Regulatory frame (LGPD, GDPR, samples) | [docs/COMPLIANCE_FRAMEWORKS.md](docs/COMPLIANCE_FRAMEWORKS.md) |
| Full flag and API reference | [docs/USAGE.md](docs/USAGE.md) |
| Architecture and connectors | [docs/TECH_GUIDE.md](docs/TECH_GUIDE.md) |

---

**Maintainers:** integrity gate in [CONTRIBUTING.md](CONTRIBUTING.md).
