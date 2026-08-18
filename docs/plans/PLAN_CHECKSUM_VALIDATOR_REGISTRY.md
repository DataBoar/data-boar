# PLAN: Checksum Validator Registry — evidência matemática além do regex

<!-- plans-hub-summary: Registro de validadores nomeados por ALGORITMO (não por país/tipo de dado), declarados via `validator:` opcional no YAML de padrão. Regex prova forma; checksum prova validade. Cobre PII (BR/EU/NA/LATAM/ME) e setorial não-PII (container ISO 6346, GS1, ISIN/LEI, IMEI/ICCID, segredos com CRC32/Base58Check/EIP-55). Implementação Python primeiro; espelho opcional em boar_fast_filter só sob paridade property-based. -->
<!-- plans-hub-related: PLAN_COMPLIANCE_EXPANSION_GLOBAL_JURISDICTIONS.md, completed/PLAN_CNPJ_ALPHANUMERIC_FORMAT_VALIDATION.md, PLAN_RUST_REGEX_STAGE.md, PLAN_YAML_PLUGIN_SYSTEM.md, PLAN_ADDITIONAL_DETECTION_TECHNIQUES_AND_FN_REDUCTION.md -->

**Status:** Draft
**Date:** 2026-08-18
**Authors:** Fabio Leitao (operador) + Claude Code (auditor R.O., brief)
**Priority:** H1
**Tags:** detection, checksum, validators, yaml, config-first, jurisdictions, sectoral, secrets, false-positive-reduction, rust, parity
**Depends on:** [PLAN_YAML_PLUGIN_SYSTEM.md](PLAN_YAML_PLUGIN_SYSTEM.md)
**GitHub:** [#1639](https://github.com/DataBoar/data-boar/issues/1639) (registro + EU/IBAN — **mãe**) · [#1640](https://github.com/DataBoar/data-boar/issues/1640) (América do Norte) · [#1641](https://github.com/DataBoar/data-boar/issues/1641) (LATAM + Oriente Médio) · [#1642](https://github.com/DataBoar/data-boar/issues/1642) (setorial não-PII) · [#527](https://github.com/DataBoar/data-boar/issues/527) (CNPJ alfa/CPF/PIS) · [#1356](https://github.com/DataBoar/data-boar/issues/1356) (boleto) · [#1055](https://github.com/DataBoar/data-boar/issues/1055) (expansão de jurisdições — mãe do eixo)

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md) (sprint **S5**; **S3** CNPJ Phase 5 checksum = subconjunto Fase 2)

---

## 0. Tese em uma linha

**Regex reconhece forma; checksum prova validade.** Falso positivo é o defeito comercial mais caro
de um scanner de compliance — cliente que recebe 400 achados e descobre que 300 eram ruído não
confia no próximo relatório. Checksum é evidência **matemática, verificável e offline**, coerente
com a doutrina "evidence, not legal conclusion" (ADR-0049/0052) e com o diferencial determinístico
(zero-LLM).

## 1. Enquadramento — o que este plano NÃO é

| ❌ Não é | ✅ É |
|---|---|
| Recurso de PII | Recurso de **evidência**: qualquer padrão de qualquer YAML pode declarar validador |
| Catálogo por país | **Registro por ALGORITMO** — `luhn`, `mod10`, `mod11(pesos)`, `iso7064_mod97_10`, `crc32_suffix`, `base58check` |
| Mudança no `boar_fast_filter` | Python primeiro; Rust **só** sob paridade provada (§5) |
| Consulta online a registro oficial | **Offline e matemático** — prova forma válida, nunca existência/registro ativo |

⚠️ **Restrição de projeto inegociável:** o catálogo é **universo aberto por YAML** (privacy,
SISCOMEX, SUSEP, agro, farma, DLP, política interna). **Validador não pode virar padrão cravado.**
Se o registro nascer indexado por país ou por "tipo de PII", a flexibilidade morre no primeiro
cliente setorial. **Indexar por algoritmo, nunca por uso.**

## 2. Contrato (config-first, opt-in, retrocompatível)

