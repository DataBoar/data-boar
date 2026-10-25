# Postura de proveniência de build e evidência de supply chain (público)

**English:** [BUILD_PROVENANCE_POSTURE.md](BUILD_PROVENANCE_POSTURE.md)

**Registro de decisão:** [ADR 0092](../adr/ADR-0092-build-provenance-scorecard-and-github-release-attestations.md) — encerra a [#1844](https://github.com/DataBoar/data-boar/issues/1844).

Este arquivo é o **mapa honesto** do que o repositório publica hoje. Não substitui [SECURITY.pt_BR.md](../../SECURITY.pt_BR.md) (vulnerabilidades) nem a mecânica de SBOM do [ADR 0003](../adr/ADR-0003-sbom-roadmap-cyclonedx-then-syft.md).

## O que expomos publicamente

| Superfície | Mecanismo | Badge no README? | Notas |
| ---------- | --------- | ---------------- | ----- |
| **Higiene de supply chain do repo** | [`.github/workflows/scorecard.yml`](../../.github/workflows/scorecard.yml) — `ossf/scorecard-action` (SHA fixo), SARIF → Code Scanning | **Sim** — OpenSSF Scorecard | Semanal + push em `main`; só relatório |
| **SBOM + assets de release** | [`.github/workflows/sbom.yml`](../../.github/workflows/sbom.yml) | **Sim** — workflow SBOM | Tags de versão + gatilhos em PR |
| **Proveniência assinada (estilo SLSA)** | Job em `sbom.yml` — `actions/attest-build-provenance` → `data-boar.intoto.jsonl` em **GitHub Releases** | **Sem badge SLSA separado** — UI “Verified” / atestação na [página de Releases](https://github.com/DataBoar/data-boar/releases) | Não espelhado como badge no PyPI |
| **PyPI (wheel/sdist)** | [`.github/workflows/publish-pypi.yml`](../../.github/workflows/publish-pypi.yml) | **Sem badge de proveniência** | JSON `urls[].provenance` ainda **null** — [PYPI_PEP740_ATTESTATION_EVIDENCE.pt_BR.md](PYPI_PEP740_ATTESTATION_EVIDENCE.pt_BR.md) |
| **Imagem Docker Hub** | Scripts do operador — [DOCKER_IMAGE_RELEASE_ORDER.md](DOCKER_IMAGE_RELEASE_ORDER.md) | **Sim** — versão no Hub | **Sem** publish por CI no repo; **sem** atestação de digest no CI |

## Critérios de aceite da #1844 (fechamento)

| Critério | Status |
| -------- | ------ |
| Decisão de rota registrada | **Feito** — ADR 0092 |
| Workflow(s) implementado(s) e CI verde | **Feito** — Scorecard + `sbom.yml` (atestação em tag) |
| Badge(s) no README | **Feito** — Scorecard, SBOM e demais shields existentes |
| Processo Docker Hub mapeado | **Feito** — ritual manual no runbook; sem atestação CI no Hub |

## O que **não** afirmamos

- Badge de “proveniência verificada” ou nível SLSA no **PyPI** no README.
- Proveniência automática para **cada** tag Docker Hub (publish fora do `sbom.yml` hoje).
- Que a nota do Scorecard seja equivalente a um nível SLSA de build.

## Trabalho relacionado (fora da #1844)

- [#1950](https://github.com/DataBoar/data-boar/issues/1950) — contrato de wrappers SBOM, emenda ADR 0003, `emit_provenance` local vs CI assinado.
- [#989](https://github.com/DataBoar/data-boar/issues/989) — contenção L3/L4 do host executor.
