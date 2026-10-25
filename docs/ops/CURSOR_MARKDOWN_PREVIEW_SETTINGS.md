# Cursor / VS Code: Markdown preview in-tab (no forced split)

**Português (Brasil):** [CURSOR_MARKDOWN_PREVIEW_SETTINGS.pt_BR.md](CURSOR_MARKDOWN_PREVIEW_SETTINGS.pt_BR.md)

**Audience:** Operator on **Windows** using **Cursor** (VS Code–compatible user settings).

## Problem

Markdown **Preview** or **Cursor Settings** opens in a **second vertical column** (side-by-side split) instead of a normal **tab** in the same editor group.

## Fix (User settings)

Edit **`%APPDATA%\Cursor\User\settings.json`** (JSON: comma-separated keys, valid syntax).

1. Set **`markdown.preview.openPreviewToTheSide`** to **`false`**.
2. Under **`workbench.editor.autoLockGroups`**, set:
   - **`mainThreadWebview-markdown.preview`**: **`false`**
   - **`workbench.editor.markdown`**: **`false`** (or remove the lock)

## Optional: keybindings

In **`%APPDATA%\Cursor\User\keybindings.json`**, bind **`Ctrl+Shift+V`** to **`markdown.showPreview`** with **`when`**: `editorLangId == markdown && !notebookEditorFocused` so the default “preview to the side” command does not win after updates.

**Note:** **`Ctrl+K`** then **`V`** is still the explicit “open preview to the side” shortcut by design.

## Anti-regression check (repo script)

From the repository root:

```powershell
.\scripts\check-cursor-markdown-preview-settings.ps1
```

- Exit **`0`**: required settings look correct.
- Exit **`1`**: fix the reported keys in `settings.json`.

This does **not** run inside GitHub CI (paths are local to the operator PC).

## Assistant / rule

See **`.cursor/rules/cursor-markdown-preview-guardrail.mdc`** and **`.cursor/skills/cursor-markdown-preview-settings/SKILL.md`**.
