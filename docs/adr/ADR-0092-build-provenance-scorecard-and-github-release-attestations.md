# ADR 0092 — Build provenance: OpenSSF Scorecard + GitHub Release attestations (not PyPI badges)

- **Date (UTC):** 2026-09-22
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Status

Accepted

### Status history

- 2026-09-22 — Proposed — records the operator decision for [#1844](https://github.com/DataBoar/data-boar/issues/1844) (Scorecard + native GitHub attestation on the SBOM/release path; no PyPI provenance badge).
- 2026-09-22 — Accepted — after merge of PR [#1963](https://github.com/DataBoar/data-boar/pull/1963) (operator audit; issue #1844 remains open until explicit close).

## Context

GitHub [#1844](https://github.com/DataBoar/data-boar/issues/1844) asked for an honest supply-chain posture: either OpenSSF Scorecard (repo hygiene badge) or SLSA-style build attestations (artifact-bound), or both. The issue body predates current CI: today the repo already runs Scorecard ([#886](https://github.com/DataBoar/data-boar/issues/886) / `.github/workflows/scorecard.yml`) and generates signed GitHub build provenance on tagged releases via `actions/attest-build-provenance` in `.github/workflows/sbom.yml` ([#1891](https://github.com/DataBoar/data-boar/issues/1891), [ADR 0003](ADR-0003-sbom-roadmap-cyclonedx-then-syft.md)).

Live evidence ([#1844](https://github.com/DataBoar/data-boar/issues/1844) comments, [`docs/ops/PYPI_PEP740_ATTESTATION_EVIDENCE.md`](../ops/PYPI_PEP740_ATTESTATION_EVIDENCE.md)) shows that **PyPI / TestPyPI JSON `urls[].provenance` remains `null`** even when `pypa/gh-action-pypi-publish` logs Sigstore attestation upload during CI. There is **no** dynamic third-party badge for “SLSA level” comparable to Scorecard. Claiming PyPI-side provenance in the README would be misleading.

Docker Hub images for `fabioleitao/data_boar` are published through **operator-run scripts** on the primary dev workstation ([`docs/ops/DOCKER_IMAGE_RELEASE_ORDER.md`](../ops/DOCKER_IMAGE_RELEASE_ORDER.md)), not a dedicated in-repo workflow; image digest attestation in CI is **out of scope** for this decision.

## Decision

1. **OpenSSF Scorecard (route A)** — Keep `.github/workflows/scorecard.yml` with SHA-pinned `ossf/scorecard-action` and SARIF upload via `github/codeql-action/upload-sarif`. Keep the dynamic README badge (`api.scorecard.dev` → Scorecard viewer). Posture: **report-only** (does not gate merges).
2. **GitHub Release build attestations (route B, GitHub-native)** — Keep `actions/attest-build-provenance` on the **tag/release SBOM workflow** (`sbom.yml`), attaching `data-boar.intoto.jsonl` and related release assets. Public evidence is the GitHub Release **“Verified” / attestations** UI and release assets—not a PyPI project badge.
3. **PyPI** — Continue Trusted Publishing and optional attestation generation in `publish-pypi.yml` where the action supports it, but **do not** add README/SECURITY badges or marketing copy that imply Warehouse-exposed PEP 740 provenance until `urls[].provenance` is populated on a release the operator accepts as canonical.
4. **Docker Hub** — Document as **manual publish** without in-repo SLSA attest for image digests; SBOM for the built image remains the Syft phase of `sbom.yml` when that workflow runs for a tag. Future CI publish for Hub would be a separate issue/ADR.
5. **Closure of #1844** — Record this ADR plus [`docs/ops/BUILD_PROVENANCE_POSTURE.md`](../ops/BUILD_PROVENANCE_POSTURE.md) as the operator-facing map; do not re-open the “zero attest in repo” premise from the original issue text.

## Consequences

- README badges: CI, CodeQL, SBOM workflow, Scorecard, Docker Hub version, GitHub Release—**no** PyPI provenance shield.
- Investigators and procurement should use Scorecard + GitHub Release attestations + SBOM artifacts; PyPI evidence doc stays for regression checks.
- [#1950](https://github.com/DataBoar/data-boar/issues/1950) (SBOM wrapper contract, ADR 0003 amendment, `emit_provenance` local vs signed) remains **separate** from #1844 closure.

## References

- [#1844](https://github.com/DataBoar/data-boar/issues/1844) · [#886](https://github.com/DataBoar/data-boar/issues/886) · [#1891](https://github.com/DataBoar/data-boar/issues/1891)
- [ADR 0003](ADR-0003-sbom-roadmap-cyclonedx-then-syft.md) · [ADR 0005](ADR-0005-ci-github-actions-supply-chain-pins.md)
- [`docs/ops/BUILD_PROVENANCE_POSTURE.md`](../ops/BUILD_PROVENANCE_POSTURE.md) · [`docs/ops/PYPI_PEP740_ATTESTATION_EVIDENCE.md`](../ops/PYPI_PEP740_ATTESTATION_EVIDENCE.md)
