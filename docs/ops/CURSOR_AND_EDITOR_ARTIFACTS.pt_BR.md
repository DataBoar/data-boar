# Artefatos Cursor, VS Code e workspace (o que versionamos)

**Público:** mantenedores e contribuidores. **Não** é documentação de operador do produto.

Este repositório versiona **parte** da configuração de editor e automação em `.cursor/`, `.vscode/` e `.github/`. Abaixo está a **política** após auditoria em 2026-04: o que é seguro no `origin`, o que fica no gitignore e o que **nunca** deve ir para o Git público.

## Versionados de propósito

| Local | Função | Risco de segredo / PII |
| ----- | ------ | ------------------------ |
| **`.github/`** | CI (workflows, CodeQL, Semgrep, Slack), Dependabot, templates de issue/PR | **Baixo** se Actions usam **Secrets** do repo/org só por **nome** no YAML, não valores. Onde aplicável, pins com SHA de commit. |
| **`.cursor/rules/`**, **`.cursor/skills/`** | Regras e skills do Cursor (política do projeto) | **Baixo** — mesmas regras dos docs rastreados (sem IP LAN, hostnames reais ou credenciais). |
| **`.cursor/mcp.json`** | Lançamento de servidores MCP (ex.: gateway Docker). Pode ter paths **placeholder** tipo `C:\\Users\\<username>\\...` | **Médio se mal editado** — não substituir placeholders por **usuário** Windows real ou paths de máquina no arquivo commitado. Preferir override local ou cópia não rastreada. |
| **`.cursor/settings.json`** | UI do Cursor (ex.: plugin Slack) | **Baixo** — sem tokens no repo. |
| **`.cursor/worktrees.json`** | Comandos ao criar **git worktree** (`setup-worktree`). | **Baixo** — deve refletir o bootstrap real do repo (**`uv sync`**, não `npm install`, neste projeto Python/`uv`). |
| **`.vscode/settings.json`** | Defaults compartilhados VS Code/Cursor (só não segredo) | **Baixo** — ver bloco de comentário no `.gitignore` perto de `.vscode/`. |
| **`.well-known/appspecific/com.chrome.devtools.json`** | Arquivo **appspecific** do Chrome DevTools (pode estar vazio). | **Baixo** — sem segredos; placeholder opcional para ferramentas. |

## Gitignored (não commitar)

| Local | Motivo |
| ----- | ------ |
| **`.pytest_cache/`**, **`.ruff_cache/`** | Caches efêmeros — **nunca** versionar. |
| **`.cursor/private/`** | Material só do operador (ver `.gitignore` na raiz). |
| **`.mcp.json`** (raiz do repo) | Lançamento local de servidores MCP (paths absolutos, comandos da máquina). Distinto do **`.cursor/mcp.json`** rastreado (placeholders). |
| **`.cursorignore`**, **`.cursorindexingignore`** | Ignore local/editor para contexto de IA (documentação Cursor). |
| **`docs/private/`** | Notas privadas e git privado empilhado — não vão para `origin`. |

## Se algo sensível aparecer em `.cursor/` ou `.vscode/`

1. **Remover** do último commit público (revert ou `git rm --cached`) e rotacionar qualquer segredo exposto.
2. Colocar o substituto em **`docs/private/`** (git privado empilhado) ou arquivo **local** não rastreado.
3. Atualizar **este arquivo** se a política mudar.

## Relacionados

- [CURSOR_AGENT_POLICY_HUB.pt_BR.md](CURSOR_AGENT_POLICY_HUB.pt_BR.md) — índice de política.
- [PRIVATE_LOCAL_VERSIONING.pt_BR.md](PRIVATE_LOCAL_VERSIONING.pt_BR.md) — workflow de `docs/private/`.
- `AGENTS.md` na raiz — acesso de agente a `docs/private/` vs Git público.
