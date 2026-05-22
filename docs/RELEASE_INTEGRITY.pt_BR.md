# Integridade de release (evidência opcional de adulteração)

**English:** [RELEASE_INTEGRITY.md](RELEASE_INTEGRITY.md)

O runtime pode fazer verificações **opcionais** para que instalações modificadas sejam marcadas como **TAMPERED** quando o **enforcement** comercial está ativo. Isso **não** prova resistência a um atacante determinado; ajuda **suporte** e **auditoria**.

## Digest de build embutido

- Arquivo: [`core/licensing/_build_digest.txt`](../core/licensing/_build_digest.txt) — padrão **`dev`** em clones de desenvolvimento.

  O arquivo **fica rastreado** no Git de propósito (*placeholder*, **sem** `.gitignore`): no release ou build dedicado ao cliente substitua a linha única pelo **SHA-256 hex** (ou id acordado); em produção defina **`DATA_BOAR_EXPECTED_BUILD_DIGEST`** com o **mesmo** valor para o guard de licença marcar **TAMPERED** sob `licensing.mode: enforced` quando houver divergência. **`dev`** sozinho em árvore OSS **não** substitui um digest contratual — a variável só ativa o contraste quando a política de implantação fornece um digest.

## Manifesto de arquivos assinado (opcional)

- Esquema JSON:

```json
{
  "version": 1,
  "files": [
    { "path": "core/licensing/guard.py", "sha256": "hex..." }
  ]
}
```

- Defina **`DATA_BOAR_RELEASE_MANIFEST_PATH`** ou `licensing.manifest_path` no config para o caminho desse arquivo.
- Na inicialização (modo enforced), os hashes são verificados; divergência → **TAMPERED**.

## Automação

- [`scripts/release-integrity-check.ps1`](../scripts/release-integrity-check.ps1) — valida um manifesto contra a árvore de trabalho (desenvolvedor / CI).
- [`scripts/example-release-manifest.json`](../scripts/example-release-manifest.json) — formato de exemplo (substitua caminhos/hashes em releases reais).

## Notas de empacotamento

- **PyInstaller / zipapp / wheel:** regenere o manifesto para o layout **instalado**.
- Prefira **assinatura de código** (Windows Authenticode / notarização Apple) para binários além das verificações de manifesto.

## SBOM (inventário da cadeia de suprimentos)

Artefatos **CycloneDX JSON** para a árvore de dependências Python e para a **imagem Docker** construída a partir deste repositório são gerados pelo workflow do GitHub Actions [**SBOM**](../.github/workflows/sbom.yml), com os mesmos nomes descritos em [**SECURITY.pt_BR.md**](../SECURITY.pt_BR.md) (**`sbom-python.cdx.json`**, **`sbom-docker-image.cdx.json`**). Registro de decisão: [**ADR 0003**](adr/ADR-0003-sbom-roadmap-cyclonedx-then-syft.md). Regeneração local (Docker necessário para o SBOM da imagem): [**scripts/generate-sbom.ps1**](../scripts/generate-sbom.ps1).

## Relacionado

- [ops/INTEGRITY_HUB.pt_BR.md](ops/INTEGRITY_HUB.pt_BR.md) ([EN](ops/INTEGRITY_HUB.md)) — hub de navegação para todas as camadas de integridade (este arquivo vs [ops/RELEASE_INTEGRITY.pt_BR.md](ops/RELEASE_INTEGRITY.pt_BR.md)).
- [ops/RELEASE_INTEGRITY.pt_BR.md](ops/RELEASE_INTEGRITY.pt_BR.md) ([EN](ops/RELEASE_INTEGRITY.md)) — especificação operacional de release (evidência Rust, checklist SRE); **não** é duplicata deste doc focado em licenciamento.
- [LICENSING_SPEC.md](LICENSING_SPEC.md) (EN)
