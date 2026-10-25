# Configuration samples (entry point)

**Português (Brasil):** [README.pt_BR.md](README.pt_BR.md)

**Canonical files live in the repository under `deploy/samples/`** (tracked YAML and CSV you can copy). This page exists so readers who start from **`docs/`** still find the same story in one place.

| What you need | Where to go |
| ------------- | ----------- |
| **Full starter** (two folders + one database + rate limit + ML/DL terms; commented optional blocks + **built-in extension catalogue**; for evaluators and operators alike) | [`deploy/samples/config.starter-lgpd-eval.yaml`](../deploy/samples/config.starter-lgpd-eval.yaml) |
| **Minimal Docker / container** (`targets: []`, `/data` paths) | [`deploy/config.example.yaml`](../deploy/config.example.yaml) |
| **Spreadsheet → YAML targets** (scope import) | [`deploy/scope_import.example.csv`](../deploy/scope_import.example.csv) + [ops/SCOPE_IMPORT_QUICKSTART.md](../ops/SCOPE_IMPORT_QUICKSTART.md) |
| **Why `config/config.json` still exists** | [`config/README.md`](../config/README.md) (legacy JSON layout only) |

**Do not** commit a real `config.yaml` from production (paths and secrets). Root **`.gitignore`** excludes common local names; see [CONTRIBUTING.md](../../CONTRIBUTING.md).
