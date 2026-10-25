#Requires -Version 5.1
<#
.SYNOPSIS
  Quick connectivity probes for lab external-eval (HTTP GET + optional TCP). Not a full Data Boar scan.

.DESCRIPTION
  Use from the operator PC to verify outbound HTTPS and optional LAN DB ports before or after
  firewall changes. ASCII-only for Windows PowerShell 5.1.

.EXAMPLE
  .\scripts\lab-external-smoke.ps1

.EXAMPLE
  .\scripts\lab-external-smoke.ps1 -TcpHost "192.0.2.1" -TcpPort 55432
#>
param(
    [string] $RestUrl = "https://api.restful-api.dev/objects",
    [string] $TcpHost = "",
    [int] $TcpPort = 0
)

$ErrorActionPreference = "Continue"
$exit = 0

Write-Host "=== lab-external-smoke: GET $RestUrl ===" -ForegroundColor Cyan
$curl = Get-Command curl.exe -ErrorAction SilentlyContinue
if (-not $curl) {
    Write-Warning "curl.exe not found on PATH."
    $exit = 2
} else {
    & curl.exe -sS -o NUL -w "HTTP_CODE=%{http_code} TIME=%{time_total}s\n" --max-time 25 $RestUrl 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "curl exit $LASTEXITCODE (may be offline, TLS, or block)."
        $exit = 1
    }
}

if ($TcpHost -and $TcpPort -gt 0) {
    Write-Host "=== TCP probe $TcpHost : $TcpPort ===" -ForegroundColor Cyan
    $t = Test-NetConnection -ComputerName $TcpHost -Port $TcpPort -WarningAction SilentlyContinue
    if ($t.TcpTestSucceeded) {
        Write-Host "TCP ok"
    } else {
        Write-Warning "TCP failed (expected if nothing listens or firewall blocks)."
        if ($exit -eq 0) { $exit = 3 }
    }
}

Write-Host "Exit code: $exit (0=ok curl; 1=curl error; 2=no curl; 3=tcp fail)" -ForegroundColor DarkGray
exit $exit
