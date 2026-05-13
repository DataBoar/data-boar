# Plano: Detecção de Dados Sensíveis em Imagens (OCR + BLOB + Embeds)

**Status:** Pending
**Date:** 2026-04-04
**Authors:** Fabio Leitao
**Priority:** H3

<!-- PLANO: PLAN_IMAGE_SENSITIVE_DATA_DETECTION -->
<!-- Status: Proposed | Prioridade: H2 (alto valor, depende de Synthetic Data Lab estável) -->
<!-- Criado: 2026-04-03 | Autor: Fabio Leitao -->

## Motivação

O Data Boar já varre texto estruturado e semi-estruturado. Mas imagens -- fotos de CPF, RG, receitas médicas, cartões de crédito, documentos digitalizados -- são um vetor de dado sensível que o scanner não enxerga hoje.

Cenários reais:

- Bucket S3 ou NAS com fotos de documentos de clientes (onboarding, KYC).
- Coluna `foto_documento` no banco MySQL armazenando base64 de RG.
- PDF de prontuário médico com imagem escaneada do cartão SUS.
- Usuário tentou burlar DLP renomeando foto de CPF para `.mp3` (cloaking).
- Email com anexo JPEG de extrato bancário.

Fundamento legal (LGPD):
- Art. 5, X -- número de documento (CPF, RG, CNH) = dado pessoal.
- Art. 5, II -- dado biométrico (rosto) e dado de saúde = dado pessoal sensível.
- Art. 14 -- dado de crianças.

Fundamento legal (GDPR):
- Art. 4(14) -- biometric data.
- Art. 9 -- special categories (health, biometric).

ADR: `docs/adr/ADR-0012-ocr-image-sensitive-data-detection.md`

---

## Sequenciamento recomendado

Deve ser executado APÓS o `PLAN_SYNTHETIC_DATA_LAB.pt_BR.md` ter gerado corpus de imagens sintéticas para testes.

Posição na fila: H2 (high value, not blocking current release).

---

## Fases

### Fase 0 -- Fundação e dependências (1-2 dias)

**Meta:** ambiente pronto, OCR funcionando, primeiro teste de smoke com imagem real.

- [ ] Adicionar dependências opcionais ao `pyproject.toml`:
  - `pytesseract` (binding Python para Tesseract)
  - `Pillow` (processamento de imagem)
  - `easyocr` (opcional, tier 2, flag separada)
  - Usar `extras` ou grupo `image` para não impor a todos os usuários.
- [ ] Documentar instalação do binário Tesseract:
  - Linux: `apt install tesseract-ocr tesseract-ocr-por`
  - macOS: `brew install tesseract tesseract-lang`
  - Windows: instalador oficial + PATH
  - Docker: adicionar ao `Dockerfile` (nova stage opcional `data_boar:image`)
- [ ] Criar `core/image_detector.py` (stub com `ImageDetector` class).
- [ ] Smoke test: passar JPEG com CPF impresso, verificar que OCR retorna texto e regex bate.
- [ ] Adicionar `enable_image_scanning: false` ao schema de config (default off).

### Fase 1 -- Varredura de arquivos de imagem standalone (3-5 dias)

**Meta:** o scanner de filesystem detecta imagens e extrai texto via OCR.

- [ ] Detecção por magic bytes (não por extensão):
  - JPEG: `FF D8 FF`
  - PNG: `89 50 4E 47`
  - GIF: `47 49 46 38`
  - TIFF: `49 49 2A 00` ou `4D 4D 00 2A`
  - WebP: `52 49 46 46` + `57 45 42 50`
  - BMP: `42 4D`
- [ ] Detectar **cloaking**: arquivo com extensão não-imagem mas magic bytes de imagem.
  - Exemplo: `curriculo.mp3` com magic bytes JPEG.
  - Reportar como `image_cloaked_as: mp3`.
- [ ] Pipeline:
  1. Abrir imagem com Pillow.
  2. Pre-processar (escala de cinza, resize se muito pequena).
  3. Passar para Tesseract com `lang=por+eng`.
  4. Aplicar regex patterns LGPD sobre texto extraído.
  5. Registrar finding com: `file_path`, `ocr_engine`, `ocr_confidence`, `pattern_matched`, `category`, `norm`.
