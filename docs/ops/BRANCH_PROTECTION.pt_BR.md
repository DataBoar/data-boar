# Proteção de branch em `main` (runbook do operador)

**English:** [BRANCH_PROTECTION.md](BRANCH_PROTECTION.md)

Este runbook registra **o que o GitHub realmente exige** no branch padrão. Ele **não** altera configurações do repositório. Releia a API ao vivo antes de afirmar que um check novo é obrigatório.

**Verificado:** `gh api` em **2026-08-19** contra `DataBoar/data-boar`.

Resumo para quem contribui: [CONTRIBUTING.pt_BR.md](../../CONTRIBUTING.pt_BR.md) (*Requisitos de pull request*). Tokens de calor: [WORKFLOW_DEFERRED_FOLLOWUPS.pt_BR.md](WORKFLOW_DEFERRED_FOLLOWUPS.pt_BR.md). Lista de qualidade desejada: [QUALITY_WORKFLOW_RECOMMENDATIONS.md](../QUALITY_WORKFLOW_RECOMMENDATIONS.md) §9.

## Regras clássicas vs rulesets

O GitHub aplica **as duas** camadas neste repositório:

| Camada                                                                         | O que a API mostrou (2026-08-19)                                                                                                                                                                                                                                                |
| ---                                                                            | ---                                                                                                                                                                                                                                                                             |
| **Clássica** `GET /repos/{owner}/{repo}/branches/main/protection`              | A regra existe (não é 404). **Assinaturas obrigatórias** ligadas. Force-push e exclusão do branch **desligados**. `enforce_admins` **desligado**. Resolução de conversas **desligada**. Este endpoint **não** lista os checks pytest obrigatórios — eles ficam num **ruleset**. |
| **Ruleset** `restriction baseline` (`13887245`, **active**, `~DEFAULT_BRANCH`) | `deletion`, `non_fast_forward`, `required_signatures`.                                                                                                                                                                                                                          |
| **Ruleset** `main-gate-pii` (`17861726`, **active**, `~DEFAULT_BRANCH`)        | `pull_request` (ver revisões abaixo) + **required status checks**.                                                                                                                                                                                                              |

Um **404 Branch not protected** na API clássica ainda pode ocorrer em outro repositório que use **só** rulesets. Aqui proteção clássica **e** rulesets estão presentes.

## Conferir de novo:

```bash
gh api repos/DataBoar/data-boar/branches/main/protection
gh api repos/DataBoar/data-boar/rulesets
gh api repos/DataBoar/data-boar/rulesets/17861726
gh api repos/DataBoar/data-boar/rulesets/13887245
```

## Status checks obrigatórios em `main`

Ruleset `main-gate-pii` → `required_status_checks` (nomes exatos de `context`):

| Obrigatório (bloqueia merge) | Consultivo nos PRs típicos (roda, fora dessa lista)                                          |
| ---                          | ---                                                                                          |
| **Test (Python 3.12)**       | **Lint (pre-commit)**, **Bandit (strict)**, **Dependency audit**, **Dependency review (PR)** |
| **Test (Python 3.13)**       | **Test Windows (Python 3.12)**, **Ansible syntax-check**                                     |
| **Test (Python 3.14)**       | **Semgrep**, **CodeQL**, **SonarQube / SonarCloud**, **Secret scan (Gitleaks)**              |

`strict_required_status_checks_policy` está **false** (o branch não precisa estar atualizado com `main` para os checks obrigatórios valerem).

Windows, lint, Bandit, Semgrep, CodeQL e Sonar são sinais **warm**: a CI roda e o operador trata job vermelho como pare, mas o GitHub ainda permite merge se os três jobs pytest Linux estiverem verdes.

Os nomes vêm de [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) e workflows irmãos. Se você adicionar um check obrigatório, espere ao menos uma execução **verde** com esse nome exato e então inclua no ruleset pela UI — não invente nomes neste arquivo.

## Revisões, CODEOWNERS, assinaturas

Parâmetros `pull_request` do ruleset `main-gate-pii` (2026-08-19):

- **Revisões aprovadoras obrigatórias:** `0`
- **Exigir revisão de code owner:** `false`
- **Descartar revisões antigas no push:** `false`
- **Métodos de merge permitidos:** merge, squash, rebase (o repositório também tem `delete_branch_on_merge: true`)

