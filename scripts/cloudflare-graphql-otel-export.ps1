<#
.SYNOPSIS
  Thin Windows wrapper for Cloudflare GraphQL -> OTLP edge metrics exporter (#1599).

.EXAMPLE
  .\scripts\cloudflare-graphql-otel-export.ps1 -Fixture tests\fixtures\cloudflare\http_requests_adaptive_groups.json -DryRun
#>
[CmdletBinding()]
param(
    [string]$Fixture = "",
    [switch]$DryRun,
    [switch]$NoWatermark,
    [string]$HostnameAllowlist = $env:CLOUDFLARE_HOSTNAME_ALLOWLIST
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$argsList = @("run", "python", "scripts/cloudflare_graphql_otel_export.py")
if ($Fixture) { $argsList += @("--fixture", $Fixture) }
if ($DryRun) { $argsList += "--dry-run" }
if ($NoWatermark) { $argsList += "--no-watermark" }
if ($HostnameAllowlist) { $argsList += @("--hostname-allowlist", $HostnameAllowlist) }

& uv @argsList
exit $LASTEXITCODE
