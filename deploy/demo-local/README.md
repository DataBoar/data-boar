# Local demo harness (`deploy/demo-local/`, #1447)

Runs the same light scenario as the public demo on one machine (plan B and
rehearsal), all on loopback, synthetic data only. Rootless Podman, Linux host
only (no PowerShell twin, see `docs/ops/SCRIPTS_CROSS_PLATFORM_PAIRING.md`).

```bash
deploy/demo-local/up.sh --mode container   # or --mode native; prints time + URL
deploy/demo-local/rehearsal.sh [--fresh]   # scan each target, measure, print a table
deploy/demo-local/down.sh                  # remove containers + every ephemeral file
```

## What comes up

| Target | Container (pinned, see `images.env`) | Memory | Seed |
| ------ | ------------------------------------ | -----: | ---- |
| `Lab_Postgres` + `Supabase_Simulated` | `postgres:17-alpine` (DBs `lab`, `supa_sim`) | 128 MiB | `lab-smoke-stack/init/postgres/*.sql`; `seed_supa_sim.py` (60 synthetic rows) |
| `Demo_SMB_Compressed` | samba-server (same digest as `deploy/demo/quadlet/samba.container`) | 96 MiB | corpus `10_compressed_smb/` (`protegido_demo.7z`, `cadastro.zip`, `.tgz`, `.tar.bz2`) |
| `Lab_Redis` | `redis:7.4.12-alpine` | 48 MiB | `lab-smoke-stack/init/redis/01_lab_smoke_seed.sh` |
| `Lab_Mongo` | `mongo:7.0.48` (WiredTiger cache 0.25 GB) | 256 MiB | `lab-smoke-stack/init/mongodb/01_lab_smoke_seed.js` |
| `WebDAV_Demo`, `REST_Demo` (optional, `--no-web` skips) | one `httpd:2.4-alpine` with `mod_dav` | 48 MiB | `seed_web.py` |
| Data Boar | `docker.io/fabioleitao/data_boar:1.8.0` + `/extras`, or `uv run python main.py --web` | 700 MiB | - |

Every container: `--memory`, `--cap-drop all`, `no-new-privileges`, published on
`127.0.0.1` only. `Supabase_Simulated` is a **local** PostgreSQL 17 database; it
does not reproduce the ~20 ms pooler latency of the real service.

Passwords are random, created at `up.sh`, kept in `$STATE/secrets.env` (mode 600,
outside the repo) and never printed. State lives in `$DEMO_LOCAL_STATE`
(default `~/.local/state/databoar-demo-local`); `down.sh` removes it.
Ports and paths can be overridden with `DEMO_LOCAL_*_PORT`, `DEMO_LOCAL_STATE`,
`DEMO_LOCAL_EXTRAS_DIR`.

## Container mode needs the `/extras` overlay

The 1.8.0 image is free-threaded CPython 3.14 without pip and without the
`nosql`, `shares` and `compressed` extras. `build-extras.sh` builds them
(`extras.txt`, versions from `uv.lock`) as cp314t wheels with `uv pip install
--target`, drops what the image already ships (the overlay comes first on
`PYTHONPATH`) and refuses any non-cp314t or abi3 module. `up.sh` runs it with
`--ensure` (cached in `~/.cache/databoar-demo-local/extras`).

The image also predates `0f9e931f` (SMB port passed to `walk/scandir/open_file`),
so it dials port 445 whatever the target says. While that holds, container mode
mounts the repo's `connectors/smb_connector.py` read-only over the image file.
`DEMO_LOCAL_NO_SMB_PATCH=1` runs the unpatched image (SMB then fails).

## Rehearsal

`rehearsal.sh` restarts Boar once per target (and once per archive variant:
7z with password, 7z without, 7z wrong password, zip, tgz, tar.bz2), POSTs
`/scan` with `{}`, samples memory every 2 s (`podman stats`, plus the cgroup
`memory.peak`; native Boar = RSS of its process tree) and checks the findings
against what the corpus and seeds were designed to contain. The output is a
markdown table plus the cut rule: target containers (Boar excluded) must stay
within ~300 MB of peak, the budget of the 1.6 GB VPS; what does not fit is
marked `CORTAR`. The table goes to `$STATE/rehearsal-table.md`, not the repo.

Archives are configured under `file_scan` (`scan_compressed`,
`compressed_extensions`, `file_passwords`): the engine copies the **global**
`file_scan` into every target, so these keys are not per target.

## Known product limits found while building this

- **SMB + `.tar.bz2` (and `.tar.gz`, `.tar.xz`):** the SMB connector stages the
  file with only the last suffix, so the tar inside is not read and nothing is
  reported (silent false negative). `.zip`, `.tgz` and `.7z` work.
- **SMB failures name the temp file** (`tmpXXXX.7z`), not the archive.
- **Wrong 7z password** is reported as `archive_read_error`, not `wrong_password`
  (py7zr 1.1.4 fails in LZMA before the CRC check).
- **WebDAV:** with `webdavclient3` 3.14.7 the connector lists nothing (the info
  dict has `size` and `name=None`, the connector reads `content_length`); the scan
  ends clean with zero findings and no failure.

## Adding the real Supabase target (outside the repo)

Create `~/.config/databoar-demo/supabase.target.yaml` (one target, or `targets:`
list). `up.sh` and the rehearsal merge it when the file exists. Use
`pass_from_env`, never a literal password, and export the variable in the shell
that runs the scripts:

```yaml
name: Supabase_Real
type: database
driver: postgresql+psycopg2
host: aws-0-REGION.pooler.supabase.com   # your pooler host
port: 5432
user: postgres.PROJECT_REF
pass_from_env: DATA_BOAR_SUPABASE_PASS
database: postgres
allowed_hosts: ["aws-0-REGION.pooler.supabase.com"]
```

```bash
export DATA_BOAR_SUPABASE_PASS=...            # from your password manager
export DEMO_LOCAL_EXTRA_ALLOWED_HOSTS=aws-0-REGION.pooler.supabase.com
deploy/demo-local/up.sh --mode container
```

The image enforces the credential-destination allowlist (#1977):
`DEMO_LOCAL_EXTRA_ALLOWED_HOSTS` extends `DATA_BOAR_CREDENTIAL_ALLOWED_HOSTS`
(default `127.0.0.1`). A remote host also needs `allow_private_networks` only if
it resolves to a private address.

## Loopback and the SSRF guard

Connectors refuse loopback unless the target sets `allow_private_networks: true`
(`connectors/url_guard.py`); every target here sets it, which is meant for this
harness and not for production. The image also needs `allowed_hosts:
["127.0.0.1"]` per credentialed target and the operator allowlist above.
