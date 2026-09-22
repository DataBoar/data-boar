# PyPI / TestPyPI PEP 740 attestation evidence

**Português (Brasil):** [PYPI_PEP740_ATTESTATION_EVIDENCE.pt_BR.md](PYPI_PEP740_ATTESTATION_EVIDENCE.pt_BR.md)

Captured **2026-09-21** (primary Linux workstation clock) for GitHub issue **#1844**. This file records **live HTTP** results. It does **not** add a PyPI provenance README badge and does **not** change `publish-pypi.yml`. Closure narrative: [BUILD_PROVENANCE_POSTURE.md](BUILD_PROVENANCE_POSTURE.md) / [ADR 0092](../adr/ADR-0092-build-provenance-scorecard-and-github-release-attestations.md).

## What was measured

| Index | Version | JSON `urls[].provenance` | HTML `verified` / `provenance` / `attestation` / `sigstore` |
| ----- | ------- | ------------------------ | ----------------------------------------------------------- |
| `https://pypi.org/pypi/data-boar/1.7.4.post12/json` | `1.7.4.post12` (also `info.version` on the project JSON) | **`None`** on both `data_boar-1.7.4.post12-py3-none-any.whl` and `.tar.gz` | **zero** matches in `GET https://pypi.org/project/data-boar/1.7.4.post12/` |
| `https://test.pypi.org/pypi/data-boar/1.7.4.post12/json` | `1.7.4.post12` | **`None`** on both files | **zero** matches in `GET https://test.pypi.org/project/data-boar/1.7.4.post12/` |

Project JSON on production PyPI: latest **`1.7.4.post12`**. Paths `.../1.8.0b0/json` and `.../1.8.0-beta/json` returned **HTTP 404**.

## Related facts (not a publish)

- `publish-pypi.yml` already uses `pypa/gh-action-pypi-publish` **v1.14.2** (SHA-pinned) with **OIDC** and **`repository-url`** legacy upload for TestPyPI (`https://test.pypi.org/legacy/`). Issue **#1844** comments already recorded Sigstore generation in GitHub Actions run `30503437031` for production `1.7.4.post12`.
- Warehouse [PR #15952](https://github.com/pypi/warehouse/pull/15952) (**Add support for uploading attestations in legacy API**) is **`closed`**, **`updated_at` `2024-07-11T18:55:59Z`** (`gh api repos/pypi/warehouse/issues/15952`). Legacy-API attestation support therefore predates this Data Boar release. **That does not explain** why `provenance` is still `None` on **both** PyPI and TestPyPI for `1.7.4.post12` as of this capture.
- This session **did not** run `gh workflow run publish-pypi.yml` (would upload a new TestPyPI/PyPI artifact). Re-check after the next **intentional** TestPyPI publish: same JSON field `urls[].provenance`.

## What this does not authorize

- README / SECURITY **PyPI attestation badges** while `urls[].provenance` stays null (public posture: [BUILD_PROVENANCE_POSTURE.md](BUILD_PROVENANCE_POSTURE.md), [ADR 0092](../adr/ADR-0092-build-provenance-scorecard-and-github-release-attestations.md))
- Treating PyPI publish logs alone as proof that end users see Warehouse provenance

## Relationship to #1844

Issue [#1844](https://github.com/DataBoar/data-boar/issues/1844) closes via **ADR 0092** and the build-provenance posture doc: Scorecard + GitHub Release attestations (`sbom.yml`), not PyPI badges. This evidence file remains the regression record for PyPI JSON/HTML.
