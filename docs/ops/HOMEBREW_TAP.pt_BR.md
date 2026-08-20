# Tap Homebrew (macOS, #1425)

**English:** [HOMEBREW_TAP.md](HOMEBREW_TAP.md)

**Issue:** [#1425](https://github.com/DataBoar/data-boar/issues/1425) · **Plan:** `docs/plans/PLAN_NATIVE_PACKAGES.md`

Este é o caminho de instalação **macOS para quem consome o produto**: um **tap próprio** ([DataBoar/homebrew-databoar](https://github.com/DataBoar/homebrew-databoar)), **não** o [homebrew-core](https://github.com/Homebrew/homebrew-core). Não há fila de revisão do Homebrew-core.

A fórmula **declara dependência do `python@3.13` do Homebrew** e faz `pip install` do sdist **PyPI** num venv do prefixo. **Não** embarca CPython (diferente dos pacotes Linux nfpm / xbps Void do canal Enterprise). Este tap **não** oferece `cp314t` / no-GIL.

## Instalar

```bash
brew tap DataBoar/databoar
brew install data-boar
data-boar --version
data-boar --demo
```

O `--demo` sobe o painel em loopback com corpus sintético (o processo permanece até você encerrar).

### Extras

A fórmula é **só a base** (ideia parecida com o pacote nfpm core, sem subpacotes de conector). Depois de instalar:

```bash
"$(brew --prefix data-boar)/libexec/bin/pip" install "data-boar[sql-community]"
```

Veja os caveats da fórmula para o caminho `opt_libexec` que o Homebrew imprime.

## Validação (CI, não metal do lab)

O GitHub Actions [`.github/workflows/homebrew-tap.yml`](../../.github/workflows/homebrew-tap.yml) roda em **macos-14** (Apple Silicon):

1. `brew audit --strict --new`
2. `brew install` a partir de uma cópia local da fórmula em `packaging/homebrew/Formula/data-boar.rb`
3. `brew test` (`--version` + `--demo` até existir o SQLite do demo, depois SIGTERM)

Macs Intel usam o mesmo caminho pip, sem bottle. Este workflow **não** tem runner Intel separado.

Fórmula canônica: [`packaging/homebrew/Formula/data-boar.rb`](../../packaging/homebrew/Formula/data-boar.rb).

## Bump a cada publicação no PyPI

A fórmula **precisa** acompanhar o sdist do PyPI (incluindo uploads `postN` sem tag Git). Sem isso o tap vira dívida manual.

```bash
uv run python scripts/homebrew_formula_bump.py --write
uv run python scripts/homebrew_formula_bump.py --check --latest
```

Automação:

- `publish-pypi.yml` chama este workflow depois de um publish **pypi** (não TestPyPI)
- `workflow_dispatch` com **bump** em `homebrew-tap.yml`
- `release: published` que não seja pre-release

Sincronizar o repositório público do tap exige o secret **`HOMEBREW_TAP_TOKEN`** (contents:write em `DataBoar/homebrew-databoar`). Sem o secret, a fórmula ainda sobe PR neste repo; o clone do tap é ignorado.

Versões git-only de pré-release (`1.8.0-beta`) **não** são alvo da fórmula — quem usa Homebrew recebe o último release **PyPI**.

## Resolução de problemas

| Sintoma | O que a fórmula faz de fato | O que fazer |
| ------- | --------------------------- | ----------- |
| `brew install` não baixa hatchling / wheels | O `install` roda `python3.13 -m pip --python <venv> install --verbose .`; o pip pode baixar **isolamento de build** (hatchling) e **wheels de runtime no PyPI**. **Não** usa `std_pip_args` do Homebrew (`--no-deps --no-build-isolation --no-binary=:all:` / blocos `resource` vendorados). | Confirme rede até `pypi.org` / `files.pythonhosted.org`. Não reescreva a fórmula no modelo de `resource` do homebrew-core — o `brew audit --strict --new` deste tap espera o caminho pip. |
| Falta `python@3.13` | `depends_on "python@3.13"` | `brew install python@3.13` e tente de novo. |
| Conectores ausentes depois do install | Caveats: fórmula só da base | `"$(brew --prefix data-boar)/libexec/bin/pip" install "data-boar[sql-community]"` (ou outro extra). |
| `brew test` estoura tempo no `--demo` | O teste espera até ~3 minutos por `$TMPDIR/data_boar_demo/audit_results.db` e depois envia SIGTERM | Veja o log que o Homebrew imprime; o `--demo` precisa gravar no diretório temp do SO. |

## Fora de escopo

arm64 Linux (#1403), xbps (#1404), MSI/winget (#1467).

Veja também: [USAGE.pt_BR.md](../USAGE.pt_BR.md) · [TECH_GUIDE.pt_BR.md](../TECH_GUIDE.pt_BR.md) · [QUICKSTART.pt_BR.md](../../QUICKSTART.pt_BR.md).
