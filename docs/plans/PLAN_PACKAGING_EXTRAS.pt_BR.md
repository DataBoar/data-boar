# Plano: extras de conector SQL + install enxuto do core (#1047)

<!-- plans-hub-summary: Extras SQL + core enxuto (#1047); v1.8.0 #1059 [noavx] wheelhouse (#929) + perfis [nlp]/[ocr]/[dl]; detecção de CPU + degrade LOUD FN-first -->
<!-- plans-hub-related: PLAN_WHEELHOUSE_DISTRIBUTION.md, PLAN_CI_OPTIONAL_EXTRAS_COVERAGE.md, PLAN_QUICKSTART.md -->

**English:** [PLAN_PACKAGING_EXTRAS.md](PLAN_PACKAGING_EXTRAS.md)

**Status:** Em andamento (extras SQL em `main`; o survey v1.8.0 [#1059](https://github.com/DataBoar/data-boar/issues/1059) enriquece este plano — não arquivar)
**Data:** 2026-06-27 (onda v1.8.0: 2026-08-27)
**Autores:** Fabio Leitao (operador); Cursor executor
**Prioridade:** H1 (packaging / ICP de install amplo)
**Milestone:** v1.8.0
**GitHub:** [#1047](https://github.com/DataBoar/data-boar/issues/1047) `[P2][packaging]` · **[#1059](https://github.com/DataBoar/data-boar/issues/1059)** (`[noavx]` / perfis de capacidade; receita [#929](https://github.com/DataBoar/data-boar/issues/929)) · **Fatia de container:** [#1400](https://github.com/DataBoar/data-boar/issues/1400) · [#1401](https://github.com/DataBoar/data-boar/issues/1401) · [#1399](https://github.com/DataBoar/data-boar/issues/1399) · [#1402](https://github.com/DataBoar/data-boar/issues/1402) · **Job CI de extras (não muda nomes de extra):** [#1638](https://github.com/DataBoar/data-boar/issues/1638) [PLAN_CI_OPTIONAL_EXTRAS_COVERAGE.md](PLAN_CI_OPTIONAL_EXTRAS_COVERAGE.md)
**Relacionado:** [ADR-0031](../adr/ADR-0031-pypi-packaging-hatchling-flat-layout.md) · [ADR-0073](../adr/ADR-0073-version-scheme-octet-maturity-and-roadmap.md) · [#1042](https://github.com/DataBoar/data-boar/issues/1042) (publicação PyPI) · [CONTRIBUTING.md](../../CONTRIBUTING.md) · [PLAN_WHEELHOUSE_DISTRIBUTION.md](PLAN_WHEELHOUSE_DISTRIBUTION.md)

**Sincronizado com:** [PLANS_TODO.md](PLANS_TODO.md)

---

## Problema

`pip install data-boar` / `pipx install data-boar` puxava **todos** os drivers SQL como dependências de **core** (`mariadb`, `mysqlclient`, `psycopg2-binary`, `pyodbc`, `oracledb`, `pymysql`, mais o placeholder suspeito `mysql>=0.0.3`). Em plataformas sem wheels (ex.: **Python 3.14** no Void Linux), **extensões C** compilam e falham se não houver toolchain + headers de desenvolvimento — bloqueando o install para quem só varre **arquivos** ou **SQLite**.

Evidência: smoke multi-nó 2026-06-27 (host lab py3.12 OK; host lab py3.14 restrito falhou no build de origem do `mariadb`). Corpo da issue + log uv privado.

---

## Decisão

### Extras (por engine)

| Extra | Pacotes PyPI | `driver` / dialecto típico |
| ----- | ------------ | -------------------------- |
| `postgres` | `psycopg2-binary` | `postgresql` / `postgresql+psycopg2` |
| `mysql` | `pymysql` (Python puro) | `mysql` / `mysql+pymysql` |
| `mariadb` | `mariadb` (Connector/C) | `mariadb` / `mariadb+mariadbconnector` |
| `mssql` | `pymssql` | `mssql` / `mssql+pymssql` (driver bare padrão) |
| `mssql-pymssql` | `pymssql` | alias de `mssql` (#1588) |
| `mssql-pyodbc` | `pyodbc` | só `mssql+pyodbc` |
| `oracle` | `oracledb` | `oracle` / `oracle+oracledb` |
| `sql-all` | união dos acima | meta-extra de conveniência (Docker / imagens de lab) |

O **core** mantém `sqlalchemy` + **SQLite** (stdlib). **Remover** do core: `mariadb`, `mysqlclient`, `mysql` (placeholder), `psycopg2-binary`, `pymysql`, `pyodbc`, `oracledb`.

### Contrato de import lazy

- `connectors/sql_connector.py` sempre **registra** os tipos de engine SQL (o YAML resolve).
- `connect()` chama `ensure_sql_driver_available(driver)` → `ImportError` claro com `pip install 'data-boar[<extra>]'` quando o módulo do driver falta.
- `core/engine.py` importa `SQLConnector` só para typing/bases de amostragem (sem install de driver no import).

### Tensão de versão / PyPI (emenda ADR-0073)

O PyPI é **imutável por versão**; **não** há canal lateral `maturity_build` no índice.

| Opção | Veredito |
| ----- | -------- |
| **`1.7.4.post1`** em `[project] version` | **Escolhido** — post-release PEP 440 para correção de packaging na **mesma linha pública** (`1.7.4`); **não** `1.7.5`; **não** um quarto segmento semver (`1.7.4.202`). |
| Adiar para **`1.8.0`** | **Rejeitado** — `1.8.0` é a **próxima linha de arquitetura**, não hotfix de packaging. |
| Reenviar **`1.7.4`** | **Impossível** no PyPI. |

**Canal lateral:** `[tool.databoar] maturity_build` **201 → 202** (maturidade de correção de packaging). **Nunca** copiar o octeto no About como quarto segmento.

**Tags Git/Docker:** permanecem na linha `1.7.4` até o operador no **release-ritual** publicar `1.7.4.post1` no PyPI (workflow da #1042).

---

## Passos de execução

| Passo | Escopo | Status |
| ----- | ------ | ------ |
| **0** | Branch `feat/sql-extras-1047`, este plano, cláusula PyPI do ADR-0073, nota de extras no ADR-0031 | ✅ |
| **1** | `pyproject.toml`: extras, corte do core, `version = "1.7.4.post1"`, `maturity_build = 202` | ✅ |
| **2** | `connectors/sql_driver_deps.py`, guarda do `sql_connector`, `engine.py`, dialecto mariadb no `DRIVER_MAP` | ✅ |
| **3** | Testes: core não lista C-ext SQL; mensagem de extra ausente | ✅ |
| **4** | Docs EN+pt-BR (USAGE, TECH_GUIDE, CONTRIBUTING); `Dockerfile` instala mínimos de driver SQL | ✅ |
| **5** | `uv lock`, `uv export`, `./scripts/check-all.sh`, PR `Closes #1047` | ✅ |

---

## Critérios de aceite (#1047)

- [x] Drivers SQL com extensão C **fora** de `[project].dependencies`
- [x] import lazy + dica acionável de extra no connect
- [x] placeholder `mysql>=0.0.3` **removido**
- [x] `pip install data-boar` (core) passa em py3.14 sem toolchain de DB (prova CI/dev via guarda de dependência + smoke do operador)
- [x] Docs de install listam extras SQL
- [x] Este plano + **ADR-0031** + cláusula PyPI do **ADR-0073** atualizados
- [x] Expressão PyPI documentada: **`1.7.4.post1`**

---

## Fora de escopo (só a fatia de biblioteca #1047)

- Stack ML/plot (`numpy`/`pandas`/…) como extras — nota secundária da issue #1047; acompanhar à parte.
- A corrida de publicação no PyPI em si — **release-ritual** do operador depois do merge.

---

## Container como artefato de entrega (no escopo — #1400 / #1401 / #1399 / #1402)

**Decisão do operador (1.8.x):** manter a **base distroless enxuta**; estender conectores em **runtime** montando wheels ABI-compatíveis pré-construídas em **`/extras`** com **`PYTHONPATH=/extras:/app`** (`/extras` primeiro). **Sem** imagem gorda dos 18 extras, **sem** matriz de imagens, **sem** exigir que o cliente faça `Dockerfile FROM` da nossa imagem e reconstrua.

| Passo | Escopo | Status |
| ----- | ------ | ------ |
| **C0** | `/extras` + `PYTHONPATH` + `VOLUME` + `DATA_BOAR_MACHINE_SEED=` no `Dockerfile` / `Dockerfile.nogil`; nonroot 65532 | ✅ |
| **C1** | Imagem base instala só `sql-community,mssql,oracle` do pyproject (não lista de pacotes à mão; não os 18) | ✅ |
| **C2** | `EXTRAS_MANIFEST.json` gerado de `[project.optional-dependencies]` + probe de import; `--check-extras`; smoke falha se `in_artifact` desviar | ✅ |
| **C3** | ABI fail-closed quando o pack montado não casa com o interpretador; mensagens de conector ausente nomeiam extra + path `/extras` (#1402) | ✅ |
| **C4** | Docs EN+pt-BR (`DOCKER_SETUP`, `USAGE`); este plano; `PLANS_TODO`; `plans_hub_sync` | ✅ |

**Ainda fora desta fatia de container:** publicar um artefato extras-pack assinado e versionado por ABI (follow-on da #1400).

---

## Pendente

| Item | Notas |
| ---- | ----- |
| Upload PyPI pós-merge | `1.7.4.post1` via `publish-pypi.yml` (fatia de biblioteca) |
| Smoke do operador | `pipx install data-boar==1.7.4.post1` no host lab py3.14 restrito |
| Smoke de container | `docker-image-smoke.sh` após build de lab; montar pack `/extras` sem `--user 0` |

---

## Changelog

- **2026-08-27:** Survey v1.8.0 **[#1059](https://github.com/DataBoar/data-boar/issues/1059)** — `[noavx]` = wheelhouse **provado** na [#929](https://github.com/DataBoar/data-boar/issues/929) (OpenBLAS do sistema, sem AVX embutido); perfis `[nlp]` / `[ocr]` / `[dl]`; installer detecta CPU; degrade **LOUD + FN-first** (nunca silencioso).
- **2026-06-27:** Plano inicial — extras SQL + core enxuto (#1047); depois mount `/extras` no container (#1400–#1402).

---

## Onda v1.8.0 — wheelhouse `[noavx]` + perfis de capacidade ([#1059](https://github.com/DataBoar/data-boar/issues/1059))

**Motivo:** Survey competitivo (dossiê privado). **Docs-first** nesta PR; esta onda **não** adiciona extra em `pyproject.toml`, binário de installer novo nem uma segunda receita de wheelhouse.

**Invariante (doutrina):** Degradação de capacidade é **LOUD e FN-first**, nunca silenciosa. Se o perfil reduzido **detecta menos**, o risco é **falso negativo**. Num scanner de PII isso é o pior resultado — o operador **precisa ver na saída** que esta execução está **reduzida** (banner / log / rodapé do relatório). Mesma regra do **piso de min-spec**: metal Alpine sem AVX no gate (**[#821](https://github.com/DataBoar/data-boar/issues/821)** / **[#406](https://github.com/DataBoar/data-boar/issues/406)**) — o artefato **se adapta ao piso e declara o que conseguiu**. SIGILL com **zero** traceback Python (classe do título da [#929](https://github.com/DataBoar/data-boar/issues/929)) é o anti-padrão que esta onda proíbe.

**O que não se afirma:** Nenhum número de performance (incluindo prefiltro Rust) sem arquivo pinado em `tests/benchmarks/`. `[noavx]` **não** é extra pip publicado em `main` hoje. O installer que escolhe CPU automaticamente está **especificado aqui**, não implementado nesta fatia de docs.

### O que já existe (não inventar um segundo stack)

| Superfície | Papel hoje | Relevância #1059 |
| ---------- | ---------- | ---------------- |
| Extras SQL (#1047) + mount `/extras` | Core enxuto; drivers opcionais | Sem mudança; `[noavx]` é **CPU/ISA**, não SQL |
| `numpy` / `scipy` / `scikit-learn` no core | ML padrão (TF-IDF + RandomForest) | Wheels PyPI podem **SIGILL** sem AVX; o wheelhouse é o conserto medido |
| Extra `[dl]` | sentence-transformers opcional | ISA mais pesada; pular ou falhar **LOUD** sem AVX — nunca omitir embeddings em silêncio |
| Extra `[richmedia]` | `pytesseract` + `tesseract-ocr` do sistema | O `[ocr]` do comprador mapeia aqui; binário ausente já é miss nomeada — manter LOUD |
| [PLAN_WHEELHOUSE_DISTRIBUTION.md](PLAN_WHEELHOUSE_DISTRIBUTION.md) | Células x86-64-v1 hospedadas + CI da receita | Distribuição **canônica** no-AVX; pip/pipx em dois passos em [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) |
| Onboarding pip / pipx | [PLAN_QUICKSTART.md](PLAN_QUICKSTART.md) + USAGE | Onde a detecção de CPU **escolhe** stock vs wheelhouse |

### `[noavx]` = receita de wheelhouse **provada** na [#929](https://github.com/DataBoar/data-boar/issues/929)

RCA de lab (metal, min-spec, sem AVX): o assassino é o **`libscipy_openblas` embutido na wheel PyPI** (AVX/SSE incondicional), não o numpy-core depois de `-Dcpu-baseline=none`. Variáveis de ambiente (`OPENBLAS_CORETYPE`, `NPY_DISABLE_CPU_FEATURES`) **não** consertam um baseline compilado.

**Conserto medido (não re-hipotetizar):** build de numpy/scipy/sklearn **a partir do source contra o OpenBLAS do sistema** (`DYNAMIC_ARCH` em runtime = seguro sem AVX); **não** embutir `scipy-openblas`. Confirmar no log: OpenBLAS do sistema **YES**, `scipy-openblas` **NO**. Revalidar **no metal** (a caixa de build com AVX pode importar uma wheel envenenada). Receita completa + armadilhas na **#929** e no plano de wheelhouse (sem `CFLAGS=-march=…`; auditar wheels por OpenBLAS embutido).

**Nome de extra no produto:** `data-boar[noavx]` significa **instalar por esse caminho de wheelhouse** (mais `openblas` / `libgomp` de runtime como a receita documenta) — **não** uma implementação nova de BLAS no tree. Ligar ao onboarding **pip / pipx** já existente (dois passos `--find-links` / índice), não a um canal greenfield.

### Perfis de capacidade (nomes do comprador → extras que existem ou ficam nomeados)

| Perfil | Pedido do comprador | Mapear em (sem segundo motor) | Regra da execução reduzida |
| ------ | ------------------- | ----------------------------- | -------------------------- |
| **`[nlp]`** | Regex + ML clássico | Caminho do detector no core (sklearn já no core) com wheels **stock** ou **wheelhouse** | Se kernels de ML faltam ou são só v1, **dizer**; só-regex é risco de FN |
| **`[ocr]`** | Texto em imagem | `[richmedia]` existente + Tesseract do sistema | Tesseract ausente / flag desligada = skip **declarado**, não silencioso |
| **`[dl]`** | Embeddings | Extra `[dl]` existente | Sem AVX, **não** carregar wheels DL AVX do PyPI; degradar **LOUD** (só regex+ML) |

Aliases exatos de extra no `pyproject.toml` ficam **TBD** até uma fatia de packaging; esta PR só trava o contrato de **mapeamento + degrade LOUD**.

### Installer detecta a CPU (planejado)

| CPU | Escolher | Tem que declarar |
| --- | -------- | ---------------- |
| Capaz (AVX / x86-64-v2+ exigido pelas wheels **stock** do PyPI) | PyPI padrão / wheel stock | Stack anunciado completo (`[dl]` se pedido) |
| Sem AVX (min-spec / x86-64-v1) | Wheelhouse (caminho `[noavx]`) | Perfil **reduzido** em stdout + relatório: quais extras carregaram, quais pulou, aviso FN-first |

**Não** auto-instalar wheels AVX numa CPU v1 (SIGILL). **Não** fingir que o DL rodou se não rodou. Pre-flight **antes** de `import numpy` continua a lição da #929 (SIGILL não é `try`/`except`).

---

## Extras de pacote nativo (issue #2185)

**Contexto:** Os pacotes nativos (.rpm/.deb/.apk/.pkg.tar.zst) entregam apenas o núcleo. O Python embutido (cp314t free-threading) bloqueia `pip` via PEP 668. Subpacotes são definidos em `packaging/nfpm/generated/` mas **não são publicados** no release (`release-manifest.json` `native_packages[]` lista apenas os 4 formatos principais).

### Receita do operador (verificada contra arquivos do repo)

Os seguintes mecanismos foram testados no AlmaLinux 9.8 com `data-boar-1.8.0-1.x86_64.rpm` (Python embutido: `/usr/lib/data-boar/python3.14t/bin/python3.14t`, cp314t free-threading):

| Mecanismo | Resultado | Notas |
| --------- | --------- | ----- |
| `pip install` / `pip install --user` | **Bloqueado** | PEP 668 ("managed by uv") |
| `pip install --target <dir> <pkg>` + `PYTHONPATH=<dir>` | **Funciona** | Launcher `/usr/bin/data-boar` respeita `PYTHONPATH`; só `--version` testado; scan com módulo extra **não verificado** |
| `python3 -m venv --system-site-packages ~/xvenv` + `pip install` no venv | **Funciona** para `nosql`, `dataformats` | Venv não tem script `data-boar`; launcher + `PYTHONPATH` ainda necessário |

**Não verificado:**
- Se um scan efetivamente usa módulos do venv (não só `import`)
- Caminho de upgrade com venv existente
- Formatos `.deb`, `.apk`, `.pkg.tar.zst`
- Extras `richmedia`, `shares`, `detection-fuzzy`, `bigdata`

### Status por extra por evidência (dos comentários da issue #2185)

| Extra | Pacotes | Status | Dependências de sistema | Notas |
| ----- | ------- | ------ | ----------------------- | ----- |
| `nosql` | `pymongo`, `redis` | **Funciona** | Nenhuma | Instala e importa no venv |
| `dataformats` | `pyarrow`, `fastavro`, `dbfread` | **Funciona** | Nenhuma | Instala e importa no venv |
| `mssql` | `pymssql` | **Parcial** | FreeTDS (`libsybdb.so.5`) | Instala; import falha sem FreeTDS (não testado) |
| `compressed` | `py7zr` | **Faz falha** | Compilador (gcc/cmake), `brotli` | Sem wheel para cp314t; cai em build de fonte |
| `dl` | `sentence-transformers` | **Faz falha** | Rust, compilador | `safetensors` cai em build de fonte |
| `richmedia` | `pytesseract`, `pillow-heif`, `mutagen` | **Não verificado** | Tesseract binário, compilador | `pytesseract` precisa tesseract-ocr |
| `shares` | `smbprotocol`, `webdavclient3`, `requests_ntlm` | **Não verificado** | Nenhuma aparente | Python puro |
| `detection-fuzzy` | `rapidfuzz` | **Não verificado** | Compilador | Extensão C++ |
| `bigdata` | `snowflake-connector-python` | **Não verificado** | Nenhuma aparente | Python puro |

**Bug `--check-extras`:** O comando `data-boar --check-extras` quebra com `FileNotFoundError: .../site-packages/pyproject.toml` (`core/extras_manifest.py:97`). O pacote nativo não instala o `pyproject.toml`, quebrando a promessa do help ("first step when a connector fails for missing dependencies"). **Não verificado** se corrigido.

### Distribuição dos subpacotes (decisão aberta — pendente decisão do operador)

Os subpacotes são definidos em `packaging/nfpm/generated/` (6 extras: compressed, dataformats, mssql, nosql, richmedia, shares) mas **não aparecem** no `release-manifest.json` `native_packages[]`. Só os 4 pacotes de formato principal são publicados.

**Opções:**
1. **Publicar subpacotes como assets do release** (um por formato: .deb/.rpm/.apk/.pkg.tar.zst) — usuários instalam via gerenciador de pacotes; exige mudanças no CI/CD e infra de assinatura
2. **Documentar só a receita de venv** — sem subpacotes; usuários montam seus próprios wheels/venvs; menor esforço mas exige compilador para alguns extras
3. **Híbrido** — publicar subpacotes para extras "fáceis" (Python puro: nosql, dataformats, shares, bigdata); documentar receita de venv para extras "difíceis" (compressed, dl, richmedia) que exigem compilador/Rust

**Trade-offs:**
- Opção 1: Melhor UX; maior manutenção (CI/CD, assinatura, 4 formatos × N extras)
- Opção 2: Menor esforço; pior UX para extras que precisam de compilador (usuários travados)
- Opção 3: Equilibrada; requer classificar extras por complexidade de build

**Decisão:** Pendente decisão do operador. Marcado como AC 3 na issue #2185.

### Cobertura de formatos de pacote nativo

| Formato | Subpacotes publicados | Status |
| ------- | --------------------- | ------ |
| `.rpm` | **Nenhum** (só pacote principal) | Verificado no AlmaLinux 9.8 |
| `.deb` | **Nenhum** | Não verificado |
| `.apk` | **Nenhum** | Não verificado |
| `.pkg.tar.zst` (Arch) | **Nenhum** | Não verificado |

**Nota:** O diretório `packaging/nfpm/generated/` contém 6 YAMLs de subpacotes, mas eles não estão no pipeline de release. O `EXTRAS_MANIFEST.native.json` lista 20 extras, e só `mssql`, `oracle` e `sql-community` têm `in_artifact: true` (incluídos na imagem base do container). Nenhum subpacote é produzido para pacotes nativos hoje.

### Página de man (relacionado a #2163)

A documentação dos extras deve aparecer também no `man data-boar` do pacote nativo (hoje ausente, rastreado em #2163). A man page deve explicar a receita escolhida (venv + `--system-site-packages` + `PYTHONPATH` ou `DATA_BOAR_EXTRAS_PATH`).

### Decisão sobre boar_fast_filter (relacionado)

Por comentários da issue: `boar_fast_filter` vai pré-compilado no pacote base. Opções:
- (a) Manter no pacote base com gating por licença (depende do fix da #2180)
- (b) Subpacote opt-in separado `data-boar-fast-filter` no canal comercial (ADR-0089 §3, 3B); repo público assinado leva só o Community

Fallback Python existe (demo produz mesmos findings sem módulo Rust), então (b) é viável tecnicamente. Decisão é do operador (AC 3 na #2185).

---

### Tabela de execução (docs-first → fatias posteriores)

| Passo | Entregável | Status |
| ----- | ---------- | ------ |
| P1 | Esta seção do plano + resumo no hub + linhas do survey em `PLANS_TODO` | ✅ Feito (PR de docs) |
| P2 | Nomear `[noavx]` no onboarding pip/pipx de USAGE/TECH_GUIDE; ponteiro para #929 + dois passos do wheelhouse (sem receita nova) | ✅ Feito (#929 / PR #1874) |
| P3 | Pre-flight de CPU + banner / rodapé de capacidade **LOUD** (texto FN-first) | 🔄 Pre-flight em runtime + aviso no log (#929); banner / rodapé do relatório ainda aberto |
| P4 | Aliases opcionais de extra `[nlp]` / `[ocr]` no `pyproject` se permanecerem distintos de `[dl]` / `[richmedia]` | ⬜ Pendente |