- [ ] Configurar `image_ocr_engine: tesseract` (default) e `easyocr` (opt-in).
- [ ] Timeout por imagem configurável (default 30s) para não travar em arquivos corrompidos.
- [ ] Testes unitários com corpus sintético do `PLAN_SYNTHETIC_DATA_LAB`.

### Fase 2 -- BLOBs e base64 em banco de dados (3-4 dias)

**Meta:** o scanner de banco detecta colunas binárias com imagens e as analisa.

- [ ] Heurística de detecção de colunas de imagem:
  - Tipo: `BLOB`, `BYTEA`, `LONGBLOB`, `MEDIUMBLOB`, `RAW`, `IMAGE`, `VARBINARY`.
  - Nome: `foto`, `imagem`, `photo`, `image`, `thumbnail`, `avatar`, `documento`, `attachment`, `img`, `picture`, `scan`.
  - Combinação de tipo + nome eleva score de suspeita.
- [ ] Detecção de base64 em colunas TEXT/VARCHAR:
  - Regex para detectar strings base64 longas (> 100 chars, charset `[A-Za-z0-9+/=]`).
  - Tentar decodificar e verificar magic bytes.
- [ ] Amostragem configurável: `image_blob_sampling_rows: 5` (nunca carregar tabela inteira).
- [ ] Pipeline: decodificar bytes -> verificar magic bytes -> se imagem, chamar OCR tier 1.
- [ ] **Privacidade por design:** nunca persistir o conteúdo decodificado da imagem em logs ou relatório. Apenas o finding (path, pattern, categoria).
- [ ] Suporte inicial: MariaDB, PostgreSQL, Oracle XE (já no synthetic lab).
- [ ] Testes: containers sintéticos com BLOBs de imagens de CPF/RG fake.

### Fase 3 -- Imagens embutidas em documentos (2-3 dias)

**Meta:** PDF, DOCX e emails com imagens embutidas também são varridos.

**PDF:**
- [ ] Usar `pymupdf` (fitz) para extrair imagens de PDFs pagina a pagina.
- [ ] Alternativa fallback: `pdfplumber` para PDFs sem texto nativo (imagem pura scaneada).
- [ ] Associar finding ao `file_path + page_number + image_index`.

**DOCX / XLSX:**
- [ ] Usar `python-docx` para extrair imagens do `word/media/` interno.
- [ ] Associar finding ao `file_path + paragraph_index`.

**EML / MSG:**
- [ ] Aproveitar parser de email existente para extrair imagens de partes `image/*`.
- [ ] Passar cada anexo de imagem para OCR tier 1.

**Teste de cloaking avançado:**
- [ ] PDF que na verdade e uma imagem scaneada sem camada de texto.
- [ ] DOCX com apenas imagens, sem texto.

### Fase 4 -- Integração com compliance report (1-2 dias)

**Meta:** findings de imagem aparecem no relatório como qualquer outro finding.

- [ ] Adicionar campo `source_type: image_file | image_blob | image_embedded` ao finding.
- [ ] Adicionar campo `ocr_engine`, `ocr_confidence` ao finding (para auditoria).
- [ ] Seção dedicada "Imagens com dados sensiveis" no relatório HTML/Excel.
- [ ] Contar imagens varridas, imagens com findings, imagens cloaked.
- [ ] Dashboard: gauge de cobertura de scan com imagens habilitadas vs desabilitadas.

### Fase 5 -- Classificação de tipo de documento (deferred / H3)

**Meta:** identificar automaticamente o tipo de documento na imagem (RG, CNH, passaporte, receita médica, extrato).

- [ ] Treinar ou usar modelo pré-treinado (CLIP zero-shot ou classificador CNN fino).
- [ ] Input: imagem; Output: `doc_type` (id_card_br, passport, prescription, bank_statement, other).
- [ ] Combinar com OCR para reduzir falsos positivos (e.g. só reportar CPF se doc_type = id_card).
- [ ] Detecção de rosto (biométrico) via `face_recognition` ou `mediapipe`.
- [ ] Detecção de menor de idade (estimativa de idade) -- alta complexidade, avaliar com cuidado.

---

## Matriz de detecção alvo

