# Data Boar — Guia de testes de POC

> **Público:** colaboradores que executam validações do scanner.
> **Versão:** 2026-04-10 — este arquivo espelha o **bloco SBOM**; o guia completo está em inglês: [TESTING_POC_GUIDE.md](TESTING_POC_GUIDE.md).

---

## Evidência de *supply Colleague-Nn* (SBOM) para revisores da POC / segurança

Para inventário de **cadeia de suprimentos** e **resposta a incidentes** (não substitui gestão de risco organizacional ISO 31000), o projeto publica **dois arquivos JSON CycloneDX 1.6** por execução do workflow de release:

| Arquivo | Conteúdo |
| -------- | -------- |
| `sbom-python.cdx.json` | Dependências Python alinhadas ao `uv.lock` |
| `sbom-docker-image.cdx.json` | Pacotes observados na imagem Docker construída (Syft) |

**Onde obter:** workflow do GitHub Actions **SBOM** (`.github/workflows/sbom.yml`) — artefatos na execução e anexados ao **GitHub Release** quando existir *release* para a tag. **Documentação:** [SECURITY.md](../SECURITY.md) (seção SBOM), [ADR 0003](adr/ADR-0003-sbom-roadmap-cyclonedx-then-syft.md). **Regeneração local:** `scripts/generate-sbom.ps1` (saídas no `.gitignore`).

**Português (Brasil):** [README.pt_BR.md](README.pt_BR.md) · **Guia completo (EN):** [TESTING_POC_GUIDE.md](TESTING_POC_GUIDE.md)
