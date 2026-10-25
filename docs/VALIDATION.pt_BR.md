# Baseline de acurácia de detecção (precisão / recall / F1)

**English:** [VALIDATION.md](VALIDATION.md)

**Público:** colaboradores, banca Design Science e compradores técnicos que precisam de
baseline de detecção **medida** (não asserção de marketing).

**Relacionado:** [TESTING_POC_GUIDE.pt_BR.md](TESTING_POC_GUIDE.pt_BR.md), ADR 0007,
issue **#835**.

---

## 1. O que é isto

Já existem benchmarks de **performance**. Este documento publica o primeiro baseline de
**acurácia** do detector de PII contra um conjunto sintético **rotulado**:

| Artefato | Caminho |
| -------- | ------- |
| Fixtures + manifesto | `tests/data/f1_validation/` (`ground_truth.yaml`) |
| Regenerar | `uv run python scripts/generate_f1_validation_fixtures.py` |
| Medir P/R/F1 | `uv run python scripts/validate_detection_f1.py` |

O harness usa a API real `SensitivityDetector.analyze` →
`(sensitivity, pattern_detected, norm_tag, confidence 0–100)`.

---

## 2. Metodologia (anti-vazamento)

Quatro classes: `pii` / `clean` / `tricky_fp` / `tricky_fn`.

| Split | Papel |
| ----- | ----- |
| `measure/` | **Único** split dos números publicados abaixo |
| `calibrate/` | Reservado para calibrar limiar de confiança no futuro |

**Regra:** o mesmo **template** sintético (e os mesmos identificadores) **não** pode
aparecer nos dois splits — senão o F1 fica otimista. O harness verifica
(`anti-leakage: OK`).

Fase 1: formatos texto (txt/csv/tsv/json/xml/html) com os **mesmos** valores entre
formatos. SQL/NoSQL/shares e bandas de confiança no relatório ficam para fases 2–4.

---

## 3. Baseline publicado (split measure)

```bash
uv run python scripts/validate_detection_f1.py --split measure
```

| Campo | Valor |
| ----- | ----- |
| **Data (UTC)** | 2026-08-17 |
| **Arquivos** | 12 (`measure`) |
| **TP / FP / TN / FN** | 6 / 4 / 0 / 2 |
| **Precisão** | **0.6000** |
| **Recall** | **0.7500** |
| **F1** | **0.6667** |

### Por padrão (measure)

| Padrão | Precisão | Recall | F1 |
| ------ | -------- | ------ | -- |
| `EMAIL` | 1.0000 | 1.0000 | 1.0000 |
| `LGPD_CNPJ` | 1.0000 | 1.0000 | 1.0000 |
| `LGPD_CPF` | 1.0000 | 0.7500 | 0.8571 |

### Por classe (measure)

| Classe | Notas |
| ------ | ----- |
| `pii` | 6/6 TP entre formatos (F1 **1.0000**) |
| `tricky_fn` | 0/2 — CPF mascarado/espaçado e placeholder de stego (FN honesta) |
| `clean` | 2 FP — ML em contexto “entertainment” no catálogo sintético |
| `tricky_fp` | 2 FP — letras com data/telefone + ML em CPF inválido (gate de checksum bloqueia `LGPD_CPF`) |

---

## 4. Limitações conhecidas (Design Science)

1. CPF mascarado/espaçado não produz `LGPD_CPF`.
2. Placeholder de stego (sem LSB binário na Fase 1).
3. Heurística ML de entretenimento pode emitir MEDIUM em texto de catálogo.
4. Padrões fracos em cifras/letras ainda aparecem (MEDIUM).
5. Escopo Fase 1 = texto; matriz PDF/OCR/office fica para depois.

---

## 5. O que isto não é

- Não é gate de CI que falha por drift de F1 (smoke testa estrutura + anti-vazamento + recall de PII claro).
- Não dispensa ADR 0007 antes de dados reais de cliente.
- Não substitui o corpus de cenários do [TESTING_POC_GUIDE.pt_BR.md](TESTING_POC_GUIDE.pt_BR.md).

---

## 6. Ritual de atualização

1. Editar/regenerar fixtures.
2. Rodar `validate_detection_f1.py --split measure`.
3. Atualizar a **§3** aqui e no EN.
4. Não misturar números de `calibrate/` na tabela publicada.
