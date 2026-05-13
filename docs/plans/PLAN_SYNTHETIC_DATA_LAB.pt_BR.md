# PLAN: Laboratório de Dados Sintéticos para Testes do Data Boar

**Status:** Pending
**Date:** 2026-04-04
**Authors:** Fabio Leitao
**Priority:** H3
**Depends on:** ADR-0007

**Prioridade:** H1 — pré-requisito para testes controlados antes de dados reais
**Dependências:** Data Boar detector pipeline (`core/detector.py`), matriz de conectores (`docs/TECH_GUIDE.pt_BR.md`)
**Colaboradores:** operador, colaboradores futuros (fornecedor de dados sintéticos e ambiente de test)
**Criado em:** 2026-04-03

---

## Objetivo

Construir um **corpus de dados sintéticos** que permita:

1. Testar a **detecção de dados pessoais/sensíveis** do Data Boar em condições controladas.
2. Mapear comportamento de **falso positivos (FP)** e **falso negativos (FN)** por tipo de dado, formato de arquivo e conector.
3. Validar **pseudo-anonimização** e capacidade de **re-identificação parcial** (para provar o risco residual ao cliente).
4. Fazer tudo isso **antes** de expor dados reais de clientes — base para demo segura e relatórios confiáveis.

---

## 1. Bases de dados em container

### 1.1 Docker Compose para laboratório

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
    # Oracle XE requer aceitar licença — use apenas para teste local

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

### 1.2 Dados sintéticos nas tabelas (seed SQL)

#### Categorias a cobrir por tabela

| Categoria | Exemplos de campos | Notas |
|---|---|---|
| **CPF** | cpf_cliente, doc_federal | válidos e inválidos (para testar regex + validador) |
| **CNPJ** | cnpj_fornecedor | similar |
| **RG** | rg, num_identidade | múltiplos formatos estaduais |
| **E-mail** | email, contato | formats reais e ofuscados |
| **Telefone** | tel, celular | com DDD, sem, internacional |
| **Endereço** | logradouro, cep, municipio | completo e fragmentado |
| **Data de nascimento** | dt_nasc, data_nascimento | datas de menores (< 18) sinalizadas |
| **Dados de saúde** | cid, diagnostico, medicamento | dado sensível LGPD art. 11 |
| **Dados financeiros** | num_cartao, agencia, conta | PAN mascarado e não-mascarado |
| **Dados de acesso** | senha_hash, token_api, chave | para validar se detector ignora hashes |
| **Dados raciais** | etnia, raca | dado sensível LGPD art. 11 |
| **Menores de idade** | flag_menor, dt_nasc | toda linha com `flag_menor=TRUE` deve ser sinalizada |

#### Linhas de FP forçado (falso positivo)

```sql
-- Números que se parecem com CPF mas são outro contexto
INSERT INTO pedidos (descricao, valor) VALUES
  ('Produto referência 123.456.789-00', 29.90),   -- look-alike CPF em texto livre
  ('NF-e série 000.000.000-01', 150.00);           -- numeração fiscal
```

#### Linhas de FN forçado (falso negativo)

```sql
-- Dado pessoal ofuscado ou fragmentado para testar limites
INSERT INTO clientes (campo_ofuscado) VALUES
  ('C*F: 123.4**.*89-0*'),      -- mascaramento parcial — detector deve encontrar?
  ('jose [at] email [dot] com'),  -- email em formato evasivo
  ('11 9 8765 4321');            -- telefone sem formatação
```

---

## 2. Matriz de arquivos por formato e variação

### 2.1 Tipos de arquivo a cobrir

| Extensão | Variações a gerar | Dados sensíveis incluídos |
|---|---|---|
| `.pdf` | normal, protegido com senha, compactado em .zip | CPF, RG, e-mail, data nascimento |
| `.docx` / `.doc` | normal, protegido, metadados com nome real | CPF, saúde, menor |
| `.xlsx` / `.xls` | normal, protegido, múltiplas abas | CPF, PAN, financeiro |
| `.csv` | delimitador `,` `;` `\t`, UTF-8 e Latin-1 | todos os tipos |
| `.txt` | plain text, log simulado | e-mail, IP, CPF inline |
| `.json` | flat e nested, array de objetos | e-mail, CPF, saúde |
| `.xml` | com namespaces, sem namespaces | CPF, RG, endereço |
| `.odt` / `.ods` | LibreOffice nativo | CPF, e-mail |
| `.pptx` | slides com tabela de dados | saúde, menor |
| `.eml` / `.msg` | e-mail simulado com anexo | CPF, RG, e-mail, IP |
| `.sqlite` | banco embutido em arquivo | todas as categorias |

### 2.2 Variações de compactação

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

## 3. Cloaking — arquivos disfarçados

> Cenário real: usuários renomeiam arquivos para burlar DLPs e controles de conformidade.

### 3.1 Tipos de cloaking a testar

