# Playbook de upgrade do runtime Python (3.12 → 3.13 → 3.14, Docker, CI)

**Localização:** Documento **meta / operação planejada** (trilha de upgrade e matriz). Fica em **`docs/plans/`**, junto de readiness e sequenciamento—não só HOWTOs cotidianos em **`docs/`**.

**English:** [PYTHON_UPGRADE_PLAYBOOK.md](PYTHON_UPGRADE_PLAYBOOK.md)

**Objetivo:** Permanecer **seguro no 3.12** enquanto **prepara** linhas mais novas do CPython sem quebrar **wheels**, drivers SQL, ORM, caminhos **Docker** multi-stage ou **CI**.

---

## 1. Contrato atual (o que precisa continuar verdadeiro)

| Camada           | Fonte da verdade                                                  | Hoje                                                                       |
| ------           | ------------------                                                | ----                                                                       |
| Faixa declarada  | `pyproject.toml` → `requires-python`                              | `>=3.12`                                                                   |
| Árvore fixada    | `uv.lock` + `uv sync`                                             | Resolvida para 3.12/3.13 (matriz de testes no CI em `main`)                |
| Imagem publicada | `Dockerfile` **`FROM`** + **`COPY .../python3.XY/site-packages`** | Precisa bater com **um** minor Python de ponta a ponta                     |
| Sinal do CI      | `.github/workflows/ci.yml`                                        | Job **Test** deve cobrir todo **minor suportado** em SECURITY/CONTRIBUTING |

**Armadilha:** Declarar **3.13** sem CI no 3.13 esconde regressões até o Docker ou o local falhar.

---

## 2. Por que 3.13 antes de 3.14?

|                           | 3.13                                                           | 3.14                                                                                     |
| ---                       | ---                                                            | ---                                                                                      |
| **Ecossistema de wheels** | Wheels **cp313** maduros para boa parte do stack científico/BD | Wheels **cp314** ainda atrás; mais risco de **build a partir do fonte**                  |
| **Atrito**                | Menor: `python:3.13-slim` oficial, mesmo padrão do 3.12        | Maior: acompanhar PyPI para `cp314` em numpy/scipy/pandas/sklearn/psycopg2/oracledb/etc. |
| **Segurança / CVE**       | Interpretador mais novo + base Debian nas imagens slim         | Mesma lógica, condicionada aos wheels das dependências                                   |

**Recomendação:** Tratar **3.13** como **próximo alvo** de produção em Docker + verificação do lockfile; **3.14** como **experimental** até `docker build` instalar **só wheels** (ou tempo de compilação aceitável) para o `requirements.txt` / `uv.lock` completos.

---

## 3. Matriz de compatibilidade a manter

| Verificação                                 | 3.12              | 3.13                                           | 3.14 (prep)            |
| -----------                                 | ----              | ----                                           | -----------            |
| `uv sync` + `uv run pytest -v -W error`     | CI                | CI (matriz)                                    | Manual ou job opcional |
| `uv run ruff`                               | CI                | Um job (ex.: 3.12)                             | N/A                    |
| `pip-audit`                                 | CI                | Igual                                          | N/A                    |
| **Docker** `docker build`                   | Publicação padrão | Branch: alterar `FROM` + caminhos `python3.XY` | Só branch              |
| **Smoke:** container, `/health`, scan vazio | Homelab           | Mesma família de tags                          | Idem                   |

**Dockerfile:** ao mudar o minor, substituir **todos** os `python3.12` em `find`/`COPY` por `python3.13` (ou `3.14`).

---

## 4. Preparar 3.14 (cedo ou tarde)

1. **CI:** Manter **3.12 + 3.13** verdes; job opcional **`workflow_dispatch`** ou **semanal** em **3.14** com `uv sync` + `pytest` (**continue-on-error** até ficar verde).
1. **Lockfile:** `uv lock` em ambiente **3.14** só quando a árvore for resolvível; PR dedicado.
1. **Auditoria de wheels:** antes de subir o `FROM`, notar compilações longas no `pip install`.
1. **`requires-python`:** subir para `>=3.13` ou `>=3.14` **só** ao **abandonar** o 3.12 — decisão de release/comunicação.

---

## 5. Docker A/B local (tempo de build + smoke)

Objetivo: comparar **`data_boar:py312`** vs **`data_boar:py313`** sem mudar `latest` até validar.

```powershell
docker build -t data_boar:ab-py312 -f Dockerfile .
# Com Dockerfile em 3.13:
docker build --no-cache -t data_boar:ab-py313 -f Dockerfile .
```

Smoke: mesmo `config.yaml`, volume, porta 8088, `/health`, scan opcional com `targets: []`.

Se o candidato falhar: manter imagem publicada em **3.12**; branch para nova tentativa.

---

## 6. O que costuma passar despercebido

- **Upgrade de Python ≠ CVE resolvido:** Muitos achados vêm de **pacotes Debian** ou **PyPI** — atualizar **tag slim**, política de `apt` e **Dependabot** na mesma.
- **`pylock.toml`:** export pode mostrar `requires-python` do **ambiente**; **fonte:** `uv.lock` + `pyproject.toml`.
- **Mirror (JFrog / privado):** garantir artefatos **cp313** / **cp314** para versões fixadas.

---

## 7. Documentos relacionados

- [TESTING.pt_BR.md](../TESTING.pt_BR.md) · [DOCKER_SETUP.pt_BR.md](../DOCKER_SETUP.pt_BR.md) · [HOMELAB_VALIDATION.pt_BR.md](../ops/HOMELAB_VALIDATION.pt_BR.md)
- [SECURITY.pt_BR.md](../SECURITY.pt_BR.md)
- [TECH_GUIDE.pt_BR.md](../TECH_GUIDE.pt_BR.md)
- [PLAN_READINESS_AND_OPERATIONS.md](PLAN_READINESS_AND_OPERATIONS.md) · [PLANS_TODO.md](PLANS_TODO.md)

---

## Última atualização: playbook em `docs/plans/`; matriz CI 3.12+3.13 nos testes.
