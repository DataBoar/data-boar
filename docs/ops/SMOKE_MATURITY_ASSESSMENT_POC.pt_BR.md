# Smoke: POC de autoavaliacao de maturidade (runbook do operador)

**English:** [SMOKE_MATURITY_ASSESSMENT_POC.md](SMOKE_MATURITY_ASSESSMENT_POC.md)

**Plano:** [PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md](../plans/completed/PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md) (checklist POC ready).

Este runbook cobre os itens **manuais** **3** (happy path) e **4** (integridade opcional). O gate **1** automatizado fica na CI e no script **`scripts/smoke-maturity-assessment-poc.ps1`** (subconjunto de pytest).

**Níveis de evidência (A/B/C):** [PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md](../plans/completed/PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md) secao *POC ready — evidence levels* — **A** = este script + CI; **B** = USAGE + ADR; **C** = secao D abaixo.

---

## A. Smoke autonomo (qualquer maquina com o clone)

Na raiz do repo (Windows):

```powershell
.\scripts\smoke-maturity-assessment-poc.ps1
```

O gate completo antes do merge continua sendo **`.\scripts\check-all.ps1`** (este script nao substitui).

### Cobertura pytest vs checklist no browser (secao D)

Os testes automatizados exercitam as **mesmas rotas e persistencia** que a secao D **sem** browser. A tabela abaixo mostra o que a CI ja prova; a **secao D** continua sendo a verificacao **humana** de UX (layout, redirects, download no browser).

| Runbook D | Testes (exemplos) |
| --- | --- |
| D1 — pagina e perguntas do pack | `test_assessment_renders_yaml_pack_when_configured`, testes de tier/flag em `tests/test_api_assessment_poc.py` |
| D2 — envio e batch salvo | `test_assessment_post_persists_answers`, `test_assessment_post_persists_answers_with_integrity_secret` |
| D3 — resumo e envios recentes | Historico/batch em `tests/test_api_assessment_poc.py`, `tests/test_database.py::test_maturity_assessment_batch_summaries_newest_first` |
| D4 — batch na URL | Mesmo modulo (GET com query `saved` / `batch`) |
| D5 — export CSV / Markdown | Assercoes de export dentro de `test_assessment_post_persists_answers` |
| D6 — locale `pt-br` | `test_assessment_placeholder_200_when_flag_on_open_tier` (GET `/pt-br/assessment`) |

**Por que D ainda e obrigatorio para “POC ready completo”:** estilo, acessibilidade e download real nao substituem uma **passada do operador** no runbook — ver [PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md](../plans/completed/PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md) secao *Autonomous vs operator*.

---

## B. Smoke manual -- pre-requisitos

1. **`uv sync`** (ou o ambiente habitual).
2. Um **`config.yaml` gravavel** (ou `CONFIG_PATH`) -- **nao** commitar paths reais ou segredos; usar copia de [deploy/config.example.yaml](../../deploy/config.example.yaml) ou **arquivo** so de lab conforme [PRIVATE_OPERATOR_NOTES.md](../PRIVATE_OPERATOR_NOTES.md).
3. Copiar o **pack de exemplo** para um path referenciavel no YAML, ou apontar para o fixture do repo:

   - `tests/fixtures/maturity_assessment/sample_pack.yaml`

---

## C. Trechos minimos de `config.yaml` (lab)

Dentro de **`api:`** no topo (fundir com o arquivo existente; **sem** duplicar chave `api:`):

```yaml
api:
  maturity_self_assessment_poc_enabled: true
  maturity_assessment_pack_path: /caminho/absoluto/ou/relativo/ao/repo/sample_pack.yaml
```

Dentro de **`licensing:`** (tier Pro+ em modo open):

```yaml
licensing:
  effective_tier: pro
```

Com **`licensing.mode: enforced`**, cumprir [LICENSING_SPEC.md](../LICENSING_SPEC.md) (JWT + chave publica). Ver [USAGE.md](../USAGE.md) -- o **`dbtier`** do JWT prevalece sobre `effective_tier` no YAML quando o token e valido.

Subir a UI web (TLS ou HTTP explicito conforme [USAGE.md](../USAGE.md)):

```powershell
uv run python main.py --web --allow-insecure-http --host 127.0.0.1 --port 8088
```

Definir `CONFIG_PATH` se o YAML nao for `./config.yaml`.

---

## D. Checklist no browser (happy path)

| Passo | Acao | Criterio |
| --- | --- | --- |
| D1 | Abrir `http://127.0.0.1:8088/en/assessment` | Pagina carrega (nao **404**); perguntas do pack aparecem. |
| D2 | Responder e enviar o formulario | Redirect **303** para `.../assessment?saved=1&batch=...` |
| D3 | Na pagina de resumo | Contagem de linhas e % da rubrica (se houver `scores` no pack); tabela **Recent submissions** com o batch. |
| D4 | Clicar no link de resumo / historico | Mesmo batch na URL. |
| D5 | **Download CSV** (e opcionalmente Markdown) | Arquivo baixa; CSV com ids / respostas. |
| D6 | `http://127.0.0.1:8088/pt-br/assessment` | Mesmo fluxo em pt-BR (`api/locales/pt-BR.json`). |

---

## E. Integridade opcional (item 4)

1. Parar o processo. Definir **`DATA_BOAR_MATURITY_INTEGRITY_SECRET`** (valor de teste) **antes** de voltar a subir o `main.py`.
2. Submeter um **novo** envio (novo batch).
3. **`GET http://127.0.0.1:8088/status`** (com chave de API se `require_api_key` estiver ligado) -- JSON com **`maturity_assessment_integrity`** e contagens verificadas.
4. **`python main.py --export-audit-trail -`** -- o mesmo bloco de integridade no audit trail.

Remover o segredo da sessao apos o teste de lab, se aplicavel.

---

## F. Depois deste checkpoint

- **#86** (sessao / passwordless no dashboard, depois RBAC): seguir [PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md](../plans/PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md) num **branch dedicado**.
- **DOCX para YAML** (conteudo privado do questionario): manter curadoria em **`docs/private/`** e formato em `core/maturity_assessment/pack.py` -- ver PLAN_MATURITY e empacotamento por **tenant** quando houver cliente real.
