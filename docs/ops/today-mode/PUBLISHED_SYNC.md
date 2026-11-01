# Published release vs repo version (anti-stale)

**Português (Brasil):** [PUBLISHED_SYNC.pt_BR.md](PUBLISHED_SYNC.pt_BR.md)

**Purpose:** After you cut a **Git tag**, **GitHub Release**, or **Docker Hub** push, dated “today mode” files and **PLANS** tables can still say “operator pending” elsewhere. This page is the **short reconciliation record**: refresh it when reality changes.

**Guard:** **`tests/test_published_sync.py`** fails when this file (or the pt-BR twin) drifts from **`pyproject.toml`** (`version` + `maturity_build`), lacks the matching **`v*`** release tag line, or still links the pre-org personal GitHub path. Network checks (PyPI / Hub) are optional/`skipif`.

---

## Last verified (operator or agent)

| Field | Value |
| ----- | ----- |
| **Verified** | **2026-11-01** |
| **`pyproject.toml` on `main`** | **`1.8.0`** (`maturity_build=200`) — `1.8.0` version line on `main` (ADR-0073). |
| **PyPI** (published) | [**data-boar `1.8.0`**](https://pypi.org/project/data-boar/1.8.0/) — `pip install data-boar` (wheel `data_boar-1.8.0-py3-none-any.whl` **2026-11-01T23:15:29Z** sha256 `019e0d4227586f2113c791b513679fea0d01b40bd89bcf2521921446116c1799`; sdist `data_boar-1.8.0.tar.gz` **2026-11-01T23:15:32Z** sha256 `6fed428b8c73ff40bd6f240f1c17bf68d06d26d1693a8189c67501f9f545a49a`; `requires_python >=3.12`). TestPyPI **1.8.0**: wheel **2026-11-01T23:11:50Z**, sdist **2026-11-01T23:11:53Z**. Historical: [**`1.7.4.post12`**](https://pypi.org/project/data-boar/1.7.4.post12/). |
| **GitHub Release Latest** (published) | [**v1.8.0**](https://github.com/DataBoar/data-boar/releases/tag/v1.8.0) — title **Data Boar 1.8.0** (not pre-release), published **2026-11-01T23:11:10Z**, annotated signed tag on commit `3b0170641f2ab7a1358058902e12ff3f1fc3f545` (notes: **`docs/releases/1.8.0.md`**, **`CHANGELOG.md`**). Historical Latest: [**v1.7.4.post12**](https://github.com/DataBoar/data-boar/releases/tag/v1.7.4.post12). |
| **Docker Hub** (published) | **`fabioleitao/data_boar:1.8.0`** + **`latest`** = `sha256:1f7a8a32b2fced12969382579721d6311a6b4f3fd98d2e6ffca921da47ec6ebc` (linux/amd64, ~281 MB compressed, pushed **2026-11-01T23:28Z**; free-threaded **cp314t**, **x86-64-v2+**; **no** `-nogil` tag). Historical: **`1.7.4.post12`** (`sha256:ab8f5dad3e336…`, GIL, any x86-64), **`1.7.4`**, **`1.7.3`** intact. |
| **Wheelhouse** | [**`wheelhouse-x86-64-v1-2026-07-29`**](https://github.com/DataBoar/data-boar-site/releases/tag/wheelhouse-x86-64-v1-2026-07-29) — **58** `.whl` (incl. **14× `cp314t`**: 10 ML + 4 SQL extras `linux_x86_64`) |
| **Next publishable** | **`1.8.0`** is on PyPI + Hub + GitHub Release (**2026-11-01**). Historical published line: **`1.7.4.post12`**. |

---

## How to re-check (copy/paste)

From repo root (needs **`gh`** auth + network):

```bash
git fetch origin --tags
git tag -l "v1.8.*" --sort=-version:refname | head -5
grep -nE '^(version|maturity_build)' pyproject.toml
gh release list --repo DataBoar/data-boar --limit 5
uv run pytest tests/test_published_sync.py -q
```

Docker Hub: confirm **`1.8.0`** and **`latest`** on [hub.docker.com/r/fabioleitao/data_boar/tags](https://hub.docker.com/r/fabioleitao/data_boar/tags) or the Registry API; **Full description** matches **[`docs/ops/DOCKER_HUB_REPOSITORY_DESCRIPTION.md`](../DOCKER_HUB_REPOSITORY_DESCRIPTION.md)**. **GitHub:** **`v1.8.0`** Release exists. **PyPI:** [project page](https://pypi.org/project/data-boar/) shows **`1.8.0`** as latest.

---

## When to update this file

- **Immediately after** tag + GitHub Release + Docker push for a new version.
- **Optionally** on a slow week: confirm row still true so carryover tables do not resurrect **done** work.
- **Always** align **`docs/plans/PLANS_TODO.md`** release bullets if they still say “in-repo / operator pending” for the same number.

Automation: **`tests/test_published_sync.py`** (offline core) + **`tests/test_about_version_matches_pyproject.py`** (`pyproject.toml` ↔ runtime/man `.TH`). Network PyPI/Hub probes in the sync test are optional.
