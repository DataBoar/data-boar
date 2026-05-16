# Contribuindo para o Data Boar

**English:** [CONTRIBUTING.md](CONTRIBUTING.md)

Obrigado por considerar contribuir. Este documento cobre a configuração local, o fluxo de trabalho e as boas práticas para que você possa executar o app, os testes e abrir alterações com segurança.

**Equipe (mantenedor + colaborador, Cursor + Git):** fluxo com **comandos**, **prompts** sugeridos e alinhamento com **rules** — **[docs/COLLABORATION_TEAM.pt_BR.md](docs/COLLABORATION_TEAM.pt_BR.md)** ([EN stub](docs/COLLABORATION_TEAM.md)). Regra aplicada: **`.cursor/rules/collaboration-maintainer-contributor.mdc`**.

## Repositório e identidade de instalação (Data Boar)

- **Produto e marca:** **Data Boar** — use esse nome em texto, issues e títulos de PR.
- **Repositório upstream:** **[github.com/FabioLeitao/data-boar](https://github.com/FabioLeitao/data-boar)** — faça fork ou clone a partir daí (troque pelo seu fork se aplicável).
- **Nome da distribuição PyPI:** o `pyproject.toml` declara **`name = "data-boar"`**. Quando houver publicação no índice de pacotes Python, a instalação será:

  ```bash
  pip install data-boar
  ```

  Até lá, use **clone git** + **`uv sync`** ou **`pip install -e .`**. O repositório ainda contém o pacote Python histórico **`lgpd_crawler`** (imports) — é detalhe de implementação, não o nome do produto. Contexto da renomeação: **[ADR 0014](docs/adr/ADR-0014-rename-repo-and-package-python3-lgpd-crawler-to-data-boar.md)**.

### Publicação no PyPI (maintainers)

O build usa **hatchling** via **`pyproject.toml`**. Na raiz do repositório (Windows):

```powershell
.\scripts\pypi-publish.ps1 -DryRun
$env:UV_PUBLISH_TOKEN = "<token de API PyPI>"
.\scripts\pypi-publish.ps1
```

Ou **`uv build`** e **`uv publish dist/*`** com **`UV_PUBLISH_TOKEN`** definido. Instalações via PyPI expõem **dois** entry points de console de **mesmo nível** (mesmo pacote, mesma régua de qualidade — regressão em qualquer um bloqueia o *gate* de merge):

- **`data-boar`** → **`main:main`** (CLI, varredura *one-shot*, servidor API com `--web`).
- **`data-boar-report`** → **`cli.reporter:main`** (Markdown executivo a partir da sessão no SQLite local — sem conector SQL ao vivo; ver [docs/USAGE.pt_BR.md](docs/USAGE.pt_BR.md) *Resumo executivo*, [EN](docs/USAGE.md) seção 5).

## Início rápido (desenvolvimento)

1. **Clone e entre no repositório**

   ```bash
   git clone https://github.com/FabioLeitao/data-boar.git
   cd data-boar
   ```

1. **Use Python 3.12+**

   O projeto usa Python 3.12 e 3.13. Veja [SECURITY.md](SECURITY.md) ([pt-BR](SECURITY.pt_BR.md)) para as versões suportadas.

1. **Instale as dependências com uv (recomendado)**

   ```bash
   uv sync
   ```

   Ou com pip em um virtualenv: `pip install -e .`

   **PowerShell (`pwsh`) — ativação manual do venv:** quando existir `.\.venv\Scripts\Activate.ps1`, execute-o na raiz. **Não** invoque o shim `activate` **sem extensão** dentro de `.venv\Scripts\` pelo caminho completo — o PowerShell só trata **`Activate.ps1`** como script (rodar `…\Scripts\activate` sem `.ps1` dá *não reconhecido*). Se o `.ps1` faltar após **`uv sync`**, use **`uv run …`** ou recrie o ambiente (apague `.venv` e rode **`uv sync`** de novo). No dia a dia prefira **`uv run …`**.

1. **Instale os hooks do pre-commit (recomendado, uma vez por clone)**

   ```bash
   uv run pre-commit install
   ```

   Os mesmos checks do job **Lint (pre-commit)** da CI rodam em todo **`git commit`** (Ruff, frescor do **plans-stats** e do **plans-hub**, markdown, locale pt-BR, guarda commercial). Antes do PR: **`uv run pre-commit run --all-files`** se você tiver usado **`--no-verify`**.

1. **Gate local completo (recomendado antes do PR)** — um comando:

   - **Windows:** `.\scripts\check-all.ps1` na raiz do repositório.
   - **Linux / macOS:** `./scripts/check-all.sh` (torne executável: `chmod +x scripts/check-all.sh`). Instale [PowerShell (`pwsh`)](https://learn.microsoft.com/powershell/scripting/install/installing-powershell) se quiser o mesmo passo de PII **gatekeeper-audit** que no Windows; senão o script segue com aviso explícito.
   - **Atalhos em par:** `./scripts/lint-only.sh`, `./scripts/quick-test.sh`, `./scripts/pre-commit-and-tests.sh` espelham os **`.ps1`** — ver **[docs/ops/SCRIPTS_CROSS_PLATFORM_PAIRING.pt_BR.md](docs/ops/SCRIPTS_CROSS_PLATFORM_PAIRING.pt_BR.md)** ([EN](docs/ops/SCRIPTS_CROSS_PLATFORM_PAIRING.md)).

1. **Execute os testes** (ou use o gate completo acima)

   ```bash
   uv run pytest -v -W error
   ```

   Todos os testes devem passar sem erros ou avisos. Veja [docs/TESTING.md](docs/TESTING.md) ([pt-BR](docs/TESTING.pt_BR.md)) para o que cada módulo de teste cobre e como executar subconjuntos.

1. **Execute a aplicação**

   ```bash
   uv run python main.py --config config.yaml
   uv run python main.py --config config.yaml --web --port 8088
   ```

## Fluxo de trabalho

- **Bugs e funcionalidades:** Abra uma issue usando os modelos [Bug report](.github/ISSUE_TEMPLATE/bug_report.md) ou [Feature request](.github/ISSUE_TEMPLATE/feature_request.md).
- **Segurança:** Não publique detalhes de exploração em público. Use o modelo [Security issue](.github/ISSUE_TEMPLATE/security.md) (apenas em alto nível) ou o processo em [SECURITY.md](SECURITY.md) ([pt-BR](SECURITY.pt_BR.md)).
- **Orientação aos planos:** [docs/plans/PLANS_HUB.md](docs/plans/PLANS_HUB.md) lista cada `PLAN_*.md` (abertos + concluídos) com resumos curtos—use para ver escopo e intenção antes de mergulhar no [docs/plans/PLANS_TODO.md](docs/plans/PLANS_TODO.md). Se você adicionar ou arquivar um plano, rode `python scripts/plans_hub_sync.py --write` e faça commit do hub atualizado (o pre-commit exige `--check`).
- **Pull requests:** Use o [modelo de PR](.github/PULL_REQUEST_TEMPLATE.md). Antes do push, prefira **`.\scripts\check-all.ps1`** (gate completo: dashboard dos planos, pre-commit, pytest com avisos como erros)—veja [docs/ops/README.pt_BR.md](docs/ops/README.pt_BR.md) § *Antes de abrir um PR*. No mínimo: testes (`uv run pytest -v -W error`; [docs/TESTING.pt_BR.md](docs/TESTING.pt_BR.md)), lint (pre-commit / Ruff) e docs/README quando o comportamento mudar. **Modelo de layout privado (versionado):** copie de **`docs/private.example/`** para **`docs/private/`** (ignorado pelo git), conforme [docs/PRIVATE_OPERATOR_NOTES.pt_BR.md](docs/PRIVATE_OPERATOR_NOTES.pt_BR.md).

### Palavras-chave de sessão no Cursor vs CLI da aplicação

Quem usa **Cursor** pode digitar **tokens em inglês** no chat (`deps`, `feature`, `docs`, …) para definir o **escopo** do assistente. Esses tokens **não** são flags do **`main.py`**. A CLI do Data Boar está em **[docs/USAGE.pt_BR.md](docs/USAGE.pt_BR.md)** ([EN](docs/USAGE.md)). Tabela **canônica**: **`.cursor/rules/session-mode-keywords.mdc`**; resumo: **[AGENTS.md](AGENTS.md)**.

### Playbooks Ansible (Debian/Ubuntu)

Cada play que instala pacotes em Debian/Ubuntu deve definir `environment: "{{ labop_debian_unattended_apt_environment }}"` (ou combinar com extras do play) para o **`apt-listbugs`** não abortar instalações `apt` não interativas. Os defaults compartilhados estão em **`group_vars/all.yml`** em cada árvore Ansible (`ops/automation/ansible/`, `deploy/ansible/`). A CI valida com **`tests/test_ansible_playbooks_unattended_apt.py`**. Contexto: **[ops/automation/ansible/README.md](ops/automation/ansible/README.md)** (Troubleshooting).

### Higiene do repositório público (LAN, credenciais)

- **`config.yaml` na raiz:** Está no `.gitignore`—costuma ter **caminhos**, hosts de BD e senhas. **Não** use `git add -f config.yaml`. Copie de `deploy/config.example.yaml` e mantenha segredos só localmente. Se o arquivo já foi commitado por engano, use `git rm --cached config.yaml` para parar de rastreá-lo; o **histórico do Git** ainda pode ter blobs antigos—use `git filter-repo` / BFG e **troque** credenciais expostas se o repositório foi público.
- **Homelab / notas do operador:** Evite **hostnames reais**, **IPs RFC1918**, **usuários Linux** ou caminhos de **`$HOME`** em Markdown versionado; use placeholders e guarde detalhes em **`docs/private/homelab/`** (gitignored) ou wiki externa. **Não** coloque links Markdown em docs públicos para caminhos dentro de `docs/private/`. Política: [docs/PRIVATE_OPERATOR_NOTES.pt_BR.md](docs/PRIVATE_OPERATOR_NOTES.pt_BR.md). Playbook genérico: [docs/ops/HOMELAB_VALIDATION.pt_BR.md](docs/ops/HOMELAB_VALIDATION.pt_BR.md) / §9 EN.
- **Gestor de senhas (ex. Bitwarden):** Guardar senhas de BD, chaves de API e tokens do lab no **Bitwarden** (plano grátis costuma bastar para uso solo) é um bom **cofre do operador**; em runtime prefira **`pass_from_env`** / `*_from_env`. Veja [docs/ops/OPERATOR_SECRETS_BITWARDEN.pt_BR.md](docs/ops/OPERATOR_SECRETS_BITWARDEN.pt_BR.md).

### Repositório público: identificadores de terceiros e histórico Git (alinhamento LGPD/GDPR)

- **Talent pool / ATS / LinkedIn:** Nomes reais, slugs e URLs de perfil ficam em caminhos **gitignored** em `docs/private/commercial/` (por exemplo `talent_pool.json`). O `scripts/talent.ps1` rastreado deve manter só o placeholder `example` e mesclar o JSON privado em runtime — **não** recolocar mapas inline de candidatos nem apelidos reais em scripts, skills ou exemplos públicos.
- **Mensagens de commit e corpos de PR:** São **permanentes** no branch padrão e em notificações. Não as use para narrativas sobre **terceiros**, **operações do pool de talento**, **contexto jurídico/denúncia** ou outros assuntos sensíveis. Prefira assuntos e textos técnicos neutros (Conventional Commits); contexto sensível fica em `docs/private/` ou canais privados acordados com o mantenedor.
- **Guardrails:** A CI roda `tests/test_pii_guard.py`, `tests/test_talent_ps1_tracked_no_inline_pool.py` e `tests/test_talent_public_script_placeholders.py` nos arquivos **rastreados**. Elas **não** reescrevem histórico antigo. Para auditar ou remediar **commits antigos**, veja [docs/ops/PII_PUBLIC_TREE_OPERATOR_GUIDE.pt_BR.md](docs/ops/PII_PUBLIC_TREE_OPERATOR_GUIDE.pt_BR.md) ([EN](docs/ops/PII_PUBLIC_TREE_OPERATOR_GUIDE.md)) — Partes I–III; nomes de arquivo antigos em `docs/ops/` redirecionam para este guia.

### Estado do PR e conselhos ao assistente (sincronizar antes de citar número)

Assistentes de IA e humanos **não** devem assumir que um PR ainda está aberto ou que o `main` local bate com o GitHub **sem verificar** — o contexto do chat pode citar um PR **já mergeado** (ex.: #80) enquanto o seguinte (#81) também já foi mergeado.

- **Mínimo:** `git fetch origin` e, no `main`, `git pull origin main` (ou pelo menos `git status -sb`) antes de aconselhar “faça merge do PR #N” ou “o que vem depois” do merge.
- **GitHub CLI:** `gh pr view <n> --json state,mergedAt,url` ou `gh pr list --head <sua-branch>`.
- **Automação:** `.\scripts\commit-or-pr.ps1` inclui fetch/rebase nos fluxos de PR; prefira-o ao git manual quando couber.
- **Depois de `gh pr create`:** Execute `gh pr view --json number,state,url` (ou `gh pr list --head <branch>`) **antes** de compartilhar o URL para o número bater com o PR **novo**, não o anterior.

O Cursor registra isso em **`.cursor/rules/git-pr-sync-before-advice.mdc`**. Veja também **[AGENTS.md](AGENTS.md)**. Pode haver um pequeno atraso do GitHub após o merge; consulte o `gh` de novo se houver dúvida.

### Reduzir conflitos de merge

- **Faça merge ou rebase de `main` na sua branch antes de abrir um PR.** Execute `git fetch origin main` e depois `git merge origin/main` (ou `git rebase origin/main`) e resolva conflitos localmente. Assim o PR permanece integrável e os revisores veem um diff limpo.
- **`report/generator.py`:** A lógica de escrita das planilhas está em `_write_excel_sheets` e helpers (`_build_report_info`, `_build_executive_summary_rows`, etc.). Ao adicionar ou alterar planilhas Excel, atualize esses helpers em vez de colocar a lógica dentro de `generate_report`. Isso mantém a mesma estrutura do `main` e evita os conflitos de merge que tivemos quando o main tinha código inline e a branch tinha o refactor.

## Código e documentação

- **Estilo:** O repositório usa [EditorConfig](.editorconfig) (indentação, charset, fins de linha). O job **Lint** da CI executa **`uv run pre-commit run --all-files`** (Ruff + format + plans-stats + plans-hub + markdown + pt-BR + guarda commercial). Localmente: **`uv run pre-commit install`** e faça commits normais, ou rode **`uv run pre-commit run --all-files`** antes do PR. Se **ruff-format** falhar: **`uv run ruff format .`** e volte a fazer stage. Veja **`.pre-commit-config.yaml`**.
- **Documentação:** Mantenha [README.md](README.md) e [docs/USAGE.md](docs/USAGE.md) em sincronia com o comportamento; atualize [README.pt_BR.md](README.pt_BR.md) e [docs/USAGE.pt_BR.md](docs/USAGE.pt_BR.md) para o português. Toda **nova** documentação voltada ao usuário deve existir em **inglês (canônico)** e **português brasileiro**; **arquivos de plano** e **ADRs numerados** em [docs/adr/](docs/adr/) podem ser apenas em inglês (veja [docs/adr/README.pt_BR.md](docs/adr/README.pt_BR.md)). Ao alterar docs para refletir atualizações da aplicação, **sincronize o outro idioma** (EN primeiro, depois pt-BR). Use seletor de idioma no topo de cada doc e links cruzados que ofereçam os dois idiomas (veja [docs/README.pt_BR.md](docs/README.pt_BR.md) — Política de documentação). **Após editar qualquer .md:** execute `uv run python scripts/fix_markdown_sonar.py` e `uv run pytest tests/test_markdown_lint.py -v -W error` para que as regras SonarQube/markdownlint (ex.: MD060 estilo de tabela) passem. O script de correção aplica MD029 (estilo de lista ordenada 1/1/1); se o doc usar **numeração semântica de passos** (1. 2. 3.), restaure à mão após rodar o script — fundamento: [ADR 0001](docs/adr/ADR-0001-markdown-fix-script-md029-and-semantic-step-lists.md) (EN).
- **Segredos:** Nunca faça commit de credenciais ou PII real. Use `.env` ou `config.local.yaml` (ambos estão no `.gitignore`) e redija em issues/PRs.

## CI e higiene de dependências

- **CI:** O GitHub Actions executa testes e **auditoria de dependências** (`uv run pip-audit`) em todo push/PR para `main` (ou `master`). Os PRs devem resolver qualquer falha de auditoria (corrigir ou atualizar dependências vulneráveis) antes do merge. Quando o SonarQube/SonarCloud estiver habilitado (veja [docs/TESTING.md](docs/TESTING.md) ([pt-BR](docs/TESTING.pt_BR.md))), trate os problemas reportados para que o quality gate permaneça verde.
- **Dependências:** A fonte de verdade das bibliotecas é o **`pyproject.toml`** (toolchain uv). O arquivo **`uv.lock`** fixa a árvore exata de dependências resolvidas para que as instalações sejam reproduzíveis e os usuários fiquem protegidos de quebras acidentais quando uma dependência atualiza (“funcionou ontem”). Declare todas as dependências em **`pyproject.toml`** (prefira **versões mínimas `>=`**; use pin `==` só quando necessário). Ao adicionar ou alterar deps, execute `uv lock`, depois `uv export --no-emit-package pyproject.toml -o requirements.txt`, e faça commit de **pyproject.toml**, **uv.lock** e **requirements.txt**. Não edite `uv.lock` nem `requirements.txt` à mão para mudanças de versão. O CI executa `uv sync` (que usa o `uv.lock`) e em seguida `pip-audit`, ou seja, o ambiente bloqueado é o que é testado e auditado. O teste **`tests/test_dependency_artifacts_sync.py`** falha se o **`uv.lock`** estiver defasado em relação ao **`pyproject.toml`** (`uv lock --check`) ou se o **`requirements.txt`** não for exatamente a saída do **`uv export`** desse lock — isso pega alterações acidentais em um único arquivo (por exemplo PRs do Dependabot que só mexem em **`requirements.txt`**).
- **Dependabot / automação:** O Dependabot abre PRs semanais para pip e GitHub Actions. Ao aplicar uma atualização de dependência (ex.: de um PR do Dependabot), atualize primeiro o **`pyproject.toml`** (suba a versão mínima), execute `uv lock` e `uv export --no-emit-package pyproject.toml -o requirements.txt`, e faça commit dos três arquivos. Faça merge dos PRs de dependência somente após o CI (testes e auditoria) passar. O Dependabot ajuda a sinalizar quando atualizar; agir nesses PRs (ou antes de uma release estável) mantém o lockfile atualizado, compatível e seguro. Para PRs **de segurança** do Dependabot, usamos o SLA opcional em [SECURITY.md](SECURITY.md) ([pt-BR](SECURITY.pt_BR.md)) (Resposta de segurança).

### Editar workflows do GitHub Actions (cadeia de suprimentos)

Se alterar **`.github/workflows/*.yml`** (jobs novos, `uses:` de terceiros ou `setup-uv`):

1. Siga o **[ADR 0005](docs/adr/ADR-0005-ci-github-actions-supply-chain-pins.md)** — fixe actions de terceiros em **SHA de commit completo (40 caracteres)** (mantenha a tag legível em **comentário** YAML na mesma linha); fixe o CLI **uv** com **`version:`** semver explícito em **`ci.yml`** — **não** `"latest"`.
1. Rode **`uv run pytest tests/test_github_workflows.py -v`** (módulo completo: pins SHA, padrão de passo de webhook Slack, forma de Semgrep/Gitleaks/SBOM, lint do **`ci.yml`** = **`pre-commit run --all-files`**, política do arquivo Slack arquivado) antes do push.

## Histórico de releases e changelog

O histórico de releases é o **histórico de commits/PRs no git** mais as **notas de release versionadas em `docs/releases/`** (ex.: um arquivo por versão). Um arquivo CHANGELOG separado no repositório **não é obrigatório**; use `docs/releases/` e as tags para “onde estamos” e o progresso.

## Checklist de release (segurança)

Antes de marcar uma **release estável**, os mantenedores devem:

- **Lockfile e auditoria:** Execute `uv lock` para atualizar o lockfile a partir do `pyproject.toml` atual, depois `uv sync` e `uv run pip-audit`. Corrija ou atualize quaisquer achados altos/críticos; em seguida execute `uv export --no-emit-package pyproject.toml -o requirements.txt` e faça commit de **uv.lock** e **requirements.txt** para que a release seja reproduzível, compatível e segura. Isso protege o usuário de quebras acidentais e mantém a release em dependências auditadas.
- **Documentação:** Garanta que [SECURITY.md](SECURITY.md) ([pt-BR](SECURITY.pt_BR.md)) e [docs/SECURITY.md](docs/SECURITY.md) ([pt-BR](docs/security.pt_BR.md)) reflitam o comportamento atual (validação, headers, API key, política de logs).
- **Segredos e logs:** Confirme que não há API keys ou senhas em logs; permissões do arquivo de config e do ambiente restringem acesso a usuários confiáveis (veja [SECURITY.md](SECURITY.md) ([pt-BR](SECURITY.pt_BR.md))). Garanta que **permissões do arquivo de config** restrinjam leitura/escrita a usuários confiáveis e que **config.yaml** (e qualquer arquivo com segredos) **não seja commitado** (veja .gitignore). Ao adicionar ou alterar logs, não registre config bruto, corpo de requisição ou credenciais; persista ou imprima texto de falha/exceção com `core.validation.sanitize_log_text` ou `core.validation.clean_error` (não `str(e)` bruto), para que corpos SQL/HTTP não vazem para SQLite ou logs (regressão: `tests/test_security.py`, `tests/test_database.py`).

## Implantação e produção

- Use um arquivo de configuração dedicado (ex.: via `CONFIG_PATH`) e nunca faça commit dele. Execute `uv run pip-audit` antes de implantar.
- Para uso público ou multi-tenant, coloque a API atrás de um proxy reverso (HTTPS, rate limiting, autenticação) conforme descrito no README.

## Ver também

- **[docs/TESTING.md](docs/TESTING.md)** ([pt-BR](docs/TESTING.pt_BR.md)) — Módulos de teste, CI, SonarQube.
- **[docs/TOPOLOGY.md](docs/TOPOLOGY.md)** ([pt-BR](docs/TOPOLOGY.pt_BR.md)) — Topologia da aplicação (módulos, classes, fluxo de dados).
- **[docs/ops/COMMIT_AND_PR.md](docs/ops/COMMIT_AND_PR.md)** ([pt-BR](docs/ops/COMMIT_AND_PR.pt_BR.md)) — Automação de commit e PR.
- **[docs/COMPLIANCE_FRAMEWORKS.md](docs/COMPLIANCE_FRAMEWORKS.md)** ([pt-BR](docs/COMPLIANCE_FRAMEWORKS.pt_BR.md)) — Rótulos de conformidade e extensibilidade.
- **[docs/COPYRIGHT_AND_TRADEMARK.pt_BR.md](docs/COPYRIGHT_AND_TRADEMARK.pt_BR.md)** ([EN](docs/COPYRIGHT_AND_TRADEMARK.md)) — Direitos autorais e marca (tornar oficial, registros). [NOTICE](NOTICE) para o aviso do projeto.
- Índice completo da documentação: [docs/README.pt_BR.md](docs/README.pt_BR.md) ([EN](docs/README.md)).

Se tiver dúvidas, abra uma discussão ou uma issue. Obrigado por contribuir.
