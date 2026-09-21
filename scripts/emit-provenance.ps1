#Requires -Version 5.1
<#
.SYNOPSIS
  Emit/verify local unsigned provenance record (#1950). Not SLSA.

.DESCRIPTION
  Twin of emit-provenance.sh. Default (no args): emit then verify with --require-sboms.
  Signed SLSA stays GitHub OIDC (`data-boar.intoto.jsonl` from the SBOM workflow).
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repoRoot
if ($args.Count -eq 0) {
    uv run python scripts/emit_provenance.py emit --require-sboms
    uv run python scripts/emit_provenance.py verify --require-sboms
    exit $LASTEXITCODE
}
uv run python scripts/emit_provenance.py @args