```yaml
- name: EU_IBAN
  regex: '...'
  validator: iso7064_mod97_10      # opcional

- name: CL_RUT
  regex: '...'
  validator: mod11
  validator_args: { weights: [2,3,4,5,6,7], alpha_check: "K" }

- name: BR_CNPJ_ALNUM
  regex: '...'
  validator: mod11_cnpj_alnum
```

**Padrão sem `validator:` mantém exatamente o comportamento de hoje.** Cliente que escreve YAML
próprio referencia validador existente **pelo nome**, sem tocar em Python nem Rust.

## 3. Fases

### Fase 1 — Núcleo do registro (bloqueia todas as outras)
- `core/validators/` com registro nomeado + resolução por nome
- Chave `validator:` / `validator_args:` no schema de padrão (`config/plugin_schema.yaml`, ADR-0052)
- Integração no `detector.py` reusando o ponto que já existe: `_CHECKSUM_GATED_PATTERNS` +
  `_append_pattern_hit` (o gate já roda hoje para `LGPD_CPF`/`LGPD_CNPJ` — **generalizar, não criar
  caminho novo**)
- Primitivos: `luhn`, `mod10`, `mod11(pesos)`, `iso7064_mod97_10`, `iso7064_mod11_10`
- **Rótulo de evidência no relatório:** `checksum_validated` vs `structural_only` vs `shape_only`

### Fase 2 — Brasil (fecha buraco conhecido; entrega **S3** / #527)
- **`mod11_cnpj_alnum`** — IN RFB 2.229/2024: mesmos pesos `_W1`/`_W2` de `cnpj_checksum_valid`,
  extração por `ASCII − 48` (`'0'`→0 … `'A'`→17), **DVs finais numéricos**. Fecha #527, cuja
  lacuna está admitida em `core/brazilian_cpf.py:181` (*"is not validated here"*)
- `mod11_pis_pasep`
- **Boleto** (#1356): Mod-10 nos campos 1–3 + Mod-11 no DV geral; **arrecadação/convênio (inicia
  com `8`) alterna Mod-10/Mod-11 conforme o 3º dígito** — ignorar isso = falso negativo em conta de
  luz/água/tributo

> **Cruzamento com sprint S3:** a linha **CNPJ Phase 5 (checksum layer)** em `PLANS_TODO.md` não
> duplica este plano — é o recorte Brasil/CNPJ-alnum dentro da **Fase 2** aqui. Formato/regex das
> fases 1–4 do [PLAN_CNPJ_ALPHANUMERIC_FORMAT_VALIDATION.md](completed/PLAN_CNPJ_ALPHANUMERIC_FORMAT_VALIDATION.md)
> já está em `completed/`; checksum é a fase 5 adiada que este registro generaliza.

### Fase 3 — Europa (#1639)
- **`iso7064_mod97_10`** → **IBAN** (cobre ~80 países num algoritmo) + derivação de país pelos 2
  primeiros caracteres + comprimento tabelado por país
- PT NIF · ES NIF/NIE (mod 23, tabela `TRWAGMYFPDXBNJZSQVHLCKE`) · FR NIR (clé mod 97, **Córsega
  2A/2B exige substituição antes do cálculo**) · IT Codice Fiscale · NL BSN (*elfproef*) · BE
  (mod 97, nascidos ≥2000 exigem prefixo `2`) · PL PESEL/NIP/REGON · Nórdicos
- **Alemanha = duas coisas distintas:** `Steuer-IdNr` (federal, ISO 7064 MOD 11,10) entra
  normalmente; **`Steuernummer` varia por Bundesland (~13 formatos, sem DV nacional)** → **tabela
  por Land em YAML**, nunca ramificação em código

### Fase 4 — América do Norte (#1640)
- **`aba_routing`** (pesos 3,7,1 mod 10) · **`luhn_npi`** (prefixo `80840`, dado de saúde/HIPAA) ·
  `vin_mod11` · `cusip_mod10`
