# Scope import quickstart (spreadsheet or memory)

**Português (Brasil):** [SCOPE_IMPORT_QUICKSTART.pt_BR.md](SCOPE_IMPORT_QUICKSTART.pt_BR.md)

Use this when you have **no** GLPI / CMDB export yet — only a workshop list, email thread, or “what we remember.” The machine-readable path is still **CSV → YAML fragment**; see [USAGE.md](../USAGE.md#scope-import-from-csv-config-fragment) for columns and types.

## In one sentence

The scope importer turns a **simple spreadsheet** (saved as UTF-8 CSV) into a **YAML list of `targets`** that you **paste** into a real config file — usually after copying **[`deploy/samples/config.starter-lgpd-eval.yaml`](../../deploy/samples/config.starter-lgpd-eval.yaml)** and replacing or merging the `targets:` block.

## Handoff checklist (non-technical author → IT operator)

| Step | Done when |
| ---- | --------- |
| Header row | Matches **[`deploy/scope_import.example.csv`](../../deploy/scope_import.example.csv)** exactly (column names unchanged). |
| Passwords | **No** real passwords in cells — only **`pass_from_env`** / **`user_from_env`** *names*; IT sets those variables on the server. |
| Encoding | File is **CSV UTF-8** (comma-separated); avoid mojibake for Portuguese accents. |
| Fragment | `scope_import_csv.py` output is **reviewed** and merged into `config.yaml` (not committed if it contains real paths). |
| Run | Operator runs `python main.py --config …` (or API) with env vars set. |

## If you are validating the product (not running IT yourself)

**Goal:** Produce a **list of places** where personal data might live (folders, databases, shares) so specialists can run the scanner. You do **not** need to understand YAML.

1. Use the steps in **Non-technical path** below to build the CSV.
1. Hand the CSV and this page to the person who runs Data Boar; they execute `scope_import_csv.py` and merge the fragment into a config starting from **[deploy/samples/config.starter-lgpd-eval.yaml](../../deploy/samples/config.starter-lgpd-eval.yaml)** (see [docs/samples/README.md](../samples/README.md)).
1. **Success looks like:** a reviewed `targets.yaml` fragment plus a real `config.yaml` with **lab paths** and **passwords in environment variables**, not in the spreadsheet.

## Non-technical path (Excel / LibreOffice)

This path is for **counsel, DPOs, or programme leads** who have a **list of systems** (from a workshop or memory) but not a CMDB export. You only build a **table**; IT runs one command to turn it into YAML.

1. Open a new spreadsheet.
1. Copy the **header row** from [`deploy/scope_import.example.csv`](../../deploy/scope_import.example.csv) (the line that starts with `type,`). **Do not change the header spelling** — the script matches these column names.
1. Add **one row per data source** (folder, database, or share). One row = one place the organisation stores files or tables that might contain personal data.
1. In **`type`**, use only values the product supports in the importer today (examples: `filesystem` for a folder path, `postgresql` or `mysql` for SQL, `smb` / `nfs` for shares). If unsure, put `filesystem` for “a folder we need to scan” and fill **`path`** with the path IT will confirm.
1. **`name`** is a free label (e.g. “HR shared drive”) so people can recognise the row in reviews — it is not a technical hostname.
1. **Never** type real passwords in the sheet. Put the **name of an environment variable** in **`pass_from_env`** (e.g. `DATA_BOAR_HR_DB_PASSWORD`) and ask IT to set that variable on the server before running scans. The name must start with `DATA_BOAR_`, `REST_API_`, or `API_`, and the finished YAML needs `allowed_hosts` listing that row’s host.
1. **Save As** → **CSV UTF-8** (comma-separated). If the tool offers only “CSV (comma delimited)”, use **Excel UTF-8** or **LibreOffice** with UTF-8 so Portuguese accents do not break.
1. Give the CSV file to the person who runs Data Boar (or run yourself if you have the repo):
   `uv run python scripts/scope_import_csv.py path/to/your.csv -o targets.fragment.yaml`
1. Open **`targets.fragment.yaml`**. It is a **fragment** — paste the `targets:` list into a full config file. Starting from **[deploy/samples/config.starter-lgpd-eval.yaml](../../deploy/samples/config.starter-lgpd-eval.yaml)** is easier than writing YAML from scratch; replace the sample `targets:` block with your merged list if needed.
1. IT sets environment variables for every **`pass_from_env`** / **`user_from_env`** name you used, then runs the app with `--config` pointing at the final `config.yaml`.

## Privacy

Treat the CSV like **internal infrastructure inventory** (permissions, no public repos). Same discipline as [SECURITY.md](../../SECURITY.md) for config.

## Later: GLPI or other exports

Vendor-specific columns will map to the same canonical schema in a future adapter; the workflow stays **export → CSV-shaped cleanup → `scope_import_csv.py`**.
