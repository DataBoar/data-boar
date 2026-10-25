# Sample configuration files

**Portuguese (Brazil):** [README.pt_BR.md](README.pt_BR.md)

These files are **tracked** in Git so new users (counsel, DPOs, auditors, or IT) can start from a **complete, sane-default** layout without copying fragments from many docs. The **same navigation** from **`docs/`** lives at **[docs/samples/README.md](../../docs/samples/README.md)** ([pt-BR](../../docs/samples/README.pt_BR.md)).

| File | Purpose |
| ---- | ------- |
| **[config.starter-lgpd-eval.yaml](config.starter-lgpd-eval.yaml)** | **Recommended starting point** for counsel, DPOs, auditors, or IT on a first on-prem or lab run: two fictional filesystem folders, one PostgreSQL-style target (password via env), timeouts, rate limiting, minimal ML/DL terms, plus **commented blocks** for optional features (compressed archives, `file_passwords`, `learned_patterns`, external pattern files, `detection.cnpj_alphanumeric`, `connector_format_id_hint`, API key, jurisdiction hints). **Comment catalogue** lists built-in file suffix groups (text, office, structured data, optional rich media, archives) aligned with `connectors/filesystem_connector.py`. Replace paths and set the env var for `pass_from_env`. |
| **[../config.example.yaml](../config.example.yaml)** | **Minimal** Docker-oriented template (`targets: []`, `/data` paths). Use when you only need the smallest valid file. |
| **[../scope_import.example.csv](../scope_import.example.csv)** | Canonical CSV header for **`scripts/scope_import_csv.py`** when building targets from a spreadsheet. |

**Do not** commit your real `config.yaml` (it may contain LAN paths and secrets). Root **`.gitignore`** excludes typical local names; see [CONTRIBUTING.md](../../CONTRIBUTING.md).

**YAML vs JSON:** New projects should use **YAML**. A legacy JSON shape (`databases` + `file_scan.directories`) is still accepted — see **[../../config/README.md](../../config/README.md)**.
