# AUDIT RITUAL - DATA BOAR INTEGRITY ENGINEERING
# Wraps repo gates with timestamped logs under logs/ (operator Maestro / preflight habit).
# Default: full gate (same as scripts/check-all.ps1). Use -Mode lint-only for docs-only slices.
# Propagates exit code so CI-style failures are not masked.
param(
    [ValidateSet('check-all', 'lint-only')]
    [string]$Mode = 'check-all'
)

$ErrorActionPreference = 'Stop'
$logDir = Join-Path $PSScriptRoot 'logs'
if (!(Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }

$logFile = Join-Path $logDir ("audit-$(Get-Date -Format 'yyyyMMdd_HHmm').log")
$sessionLink = Join-Path $logDir 'latest.log'

$gateScript = if ($Mode -eq 'lint-only') {
    Join-Path $PSScriptRoot 'scripts\lint-only.ps1'
} else {
    Join-Path $PSScriptRoot 'scripts\check-all.ps1'
}

"--- AUDIT START: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ---" | Tee-Object -FilePath $logFile
"Mode: $Mode -> $gateScript" | Tee-Object -FilePath $logFile -Append
"Operator: $($env:USERNAME)" | Tee-Object -FilePath $logFile -Append
"Branch: $(git rev-parse --abbrev-ref HEAD) | Commit: $(git rev-parse --short HEAD)" | Tee-Object -FilePath $logFile -Append
"---------------------------------------------------" | Tee-Object -FilePath $logFile -Append

& $gateScript 2>&1 | Tee-Object -FilePath $logFile -Append
$exitCode = $LASTEXITCODE
if ($null -eq $exitCode) { $exitCode = 0 }

"---------------------------------------------------" | Tee-Object -FilePath $logFile -Append
"--- AUDIT END: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') | exit=$exitCode ---" | Tee-Object -FilePath $logFile -Append

Copy-Item $logFile $sessionLink -Force
exit $exitCode
