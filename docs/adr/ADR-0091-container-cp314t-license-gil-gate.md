# ADR 0091 — One published container image (cp314t); GIL restored by license at ENTRYPOINT

- **Date (UTC):** 2026-08-29
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Status

Proposed

### Status history

- 2026-08-29 — Proposed ([#1409](https://github.com/DataBoar/data-boar/issues/1409) operator decision comment; born Proposed per ADR-0045 T1).

## Context

A free-threaded (no-GIL) image existed locally (`Dockerfile.nogil`, ~1.25 GB unpruned) while Hub `:latest` stayed GIL-on (~309 MB). Publishing a second tag would double extras holes and invent a suffix that dies when `:latest` moves. Issue text once argued that gating **runtime** by tier would break the **additive** licensing invariant ([ADR 0064](ADR-0064-license-enforcement-additive-model.md)). The operator **consciously diverged**: free-threading was never a low-tier capability, so requiring Enterprise for no-GIL does not remove a capability that Community already had.

Distroless has **no shell**, so `PYTHON_GIL` cannot be set in `entrypoint.sh`. `PYTHON_GIL` is applied only at **process start** — a probe interpreter must `os.execve` a child. `is_feature_available` is **OPEN-bypass** and must not be used. `PYTHON_GIL=0` is forbidden (unsafe C extensions).

## Decision

1. **One image.** Hub `:latest` is built from **`Dockerfile`**: uv-installed CPython **3.14 free-threaded** (`python3.14t` / **cp314t**). **`Dockerfile.nogil`** is an alias of the same stages. No parallel GIL-on tag for the same semver.
2. **Paid-tier via license, not a second binary.** Container `ENTRYPOINT` is `python3.14t -m core.licensing.gil_container_gate`. It uses `get_runtime_tier_for_features` (same as the app) then `execve`s with **`PYTHON_GIL=1`** unless the tier is **exactly `Tier.ENTERPRISE`**. OPEN, Community, Std, Pro, Pro+, and **Partner** get the GIL. Lab no-GIL: `licensing.mode: open` and `licensing.effective_tier: enterprise`.
3. **Binary contract stays in the build.** SQLAlchemy is pure-Python (`DISABLE_SQLALCHEMY_CEXT=1`); the builder `assert` (zero sqlalchemy `*.so` and `sys._is_gil_enabled() is False`) is a **release gate**, probed with `--entrypoint /usr/local/bin/python3.14t` so the license gate does not mask it.
4. **Size.** Publish via `collect-runtime-rootfs.sh` + distroless (same path as the previous ~309 MB Hub image). Do not ship the unpruned 1.25 GB local tree. Explain any remaining compressed-size delta at publish time.
5. **CPU floor.** cp314t wheels need **x86-64-v2+**. That is an accepted break vs the old `popcnt=0` GIL image.

## Consequences

- Default `docker run` (OPEN / no JWT) runs **with** the GIL even though the bits are free-threaded.
- HEALTHCHECK does not use the license ENTRYPOINT.
- Additive invariant: we do not strip a Community capability that existed; we withhold a new Enterprise differentiator.
- Native packages (nfpm) remain a separate channel ([ADR 0084](ADR-0084-native-package-embedded-cpython-by-channel.md)); this ADR is the **container** story.

## References

- [#1409](https://github.com/DataBoar/data-boar/issues/1409) · [#551](https://github.com/DataBoar/data-boar/issues/551) · [#1398](https://github.com/DataBoar/data-boar/issues/1398)
- `core/licensing/gil_container_gate.py` · `docs/DOCKER_SETUP.md` · `docs/ops/DOCKER_IMAGE_RELEASE_ORDER.md`
