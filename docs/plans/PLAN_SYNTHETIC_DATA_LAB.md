# Plan: Synthetic data lab for Data Boar tests

**Status:** Pending
**Date:** 2026-04-04
**Authors:** Fabio Leitao
**Priority:** H3
**Depends on:** ADR-0007

**Português (Brasil):** [PLAN_SYNTHETIC_DATA_LAB.pt_BR.md](PLAN_SYNTHETIC_DATA_LAB.pt_BR.md)

<!-- plans-hub-summary: Synthetic corpus (SQL, files, cloaking, minors, images) for FP/FN before real data. ADR-0007. -->

**Priority (queue):** H1 — prerequisite for controlled tests before real data
**Dependencies:** Data Boar detector pipeline (`core/detector.py`), connector matrix (`docs/TECH_GUIDE.md`)
**Collaborators:** operator, future collaborators (synthetic-data provider and test environment)
**Created:** 2026-04-03

---

## Goal

Build a **synthetic data corpus** that lets us:

1. Test **personal/sensitive-data detection** under controlled conditions.
2. Map **false positives (FP)** and **false negatives (FN)** by data type, file format, and connector.
3. Validate **pseudo-anonymisation** and **partial re-identification** (to show residual risk to a customer).
4. Do all of this **before** exposing real customer data — a base for a safe demo and trustworthy reports.

ADR: [ADR-0007](../adr/ADR-0007-synthetic-data-corpus-before-real-data.md)

---

## 1. Databases in containers

### 1.1 Docker Compose for the lab

```yaml
# docs/private/lab/synthetic-data-lab/docker-compose.yml
# (gitignored; dados sintéticos ficam aqui)
version: "3.9"
services:

  mariadb:
    image: mariadb:11
    container_name: lab_mariadb
    environment:
      MARIADB_ROOT_PASSWORD: lab_root_pw
      MARIADB_DATABASE: databoar_test
    ports:
      - "3306:3306"
    volumes:
      - ./seed/mariadb:/docker-entrypoint-initdb.d

  postgres:
    image: postgres:16
    container_name: lab_postgres
    environment:
      POSTGRES_PASSWORD: lab_root_pw
      POSTGRES_DB: databoar_test
    ports:
      - "5432:5432"
    volumes:
      - ./seed/postgres:/docker-entrypoint-initdb.d

  oracle-xe:
    image: gvenzl/oracle-xe:21-slim
    container_name: lab_oracle
    environment:
      ORACLE_PASSWORD: lab_oracle_pw
    ports:
      - "1521:1521"
    # Oracle XE requires accepting the licence — local test only

  mongodb:
    image: mongo:7
    container_name: lab_mongo
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: lab_root_pw
    ports:
      - "27017:27017"
    volumes:
      - ./seed/mongo:/docker-entrypoint-initdb.d

  redis:
    image: redis:7-alpine
    container_name: lab_redis
    ports:
      - "6379:6379"
```

### 1.2 Synthetic table data (seed SQL)

#### Categories to cover per table

| Category | Example fields | Notes |
| --- | --- | --- |
| **National ID (CPF)** | cpf_cliente, doc_federal | valid and invalid (regex + validator) |
| **Company ID (CNPJ)** | cnpj_fornecedor | similar |
| **Registry (RG)** | rg, num_identidade | multiple state formats |
| **Email** | email, contato | realistic and obfuscated |
| **Phone** | tel, celular | with area code, without, international |
| **Address** | logradouro, cep, municipio | complete and fragmented |
| **Date of birth** | dt_nasc, data_nascimento | minors (< 18) flagged |
| **Health data** | cid, diagnostico, medicamento | sensitive LGPD art. 11 |
| **Financial data** | num_cartao, agencia, conta | masked and unmasked PAN |
| **Access data** | senha_hash, token_api, chave | detector should ignore hashes |
| **Racial data** | etnia, raca | sensitive LGPD art. 11 |
| **Minors** | flag_menor, dt_nasc | every row with `flag_menor=TRUE` must be flagged |

#### Forced FP rows (false positive)

