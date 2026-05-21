# beforeShellExecution hook - ADR file protection
# G0-S - agent safety hardening 2026-05-21
# Platform: Windows 11 + PowerShell
param([string]$Command = "")

if ($Command -match "git\s+(add|commit|stage)") {
    $staged = git diff --cached --name-only 2>$null | Where-Object { $_ -match "docs/adr/ADR-.*\.md" }
    if ($staged) {
        Write-Error "BLOCKED [G0-S]: commit includes ADR file: $($staged[0])"
        Write-Error "ADR modification requires explicit operator authorization (ADR-0056)."
        exit 1
    }
}
exit 0
