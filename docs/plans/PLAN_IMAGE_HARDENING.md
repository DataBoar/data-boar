# Plan: Release image hardening (distroless runtime, grype gate, VEX)

<!-- plans-hub-summary: Endurecer imagem de release — runtime distroless Debian 13 (nonroot, sem shell) via multi-stage; gate grype --fail-on high --only-fixed; VEX por-CVE justificado. Reduz ruído de CVE de base (High+ sem fix) para imagem GA-clean p/ parceiros. -->

**Status:** In progress — **PR-A** ready for review (distroless base-swap + smoke/TLS/.so verified locally); **PR-B** VEX pending.
**Date:** 2026-06-27
**Authors:** Fabio Leitao (operator); draft RO vault + execução Cursor
**Priority:** H1
**GitHub:** [#1028](https://github.com/FabioLeitao/data-boar/issues/1028) `[P2][build][security]`
**Related:** [#856](https://github.com/FabioLeitao/data-boar/issues/856) (integrity/trust) · [PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md](PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md) · [ADR-0074](../adr/ADR-0074-supply-chain-layer1-digest-pins-and-rust-sca.md) (digest pins) · release machinery [#75](https://github.com/FabioLeitao/data-boar/issues/75)

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)

---

## Problem

GA release image scan (**grype**, release-ritual v2, **1.7.4**, 2026-06-26) reported **~10 Critical + ~25 High** — **zero** with an available fix. Noise comes from **`python:3.13-slim`** (Debian 13) base packages (`perl-base`, `libc6`, `libmariadb3`, `ncurses`, `util-linux`, …). None is application code; none is actionable under `--only-fixed`. The product ships to partners (weAi/Futurex) as a **compliance/security** tool — base Criticals hurt optics even when not exploitable in our threat model.

**Evidence (operator-local):** grype log from release-ritual **1.7.4** scan (2026-06-26); path stays on the operator workstation — see issue [#1028](https://github.com/FabioLeitao/data-boar/issues/1028).

| Severity | Total (approx.) | With fix (`FIXED IN`) |
| -------- | ---------------: | --------------------- |
| Critical | ~10 | **0** (won't fix / no fix) |
| High | ~25 | **0** |
| Medium (actionable) | 2 | Python `CVE-2025-15366/15367` → fix only in **3.15.0a6** (alpha — inactionable) |

---

## Decision (operator-approved: distroless family)

### Runtime base

Google Distroless (Debian 13), not Ubuntu Chiseled.

| Candidate | Verdict | Rationale |
| --------- | ------- | --------- |
| **`gcr.io/distroless/cc-debian13:nonroot`** + bundled CPython **3.13** from builder | **Chosen** | glibc matches `python:3.13-slim` (Debian 13 / trixie); **exact** Python minor for CI (3.12–3.14); nonroot **uid 65532**; no shell/apt in final layer. |
| `gcr.io/distroless/python3-debian13` | **Not chosen alone** | Ships **Debian's** Python (may lag **3.13**); app requires `requires-python >=3.12` and CI exercises **3.13** — version skew risk. |
| `gcr.io/distroless/cc-debian12:nonroot` | **Rejected** | **glibc / OS mismatch** with `python:3.13-slim` builder (Debian **13**). |
| Ubuntu **chiseled** `ubuntu/python` | **Rejected** | Operator blessed **distroless**; chiseled Python slices less battle-tested for **Python + Rust PyO3 + native DB wheels** (mariadb/odbc/pq). |
| `python:*-alpine` (musl) | **Rejected** | mariadb/odbc wheel compatibility unvalidated (issue #1028 note). |

**Distroless “python3” intent:** Operator approved the **distroless** line (minimal, nonroot, no shell). Implementation uses **`cc-debian13:nonroot`** as the empty glibc runtime and **copies** the interpreter + `site-packages` built on **`python:3.13-slim`** — the standard pattern when the app needs a **specific** CPython minor not guaranteed by `distroless/python3-*`.

---

## Approach (three-stage multi-stage)

```
builder (python:3.13-slim + toolchain)
    → runtime-assembler (slim + runtime .deb only + collect-runtime-rootfs.sh)
    → runtime (gcr.io/distroless/cc-debian13:nonroot)
```

| Stage | Contents | Shipped? |
| ----- | -------- | -------- |
| **builder** | `gcc`, `*-dev`, `pip install -r requirements.txt`, `pip install -e .` (no `-e` in export); optional **maturin** for `boar_fast_filter` | No |
| **runtime-assembler** | `libpq5`, `libffi8`, `unixodbc`, `libmariadb3`; copy `/usr/local`; **strip pip/wheel/setuptools**; run [`scripts/docker/collect-runtime-rootfs.sh`](../../scripts/docker/collect-runtime-rootfs.sh) → `/rootfs` | No |
| **runtime** | `COPY --from=runtime-assembler /rootfs /`; app tree; **USER 65532:65532**; **exec-form** `CMD` | Yes |

### Invariants

- No `build-essential`, `apt`, `pip`, or shell in the final image.
- **Nonroot:** distroless `:nonroot` (**uid/gid 65532**) — fixes Podman build warning `appuser uid 1000 > SYS_UID_MAX 999` from the legacy `useradd -u 1000` pattern.
- **Gate:** `grype IMG --fail-on high --only-fixed` must pass (actionable High/Critical only).
- **VEX:** `.grype.yaml` (PR-B) documents won't-fix / not-applicable base CVEs with **per-CVE or per-class** rationale — audit posture, not blind suppression.

---

## Gaps (issue + original prompt did not close — this plan owns them)

Reconciliation against branch `feat/image-hardening-1028` (2026-06-27):

| Gap | Requirement | Status | PR | Notes |
| --- | ----------- | ------ | -- | ----- |
| **Python-version match** | Distroless runtime must run the same CPython minor CI uses (**3.13** primary; support **3.12–3.14** band in docs) | ✅ PR-A | **A** | Bundled `/usr/local` from `python:3.13-slim` builder; smoke verifies `_package_version()` and imports. |
| **PyO3 `.so` + glibc** | `boar_fast_filter` built in **builder** against **glibc** compatible with runtime; `.so` copied via `site-packages` | ✅ PR-A | **A** | `maturin build --release` in builder; `docker-image-smoke.sh` imports `boar_fast_filter`. |
| **CA certs / OpenSSL / TLS** | HTTPS connectors need `ca-certificates` + `libssl`/`libcrypto` in rootfs | ✅ PR-A | **A** | `collect-runtime-rootfs.sh` + TLS probe (`httpx` → `https://example.com`). |
| **`tzdata`** | Correct local time in logs/reports when connector uses TZ | ⬜ Deferred | **A** | Container defaults UTC; operator may set `-e TZ=...` — document in PR-B or DOCKER_SETUP if needed. |
| **No-shell entrypoint** | `CMD`/`ENTRYPOINT` exec form; healthchecks must not assume `sh -c` | ✅ PR-A | **A** | `CMD ["/usr/local/bin/python3.13", ...]` |
| **Smoke `_package_version()`** | `podman run --rm IMG python -c '...'` | ✅ PR-A | **A** | `scripts/docker/docker-image-smoke.sh` + `python`/`python3.13` symlinks for wrapper compat. |
| **`build-push-podman.sh` compat** | Steps 3–4: smoke + `grype --fail-on high --only-fixed` | ✅ PR-A | **B** | Verified locally on `data_boar:hardening-test`; `.grype.yaml` formalizes won't-fix in PR-B. |

---

## Fatiamento (thin PRs)

### PR-A — Base-swap (multi-stage + distroless + nonroot + smoke + TLS)

**Branch:** `feat/image-hardening-1028` (or follow-up from it).

| # | To-do | Status |
| - | ----- | ------ |
| A.1 | Dockerfile: builder → runtime-assembler → `cc-debian13:nonroot` (digest-pinned) | ✅ |
| A.2 | `scripts/docker/collect-runtime-rootfs.sh` — `/usr/local`, DB libs, CA bundle, `ldd` closure | ✅ |
| A.3 | Strip pip/wheel/setuptools from runtime export | ✅ |
| A.4 | `maturin` / `boar_fast_filter` in builder | ✅ |
| A.5 | Local: `podman build` + smoke `_package_version()` + octet-leak grep (wrapper contract) | ✅ |
| A.6 | TLS probe smoke (`httpx` → `https://example.com`) | ✅ |
| A.7 | `tests/test_docker_image_hardening.py` + `test_github_workflows` digest guard (3 stages) | ✅ |
| A.8 | Update [scripts/docker/README.md](../../scripts/docker/README.md) — smoke + collect scripts | ✅ |

**Pause after PR-A opens** — Claude Code audits diff before merge.

### PR-B — VEX + grype gate in repo

| # | To-do | Status |
| - | ----- | ------ |
| B.1 | `.grype.yaml` — ignore rules with **per-CVE or per-package-class** `reason:` (won't-fix base noise); review on each base digest bump | ⬜ |
| B.2 | `scripts/grype-image-gate.sh` + `scripts/grype-image-gate.ps1` (mirror `docker-scout-critical-gate.ps1` contract: `--fail-on high --only-fixed`) | ⬜ |
| B.3 | Document gate in [DOCKER_IMAGE_RELEASE_ORDER.md](../ops/DOCKER_IMAGE_RELEASE_ORDER.md) + `.cursor/rules/release-publish-sequencing.mdc` pointer (formalize wrapper behaviour) | ⬜ |
| B.4 | Attach post-change grype log excerpt as release evidence (operator-local log or CI artifact when wired) | ⬜ |

**Closes #1028** when **A + B** merge and operator release smoke is green.

---

## Acceptance criteria (issue + operator prompt)

- [ ] Image on **distroless `cc-debian13:nonroot`**, **nonroot**, smoke `_package_version()` OK, TLS connectors smoke OK.
- [ ] `grype IMG --fail-on high --only-fixed` green (with `.grype.yaml` documented in PR-B).
- [ ] `check-all` local + CI green.
- [ ] PR(s) `Closes #1028`.
- [ ] Compatible with operator-local `build-push-podman.sh` (smoke + grype + octet guard).

---

## Operator release wrapper (contract — do not break)

Local pipeline (`build-push-podman.sh`):

1. `git pull` on `main`
2. `podman build -t docker.io/fabioleitao/data_boar:$VERSION .`
3. Smoke: `_package_version()` contains `$VERSION`, **no** `$VERSION.<octet>` leak
4. `grype $IMG --fail-on high --only-fixed`
5. Tag `latest` + push

Repo changes must not require wrapper edits unless we add optional `grype --config .grype.yaml` (PR-B gate script documents both).

---

## Risk / rollback

| Risk | Mitigation |
| ---- | ---------- |
| Missing `.so` at runtime (odbc/mariadb/pq) | `collect-runtime-rootfs.sh` + PR-A smoke; rollback = revert Dockerfile to `python:3.13-slim` runtime stage |
| No shell for debug | Use **`gcr.io/distroless/cc-debian13:debug-nonroot`** only for troubleshooting — **never** publish `:latest` from debug variant |
| grype noise returns after digest bump | Re-run scan; update `.grype.yaml` only with justified rows; never weaken `--only-fixed` gate |
| `boar_fast_filter` build lengthens CI image job | Builder-only cost; optional feature — Python path remains fallback |

---

## Current implementation snapshot (branch)

Files touched before PLAN graduation:

- [`Dockerfile`](../../Dockerfile) — 3-stage; `cc-debian13:nonroot@sha256:7f2a0e5b50575d355720a9d7ca9c871124780eb6a1dc0dbd70a67d5fd11629d2`
- [`scripts/docker/collect-runtime-rootfs.sh`](../../scripts/docker/collect-runtime-rootfs.sh) — rootfs bundler for distroless

**Not yet in branch:** `.grype.yaml`, grype gate scripts, maturin in builder, automated smoke test, docs sync.

---

## Provenance

- **Vault draft:** `obsidian-vault/_inbox/PLAN_IMAGE_HARDENING.draft.md` (Claude Code RO, 2026-06-27) — graduated into this file; remove inbox copy after merge.
- **Cursor exec:** multi-stage design, Debian 13 distroless choice, collect script (2026-06-27).
