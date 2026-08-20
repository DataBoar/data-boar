# Detecção de sensibilidade: termos de treino ML e DL

A aplicação usa um pipeline **híbrido** para classificar nomes de colunas e conteúdo amostrado como sensível ou não:

1. **Regex** – Padrões embutidos (CPF, CNPJ, e-mail, telefone, SSN, cartão de crédito, datas) mais overrides opcionais via arquivo de config.
1. **ML** – TF-IDF + RandomForest treinado em uma lista de termos **(texto, rótulo)** (sensível vs não sensível). Os termos vêm de arquivo ou da config inline. A floresta usa **`random_state` fixo** para confianças reproduzíveis entre execuções e instâncias do detector.
1. **DL (opcional)** – Embeddings de sentenças + um classificador pequeno treinado nos seus termos. Usado quando a dependência opcional `sentence-transformers` está instalada e você fornece termos DL (arquivo ou inline). A confiança é combinada com a do ML (ex.: `max(ml_confidence, dl_confidence)`).

Você pode **definir as palavras de treino para ML e DL** no arquivo de config principal (inline) ou em arquivos YAML/JSON separados.

**Não é LLM generativo:** Este caminho híbrido permanece **determinístico + supervisionado** — pontua **evidência já presente** na amostra; **não** chama um **modelo de linguagem grande** na nuvem para “explicar” o banco. Essa escolha mantém sessões **comparáveis** e alinha com **agregação de quasi-identificadores**, sinais de **menores** e heurísticas de **jurisdição** como **saídas estruturadas de relatório**, não prosa aberta. Veja [TECH_GUIDE.pt_BR.md](TECH_GUIDE.pt_BR.md#detection-stack-vs-generative-llms), [COMPLIANCE_FRAMEWORKS.pt_BR.md](COMPLIANCE_FRAMEWORKS.pt_BR.md#detecção-determinística-vs-hype-de-llm-generativo), [GLOSSARY.pt_BR.md](GLOSSARY.pt_BR.md) §8 e [docs/ops/LLM_AGENT_EDITING_CAUTION.pt_BR.md](ops/LLM_AGENT_EDITING_CAUTION.pt_BR.md).

**English:** [SENSITIVITY_DETECTION.md](SENSITIVITY_DETECTION.md)

**Detecção de dados de menores:** A aplicação pode sinalizar possíveis dados de menores (colunas de DOB/idade) e aplicar tratamento diferenciado nos relatórios (LGPD Art. 14, GDPR Art. 8). O limite de idade (padrão 18) é configurável no arquivo de config externo. Consulte [MINOR_DETECTION.pt_BR.md](MINOR_DETECTION.pt_BR.md) para configuração e ajuste fino.

**Risco de identificação agregada / cruzada:** Quando várias categorias de quasi-identificadores (ex.: gênero, cargo, saúde, endereço, telefone) aparecem na **mesma tabela ou arquivo**, o gerador de relatório sinaliza isso como **caso especial** para DPO e compliance (LGPD Art. 5, GDPR Recital 26 – identificabilidade pela combinação de dados). O relatório Excel inclui a aba **"Cross-ref data – ident. risk"** listando cada caso (alvo, tabela/arquivo, colunas envolvidas, categorias, explicação) e uma recomendação de alta prioridade. Isso é opcional e configurável via `detection.aggregated_identification_enabled`, `aggregated_min_categories` e `quasi_identifier_mapping`. Notas históricas de desenho: **`PLAN_AGGREGATED_IDENTIFICATION`** arquivado em `docs/plans/completed/` (mantenedores).

### Contexto embutido: letras, tablaturas, Markdown de projeto, `.txt` de letra, legendas, texto tipo OCR

O detector aplica tratamento de **entretenimento / documento de baixo risco de PII** (penalidade na confiança; ML só **HIGH** limitado a **MEDIUM** com padrões como `ML_POTENTIAL_ENTERTAINMENT`) quando:

- O conteúdo parece **letra de música** (palavras-chave ou muitas linhas curtas que **não** são sobretudo linhas CSV/TSV/ponto-e-vírgula), **tablatura** (linhas de dígitos/pipe que **não** são essas tabelas delimitadas), **grade de acordes** (incluindo **cifras** com vários acordes por linha) ou **cifra entrelaçada** (linhas de acorde alternando com linhas de letra; grafias podem misturar maiúsculas/minúsculas, ex.: `C`, `Am`, `EM7`, `D2sus9`).
- O caminho ou o conteúdo parecem **legenda ou transcrição** (ex.: `.srt` / `.vtt` / `.ass` / `.ssa`, ou padrões de *cue*/tempo após normalização). **Regex forte de PII** ainda gera **HIGH** (prioridade a não perder verdadeiros positivos).
- Texto vindo de **OCR de imagem** (`file_scan.scan_image_ocr`) costuma ser ruidoso; quando o markup é parecido com legenda, o teto do ML segue a mesma lógica de entretenimento. **Falsos positivos** ainda podem ocorrer em formulários ou placas fotografados — revisar no contexto.
- O **nome do arquivo** sugere **Markdown** típico de repositório aberto (`README`, `CONTRIBUTING`, `CODE_OF_CONDUCT`, `CHANGELOG`, `LICENSE`, `SECURITY`, `HISTORY`, …) **e** o corpo tem títulos Markdown (`#` / `##`). Se a **amostra for curta**, **um** título de nível superior e pelo menos **~60 caracteres** de corpo já bastam quando o *stem* bate com esses nomes OSS — o primeiro recorte não precisa de dois títulos. No filesystem, o orçamento de texto plano é **`file_scan.file_sample_max_chars`** (padrão 12 mil caracteres); **`sample_limit`** continua sendo o limite no estilo linhas/TOPN para bancos e colunas no modo SQLite como DB. **Na amostragem por coluna em SQL (SQLAlchemy) e Snowflake**, usa-se `WHERE <coluna> IS NOT NULL` antes desse teto, para colunas esparsas ainda alimentarem o detector quando houver valor não nulo (ver [USAGE.md](USAGE.md)).
- O arquivo é **`.txt`** com várias linhas de **tamanho médio curto** (estrofes sem cabeçalhos explícitos `Verse` / `Chorus`).
- O **nome base** traz **acorde entre parênteses** (ex.: `Rosa(D).txt`), indicando cifra.

**Regex forte** (CPF, e-mail, cartão, …) ainda produz **HIGH** quando aplicável. Subir **`medium_confidence_threshold`** afeta sobretudo a faixa MEDIUM; o limite padrão **70** para ML só **HIGH** não muda — essas heurísticas atacam **HIGH** falso em clones de repo e bibliotecas de música no filesystem.

### Padrões genéricos de dígitos e escopo de falso positivo

Regex regionais opcionais em **amostras de compliance** (ex.: **CEP_BR**, **DNI_AR**) costumam usar **formatos numéricos curtos** que também aparecem em SKUs, IDs internos, contadores e linhas. Espere **muitos falsos positivos** em texto amplo ou catálogos; revise no contexto e aperte overrides para produção. O contexto **entretenimento** trata alguns padrões como mais fracos (veja `WEAK_PATTERNS_IN_ENTERTAINMENT` no detector). Lembre-se de **mesclar** `recommendation_overrides` das amostras na config para a aba **Recomendações** refletir texto por framework — veja [USAGE.pt_BR.md](USAGE.pt_BR.md) (checklist de amostras).

| Classe de padrão | Risco típico | Mitigação do operador |
| --- | --- | --- |
| Sequências tipo CEP/DNI | Batem em códigos não-PII | Revisão por coluna/contexto; regex mais estrita |
| `\d{n,m}` amplo no YAML | Inundação de alertas | Sobrescrever padrão; desativar o nome do padrão se não usar |

---

## Formatos de CNPJ (Brasil): numérico legado e alfanumérico

O **CNPJ** (Cadastro Nacional da Pessoa Jurídica) é o identificador fiscal de empresas. Dois formatos são relevantes:

## Legado (apenas numérico):

- 14 dígitos, opcionalmente formatados como `XX.XXX.XXX/XXXX-XX` (pontos, barra, hífen). Continua válido; não há migração obrigatória.

## Alfanumérico (formato oficial atual):

- Definido pela **Instrução Normativa RFB nº 2.229/2024** (Receita Federal). Mesmo comprimento de 14 caracteres; pontuação de exibição inalterada (`XX.XXX.XXX/XXXX-XX`).
- **Posições 1–8 (raiz):** alfanumérico `0–9`, `A–Z` (maiúsculas).
- **Posições 9–12 (ordem de inscrição):** alfanumérico `0–9`, `A–Z`.
- **Posições 13–14 (dígitos verificadores):** apenas numérico `0–9`.
- Novos registros de empresas receberão CNPJs alfanuméricos a partir de **julho de 2026**; CNPJs numéricos existentes permanecem válidos.

O projeto suporta os dois formatos. A detecção alfanumérica é **opt-in** para não alterar o comportamento atual:

- `LGPD_CNPJ` – formato legado, apenas numérico (sempre ativo).
- `LGPD_CNPJ_ALNUM` – formato alfanumérico conforme IN RFB 2.229/2024 (12 primeiras posições `[0-9A-Z]`, duas últimas dígitos). Ativo quando:
- `detection.cnpj_alphanumeric: true` está definido no config, ou
- um override para `LGPD_CNPJ_ALNUM` é adicionado via `regex_overrides_file`.

Ambos os padrões usam o mesmo `norm_tag` (`LGPD Art. 5`). O detector faz apenas **compatibilidade de formato** (regex); **validação de dígito verificador** (ex.: Módulo 11 no alfanumérico) fica para uma fase futura do detector. Se seu setor usar variante (ex.: letras minúsculas), ajuste o regex no seu override.

---

## Tipo de conteúdo e disfarce simples de extensão

**Disfarce simples** (no sentido deste produto) é quando a **extensão do nome** sugere um formato e os **magic bytes** no início do arquivo apontam para outro. Fluxos que confiam **só** na extensão podem tratar o arquivo errado; a inferência opcional pelo **conteúdo** (primeiros bytes) reduz esse gap.

A partir da versão 1.6.0+:

- **Helpers:** `infer_content_type(path_or_bytes)` e lógica relacionada em `core/content_type.py` / `core/rich_media_magic.py` usam **magic bytes e heurísticas simples** para inferir rótulo grosseiro (ex.: `pdf`, `zip`, `text`) ou remapear tipos de mídia rica. Exemplos: bytes de PDF com nome `.txt` **ou** extensão **não textual** como `.mp3` — se for PDF, o cabeçalho segue `%PDF-...`.
- **Ligação opt-in:** Com **`file_scan.use_content_type`** `true`, ou **`--content-type-check`** / dashboard / API numa execução, os conectores de **filesystem** e **compartilhamento** usam esses helpers para que a extensão enganosa **não** seja o único critério de extração (recorte PDF + remapeamento de mídia rica onde existir), ao custo de uma leitura extra por arquivo. O padrão continua sendo por extensão. Veja [USAGE.pt_BR.md](USAGE.pt_BR.md) (`file_scan`, **`use_content_type`**) e [TECH_GUIDE.pt_BR.md](TECH_GUIDE.pt_BR.md).
- **Roadmap mais amplo:** evasões mais elaboradas e detecção estilo esteganografia ficam em planos separados; notas de desenho: **`PLAN_CONTENT_TYPE_AND_CLOAKING_DETECTION`** em `docs/plans/`.

## Chaves de config

| Chave | Descrição |
| --- | --- |
| `ml_patterns_file` | Caminho para arquivo YAML/JSON com termos de treino ML (lista de `{ text, label }`). Usado quando `sensitivity_detection.ml_terms` não está definido. |
| `dl_patterns_file` | Caminho para arquivo YAML/JSON com termos de treino DL (mesmo formato). Usado quando `sensitivity_detection.dl_terms` não está definido. |
| `sensitivity_detection` | Seção opcional com termos inline (dispensa arquivo separado). |
| `sensitivity_detection.ml_terms` | Lista de `{ text: string, label }` com **label** `"sensitive"` ou `"non_sensitive"`. Substitui/complementa `ml_patterns_file` quando não vazia. |
| `sensitivity_detection.dl_terms` | Mesmo formato que **ml_terms** no caminho DL. Substitui/complementa `dl_patterns_file` quando não vazia. |
| `sensitivity_detection.medium_confidence_threshold` | Inteiro **1–69**, padrão **40**. Confiança mínima combinada ML/DL (0–100) para **MEDIUM** sem regex forte. **HIGH** continua em 70. Valores menores expõem mais casos limítrofes (prioridade a reduzir falsos negativos). |
| `sensitivity_detection.column_name_normalize_for_ml` | Booleano, padrão **false**. Se **true**, **remove acentos** e **normaliza separadores** só no nome da coluna **para entrada ML/DL** (regex e heurísticas menores continuam com o nome bruto). Reduz FN em nomes como `téléphone` vs termo `telefone`. |
| `sensitivity_detection.fuzzy_column_match` | Booleano, padrão **false**. Se **true** e **`rapidfuzz`** instalado (`pip install .[detection-fuzzy]` ou `uv sync --group dev`), compara o nome da coluna aos termos **sensíveis** ML/DL. Sem regex, com confiança ML/DL na faixa **abaixo** do limiar MEDIUM e similaridade ≥ `fuzzy_column_match_min_ratio`, retorna **MEDIUM** com `FUZZY_COLUMN_MATCH`. **Desligado por padrão.** |
| `sensitivity_detection.fuzzy_column_match_min_confidence` | Inteiro **0–100**, padrão **25**. Piso da faixa de confiança (inclusivo). |
| `sensitivity_detection.fuzzy_column_match_max_confidence` | Inteiro **0–100**, padrão **45**. Teto efetivo = `min(valor, medium_confidence_threshold - 1)` para não alterar MEDIUM normal por ML/DL. |
| `sensitivity_detection.fuzzy_column_match_min_ratio` | Inteiro **50–100**, padrão **85**. Score mínimo `rapidfuzz` (máx. entre ratio / partial_ratio / token_set_ratio) vs um termo sensível. |
| `sensitivity_detection.embedding_prototype_hint` | Booleano, padrão **false**. Dica semântica opcional do Plano §5: quando o backend DL estiver pronto, sem regex e com confiança combinada numa faixa limítrofe abaixo de MEDIUM, alta similaridade com o protótipo de embeddings sensíveis pode elevar para **MEDIUM** com `pattern_detected` **`EMBEDDING_PROTOTYPE_HINT`**. |
| `sensitivity_detection.embedding_prototype_hint_min_confidence` | Inteiro **0–100**, padrão **20**. Piso da faixa de confiança da dica de protótipo. |
| `sensitivity_detection.embedding_prototype_hint_max_confidence` | Inteiro **0–100**, padrão **39**. Teto da faixa; limite efetivo = `medium_confidence_threshold - 1`. |
| `sensitivity_detection.embedding_prototype_hint_min_similarity` | Inteiro **50–100**, padrão **80**. Similaridade cosseno mínima (0–100) entre embedding da coluna/amostra e protótipo de termos sensíveis. |
| `sensitivity_detection.connector_format_id_hint` | Booleano, padrão **false**. Se **true**, os conectores passam tipos SQL declarados (ex.: `VARCHAR(11)`, `BIGINT`) ao detector. Sem regex e com confiança ML/DL **abaixo** do limiar MEDIUM, dicas conservadoras de schema podem elevar para **MEDIUM**: **(a)** tamanhos `CHAR`/`VARCHAR` ID-like → `FORMAT_LENGTH_HINT_ID` (comprimentos de dígitos **CPF/CNPJ/SSN**; tipo **UUID** **32** / **36** quando o nome da coluna contém `uuid`, `guid` ou `uniqueidentifier`); **(b)** tipos inteiros (`INT`, `BIGINT`, `NUMERIC(...,0)`) com nomes ID-like → `FORMAT_TYPE_HINT_ID_INT`; **(c)** tamanhos típicos de e-mail (`128/191/254/255/256/320`) com nomes de e-mail (`email`, `e_mail`, `mail`) → `FORMAT_LENGTH_HINT_EMAIL`. O conector **REST/API** infere `VARCHAR(n)` / `BIGINT` a partir de amostras escalares JSON quando possível. **Desligado por padrão.** Ver `tests/test_format_length_hint.py`, `tests/test_rest_connector_format_hint.py` e o plano §4 em `PLAN_ADDITIONAL_DETECTION_TECHNIQUES_AND_FN_REDUCTION.md`. |
| `detection.persist_low_id_like_for_review` | Booleano, padrão **false**. Se **true**, **conectores estilo banco** (SQL, Snowflake, MongoDB, Redis, Dataverse, Power BI, chaves JSON em REST) podem persistir colunas **LOW** com nome de identificador (`*_id`, `*_uuid`, `*_number`, etc.; ver `core.suggested_review`) com padrão `SUGGESTED_REVIEW_ID_LIKE` na aba **Suggested review (LOW)**. |
| `report.include_suggested_review_sheet` | Booleano, padrão **true**. Se **true**, achados `SUGGESTED_REVIEW_ID_LIKE` vão para **Suggested review (LOW)** e **são removidos** das abas Database/Filesystem para não duplicar. **false** mantém só nas abas principais. |

**Valores de label:** `sensitive` ou `1` = sensível (dados pessoais/PII); `non_sensitive` ou `0` = não sensível.

### Revisão sugerida (LOW) e limiar MEDIUM (redução de FN)

1. Reduza `sensitivity_detection.medium_confidence_threshold` (ex.: **35**) para que scores limítrofes ML/DL virem **MEDIUM** em vez de **LOW**.
1. Ative `detection.persist_low_id_like_for_review: true` em alvos de banco para persistir colunas identificadoras que continuem **LOW** e listá-las em **Suggested review (LOW)**.

Detalhes: opções do detector neste guia e em [TECH_GUIDE.pt_BR.md](TECH_GUIDE.pt_BR.md); backlog estendido: **`PLAN_ADDITIONAL_DETECTION_TECHNIQUES_AND_FN_REDUCTION`** em `docs/plans/` (mantenedores).

#### Por que “Suggested review” precisa de `persist_low_id_like_for_review: true` (ou fixtures)

Por padrão os conectores **não gravam** achados **LOW** (menos ruído no SQLite/relatório). **Suggested review** continua sendo **LOW**; só muda o `pattern_detected` para o Excel listar na aba dedicada. Por isso a aba só enche se:

- **`detection.persist_low_id_like_for_review: true`**, ou
- testes/inserções manuais (fixtures).

#### Limiar MEDIUM **vs** flag de persistência (postura FN-first)

| Opção                                              | Efeito                                                                                                  |
| -------                                            | --------                                                                                                |
| **Reduzir `medium_confidence_threshold`** (ex. 35) | Mais casos viram **MEDIUM** e entram nas abas principais; mais revisão humana ampla.                    |
| **`persist_low_id_like_for_review: true`**         | Só nomes **ID-like** ainda **LOW** viram linhas na aba **Suggested review**; não alarga a faixa MEDIUM. |

Em ambientes com **alto custo de FN regulatório**, combinar **limiar um pouco mais baixo** e/ou **persist ID-like** é coerente com “preferir falso positivo + confirmação humana”. Padrões permanecem conservadores.

---

## Formato do arquivo (YAML ou JSON)

Tanto `ml_patterns_file` quanto `dl_patterns_file` usam a mesma estrutura. Você pode apontar ambos para o mesmo arquivo se quiser que ML e DL usem os mesmos termos.

## Exemplo YAML

```yaml
# Lista de termos; cada um tem "text" e "label"
- text: "cpf"

  label: sensitive

- text: "email"

  label: sensitive

- text: "data de nascimento"

  label: sensitive

- text: "senha"

  label: sensitive

- text: "item_count"

  label: non_sensitive

- text: "config_file"

  label: non_sensitive
```

**Chave alternativa:** alguns configs usam `patterns` ou `terms` como chave raiz:

```yaml
patterns:

- text: "cpf"

    label: sensitive

- text: "email"

    label: sensitive

- text: "system_log"

    label: non_sensitive
```

## Exemplo JSON

```json
[
  { "text": "cpf", "label": "sensitive" },
  { "text": "email", "label": "sensitive" },
  { "text": "item_count", "label": "non_sensitive" }
]
```

---

## Identificação agregada: configuração e exemplos

Quando a **identificação agregada** está habilitada, o gerador de relatório agrupa achados por tabela (banco) ou arquivo (sistema de arquivos) e sinaliza casos em que **várias categorias de quasi-identificadores** (ex.: gênero, cargo, saúde, endereço, telefone) aparecem juntas, o que pode permitir reidentificação (LGPD Art. 5, GDPR Recital 26). O relatório Excel ganha a aba **"Cross-ref data – ident. risk"** e uma recomendação de alta prioridade.

| Chave                                                    | Tipo    | Padrão    | Descrição                                                                                                                                                                                                                                                                                             |
| ---                                                      | ---     | ---       | ---                                                                                                                                                                                                                                                                                                   |
| `detection.aggregated_identification_enabled`            | boolean | **true**  | Defina como `false` para desativar a agregação e a aba Cross-ref.                                                                                                                                                                                                                                     |
| `detection.aggregated_min_categories`                    | inteiro | **2**     | Número mínimo de categorias distintas de quasi-identificadores em uma tabela/arquivo para sinalizar (ex.: 3 para mais rigor).                                                                                                                                                                         |
| `detection.aggregated_incomplete_data_mode`              | boolean | **false** | Modo opcional C10 para cobertura parcial: reduz o limiar efetivo de agregação em **1** (mínimo 1) e marca a explicação como orientada a dados incompletos; aumenta recall/linhas de revisão sugerida.                                                                                                 |
| `detection.aggregated_single_high_risk_suggested_review` | boolean | **false** | Modo opcional C11: se só uma categoria for detectada mas ela for de alto risco (**health**), ainda gera linha agregada como **MEDIUM suggested review** (em vez de descartar).                                                                                                                        |
| `detection.quasi_identifier_mapping`                     | lista   | **[]**    | Lista opcional de `{ column_pattern, category }` ou `{ pattern_detected, category }` para mapear colunas/padrões para `gender`, `job_position`, `health`, `address`, `phone`, `other`. Já existem mapeamentos padrão para nomes comuns (ex.: gender, sex, cargo, department, health, address, phone). |

### Tabela de decisão dos modos agregados (guia rápido para operação)

| Cenário                                                                                | Opções recomendadas                                                                                  | Motivo                                                                                      |
| ---                                                                                    | ---                                                                                                  | ---                                                                                         |
| Scans com cobertura completa, equilíbrio entre ruído e recall                          | Manter padrões (`aggregated_min_categories: 2`, modos opcionais `false`)                             | Linha de base conservadora, comportamento estável e menos linhas de revisão sugerida.       |
| Scans parciais/incrementais (amostras, janelas reduzidas)                              | Ativar `aggregated_incomplete_data_mode: true` e manter `aggregated_min_categories`                  | O limiar efetivo cai em 1 (mínimo 1), aumentando recall quando a cobertura está incompleta. |
| Domínios de alto arrependimento (dados de saúde) com baixa tolerância a alerta perdido | Ativar `aggregated_single_high_risk_suggested_review: true` (opcionalmente junto ao modo incompleto) | Sinaliza categoria única de saúde como MEDIUM suggested review em vez de descartar.         |
| Ruído alto de revisão após ativar modos opcionais                                      | Desligar primeiro um modo opcional (normalmente single-high-risk) e reavaliar                        | Controla carga de triagem mantendo suporte a cobertura parcial.                             |

Ambos os modos opcionais são opt-in e foram pensados para revisão humana no loop.

## Exemplo: habilitar com mapeamento customizado e mínimo de 3 categorias

```yaml
# config.yaml
targets: []
report:
  output_dir: ./reports
detection:
  aggregated_identification_enabled: true
  aggregated_min_categories: 3
  quasi_identifier_mapping:

    - { column_pattern: "cargo", category: job_position }
    - { column_pattern: "departamento", category: job_position }
    - { pattern_detected: "PHONE_BR", category: phone }
    - { pattern_detected: "EMAIL", category: other }

```

**Como usar:** Execute um scan (CLI: `python main.py --config config.yaml` ou API: iniciar scan pelo dashboard). Em seguida gere o relatório (CLI: o relatório é gerado ao final do scan; API: baixe pela sessão). Se alguma tabela ou arquivo tiver pelo menos `aggregated_min_categories` categorias presentes, o relatório incluirá a aba **"Cross-ref data – ident. risk"** e uma linha de recomendação **AGGREGATED_IDENTIFICATION**.

**Para desativar:** Defina `detection.aggregated_identification_enabled: false` no config; a aba Cross-ref e a recomendação agregada não serão geradas.

**Guia prático para operação:** [ops/AGGREGATED_IDENTIFICATION_TUNING.md](ops/AGGREGATED_IDENTIFICATION_TUNING.md) (pt-BR: [ops/AGGREGATED_IDENTIFICATION_TUNING.pt_BR.md](ops/AGGREGATED_IDENTIFICATION_TUNING.pt_BR.md)).

### Pacote rápido de toggles (discoverability)

```yaml
# config.yaml
detection:
  aggregated_identification_enabled: true
  aggregated_min_categories: 2
  aggregated_incomplete_data_mode: false
  aggregated_single_high_risk_suggested_review: false

sensitivity_detection:
  embedding_prototype_hint: false
  embedding_prototype_hint_min_confidence: 20
  embedding_prototype_hint_max_confidence: 39
  embedding_prototype_hint_min_similarity: 80
```

Use este bloco como linha de base e depois ajuste por alvo usando o guia prático de operação.

---

## Termos inline no config principal

Você pode definir os termos de treino ML e DL diretamente no seu `config.yaml` (ou JSON) principal, na seção `sensitivity_detection`, sem arquivos separados.

## Exemplo: termos ML e DL inline

```yaml
# config.yaml
targets: []
file_scan:
  extensions: [.txt, .csv, .pdf]
  recursive: true
report:
  output_dir: .

# Termos de treino para sensibilidade (ML = TF-IDF + RandomForest; DL = embeddings + classificador quando .[dl] instalado)
sensitivity_detection:
  ml_terms:

    - { text: "cpf", label: sensitive }
    - { text: "email", label: sensitive }
    - { text: "senha", label: sensitive }
    - { text: "data de nascimento", label: sensitive }
    - { text: "item_count", label: non_sensitive }
    - { text: "system_log", label: non_sensitive }

  dl_terms:

    - { text: "customer name", label: sensitive }
    - { text: "health record", label: sensitive }
    - { text: "salary", label: sensitive }
    - { text: "internal id", label: non_sensitive }
    - { text: "cache key", label: non_sensitive }

```

Se você definir **apenas** `ml_terms` (ou apenas `dl_terms`), o outro continua usando arquivo ou padrões embutidos: o ML usa `ml_patterns_file` ou termos embutidos quando `ml_terms` está vazio; o DL só é usado quando `dl_terms` ou `dl_patterns_file` é fornecido e o pacote opcional `sentence-transformers` está instalado.

---

## Usando apenas arquivos (sem inline)

```yaml
# config.yaml
ml_patterns_file: config/ml_terms.yaml
dl_patterns_file: config/dl_terms.yaml
# ... resto do config
```

Ou use o mesmo arquivo para os dois:

```yaml
ml_patterns_file: config/sensitivity_terms.yaml
dl_patterns_file: config/sensitivity_terms.yaml
```

---

## Habilitando o backend DL

A etapa DL usa **embeddings de sentenças** (ex.: `sentence-transformers/all-MiniLM-L6-v2`) e treina um classificador pequeno nos seus termos DL na inicialização. Instale a dependência opcional:

```bash
uv pip install -e ".[dl]"
# ou
pip install -e ".[dl]"
```

Isso instala o `sentence-transformers` (e suas dependências). Se `.[dl]` não estiver instalado, o pipeline continua rodando com **regex + ML**; a etapa DL é ignorada e a confiança vem apenas do ML.

---

## Exemplo: arquivo de termos compartilhado

Crie por exemplo `config/sensitivity_terms.yaml` (ou copie de [sensitivity_terms.example.yaml](sensitivity_terms.example.yaml)):

```yaml

- text: "cpf"

  label: sensitive

- text: "cnpj"

  label: sensitive

- text: "email"

  label: sensitive

- text: "telefone"

  label: sensitive

- text: "data de nascimento"

  label: sensitive

- text: "nome completo"

  label: sensitive

- text: "senha"

  label: sensitive

- text: "salário"

  label: sensitive

- text: "health record"

  label: sensitive

- text: "item_count"

  label: non_sensitive

- text: "config_file"

  label: non_sensitive

- text: "temp_data"

  label: non_sensitive

- text: "lyrics"

  label: non_sensitive

- text: "tablature"

  label: non_sensitive
```

Referencie no config:

```yaml
ml_patterns_file: config/sensitivity_terms.yaml
dl_patterns_file: config/sensitivity_terms.yaml
```

---

## Categorias sensíveis (saúde, religião, política, etc.)

A aplicação já inclui um **subconjunto** dessas categorias nos termos ML de fábrica (DEFAULT_ML_TERMS em `core/detector.py`), de modo que a detecção imediata inclui, por exemplo, religião, filiação política, gênero, biométrico, genético, raça, sindicato, PEP e vida sexual. Para detectar **mais dados pessoais sensíveis** (LGPD Art. 5 II, 11; GDPR Art. 9)—como CID/ICD (códigos de diagnóstico), gênero, religião, filiação política, PEP, raça/cor da pele, filiação sindical, dados genéticos/biométricos, vida sexual, saúde/deficiência—adicione ou estenda termos de treino via `ml_patterns_file` / `dl_patterns_file` ou `sensitivity_detection.ml_terms` / `sensitivity_detection.dl_terms`.

- **Tabela de categorias (plano histórico):** **`PLAN_SENSITIVE_CATEGORIES_ML_DL`** em `docs/plans/completed/` (mantenedores)
- **Arquivo de exemplo pronto para uso:** [sensitivity_terms_sensitive_categories.example.yaml](sensitivity_terms_sensitive_categories.example.yaml)

Copie esse arquivo (ou mescle suas entradas) em `ml_patterns_file` / `dl_patterns_file`, ou em `sensitivity_detection.ml_terms` / `sensitivity_detection.dl_terms`. Você pode usar `report.recommendation_overrides` para que achados nessas categorias tenham a Base legal, Risco e Prioridade corretos no relatório. Exemplo completo (saúde, religião, política, PEP, raça, sindicato, genético, biométrico, vida sexual) em [USAGE.pt_BR.md](USAGE.pt_BR.md) (Notas sobre configuração); [USAGE.md](USAGE.md) (English).

---

## Padrões regex customizados (detectar novos dados pessoais/sensíveis)

O detector aplica **padrões regex** ao texto combinado (nome da coluna + amostra do conteúdo). Os padrões embutidos cobrem CPF, CNPJ, e-mail, telefone, SSN, cartão de crédito e datas. Para que a aplicação se atente a **novos valores possivelmente pessoais ou sensíveis** (ex.: RG, placa de veículo, número de plano de saúde, outros IDs por país), você adiciona **padrões customizados** via um arquivo e aponta o config para ele.

### Onde configurar

No arquivo de config principal (`config.yaml` ou JSON), defina a chave **`regex_overrides_file`** com o caminho de um arquivo YAML ou JSON que lista seus padrões. O caminho pode ser absoluto ou relativo ao diretório de trabalho do processo. A aplicação carrega esse arquivo na inicialização e **mescla** seus padrões aos embutidos (nomes iguais aos embutidos são sobrescritos pelos seus).

```yaml
# config.yaml
regex_overrides_file: config/regex_overrides.yaml
# ... resto do config (targets, file_scan, report, etc.)
```

Prefira a chave **unificada** quando também enviar termos ML/DL no mesmo arquivo:

```yaml
# config.yaml
patterns_plugin_file: config/my_patterns.yaml
```

`patterns_plugin_file` prevalece sobre a chave legada na **mesma seção**. Contrato do autor (schema, ReDoS, o que o YAML não pode fazer): [PLUGIN_AUTHOR_GUIDE.pt_BR.md](PLUGIN_AUTHOR_GUIDE.pt_BR.md) ([EN](PLUGIN_AUTHOR_GUIDE.md)).

Se `regex_overrides_file` (e `patterns_plugin_file`) forem omitidos ou o arquivo não existir, apenas os padrões embutidos são usados.

### Formato do arquivo

O arquivo deve conter uma **lista de objetos**, cada um com:

| Campo      | Obrigatório | Descrição                                                                                                                                                                                                                                                                                                                                             |
| ---        | ---         | ---                                                                                                                                                                                                                                                                                                                                                   |
| `name`     | Sim         | Identificador curto do padrão (ex.: `RG_BR`, `PLATE_BR`). Aparece nos relatórios como `pattern_detected`.                                                                                                                                                                                                                                             |
| `pattern`  | Sim         | Expressão regular (sintaxe Python `re`). É aplicada ao nome da coluna + amostra. Use strings cruas; prefira `\b` para limites de palavra.                                                                                                                                                                                                             |
| `norm_tag` | Não         | Rótulo para conformidade/relatório (ex.: `LGPD Art. 5`, `Custom`). Padrão: `"Custom"`. Você pode definir qualquer rótulo de framework (ex.: "UK GDPR", "PIPEDA s. 2", "APPI", "POPIA") para os achados aparecerem sob essa norma nos relatórios e recomendações; veja [Frameworks de conformidade e extensibilidade](COMPLIANCE_FRAMEWORKS.pt_BR.md). |

Você pode usar uma lista na raiz ou uma chave `patterns` ou `regex` com a lista. Você pode copiar de [regex_overrides.example.yaml](regex_overrides.example.yaml) e editar. Use YAML em **aspas duplas** para os valores de `pattern` com **barras invertidas escapadas** (ex.: `"\\b\\d{5}"`) para que linters e loaders não reportem sequências de escape inválidas; veja `.cursor/rules/yaml-regex-patterns.mdc`.

## Exemplo YAML (regex overrides)

```yaml
# config/regex_overrides.yaml
- name: "RG_BR"

  pattern: "\\b\\d{1,2}\\.?\\d{3}\\.?\\d{3}-?[0-9Xx]\\b"
  norm_tag: "LGPD Art. 5"

- name: "PLATE_BR"

  pattern: "\\b[A-Z]{3}-?\\d{4}\\b"
  norm_tag: "Personal data context"

- name: "HEALTH_PLAN_ID"

  pattern: "\\b\\d{6,14}\\b"
  norm_tag: "Health/insurance context"

# Exemplo: padrão de CNPJ alfanumérico (mesma estrutura do LGPD_CNPJ_ALNUM embutido).

- name: "LGPD_CNPJ_ALNUM"

  pattern: "\\b[A-Z0-9]{2}\\.?[A-Z0-9]{3}\\.?[A-Z0-9]{3}/?[A-Z0-9]{4}-?\\d{2}\\b"
  norm_tag: "LGPD Art. 5"
```

## Exemplo JSON (regex overrides)

```json
[
  { "name": "RG_BR", "pattern": "\\b\\d{1,2}\\.?\\d{3}\\.?\\d{3}-?[0-9Xx]\\b", "norm_tag": "LGPD Art. 5" },
  { "name": "PLATE_BR", "pattern": "\\b[A-Z]{3}-?\\d{4}\\b", "norm_tag": "Personal data context" }
]
```

### Padrões embutidos (referência)

A aplicação já inclui estes padrões; não é preciso redefini-los a menos que queira alterar o regex ou o norm tag.

| Nome          | Descrição                                          | Norm tag              |
| ---           | ---                                                | ---                   |
| `LGPD_CPF`    | CPF brasileiro (11 dígitos, opcional pontos/traço) | LGPD Art. 5           |
| `LGPD_CNPJ`   | CNPJ brasileiro (14 dígitos, formatação opcional)  | LGPD Art. 5           |
| `EMAIL`       | Endereço de e-mail                                 | GDPR Art. 4(1)        |
| `CREDIT_CARD` | Cartão 16 dígitos (espaços/traços opcionais)       | PCI/GLBA              |
| `PHONE_BR`    | Telefone BR (+55 opcional, DDD obrigatório)        | LGPD Art. 5           |
| `CCPA_SSN`    | SSN EUA (XXX-XX-XXXX)                              | CCPA                  |
| `DATE_DMY`    | Data d/m/a (ex.: 31/12/2024)                       | Personal data context |

**Dígitos verificadores do CPF (opcional):** a validação **Módulo 11** para valores que já coincidem com a *forma* ``LGPD_CPF`` está em ``core.brazilian_cpf`` (``cpf_checksum_valid``, ``normalize_cpf_digits``, ``PIIValidator``) para contratos de laboratório, relatórios personalizados ou *hooks* futuros do *pipeline*. Mantenha ``CPF_SHAPE_PATTERN`` nesse módulo **idêntico** ao *regex* ``LGPD_CPF`` em ``core.detector.DEFAULT_PATTERNS``. Só o *match* por regex **não** prova os dígitos verificadores.

### Exemplos de padrões adicionais úteis

- **RG (Brasil):** formato varia por estado; uma forma comum é dígitos com pontos opcionais e dígito ou X no final:

  `\b\d{1,2}\.?\d{3}\.?\d{3}-?[0-9Xx]\b`

- **Placa de veículo Brasil (antiga):** `AAA-9999`:

  `\b[A-Z]{3}-?\d{4}\b`

- **Placa Mercosul:** `AAA9A99`:

  `\b[A-Z]{3}\d[A-Z]\d{2}\b`

- **ID numérico genérico (ex. plano de saúde):** cuidado com o tamanho para evitar falsos positivos; ex. 8–14 dígitos:

  `\b\d{8,14}\b` (use só quando o contexto for adequado; combine com ML/DL se possível).

- **Telefone EUA:** `(XXX) XXX-XXXX` ou `XXX-XXX-XXXX`:

  `\b\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b`

- **CEP (Brasil):** `99999-999`:

  `\b\d{5}-?\d{3}\b`

  **Precisão:** O mesmo formato casa com muitos valores que **não** são CEP (SKU de produto, IDs internos, códigos em planilhas). Trate o match como **indício de formato**, não como prova de endereço; revise achados em exportações de catálogo/estoque. Em contexto de **letras/cifras/tablatura**, `CEP_BR` é tratado como padrão fraco (como datas/telefone), ver `WEAK_PATTERNS_IN_ENTERTAINMENT` em `core/detector.py`. Regras mais estritas (ex.: exigir a palavra “CEP” ou coluna `cep`) não vêm habilitadas por padrão no motor genérico de regex.

Quando um padrão customizado der match no nome da coluna ou no texto amostrado, o achado é reportado com sensibilidade **HIGH** (ou MEDIUM em contexto de letras/cifras para padrões fracos), com `pattern_detected` igual ao seu `name` e `norm_tag` no relatório.

### Resumo

- **Configurar:** Defina `regex_overrides_file` no config principal com o caminho do seu arquivo YAML/JSON.
- **Formato:** Lista de `{ name, pattern, norm_tag }`; `norm_tag` opcional (padrão `"Custom"`).
- **Efeito:** Seus padrões são mesclados aos embutidos; qualquer match em (nome da coluna + amostra) é sinalizado. Use padrões precisos e limites de palavra para reduzir falsos positivos.
- **ML/DL:** Para contexto (ex.: “este nome de coluna sugere PII”), use os [termos de treino ML/DL](#chaves-de-config) além do regex.

---

## Resumo do documento

- **Termos ML:** De `sensitivity_detection.ml_terms` (inline) ou `ml_patterns_file`. Usados pelo classificador TF-IDF + RandomForest.
- **Termos DL:** De `sensitivity_detection.dl_terms` (inline) ou `dl_patterns_file`. Usados pelo opcional embedding + classificador quando `.[dl]` está instalado.
- **Mesmo formato:** Ambos usam uma lista de `{ text, label }` com `label` = `sensitive` ou `non_sensitive` (ou `1` / `0`).
- **Inline sobrescreve arquivo:** Quando `ml_terms` ou `dl_terms` estão preenchidos no config, eles são usados no lugar do carregamento do arquivo correspondente.

**Padrões regex:** Use `regex_overrides_file` no config principal para adicionar ou sobrescrever padrões de detecção por valor (veja [Padrões regex customizados](#padrões-regex-customizados-detectar-novos-dados-pessoaissensíveis) acima).

**Índice da documentação** (todos os tópicos, ambos os idiomas): [README.md](README.md) · [README.pt_BR.md](README.pt_BR.md).