| Tipo de imagem                        | Método primário          | Categoria LGPD         | Norm             |
|---------------------------------------|--------------------------|------------------------|------------------|
| Foto de CPF impresso                  | OCR regex CPF            | Dado pessoal           | Art. 5, X        |
| Foto de RG (frente/verso)             | OCR regex + doc_type     | Dado pessoal           | Art. 5, X        |
| Foto de CNH                           | OCR regex + doc_type     | Dado pessoal           | Art. 5, X        |
| Foto de passaporte                    | OCR regex + doc_type     | Dado pessoal           | Art. 5, X        |
| Foto de rosto                         | Face detector (Fase 5)   | Dado sensível biom.    | Art. 5, II       |
| Foto de receita médica                | OCR + doc_type           | Dado sensível saude    | Art. 5, II       |
| Foto de exame / laudo                 | OCR + doc_type           | Dado sensível saude    | Art. 5, II       |
| Foto de cartão de crédito             | OCR regex PAN            | Dado pessoal financ.   | Art. 5; PCI DSS  |
| Foto de extrato bancário              | OCR regex + doc_type     | Dado pessoal financ.   | Art. 5           |
| Foto de criança                       | Face + age estimator     | Dado de menor          | Art. 14          |
| BLOB JPEG em banco com CPF            | BLOB detect + OCR        | Dado pessoal           | Art. 5, X        |
| base64 de imagem em coluna TEXT       | base64 detect + OCR      | Dado pessoal           | Art. 5           |
| PDF scaneado (sem texto nativo)       | Embed extract + OCR      | Conforme conteúdo      | Conforme achado  |
| JPEG cloaked como MP3                 | Magic bytes + OCR        | Conforme conteúdo      | Conforme achado  |

---

## Dependências técnicas

| Pacote           | Uso                              | Tier         | PyPI / sistema              |
|------------------|----------------------------------|--------------|-----------------------------|
| `pytesseract`    | OCR tier 1                       | Opcional     | `pip install pytesseract`   |
| `Pillow`         | Abrir/pre-processar imagens      | Opcional     | `pip install Pillow`        |
| `easyocr`        | OCR tier 2 (alta acurácia)       | Opt-in       | `pip install easyocr`       |
| `pymupdf`        | Extrair imagens de PDF           | Opcional     | `pip install pymupdf`       |
| `tesseract-ocr`  | Binário sistema (Linux/Mac/Win)  | Sistema      | apt/brew/msi                |
| `tesseract-ocr-por` | Idioma pt-BR para Tesseract  | Sistema      | apt / traineddata           |

---

## Guardrails

- Nunca salvar conteúdo binário decodificado de BLOBs em logs, relatórios ou arquivos de artefato.
- Nunca enviar imagens para API externa sem consentimento explícito do operador e base legal documentada.
- Timeout por imagem: evitar travar em arquivos corrompidos ou muito grandes.
- Sampling de BLOBs: nunca carregar tabela inteira em memória; amostrar N linhas.
- Resultados de OCR podem ter falsos positivos -- expor `ocr_confidence` no finding para triagem.

---

## Indicadores de sucesso

- [ ] Scanner detecta CPF em JPEG com Tesseract com F1 > 0.85 no corpus sintético.
- [ ] BLOB com imagem de RG em MariaDB sintético reportado como finding.
- [ ] PDF scaneado (sem texto nativo) com CPF retorna finding.
- [ ] Arquivo `.mp3` com magic bytes JPEG reportado como `image_cloaked_as: mp3`.
- [ ] Nenhum conteúdo de imagem persistido em artefatos de relatório.
- [ ] Scan de 1000 imagens JPG/PNG termina em menos de 10 min em CPU (worker=4).

---

## Pendências e decisões abertas

- Decidir se EasyOCR vai no Dockerfile default ou apenas em `data_boar:image` (nova tag).
- Avaliar se detecção de rosto (biométrico, Fase 5) entra no escopo v2.0 ou fica como plugin.
- Definir quais extensoes de arquivo disparam a varredura de imagem por default (tudo vs lista curada).
- Confirmar com colaboradores se clientes alvos (EAD/Sul, escritorio de advocacia) armazenam imagens em banco ou apenas no filesystem.
