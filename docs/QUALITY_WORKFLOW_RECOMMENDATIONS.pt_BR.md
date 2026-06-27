# Fluxo de qualidade: recomendações e camadas adicionais

**English:** [QUALITY_WORKFLOW_RECOMMENDATIONS.md](QUALITY_WORKFLOW_RECOMMENDATIONS.md)

Este documento sugere **camadas adicionais** (ferramentas, hábitos e fluxo de trabalho) para manter o app funcionando com segurança, de forma legível e reduzir toil, retrabalho e refatorações. Use como checklist; adote de forma incremental. O que já existe está em [TESTING.md](TESTING.md), [SECURITY.md](../SECURITY.md) e na regra/skill do Cursor (`.cursor/rules/quality-sonarqube-codeql.mdc`, `.cursor/skills/quality-sonarqube-codeql/SKILL.md`).

**Já implementado:** Ruff roda no CI (`uv run ruff check .`); `pyproject.toml` tem `extend-exclude` para diretórios legados (`db`, `scanners`, `utils`, `logging_custom`). Execute `uv run ruff check .` antes do PR. Opcional: `uv run pre-commit install` para que o Ruff rode no commit (veja `.pre-commit-config.yaml`).

## O que você já tem (linha de base)

- **Testes:** Suite completa de pytest com `-W error`; testes estilo SonarQube (S3981, S3776, S4423, S5706, S1192, etc.), testes de segurança (SQL injection, path traversal, safe_load), lint de markdown (incluindo `.cursor/`).
- **CI:** Testes + `pip-audit` a cada push/PR; SonarQube opcional quando `SONAR_TOKEN` está definido; CodeQL em workflow separado.
- **Cursor:** Regra e skill para que o agente evite violações SonarQube/CodeQL e execute testes de qualidade após editar Python/markdown.
- **Docs:** CONTRIBUTING (checklist de release, auditoria, versões mínimas), SECURITY.md, TESTING.md, hardening de deploy.

---

## Camadas recomendadas (por prioridade)

### 1. Ruff no CI (alto valor, baixo esforço)

**Por quê:** O Ruff captura problemas de estilo, imports não utilizados e muitos padrões propensos a bugs antes de chegarem ao main. O template de PR diz "Sem novos problemas de linter/format" mas o Ruff não rodava no CI, tornando fácil esquecer.

#### O que fazer (Ruff no CI):

- Adicionar um job (ou step) de **lint** em `.github/workflows/ci.yml` que execute:
  - `uv run ruff check .` (e opcionalmente `uv run ruff format --check .`).
- Manter a config do Ruff em `pyproject.toml` (já existe `[tool.ruff.lint.per-file-ignores]`); adicionar uma seção `[tool.ruff]` com `target-version`, `line-length` e conjuntos de regras se quiser consistência.
- Atualizar CONTRIBUTING e a regra/skill de qualidade: "Antes do PR, execute `uv run ruff check .` (e corrija ou ajuste a config)."

**Previne:** Deriva de estilo, código não utilizado, muitos bugs simples; reduz toil de revisão e correções pós-merge.

---

### 2. Hooks de pre-commit (opcional mas eficaz)

**Por quê:** Captura problemas **antes** do push, fazendo o CI falhar menos e evitando a situação de "correr atrás da cauda" em estilo/lint.

#### O que fazer (pre-commit):

