# Colaboração em equipe (Cursor + Git) — guia para mantenedor e contribuidor

**English:** [COLLABORATION_TEAM.md](COLLABORATION_TEAM.md)

Este guia resume **como trabalhar em conjunto** (papéis **mantenedor** e **contribuidor**) com **coesão**: fluxo Git, identidade nos commits, limites do assistente no Cursor e **o que configurar** no repositório (rules, `AGENTS.md`, hábitos).

**Relacionado:** [CONTRIBUTING.pt_BR.md](../CONTRIBUTING.pt_BR.md), [docs/ops/COMMIT_AND_PR.pt_BR.md](ops/COMMIT_AND_PR.pt_BR.md), [AGENTS.md](../AGENTS.md), [README.pt_BR.md](README.pt_BR.md) (**Interno e referência** → **TOKEN_AWARE_USAGE** em `docs/plans/`), [TALENT_POOL_LEARNING_PATHS.pt_BR.md](TALENT_POOL_LEARNING_PATHS.pt_BR.md) (certificações/cursos opcionais por **arquétipo** — sem dados pessoais), [docs/ops/TALENT_DOSSIER_AND_POOL_SYNC.pt_BR.md](ops/TALENT_DOSSIER_AND_POOL_SYNC.pt_BR.md), [docs/ops/LINKEDIN_ATS_PLAYBOOK.pt_BR.md](ops/LINKEDIN_ATS_PLAYBOOK.pt_BR.md). Regra Cursor: **`.cursor/rules/collaboration-maintainer-contributor.mdc`**.

---

## 1. Fork vs um só repositório — o que faz sentido

| Abordagem                                                                  | Vantagens                                                                                       | Desvantagens                                                                         |
| ---------                                                                  | ---------                                                                                       | -------------                                                                        |
| **Fork** (contribuidor com cópia sob o próprio usuário no GitHub)          | Fluxo “open source” claro; bom enquanto o colaborador **aprende**; PRs do fork → repo canônico. | Exige **sincronizar** com o upstream com frequência (`fetch` + merge/rebase).        |
| **Colaborador no repo canônico** (convite GitHub com permissão de escrita) | Um `origin`, menos atrito; branches `feature/…` e PRs **no mesmo repo**.                        | Exige confiança e disciplina de branch (não commitar direto em `main` sem combinar). |

**Sugestão prática:** começar com **fork + PR**; quando o ritmo ficar alto, **adicionar o colaborador no repositório canônico** e manter a mesma regra: **branch por tarefa** + **PR** + revisão.

**Repo canônico:** use a URL que vocês adotarem (ex.: organização ou usuário do mantenedor). Nos exemplos abaixo, `UPSTREAM_URL` é um placeholder — substituam pela URL real do remoto **oficial**.

---

## 2. Git e GitHub sabem quem commitou; o Cursor não adivinha sozinho

- **`user.name` / `user.email`** em cada máquina definem o **autor do commit**. No GitHub, isso aparece no histórico e nos PRs.
- O **assistente no Cursor** não recebe um sinal confiável do tipo “quem está no teclado”. Ele vê o **workspace**, arquivos e o que escrevem no chat.
- **Conclusão:** coesão vem de **processo** (branches, PRs, issues) + **documentação** (`AGENTS.md`, este guia, opcionalmente labels no GitHub), não de “memória mágica” do modelo.

---

## 3. Separar “tarefas do mantenedor” vs “tarefas do colaborador”

| Mecânismo                        | Uso                                                                                                                                                                                                                                                                                                                                    |
| ---------                        | ---                                                                                                                                                                                                                                                                                                                                    |
| **Issues / Projects no GitHub**  | Assignee **mantenedor** vs **contribuidor**; labels `owner:maintainer`, `owner:contributor` (ou equivalentes que a equipe adotar).                                                                                                                                                                                                      |
| **Nomes de branch**              | Ex.: `contributor/descricao-curta`, `maintainer/descricao-curta` ou só `feature/…` com assignee na PR.                                                                                                                                                                                                                                 |
| **`docs/private/`** (gitignored) | Notas **só do mantenedor** / LAB-OP **reais** — **não** entram no clone público do colaborador da mesma forma; evita misturar “chores” pessoais com o que o contribuidor precisa ler.                                                                                                                                                    |
| **Planos (`docs/plans/`)**       | Podem continuar **só em inglês** por política do repo; visão geral para humanos: **[PLANS_HUB.md](plans/PLANS_HUB.md)** (tabela auto-atualizada); backlog canônico: `PLANS_TODO.md`. Quem implementa marca progresso em PR + `PLANS_TODO.md` quando fizer sentido e roda `plans_hub_sync.py --write` ao criar/arquivar um `PLAN_*.md`. |

