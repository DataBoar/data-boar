# Published release vs repo version (anti-stale)

**Português (Brasil):** [PUBLISHED_SYNC.pt_BR.md](PUBLISHED_SYNC.pt_BR.md)

**Purpose:** After you cut a **Git tag**, **GitHub Release**, or **Docker Hub** push, dated “today mode” files and **PLANS** tables can still say “operator pending” elsewhere. This page is the **short reconciliation record**: refresh it when reality changes.

**Guard:** **`tests/test_published_sync.py`** fails when this file (or the pt-BR twin) drifts from **`pyproject.toml`** (`version` + `maturity_build`), lacks the matching **`v*`** release tag line, or still links the pre-org personal GitHub path. Network checks (PyPI / Hub) are optional/`skipif`.

---

## Last verified (operator or agent)

| Field | Value |
| ----- | ----- |
| **Verified** | **2026-08-18** |
| **`pyproject.toml` on `main`** | **`1.8.0-beta`** (`maturity_build=69`) — `1.8.0` beta line; octet reconciled after sprint (ADR-0073). Git-only for consumers; **not** on PyPI/Hub. |
| **PyPI** (published) | [**data-boar `1.7.4.post12`**](https://pypi.org/project/data-boar/1.7.4.post12/) — `pip install data-boar` (published **2026-07-30 00:42:09 UTC**, Trusted Publishing via **`publish-pypi.yml`**) |
| **GitHub Release Latest** (published) | [**v1.7.4.post12**](https://github.com/DataBoar/data-boar/releases/tag/v1.7.4.post12) (notes: **`docs/releases/1.7.4.post12.md`**, **`CHANGELOG.md`**; annotated tag SSH-signed). Optional pre-release tag **`v1.8.0-beta`** when operator cuts it — see [1.8.0-beta.md](../../releases/1.8.0-beta.md). |
| **Docker Hub** (published) | **`fabioleitao/data_boar:1.7.4.post12`** + **`latest`** = `sha256:ab8f5dad3e336…` (published **2026-07-30**; base **`python:3.14-slim`**, distroless nonroot, **`popcnt=0`**). Historical June GA tag **`1.7.4`** left untouched. **No** Hub marketing refresh for **`-beta`**. |
| **Wheelhouse** | [**`wheelhouse-x86-64-v1-2026-07-29`**](https://github.com/DataBoar/data-boar-site/releases/tag/wheelhouse-x86-64-v1-2026-07-29) — **56** assets (incl. **10× `cp314t`** free-threaded / no-GIL cells) |
| **Next publishable** | Promote toward **`1.8.0-rc`** / stable **`1.8.0`** per [VERSIONING.md](../VERSIONING.md) + ADR-0072/0073 (release gate + release-ritual) |

---

## How to re-check (copy/paste)

From repo root (needs **`gh`** auth + network):

```bash
git fetch origin --tags
git tag -l "v1.7.*" --sort=-version:refname | head -5
grep -nE '^(version|maturity_build)' pyproject.toml
gh release list --repo DataBoar/data-boar --limit 5
uv run pytest tests/test_published_sync.py -q
```

Docker Hub: confirm **`1.7.4.post12`** and **`latest`** on [hub.docker.com/r/fabioleitao/data_boar/tags](https://hub.docker.com/r/fabioleitao/data_boar/tags) or the Registry API; **Full description** matches **[`docs/ops/DOCKER_HUB_REPOSITORY_DESCRIPTION.md`](../DOCKER_HUB_REPOSITORY_DESCRIPTION.md)**. **GitHub:** **`v1.7.4.post12`** Release exists. **PyPI:** [project page](https://pypi.org/project/data-boar/) shows **`1.7.4.post12`** as latest.

---

## When to update this file

- **Immediately after** tag + GitHub Release + Docker push for a new version.
- **Optionally** on a slow week: confirm row still true so carryover tables do not resurrect **done** work.
- **Always** align **`docs/plans/PLANS_TODO.md`** release bullets if they still say “in-repo / operator pending” for the same number.

Automation: **`tests/test_published_sync.py`** (offline core) + **`tests/test_about_version_matches_pyproject.py`** (`pyproject.toml` ↔ runtime/man `.TH`). Network PyPI/Hub probes in the sync test are optional.
