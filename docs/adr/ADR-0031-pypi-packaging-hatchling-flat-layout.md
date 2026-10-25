# ADR 0031 — PyPI packaging with Hatchling (flat layout)

- **Status:** Accepted
- **Date (UTC):** 2026-04-19
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Context

- Distribution id **`data-boar`** ([ADR 0014](ADR-0014-rename-repo-and-package-python3-lgpd-crawler-to-data-boar.md)) requires a **publishable** sdist/wheel.
- Default setuptools discovery fails on this repo (**many** top-level directories with Python modules).
- CI already uses **`uv`**; **`uv build`** / **`uv publish`** integrate cleanly.

## Decision

- Use **[hatchling](https://github.com/pypa/hatch)** as **`[build-system]`** backend.
- Declare **explicit** `[tool.hatch.build.targets.wheel] packages = [...]` for application packages plus **`force-include`** for **`main.py`** at repo root.
- Add **`[project.scripts]`** → **`data-boar = "main:main"`** for `pip install` UX.
- Maintainer publish: **`scripts/pypi-publish.ps1`** / **`pypi-publish.sh`** dispatch **`.github/workflows/publish-pypi.yml`** (PyPI Trusted Publishing / OIDC — **no** workstation API token; superseded local **`uv publish`** + **`UV_PUBLISH_TOKEN`** per #1046).
- **Optional dependencies:** heavy or platform-specific connectors belong in **`[project.optional-dependencies]`** extras (see [PLAN_PACKAGING_EXTRAS.md](../plans/PLAN_PACKAGING_EXTRAS.md), #1047) — **core** `pip install data-boar` must not pull SQL C-extensions.

## Consequences

- **`uv.lock`** records the project as **`editable`** workspace source (normal for `uv sync` on this tree).
- **`requirements.txt`** remains **uv-exported** for Docker/CI — unchanged intent ([ADR 0030](ADR-0030-python-dependency-update-closure-single-pass.md)).
- **PyPI upload** uses **OIDC Trusted Publishing** in CI (**`publish-pypi.yml`**); operators dispatch via **`scripts/pypi-publish.*`** — not a committed API token ([ADR-0005](ADR-0005-ci-github-actions-supply-chain-pins.md) pins workflow Actions).
