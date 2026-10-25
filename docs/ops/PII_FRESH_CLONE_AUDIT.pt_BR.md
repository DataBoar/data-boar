# Auditoria PII com clone fresco (Windows, um comando)

**English:** [PII_FRESH_CLONE_AUDIT.md](PII_FRESH_CLONE_AUDIT.md)

**Objetivo:** Rodar os mesmos comandos de **autoauditoria** de um round **`clean-slate`** no Linux (`pii_history_guard.py --full-history` + `test_pii_guard`) em um **`git clone` novo** sob `%TEMP%`, sem apagar a árvore de trabalho principal.

**Não é:** Reescrita de histórico (`git filter-repo`, `scripts/run-pii-history-rewrite.ps1`). Ver **[PII_PUBLIC_TREE_OPERATOR_GUIDE.pt_BR.md](PII_PUBLIC_TREE_OPERATOR_GUIDE.pt_BR.md)** Parte II.

---

## Quando usar

- Validação periódica de que o **`main` público** + histórico completo ainda passam na automação (alinhamento ao ADR 0020).
- Depois de mudar guards de PII, política de seeds ou tabelas de substituição — comparar a intenção com um clone **limpo**.

---

## Comando

```powershell
.\scripts\pii-fresh-clone-audit.ps1
```

Padrão: clona **`main`** com **histórico completo** (necessário para `--full-history`), roda **`uv sync`**, depois:

1. `uv run python scripts/pii_history_guard.py --full-history`
2. `uv run pytest tests/test_pii_guard.py -q`

### Opções

| Opção | Significado |
| ----- | ----------- |
| `-KeepClone` | Mantém o diretório temporário em `%TEMP%` (para inspeção). |
| `-IncludeTalentGuards` | Roda também `tests/test_talent_public_script_placeholders.py` e `tests/test_talent_ps1_tracked_no_inline_pool.py` (ver seção D do guia). |
| `-SkipUvSync` | Pula `uv sync` (só faz sentido reaproveitando um clone mantido manualmente). |
| `-RepoUrl` | URL de clone (padrão: HTTPS público do GitHub). |
| `-TempCloneName` | Nome fixo da pasta em `%TEMP%` (padrão: `data-boar-pii-audit-*` com timestamp). |

---

## Fluxos relacionados

| Fluxo | Script / doc |
| ----- | ------------- |
| Greps de histórico para segmento **`C:\Users\...`** no Windows (escopo estreito) | **`scripts/new-b2-verify.ps1`** |
| Reset destrutivo + re-clone + seeds no Linux | **`docs/private.example/scripts/clean-slate.sh.example`** → **`clean-slate.sh`** privado; **[PII_PUBLIC_TREE_OPERATOR_GUIDE.pt_BR.md](PII_PUBLIC_TREE_OPERATOR_GUIDE.pt_BR.md)** H.9 |
| Assistente / memória (sem simulação) | Mesmo guia **H.10**; **`.cursor/rules/clean-slate-pii-self-audit.mdc`** |
| Palavra-chave de sessão | **`pii-fresh-audit`** em **`.cursor/rules/session-mode-keywords.mdc`** |

---

## Skill

`.cursor/skills/pii-fresh-clone-audit/SKILL.md`
