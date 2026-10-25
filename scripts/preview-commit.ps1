# Preview what would be committed (no stage, no commit). Use before crafting title/body for commit-or-pr.ps1.
# Usage: .\scripts\preview-commit.ps1
# Run from repo root. See commit-or-pr.ps1 -Action Preview for optional -Title/-Body to see proposed message.
& (Join-Path $PSScriptRoot "commit-or-pr.ps1") -Action Preview
