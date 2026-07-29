# Lab smoke stack (PostgreSQL + MariaDB + MSSQL + Oracle XE + Redis + optional MongoDB)

Docker Compose bundle for **LAN-only** multi-host Data Boar tests. See **[docs/ops/LAB_SMOKE_MULTI_HOST.md](../../docs/ops/LAB_SMOKE_MULTI_HOST.md)** for host order, firewall, and checklist.

**MongoDB:** not included in the default `docker compose up -d`; add **`docker compose -f docker-compose.yml -f docker-compose.mongo.yml up -d`** (or only `docker-compose.mongo.yml` if you need Mongo alone). Data Boar needs **`uv sync --extra nosql`** for `driver: mongodb` and **`driver: redis`**.

**Quick start:**

```bash
cd deploy/lab-smoke-stack
cp env.example .env
docker compose up -d
```

**Optional MongoDB (local `driver: mongodb` smoke):**

```bash
docker compose -f docker-compose.mongo.yml up -d
```

**Config example for Data Boar:** `config.lab-smoke.example.yaml` (copy elsewhere, set hub host IP, mount `tests/data/compressed` and `tests/data/homelab_synthetic` as documented). External/public API + DB eval: **`docs/ops/LAB_EXTERNAL_CONNECTIVITY_EVAL.md`**.

**SQL seeds:** `init/postgres/` and `init/mariadb/` load via each image’s `/docker-entrypoint-initdb.d` hook. **`init/mssql/`** and **`init/oracle/`** load via one-shot **`lab-mssql-init`** and **`lab-oracle-init`** (same pattern as **`lab-redis-init`**) — the official MSSQL image has no auto-init mount, and gvenzl Oracle hooks run as SYS on the CDB root instead of `XEPDB1`. Scripts: `init/mssql/apply_lab_smoke.sh`, `init/oracle/apply_lab_smoke_pdb.sh`. Corpus: `01_*` base tables, `02_*` linkage + minor-adjacent + shared-phone rows, `03_*` **#1332** INTEGER false-positive repro (`lab_fp_numeric_ids`).

### Expected detector signal — `lab_fp_numeric_ids` ([#1332](https://github.com/DataBoar/data-boar/issues/1332) / [#1371](https://github.com/DataBoar/data-boar/issues/1371))

| Table / scope | `sample_limit` | `CREDIT_CARD` column findings (today → after #1332 fix) |
| --- | --- | --- |
| `lab_fp_numeric_ids` (`id`, `ref_a`, `ref_b`, `ref_c`) | **≥ 4** | **4 → 0** (one per INT column; joined sample crosses value boundaries) |
| `lab_fp_numeric_ids` (`ctrl_3digit`, `ctrl_5digit`) | ≥ 4 | **0 → 0** (negative control — 3- and 5-digit values must not match card regex) |
| `lab_fp_numeric_ids` (`id`, …) | **1** | **0 → 0** (too few distinct values to close the four-group pattern) |

Same semantics on **PostgreSQL, MariaDB, MSSQL, and Oracle** (`init/*/03_lab_fp_numeric_ids.sql`). Rest of the SQL corpus (`01_*`, `02_*`) must keep detecting **LGPD_CPF**, **EMAIL**, **PHONE_BR**, and **DOB_POSSIBLE_MINOR** — guarded by `tests/test_lab_smoke_fp_numeric_ids.py`.

**Mongo seed:** `init/mongodb/01_lab_smoke_seed.js` (database `lab_smoke_mongo`).

**Redis seed:** `init/redis/01_lab_smoke_seed.sh` — loaded by one-shot service **`lab-redis-init`** after **`lab-redis`** is healthy (opaque string keys, hash/list/set fixtures, talkative-key control, audit/migration negative controls). Designed to **expose [#1348](https://github.com/DataBoar/data-boar/issues/1348)**: today `redis_connector.py` uses `GET` only; PII in hash fields should **not** appear until the connector is fixed — that is the expected baseline, not a seed bug.

**Engines and default published ports:**

| Service | Image | Port (host) | Data Boar `driver` |
| --- | --- | --- | --- |
| `lab-postgres` | `postgres:16-alpine` | 55432 | `postgresql+psycopg2` |
| `lab-mariadb` | `mariadb:11` | 33306 | `mysql+pymysql` |
| `lab-mssql` | `mcr.microsoft.com/mssql/server:2022-latest` | 14333 | `mssql+pymssql` (extras: `sql-all` or `mssql`) |
| `lab-oracle` | `gvenzl/oracle-xe:21-slim` | 15211 | `oracle+oracledb` (extras: `sql-all` or `oracle`) |
| `lab-redis` | `redis:7-alpine` | 56379 | `redis` (extras: `nosql`) |

**Init permissions:** If `init/*` dirs are not world-readable after SCP/rsync, run `chmod -R a+rX init/postgres init/mariadb init/mssql init/oracle init/redis` on the hub, or use **`ops/automation/ansible/playbooks/lab-smoke-stack-init-perms.yml`**. Maestro **`stage_lab_db_init`** stages SQL dirs to `/tmp` with `a+rX` before `podman run` — same pattern for new engines.

---

## Podman (optional — e.g. rootless experiments on LAB-NODE-01)

The same Compose files work with **Podman** on Debian/LMDE when the `podman` and `compose`/`podman-compose` stack is installed. This repo’s **Ansible baseline for LAB-NODE-01 still defaults to Docker CE** (`playbooks/lab-node-01-baseline.yml`); Podman is **opt-in** (`lab-node-01_install_podman: true`) and can **coexist** with Docker — you do **not** need to uninstall Docker to try Podman.

**Typical flow (hub host shell):**

```bash
cd deploy/lab-smoke-stack
cp env.example .env
# Podman 4+ (Debian bookworm/trixie backports or upstream):
podman compose up -d
podman compose -f docker-compose.mongo.yml up -d
```

**Rootless Podman:** published ports must reach LAN clients; if binds fail, check [Podman networking docs](https://docs.podman.io/en/latest/markdown/podman-compose.1.html) and firewall. Prefer the same **hub LAN IP** in Data Boar config as with Docker.

**Kubernetes (k3s):** `lab-node-01-baseline.yml` can install k3s (`lab-node-01_install_k3s: true`), but this stack is maintained as **Compose** for simplicity. Converting to Helm/manifests is a separate exercise — not required for Data Boar lab smoke.

**If `docker` service is stopped on LAB-NODE-01:** start it with `sudo systemctl start docker` (interactive sudo) before expecting `docker compose` to work; Podman does not replace `systemd` unit `docker` unless you deliberately migrate — document that choice in operator notes, not in tracked inventory.
