# Wheelhouse recipe scripts (#1379)

**Single source of truth:** [`recipe-manifest.yaml`](recipe-manifest.yaml) — pinned package specs, gates, container images, and MariaDB Connector/C checksum. Human narrative + tables live in [`docs/plans/PLAN_WHEELHOUSE_DISTRIBUTION.md`](../../docs/plans/PLAN_WHEELHOUSE_DISTRIBUTION.md); CI must **not** duplicate pins in workflow YAML.

| Script | Role |
| ------ | ---- |
| `load_manifest.py` | Read manifest (`--export-build-env`, `--get`, `--json`) |
| `run_cell.sh` | Host driver: one `musl\|glibc` × Python cell via Docker (`--platform` from manifest) |
| `build_musl_incontainer.sh` | In-container scientific stack (port of vault `build-v1-musl.sh`) |
| `build_glibc_incontainer.sh` | In-container glibc cell (port of vault `build-v1-glibc.sh`) |
| `verify_connector_c_checksum.sh` | Fail if Connector/C tarball ≠ manifest sha256 |
| `verify_release_sha256sums.sh` | Fail if `SHA256SUMS` line count ≠ `.whl` count (`--dir` or `--repo`/`--tag`) — [#1410](https://github.com/DataBoar/data-boar/issues/1410) |

**Gates (job failure, not warnings):** `popcnt == 0`, `_multiarray_umath*.so` size `< 8_000_000`, scipy wheel has **no** `libscipy_openblas`. Remember `grep -c … \|\| true` under `set -e`.

**Local canary (≈10–25 min):**

```bash
./scripts/wheelhouse/verify_connector_c_checksum.sh
./scripts/wheelhouse/run_cell.sh musl 3.12
```

Workflow: [`.github/workflows/wheelhouse-recipe.yml`](../../.github/workflows/wheelhouse-recipe.yml).