[`.github/CODEOWNERS`](../../.github/CODEOWNERS) ainda cobre os caminhos do gate de PII/segurança ([ADR 0071](../adr/ADR-0071-self-protecting-pii-gate.md)). O ruleset **ainda não** exige essa revisão. Ligar **Require review from Code Owners** é mudança na UI do GitHub, não edição de docs.

**Assinaturas obrigatórias** estão na proteção **clássica** **e** no ruleset `restriction baseline`. Branches só-bot (Dependabot) que não assinam commits precisam de um PR substituto assinado pelo mantenedor — veja a issue **#1419**.

## `ZIZMOR_ENFORCE`

| Fato                            | Valor (2026-08-19)                                                                                                                                                                                                             |
| ---                             | ---                                                                                                                                                                                                                            |
| Variável Actions do repositório | **`ZIZMOR_ENFORCE=true`**                                                                                                                                                                                                      |
| Workflow                        | [`.github/workflows/zizmor.yml`](../../.github/workflows/zizmor.yml)                                                                                                                                                           |
| Quando roda                     | Todo `pull_request` / `push` em `main`/`master` (**sem** filtro `paths:` — um ruleset `code_scanning` que exige zizmor precisa de resultado para aquele commit e ref); agenda semanal; `workflow_dispatch`                                                                                                                  |
| Comportamento do job            | Com a variável **diferente** de `false`, um achado do zizmor **falha o job** (`ENFORCE_ZIZMOR`). Esse job **não** está em `required_status_checks`. Rodar sempre deixa uma exigência `code_scanning` **elegível** sem deadlock de merge; recolocar o zizmor no ruleset é passo separado na UI do operador. |
| Local / `check-all`             | Consultivo salvo `DATA_BOAR_ENFORCE_ZIZMOR` / `-Enforce` — veja [WORKFLOW_DEFERRED_FOLLOWUPS.pt_BR.md](WORKFLOW_DEFERRED_FOLLOWUPS.pt_BR.md) e `scripts/workflow-security-lint.*`.                                             |

**Conferir de novo:** `gh api repos/DataBoar/data-boar/actions/variables/ZIZMOR_ENFORCE`

Não desligue a variável para silenciar um achado. Corrija o YAML do workflow (ou use exceção documentada e aprovada pelo operador). Mesma postura dos outros gates de segurança.

## Modelo de calor (cold → warm → hot)

Os mesmos tokens de [WORKFLOW_DEFERRED_FOLLOWUPS.pt_BR.md](WORKFLOW_DEFERRED_FOLLOWUPS.pt_BR.md):

| Token         | Significado aqui                                                                             |
| ---           | ---                                                                                          |
| **cold**      | Só documentado; sem gate no GitHub.                                                          |
| **warm**      | Job de CI ou hábito existe; **não** é check obrigatório (ou só uma fatia é obrigatória).     |
| **hot**       | O nome está na lista `required_status_checks` do ruleset (ou bloqueio de merge equivalente). |
| **maxed_out** | Regras / atestações no nível da org, além deste repositório.                                 |

**Neste repositório (2026-08-19):** a linha **Branch protection** dos follow-ups permanece **warm**. A matriz pytest Linux já é **hot**. Suba a linha dos follow-ups para **hot** só quando o conjunto recomendado no QUALITY §9 (Lint, audit, Bandit, Semgrep e qualquer CodeQL/Sonar que você queira bloquear) estiver **obrigatório** em `main`.

## Relacionado

- [COMMIT_AND_PR.pt_BR.md](COMMIT_AND_PR.pt_BR.md) ([EN](COMMIT_AND_PR.md)) — scripts locais de commit/PR
- [GITHUB_ISSUE_CANONICAL_AND_DUPLICATE_CLOSE.pt_BR.md](GITHUB_ISSUE_CANONICAL_AND_DUPLICATE_CLOSE.pt_BR.md) — merge só com `gh pr checks` verde
- [ADR 0005](../adr/ADR-0005-ci-github-actions-supply-chain-pins.md) — pins SHA das Actions
- [ADR 0071](../adr/ADR-0071-self-protecting-pii-gate.md) — CODEOWNERS + arquivos do gate