- **`luhn` reusado**: SIN e BN canadenses saem quase de graça
- ⚠️ **SSN NÃO TEM CHECKSUM** — randomização de 25/jun/2011 eliminou qualquer relação aritmética.
  **Documentar explicitamente** para ninguém "implementar o checksum do SSN". Sobra validação
  **estrutural** por faixas SSA (área `000`/`666`/`900-999`, grupo `00`, série `0000`), rotulada
  como evidência mais fraca. Idem **EIN** (prefixos IRS) e **Egito** (§Fase 5)
- DL por estado (~51 formatos) e saúde por província canadense (OHIP/RAMQ/BC/AB) → **tabela YAML**

### Fase 5 — LATAM + Oriente Médio (#1641)
- **`mod11` parametrizável por pesos cobre quase toda a LATAM** — uma função, não uma por país
- Armadilhas obrigatórias: **RUT chileno com DV `K`** (hoje há padrão `RUT_CL` em YAML de compliance,
  sem validação de checksum) · **Equador troca de algoritmo pelo 3º dígito** (Mod-10 PF vs Mod-11 PJ
  — implementar só um perde toda pessoa jurídica) · **CURP/RFC** com tabela alfanumérica própria
- **Luhn reusado** (Teudat Zehut, Emirates ID, National ID saudita) · TR TC Kimlik · IR mod 11
- Egito **sem DV** → estrutural declarado

### Fase 6 — Setorial não-PII (#1642) — **maior diferencial competitivo**
- **`iso6346_container`** (mod 11) — âncora do eixo portuário/SISCOMEX; **ninguém no mercado de
  discovery cobre isso** · IMO number
- **`mod10` genérico** → GTIN-8/12/13/14, EAN, UPC, SSCC, GLN, SEDOL (agro, varejo, farma,
  serialização DSCSA/EU FMD)
- **`iso7064_mod97_10` reusado por LEI** (ISO 17442 = mesma norma do IBAN, custo marginal ~zero)
  · ISIN (Luhn) · CUSIP
