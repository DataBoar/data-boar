# One-off: run commit-or-pr.ps1 with a predefined message (avoids CLI escaping).
$Title = "Quality: SonarQube markdown fixes and commit/PR automation"
$Body = @"
Markdown: fix SonarQube MD007, MD009, MD012, MD029, MD032, MD036, MD047, MD060 across project .md files
- Add scripts/fix_markdown_sonar.py for automated MD fixes; align tables, trailing spaces, blanks, list style
- Resolve duplicate headings in README, USAGE, SENSITIVITY_DETECTION (EN/pt-BR)
- Update test_markdown_lint to accept aligned table style; document in TESTING.md
- SonarQube: add sonar-project.properties, CI job, scripts/sonar_issues.py, and docs for extension + automation
- commit-or-pr.ps1: here-string removed for parser; discard branch check output via null; dry run verified
"@
& (Join-Path $PSScriptRoot "commit-or-pr.ps1") -Action Commit -Title $Title -Body $Body
