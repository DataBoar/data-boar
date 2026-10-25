<#
.SYNOPSIS
  Add a Windows Defender Firewall allow rule for inbound Data Boar HTTP (default TCP 8088) on the Private profile.

.DESCRIPTION
  Lab-only helper: scope to your LAN by using Private profile and/or adjusting RemoteAddress.
  Run elevated (Administrator) so New-NetFirewallRule succeeds.
  Does not open WAN; review rule in wf.msc after creation.

.PARAMETER Port
  TCP port (default 8088).
#>
[CmdletBinding()]
param(
    [int] $Port = 8088
)

$ErrorActionPreference = "Stop"
$ruleName = "Data Boar lab inbound TCP $Port (Private profile)"

if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
        [Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "Run PowerShell as Administrator to create firewall rules."
    exit 1
}

$existing = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "Rule already exists: $ruleName"
    exit 0
}

New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Protocol TCP -LocalPort $Port -Action Allow -Profile Private
Write-Host "Created: $ruleName"