| Arquivo real | Extensão falsa | Objetivo do teste |
|---|---|---|
| planilha Excel com CPF | `.mp3` | detector de tipo real vs extensão |
| PDF com RG | `.jpg` | conteúdo binário vs extensão |
| CSV com dados de saúde | `.txt` | trivial — extensão diferente mas legível |
| ZIP com PDFs | `.bak` | arquivo compactado disfarçado |
| SQLite com PII | `.db` → `.log` | banco embutido com extensão de log |
| DOCX com CPF | `.pdf` | formato Office disfarçado de PDF |
| Script Python com token hardcoded | `.txt` | segredo em arquivo texto |

### 3.2 Geração dos arquivos cloaked

```bash
# Copiar e renomear mantendo conteúdo original
cp clientes_com_cpf.xlsx musica_favorita.mp3
cp relatorio_medico.pdf foto_praia.jpg
cp planilha_saude.csv notas_reuniao.txt
cp backup_clientes.zip configuracao.bak
```

---

## 4. Dados de menores de idade (simulados)

> LGPD art. 14: dados de crianças e adolescentes requerem tratamento especialmente cuidadoso.

### 4.1 Regras do corpus

- **Nenhum dado real** — apenas nomes, CPFs e datas totalmente fictícios e marcados como sintéticos.
- Incluir campo `fonte: SINTETICO` em todos os registros.
- Datas de nascimento configuradas para idades 0–17 anos.

### 4.2 Cenários

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

## 5. Pseudo-anonimização e re-identificação

### 5.1 Técnicas a testar como entrada

| Técnica | O que gerar | Por que importa |
|---|---|---|
| **Supressão parcial** | `CPF: 123.***.***-**` | detector deve sinalizar campo, não apenas conteúdo |
| **Generalização** | `Faixa etária: 30-40` em vez de data exata | re-identificação por combinação |
| **Pseudonimização** com chave | `hash(CPF) = abc123def456` | sem a chave, dado parece não-PII |
| **k-Anonimato simulado** | grupo de 3+ registros com mesma faixa+CEP+gênero | risco de re-identificação combinatória |
| **Dados incompletos** | somente nome + bairro + profissão | re-identificação por inferência |

### 5.2 Dataset de re-identificação controlada

```csv
# pseudo_anon_sample.csv — para demonstrar risco ao cliente
id_hash,faixa_etaria,genero,cep_prefix,profissao,diagnostico
a1b2c3,30-35,M,24020,engenheiro,hipertensão
d4e5f6,30-35,M,24020,engenheiro,diabetes
# → k=2: combinação faixa+CEP+profissão já estreita muito a população
```

---

## 6. Limites de FP e FN — casos de borda

### 6.1 Falsos Positivos esperados (a mapear e documentar)

| Caso | Dado | Esperado | Resultado ideal |
|---|---|---|---|
| Numeração fiscal | `000.000.000-00` | FP (parece CPF) | config de whitelist |
| Código de produto | `987.654.321-X` | FP | whitelist por contexto |
| Coordenadas GPS | `-22.9068, -43.1729` | sem PII | não deve acionar |
| Número de pedido | `2024.001.000-5` | FP | ajuste de pattern |

### 6.2 Falsos Negativos esperados (a detectar como lacuna)

| Caso | Dado | Esperado | Risco |
|---|---|---|---|
| CPF sem formatação | `12345678900` | deve detectar | FN se só testa com pontuação |
| E-mail Unicode | `usuario@domínio.com.br` | deve detectar | encoding edge case |
| Telefone internacional | `+55 11 98765-4321` | deve detectar | pattern só doméstico |
| Nome próprio isolado | `Carlos Eduardo da Colleague-V` | depende de contexto | difícil sem ML |

---

## 7. Plano de execução

### Fase 0 — Scaffolding (1 sprint)

- [ ] Criar `docs/private/lab/synthetic-data-lab/` (gitignored).
- [ ] Criar `docker-compose.yml` conforme §1.1.
- [ ] Criar `scripts/lab/generate_synthetic_corpus.py` para gerar arquivos e dados sintéticos programaticamente.
- [ ] Criar `scripts/lab/start_lab_dbs.ps1` (wrapper PowerShell para `docker compose up -d`).

### Fase 1 — Corpus básico (1–2 sprints)

- [ ] Seed SQL para MariaDB e PostgreSQL com todas as categorias de §1.2.
- [ ] Arquivos de todos os formatos de §2.1 (versão simples — sem senha, sem compactação).
- [ ] Executar varredura Data Boar e registrar FP/FN baseline.

### Fase 2 — Variações avançadas (2–3 sprints)

- [ ] Arquivos protegidos por senha e compactados (§2.2).
- [ ] Cloaking matrix completa (§3).
- [ ] Dados de menores (§4).
- [ ] Oracle XE se licença for aceita em lab.

### Fase 3 — Pseudo-anonimização e re-identificação (1–2 sprints)

- [ ] Dataset pseudo-anon (§5).
- [ ] Relatório de risco de re-identificação gerado pelo Data Boar.
- [ ] Ajuste de thresholds e whitelist baseado em resultados.

### Fase 4 — Dados reais (com colaboradores — futuro)

- [ ] Receber dataset parcial / anonimizado de produção.
- [ ] Confirmar comportamento vs corpus sintético.
- [ ] Documentar delta e ajustes necessários.