- Adicionar [pre-commit](https://pre-commit.com/) (ex.: no grupo de dependências de dev) e um `.pre-commit-config.yaml` com:
  - `ruff` (check + format),
  - `markdownlint` ou um hook que execute `scripts/fix_markdown_sonar.py` / `pytest tests/test_markdown_lint.py`,
  - opcionalmente um subset "rápido" de pytest (ex.: `test_markdown_lint`, `test_sonarqube_python`, `test_security`) se for suficientemente veloz.
- Documentar em CONTRIBUTING: "Instale os hooks com `pre-commit install`; eles rodam no commit."

**Previne:** Push de commits que vão falhar no CI; mantém local e CI sincronizados.

---

### 3. Bandit (linter de segurança) — dev + CI (medium+)

**Por quê:** Complementa CodeQL, Semgrep e SonarQube com verificações específicas de Python: `try/except/pass`, heurísticas de string SQL ingênua, `subprocess`, `assert` fora de testes, strings que parecem senhas, etc.

#### O que fazemos (Bandit):

- **`bandit`** está no grupo **`uv` dev**; **`[tool.bandit]`** em **`pyproject.toml`** define **`exclude_dirs`** e **`skips`** (ex.: **B608** onde SQL usa identificadores verificados — alinhado com exclusões do Semgrep em [`.github/workflows/semgrep.yml`](../.github/workflows/semgrep.yml)).
- **CI:** Job **Bandit (medium+)** em [`.github/workflows/ci.yml`](../.github/workflows/ci.yml): `uv run bandit -c pyproject.toml -r api core config connectors database file_scan report main.py -ll -q` (falha apenas em **medium** e **high** até triagem do **low**).
- **Triagem:** `uv run bandit -c pyproject.toml -r … -i` para **low**; corrigir, usar **`# nosec Bxxx`** com razão curta ou estender a config — veja [SECURITY.md](../SECURITY.md) e **`[tool.bandit]`** em **`pyproject.toml`**.
- **Hábito do agente:** [`.cursor/skills/quality-sonarqube-codeql/SKILL.md`](../.cursor/skills/quality-sonarqube-codeql/SKILL.md) — executar Bandit após edições Python sensíveis à segurança quando relevante.

**Previne:** Padrões anti-segurança comuns que os testes podem não cobrir.

---

### 4. Semgrep (CI habilitado)

**Por quê:** SAST baseado em padrões; regras customizadas e da comunidade para padrões de segurança e bugs. Se sobrepõe ao CodeQL e SonarQube, mas pode capturar padrões específicos do projeto.

#### O que fazemos (Semgrep):

- **GitHub Actions:** [`.github/workflows/semgrep.yml`](../.github/workflows/semgrep.yml) roda em push/PR para `main`/`master` usando o container oficial **`semgrep/semgrep`**, ruleset **`p/python`**, **`--metrics=off`** e uma **regra excluída** documentada nos comentários do workflow (falso positivo em caminhos `sqlalchemy.text` verificados).
- **Local (opcional):** `uvx semgrep scan --config p/python --metrics=off` com o mesmo **`--exclude-rule`** do workflow (veja **§ check-all espelho unificado** abaixo). Regras customizadas podem ficar sob `.semgrep/` no futuro.

**Previne:** Padrões extras de vulnerabilidade/bug em Python; complementa o CodeQL.

---

### 4b. Zizmor (análise estática de workflows)

**Por quê:** Workflows do GitHub Actions são código — `permissions` mal configuradas, actions sem pin ou padrões perigosos de `pull_request_target` são riscos de cadeia de suprimentos e abuso. O **Zizmor** varre `.github/workflows/` nessas classes de problema.

#### O que fazemos (Zizmor):

- **CI:** [`.github/workflows/zizmor.yml`](../.github/workflows/zizmor.yml) roda em push/PR via **`zizmorcore/zizmor-action`** (SHA fixo). **Avisório** por padrão, salvo **`ZIZMOR_ENFORCE`** / **`ENFORCE_ZIZMOR`** no repo — veja [OPERATOR_NOTIFICATION_CHANNELS.md](ops/OPERATOR_NOTIFICATION_CHANNELS.md) e **`scripts/workflow-security-lint.sh`**.
- **Local:** `uvx zizmor .github/workflows/` (mesmo caminho que **`workflow-security-lint.sh`**). O **`check-all`** executa Zizmor no tier **padrão** de security scans e **falha** em achados (postura shift-left antes do merge).

**Previne:** Misconfigurações de workflow que Bandit/Semgrep não veem.

---

### 4c. `check-all` como espelho unificado do CI (tiered)

**Por quê:** Contribuidores na estação **Linux primary** e agentes devem rodar **um** ritual local que espelha **o que o CI vai rodar**, sem redigitar comandos de cinco workflows.

#### Tiers (`./scripts/check-all.sh` / `.\scripts\check-all.ps1`)

| Tier | Quando | O quê (após gatekeeper, Rust, plans-stats, hubs, Pester, pre-commit, pytest) |
| ---- | ------ | ---------------------------------------------------------------------------- |
| **Padrão (offline-capable)** | Todo pré-PR / slice do agente | **Bandit** — `uv run bandit -c pyproject.toml -r api core config connectors database file_scan report main.py -ll -q`. **Zizmor** — `uvx zizmor .github/workflows/`. |
| **Opt-in `--enforced` / `-Enforced`** | Antes de PRs sensíveis à segurança | **+ Semgrep** — `uvx semgrep scan --config p/python --metrics=off` com o mesmo **`--exclude-rule`** de [`.github/workflows/semgrep.yml`](../.github/workflows/semgrep.yml), **`--error .`**. Requer rede para `uvx`. |

**Fail-collect:** O tier de security scans roda **todos** os scans do tier e só então reporta **todas** as falhas (sem fail-fast entre Bandit / Zizmor / Semgrep). Gates anteriores (gatekeeper PII, Rust, pre-commit) ainda abortam imediatamente — veja **`scripts/check-all-security-scans.sh`** / **`.ps1`**.

**Fora do `check-all` padrão (jobs CI separados):** CodeQL, Sonar, pip-audit, build SBOM — rodar via CI ou scripts dedicados.

#### Ondas futuras (mesmo doc — fora do escopo de #1044)

| Onda | Intenção | Status |
| ---- | -------- | ------ |
| **Onda 2** | Hooks **pre-commit** opcionais para Bandit / Zizmor (subconjunto rápido) | Adiado |
| **Onda 3** | Regra Cursor: **`check-all --enforced` antes de PR** quando o slice toca conectores, workflows ou auth | Adiado — ponteiro na **§10** |

---

### ROI — economia shift-left

Rodar **`check-all`** localmente (tier padrão) troca **~2–5 minutos** no PC de dev por **evitar uma volta completa no CI** (fila + matriz + container Semgrep), tipicamente **15–40+ minutos** quando Bandit ou workflow falham tarde.

| Classe de achado | Sem espelho local | Com tier padrão do `check-all` |
| ---------------- | ----------------- | ------------------------------ |
| Bandit em connectors | Falha no job **Bandit** depois de lint+test | Surge num passe local |
| Drift de permissão em workflow | Falha no workflow **Zizmor** (ou fica avisório) | Surge antes do push |
| Caminho FP SQLAlchemy no Semgrep | Só com **`--enforced`** ou Semgrep no CI | Opt-in operador/agente — mesmo comando do container |

**Hábito token-aware:** Use **`./scripts/check-all.sh --skip-pre-commit`** só ao iterar testes; rode **`check-all` completo** antes de abrir o PR. Use **`--enforced`** quando o diff tocar **superfícies de segurança** da Onda 3 — não em todo slice só de docs.

---

### 5. Verificação de tipos com mypy (gradual — somente dev por ora)

**Por quê:** Tipos tornam refatorações mais seguras e reduzem regressões do tipo "funcionava até mudarmos X".

#### O que temos (mypy):

- **`mypy`** e **`types-PyYAML`** estão no grupo **`uv` dev**. **`[tool.mypy]`** em **`pyproject.toml`** começa de forma **suave**: `disallow_untyped_defs = false`, `check_untyped_defs = false`, `warn_return_any = false`, `ignore_missing_imports = true`, `warn_unused_ignores = false` — **não** é "modo strict".
- **Local:** `uv run mypy api core` (mypy ainda segue imports para **`config`**, **`connectors`**, etc., então espere **muitos erros** até triagem módulo por módulo). **CI:** ainda não configurado — adicionar job apenas quando o relatório estiver próximo de limpo, ou usar `continue-on-error` deliberadamente.

**Previne:** Bugs relacionados a tipos assim que a base de código for alinhada; até lá, mypy é um **sinal local opcional**, não um gate de merge.

**Apertar com o tempo:** `disallow_untyped_defs = true` (ou overrides por pacote), `warn_return_any = true`, adicionar stubs (`types-*`) ou `[[tool.mypy.overrides]]` para lacunas de terceiros.

---

### 6. MD029 e o script de correção (reduzir retrabalho)

**Por quê:** `scripts/fix_markdown_sonar.py` aplica MD029 (estilo de lista ordenada 1/1/1), convertendo todos os números de lista para `1.`. Isso pode quebrar numeração **semântica** (ex.: "Passo 1, 2, 3" vira "1, 1, 1") e força reedição manual em muitos docs.

**Decisão aceita (registro):** [ADR 0001](adr/ADR-0001-markdown-fix-script-md029-and-semantic-step-lists.md) — manter MD029 no script; restaurar **1. 2. 3.** manualmente para listas de passos reais; revisar heurísticas mais inteligentes apenas se o atrito aumentar.

#### O que fazer (MD029):

- **Prática atual:** (c) documentada em CONTRIBUTING, regra markdown-lint e ADR 0001. As alternativas (a) pular MD029 em alguns contextos ou (b) parar de aplicar MD029 globalmente permanecem como opções **futuras** caso o retrabalho manual se torne excessivo.

**Previne:** Retrabalho repetido e confusão em docs após cada execução de correção de markdown.

---

### 7. Registros de arquitetura / decisões (reduzir refatorações erradas)

**Por quê:** Quando o "porquê" está documentado, refatorações têm menos probabilidade de reintroduzir os mesmos erros ou toil.

#### O que temos (ADRs):

- **Índice:** [docs/adr/README.md](adr/README.md) ([pt-BR](adr/README.pt_BR.md)) — convenção de numeração, corpos de ADR somente em inglês (como arquivos de plano), baseline **[ADR 0000](adr/ADR-0000-project-origin-and-adr-baseline.md)** (origem + histórico pré-ADR), depois **[ADR 0001](adr/ADR-0001-markdown-fix-script-md029-and-semantic-step-lists.md)** (MD029 + `fix_markdown_sonar.py`), **[ADR 0004](adr/ADR-0004-external-docs-no-markdown-links-to-plans.md)** (arquitetura da informação), **[ADR 0005](adr/ADR-0005-ci-github-actions-supply-chain-pins.md)** (CI: Actions com SHA fixo + uv fixo), etc.
- **Ainda opcional / incremental:** Manter uma visão curta de **arquitetura** no TECH_GUIDE ou num futuro `docs/architecture.md` para componentes e fluxo de dados; adicionar novos `docs/adr/000N-....md` para escolhas com impacto em segurança ou processo. Linkar de SECURITY.md ou CONTRIBUTING quando uma decisão afeta contribuidores diretamente.

**Previne:** Refatoração que acidentalmente enfraquece a segurança ou duplica erros passados.

---

### 8. SBOM e cadeia de suprimentos (opcional)

**Por quê:** pip-audit já trata vulnerabilidades conhecidas; um **Software Bill of Materials** formal suporta **transparência da cadeia de suprimentos** e **resposta a incidentes** (mapear o que foi entregue).

**CI / GitHub Actions (aplicado no repo):** Actions de terceiros são fixadas a **SHAs completos**; **`astral-sh/setup-uv`** usa um **semver fixo de uv** (não `latest`); **`tests/test_github_workflows.py`** guarda **`ci.yml`**. **Decisão + limites de escopo**: **[ADR 0005](adr/ADR-0005-ci-github-actions-supply-chain-pins.md)**.

#### O que fazer (SBOM):

- **Implementado:** Workflow GitHub Actions [**SBOM**](../.github/workflows/sbom.yml) — **JSON CycloneDX** via `uv export` + `cyclonedx-py` (`sbom-python.cdx.json`), **Syft** na imagem construída (`sbom-docker-image.cdx.json`). Veja [SECURITY.md](../SECURITY.md), [RELEASE_INTEGRITY.md](RELEASE_INTEGRITY.md), [ADR 0003](adr/ADR-0003-sbom-roadmap-cyclonedx-then-syft.md). Local: [`scripts/generate-sbom.ps1`](../scripts/generate-sbom.ps1).

**Previne:** Pontos cegos no inventário de dependências e imagem; resposta mais lenta a questões de cadeia de suprimentos ou IR.

---

### 9. Checklist de PR e proteção de branch

**Por quê:** Garante que nada seja mergeado sem testes e auditoria; reduz "corrigir no main" e retrabalho.

#### O que fazer (proteção de branch):

- No GitHub: **Proteção de branch** em `main` (e `master` se usado) exigindo que status checks passem antes do merge. **Checks obrigatórios recomendados** assim que estáveis: jobs **CI** **Test** (matriz), **Lint (pre-commit)** (inclui Ruff + plans-stats + markdown + pt-BR + commercial guard), **Dependency audit**, **Bandit (medium+)** e o workflow **Semgrep**; adicione **CodeQL** se quiser que a aba Security bloqueie merges.
- **Prontidão:** Ativar proteção após o branch que carrega **Semgrep** (e outros novos workflows) estar **mergeado** e pelo menos uma execução **verde** existir para cada nome de check obrigatório.
- No **template de PR**, tornar o checklist explícito: testes passam, `uv run pre-commit run --all-files` limpo (ou hooks instalados), docs atualizados, mudanças sensíveis à segurança consideradas. Referenciar CONTRIBUTING e TESTING.md.

**Previne:** Merge de código quebrado ou inseguro e commits de correção posteriores.

---

### 10. Regras e skills do Cursor (continuar estendendo)

**Por quê:** Regras e skills guiam o agente para que menos violações sejam introduzidas inicialmente; os testes permanecem como mecanismo de aplicação.

#### O que fazer (regras e skills):

- Ao adicionar uma **nova** verificação de qualidade ou segurança (ex.: Ruff no CI, Bandit, nova regra do Sonar): atualize a **regra de qualidade** e a **skill** com o novo comando e o que evitar. Manter TESTING.md e este doc em sincronia.
- Considerar uma **regra** curta que dispare ao editar config ou código de conector: "Use queries parametrizadas; sem segredos em logs; execute testes de segurança após mudança."
- **Espelho `check-all` (#1044):** Gate local padrão = **`./scripts/check-all.sh`** / **`.\scripts\check-all.ps1`** (Bandit + Zizmor após pre-commit/pytest). Use **`--enforced`** / **`-Enforced`** para paridade Semgrep antes de PRs sensíveis — veja **§4c**. **Onda 3 (futuro):** codificar "rodar `--enforced` antes do PR" em **`.cursor/rules/quality-sonarqube-codeql.mdc`** quando o slice tocar conectores, workflows ou auth.

**Previne:** Regressões e maus hábitos que se infiltram durante edições cotidianas.

---

## Tabela resumo

| Camada                    | Objetivo                                           | Esforço | Previne                                                         |
| ------------------        | -------------------------------                    | ------ | ---------------------------------                               |
| Lint (pre-commit) no CI   | Mesmos hooks que `.pre-commit-config.yaml`         | Baixo  | Deriva em relação a hooks locais, job de lint falhando          |
| Pre-commit (local)        | Capturar no `git commit`                           | Baixo  | CI falhando, retrabalho                                         |
| Bandit                    | Padrões de segurança Python (CI **medium+**)       | Baixo  | Antipadrões que testes podem perder; triagem **low** na Phase 3 |
| Zizmor                    | Higiene de workflows GitHub Actions                | Baixo  | Deriva de permissões/pins antes do CI                          |
| Espelho `check-all`       | Paridade local tiered (Bandit+Zizmor+Semgrep opt.) | Baixo  | Falhas tardias no CI, loops de retrabalho                     |
| Semgrep                   | SAST customizado + comunidade                      | Médio  | Padrões extras de vulnerabilidade/bug                           |
| mypy                      | Segurança de tipos                                 | Médio  | Bugs de refatoração, tipos errados                              |
| MD029 / script de correção | Evitar retrabalho em docs                         | Baixo  | Correções manuais repetidas de numeração                        |
| ADRs / arquitetura        | Registrar o "porquê"                               | Baixo  | Refatorações erradas, erros repetidos                           |
| SBOM                      | Inventário de cadeia de suprimentos + resposta IR  | Baixo  | Componentes ausentes de deps/imagem ao responder a incidentes   |
| Pins de Actions / uv no CI | Reduzir deriva de tag e instalador no CI          | Baixo  | Action comprometida silenciosa ou uv flutuante sem revisão      |
| Proteção de branch        | Bloquear merges ruins                              | Baixo  | Merge de código quebrado ou inseguro                            |
| Estender regras/skills    | Guiar o agente em novos checks                     | Baixo  | Novas violações ao adicionar ferramentas                        |

---

## O que você pode não estar monitorando ainda

1. **Lint vs local** — CI roda **`pre-commit run --all-files`**; instale **`uv run pre-commit install`** para que **`git commit`** tenha paridade. **`check-all`** adiciona **Bandit + Zizmor** (padrão) e **Semgrep** opcional com **`--enforced`** — veja **§4c**.
1. **MD029 e listas semânticas** — O script de correção pode sobrescrever numeração intencional 1/2/3; veja [ADR 0001](adr/ADR-0001-markdown-fix-script-md029-and-semantic-step-lists.md).
1. **Proteção de branch** — Habilitar quando os nomes de checks obrigatórios estiverem estáveis (incluir **Semgrep** se quiser bloquear merges). Veja [WORKFLOW_DEFERRED_FOLLOWUPS.md](ops/WORKFLOW_DEFERRED_FOLLOWUPS.md).
1. **Tipos** — mypy é gradual somente-dev até triagem (§5).
1. **SBOM** — CycloneDX depois Syft; [ADR 0003](adr/ADR-0003-sbom-roadmap-cyclonedx-then-syft.md).
1. **Cadeia de suprimentos CI** — Actions e uv fixados; [ADR 0005](adr/ADR-0005-ci-github-actions-supply-chain-pins.md).

Adote o que se encaixa na sua equipe e cronograma; base sólida: **paridade pre-commit no CI**, **proteção de branch**, **MD029/script**, **Bandit** + **Semgrep**. **mypy** permanece opcional até estar limpo.
