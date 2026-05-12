# ADR 0031 — PyPI packaging with Hatchling (flat layout)

## Status

Accepted

## Context

- Distribution id **`data-boar`** ([ADR 0014](ADR-0014-rename-repo-and-package-python3-lgpd-crawler-to-data-boar.md)) requires a **publishable** sdist/wheel.
- Default setuptools discovery fails on this repo (**many** top-level directories with Python modules).
- CI already uses **`uv`**; **`uv build`** / **`uv publish`** integrate cleanly.

## Decision

- Use **[hatchling](https://github.com/pypa/hatch)** as **`[build-system]`** backend.
- Declare **explicit** `[tool.hatch.build.targets.wheel] packages = [...]` for application packages plus **`force-include`** for **`main.py`** at repo root.
- Add **`[project.scripts]`** → **`data-boar = "main:main"`** for `pip install` UX.
- Maintainer publish: **`scripts/pypi-publish.ps1`** (wraps **`uv build`** + **`uv publish`** with **`UV_PUBLISH_TOKEN`**).

## Consequences

- **`uv.lock`** records the project as **`editable`** workspace source (normal for `uv sync` on this tree).
- **`requirements.txt`** remains **uv-exported** for Docker/CI — unchanged intent ([ADR 0030](ADR-0030-python-dependency-update-closure-single-pass.md)).
- First PyPI upload still needs a **PyPI API token** in the environment (never committed).
