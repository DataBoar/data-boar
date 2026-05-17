# EXIF, OCR e metadados de imagem para contexto do assistente (Windows + uv)

**English:** [IMAGE_EXIF_OCR_FOR_AGENT.md](IMAGE_EXIF_OCR_FOR_AGENT.md)

## Finalidade

O assistente precisa de **texto com teto** a partir de **fotos (HEIC/JPEG do iPhone)**, **áudio** e **vídeo** sem fingir que o modelo “vê” binários nativamente. O repo já implementa extração no **produto** em **`connectors/rich_media_sample.py`** (ligado a `file_scan.scan_rich_media_metadata` e `scan_image_ocr` — ver [USAGE.pt_BR.md](../USAGE.pt_BR.md)). O **CLI do operador** expõe a **mesma pilha** para trabalho ad-hoc no Cursor.

## Taxonomia (complexidade vs tokens e superfície)

| Nível | O quê | Quando |
| ----- | ---- | ------ |
| **L0** | Não ler pixels / tags | O operador cola texto; arquivo fora de escopo ou sensível demais. |
| **L1** | **Só metadados** (padrão: sem `--no-metadata`): EXIF, mutagen, ffprobe | Fotos do iPhone: data, câmera, strings de **localização** no EXIF — ainda **vizinhas de PII**; manter fluxos sob **`docs/private/`**. |
| **L2** | **L1 + OCR** (`--ocr` em imagens): Tesseract num raster **redimensionado** | *Screenshots*, digitalizações, texto impresso em fotos — mesmo motor do OCR opcional do scanner. |
| **L3** | **Varredura Data Boar** num diretório com **ML/DL** do detector | Conformidade / inventário: o motor pontua **amostras de texto** (incluindo saída de OCR quando habilitado na **config**), não “busca por similaridade visual” em biblioteca de fotos. |

## O que o ML/DL do Data Boar é (e não é)

- **É:** classificadores e *gates* sobre conteúdo **textual** (regex, vocabulário, níveis ML ligados a **sensibilidade** / rótulos de conformidade no pipeline do produto).
- **Não é:** **embedding visual** geral ou busca estilo **CLIP** (“achar todas as fotos do objeto X”) em dezenas de milhares de imagens. Isso exige **pipeline de indexação** (*embeddings* + armazenamento vetorial) e revisão explícita de privacidade.
- **Padrão “encontrar” hoje:** rodar OCR **L2** em lote (um script em lote pode ser evolução futura) e **pesquisar o texto extraído** com **`repo-grep.ps1`** / **`rg`** sobre `.txt` exportados — token-aware e explicável.

## Automação principal

| Ferramenta | Papel |
| ---------- | ----- |
| **`scripts/image-inspect.ps1`** | Wrapper Windows: **`uv run python scripts/image_inspect.py ...`** |
| **`scripts/image_inspect.py`** | CLI de um arquivo sobre **`build_rich_media_text_sample`** |

**Exemplos (raiz do repo):**

```powershell
.\scripts\image-inspect.ps1 -Path "docs\private\icloud_temp\IMG_1234.HEIC"
.\scripts\image-inspect.ps1 -Path ".\photo.jpg" -Ocr -OcrLang "por"
.\scripts\image-inspect.ps1 -Path ".\clip.mov"
```

**Dependências (matriz honesta):**

| Objetivo | Dica de instalação |
| -------- | ------------------ |
| HEIC / HEIF | **`uv sync --extra richmedia`** ( **`pillow-heif`** — igual ao produto). |
| OCR | **`uv sync --extra richmedia`** + **`tesseract`** do sistema no `PATH` (instalador Windows ou `winget` — escolha uma build que a organização confie). |
| Tags de vídeo | **`ffprobe`** no `PATH` (`winget install ffmpeg`). |
| Tags de áudio | **mutagen** via extra **richmedia**. |

Se faltar dependência, a saída pode ficar vazia; o CLI imprime dica em stderr.

## Fluxo iPhone / iCloud (árvore privada)

1. Obter cópias em **`docs/private/icloud_temp/`** (ou outro caminho **gitignored**) com **`scripts/icloud-photos-fetch-range.ps1`** — ver guia privado **`ICLOUD_PHOTOS_SYNC_GUIDE.md`** quando existir.
2. Rodar **`image-inspect.ps1`** no arquivo.
3. **Não** colar GPS bruto de EXIF nem nomes pessoais em **issues/PRs públicos**.

## Par com *frames* de vídeo

Gravações de **tela**: continue com **`scripts/video-frame-samples.ps1`** + visão em PNG — [VIDEO_FRAME_EXTRACT_FOR_AGENT.pt_BR.md](VIDEO_FRAME_EXTRACT_FOR_AGENT.pt_BR.md). **Fotos estáticas**: use **este** documento.

## Referências

- **`connectors/rich_media_sample.py`**, **`core/rich_media_magic.py`**
- [USAGE.pt_BR.md](../USAGE.pt_BR.md) — `scan_rich_media_metadata`, `scan_image_ocr`
- [ADR 0012](../adr/ADR-0012-ocr-image-sensitive-data-detection.md)
- **`docs/ops/TOKEN_AWARE_SCRIPTS_HUB.pt_BR.md`**, **`.cursor/skills/image-inspect-for-agent/SKILL.md`**
