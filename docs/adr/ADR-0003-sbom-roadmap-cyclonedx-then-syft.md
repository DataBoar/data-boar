# ADR 0003 — SBOM roadmap — CycloneDX (JSON) first, then Syft on Docker images

- **Status:** Accepted
- **Date (UTC):** 2026-03-26
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao
- **2026-09-21:** Amended — GitHub [#1950](https://github.com/DataBoar/data-boar/issues/1950) names the implemented wrappers, canonical artifact filenames, check-sbom invariants, and emit-provenance failure semantics. Phase A/B (CycloneDX then Syft) is unchanged; there is no third SBOM.

## Context

A **Software Bill of Materials (SBOM)** is primarily for **software supply-chain** visibility and **incident response** (e.g. mapping advisories and CVEs to what shipped in a given release or image). It can also satisfy **procurement** questionnaires; it is **not** organizational risk management under **ISO 31000**—see [COMPLIANCE_FRAMEWORKS.md](../COMPLIANCE_FRAMEWORKS.md#iso-31000-framing). The project already runs **`pip-audit`** in CI for known vulnerabilities; a **formal** SBOM adds a portable inventory alongside that signal.

Two common outputs matter for this codebase:

1. **Python application** — resolved dependencies (best source: **`uv.lock`** / environment export).
1. **Published Docker image** — OS + Python layers include packages not visible from the lockfile alone.

## Decision

1. **Phase A (next):** Generate **CycloneDX JSON** with a **recent spec version** (e.g. 1.5+) from the **application** dependency set, attached as a **release artifact** or CI artifact on tagged releases. Prefer tooling that reads **`uv.lock`** or an **`uv export`** snapshot for fidelity.
1. **Phase B (soon after):** Add **Syft** (or equivalent) against the **published** **`fabioleitao/data_boar`** image (or internal tag) so the **image** SBOM complements the Python SBOM.
1. Document the **where to download** and **which tag** the SBOM belongs to in **[SECURITY.md](../../SECURITY.md)** and/or **[docs/RELEASE_INTEGRITY.md](../RELEASE_INTEGRITY.md)** when automation lands; keep secrets and internal registry URLs out of tracked docs.

## Consequences

- **Positive:** Faster **supply-chain** and **IR** answers (“what shipped in 1.x.y?” / “what is in this image tag?”); clearer responses on **dependency** inventory for security reviews.
- **Negative:** CI/release script maintenance; must regenerate when lockfile or base image changes.

## Implementation (2026-03)

- **Workflow:** [`.github/workflows/sbom.yml`](../../.github/workflows/sbom.yml) — **CycloneDX 1.6 JSON** from `uv export` + `cyclonedx-py` (`sbom-python.cdx.json`); **Syft** `v1.28.0` image against `docker:data_boar:sbom` built from [`Dockerfile`](../../Dockerfile) (`sbom-docker-image.cdx.json`). Triggers: tags `v*`, `release: published`, path-filtered PRs to `main`, `workflow_dispatch`. Artifacts upload on every run; **GitHub Release** attachment when a release already exists for the tag.
- **Local:** [`scripts/generate-sbom.ps1`](../../scripts/generate-sbom.ps1) (requires Docker for the Syft step).
- **Docs:** [SECURITY.md](../../SECURITY.md), [RELEASE_INTEGRITY.md](../RELEASE_INTEGRITY.md) — where to download and what each file contains.
- **Dev dependency:** `cyclonedx-bom` in [`pyproject.toml`](../../pyproject.toml) `[dependency-groups].dev` (same tooling as CI).

### POC / procurement evidence (2026-04)

The **same two CycloneDX JSON files** are the usual answer when a POC or enterprise security review asks for an **SBOM**: they inventory **Python dependencies** (lockfile-aligned) and the **built container image** layers. No second format or tool was chosen—**reviewers are pointed to [SECURITY.md](../../SECURITY.md) (SBOM section) and to the workflow run or GitHub Release for the **tag under evaluation**. Operational checklist for handing artifacts to a partner lives in **gitignored** `docs/private/plans/POC_SBOM_ENTREGA.pt_BR.md` (operator copy-me). This is an **evidence packaging** note, not a change to the Phase A/B decision above.

## Amendment (2026-09-21) — wrapper contract (#1950)

This amendment **names** the wrappers and failure semantics already implemented on this tree (`9392cba9` Cargo.lock merge, `2013932f` emit-provenance, `8644873f` SECURITY/hub naming). It does **not** change Phase A/B or invent a third inventory.

### Canonical artifacts (exactly two)

| Canonical path | What it inventories | How it is produced |
| -------------- | ------------------- | ------------------ |
| [`sbom/sbom-application.cdx.json`](../../sbom/) | Resolved **application** graph: Python from `uv export` + `cyclonedx-py`, **plus** the resolved crate graph from [`rust/boar_fast_filter/Cargo.lock`](../../rust/boar_fast_filter/Cargo.lock) | [`scripts/application_sbom.py`](../../scripts/application_sbom.py) `merge --canonical` |
| [`sbom/sbom-runtime.cdx.json`](../../sbom/) | **Runtime / image** surface (what was packaged), via **Syft** | Copy of `sbom-docker-image.cdx.json` after `anchore/syft:v1.28.0` on `docker:data_boar:sbom` |

Working copies used by CI and the generate wrappers (same bytes, not a third source of truth):

- Application: `sbom-python.cdx.json` (then copied to `sbom/sbom-application.cdx.json`).
- Runtime: `sbom-docker-image.cdx.json` (then copied to `sbom/sbom-runtime.cdx.json`).

Both views are generated from repository/build inputs. Do not hand-edit either JSON.

### Wrapper commands (this repository)

| Role | Commands (real paths) |
| ---- | --------------------- |
| **generate-sbom** | [`scripts/generate-sbom.sh`](../../scripts/generate-sbom.sh) and [`scripts/generate-sbom.ps1`](../../scripts/generate-sbom.ps1) — `uv export` → `cyclonedx-py` → `application_sbom.py merge` → Docker build → Syft → copies under `sbom/` → emit-provenance |
| **check-sbom** | [`scripts/check-sbom.sh`](../../scripts/check-sbom.sh) and [`scripts/check-sbom.ps1`](../../scripts/check-sbom.ps1) — exec [`scripts/application_sbom.py`](../../scripts/application_sbom.py) `check` |
| **emit-provenance** | [`scripts/emit-provenance.sh`](../../scripts/emit-provenance.sh) and [`scripts/emit-provenance.ps1`](../../scripts/emit-provenance.ps1) — default emit+verify; implementation [`scripts/emit_provenance.py`](../../scripts/emit_provenance.py) |
| **CI / release** | [`.github/workflows/sbom.yml`](../../.github/workflows/sbom.yml) calls the same Python entrypoints (no duplicated CycloneDX merge logic). Tag/release job uses SHA-pinned `actions/attest-build-provenance` and copies the bundle to `data-boar.intoto.jsonl`. |

BFFs in other repositories adapt these names; that work is out of this tree.

### Verification invariants (`check-sbom`)

`application_sbom.py check` (via `check-sbom.*`) **fails closed** when:

1. The application file is missing, is not a JSON object, or `bomFormat` is not `CycloneDX`.
2. Any `[[package]]` from `rust/boar_fast_filter/Cargo.lock` is absent from `components` (name+version). Drift vs the lockfile is a hard fail.
3. Metadata property `data-boar:application-sbom` is not `python+rust-cargo-lock`.
4. If a runtime path is passed (or `sbom-docker-image.cdx.json` exists and the wrapper forwards it): `bomFormat` is not `CycloneDX`, or `components` is missing/empty.

`check-sbom` does **not** claim SLSA and does **not** bind commit/version by itself. Commit, version, toolchain, workflow inputs, and SBOM/artifact **digests** live in `sbom/provenance-local.json` from **emit-provenance**.

### Failure semantics (emit-provenance)

From the module docstring and `build_record` / `verify_record` in `scripts/emit_provenance.py`:

- This record is **not** signed SLSA. Field **`signed_slsa` is always `false`**. `verify` rejects any other value.
- **`signed_attestation`** is `null` when `data-boar.intoto.jsonl` is absent (normal **local** run).
- After CI copies the OIDC bundle to `data-boar.intoto.jsonl`, emit records `signed_attestation={path, sha256}` (the file digest). That is still **not** a local signature; it is a pointer to the CI attestation.
- `--require-sboms` fails if `sbom-python.cdx.json` or `sbom-docker-image.cdx.json` is missing, or if verify sees empty `sbom_digests.application` / `.runtime`.
- `--require-signed-attestation` fails unless that intoto file exists and `signed_attestation.sha256` is a 64-char hex digest. Local generate wrappers **must not** pass this flag.

Tests: `tests/test_emit_provenance.py`, `tests/test_application_sbom.py`.

## References

- [docs/COMPLIANCE_FRAMEWORKS.md](../COMPLIANCE_FRAMEWORKS.md) — ISO 31000 framing vs SBOM role
- [docs/QUALITY_WORKFLOW_RECOMMENDATIONS.md](../QUALITY_WORKFLOW_RECOMMENDATIONS.md) — SBOM section
- [SECURITY.md](../../SECURITY.md) — dependency and reporting context
- [docs/RELEASE_INTEGRITY.md](../RELEASE_INTEGRITY.md) — release integrity posture
- GitHub [#1950](https://github.com/DataBoar/data-boar/issues/1950) — canonical SBOM and provenance wrappers
