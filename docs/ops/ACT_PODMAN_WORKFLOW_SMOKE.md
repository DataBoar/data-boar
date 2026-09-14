# Optional local GitHub Actions smoke with act + Podman

**Português (Brasil):** [ACT_PODMAN_WORKFLOW_SMOKE.pt_BR.md](ACT_PODMAN_WORKFLOW_SMOKE.pt_BR.md)

**Related:** [QUALITY_WORKFLOW_RECOMMENDATIONS.md](../QUALITY_WORKFLOW_RECOMMENDATIONS.md) · [TOKEN_AWARE_SCRIPTS_HUB.md](TOKEN_AWARE_SCRIPTS_HUB.md) · [SCRIPTS_CROSS_PLATFORM_PAIRING.md](SCRIPTS_CROSS_PLATFORM_PAIRING.md)

Use this when a PR changes **`.github/workflows/*.yml`** and you want to exercise a **real job** on the workstation **before** push. It is **not** a substitute for the static folded-`run:` guard (#1918) and it is **not** part of **`./scripts/check-all.sh`** / **`.\scripts\check-all.ps1`**.

## Layer 1 (always — cheap)

`uv run python scripts/workflow_run_scalar_guard.py` walks **`.github/workflows/`** and fails if a `run:` uses YAML folded style (`>` / `>-` / `>+`) **and** contains a backslash. That combination collapses `pip … --require-hashes \` + `-r file` into `Invalid requirement: '-r'` (#1904, #1906). Pre-commit hook **`workflow-run-scalar-guard`** and **`check-all`** both run it. Prefer a literal block (`|`) for shell line continuations.

## Layer 2 (manual — [nektos/act](https://github.com/nektos/act))

The Linux primary workstation may have **Podman** without a Docker daemon. `act` talks to a container engine via **`DOCKER_HOST`**.

1. Enable the user Podman socket (once per login session / linger as you prefer):

   ```bash
   systemctl --user enable --now podman.socket
   export DOCKER_HOST="unix:///run/user/$(id -u)/podman/podman.sock"
   ```

1. Install `act` via the distro or upstream docs (do not pin a host-specific package name here).

1. From the **repo root**, run one job (example — replace the workflow and job names):

   ```bash
   act pull_request -W .github/workflows/ci.yml -j ansible-syntax
   ```

`act` pulls a **GitHub-compatible runner image**. That is slower and heavier than the Python guard. Use it for a **workflow-touching PR**, not every commit.

**Do not** add `act` to pre-commit, **`check-all`**, or CI. GitHub Actions remains the merge proof for jobs that need hosted runners, secrets, or matrix OS images.
