#Requires -Version 7.6.1
<#
.NAME
 scripts/maestro/Handle-LicensingMatrix.ps1

.SYNOPSIS
 Maestro capo: validate JWT tier enforcement matrix (community / pro / enterprise).

.DESCRIPTION
 Issues dev JWTs per tier, starts a short-lived API on loopback with licensing.mode enforced,
 and asserts Pro+ gates (report_pdf, scheduled_scans) allow or deny as expected.
 Skips with exit 0 when the lab signing key is missing.
#>

param(
    [string]$RepoRoot = "",
    [int]$Port = 19987,
    [int]$HealthTimeoutSec = 45
)

$ErrorActionPreference = "Stop"

function Write-MaestroStep {
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet("PASS", "FAIL", "SKIP", "INFO")]
        [string]$Status,
        [Parameter(Mandatory = $true)]
        [string]$Message
    )
    $color = switch ($Status) {
        "PASS" { "Green" }
        "FAIL" { "Red" }
        "SKIP" { "Yellow" }
        default { "Cyan" }
    }
    Write-Host "[Maestro:$Status] $Message" -ForegroundColor $color
}

function Get-RepoRoot {
    param([string]$Hint)
    if (-not [string]::IsNullOrWhiteSpace($Hint)) {
        return (Resolve-Path $Hint).Path
    }
    return (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
}

function Convert-ToYamlPath {
    param([string]$PathValue)
    return ($PathValue -replace "\\", "/")
}

function New-LicensingMatrixConfig {
    param(
        [string]$ConfigPath,
        [string]$LicensePath,
        [string]$PublicKeyPath,
        [string]$WorkDir,
        [int]$ApiPort
    )
    $sqlite = Join-Path $WorkDir "audit.db"
    $outDir = Join-Path $WorkDir "reports"
    New-Item -ItemType Directory -Force -Path $WorkDir | Out-Null
    New-Item -ItemType Directory -Force -Path $outDir | Out-Null
    $yaml = @"
licensing:
  mode: enforced
  license_path: $(Convert-ToYamlPath $LicensePath)
  public_key_path: $(Convert-ToYamlPath $PublicKeyPath)
targets: []
sqlite_path: $(Convert-ToYamlPath $sqlite)
report:
  output_dir: $(Convert-ToYamlPath $outDir)
api:
  port: $ApiPort
  require_api_key: false
"@
    Set-Content -Path $ConfigPath -Value $yaml -Encoding utf8NoBOM
}

function Wait-ApiHealth {
    param(
        [string]$BaseUrl,
        [int]$TimeoutSec
    )
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -Uri "$BaseUrl/health" -Method Get -TimeoutSec 3 -SkipHttpErrorCheck
            if ($response.StatusCode -eq 200) {
                return $true
            }
        } catch {
            # retry until timeout
        }
        Start-Sleep -Milliseconds 500
    }
    return $false
}