---

## 9. Corpus de imagens sinteticas (novo -- para PLAN_IMAGE_SENSITIVE_DATA_DETECTION)

Esta secao e um satelite do `PLAN_IMAGE_SENSITIVE_DATA_DETECTION.pt_BR.md`: gera o corpus de imagens necessario para testar o scanner OCR antes de tocar dados reais.

### 9.1 Tipos de imagem a gerar

| Tipo                         | Ferramenta sugerida              | Conteudo fake                                    | Cenario de teste              |
|------------------------------|----------------------------------|--------------------------------------------------|-------------------------------|
| CPF impresso (A4 scan sim.)  | Pillow (texto sobre fundo branco)| CPF invalido formato valido (ex: 000.000.000-00) | Deteccao OCR tier 1           |
| RG (frente)                  | Pillow + layout basico           | Nome, RG, data nascimento ficticios              | Deteccao OCR + doc_type       |
| CNH (frente)                 | Pillow + layout basico           | Nome, CPF, validade ficticios                    | Deteccao OCR + doc_type       |
| Receita medica               | Pillow + texto medico ficticio   | Paciente, CRM, medicamento (ficticio)            | Dado de saude sensivel        |
| Extrato bancario sim.        | Pillow + tabela de lancamentos   | Agencia/conta ficticios, valores pequenos        | Dado financeiro               |
| Foto de rosto (avatar)       | Gerada por IA ou Pillow oval     | Rosto sem identidade real                        | Biometrico (Fase 5)           |
| Crianca (placeholder)        | Texto "[menor ficticio]"         | Sem foto real de crianca                         | LGPD Art. 14                  |
| Imagem corrompida            | Bytes aleatorios com magic bytes | N/A                                              | Robustez / timeout            |
| Imagem cloaked (.mp3, .docx) | Copia JPEG com extensao errada   | Qualquer imagem acima                            | Deteccao de cloaking          |
| Imagem sem PII               | Pillow paisagem / formas         | Sem dado pessoal                                 | Teste de falso positivo       |
| base64 de CPF-imagem em .txt | Script Python encode             | CPF ficticio em JPEG base64                      | Deteccao base64 em texto      |

### 9.2 Script de geracao

Criar `scripts/lab/generate_synthetic_images.py`:

- Gera imagens com `Pillow` para cada tipo acima.
- Salva em `docs/private/lab/images/` (gitignored).
- Gera manifesto `docs/private/lab/images/MANIFEST.json` com: tipo, arquivo, PII esperado, categoria LGPD, resultado esperado (TP/TN).
- Nunca usa fotos reais de pessoas; nunca usa CPF/RG/CNH reais.

### 9.3 BLOBs no banco sintetico

Extender os scripts de seed dos containers MariaDB/PostgreSQL/Oracle para:

- [ ] Coluna `foto_documento LONGBLOB` na tabela `clientes` com 3 a 5 imagens de RG ficticio.
- [ ] Coluna `attachment TEXT` com base64 de JPEG de CPF ficticio.
- [ ] Coluna `thumbnail BLOB` com imagem sem PII (teste de falso positivo).

### 9.4 PDFs scaneados (sem camada de texto)

- [ ] Gerar PDF onde cada pagina e uma imagem JPEG (nao PDF com texto nativo).
- [ ] Usar `reportlab` ou `img2pdf` para empacotar as imagens de CPF/RG.
- [ ] Salvar em `docs/private/lab/files/` ao lado dos demais arquivos sinteticos.

### 9.5 Guardrails especificos para corpus de imagem

- Nunca usar fotos reais de pessoas, mesmo que publicas (copyright + privacidade).
- Nunca usar documentos reais (escanear CPF/RG/CNH proprios para teste e proibido -- cria dado real em repositorio de teste).
- CPFs usados devem ser visivelmente invalidos (todos iguais, sequencias repetidas) ou com sufixo sintetico visivel na propria imagem.
- Imagens de "rosto" apenas com avatares gerados por IA ou formas geometricas.

---

## 8. Guardrails

- **Nunca commitar** dados sintéticos que contenham padrões confundíveis com dados reais de pessoas reais (ex.: CPFs de sequências intencionalmente inválidas, nomes claramente fictícios com sufixo "Fictício/Sintético").
- Manter corpus em `docs/private/lab/` (gitignored).
- Scripts de geração ficam em `scripts/lab/` — commitar scripts, **não** os dados gerados.
- Registrar resultados de varredura em `docs/private/lab/reports/` (gitignored) — nunca em issues/PRs públicos.

---

## Relacionados

- [TECH_GUIDE.pt_BR.md](../TECH_GUIDE.pt_BR.md) — matriz de conectores e formatos suportados.
- [PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md](PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md) — stack de observabilidade para o lab.
- [LAB_OP_MINIMAL_CONTAINER_STACK.pt_BR.md](../ops/LAB_OP_MINIMAL_CONTAINER_STACK.pt_BR.md) — containers base.
- [PLANS_TODO.md](PLANS_TODO.md) — priorização geral do projeto.

