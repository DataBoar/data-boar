# Proteção da estação Linux principal de desenvolvimento (sem operações destrutivas no repo aqui)

**English:** [PRIMARY_LINUX_WORKSTATION_PROTECTION.md](PRIMARY_LINUX_WORKSTATION_PROTECTION.md)

**primary Linux dev workstation** (LMDE 7) é a **estação de desenvolvimento principal** do operador **enquanto o laptop Windows anterior está em reparo Lenovo** (falha de hardware **2026-06-07**; referência de chamado **E0482B2DMD**). Hospeda o clone **canônico** do `data-boar`, evidências locais e a **continuidade do histórico Git**. Papel **temporário** até o Windows principal voltar — ver [ADR 0068](../adr/ADR-0068-primary-linux-dev-workstation-temporary.md) (*Reversão quando o Windows principal voltar*).

**Caminho do clone canônico (padrão do operador):** `~/Projects/dev/data-boar` — trate como **`DATA_BOAR_ROOT`**. **Não** incorpore caminhos reais de home em commits rastreados; detalhes de máquina ficam só em **`docs/private/`**.

**Contraste:** hosts **LAB-OP** do manifesto SSH **não** são esta árvore — `git reset --hard`, `lab-op-git-align-main` e similares aplicam-se **só** nesses **`repoPaths`**, não no workspace Cursor no Linux primary dev workstation — ver **`docs/ops/LAB_COMPLETAO_RUNBOOK.md`** (*Blast radius*).

Quando o PC Windows principal voltar do reparo, retome **`docs/ops/PRIMARY_WINDOWS_WORKSTATION_PROTECTION.pt_BR.md`** e **`.cursor/rules/primary-windows-workstation-protected-no-destructive-repo-ops.mdc`** nessa máquina; o Linux primary pode continuar como nó lab-op, mas **deixa** de ser o único clone canônico salvo repriorização explícita do operador.

---

## Objetivos

- **Zero** apagamento acidental de **árvore completa**, reset **tipo clean-slate** ou **reescrita de histórico** na máquina onde o trabalho **cotidiano** vive hoje.
- Ensaios **destrutivos** (clone destrutivo, `git filter-repo`, ensaios de force-push) só noutros **hosts de lab** — ou em **diretórios isolados em `/tmp/`** — **não** por padrão no Linux primary dev workstation.

---

## Proibido no Linux primary dev workstation (clone canônico)

| Classe | Exemplos |
| ----- | -------- |
| **Clean-slate destrutivo** | Fluxos **`clean-slate.sh`** privados / modelo que fazem **`rm -rf`** em **`DATA_BOAR_ROOT`** e voltam a clonar (ver **`docs/ops/PII_PUBLIC_TREE_OPERATOR_GUIDE.pt_BR.md`** H.9). |
| **Reescrita de histórico sem guard** | **`scripts/run-pii-history-rewrite.ps1`** — bloqueado sem **`DATA_BOAR_ALLOW_DESTRUCTIVE_REPO_OPS=1`**; **não** definir isto no Linux primary dev workstation para trabalho normal. |
| **Git destrutivo no clone canônico** | **`git reset --hard`**, **`git clean -fdx`**, **force** em branch ou qualquer operação que **descarte** trabalho não integrado em **`~/Projects/dev/data-boar`** — use **`git pull`**, **`git merge`**, **`git stash`** ou **branch nova**. |
| **Narrativas falsas** | Dizer no chat que um reset destrutivo “correu” sem comandos reais num host acordado — ver **`clean-slate-pii-self-audit.mdc`**. |

---

## Permitido no Linux primary dev workstation (seguro para a árvore canônica)

| Ação | Notas |
| ------ | ----- |
| **Guards na árvore atual** | `uv run python scripts/pii_history_guard.py`, `uv run pytest tests/test_pii_guard.py`, **`./scripts/check-all.sh`** |
| **Auditorias com clone só em temp** | Diretório vazio em **`/tmp/`** + `git clone` + mesmos guards — **nunca** apagar **`DATA_BOAR_ROOT`**. Equivalentes Windows usam só **`%TEMP%`**. |
| **Git normal** | `git fetch`, `git pull`, merge/rebase, stash, branches de feature |
| **Pre-commit + gate de PR** | **`uv run pre-commit install`** uma vez por clone; **`./scripts/check-all.sh`** antes de cada PR (ver **`docs/ops/COMMIT_AND_PR.pt_BR.md`**) |
| **Busca só leitura de arquivo / caminho** | Ver **Busca de arquivos (Linux)** abaixo — **não** Voidtools **`es.exe`**. |
| **tmux remoto (Cursor + Claude)** | **`./scripts/primary-linux-agent-sessions.sh start`** — sessões worker + `/rc`; **`install-systemd`** + **`loginctl enable-linger`** para sobreviver a logout/boot |

---

## Busca de arquivos (Linux — substitui Everything / `es-find` no Windows)

No **primary Linux dev workstation**, **`scripts/es-find.ps1`** e **`es.exe`** **não** se aplicam. Use ferramentas nativas (palavra-chave **`es-find`** continua **só Windows** — **`.cursor/rules/session-mode-keywords.mdc`**).

| Ferramenta | Uso típico |
| ---- | ----------- |
| **`find`** | Varreduras com escopo; último recurso quando índice está desatualizado ou path fora da cobertura do `updatedb`. |
| **`fd`** | Busca rápida por nome; prefira a **`find`** sem limite a partir de `$HOME` ou árvores enormes de sync. |
| **`locate` / `plocate`** | Lookup indexado de basename/caminho — **plocate 1.1.23** no primary Linux dev workstation; confirme **`updatedb`** / **`plocate-build`** antes de confiar no resultado. |
| **`git grep`** | Conteúdo em arquivos **rastreados** no **`HEAD`** ou no histórico (`git log -S`, fluxos pickaxe). |
| **`grep -r`** | Conteúdo na working tree ou raízes acordadas (inclui **`docs/private/`** no disco — redija na saída pública). |

**Assistentes no Linux primary dev workstation:** prefira **`Glob`** / **`Grep`** dentro do workspace quando for rápido; use **`find`**, **`fd`** ou **`plocate`** fora do workspace ou em árvores grandes. **Não** peça para instalar Everything no Linux.

**Referências:** [ADR 0023](../adr/ADR-0023-windows-primary-dev-filename-search-everything-es-first-with-fallback.md) (**`es.exe`** no Windows); [ADR 0068](../adr/ADR-0068-primary-linux-dev-workstation-temporary.md) (Linux primary temporário + mapeamento de ferramentas).

---

## Onde correr fluxos classe destrutiva

1. **Host de lab designado** (SSH **lab-op**): operador corre **`clean-slate`** / ensaios de rewrite aí, ou usa **diretório vazio** + clone nessa máquina.
2. **Env opt-in** (só script de rewrite): **`DATA_BOAR_ALLOW_DESTRUCTIVE_REPO_OPS=1`** — documentar em notas **privadas** que **nunca** está ativo no Linux primary dev workstation para uso rotineiro.

---

## Regra do assistente

**`.cursor/rules/primary-linux-workstation-protected-no-destructive-repo-ops.mdc`** (`alwaysApply: true`).

**Windows (quando o primário voltar):** **`.cursor/rules/primary-windows-workstation-protected-no-destructive-repo-ops.mdc`** + **`docs/ops/PRIMARY_WINDOWS_WORKSTATION_PROTECTION.pt_BR.md`**.
