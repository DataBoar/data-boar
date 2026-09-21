# Evidência de atestação PEP 740 no PyPI / TestPyPI

**English:** [PYPI_PEP740_ATTESTATION_EVIDENCE.md](PYPI_PEP740_ATTESTATION_EVIDENCE.md)

Capturado em **2026-09-21** (relógio da estação Linux primária) para a issue **#1844**. Este arquivo registra resultados **HTTP ao vivo**. **Não** adiciona badge no README, **não** fecha a issue e **não** altera `publish-pypi.yml`.

## O que foi medido

| Índice | Versão | JSON `urls[].provenance` | HTML `verified` / `provenance` / `attestation` / `sigstore` |
| ------ | ------ | ------------------------ | ----------------------------------------------------------- |
| `https://pypi.org/pypi/data-boar/1.7.4.post12/json` | `1.7.4.post12` | **`None`** no wheel e no `.tar.gz` | **zero** ocorrências em `GET https://pypi.org/project/data-boar/1.7.4.post12/` |
| `https://test.pypi.org/pypi/data-boar/1.7.4.post12/json` | `1.7.4.post12` | **`None`** nos dois arquivos | **zero** ocorrências em `GET https://test.pypi.org/project/data-boar/1.7.4.post12/` |

JSON do projeto no PyPI de produção: último **`1.7.4.post12`**. Os caminhos `.../1.8.0b0/json` e `.../1.8.0-beta/json` retornaram **HTTP 404**.

## Fatos relacionados (não é um publish)

- `publish-pypi.yml` já usa `pypa/gh-action-pypi-publish` **v1.14.2** (SHA pinado) com **OIDC** e upload legado no TestPyPI. Os comentários da **#1844** já registraram geração Sigstore no run `30503437031` para `1.7.4.post12` em produção.
- O [PR #15952](https://github.com/pypi/warehouse/pull/15952) do Warehouse está **`closed`**, **`updated_at` `2024-07-11T18:55:59Z`**. O suporte a atestação na API legado **é anterior** a esta release do Data Boar. **Isso não explica** `provenance: None` nos **dois** índices nesta captura.
- Esta sessão **não** disparou `gh workflow run publish-pypi.yml`. Depois do próximo publish **intencional** no TestPyPI, conferir de novo o campo JSON `urls[].provenance`.

## O que isto não autoriza

- Badges de atestação no README / SECURITY
- `actions/attest-build-provenance` no job de publish PyPI (SLSA de Release continua no workflow **SBOM**; ADR 0003)
- `Closes #1844`
