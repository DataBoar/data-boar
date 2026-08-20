# Homebrew tap (macOS, #1425)

**Português (Brasil):** [HOMEBREW_TAP.pt_BR.md](HOMEBREW_TAP.pt_BR.md)

**Issue:** [#1425](https://github.com/DataBoar/data-boar/issues/1425) · **Plan:** `docs/plans/PLAN_NATIVE_PACKAGES.md`

This is the **macOS consumer** install path: an **own tap** ([DataBoar/homebrew-databoar](https://github.com/DataBoar/homebrew-databoar)), **not** [homebrew-core](https://github.com/Homebrew/homebrew-core). There is no Homebrew-core review queue.

The formula **depends on Homebrew `python@3.13`** and `pip install`s the published **PyPI** sdist into a prefix venv. It does **not** embed CPython (unlike Linux nfpm / Void xbps Enterprise packages). `cp314t` / no-GIL is **not** offered on this tap.

## Install

```bash
brew tap DataBoar/databoar
brew install data-boar
data-boar --version
data-boar --demo
```

`--demo` starts the dashboard on loopback with a synthetic corpus (process stays up until you stop it).

### Extras

The formula is **base only** (same idea as the nfpm core package, without shipping connector subpackages). After install:

```bash
"$(brew --prefix data-boar)/libexec/bin/pip" install "data-boar[sql-community]"
```

See formula caveats for the `opt_libexec` path Homebrew prints.

## Validation (CI, not lab metal)

GitHub Actions [`.github/workflows/homebrew-tap.yml`](../../.github/workflows/homebrew-tap.yml) runs on **macos-14** (Apple Silicon):

1. `brew audit --strict --new`
2. `brew install` from a local tap copy of `packaging/homebrew/Formula/data-boar.rb`
3. `brew test` (`--version` + `--demo` until the demo SQLite DB exists, then SIGTERM)

Intel Macs use the same bottle-less pip path. This workflow does **not** gate a separate Intel runner.

Canonical formula: [`packaging/homebrew/Formula/data-boar.rb`](../../packaging/homebrew/Formula/data-boar.rb).

## Bump on every PyPI publish

The formula **must** track the PyPI sdist (including `postN` uploads that have no Git tag). Otherwise the tap goes stale by hand.

```bash
uv run python scripts/homebrew_formula_bump.py --write
uv run python scripts/homebrew_formula_bump.py --check --latest
```

Automation:

- `publish-pypi.yml` calls this workflow after a successful **pypi** (not TestPyPI) publish
- `workflow_dispatch` with **bump** on `homebrew-tap.yml`
- non-prerelease GitHub `release: published`

Sync to the public tap repo needs repository secret **`HOMEBREW_TAP_TOKEN`** (contents:write on `DataBoar/homebrew-databoar`). Without it, the formula still bumps in this product repo via PR; the tap clone is skipped.

Pre-release git-only versions (`1.8.0-beta`) are **not** formula targets — Homebrew users get the latest **PyPI** release.

## Out of scope

arm64 Linux (#1403), xbps (#1404), MSI/winget (#1467).

See also: [USAGE.md](../USAGE.md) · [TECH_GUIDE.md](../TECH_GUIDE.md) · [QUICKSTART.md](../../QUICKSTART.md).
