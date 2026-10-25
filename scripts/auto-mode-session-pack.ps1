param(
    [string]$TodayDate = "",
    [string]$RunDocsGate = "true",
    [string]$RunCodeGate = "false",
    [string]$RunProgressSnapshot = "true"
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($TodayDate)) {
    $TodayDate = (Get-Date).ToString("yyyy-MM-dd")
}

$runDocs = $RunDocsGate.ToLowerInvariant() -in @("1","true","yes","y")
$runCode = $RunCodeGate.ToLowerInvariant() -in @("1","true","yes","y")
$runSnap = $RunProgressSnapshot.ToLowerInvariant() -in @("1","true","yes","y")

Write-Host "=== Auto-mode session pack ==="
Write-Host "Date anchor: $TodayDate"
Write-Host ""

Write-Host "[1/5] Repo reality check"
git status -sb
git fetch origin
if (Get-Command gh -ErrorAction SilentlyContinue) {
    gh pr list --state open
} else {
    Write-Host "gh not available; skipping PR list." -ForegroundColor Yellow
}
Write-Host ""

if ($runDocs) {
    Write-Host "[2/5] Docs gate (locale + markdown)"
    uv run pytest tests/test_docs_pt_br_locale.py -q
    uv run pytest tests/test_markdown_lint.py::test_markdown_lint_no_violations -q
    Write-Host ""
}

if ($runCode) {
    Write-Host "[3/5] Code gate (check-all)"
    .\scripts\check-all.ps1
    Write-Host ""
} else {
    Write-Host "[3/5] Code gate skipped (RunCodeGate not enabled)"
    Write-Host ""
}

if ($runSnap) {
    Write-Host "[4/5] Progress snapshot"
    $out = "docs/private/progress/progress_snapshot_$TodayDate.md"
    powershell -NoProfile -ExecutionPolicy Bypass -File "scripts/progress-snapshot.ps1" -TodayDate $TodayDate -OutputMarkdown $out
    Write-Host ""
} else {
    Write-Host "[4/5] Progress snapshot skipped"
    Write-Host ""
}

Write-Host "[5/5] Safe close reminder"
Write-Host "- Run preview before commit/PR:"
Write-Host "  .\scripts\preview-commit.ps1"
Write-Host '  .\scripts\commit-or-pr.ps1 -Action Preview -Title "<title>" -Body "<bullets>"'
Write-Host "- Update carryover with explicit date for deferred items."
