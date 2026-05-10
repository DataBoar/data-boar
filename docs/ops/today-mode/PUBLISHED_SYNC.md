# Published release vs repo version (anti-stale)

**Português (Brasil):** [PUBLISHED_SYNC.pt_BR.md](PUBLISHED_SYNC.pt_BR.md)

**Purpose:** After you cut a **Git tag**, **GitHub Release**, or **Docker Hub** push, dated “today mode” files and **PLANS** tables can still say “operator pending” elsewhere. This page is the **short reconciliation record**: refresh it when reality changes.

---

## Last verified (operator or agent)

| Field | Value |
| ----- | ----- |
| **Verified** | **2026-05-10** |
| **`pyproject.toml` on `main`** | **1.7.4-rc** (working **pre-release**; **published** stable = **1.7.3** / tag **`v1.7.3`** per [VERSIONING.md](../VERSIONING.md)) |
| **GitHub Release Latest** | [**v1.7.3**](https://github.com/FabioLeitao/data-boar/releases/tag/v1.7.3) (notes: **`docs/releases/1.7.3.md`**, **`CHANGELOG.md`**) |
| **Docker Hub** | **`fabioleitao/data_boar:1.7.3`** + **`latest`** (same digest) — `sha256:510a51b0dc89e79d084b515b5201c803328040dbda594744c96ee245efcc4866`; **Full description** from **[`docs/ops/DOCKER_HUB_REPOSITORY_DESCRIPTION.md`](../DOCKER_HUB_REPOSITORY_DESCRIPTION.md)** |
| **Next public version** (when `main` has a new bundle) | **1.7.4** — follow **`docs/VERSIONING.md`** + **`docs/releases/`** |

---

## How to re-check (copy/paste)

From repo root (needs **`gh`** auth + network):

```bash
git fetch origin --tags
git tag -l "v1.7.*" --sort=-version:refname | head -5
grep -n '^version' pyproject.toml
gh release list --repo FabioLeitao/data-boar --limit 5
```

Docker Hub: confirm **`1.7.3`** and **`latest`** on [hub.docker.com/r/fabioleitao/data_boar/tags](https://hub.docker.com/r/fabioleitao/data_boar/tags) or the Registry API; **Full description** matches **[`docs/ops/DOCKER_HUB_REPOSITORY_DESCRIPTION.md`](../DOCKER_HUB_REPOSITORY_DESCRIPTION.md)**. **GitHub:** **`v1.7.3`** Release exists.

---

## When to update this file

- **Immediately after** tag + GitHub Release + Docker push for a new version.
- **Optionally** on a slow week: confirm row still true so carryover tables do not resurrect **done** work.
- **Always** align **`docs/plans/PLANS_TODO.md`** release bullets if they still say “in-repo / operator pending” for the same number.

Automation note: **`tests/test_about_version_matches_pyproject.py`** guards **`pyproject.toml`** ↔ runtime/man `.TH`; it does **not** query GitHub or Hub — human or agent verification stays here.
