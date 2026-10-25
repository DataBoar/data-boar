# LAB-OP shorthands (taxonomy + safe wrappers)

**pt-BR:** [LAB_OP_SHORTHANDS.pt_BR.md](LAB_OP_SHORTHANDS.pt_BR.md)

## Goal

Give operators and collaborators stable “muscle memory” commands for LAB-OP workflows, without encouraging unsafe shortcuts.

## Taxonomy

- **report**: run `homelab-host-report.sh` (inventory + posture snapshot)
- **report-all**: run the report on all hosts in the private manifest
- **sync-collect**: (optional) git pull on each host clone, then report (multi-host)

## Shorthand wrapper

Use `scripts/lab-op.ps1` as the stable entry point:

```powershell
.\scripts\lab-op.ps1 -Action report -SshHost lab-op
.\scripts\lab-op.ps1 -Action report-all
.\scripts\lab-op.ps1 -Action report-all -Privileged -Deep
.\scripts\lab-op.ps1 -Action sync-collect -SkipFping
```

## Windows primary dev PC vs lab-op (file search)

- **`lab-op`** here means **Linux over SSH** (`lab-op.ps1`, host reports). Filename search on the server uses **`find`** / **`fd`**, not Voidtools.
- On the **Windows** dev PC (**L-series**), fast filename/path search uses **`.\scripts\es-find.ps1`** (**Everything** / **`es.exe`**). See **[EVERYTHING_ES_PRIMARY_WINDOWS_DEV_LAB.md](EVERYTHING_ES_PRIMARY_WINDOWS_DEV_LAB.md)** and session keyword **`es-find`**.

## Guardrails

- Privileged probes are **opt-in** (`--privileged` / `-Privileged`).
- “Deep” checks are **opt-in** (`--deep` / `-Deep`) and may increase runtime/noise.
- Do **not** add broad `NOPASSWD` rules; see [LAB_OP_PRIVILEGED_COLLECTION.md](LAB_OP_PRIVILEGED_COLLECTION.md) for the restricted sudoers pattern.

