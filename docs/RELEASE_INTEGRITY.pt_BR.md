# Integridade de release (evidência opcional de adulteração)

**English:** [RELEASE_INTEGRITY.md](RELEASE_INTEGRITY.md)

O runtime pode fazer verificações **opcionais** para que instalações modificadas sejam marcadas como **TAMPERED** quando o **enforcement** comercial está ativo. Isso **não** prova resistência a um atacante determinado; ajuda **suporte** e **auditoria**.

## Digest de build embutido

- Arquivo: [`core/licensing/_build_digest.txt`](../core/licensing/_build_digest.txt) — **gitignored**; gerado localmente ou no CI (não commitado em `main`).

  O script [`scripts/generate_build_digest.py`](../scripts/generate_build_digest.py) calcula um **SHA-256 hex determinístico** sobre arquivos fonte críticos ordenados (`main.py`, `core/**/*.py`, `connectors/**/*.py`, `scanners/**/*.py`, `cli/**/*.py`) e grava a linha única. O workflow **SBOM** executa esse passo **antes** do `docker build` para embutir o digest nas imagens de release. Em produção, defina **`DATA_BOAR_EXPECTED_BUILD_DIGEST`** com o **mesmo** valor (veja [`.env.example`](../.env.example)) para o guard marcar **TAMPERED** com `licensing.mode: enforced` quando a linha embutida divergir. Tags de release também anexam **`build-digest.txt`** no GitHub Release para verificação independente.

## Manifesto de arquivos assinado (opcional)

- Esquema JSON (gerado por [`scripts/generate_release_manifest.py`](../scripts/generate_release_manifest.py)):

```json
{
  "generated_at": "2026-05-24T23:00:00Z",
  "data_boar_version": "1.7.4",
  "files": [
    { "path": "main.py", "sha256": "hex..." },
    { "path": "core/licensing/guard.py", "sha256": "hex..." }
  ]
}
```

  Os caminhos críticos seguem o mesmo conjunto do build digest mais `boar_fast_filter*.so` quando a extensão Rust está compilada. O workflow **SBOM** gera `release-manifest.json` **dentro** da imagem Docker (após `docker build`) para que caminhos da extensão nativa coincidam com o runtime; o arquivo vai para GitHub Releases junto com SBOMs e `build-digest.txt`.

- Defina **`DATA_BOAR_RELEASE_MANIFEST_PATH`** ou `licensing.manifest_path` no config (veja [`.env.example`](../.env.example)).
- Na inicialização (modo enforced), os hashes são verificados; divergência → **TAMPERED**.
- Verificação local: `uv run python scripts/generate_release_manifest.py --check dist/release-manifest.json`

## Automação

- [`scripts/generate_build_digest.py`](../scripts/generate_build_digest.py) — digest canônico de build (`--check` falha se houver drift).
- [`scripts/generate_release_manifest.py`](../scripts/generate_release_manifest.py) — manifesto SHA-256 por arquivo (`--out`, `--check`).
- [`scripts/release-integrity-check.ps1`](../scripts/release-integrity-check.ps1) — valida um manifesto contra a árvore de trabalho (desenvolvedor / CI).
- [`scripts/example-release-manifest.json`](../scripts/example-release-manifest.json) — exemplo mínimo legado (prefira a saída do gerador em releases).

## Notas de empacotamento

- **PyInstaller / zipapp / wheel:** regenere o manifesto para o layout **instalado**.
- Prefira **assinatura de código** (Windows Authenticode / notarização Apple) para binários além das verificações de manifesto.

## SBOM (inventário da cadeia de suprimentos)

Artefatos **CycloneDX JSON** para a árvore de dependências Python e para a **imagem Docker** construída a partir deste repositório são gerados pelo workflow do GitHub Actions [**SBOM**](../.github/workflows/sbom.yml), com os mesmos nomes descritos em [**SECURITY.pt_BR.md**](../SECURITY.pt_BR.md) (**`sbom-python.cdx.json`**, **`sbom-docker-image.cdx.json`**). Registro de decisão: [**ADR 0003**](adr/ADR-0003-sbom-roadmap-cyclonedx-then-syft.md). Regeneração local (Docker necessário para o SBOM da imagem): [**scripts/generate-sbom.ps1**](../scripts/generate-sbom.ps1).

## Relacionado

- [ops/INTEGRITY_HUB.pt_BR.md](ops/INTEGRITY_HUB.pt_BR.md) ([EN](ops/INTEGRITY_HUB.md)) — hub de navegação para todas as camadas de integridade (este arquivo vs [ops/RELEASE_INTEGRITY.pt_BR.md](ops/RELEASE_INTEGRITY.pt_BR.md)).
- [ops/RELEASE_INTEGRITY.pt_BR.md](ops/RELEASE_INTEGRITY.pt_BR.md) ([EN](ops/RELEASE_INTEGRITY.md)) — especificação operacional de release (evidência Rust, checklist SRE); **não** é duplicata deste doc focado em licenciamento.
- [LICENSING_SPEC.md](LICENSING_SPEC.md) (EN)
