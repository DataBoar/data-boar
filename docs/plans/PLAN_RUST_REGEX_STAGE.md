<!-- plans-hub-summary: Cached Regex loop + Python translator (RegexSet rejected); GIL release via py.detach + thread scale; form B; #1414 mother; ADR-0078/0083. -->
<!-- plans-hub-related: PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md, PLAN_BENCHMARK_SAFE_AXIS.md, PLAN_CLAIMS_CONSISTENCY_AND_ANTI_OVERCLAIM.md -->

# Plan: Rust regex stage (open-domain YAML / accept form B)

**Status:** In progress — core stage wired on branch `feat/1414-rust-regex-stage` (phases 1–5); docs/thread-scale tests (6–7) pending
**Date:** 2026-07-31
**Authors:** Cursor (executor) + Claude Code brief (auditor R.O.) + operator
**Priority:** H0 / U1 (detection correctness)
**Mother (spec):** [#1414](https://github.com/DataBoar/data-boar/issues/1414)
**Bus (agent dialogue):** [#1413](https://github.com/DataBoar/data-boar/issues/1413)
**Correlatas:** [#1411](https://github.com/DataBoar/data-boar/issues/1411) (call site) · [#1412](https://github.com/DataBoar/data-boar/issues/1412) (manifest — **merge prerequisite**) · [#1116](https://github.com/DataBoar/data-boar/issues/1116) / [#1199](https://github.com/DataBoar/data-boar/issues/1199) (plugin/SDK)
**ADRs:** [0078](../adr/ADR-0078-multi-pattern-regex-benchmark-gate-regexset-before-vectorscan.md) (**amended** — RegexSet spike failed) · [0080](../adr/ADR-0080-local-validation-gate-inviolable.md) · **[0083](../adr/ADR-0083-rust-regex-stage-superset-accept-form-b.md) (Accepted — form B)**
**Brief:** operator draft `BRIEF-rust-regex-stage-2026-07-31.md` (local; not tracked)
**Probe:** `~/data-boar-drafts/regex-parity-probe-2026-07-31/` (local; not tracked) — `translate.py`, `regex_stage_parity_bench.json`; narrative in **#1413**

---

## 0. Enquadramento (substitui WIP prefiltro/latch)

| Antigo (não shipar) | Novo (#1414 / #1413) |
| --- | --- |
| Prefiltro que **porteia** ML / pula não-suspeitos | Rust **executa** o estágio de casamento de padrão |
| Latch “zero-regressão” porque skip muda findings | **Sem skip** → latch **não se aplica** |
| 3 regex cravadas em `lib.rs` (CPF / e-mail / cartão) | **Zero padrão cravado** no Rust; motor, não catálogo |
| `RegexSet` multi-padrão (ADR-0078 spike) | **Rejeitado** — 5,7× mais lento que laço; ver §2.0 |
| Troca recall ↔ velocidade | Aceleração com **tradutor Python** + fallback **por padrão** |

**WIP no branch** (`core/pro_scan_path.py`, latch, docs “latched off when skip…”): **não mergear nessa narrativa**. Passo 0 da implementação: aposentar skip+latch; reaproveitar só superfícies úteis a **#1412** sob o enquadramento novo.

**Invariante de fronteira:** o Rust só acelera estágio que é função pura *padrão × texto*. Caminhos dirigidos por nome de coluna, tipo declarado ou heurística semântica (menor/DOB, jurisdiction hints, `connector_data_type`) rodam **sempre** em Python.

**Semântica:** Python `re` é a fonte da verdade observável. Rust é detalhe de implementação — o tradutor mora no Python no load; o Rust recebe padrão já correto para a crate.

---

## 1. Escopo de domínio — universo aberto (não só LGPD/GDPR/CCPA)

Domínios de cliente incluem, sem lista fechada: privacy / LGPD / GDPR / CCPA / …, **SISCOMEX**, **SUSEP**, agro, farma, DLP, políticas internas — qualquer YAML.

**Já verificado:** `_load_regex_overrides` (`core/detector.py` ~719–785) aceita `norm_tag` livre com default **`"Custom"`**. Domínio novo = **YAML**, não código.

**Demo ANVISA (probe 2026-07-31):** jurisdição inexistente no produto, **só YAML**, zero linha de código de produto — 10 padrões; Python 18 matches = Rust traduzido 18 (cru 17).

Consequências duras:

1. **Zero padrão cravado em `rust/boar_fast_filter/src/lib.rs`.**
2. Compilação em **tempo de carga** (instância do detector).
3. Regex malformada falha **alto** em `--validate-config`.
4. Aceite **não** é “passa nas 44”. As 44 são regressão. Aceite = *property-based* sob invariante **B** (§4).
5. Manifest (#1412) registra acelerados / traduzidos / fallbacks / só-Rust — **pré-requisito de merge**.

---

## 2. Brief §10 + probe 2026-07-31 (fechados neste PLAN)

### 2.0 Probe — RegexSet perde; laço de Regex ganha

Medido 2026-07-31 (`regex` 1.10 / Python 3.13), estágio de matching **isolado** (não ponta a ponta; não confundir com `rust_prefilter_hotspot` 4,69× / 3 padrões):

| Métrica | Valor |
| --- | --- |
| Padrões | 284 (8 built-in + 267 compliance-samples + 10 ANVISA) |
| Hits (laço Regex vs Python) | 119182 = 119182 |
| Laço de `Regex` cacheadas | **0,686 s** |
| `RegexSet::matches` | **3,907 s** → **5,7× mais lento** |
| `size_limit` default (10 MiB) | RegexSet **não compila** (precisa ≥20 MiB neste conjunto) |
| Rust laço vs Python `re.search` | 0,690 s vs 1,837 s → **2,66×** (melhor de 3) |

**Motivo:** `RegexSet::matches()` avalia **todos** os padrões — sem saída antecipada. O detector precisa de nomes que casaram; o laço de Regex individuais permite o mesmo veredito com custo menor.

**Decisão fechada:** **não** usar `RegexSet` no estágio do detector. Motor = **laço de `regex::Regex` compiladas e cacheadas por instância**. ADR-0078 amendida em conformidade.

### 2.0b Justificativa principal — GIL, `py.detach` e escala com threads

Velocidade **por operação** (2,66× isolado) é secundária. O achado mais forte do probe: o `filter_batch` atual **não solta o GIL** (assinatura PyO3 retém token Python durante o match). Em build **com GIL**, soltar o GIL no laço de match permite escala real com threads; Python não escala.

| Threads | Python wall | Escala vs 1t | Rust (GIL liberado) | Escala vs 1t |
| --- | --- | --- | --- | --- |
| 1 | 1700,4 ms | 1,00× | 806,2 ms | 1,00× |
| 8 | 2174,2 ms | **0,78×** (piora) | 247,5 ms | **3,26×** |

Ponta a ponta nesse setup: **~6,9×** Rust+threads vs Python. Sem soltar o GIL, uma regressão que **reintroduza retenção do GIL** deixa paridade de findings verde e destrói a escala — por isso o aceite **exige** teste de escalonamento em build **com GIL**.

**API PyO3:** o método exposto libera o GIL com **`py.detach`** (em PyO3 **0.29**, `allow_threads` foi renomeado para `detach`).

**Custo de compilação (cache = requisito):** 284 padrões → **108,9 ms** em Rust vs **12,4 ms** em Python. Recompilar por batch apaga o ganho do match — cache **uma vez por instância** do detector (só no reload de config).

### 2.1 Call site vs `pro/engine.py` (brief §10.1)

| Decisão | Escolha |
| --- | --- |
| Onde entra | Loop de regex em `SensitivityDetector.analyze` (~1420–1432): hoje `rex.search(combined)` → `found_patterns` |
| O que Rust devolve | Conjunto de **nomes** que casaram (booleano por padrão via laço `is_match`). Checksums / join / ML/DL ficam em Python |
| Precedência | Detector já agrega **todos** os hits (`_join_pattern_hits`). Laço de Regex basta — **sem** fase 2 de posição e **sem** `RegexSet` |
| `ProScanner` / `filter_batch` (~40–71, ~119–134) | Desenho antigo “porteia ML”. **Não** é o veículo do #1414. Manter legado (ProcessPool / QA) até migração explícita; **não duplicar** um segundo motor no CLI |
| Relação | **Substituir o papel do Rust no detector**; não wire CLI→`ProScanner.scan` skip |

### 2.2 Como os padrões chegam ao Rust (brief §10.2)

1. Fonte: instância viva do `SensitivityDetector` após built-ins + `_load_regex_overrides` + plugin (nunca catálogo no `lib.rs`).
2. **Antes do Rust:** `translate(pattern) -> (rust_pattern | None, reason)` no Python (§2.7) — Rust só vê padrões já traduzidos ou aceleráveis.
3. Assinatura PyO3 sugerida: `compile_patterns(names: list[str], patterns: list[str], size_limit: int | None) -> handle` + `match_names(text: str) -> list[str]` sobre **lista de `Regex`**, **não** `RegexSet`.
4. **`match_names` (e qualquer hot path de match) deve chamar `py.detach`** ao redor do laço Rust — sem isso não há escala com threads sob GIL (§2.0b).
5. **Cache por instância do detector** — requisito (§2.0b, 108,9 ms / 284 padrões). Compilar cada `Regex` **uma vez** na construção / reload. **Não** recompilar por batch.
6. Invalidação: só quando o conjunto de padrões muda (novo detector / reload de YAML). Scan hot path só faz `is_match` em laço.
7. `size_limit`: **por padrão** via `RegexBuilder` (default são da crate); estouro → fallback **daquele** padrão (nunca crash).

### 2.3 Gate de tier (brief §10.3)

- Feature key nova preferida: `rust_regex_stage` (evitar herdar narrativa `pro_prefilter_accel` / skip).
- Tier insuficiente **ou** extensão ausente **ou** pânico → caminho Python **inteiro**.
- Invariante: licença / ausência de wheel **nunca** muda o resultado para pior que Python; sob form **B**, máquina com Rust pode ter **mais** findings (atribuídos) — por isso #1412 é merge blocker (§4.1).
- Degrada **só velocidade**, nunca correção no sentido “sumiu finding que o Python teria”.

### 2.4 Teste diferencial permanente sem estourar ADR-0080 (brief §10.4)

| Faixa | Conteúdo | Onde |
| --- | --- | --- |
| Fast | Property-based / fixture pequena + tradutor + Classe A/B + `LGPD_CNPJ_ALNUM` em fallback + **controle cru vs traduzido** | `check-all` / pytest default |
| Regression | 44 compliance-samples: conjunto de `pattern_detected` sob invariante **⊇** + atribuição de extras | marker `slow` ou job CI dedicado |
| Permanente | Diferencial Rust on/off no mesmo processo (flag / monkeypatch extensão) | CI sempre |

Aceite property-based: **qualquer** YAML — não “passa nas 44”.

**Controle obrigatório (probe):** no corpus de 275 padrões — Python 212 · Rust **cru** 154 · Rust **traduzido** 212 (zero divergência nas duas direções). As 58 perdas do braço cru estão em **duas linhas** (`LOCATİON:` / `locatıon:`) e derrubam `LOCATION_CSV_PAIR` em **29 jurisdições**. Testes de produto devem falhar se o braço cru “passar” sem o tradutor.

### 2.5 Guarda Classe B — possessivo e ambíguos (brief §10.5)

**Onde:** dentro de `_load_regex_overrides` / carga do detector, **via o tradutor** (§2.7), ao lado de `_has_nested_quantifier` (#829) — mesmo `PluginValidationWarning`.

| Classe | Exemplos | Ação |
| --- | --- | --- |
| A (não compila) | lookaround, `\1`–`\9`, `(?>`, `(?(1)`, `\Z`, `(?a)`/`(?L)` | `translate` → `(None, reason)` → fallback Python |
| B (compila ≠ equivalente) | Possessivos `*+` `++` `?+` `}+`; `(?i)` **escopado** ou no meio do padrão | **Forçar fallback** mesmo se a crate compilasse |
| Traduzível | `(?i)` **global no início** + literal/`[]` com `i`; `$` sem `(?m)` | Reescrita mecânica (§2.7) |

**Anti-FP:** não tratar `+` dentro de `[]` como possessivo; respeitar escapes; faixas `[a-z]`/`[h-j]` que alcançam `i` recebem `İı`. “Compilou” **nunca** é prova de equivalência. Calibração: estilo `tests/test_redos_guard.py` + testes do `translate.py` (adversarial).

### 2.6 `LGPD_CNPJ_ALNUM` (brief §10.6)

| Fase | Ação |
| --- | --- |
| 1 (merge) | **Aceitar fallback por padrão** (lookahead). Probe: **1** fallback nos 275; zero risco de reescrita errada |
| 2 (follow-up) | Reescrita sem lookahead **só** com prova de equivalência + teste diferencial dedicado |

### 2.7 Tradutor Python (portar — não reescrever)

**Fonte:** `~/data-boar-drafts/regex-parity-probe-2026-07-31/translate.py` (issue #1414). Portar para `core/` (módulo ao lado do detector), **não** reescrever do zero.

**Contrato:**

```text
translate(pattern) -> (rust_pattern | None, reason)
  rust_pattern is None  =>  fallback Python; reason vai ao manifest (#1412) e --validate-config
```

**Efeito medido nos 275 padrões do produto:**

| Destino | Contagem |
| --- | --- |
| Acelerado direto | 162 |
| Traduzido | 112 |
| Fallback Python | 1 (`LGPD_CNPJ_ALNUM`) |

**Traduções mecânicas (medidas):**

1. Sob `(?i)` global no início: literal `i`/`I` → `[iIİı]`; classe/faixa que alcança `i`/`I` ganha `İı`. BMP: **únicos** codepoints divergentes na direção Python→Rust.
2. `$` sem `(?m)` → `(?:\n?\z)` (Python aceita `\n` final; Rust é fim-de-texto estrito).

**Fallbacks sem tradução:** lookaround, backreference, atomic, conditional, `\Z`, `(?a)`/`(?L)`, possessivo, `(?i)` escopado/`(?i)` no meio (expansão global causaria over-match).

**Bugs adversarial já corrigidos no protótipo (preservar no port):** `(?i)` escopado; faixa `[h-j]`/`[a-z]`; grupo nomeado `(?P<x>i)`; **não** validar saída Rust com `re.compile` (`\z` é inválido no Python — validar só a **entrada**).

---

## 3. Validação — NÃO construir maquinário novo

`_load_regex_overrides` já valida ADR-0052, emite `PluginValidationWarning` por item, guarda ReDoS #829, e `re.error`.

**Tradutor + Classe A/B entram ALI** (ou na mesma carga do detector), ao lado da guarda ReDoS. Calibração: `tests/test_redos_guard.py` + suite do probe portada.

### 3.1 Consultor — três camadas + garantia B

Modo de falha a documentar: consultor testa em Python, YAML acelera em Rust com semântica Y → finding a menos sem erro.

Camadas: (1) `--validate-config` ativo · (2) manifest #1412 · (3) docs/samples referência.

**Garantia literal (B) para docs na implementação:**

> Nenhum padrão que você testou em Python deixa de rodar. A aceleração em Rust nunca remove detecção. Em alguns casos ela detecta **a mais** — padrões que o motor Python recusa por risco de travamento (ReDoS) rodam com segurança em Rust, porque aquele motor tem tempo de execução linear garantido. Todo finding adicional é atribuído no manifesto ao padrão que o gerou.

---

## 4. DECISÃO DO OPERADOR — forma **B** (Accepted)

Medição 2026-07-31 — `(a+)+$` / 40× `a` + `!`: Rust ~82 µs · Python travou >5 s.

| | Invariante | Cobertura |
| --- | --- | --- |
| A · paridade estrita (rejeitada) | findings idênticos | Nested quantifier descartado nos dois |
| **B · cobertura ampliada (escolhida)** | **`findings(Rust) ⊇ findings(Python)` — nunca subset** | Padrão #829 pode rodar **só** no Rust |

- [ ] A — paridade estrita
- [x] **B — cobertura ampliada** — operador, 2026-07-31

**Invariante final:** nenhum finding que o Python produziria pode sumir. Findings a mais são aceitos **e têm de ser explicáveis** — rastreáveis a um padrão que o Python descartou (#829) ou a diferença mecânica **documentada**. *“O Rust achou mais”* sem atribuição **não passa no aceite**.

Registro formal: **[ADR 0083](../adr/ADR-0083-rust-regex-stage-superset-accept-form-b.md)** (Accepted).

### 4.1 Consequência — #1412 é pré-requisito de merge

Sob B, a mesma config em duas máquinas (com/sem extensão) pode gerar relatórios diferentes. Sem manifest isso **parece não-determinismo** e ataca a claim de repetibilidade em [COMPLIANCE_FRAMEWORKS.md](../COMPLIANCE_FRAMEWORKS.md) (*Deterministic detection vs generative LLM hype*).

**Reconciliação:** repetibilidade **condicionada ao motor**; o motor fica na evidência. Mínimo no manifest / status:

- motor + versão
- nº acelerados / traduzidos
- nº em fallback Python **com motivo por padrão**
- **quais padrões rodaram só em Rust**
- se a extensão estava ausente e por quê

**Não mergear ativação do estágio Rust (#1414 / call site #1411) sem #1412 completo.**

### 4.2 Postura open-core (palavras do operador)

Mais valor no pago **sem** fragilidade proposital no free:

| Path | Comportamento |
| --- | --- |
| Community / sem extensão | **Nunca** produz finding **errado**. **Recusa** executar padrão que seu motor não roda com segurança (#829) e **avisa**. Comportamento do free **idêntico** ao de hoje |
| Pago / com Rust | Remove uma limitação: padrões seguros no autômato linear podem rodar |

A diferença é de **mecânica da linguagem** (`re` = backtracking; crate `regex` = tempo linear), não de política que piora o Community.

---

## 5. Documentação (quatro superfícies)

USAGE + TECH_GUIDE + SENSITIVITY_DETECTION (EN + pt-BR) · `--help` · `GET /status` · man §1/§5.

CLI: `python main.py --config config.yaml --…`.

---

## 6. Fases de implementação (só após Approve — código espera o PLAN)

| # | Fase | Status |
| - | ---- | ------ |
| 0 | Aposentar WIP latch/ProScanner-skip (não shipar narrativa antiga) | 🟡 observability → `rust_regex_stage`; legado ProScanner ainda presente |
| 1 | **#1412 schema** — **blocker** · ADR-0083 Accepted | ✅ (#1412 fechado; manifest estendido) |
| 2 | **Portar `translate.py`** para `core/` + testes (controle cru vs traduzido) | ✅ `core/regex_translate.py` + adversarial pytest |
| 3 | Classe A/B / fallback reasons via tradutor em `_load_regex_overrides` (§2.5–2.7) | ✅ `classify_pattern` no build do stage; warnings `--validate-config` → fase 6 |
| 4 | API Rust: **`Vec<Regex>` + cache** + **`py.detach`** no match — zero padrão cravado; **não** RegexSet | ✅ `RegexStageEngine` |
| 5 | Wire `analyze` + tier fail-soft (§2.1–2.3) | ✅ `_match_regex_patterns` + `rust_regex_stage` tier |
| 6 | validate-config + status/help/man/docs (garantia B) | ⬜ |
| 7 | Testes diferenciais (§2.4) + **escala com threads em build COM GIL** (§2.0b); migrar `FastFilter` legado | ⬜ |
| 8 | Opcional: reescrita `LGPD_CNPJ_ALNUM` (§2.6) | ⬜ |

Ordem de merge: **#1412 antes ou no mesmo PR** que liga o estágio Rust (#1414).

---

## 7. Aceite (checklist)

1. Fronteira §0 respeitada.
2. Zero padrão cravado no `lib.rs` do caminho novo.
3. Tradutor + compat Rust via carga do detector / `_load_regex_overrides` (§3 / §2.7).
4. **`findings(Rust) ⊇ findings(Python)`**; extras atribuídos.
5. Controlo cru vs traduzido verde; ANVISA YAML-only 18=18 (ou equivalente).
6. Teste diferencial permanente no CI.
7. Manifest #1412 completo (**merge blocker**).
8. Community path = comportamento atual (#829); sem finding errado no free.
9. Benchmark com escopo declarado (2,66× isolado ≠ 4,69× prefilter; RegexSet **não** citado como caminho).
10. Motor = laço de Regex cacheadas — **não** RegexSet.
11. Hot path de match libera o GIL com **`py.detach`** (PyO3 ≥ 0.29).
12. Teste de **escalonamento com threads** em build **com GIL** verde (regressão que retenha o GIL deve falhar mesmo com paridade de findings OK).
13. Cache por instância obrigatório — sem recompile por batch (custo ~109 ms / 284 padrões).

---

## 8. Fora de escopo (bus #1413)

Unicode residual além do tradutor · backtracking/timeout sob carga · diferencial exaustivo global · Vectorscan — #1413 / ADR-0078 gate.

**Discórdias:** #1413 ou este PLAN — não implementar em silêncio (ADR-0046).
