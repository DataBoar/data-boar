# Build provenance and supply-chain evidence (public posture)

**Português (Brasil):** [BUILD_PROVENANCE_POSTURE.pt_BR.md](BUILD_PROVENANCE_POSTURE.pt_BR.md)

**Decision record:** [ADR 0092](../adr/ADR-0092-build-provenance-scorecard-and-github-release-attestations.md) — closes GitHub [#1844](https://github.com/DataBoar/data-boar/issues/1844).

This page is the **honest map** of what the repository actually publishes today. It does not replace [SECURITY.md](../../SECURITY.md) vulnerability reporting or [ADR 0003](../adr/ADR-0003-sbom-roadmap-cyclonedx-then-syft.md) SBOM mechanics.

## What we expose publicly

| Surface | Mechanism | README badge? | Notes |
| ------- | --------- | ------------- | ----- |
| **Repo supply-chain hygiene** | [`.github/workflows/scorecard.yml`](../../.github/workflows/scorecard.yml) — `ossf/scorecard-action` (SHA-pinned), SARIF → Code Scanning, `publish_results: true` | **Yes** — OpenSSF Scorecard | Weekly + `main` push; advisory only |
| **SBOM + release assets** | [`.github/workflows/sbom.yml`](../../.github/workflows/sbom.yml) — CycloneDX + Syft; workflow badge | **Yes** — SBOM workflow | PR/path triggers + version tags |
| **Signed build provenance (SLSA-style)** | Same `sbom.yml` job — `actions/attest-build-provenance` → `data-boar.intoto.jsonl` on **GitHub Releases** for version tags | **No separate SLSA badge** — use [GitHub Releases](https://github.com/DataBoar/data-boar/releases) “Verified” / attestation UI | Not mirrored as a PyPI project badge |
| **PyPI wheels/sdist** | [`.github/workflows/publish-pypi.yml`](../../.github/workflows/publish-pypi.yml) — Trusted Publishing + action attestation logs | **No provenance badge** | Warehouse `urls[].provenance` still **null** in live JSON — see [PYPI_PEP740_ATTESTATION_EVIDENCE.md](PYPI_PEP740_ATTESTATION_EVIDENCE.md) |
| **Docker Hub image** | Operator scripts — [DOCKER_IMAGE_RELEASE_ORDER.md](DOCKER_IMAGE_RELEASE_ORDER.md) | **Yes** — Docker Hub version shield | **No in-repo CI publish**; **no** digest attestation workflow in this repo |

## Issue #1844 acceptance criteria (closure)

| Criterion | Status |
| --------- | ------ |
| Route decision recorded (ADR or issue) | **Done** — [ADR 0092](../adr/ADR-0092-build-provenance-scorecard-and-github-release-attestations.md) |
| Workflow(s) implemented and CI green | **Done** — Scorecard runs on `main` (e.g. workflow `scorecard.yml`); SBOM + attest on tag path in `sbom.yml` |
| Badge(s) in README | **Done** — Scorecard + SBOM + existing CI/CodeQL/Docker/Release shields ([`tests/test_readme_status_badges.py`](../../tests/test_readme_status_badges.py)) |
| Docker Hub publish process mapped | **Done** — manual operator ritual in [DOCKER_IMAGE_RELEASE_ORDER.md](DOCKER_IMAGE_RELEASE_ORDER.md); no CI attest for Hub digests |

## What we do **not** claim

- A **PyPI** “verified provenance” or SLSA level badge on the README.
- **Automatic** provenance for every Docker Hub tag (publish is outside `sbom.yml` today).
- That OpenSSF Scorecard score equals a SLSA build level — Scorecard includes SLSA-related *checks* among many others.

## Related work (not #1844)

- [#1950](https://github.com/DataBoar/data-boar/issues/1950) — SBOM wrapper contract, ADR 0003 amendment, local `emit_provenance` vs CI-signed attestation.
- [#989](https://github.com/DataBoar/data-boar/issues/989) — executor-host / L3–L4 containment (separate from build provenance badges).

## Verification hints (operators)

```bash
# Last Scorecard runs
gh run list --repo DataBoar/data-boar --workflow=scorecard.yml --limit 3

# PyPI JSON (expect provenance null until Warehouse exposes it)
curl -sS 'https://test.pypi.org/pypi/data-boar/json' | jq '.urls[].provenance' | head
```

After a **stable** GitHub Release tag, open the release page and confirm attestation / SBOM assets attached by the SBOM workflow.
