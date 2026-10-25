<#
.SYNOPSIS
    Mount or unmount a VeraCrypt file container (generic paths).
.DESCRIPTION
    Wrapper for VeraCrypt.exe. No passwords in this script; mount may open the
    VeraCrypt GUI for passphrase when /q is used without /p (recommended).

    Set environment defaults on the operator machine only, e.g.:
      DATA_BOAR_VERACRYPT_CONTAINER = full path to .hc
      DATA_BOAR_VERACRYPT_DRIVE     = single letter, e.g. V

.PARAMETER VaultPath
    Full path to the VeraCrypt container (.hc / .vc).
.PARAMETER DriveLetter
    Drive letter without colon (e.g. V).
.PARAMETER Unmount
    Dismount the drive letter.
.PARAMETER VeraCryptExe
    Override path to VeraCrypt.exe.
.EXAMPLE
    .\\scripts\\mount-secure-vault.ps1 -VaultPath $env:DATA_BOAR_VERACRYPT_CONTAINER -DriveLetter V
.EXAMPLE
    .\\scripts\\mount-secure-vault.ps1 -DriveLetter V -Unmount
#>
param(
    [Parameter(Mandatory = $false)]
    [string] $VaultPath = "",
    [Parameter(Mandatory = $false)]
    [ValidatePattern("^[A-Za-z]$")]
    [string] $DriveLetter = "",
    [switch] $Unmount,
    [Parameter(Mandatory = $false)]
    [string] $VeraCryptExe = "C:\Program Files\VeraCrypt\VeraCrypt.exe"
)

$ErrorActionPreference = "Stop"

if (-not $DriveLetter -and $env:DATA_BOAR_VERACRYPT_DRIVE) {
    $DriveLetter = $env:DATA_BOAR_VERACRYPT_DRIVE.TrimEnd(':')
}
if (-not $VaultPath -and $env:DATA_BOAR_VERACRYPT_CONTAINER) {
    $VaultPath = $env:DATA_BOAR_VERACRYPT_CONTAINER
}

if (-not $DriveLetter) {
    Write-Error "DriveLetter required or set DATA_BOAR_VERACRYPT_DRIVE."
    exit 1
}

$letter = $DriveLetter.Substring(0, 1).ToUpperInvariant()
$drivePath = "${letter}:\"

if (-not (Test-Path -LiteralPath $VeraCryptExe)) {
    Write-Error "VeraCrypt not found: $VeraCryptExe (install or pass -VeraCryptExe)."
    exit 1
}

if ($Unmount) {
    Write-Host "Dismounting ${letter}: ..."
    & $VeraCryptExe /d $letter /q /s
    if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne $null) {
        exit $LASTEXITCODE
    }
    Write-Host "Done."
    exit 0
}

if (-not $VaultPath) {
    Write-Error "VaultPath required or set DATA_BOAR_VERACRYPT_CONTAINER."
    exit 1
}
if (-not (Test-Path -LiteralPath $VaultPath)) {
    Write-Error "Container not found: $VaultPath"
    exit 1
}

if (Test-Path -LiteralPath $drivePath) {
    Write-Host "${letter}: already mounted."
    exit 0
}

Write-Host "Mounting vault at ${letter}: (GUI may ask for passphrase) ..."
& $VeraCryptExe /v $VaultPath /l $letter /q
if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne $null) {
    exit $LASTEXITCODE
}
Write-Host "If mount succeeded, ${letter}: is available."
exit 0