function Invoke-ApiPostStatus {
    param(
        [string]$Url,
        [string]$BodyJson = "{}"
    )
    $response = Invoke-WebRequest `
        -Uri $Url `
        -Method Post `
        -ContentType "application/json; charset=utf-8" `
        -Body $BodyJson `
        -SkipHttpErrorCheck
    return [int]$response.StatusCode
}

function Test-StatusAllowed {
    param(
        [int]$StatusCode,
        [int[]]$Allowed
    )
    return ($Allowed -contains $StatusCode)
}

function Start-MatrixApiProcess {
    param(
        [string]$Root,
        [string]$ConfigPath,
        [string]$LicensePath,
        [int]$ApiPort,
        [string]$PublicKeyPath
    )
    $logPath = Join-Path ([System.IO.Path]::GetTempPath()) ("data-boar-lic-matrix-log-" + [guid]::NewGuid().ToString("n") + ".txt")
    $errPath = $logPath -replace '\.txt$', '-err.txt'
    $args = @(
        "run", "python", "main.py",
        "--config", $ConfigPath,
        "--web",
        "--host", "127.0.0.1",
        "--port", "$ApiPort",
        "--allow-insecure-http"
    )
    $childEnv = [System.Collections.Hashtable](
        [System.Environment]::GetEnvironmentVariables([System.EnvironmentVariableTarget]::Process)
    )
    $childEnv["DATA_BOAR_LICENSE_PATH"] = $LicensePath
    $childEnv["DATA_BOAR_LICENSE_PUBLIC_KEY_PATH"] = $PublicKeyPath
    $childEnv["CONFIG_PATH"] = $ConfigPath
    $proc = Start-Process `
        -FilePath "uv" `
        -ArgumentList $args `
        -WorkingDirectory $Root `
        -RedirectStandardOutput $logPath `
        -RedirectStandardError $errPath `
        -PassThru `
        -WindowStyle Hidden `
        -Environment $childEnv
    return [PSCustomObject]@{
        Process = $proc
        LogPath = $logPath
        ErrPath = $errPath
    }
}

function Get-MatrixApiLogSnippet {
    param(
        $ApiBundle,
        [int]$MaxLines = 8
    )
    if ($null -eq $ApiBundle) {
        return ""
    }
    $parts = @()
    foreach ($label in @("stdout", "stderr")) {
        $pathProp = if ($label -eq "stdout") { "LogPath" } else { "ErrPath" }
        $path = $ApiBundle.$pathProp
        if (-not $path -or -not (Test-Path -LiteralPath $path)) {
            continue
        }
        $lines = Get-Content -LiteralPath $path -Tail $MaxLines -ErrorAction SilentlyContinue
        if ($lines) {
            $parts += "${label}: $($lines -join ' | ')"
        }
    }
    if ($parts.Count -eq 0) {
        return ""
    }
    return " (" + ($parts -join "; ") + ")"
}

function Stop-MatrixApiProcess {
    param($ApiBundle)
    if ($null -eq $ApiBundle -or $null -eq $ApiBundle.Process) {
        return
    }
    $proc = $ApiBundle.Process
    if (-not $proc.HasExited) {
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 1
    }
    if ($ApiBundle.LogPath -and (Test-Path $ApiBundle.LogPath)) {
        Remove-Item -Path $ApiBundle.LogPath -Force -ErrorAction SilentlyContinue
    }
    if ($ApiBundle.ErrPath -and (Test-Path $ApiBundle.ErrPath)) {
        Remove-Item -Path $ApiBundle.ErrPath -Force -ErrorAction SilentlyContinue
    }
}

function Add-MatrixAssertion {
    param(
        [ref]$FailureList,
        [string]$Tier,
        [string]$CaseName,
        [bool]$Ok,
        [string]$Detail
    )
    if ($Ok) {
        Write-MaestroStep INFO "tier=$Tier case=$CaseName ok ($Detail)"
        return
    }
    $msg = "tier=$Tier case=$CaseName $Detail"
    $FailureList.Value += $msg
    Write-MaestroStep INFO "tier=$Tier case=$CaseName FAIL ($Detail)"
}

$RepoRoot = Get-RepoRoot -Hint $RepoRoot
$homeRoot = if ($env:USERPROFILE) { $env:USERPROFILE } else { $env:HOME }
if ([string]::IsNullOrWhiteSpace($homeRoot)) {
    Write-MaestroStep FAIL "cannot resolve USERPROFILE or HOME for keys path"
    exit 1
}

$keysDir = Join-Path $homeRoot ".keys/data-boar"
$signKey = $env:DATA_BOAR_LICENSE_ISSUER_PRIVATE_KEY_PEM_FILE
if ([string]::IsNullOrWhiteSpace($signKey)) {
    $signKey = Join-Path $keysDir "license-signing-v1-pkcs8.pem"
}
if (-not (Test-Path -LiteralPath $signKey)) {
    Write-MaestroStep SKIP "no signing key"
    exit 0
}

$pubKey = Join-Path $keysDir "license-pub-v1.pem"
if (-not (Test-Path -LiteralPath $pubKey)) {
    Write-MaestroStep SKIP "no public key at $(Convert-ToYamlPath $pubKey)"
    exit 0
}

$issuerScript = Join-Path $RepoRoot "scripts/issue_dev_license_jwt.py"
if (-not (Test-Path -LiteralPath $issuerScript)) {
    Write-MaestroStep FAIL "missing issuer script at $(Convert-ToYamlPath $issuerScript)"
    exit 1
}

New-Item -ItemType Directory -Force -Path $keysDir | Out-Null
$env:DATA_BOAR_LICENSE_ISSUER_PRIVATE_KEY_PEM_FILE = $signKey

$tierLicenses = @{
    community  = Join-Path $keysDir "dev-community.lic"
    pro        = Join-Path $keysDir "dev-pro.lic"
    enterprise = Join-Path $keysDir "dev-enterprise.lic"
}

foreach ($tier in @("community", "pro", "enterprise")) {
    $outPath = $tierLicenses[$tier]
    & uv run python $issuerScript `
        --dbtier $tier `
        --sub "maestro-$tier" `
        --out $outPath `
        --private-key-pem-file $signKey
    if ($LASTEXITCODE -ne 0) {
        Write-MaestroStep FAIL "JWT issue failed for tier=$tier"
        exit 1
    }
}

Remove-Item Env:DATA_BOAR_LICENSE_PATH -ErrorAction SilentlyContinue
Remove-Item Env:DATA_BOAR_LICENSE_PUBLIC_KEY_PATH -ErrorAction SilentlyContinue
Remove-Item Env:CONFIG_PATH -ErrorAction SilentlyContinue

$failures = [System.Collections.Generic.List[string]]::new()
$workRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("data-boar-lic-matrix-" + [guid]::NewGuid().ToString("n"))
New-Item -ItemType Directory -Force -Path $workRoot | Out-Null

try {
    foreach ($tier in @("community", "pro", "enterprise")) {
        $tierDir = Join-Path $workRoot $tier
        New-Item -ItemType Directory -Force -Path $tierDir | Out-Null
        $cfgPath = Join-Path $tierDir "config.yaml"
        New-LicensingMatrixConfig `
            -ConfigPath $cfgPath `
            -LicensePath $tierLicenses[$tier] `
            -PublicKeyPath $pubKey `
            -WorkDir $tierDir `
            -ApiPort $Port

        $apiBundle = $null
        try {
            $apiBundle = Start-MatrixApiProcess -Root $RepoRoot -ConfigPath $cfgPath -LicensePath $tierLicenses[$tier] -ApiPort $Port -PublicKeyPath $pubKey
            $baseUrl = "http://127.0.0.1:$Port"
            if (-not (Wait-ApiHealth -BaseUrl $baseUrl -TimeoutSec $HealthTimeoutSec)) {
                $logHint = Get-MatrixApiLogSnippet -ApiBundle $apiBundle
                Add-MatrixAssertion -FailureList ([ref]$failures) -Tier $tier -CaseName "health" -Ok $false -Detail "API did not become healthy on $baseUrl$logHint"
                continue
            }

            $healthResp = Invoke-WebRequest -Uri "$baseUrl/health" -Method Get -SkipHttpErrorCheck
            Write-MaestroStep INFO "tier=$tier health.license=$($healthResp.Content)"

            $pdfStatus = Invoke-ApiPostStatus -Url "$baseUrl/scan_pdf" -BodyJson "{}"
            $scanSchedStatus = Invoke-ApiPostStatus -Url "$baseUrl/scan" -BodyJson '{"scheduled":true}'
            $scanNormalStatus = Invoke-ApiPostStatus -Url "$baseUrl/scan" -BodyJson "{}"

            if ($tier -eq "community") {
                Add-MatrixAssertion -FailureList ([ref]$failures) -Tier $tier -CaseName "scan_pdf" -Ok ($pdfStatus -eq 403) -Detail "expected 403 got $pdfStatus"
                Add-MatrixAssertion -FailureList ([ref]$failures) -Tier $tier -CaseName "scan_scheduled" -Ok ($scanSchedStatus -eq 403) -Detail "expected 403 got $scanSchedStatus"
                Add-MatrixAssertion -FailureList ([ref]$failures) -Tier $tier -CaseName "scan_normal" -Ok (Test-StatusAllowed -StatusCode $scanNormalStatus -Allowed @(200, 202)) -Detail "expected 200/202 got $scanNormalStatus"
            } else {
                Add-MatrixAssertion -FailureList ([ref]$failures) -Tier $tier -CaseName "scan_pdf" -Ok (Test-StatusAllowed -StatusCode $pdfStatus -Allowed @(200, 202)) -Detail "expected 200/202 got $pdfStatus"
                Add-MatrixAssertion -FailureList ([ref]$failures) -Tier $tier -CaseName "scan_scheduled" -Ok (Test-StatusAllowed -StatusCode $scanSchedStatus -Allowed @(200, 202)) -Detail "expected 200/202 got $scanSchedStatus"
            }
        } finally {
            Stop-MatrixApiProcess -ApiBundle $apiBundle
        }
    }
} finally {
    Remove-Item -Recurse -Force $workRoot -ErrorAction SilentlyContinue
}

if ($failures.Count -eq 0) {
    Write-MaestroStep PASS "licensing matrix assertions ok (community/pro/enterprise)"
    exit 0
}

Write-MaestroStep FAIL ($failures -join "; ")
exit 1
