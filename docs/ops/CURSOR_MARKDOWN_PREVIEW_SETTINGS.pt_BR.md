# Cursor / VS Code: preview de Markdown em aba (sem split forcado)

**English:** [CURSOR_MARKDOWN_PREVIEW_SETTINGS.md](CURSOR_MARKDOWN_PREVIEW_SETTINGS.md)

**Audiencia:** Operador no **Windows** com **Cursor** (definicoes de utilizador compativeis com VS Code).

## Problema

O **Preview** de Markdown ou **Cursor Settings** abre numa **segunda coluna** (split vertical) em vez de uma **aba** normal no mesmo grupo de editores.

## Correcao (settings do utilizador)

Editar **`%APPDATA%\Cursor\User\settings.json`** (JSON valido: virgulas entre chaves).

1. **`markdown.preview.openPreviewToTheSide`:** **`false`**.
2. Em **`workbench.editor.autoLockGroups`**:
   - **`mainThreadWebview-markdown.preview`:** **`false`**
   - **`workbench.editor.markdown`:** **`false`** (ou remover o lock)

## Opcional: atalhos

Em **`%APPDATA%\Cursor\User\keybindings.json`**, ligar **`Ctrl+Shift+V`** a **`markdown.showPreview`** com **`when`**: `editorLangId == markdown && !notebookEditorFocused`.

**Nota:** **`Ctrl+K`** depois **`V`** continua sendo o atalho explicito para preview **ao lado**.

## Verificacao anti-regressao (script no repo)

Na raiz do repositorio:

```powershell
.\scripts\check-cursor-markdown-preview-settings.ps1
```

- **`0`:** valores obrigatorios parecem corretos.
- **`1`:** corrigir as chaves indicadas em `settings.json`.

**Nao** corre no CI do GitHub (caminhos sao locais ao PC do operador).

## Regra / skill do assistente

Ver **`.cursor/rules/cursor-markdown-preview-guardrail.mdc`** e **`.cursor/skills/cursor-markdown-preview-settings/SKILL.md`**.
