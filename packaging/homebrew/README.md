# Homebrew tap source (macOS, #1425)

**Issue:** [#1425](https://github.com/DataBoar/data-boar/issues/1425).

Published tap: **[DataBoar/homebrew-databoar](https://github.com/DataBoar/homebrew-databoar)** (`brew tap DataBoar/databoar`). This is an **own tap**, not [homebrew-core](https://github.com/Homebrew/homebrew-core).

Operator runbook: [docs/ops/HOMEBREW_TAP.md](../../docs/ops/HOMEBREW_TAP.md) ([pt-BR](../../docs/ops/HOMEBREW_TAP.pt_BR.md)).

## What this directory is

| Artifact | Role |
| -------- | ---- |
| [`Formula/data-boar.rb`](Formula/data-boar.rb) | Canonical formula (copied to the tap repo on bump) |

The formula **depends on Homebrew `python@3.13`** and `pip install`s the **PyPI sdist** into a prefix venv. It does **not** embed CPython (that is the Linux nfpm / Void xbps Enterprise channel, ADR-0084).

Connector extras (`sql-community`, `nosql`, …) stay out of the formula; install them into the formula venv after `brew install` (see caveats).

## Maintainer bump

After each **PyPI** publish (including `postN` that has no Git tag):

```bash
uv run python scripts/homebrew_formula_bump.py --write
uv run python scripts/homebrew_formula_bump.py --check --latest
```

CI workflow [`.github/workflows/homebrew-tap.yml`](../../.github/workflows/homebrew-tap.yml) runs `brew audit --strict --new` plus `brew test` on **macos-14** (Apple Silicon). Intel macOS is the same bottle-less pip path; GitHub no longer gates a separate Intel runner here.

**Out of scope:** arm64 Linux (#1403), xbps (#1404), MSI/winget (#1467).
