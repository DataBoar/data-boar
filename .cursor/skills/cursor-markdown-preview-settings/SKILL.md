---
name: cursor-markdown-preview-settings
description: >-
  Restore and verify Cursor/VS Code settings so Markdown preview opens in a normal tab
  instead of a forced side-by-side split. Use when the operator reports Ctrl+Shift+V or
  preview opening in a second editor column after updates or settings sync.
---

# Cursor Markdown preview (no forced split)

## Files (Windows)

| File | Purpose |
| ---- | ------- |
| `%APPDATA%\Cursor\User\settings.json` | `markdown.preview.openPreviewToTheSide`, `workbench.editor.autoLockGroups` |
| `%APPDATA%\Cursor\User\keybindings.json` | Optional explicit `Ctrl+Shift+V` -> `markdown.showPreview` |

## Required values

1. `"markdown.preview.openPreviewToTheSide": false`
2. Under `workbench.editor.autoLockGroups`: `"mainThreadWebview-markdown.preview": false`, `"workbench.editor.markdown": false` (or omit / false).
3. Optional: keybinding for `markdown.showPreview` on `ctrl+shift+v` for Markdown editors only.

## Repo guardrail

Run from repo root:

```powershell
.\scripts\check-cursor-markdown-preview-settings.ps1
```

Exit `0` = OK; `1` = fix settings per **`docs/ops/CURSOR_MARKDOWN_PREVIEW_SETTINGS.md`**.

## After Cursor upgrades

Re-run the script; major upgrades may reset or merge JSON incorrectly.
