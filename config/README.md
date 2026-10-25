# `config/` directory — legacy JSON illustration

**Portuguese (Brazil):** [README.pt_BR.md](README.pt_BR.md)

The file **`config.json`** in this folder exists to show the **legacy** configuration shape the loader still accepts:

- Top-level **`databases`**: list of connection objects (mapped to `type: database` targets).
- Top-level **`file_scan.directories`**: list of folder paths (each becomes a `type: filesystem` target).

**For new work, prefer YAML** — it is easier to comment, review, and merge. A **single copy-paste-friendly starter** (targets, rate limits, ML/DL terms, and **commented optional** blocks for compressed files, passwords, learned patterns, etc.) lives under **`deploy/samples/config.starter-lgpd-eval.yaml`**. From **`docs/`**, open **[docs/samples/README.md](../docs/samples/README.md)** for the same links in one place. **First-run narrative** (YAML vs JSON, table of samples): [USAGE.md](../docs/USAGE.md#configuration-file-first-run) ([pt-BR](../docs/USAGE.pt_BR.md#arquivo-de-configuração-primeira-execução)).

The minimal Docker-oriented template is **`deploy/config.example.yaml`** (`targets: []`). For SQL/Snowflake row-cap overrides without cluttering the main file, optional root keys **`sql_sampling_file`** / **`sql_sampling_files`** point at YAML fragments merged into **`sql_sampling`** (see [USAGE.md](../docs/USAGE.md) — relational sampling). Optional **`regex_overrides_files`** / **`ml_patterns_files`** / **`compliance_frameworks`** compose compliance samples the same way (later wins); sample **`recommendation_overrides`** merge into **`report.recommendation_overrides`**.

Do **not** treat **`config.json`** as production-ready: keep real credentials in environment variables (`pass_from_env`, etc.) and real paths only in files that are **not** committed (see root `.gitignore` and [CONTRIBUTING.md](../CONTRIBUTING.md)).
