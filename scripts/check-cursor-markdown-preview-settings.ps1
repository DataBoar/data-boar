#Requires -Version 5.1
<#
.SYNOPSIS
  Validates Cursor/VS Code user settings that keep Markdown preview in-tab (no forced vertical split).

.DESCRIPTION
  Reads %APPDATA%\Cursor\User\settings.json and optionally keybindings.json.
  Exit 0 = checks pass; 1 = misconfiguration or unreadable files.
  ASCII-only for Windows PowerShell 5.1.

.EXAMPLE
  .\scripts\check-cursor-markdown-preview-settings.ps1
#>
$ErrorActionPreference = "Stop"
$exitCode = 0

function Write-Issue([string]$Message) {
    Write-Warning $Message
    $script:exitCode = 1
}

$settingsPath = Join-Path $env:APPDATA "Cursor\User\settings.json"
$keybindingsPath = Join-Path $env:APPDATA "Cursor\User\keybindings.json"

if (-not (Test-Path -LiteralPath $settingsPath)) {
    Write-Issue "Missing settings file: $settingsPath"
    exit $exitCode
}

try {
    $raw = Get-Content -LiteralPath $settingsPath -Raw -Encoding UTF8
    $s = $raw | ConvertFrom-Json
} catch {
    Write-Issue "Invalid JSON in settings.json: $_"
    exit $exitCode
}

if ($null -ne $s.'markdown.preview.openPreviewToTheSide' -and $s.'markdown.preview.openPreviewToTheSide' -ne $false) {
    Write-Issue "Set markdown.preview.openPreviewToTheSide to false (got: $($s.'markdown.preview.openPreviewToTheSide'))."
}

$al = $s.'workbench.editor.autoLockGroups'
if ($null -ne $al) {
    if ($al.'mainThreadWebview-markdown.preview' -eq $true) {
        Write-Issue "Set workbench.editor.autoLockGroups['mainThreadWebview-markdown.preview'] to false."
    }
    if ($al.'workbench.editor.markdown' -eq $true) {
        Write-Issue "Set workbench.editor.autoLockGroups['workbench.editor.markdown'] to false (or omit)."
    }
}

if (Test-Path -LiteralPath $keybindingsPath) {
    try {
        $kbRaw = Get-Content -LiteralPath $keybindingsPath -Raw -Encoding UTF8
        # Strip // comments (JSONC) for a naive parse: remove full-line // comments
        $kbLines = $kbRaw -split "`n" | Where-Object { $_ -notmatch '^\s*//' }
        $kbJson = ($kbLines -join "`n")
        $kb = $kbJson | ConvertFrom-Json
        $found = $false
        foreach ($entry in $kb) {
            if ($entry.key -eq 'ctrl+shift+v' -and $entry.command -eq 'markdown.showPreview') {
                $found = $true
                break
            }
        }
        if (-not $found) {
            Write-Host "Optional: add keybinding Ctrl+Shift+V -> markdown.showPreview (see docs/ops/CURSOR_MARKDOWN_PREVIEW_SETTINGS.md)." -ForegroundColor DarkGray
        }
    } catch {
        Write-Host "Note: keybindings.json not fully parsed (JSONC); check manually. $_" -ForegroundColor DarkGray
    }
} else {
    Write-Host "No keybindings.json (optional override skipped)." -ForegroundColor DarkGray
}

if ($exitCode -eq 0) {
    Write-Host "check-cursor-markdown-preview-settings: OK" -ForegroundColor Green
}
exit $exitCode
