# ADR 0003 — SBOM roadmap — CycloneDX (JSON) first, then Syft on Docker images

- **Status:** Accepted
- **Date (UTC):** 2026-03-26
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

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

## References

- [docs/COMPLIANCE_FRAMEWORKS.md](../COMPLIANCE_FRAMEWORKS.md) — ISO 31000 framing vs SBOM role
- [docs/QUALITY_WORKFLOW_RECOMMENDATIONS.md](../QUALITY_WORKFLOW_RECOMMENDATIONS.md) — SBOM section
- [SECURITY.md](../../SECURITY.md) — dependency and reporting context
- [docs/RELEASE_INTEGRITY.md](../RELEASE_INTEGRITY.md) — release integrity posture
