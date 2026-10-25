# Proteção da estação de trabalho PC Windows principal de desenvolvimento (sem operações destrutivas no repo aqui)

**English:** [PRIMARY_WINDOWS_WORKSTATION_PROTECTION.md](PRIMARY_WINDOWS_WORKSTATION_PROTECTION.md)

**L-series** é um **papel**: o **PC Windows principal** de desenvolvimento, onde o clone **canônico** do `data-boar`, evidências locais e a **continuidade do histórico Git** devem ser preservados. **Não** é um hostname para commits ou docs públicos. **Âncora de hardware:** o laptop principal do operador costuma ser um ThinkPad **L-series** (ou similar); **nunca** confundir scripts de alinhamento **LAB-OP** (`lab-op-git-align-main`, `lab-op-git-ensure-ref` em **Reset**, etc.) com a árvore **canônica** nesta máquina — esses scripts atingem só hosts do **manifesto SSH**, não o workspace do Cursor no PC dev principal.

---

## Objetivos

- **Zero** apagamento acidental de **árvore completa**, reset **tipo clean-slate** ou **reescrita de histórico** na máquina onde o trabalho **cotidiano** vive.
- Ensaios **destrutivos** (clone destrutivo, `git filter-repo`, ensaios de force-push) só noutros **hosts de lab** — ou em **pastas isoladas** — à escolha do operador, **não** por defeito no PC Windows principal de desenvolvimento.

---

## Proibido no PC Windows principal de desenvolvimento

| Classe | Exemplos |
| ----- | -------- |
| **Clean-slate destrutivo** | Fluxos **`clean-slate.sh`** privados / modelo que fazem **`rm -rf`** na árvore principal e voltam a clonar (ver **PII_PUBLIC_TREE_OPERATOR_GUIDE.pt_BR.md** H.9). Inclui **WSL** se o alvo for a **mesma árvore canônica**. |
| **Reescrita de histórico sem guard** | **`scripts/run-pii-history-rewrite.ps1`** — bloqueado sem **`DATA_BOAR_ALLOW_DESTRUCTIVE_REPO_OPS=1`**; **não** definir isto no PC Windows principal de desenvolvimento para trabalho normal. |
| **Git destrutivo no clone canônico** | **`git reset --hard`**, **`git clean -fdx`**, **force** em branch ou qualquer operação que **descarte** trabalho não integrado na árvore **principal** no PC Windows principal — use **`git pull`**, **`git merge`**, **`git stash`** ou **branch nova**. (Contraste: hosts **LAB-OP** no **`lab-op-hosts.manifest.json`** podem usar reset duro / scripts de alinhamento **só nesses hosts** — ver **`LAB_COMPLETAO_RUNBOOK.md`** *Blast radius*.) |
| **Narrativas falsas** | Dizer no chat que um reset destrutivo “correu” sem comandos reais num host acordado — ver **`clean-slate-pii-self-audit.mdc`**. |

---

## Permitido no PC Windows principal de desenvolvimento (seguro para a árvore canônica)

| Ação | Notas |
| ------ | ----- |
| **Guards na árvore atual** | `uv run python scripts/pii_history_guard.py`, `pytest tests/test_pii_guard.py`, `.\scripts\check-all.ps1` |
| **Auditorias com clone só em temp** | **`scripts/pii-fresh-clone-audit.ps1`**, **`scripts/new-b2-verify.ps1`** — trabalham sob **`%TEMP%`** (ou path temp explícito); **não** apagam a pasta principal do repo. |
| **Everything / `es.exe`** | **`scripts/es-find.ps1`** — pesquisa só de nomes de arquivo, só leitura; **`docs/ops/EVERYTHING_ES_PRIMARY_WINDOWS_DEV_LAB.pt_BR.md`**; palavra-chave **`es-find`**; **`.cursor/rules/everything-es-cli.mdc`**. |

---

## Onde correr fluxos classe destrutiva

1. **Host de lab designado** (ex.: sessão SSH **lab-op**): o operador corre **`clean-slate`** / ensaios de rewrite aí, ou usa **diretório vazio** + clone nessa máquina.
2. **Env opt-in** (só script de rewrite): **`DATA_BOAR_ALLOW_DESTRUCTIVE_REPO_OPS=1`** — documentar em notas **privadas** que **nunca** está ativo no PC Windows principal de desenvolvimento para uso rotineiro; só numa máquina à parte, explícita, para remediação.

---

## Regra do assistente

**`.cursor/rules/primary-windows-workstation-protected-no-destructive-repo-ops.mdc`** (`alwaysApply: true`).