- **IMEI / ICCID** — Luhn puro, saem de graça
- **Segredos — melhor razão valor/esforço de toda a família:** tokens GitHub (`ghp_`/`github_pat_`
  etc.) carregam **CRC32** nos últimos 6 chars; **Bitcoin = Base58Check** (duplo SHA-256);
  **Ethereum = EIP-55** (Keccak-256 no caso das letras); AWS Access Key ID com checksum.
  Detecção de segredo por regex é notoriamente ruidosa — com checksum o FP cai a ~zero, porque
  string aleatória não satisfaz checksum por acaso. Alimenta [#1477](https://github.com/DataBoar/data-boar/issues/1477)
  (dogfood) e [#1620](https://github.com/DataBoar/data-boar/issues/1620) (segredos)
- ISBN-10/13 · ISSN · IATA (mod 7) · MPAN (mod 11)

## 4. Cobertura por reuso (por que o custo marginal cai rápido)

| Primitivo | Serve |
|---|---|
| `luhn` | PAN · SIN (CA) · BN (CA) · IMEI · ICCID · ISIN · Teudat Zehut · Emirates ID · National ID (SA) · NPI (US) |
| `iso7064_mod97_10` | IBAN (~80 países) · **LEI** · BE Rijksregisternummer |
| `mod10` | GTIN/EAN/UPC · SSCC · GLN · SEDOL · CUSIP · boleto (campos) · CURP (MX) |
| `mod11(pesos)` | CPF · CNPJ · PIS · RUT (CL) · CUIT (AR) · NIT (CO) · RUC (PE/PY) · RIF (VE) · NIT (BO) · PT NIF · NL BSN · VIN · MPAN · ISBN-10 · ISSN · ISO 6346 · IR |

**`luhn` já existe** em `rust/boar_fast_filter/src/lib.rs` (`check_luhn`, hoje acoplado ao cartão no
prefiltro) — falta expor como **validador nomeado reutilizável** no registro Python (§5).

## 5. Python × boar_fast_filter — regra de decisão (NÃO é "fazer nos dois")

**Python é a fonte de verdade observável.** Onde o validador roda é decisão de desempenho, não de
semântica — mesmo princípio do ADR-0083 para o estágio regex.

**Ordem obrigatória:**
1. **Python primeiro, sempre.** Fase 1–6 entregam valor completo sem tocar no Rust.
2. **Medir antes de considerar Rust.** O custo da travessia Python↔Rust é proporcional à **taxa de
   acerto**, não ao volume de linhas. Em coluna densa de documento (acerto ~100%) cada acerto
   atravessa a fronteira; em coluna esparsa é irrelevante. **Sem medição em coluna real, não
   otimizar.**
3. **Espelho em Rust só sob paridade property-based.** Validador é **regra de compliance**:
   divergência de um dígito entre Python e Rust faz o **relatório mentir**, e mentir em auditoria é
   pior que ser lento. Aceite exige geração aleatória em massa comparando as duas implementações —
   **nunca teste de exemplo**.
4. **Cabe no invariante de fronteira** do [PLAN_RUST_REGEX_STAGE.md](PLAN_RUST_REGEX_STAGE.md) §0
   (só função pura `entrada × algoritmo`), mas é **ampliação de escopo** — decisão do operador, não
   automática.

⛔ **PROIBIDO** (ver [PLAN_RUST_REGEX_STAGE.md](PLAN_RUST_REGEX_STAGE.md) §0 e `core/pro_scan_path.py`):
expandir ou reintroduzir o modelo de **prefiltro que porteia/pula linhas antes do ML**,
`PRO_SCAN_PATH_ZERO_REGRESSION_LATCH`, ou âncora de regressão `#1411`. O caminho de observabilidade
tier-paid em `pro_scan_path` permanece **fora do escopo** deste plano — **nada aqui exige ou
autoriza** voltar à narrativa de skip/latch como otimização de validador.

## 6. Disciplina de teste

- ✅ **Comportamental:** DV correto ⇒ achado; DV corrompido ⇒ não-achado. Vetores **públicos
  oficiais** por padrão/país
- ✅ **Property-based** para paridade Python↔Rust (se e quando §5.3)
- ❌ **PROIBIDO: invariante negativa** — teste que congela limitação como contrato (ex.: "este
  padrão deve **jamais** traduzir para o motor X"). Pune melhoria, acopla motor a catálogo aberto, e
  dá falsa sensação de cobertura. Cicatriz real: `test_lgpd_cnpj_alnum_stays_python_fallback`
- ❌ **PROIBIDO: teto numérico** como guarda (ex.: "falhar se skips > N") — quebra em mudança
  não-relacionada e não mede o que diz medir

## 7. Anti-overclaim (obrigatório no texto do relatório)

Checksum válido prova **forma matematicamente válida**. **Nunca** prova que o documento existe, está
ativo, é registrado, ou pertence a alguém. Boleto com DV válido não é boleto pagável; IBAN válido
não é conta aberta; CNPJ válido não é empresa ativa. Os três níveis de evidência
(`checksum_validated` / `structural_only` / `shape_only`) devem aparecer no relatório —
essa gradação **é** o produto.

## 8. Sequenciamento sugerido

Fase 1 (registro) → Fase 2 (Brasil, fecha #527/#1356 e **S3**) → Fase 6 (setorial: container + segredos =
maior diferencial) → Fase 3 (EU/IBAN) → Fase 5 (LATAM, alto reuso) → Fase 4 (NA)

**Racional:** Fase 2 fecha buraco admitido no código hoje e serve de piloto do contrato; Fase 6 sobe
antes das demais jurisdições porque container ISO 6346 e checksum de segredo são onde a concorrência
genérica não chega.

---

## Acceptance criteria (plan-level)

| # | Criterion | Status |
| - | --------- | ------ |
| A1 | `PLAN_CHECKSUM_VALIDATOR_REGISTRY.md` + hub + `PLANS_TODO` (S5; S3 cruzado) | ⬜ |
| A2 | Fase 1: registro + schema `validator:` + generalização do gate no detector | ⬜ |
| A3 | Fase 2: `mod11_cnpj_alnum` + boleto (#1356); fecha lacuna #527 / sprint S3 | ⬜ |
| A4 | Issues filhas #1639–#1642 rastreadas sem duplicar escopo no hub | ⬜ |
| A5 | Sem prefiltro skip/latch, sem invariante negativa, sem teto numérico de skip | ⬜ |
