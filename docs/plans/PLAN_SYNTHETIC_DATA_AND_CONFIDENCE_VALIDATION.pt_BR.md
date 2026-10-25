# Plano: Fontes sintéticas e true-like, score de confiança e orientação ao operador

<!-- plans-hub-summary: Fixtures sintéticas + harness F1 (#835); v1.8.0 #1060 eval composto (F1 + latência + throughput + risco de re-id em eixos separados; sem score único) -->
<!-- plans-hub-related: PLAN_SYNTHETIC_DATA_LAB.pt_BR.md, PLAN_BENCHMARK_SAFE_AXIS.md, PLAN_CLAIMS_CONSISTENCY_AND_ANTI_OVERCLAIM.md, ../VALIDATION.md -->

**English:** [PLAN_SYNTHETIC_DATA_AND_CONFIDENCE_VALIDATION.md](PLAN_SYNTHETIC_DATA_AND_CONFIDENCE_VALIDATION.md)

**Status:** Em andamento (Fases 1 + 5.1 em `main`; o survey v1.8.0 [#1060](https://github.com/DataBoar/data-boar/issues/1060) enriquece este plano — não arquivar)
**Data:** 2026-03-15 (onda v1.8.0: 2026-08-27)
**Autores:** Fabio Leitao
**Prioridade:** H3
**Depende de:** ADR-0007
**Milestone:** v1.8.0
**Issue:** [#835](https://github.com/DataBoar/data-boar/issues/835) (Fase 1 + 5.1 baseline F1) · **[#1060](https://github.com/DataBoar/data-boar/issues/1060)** (metodologia de eval composto)

**Sincronizado com:** [PLANS_TODO.md](PLANS_TODO.md) (lista central de to-dos)

## Ao implementar passos: atualizar docs e testes; depois atualizar PLANS_TODO.md e este arquivo.

Este plano permite **criar fontes sintéticas e possivelmente “true-like”** que cubram o leque de ingredientes que o app ingere (todos os formatos de arquivo compatíveis, shares de rede, SQL e NoSQL nas variantes populares). Acrescenta **falsos positivos e falsos negativos intencionais** para **validar e pontuar a confiança** de um achado, e entrega **orientação ao operador**: de “provavelmente nada grave, mas melhor pecar pelo excesso de cautela” (com instruções para verificar na mão) até “chance de alto risco de violação, mas o ML/DL pode estar sofrendo” (como verificar na mão e como ajustar configs). Também cobre **timeouts e problemas de conectividade / I/O de rede** com instruções para resolver ou prevenir nas próximas sessões de scan.

---

## Objetivos

- **Fontes sintéticas e true-like:** Fornecer ou documentar como criar fixtures que incluam:
- **Todos os formatos de arquivo compatíveis** (txt, csv, tsv, json, xml, html, pdf, docx, odt, xlsx, msg, eml, etc. — ver [connectors/filesystem_connector.py](../connectors/filesystem_connector.py) e extração de texto).
- **Shares de rede:** SMB/CIFS, NFS, WebDAV, SharePoint — dados de amostra ou scripts para expor shares mínimas de teste.
- **SQL:** PostgreSQL, MySQL/MariaDB, SQLite, MSSQL, Oracle (variantes populares) — p.ex. Docker Compose ou DBs in-memory com schema e linhas conhecidas.
- **NoSQL:** MongoDB, Redis, Snowflake — collections/chaves/dados de amostra.
- **Falsos positivos e falsos negativos:** Nos dados da fixture, incluir:
- **Rótulos de ground truth** (por coluna, arquivo ou linha: PII/sensível de verdade vs não).
- **Falsos positivos intencionais:** Conteúdo que pode disparar detecção sem ser PII real (ex.: letras com dígitos, ficção com CPF falso, tablatura).
- **Falsos negativos intencionais:** PII ou dado sensível real difícil de detectar (mascarado, formato fora do padrão, padrão raro).
- Usar isso para **validar** o detector e **pontuar** confiança (ex.: precision/recall por execução ou por padrão).
- **Confiança e orientação ao operador:** De cada achado (sensitivity_level, pattern_detected, ml_confidence), derivar uma **faixa de confiança** e **recomendações**:
- **Provavelmente nada grave:** Confiança baixa/média ou padrão fraco; recomendar “melhor pecar pelo excesso de cautela” e **como acessar e verificar na mão** (abrir a tabela/arquivo, conferir valores).
- **Alto risco mas o ML/DL pode estar sofrendo:** Sensibilidade alta com confiança limítrofe ou sinais conflitantes; recomendar **verificação manual** e **como ajustar** (regex_overrides_file, ml_patterns_file, dl_patterns_file, min_sensitivity, timeouts, sample_limit).
- **Achado de alta confiança:** Padrão forte + ml_confidence alto; ainda assim recomendar verificação e passos de remediação.
- **Timeouts e conectividade:** Documentar e, quando útil, **simular** timeout e I/O de rede para que:
- O **failure_hint** já existente (unreachable, auth_failed, permission_denied, timeout) apareça em relatórios e docs.
- Haja **instruções**: como **resolver** (aumentar timeout, checar rede, retry) e como **prevenir** no próximo scan (timeouts na config, caminho de rede, horário de menor pico).

---

## Estado atual

- **Formatos de arquivo:** [connectors/filesystem_connector.py](../connectors/filesystem_connector.py) e extração de texto suportam txt, csv, tsv, json, xml, html, pdf, docx, odt, xlsx, ods, odp, msg, eml, etc. (SUPPORTED_EXTENSIONS).
- **Conectores:** SQL (PostgreSQL, MySQL, MariaDB, SQLite, MSSQL, Oracle), MongoDB, Redis, Snowflake, SMB, NFS, WebDAV, SharePoint, Power BI, Dataverse, REST API (ver [TOPOLOGY.md](TOPOLOGY.md)).
- **Detecção:** [core/detector.py](../core/detector.py) devolve sensitivity_level, pattern_detected, norm_tag, ml_confidence (0–100). O relatório inclui aba de recomendações e dicas de falha ([core/database.py](../core/database.py) `failure_hint(reason)`).
- **Dataset sintético compartilhado com P/R/F1 medido:** a Fase 1 (#835) adiciona `tests/data/f1_validation/` + `scripts/validate_detection_f1.py` e publica números em [VALIDATION.md](../VALIDATION.md). O corpus de cenário POC (`generate_synthetic_poc_corpus.py` / EXPECTED.txt) continua complementar. Fases 2–4 (SQL/NoSQL/shares, faixas de confiança no relatório) ainda abertas.
- **Relatório:** Recomendações e falhas de scan já mostram dicas; ainda não há **faixa de confiança do achado** explícita (ex.: “provavelmente nada grave” vs “alto risco, ajustar ML/DL”) nem seção dedicada de “orientação ao operador” para verificação e ajuste.

---

## Escopo: ingredientes de dados sintéticos

| Categoria     | Ingredientes a cobrir                                                                | Entrega (fixture / doc / script)         |
| ------------- | ------------------------------------------------------------------------------------ | ---------------------------------------- |
| **Arquivos**  | txt, csv, tsv, json, xml, html, pdf, docx, odt, xlsx, ods, msg, eml, etc.            | Árvore de fixture + manifesto de verdade |
| **SQL**       | PostgreSQL, MySQL, MariaDB, SQLite, MSSQL, Oracle                                    | Docker Compose ou in-memory + dumps SQL  |
| **NoSQL**     | MongoDB, Redis, Snowflake                                                            | Docker ou test containers + seed         |
| **Shares**    | SMB/CIFS, NFS, WebDAV, SharePoint                                                    | Scripts ou servidor mínimo + arquivos    |
| **APIs**      | REST (JSON), Power BI, Dataverse                                                     | Mock ou API mínima + respostas de amostra |

Ground truth: para cada fixture (arquivo, tabela/coluna, resposta de API), um **manifesto** (YAML/JSON) diz se contém PII real, sem PII, ou “tricky” (FP/FN) para comparar a saída do scan e calcular precision/recall e confiança.

---

## Falsos positivos e falsos negativos (nas fixtures)

- **Falso positivo (FP):** Conteúdo que o detector marca como sensível mas **não** é PII real (ex.: letras de música com datas, dígitos de tablatura, romance com CPF falso). Incluir vários; rotular no manifesto para medir taxa de FP e ajustar limiares ou padrões.
- **Falso negativo (FN):** Conteúdo que **é** PII/sensível e o detector perde (ex.: CPF mascarado, data fora do padrão, identificador raro). Incluir vários; rotular para medir FN e melhorar regex/ML/DL ou documentar “verificação manual recomendada”.
- **Uso:** (1) Rodar scan no conjunto; (2) comparar achados ao manifesto; (3) calcular precision, recall, F1; (4) opcionalmente **pontuar confiança** por achado (ex.: “bate com FP conhecido” → confiança menor; “bate com PII conhecido” → alta). Resultados alimentam a **orientação ao operador** (ex.: “ML/DL pode estar sofrendo” quando a taxa de FN é alta em linhas tricky).

---

## Faixas de confiança e orientação ao operador

- **Entradas:** sensitivity_level, pattern_detected, ml_confidence (e dl_confidence opcional), mais “matches_ground_truth” opcional ao rodar contra fixtures rotuladas.
- **Faixas (exemplo):**
- **Provavelmente nada grave:** Sensibilidade LOW, ou MEDIUM com confiança baixa e padrão fraco (ex.: GENERAL). Orientação: “Melhor pecar pelo excesso de cautela. Verifique na mão: [link ou passos para abrir o alvo]. Se confirmar não-sensível, considere termos ML não-sensíveis ou excluir o path na config.”
- **Melhor pecar pelo excesso de cautela:** Sensibilidade MEDIUM ou HIGH com confiança moderada. Orientação: “Acesse e verifique na mão: [passos]. Se PII confirmado, remediação; se FP, ajuste regex_overrides ou ml_patterns_file.”
- **Alto risco – verificar e remediar:** Sensibilidade HIGH e confiança alta. Orientação: “Trate como possível violação. Verifique na mão: [passos]. Remediar (mascarar, apagar ou documentar base legal).”
- **Alto risco mas o ML/DL pode estar sofrendo:** HIGH com confiança baixa/limítrofe, ou pattern_detected = ML_DETECTED / ML_POTENTIAL com muitos FN na validação. Orientação: “Verificação manual fortemente recomendada. Considere: (1) exemplos em ml_patterns_file / dl_patterns_file; (2) regex_overrides_file do domínio; (3) sample_limit ou min_sensitivity; (4) docs/SENSITIVITY_DETECTION.md.”
- **Relatório:** Acrescentar coluna ou seção “Discovery confidence” e “Operator guidance” (texto curto ou link). A aba de recomendações pode estender essas mensagens por achado ou por faixa.

---

## Timeouts e conectividade

- **Já existe:** [core/database.py](../core/database.py) `failure_hint(reason)` já mapeia unreachable, auth_failed, permission_denied, timeout para próximos passos. Falhas de scan aparecem no relatório com essas dicas.
- **Plano:** (1) **Documentar** no USAGE ou em “Troubleshooting”: como **resolver** (timeout na config ou no conector, rede/DNS/firewall, retry fora de pico) e como **prevenir** no próximo scan (timeouts, menos paralelismo, caminho de rede estável). (2) Opcionalmente **fixture ou teste** que simule alvo lento/timeout para o relatório mostrar a dica. (3) Estender failure_hint ou o texto do relatório com uma linha “Prevenir da próxima vez” quando útil.

---

## Fases de implementação (to-dos)

### Fase 1: Estrutura de fixture e cobertura de formatos

| #   | To-do                                                                                                                                                                                  | Status |
| --- | ---------------------------------------------------------------------                                                                                                                  | ------ |
| 1.1 | Criar raiz de fixture (ex.: `fixtures/synthetic_data/` ou `test_data/validation/`) com subdirs: files/, sql/, nosql/, shares/ (ou doc para shares).                                    | ✅ Feito (`tests/data/f1_validation/` measure+calibrate; sql/nosql/shares → Fases 2–3) |
| 1.2 | Arquivos de amostra para extensões compatíveis: uns com PII, uns sem, uns FP, uns FN.                                                                                                  | ✅ Parcial — formatos texto txt/csv/tsv/json/xml/html + 4 classes; binary/office depois |
| 1.3 | Manifesto de ground-truth (YAML/JSON): path → rótulo (`pii` / `clean` / `tricky_fp` / `tricky_fn`) + `expected_miss` + templates measure/calibrate disjuntos.                          | ✅ Feito (`ground_truth.yaml`) |
| 1.4 | Doc: como rodar scan na raiz da fixture e comparar ao manifesto (manual ou script).                                                                                                    | ✅ Feito ([VALIDATION.md](../VALIDATION.md) + harness) |
| 1.5 | Testes: pytest opcional no detector num subset; ou só doc.                                                                                                                             | ✅ Feito (`tests/test_validate_detection_f1.py` — estrutura/anti-leakage/PII claro; números de F1 publicados, não assertados) |

### Fase 2: Fixtures SQL e NoSQL

| #   | To-do                                                                                                                                                                      | Status |
| --- | ---------------------------------------------------------------------                                                                                                      | ------ |
| 2.1 | SQL: Docker Compose ou script para PostgreSQL, MySQL, SQLite com colunas PII / não-PII / FP / FN conhecidas; documentar conexão.                                           | ⬜      |
| 2.2 | NoSQL: seed MongoDB e Redis (collections/chaves com rótulos); documentar como apontar a config.                                                                            | ⬜      |
| 2.3 | Estender o manifesto para fixtures de DB (table.column → rótulo).                                                                                                          | ⬜      |
| 2.4 | Doc: scan completo arquivo + SQL + NoSQL vs manifesto; script opcional de precision/recall.                                                                                | ⬜      |

### Fase 3: Shares de rede e cenários de conectividade

| #   | To-do                                                                                                                                                                                         | Status |
| --- | ---------------------------------------------------------------------                                                                                                                         | ------ |
| 3.1 | Documentar ou scriptar SMB/NFS/WebDAV mínimo com arquivos de amostra; incluir no manifesto.                                                                                                   | ⬜      |
| 3.2 | Timeout/conectividade: doc “Troubleshooting”; estender failure_hint ou relatório com “Prevenir da próxima vez” quando couber.                                                                 | ⬜      |
| 3.3 | Opcional: teste/fixture que dispare timeout e assertar a dica no relatório.                                                                                                                   | ⬜      |

### Fase 4: Faixas de confiança e orientação no relatório

| #   | To-do                                                                                                                                                                                                                 | Status |
| --- | ---------------------------------------------------------------------                                                                                                                                                 | ------ |
| 4.1 | Definir faixas (probably_nothing_serious, better_safe_than_sorry, high_risk_verify, high_risk_ml_struggling) a partir de sensitivity_level + pattern_detected + ml_confidence (e FP/FN opcional).                      | ⬜      |
| 4.2 | Mapear cada faixa para texto de orientação: verificação manual, ajuste, link para docs.                                                                                                                               | ⬜      |
| 4.3 | Acrescentar “Discovery confidence” (e opcionalmente “Operator guidance”) ao relatório.                                                                                                                                | ⬜      |
| 4.4 | Docs: USAGE ou doc novo de orientação; EN + pt_BR.                                                                                                                                                                    | ⬜      |
| 4.5 | Testes: assertar confiança/orientação no relatório com fixture de FP/FN conhecida; sem regressão.                                                                                                                     | ⬜      |

### Fase 5: Score de validação e recomendações

| #   | To-do                                                                                                                                       | Status |
| --- | ---------------------------------------------------------------------                                                                       | ------ |
| 5.1 | Script opcional: scan no conjunto, comparar ao manifesto, emitir precision/recall/F1 e stats por padrão.                                    | ✅ Feito (`scripts/validate_detection_f1.py`; baseline em [VALIDATION.md](../VALIDATION.md)) |
| 5.2 | Documentar como usar o conjunto e o score para ajustar config e re-rodar.                                                                   | ⬜ Pendente |
| 5.3 | Atualizar PLANS_TODO.md e este plano; timeouts e “verificar / ajustar na mão” nos docs de operador.                                         | 🔄 Parcial — plano + PLANS_TODO + VALIDATION para Fase 1/5.1; timeouts ainda Fase 3 |

---

## Horizonte distante (H3/H4) — pesquisa de calibração federada ([#1067](https://github.com/DataBoar/data-boar/issues/1067))

Revisão readonly off-band de stacks de ML com preservação de privacidade (ex.: OpenMined/PySyft). **Só registro de padrão** — **sem compromisso de roadmap**, sem dependências novas, sem código FL/DP.

**Cenário Enterprise hipotético:** se um dia melhorarmos a **calibração** ML/DL agregando **sinais entre vários clientes Enterprise** sem centralizar dado bruto, **federated learning** com **composição de differential privacy** é o formato arquitetural correto. Candidato natural de packaging: `dbtier: enterprise`.

> **Ressalva técnica (não simplificar):** PySyft sozinho **não** é differential privacy pronta. DP de verdade exige composição com **Opacus** (PyTorch) ou TF-Privacy no treino. Tratar PySyft como **referência de arquitetura**, não dependência drop-in.

**Enquadramento acadêmico adjacente (contexto de tese do operador, sem ação no repo):** anonimização estática de dataset (k-anonimato / l-diversity, p.ex. ARX) e treino federado atacam **estágios diferentes**; o stack determinístico de discovery do Data Boar continua uma **terceira categoria** (inventário de onde o dado sensível vive).

---

## Dependências e restrições

- **Fixtures são opcionais:** o app principal e os testes padrão não dependem do dataset sintético completo; serve para validação e treino do operador. O CI pode rodar um subset.
- **Nenhum segredo nas fixtures:** só sintético ou anonimizado; sem PII real no repo.
- **Confiança e orientação são aditivas:** colunas e lógica de recomendação atuais permanecem; novas colunas só acrescentam informação.

---

## Conflito e lugar no roadmap

- **Sem conflitos** com outros planos. Aditivo (fixtures, manifesto, colunas/seção do relatório, docs).
- **Lugar:** Independente; pode seguir ou rodar em paralelo com Compliance samples ou Selenium QA. Ver [PLANS_TODO.md](PLANS_TODO.md).

---

## Changelog

- **2026-08-27:** Survey v1.8.0 **[#1060](https://github.com/DataBoar/data-boar/issues/1060)** — eixos de eval composto (F1 + latência + throughput + risco de re-id como **privacidade**); contrato de citação; nenhum número novo publicado nesta PR.
- **2026-03-15:** Plano inicial — fixtures sintéticas/true-like, faixas de confiança, orientação; depois harness F1 da #835 Fase 1 + 5.1.

---

## Onda v1.8.0 — eval composto, não só F1 ([#1060](https://github.com/DataBoar/data-boar/issues/1060))

**Motivo:** Survey competitivo (dossiê privado). **Docs-first** nesta PR. Esta onda define **o que medir** e **como comparar**. **Não** publica tabela nova de resultado, harness novo nem score de ranking fundido.

**Tese (não diluir):** **O ranking de sistemas muda quando se mede só F1.** Um detector que ganha em F1 e perde uma **ordem de grandeza** em throughput não é “melhor” — é **outro trade-off**. Eval de uma dimensão só produz **ordenação falsa**.

**O que não se afirma:** Inventário e scores aqui são **evidência**, não conclusão jurídica ([ADR 0025](../adr/ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md)). Risco de re-id **não** é chancela de conformidade. Esta PR **não** reitera figuras de F1, latência ou speedup — elas só vivem nos artefatos pinados se forem citadas depois.

### O que já existe (não inventar um segundo lab)

| Superfície | Papel hoje | Eixo #1060 |
| ---------- | ---------- | ---------- |
| [VALIDATION.md](../VALIDATION.md) | **Metodologia do baseline F1** (atalho da issue `F1_BASELINE_METHODOLOGY` — **não** há arquivo com esse nome): splits, anti-leakage, `tests/data/f1_validation/` + `scripts/validate_detection_f1.py` | Só **F1 / P / R**; números publicados ficam naquele doc |
| Fases 1 + 5.1 deste plano | Fixtures de texto rotuladas + script F1 sob demanda | Eixo de acurácia já especificado |
| [PLAN_SYNTHETIC_DATA_LAB.pt_BR.md](PLAN_SYNTHETIC_DATA_LAB.pt_BR.md) + [ADR-0007](../adr/ADR-0007-synthetic-data-corpus-before-real-data.md) | Corpus de lab **antes** de dado real; exercícios de pseudo-anonimização / re-id residual | Trilha de lab de **risco de re-id** — ainda sem score fundido |
| Agregação de quasi-identificadores (aba do relatório) | **Inventário** heurístico de combinações | Insumo de métrica de **privacidade** depois; não é F1 |
| [PLAN_BENCHMARK_SAFE_AXIS.md](PLAN_BENCHMARK_SAFE_AXIS.md) + `tests/benchmarks/README.md` | Gates de wall-clock / recall com **benchmark id** | **Latência / throughput** só quando citados do JSON pinado |
| [PLAN_CLAIMS_CONSISTENCY_AND_ANTI_OVERCLAIM.md](PLAN_CLAIMS_CONSISTENCY_AND_ANTI_OVERCLAIM.md) | Claims precisam de `backed_by` | Mesma regra para qualquer write-up composto futuro |

### Quatro eixos (relatar separado — nunca um escalar)

| Eixo | Tipo | O que responde | Não deve |
| ---- | ---- | -------------- | -------- |
| **F1** (com P/R) | Qualidade de detecção vs verdade sintética rotulada | Marcamos as linhas/arquivos certos **neste** split? | Substituir velocidade ou privacidade |
| **Latência** | Performance | Tempo até uma unidade definida (lote, arquivo, sessão) | Comparar entre escopos que não batem |
| **Throughput** | Performance | Trabalho por unidade de tempo numa carga definida | Ser inferido do F1 |
| **Risco de re-id** | **Privacidade**, não qualidade | Quanto as **saídas do sistema** ajudam a reidentificar um titular | Somar ao F1 num score “geral” que esconda o trade-off |

Um dashboard futuro pode mostrar **quatro colunas** (ou Pareto / radar). **Não** pode colapsá-las num número que reordene sistemas como se F1 fosse a história toda.

### Contrato de citação (todo número publicado)

Número sem **escopo** é o defeito que este repo já proíbe. Qualquer write-up posterior **precisa** carregar, juntos:

1. **Escopo** — filtro isolado vs conector vs scan ponta a ponta (não são intercambiáveis).
2. **Artefato pinado** em `tests/benchmarks/` (ou o caminho de publicação F1 em [VALIDATION.md](../VALIDATION.md) só para acurácia).
3. **`benchmark` id** alinhado a `tests/benchmarks/README.md` para aquele escopo exato (não reusar id de hotspot numa afirmação E2E).
4. **`git_sha`** da árvore que gerou o artefato.
5. **Data** da execução (UTC).

Esta onda **não** cita razões desses arquivos. **Não** colar speedups de marketing da classe de cicatriz (incluindo headlines de prefiltro Rust) nem afirmações de eliminação total de FP. Se uma PR futura precisar de um valor, **abrir o JSON pinado** e copiar só com a tupla acima.

### Risco de re-id (dimensão de privacidade)

**Risco de re-id** mede **exposição de privacidade**: a chance de um **titular** ser reidentificado a partir do que o **produto expõe** (achados, amostras, agregados, relatórios) — **não** “quão acurado é o detector.”

- **Não** tratar F1 alto como risco de re-id baixo (um detector minucioso pode **aumentar** a identificabilidade residual das saídas se amostras vazam).
- **Não** tratar flags de quasi-id no Excel como prova pontuada de k-anonimato; são **inventário heurístico** (linha de quasi-identificador em [GLOSSARY.md](../GLOSSARY.md)).
- Trabalho de lab de re-id residual **controlado** permanece em [PLAN_SYNTHETIC_DATA_LAB.pt_BR.md](PLAN_SYNTHETIC_DATA_LAB.pt_BR.md) / ADR-0007 — ainda **só sintético** no git.

### Tabela de execução (docs-first → fatias posteriores)

| Passo | Entregável | Status |
| ----- | ---------- | ------ |
| P1 | Esta seção do plano + resumo no hub + linhas do survey em `PLANS_TODO` | ✅ Feito (PR de docs) |
| P2 | Checklist do operador: quatro eixos + tupla de citação (adendo USAGE ou VALIDATION — sem números novos) | ⬜ Pendente |
| P3 | Extensão opcional do harness: emitir **campos** de latência/throughput ao lado do F1 na mesma execução rotulada (ainda sem score fundido) | ⬜ Pendente |
| P4 | **Protocolo** de risco de re-id nas saídas do lab sintético (espec de métrica de privacidade; não conclusão jurídica) | ⬜ Pendente |

---

## Última atualização com o arquivo do plano. Atualize PLANS_TODO.md ao completar ou acrescentar to-dos.