```sql
-- Numbers that look like a national ID but are another context
INSERT INTO pedidos (descricao, valor) VALUES
  ('Produto referência 123.456.789-00', 29.90),   -- look-alike CPF in free text
  ('NF-e série 000.000.000-01', 150.00);           -- fiscal numbering
```

#### Forced FN rows (false negative)

```sql
-- Obfuscated or fragmented personal data to test limits
INSERT INTO clientes (campo_ofuscado) VALUES
  ('C*F: 123.4**.*89-0*'),      -- partial masking — should the detector find it?
  ('jose [at] email [dot] com'),  -- evasive email
  ('11 9 8765 4321');            -- unformatted phone
```

---

## 2. File-format matrix and variants

### 2.1 File types to cover

| Extension | Variants to generate | Sensitive data included |
| --- | --- | --- |
| `.pdf` | normal, password-protected, zipped | national ID, registry, email, DOB |
| `.docx` / `.doc` | normal, protected, metadata with a realistic name | national ID, health, minor |
| `.xlsx` / `.xls` | normal, protected, multiple sheets | national ID, PAN, financial |
| `.csv` | delimiters `,` `;` `\t`, UTF-8 and Latin-1 | all types |
| `.txt` | plain text, simulated log | email, IP, inline national ID |
| `.json` | flat and nested, array of objects | email, national ID, health |
| `.xml` | with namespaces, without | national ID, registry, address |
| `.odt` / `.ods` | native LibreOffice | national ID, email |
| `.pptx` | slides with a data table | health, minor |
| `.eml` / `.msg` | simulated email with attachment | national ID, registry, email, IP |
| `.sqlite` | embedded database file | all categories |

### 2.2 Compression variants

```bash
# Scripts para gerar arquivo base e variantes (em scripts/lab/generate_synthetic_files.sh)
# Protegido com senha:
zip -P "senha123" arquivo_protegido.zip arquivo_com_dados.pdf
# 7z AES-256:
7z a -p"senha456" -mhe=on protegido_aes.7z arquivo_com_dados.csv
# GZIP / TAR:
gzip -k arquivo_com_dados.csv
tar czf bundle.tar.gz *.csv *.pdf
```

---

## 3. Cloaking — disguised files

> Real scenario: users rename files to bypass DLP and compliance controls.

### 3.1 Cloaking types to test

| Real file | Fake extension | Test goal |
| --- | --- | --- |
| Excel workbook with national IDs | `.mp3` | real type vs extension |
| PDF with registry card | `.jpg` | binary content vs extension |
| CSV with health data | `.txt` | trivial — different extension, still readable |
| ZIP of PDFs | `.bak` | disguised archive |
| SQLite with PII | `.db` → `.log` | embedded DB with log extension |
| DOCX with national IDs | `.pdf` | Office format disguised as PDF |
| Python script with a hardcoded token | `.txt` | secret in a text file |

### 3.2 Generating cloaked files

```bash
# Copiar e renomear mantendo conteúdo original
cp clientes_com_cpf.xlsx musica_favorita.mp3
cp relatorio_medico.pdf foto_praia.jpg
cp planilha_saude.csv notas_reuniao.txt
cp backup_clientes.zip configuracao.bak
```

---

## 4. Minors’ data (simulated)

> LGPD art. 14: children’s and adolescents’ data require especially careful treatment.

### 4.1 Corpus rules

- **No real data** — names, national IDs, and dates are fully fictitious and marked synthetic.
- Include `fonte: SINTETICO` on every record.
- Dates of birth configured for ages 0–17.

### 4.2 Scenarios

```sql
-- Menor com dados de saúde (dupla sensibilidade)
INSERT INTO pacientes (nome, dt_nasc, cid, flag_menor, fonte) VALUES
  ('Colleague-W S. Fictício', '2015-03-15', 'F90.0', TRUE, 'SINTETICO'),
  ('Maria T. Fictícia', '2012-07-22', 'E11.9', TRUE, 'SINTETICO');

-- Menor em contexto escolar (LGPD + Marco Civil)
INSERT INTO alunos (nome, cpf_responsavel, dt_nasc_aluno, flag_menor, fonte) VALUES
  ('Colleague-I F. Fictício', '123.456.789-00', '2016-01-10', TRUE, 'SINTETICO');
```