---

## 4. Comandos Git concretos

### 4.1 Colaborador — clone do **fork** (primeira vez)

```bash
git clone https://github.com/CONTRIBUTOR_USER/nome-do-fork.git
cd nome-do-fork
git remote add upstream UPSTREAM_URL
git remote -v
```

`UPSTREAM_URL` = URL HTTPS ou SSH do repositório **canônico** (upstream).

### 4.2 Colaborador — identidade Git (obrigatório em cada máquina)

```bash
git config user.name "Nome que aparece no GitHub"
git config user.email "email@que-consta-no-GitHub"
```

Confirmação:

```bash
git config --get user.name
git config --get user.email
```

### 4.3 Colaborador — começar trabalho novo

```bash
git fetch upstream
git checkout main
git merge upstream/main
# ou: git rebase upstream/main
git checkout -b contributor/minha-feature
```

### 4.4 Colaborador — antes de abrir PR

```bash
git fetch upstream
git merge upstream/main
# resolver conflitos se houver
uv sync
uv run pytest -v -W error
git push origin contributor/minha-feature
```

No GitHub: **Open Pull Request** do fork **→** repositório canônico (`upstream`).

### 4.5 Mantenedor — alinhar `main` local

```bash
git checkout main
git pull origin main
```

### 4.6 Mantenedor — adicionar remote do fork do contribuidor (opcional, para `fetch` da branch dele)

```bash
git remote add contributor-fork https://github.com/CONTRIBUTOR_USER/nome-do-fork.git
git fetch contributor-fork
git checkout -b review/contrib-feature contributor-fork/contributor/minha-feature
```

(Ajustar nome da branch conforme o contribuidor empurrou.)

### 4.7 Quando ambos trabalham no **mesmo** repo (colaborador convidado)

```bash
git clone UPSTREAM_URL
cd repositorio
git config user.name "..."
git config user.email "..."
git checkout main
git pull origin main
git checkout -b contributor/minha-feature
# ... commits ...
git push -u origin contributor/minha-feature
```

Política: **PR obrigatório** para `main` (branch protection no GitHub, se possível).

---

## 5. Comandos úteis de verificação (ambos)

```bash
git status
git log -3 --oneline
gh pr list --state open
```

