# One-off: PR for release 1.4.1 (release notes, permissions, conflict prevention).
$Title = "Release 1.4.1: release notes, workflow permissions, merge-conflict prevention"
$Body = @"
Add release notes and finish release-prep changes for 1.4.1.

- Add docs/releases/1.4.1.md with release notes for GitHub release pack
- CI/CodeQL: explicit permissions in workflows (satisfy GitHub warning); comment in codeql.yml
- CONTRIBUTING: Reducing merge conflicts (rebase/merge main before PR; report/generator.py structure)
- report/generator.py: module docstring notes _write_excel_sheets pattern for future merges
"@
& (Join-Path $PSScriptRoot "commit-or-pr.ps1") -Action PR -Title $Title -Body $Body