---

## 5. Pseudo-anonymisation and re-identification

### 5.1 Techniques to test as input

| Technique | What to generate | Why it matters |
| --- | --- | --- |
| **Partial suppression** | `CPF: 123.***.***-**` | detector should flag the field, not only the value |
| **Generalisation** | `Age band: 30-40` instead of exact date | re-identification by combination |
| **Keyed pseudonymisation** | `hash(CPF) = abc123def456` | without the key, looks like non-PII |
| **Simulated k-anonymity** | group of 3+ records with same band+postcode+gender | combinatorial re-identification risk |
| **Incomplete data** | name + neighbourhood + occupation only | inference re-identification |

### 5.2 Controlled re-identification dataset

```csv
# pseudo_anon_sample.csv — para demonstrar risco ao cliente
id_hash,faixa_etaria,genero,cep_prefix,profissao,diagnostico
a1b2c3,30-35,M,24020,engenheiro,hipertensão
d4e5f6,30-35,M,24020,engenheiro,diabetes
# → k=2: combinação faixa+CEP+profissão já estreita muito a população
```

---

## 6. FP and FN limits — edge cases

### 6.1 Expected false positives (map and document)

| Case | Data | Expected | Ideal outcome |
| --- | --- | --- | --- |
| Fiscal numbering | `000.000.000-00` | FP (looks like national ID) | whitelist config |
| Product code | `987.654.321-X` | FP | context whitelist |
| GPS coordinates | `-22.9068, -43.1729` | not PII | must not fire |
| Order number | `2024.001.000-5` | FP | pattern tweak |

### 6.2 Expected false negatives (detect as gaps)

| Case | Data | Expected | Risk |
| --- | --- | --- | --- |
| Unpunctuated national ID | `12345678900` | should detect | FN if tests only use punctuation |
| Unicode email | `usuario@domínio.com.br` | should detect | encoding edge case |
| International phone | `+55 11 98765-4321` | should detect | domestic-only pattern |
| Isolated personal name | `Colleague-N Fictício` | context-dependent | hard without ML |

---

## 7. Execution plan

### Phase 0 — Scaffolding (1 sprint)

- [ ] Create `docs/private/lab/synthetic-data-lab/` (gitignored).
- [ ] Create `docker-compose.yml` per §1.1.
- [ ] Create `scripts/lab/generate_synthetic_corpus.py` to generate files and synthetic data programmatically.
- [ ] Create `scripts/lab/start_lab_dbs.ps1` (PowerShell wrapper for `docker compose up -d`).

### Phase 1 — Basic corpus (1–2 sprints)

- [ ] SQL seed for MariaDB and PostgreSQL covering all §1.2 categories.
- [ ] Files of every §2.1 format (simple — no password, no compression).
- [ ] Run a Data Boar scan and record FP/FN baseline.

### Phase 2 — Advanced variants (2–3 sprints)

- [ ] Password-protected and compressed files (§2.2).
- [ ] Full cloaking matrix (§3).
- [ ] Minors’ data (§4).
- [ ] Oracle XE if the licence is accepted in lab.

### Phase 3 — Pseudo-anonymisation and re-identification (1–2 sprints)

- [ ] Pseudo-anon dataset (§5).
- [ ] Re-identification risk report produced by Data Boar.
- [ ] Threshold and whitelist adjustments from results.

### Phase 4 — Real data (with collaborators — future)

- [ ] Receive a partial / anonymised production dataset.
- [ ] Confirm behaviour vs the synthetic corpus.
- [ ] Document delta and required adjustments.

---

## 9. Synthetic image corpus (for PLAN_IMAGE_SENSITIVE_DATA_DETECTION)

This section is a satellite of [PLAN_IMAGE_SENSITIVE_DATA_DETECTION.md](PLAN_IMAGE_SENSITIVE_DATA_DETECTION.md) ([pt-BR](PLAN_IMAGE_SENSITIVE_DATA_DETECTION.pt_BR.md)): it generates the image corpus needed to test the OCR scanner before touching real data.