(`gh` exige [GitHub CLI](https://cli.github.com/) autenticado.)

---

## 6. Prompts sugeridos para o Cursor (copiar e adaptar)

## No início de uma sessão (colaborador):

> Estou no papel de **contribuidor**. Branch atual: `contributor/…` ou `feature/…`. Segue [AGENTS.md](AGENTS.md) e [CONTRIBUTING.pt_BR.md](../CONTRIBUTING.pt_BR.md). Não assumas acesso a `docs/private/`. Proponha alterações em commits pequenos e compatíveis com PR único para a feature X.

## No início de uma sessão (mantenedor):

> Sou o **mantenedor**. Posso referir políticas em `docs/private/` apenas em notas locais — não sugerir colar segredos ou IPs reais em arquivos rastreados. Prioridade: alinhar com **PLANS_TODO** (entrada em [README.pt_BR.md](README.pt_BR.md) § Interno e referência) e [`.cursor/rules/execution-priority-and-pr-batching.mdc`](../.cursor/rules/execution-priority-and-pr-batching.mdc).

## Para reduzir interferência entre pessoas:

> Esta tarefa é **só para o contribuidor** (documentação de onboarding). Não mistures com itens de homelab ou estudo do mantenedor.

## Antes de merge/release:

> Rode a sugestão de verificação: `uv run pytest -v -W error` e, se aplicável, `scripts/check-all.ps1`. Confirma estado do Git com `git fetch` e `git status`.

## Token-aware (sessão curta):

> **short** — uma só fatia: [descrever]. Sem expandir para outros planos.

---

## 7. Rules, skills e guidelines no repositório

| Artefato                                                                                                                      | Função                                                                                                                                                                            |
| --------                                                                                                                      | ------                                                                                                                                                                            |
| **[`AGENTS.md`](../AGENTS.md)**                                                                                               | Contrato global do assistente: idioma, segredos, homelab, Git/PR, testes. **Ambos** devem ler uma vez; o contribuidor segue o mesmo arquivo ao clonar.                              |
| **[`.cursor/rules/`](../.cursor/rules/)**                                                                                     | Regras automáticas ou por contexto (ex.: `git-pr-sync-before-advice.mdc`, `execution-priority-and-pr-batching.mdc`). **Colaboração:** `collaboration-maintainer-contributor.mdc`. |
| **[`.cursor/skills/`](../.cursor/skills/)**                                                                                   | Playbooks longos (Docker, token-aware, etc.). Use quando a tarefa combinar.                                                                                                       |
| **[`CONTRIBUTING.md`](../CONTRIBUTING.md)** / **[`CONTRIBUTING.pt_BR.md`](../CONTRIBUTING.pt_BR.md)**                         | Fluxo de contribuição e testes.                                                                                                                                                   |
| **[`TALENT_POOL_LEARNING_PATHS.md`](TALENT_POOL_LEARNING_PATHS.md)** / **[`.pt_BR.md`](TALENT_POOL_LEARNING_PATHS.pt_BR.md)** | Mini-roteiros opcionais (repo + carreira) por **arquétipo**; dados por candidato só em `docs/private/`.                                                                           |
| **[`ops/TALENT_DOSSIER_AND_POOL_SYNC.md`](ops/TALENT_DOSSIER_AND_POOL_SYNC.md)** / **[`.pt_BR.md`](ops/TALENT_DOSSIER_AND_POOL_SYNC.pt_BR.md)** | `talent-dossier next` + snapshot do pool; PDFs em `docs/private/team_info/`.                                                                                                    |
| **[`ops/LINKEDIN_ATS_PLAYBOOK.md`](ops/LINKEDIN_ATS_PLAYBOOK.md)** / **[`.pt_BR.md`](ops/LINKEDIN_ATS_PLAYBOOK.pt_BR.md)** | Playbook público LinkedIn + ATS; redação final por pessoa em `docs/private/commercial/`.                                                                                         |
| **Este arquivo**                                                                                                              | Papéis, comandos e prompts — **maturidade de equipe** sem substituir o CONTRIBUTING.                                                                                              |

### 7.1 Ajustes opcionais quando a equipe crescer

1. **Branch protection** em `main` (ex.: exigir PR, status de CI).
1. **`CODEOWNERS`** (`.github/CODEOWNERS`) para pedir revisão automática do mantenedor em pastas críticas.
1. **Issue templates** no GitHub (“bug”, “feature”, “doc”) com checklist de testes.
1. Nova rule **`.mdc`** só se houver **regra repetida** que o CONTRIBUTING não cubra (mantê-las **curtas**).

---

## 8. O que **não** fazer

- Colocar **tokens, senhas, URLs internas com segredos** em Markdown rastreado ou em rules.
- Depender do assistente para saber **quem** está no PC sem declarar no chat ou sem Git configurado.
- Trabalhar semanas em `main` desatualizado sem `fetch upstream` / `pull`.

---

## 9. Revisão do documento

| Data       | Nota                                                                         |
| ----       | ----                                                                         |
| 2026-03-01 | Versão inicial (papéis mantenedor/contribuidor, fork ou repo único, comandos, prompts, rules). |
| 2026-03-27 | Referência a roteiros de talent pool (arquétipos).                           |
| 2026-04-08 | Exemplos genericizados (sem identificadores pessoais em narrativas públicas). |

Atualizem esta tabela quando mudarem URL canônica, política de branch ou nomes dos remotes.
