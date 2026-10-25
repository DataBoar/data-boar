#Requires -Version 5.1
<#
.SYNOPSIS
    Revoga uma chave GPG local e publica a revogacao nos keyservers.

.PARAMETER KeyId
    ID da chave GPG a revogar (8 ou 40 hex chars).

.PARAMETER Reason
    Razao: 0=nenhuma, 1=comprometida, 2=substituida, 3=nao_usada (default: 3)

.PARAMETER Description
    Texto descritivo da revogacao.

.PARAMETER NoPublish
    Se informado, nao publica nos keyservers (apenas importa localmente).

.EXAMPLE
    .\scripts\gpg-revoke-key.ps1 -KeyId AD93917A9ED8C7EA
    .\scripts\gpg-revoke-key.ps1 -KeyId AD93917A9ED8C7EA -Reason 1 -Description "Chave comprometida"
#>
param(
    [Parameter(Mandatory)]
    [string]$KeyId,
    [int]$Reason = 3,
    [string]$Description = "Superseded by ED25519 key D6F81740AA5FAB8ACE5716AF871542E6F789F64F",
    [switch]$NoPublish
)

$gpg = "C:\Program Files\GnuPG\bin\gpg.exe"
if (-not (Test-Path $gpg)) { $gpg = (Get-Command gpg -ErrorAction SilentlyContinue)?.Source }
if (-not $gpg) { Write-Error "GPG nao encontrado"; exit 1 }

$outFile = "$env:TEMP\revoke_$KeyId.asc"

Write-Host "Gerando certificado de revogacao para $KeyId ..."
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $gpg
$psi.Arguments = "--command-fd 0 --output `"$outFile`" --gen-revoke $KeyId"
$psi.RedirectStandardInput = $true
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.UseShellExecute = $false
$psi.CreateNoWindow = $true
$proc = [System.Diagnostics.Process]::Start($psi)
$proc.StandardInput.WriteLine("y")
$proc.StandardInput.WriteLine($Reason)
$proc.StandardInput.WriteLine($Description)
$proc.StandardInput.WriteLine("")
$proc.StandardInput.WriteLine("y")
$proc.StandardInput.Close()
$proc.WaitForExit(15000)

if ($proc.ExitCode -ne 0 -or -not (Test-Path $outFile)) {
    Write-Error "Falha ao gerar certificado"
    exit 1
}
Write-Host "  Certificado gerado: $outFile ($((Get-Item $outFile).Length) bytes)"

Write-Host "Importando revogacao localmente..."
& $gpg --import $outFile 2>&1 | Select-String "revogacao|revocation|importado"

if (-not $NoPublish) {
    Write-Host "Publicando nos keyservers..."
    @("hkps://keyserver.ubuntu.com","hkps://keys.openpgp.org","hkps://keys.mailvelope.com") | ForEach-Object {
        & $gpg --keyserver $_ --send-keys $KeyId 2>&1 | Select-String "enviando|error|fail" | Select-Object -First 2
    }
}

Write-Host "`nConcluido. Verificar:"
& $gpg --list-keys --with-colons $KeyId 2>&1 | Select-String "^pub:" | ForEach-Object {
    $f = $_ -split ":"
    $st = switch($f[1]) { "r" {"REVOGADA"} "u" {"ATIVA"} "e" {"EXPIRADA"} default {$f[1]} }
    Write-Host "  $KeyId -> $st"
}