### 9.1 Image types to generate

| Type | Suggested tool | Fake content | Test scenario |
| ---- | -------------- | ------------ | ------------- |
| Printed national ID (A4 scan sim.) | Pillow (text on white) | Invalid ID in valid format (e.g. 000.000.000-00) | OCR tier 1 |
| Registry card (front) | Pillow + basic layout | Fictitious name, registry, DOB | OCR + doc_type |
| Driver licence (front) | Pillow + basic layout | Fictitious name, national ID, expiry | OCR + doc_type |
| Medical prescription | Pillow + fictitious medical text | Patient, licence number, medicine (fake) | Sensitive health |
| Simulated bank statement | Pillow + posting table | Fictitious branch/account, small amounts | Financial |
| Face photo (avatar) | AI-generated or Pillow oval | Face with no real identity | Biometric (Phase 5) |
| Child (placeholder) | Text "[fictitious minor]" | No real child photo | LGPD Art. 14 |
| Corrupt image | Random bytes with magic | N/A | Robustness / timeout |
| Cloaked image (.mp3, .docx) | JPEG copy with wrong extension | Any image above | Cloaking detection |
| Image with no PII | Pillow landscape / shapes | No personal data | False-positive test |
| base64 national-ID image in .txt | Python encode | Fictitious ID in JPEG base64 | base64-in-text detection |

### 9.2 Generation script

Create `scripts/lab/generate_synthetic_images.py`:

- Generate images with `Pillow` for each type above.
- Save under `docs/private/lab/images/` (gitignored).
- Generate `docs/private/lab/images/MANIFEST.json` with: type, file, expected PII, LGPD category, expected result (TP/TN).
- Never use real photos of people; never use real national IDs or licences.

### 9.3 BLOBs in the synthetic database

Extend MariaDB/PostgreSQL/Oracle seed scripts to:

- [ ] `foto_documento LONGBLOB` on `clientes` with 3–5 fictitious registry-card images.
- [ ] `attachment TEXT` with base64 of a fictitious national-ID JPEG.
- [ ] `thumbnail BLOB` with a no-PII image (false-positive test).

### 9.4 Scanned PDFs (no text layer)

- [ ] Generate a PDF where each page is a JPEG (not a native-text PDF).
- [ ] Use `reportlab` or `img2pdf` to pack national-ID / registry images.
- [ ] Save under `docs/private/lab/files/` beside other synthetic files.

### 9.5 Image-corpus guardrails

- Never use real photos of people, even if public (copyright + privacy).
- Never use real documents (scanning the operator’s own ID for tests is forbidden — that creates real data in a test tree).
- National IDs used must be visibly invalid (all-same digits, repeated sequences) or carry a synthetic suffix visible on the image itself.
- “Face” images only as AI avatars or geometric shapes.

---

## 8. Guardrails

- **Never commit** synthetic data that could be confused with real people (use intentionally invalid ID sequences; fictitious names with a “Fictício/Sintético” suffix).
- Keep the corpus under `docs/private/lab/` (gitignored).
- Generation scripts live in `scripts/lab/` — commit scripts, **not** generated data.
- Record scan results under `docs/private/lab/reports/` (gitignored) — never in public issues/PRs.

---

## Related

- [TECH_GUIDE.md](../TECH_GUIDE.md) — connector and format matrix.
- [PLAN_LAB_OP_OBSERVABILITY_STACK.md](PLAN_LAB_OP_OBSERVABILITY_STACK.md) — lab observability stack.
- [LAB_OP_MINIMAL_CONTAINER_STACK.md](../ops/LAB_OP_MINIMAL_CONTAINER_STACK.md) — baseline containers.
- [PLANS_TODO.md](PLANS_TODO.md) — project sequencing.
- [PLAN_IMAGE_SENSITIVE_DATA_DETECTION.md](PLAN_IMAGE_SENSITIVE_DATA_DETECTION.md) — OCR/BLOB after this corpus.
