# Published release vs repo version (anti-stale)

**Português (Brasil):** [PUBLISHED_SYNC.pt_BR.md](PUBLISHED_SYNC.pt_BR.md)

**Purpose:** After you cut a **Git tag**, **GitHub Release**, or **Docker Hub** push, dated “today mode” files and **PLANS** tables can still say “operator pending” elsewhere. This page is the **short reconciliation record**: refresh it when reality changes.

---

## Last verified (operator or agent)

| Field | Value |
| ----- | ----- |
| **Verified** | **2026-06-26** |
| **`pyproject.toml` on `main`** | **`1.7.4`** on branch **`release/1.7.4`** (PR **#1024** pending operator merge; **published** stable still **1.7.3** until post-merge **release-ritual**) |
| **GitHub Release Latest** | [**v1.7.3**](https://github.com/FabioLeitao/data-boar/releases/tag/v1.7.3) (notes: **`docs/releases/1.7.3.md`**, **`CHANGELOG.md`**) — **v1.7.4** after publish |
| **Docker Hub** | **`fabioleitao/data_boar:1.7.3`** + **`latest`** (published) — target **`1.7.4`** after operator publish |
| **Next public version** (after **1.7.4** publish) | **`1.8.0-beta`** per [VERSIONING.md](../VERSIONING.md) + ADR-0073 |

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
