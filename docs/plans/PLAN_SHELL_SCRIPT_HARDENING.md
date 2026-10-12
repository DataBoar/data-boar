# Plan: Shell script hardening (shellcheck + selective bats)

<!-- plans-hub-summary: Tracked `.sh` inventory, error-level shellcheck in check-all, and hermetic bats for pure-parse helpers (#1926 part 2). -->

**Status:** In progress
**Date:** 2026-10-11
**Authors:** Fabio Leitao
**Priority:** P3
**GitHub:** [#1926](https://github.com/DataBoar/data-boar/issues/1926)

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)

## Goal

Harden tracked Bash scripts without turning every lab wrapper into CI noise: enforce **shellcheck severity=error** in both `check-all` twins (#1926 part 1, already on `main`), document a **concrete per-file verdict**, and add a **small hermetic bats** slice wired as an **optional** local step (skip with a visible warning when `bats` is missing). **No bats job in CI.**

## Bats qualification criterion

A script **qualifies for bats** when it has **real branching, argument parsing, or subprocess orchestration** that can be exercised **hermetically** (tmp dirs only, no network, no `sudo`, no Docker). Scripts that only wrap long lab/ansible/docker flows are inventoried but **deferred**. Library `.sh` files meant to be **sourced** qualify when pure functions can be tested without side effects.

| Bats verdict | Meaning |
| ------------ | ------- |
| **yes** | Hermetic bats added under `tests/bats/` |
| **pester** | Covered by `tests/pester/` (bash invoked from PowerShell) |
| **defer** | Qualifies logically but needs lab/network/privilege |
| **no** | Thin wrapper or meta gate; shellcheck only |
| **n/a** | Example/template under `docs/private.example/` |

## Tracked `.sh` inventory (73 files)

Evaluated on branch `epic/boar-ga-hygiene-3` via `git ls-files '*.sh'`. **Logic** = branching/argument parsing/orchestration worth hardening review.

| Path | Logic | Bats | Notes |
| ---- | ----- | ---- | ----- |
| `audit.sh` | no | no | Tees into check-all wrapper |
| `deploy/compat-matrix-config-ref/run-across-corners.sh` | yes | defer | Docker/matrix orchestration |
| `deploy/compat-matrix-config-ref/run-config-matrix.sh` | yes | defer | Config matrix + containers |
| `deploy/lab-smoke-stack/init/mssql/apply_lab_smoke.sh` | yes | defer | DB init against lab stack |
| `deploy/lab-smoke-stack/init/oracle/apply_lab_smoke_pdb.sh` | yes | defer | Oracle lab init |
| `deploy/lab-smoke-stack/init/redis/01_lab_smoke_seed.sh` | yes | defer | Redis seed for lab smoke |
| `docs/private.example/homelab/lab-op-vc-container-rsync.example.sh` | n/a | n/a | Operator example only |
| `docs/private.example/scripts/session-b-git-filter-repo.example.sh` | n/a | n/a | Destructive example only |
| `prep_audit.sh` | no | no | Invokes audit/check-all path |
| `scripts/ansible-syntax-check.sh` | yes | defer | Ansible + subprocess |
| `scripts/check-all-security-scans.sh` | yes | defer | Security scan orchestration |
| `scripts/check-all.sh` | yes | no | Meta publish gate (self-test avoided) |
| `scripts/check-cross-platform-gaps.sh` | yes | **yes** | Arg mirror of `.ps1` → Python |
| `scripts/check-hubs.sh` | no | no | Thin doc-hub check wrapper |
| `scripts/check-sbom.sh` | yes | defer | External SBOM tooling |
| `scripts/ci-install-gitleaks-pinned.sh` | yes | defer | CI download/install |
| `scripts/ci_dependabot_requirements_sync.sh` | no | no | Single Python entry |
| `scripts/databoar-env-load.sh` | yes | defer | Env file sourcing for lab |
| `scripts/db-tool-bootstrap.sh` | yes | defer | DB client bootstrap |
| `scripts/demo.sh` | yes | **yes** | `--help` / case flags (headless path needs `uv`) |
| `scripts/docker/apply_wheelhouse_v1.sh` | yes | defer | Docker build context |
| `scripts/docker/build-nogil-local.sh` | yes | defer | Local Docker build |
| `scripts/docker/collect-runtime-rootfs.sh` | yes | defer | Docker inspection |
| `scripts/docker/compare-gil-nogil-demo-timing.sh` | yes | defer | Docker timing compare |
| `scripts/docker/docker-image-smoke.sh` | yes | defer | Image smoke |
| `scripts/dump-context.sh` | no | no | Context dump helper |
| `scripts/emit-provenance.sh` | yes | defer | Provenance emit tooling |
| `scripts/export_public_gemini_bundle.sh` | yes | defer | Bundle export orchestration |
| `scripts/gate-trailer-attest.sh` | yes | defer | Signing / git attest |
| `scripts/generate-sbom.sh` | yes | defer | SBOM generation |
| `scripts/grype-image-gate.sh` | yes | defer | Grype image scan |
| `scripts/homelab-host-report.sh` | yes | defer | SSH/collect lab report |
| `scripts/lab-allow-data-boar-inbound.sh` | yes | defer | Firewall/lab network |
| `scripts/lab-completao-container-smoke-original.sh` | yes | defer | Container completão smoke |
| `scripts/lab-completao-container-smoke.sh` | yes | defer | Container completão smoke |
| `scripts/lab-completao-container-smoke2.sh` | yes | defer | Container completão smoke |
| `scripts/lab-completao-host-smoke.sh` | yes | defer | Host completão smoke |
| `scripts/lab-node-01-ansible-labop-podman-apply.sh` | yes | defer | Ansible + podman |
| `scripts/lab-node-01-ansible-preflight.sh` | yes | defer | Ansible preflight |
| `scripts/labop-dep-doctor.sh` | yes | defer | Multi-branch lab doctor |
| `scripts/labop-firewall-lib.sh` | yes | defer | Firewall backends + sudo |
| `scripts/labop-fw-guard-ensure.sh` | yes | defer | Privileged ensure |
| `scripts/labop-gate-readiness.sh` | yes | defer | Gate readiness + SSH |
| `scripts/labop-nfs-server-ensure.sh` | yes | defer | NFS ensure + sudo |
| `scripts/labop-rfc1918-cidr-lib.sh` | yes | **yes** | Sourced pure CIDR matcher |
| `scripts/labop-share-client-install.sh` | yes | defer | Client install orchestration |
| `scripts/labop-smb-server-ensure.sh` | yes | defer | SMB ensure + sudo |
| `scripts/labop-sudoers-load-order-lib.sh` | yes | **pester** | `tests/pester/SudoersLoadOrder.Tests.ps1` |
| `scripts/lint-only.sh` | no | no | pre-commit wrapper |
| `scripts/native-nfpm-populate-staging.sh` | yes | defer | nfpm staging |
| `scripts/pre-commit-and-tests.sh` | no | no | check-all inner wrapper |
| `scripts/primary-linux-agent-sessions.sh` | yes | defer | Session orchestration |
| `scripts/private-git-sync.sh` | yes | defer | Nested git + remotes |
| `scripts/pypi-publish.sh` | yes | defer | Publish orchestration |
| `scripts/quick-test.sh` | yes | no | pytest wrapper |
| `scripts/run-gitleaks-strict.sh` | no | no | gitleaks wrapper |
| `scripts/run-homelab-host-report.sh` | yes | defer | SSH report wrapper |
| `scripts/run-osv-scanner.sh` | no | no | osv-scanner wrapper |
| `scripts/snmp-lab-ifwalk.sh` | yes | defer | SNMP lab walk |
| `scripts/*-bitwarden-cli-bootstrap.sh` | yes | defer | Host bootstrap (Bitwarden CLI) |
| `scripts/*-docker-remove-live-restore-and-restart.sh` | yes | defer | Docker daemon change |
| `scripts/*-fix-docker-list.sh` | yes | defer | Docker list fix |
| `scripts/*-install-veracrypt-console-debian13.sh` | yes | defer | VeraCrypt install |
| `scripts/*-session-warm.sh` | yes | defer | Session warm orchestration |
| `scripts/*-veracrypt-mount-private-repo.sh` | yes | defer | VeraCrypt mount |
| `scripts/tool-pins.sh` | no | no | Pin echo helper |
| `scripts/void-xbps-podman-validate.sh` | yes | defer | Void/podman validate |
| `scripts/wheelhouse/build_glibc_incontainer.sh` | yes | defer | In-container wheel build |
| `scripts/wheelhouse/build_musl_incontainer.sh` | yes | defer | In-container wheel build |
| `scripts/wheelhouse/run_cell.sh` | yes | defer | Wheelhouse cell runner |
| `scripts/wheelhouse/verify_connector_c_checksum.sh` | yes | defer | Checksum verify |
| `scripts/wheelhouse/verify_release_sha256sums.sh` | no | no | sha256sum verify |
| `scripts/workflow-security-lint.sh` | yes | defer | zizmor workflow lint |

**Bats slice (this phase):** 3 files, 11 tests — `check_cross_platform_gaps.bats`, `demo_help.bats`, `labop_rfc1918_cidr.bats`.

## Phases

| Step | Status |
| ---- | ------ |
| shellcheck `--severity=error` on all tracked `*.sh` in `check-all.sh` / `.ps1` | ✅ Done (on `main`) |
| Per-file inventory + plan doc (this file) | ✅ Done |
| Hermetic `tests/bats/` + optional `check-all` step | ✅ Done |
| Expand bats for `labop-sudoers-load-order-lib` on Linux (duplicate pester) | ⬜ Pending |
| Additional defer-row coverage via fixture labs | ⬜ Pending |

## Out of scope

- CI workflow job for bats (operator policy: local optional only).
- Replacing Maestro/lab completão bash with bats integration tests.
