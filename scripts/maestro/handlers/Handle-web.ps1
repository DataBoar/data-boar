#Requires -Version 7.6.1
<#
.NAME
 scripts/maestro/handlers/Handle-web.ps1

.SYNOPSIS
 Sub-Orquestrador especialista na persona 'web'.

.DESCRIPTION
 Responsável por validar se o Data Boar está servindo corretamente o Dashboard e a API no nó alvo.
 Ele atua como um pre-flight ou health-check de monitoramento HTTP, sendo uma etapa crucial
 antes que scripts de teste de carga ou API (que estão na esteira) tentem se comunicar com o serviço.
#>

param(
    [Parameter(Mandatory=$true)]$Node,
    [string]$Ref = "WorkingTree",
    [switch]$Deep # <--- Injeção do Maestro para habilitar o Benchmark
)

Write-Host "   [Web] Realizando Health Check da API/Dashboard e disparando orquestração containerizada (Deep: $Deep) em $($Node.hostname)..." -ForegroundColor DarkCyan

# Se for Deep, passa o caminho do config. Se não, não passa nada (comportamento original)
$configArg = if ($Deep) { "tests/config/benchmark-rc.yaml" } else { "" }

function Get-NodePropOrDefault {
    param(
        [Parameter(Mandatory = $true)]$Obj,
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)]$DefaultValue
    )
    $prop = $Obj.PSObject.Properties[$Name]
    if ($null -eq $prop -or $null -eq $prop.Value -or ($prop.Value -is [string] -and [string]::IsNullOrWhiteSpace($prop.Value))) {
        return $DefaultValue
    }
    return $prop.Value
}

# Definimos as configurações base de rede com defaults alinhados ao USAGE/TECH_GUIDE.
$targetIp = $Node.ip
$targetHost = $Node.hostname
$targetUser = $Node.user
$webScheme = [string](Get-NodePropOrDefault -Obj $Node -Name "web_scheme" -DefaultValue "http")
$webPort = [int](Get-NodePropOrDefault -Obj $Node -Name "web_port" -DefaultValue 8088)
$webHealthPath = [string](Get-NodePropOrDefault -Obj $Node -Name "web_health_path" -DefaultValue "/health")
if (-not $webHealthPath.StartsWith("/")) { $webHealthPath = "/$webHealthPath" }
$allowInsecureTls = [bool](Get-NodePropOrDefault -Obj $Node -Name "web_allow_insecure_tls" -DefaultValue $false)
$retries = [int](Get-NodePropOrDefault -Obj $Node -Name "web_check_retries" -DefaultValue 3)
$waitSeconds = [int](Get-NodePropOrDefault -Obj $Node -Name "web_check_wait_seconds" -DefaultValue 2)
$apiUrl = "${webScheme}://${targetIp}:${webPort}${webHealthPath}"
$localHealthOk = $false

function Test-HealthUrl {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Url,
        [Parameter(Mandatory = $true)]
        [string]$Scheme,
        [Parameter(Mandatory = $true)]
        [bool]$SkipTls
    )
    try {
        $req = @{
            Uri = $Url
            Method = "Get"
            TimeoutSec = 3
            UseBasicParsing = $true
            ErrorAction = "Stop"
        }
        if ($Scheme -eq "https" -and $SkipTls) {
            $req["SkipCertificateCheck"] = $true
        }
        $response = Invoke-WebRequest @req
        return ($response.StatusCode -eq 200)
    } catch {
        return $false
    }
}

# Sinal operacional extra: valida se o host remoto está escutando a porta alvo.
$listenerCmd = "ss -ltn 2>/dev/null | awk 'NR==1 || /:$webPort\b/'"
$listenerOut = ssh -q -o BatchMode=yes "$targetUser@$targetHost" "$listenerCmd"
if ($LASTEXITCODE -eq 0 -and $listenerOut -match ":$webPort") {
    Write-Host "      [Web-Precheck] Porta $webPort em escuta no host $targetHost." -ForegroundColor DarkGray
} else {
    Write-Warning "      [Web-Precheck] Porta $webPort sem listener visível em $targetHost."
}

for ($attempt = 1; $attempt -le $retries; $attempt++) {
    if (Test-HealthUrl -Url $apiUrl -Scheme $webScheme -SkipTls $allowInsecureTls) {
        Write-Host "      [SUCCESS] Persona Web Ativa! $($Node.hostname) responde HTTP 200 em $apiUrl." -ForegroundColor Green
        $localHealthOk = $true
        break
    } else {
        Write-Warning "      [WARNING] Health Check falhou para $apiUrl (tentativa $attempt/$retries)."
    }

    if ($attempt -lt $retries) {
        Start-Sleep -Seconds $waitSeconds
    }
}

if ($localHealthOk) {
    return
}

Write-Warning "      [Web-Recovery] Health check falhou. Tentando start fallback com main.py --web --host 0.0.0.0 --allow-insecure-http..."

$candidatePorts = @($webPort, 18088, 28088, 38088) | Select-Object -Unique
$portsJoined = ($candidatePorts -join " ")
$remoteStartCmd = @'
set -e
cd __NODE_PATH__
CHOSEN_PORT=""
for P in __PORTS_JOINED__; do
  if ! ss -ltn 2>/dev/null | grep -q ":${P}\b"; then
    CHOSEN_PORT="$P"
    break
  fi
done
if [ -z "$CHOSEN_PORT" ]; then
  CHOSEN_PORT="__WEB_PORT__"
fi
CFG_ARG=""
if [ -f config.yaml ]; then
  CFG_ARG="--config config.yaml"
elif [ -f deploy/config.example.yaml ]; then
  CFG_ARG="--config deploy/config.example.yaml"
fi
echo "$CHOSEN_PORT" > ~/.labop-web-port
if [ -x .venv/bin/python ]; then
  START_CMD=".venv/bin/python main.py ${CFG_ARG} --web --host 0.0.0.0 --allow-insecure-http --port ${CHOSEN_PORT}"
elif command -v uv >/dev/null 2>&1; then
  START_CMD="uv run python main.py ${CFG_ARG} --web --host 0.0.0.0 --allow-insecure-http --port ${CHOSEN_PORT}"
else
  START_CMD="python3 main.py ${CFG_ARG} --web --host 0.0.0.0 --allow-insecure-http --port ${CHOSEN_PORT}"
fi
nohup bash -lc "$START_CMD" > ~/.labop-web.log 2>&1 < /dev/null &
sleep 2
echo "$CHOSEN_PORT"
'@
$remoteStartCmd = $remoteStartCmd.Replace("__NODE_PATH__", [string]$Node.path)
$remoteStartCmd = $remoteStartCmd.Replace("__PORTS_JOINED__", [string]$portsJoined)
$remoteStartCmd = $remoteStartCmd.Replace("__WEB_PORT__", [string]$webPort)
$remoteStartCmd = $remoteStartCmd -replace "`r", ""
$startOut = ssh -q -o BatchMode=yes "$targetUser@$targetHost" "$remoteStartCmd"
if ($LASTEXITCODE -ne 0 -or -not $startOut) {
    Write-Warning "      [ERROR] Fallback web start falhou em $targetHost."
    return
}

$chosenPort = $webPort
foreach ($line in $startOut) {
    if ($line -match '^\d+$') {
        $chosenPort = [int]$line
    }
}

$remoteCurlCmd = "curl -fsS --max-time 5 http://127.0.0.1:$chosenPort$webHealthPath >/dev/null"
ssh -q -o BatchMode=yes "$targetUser@$targetHost" "$remoteCurlCmd" > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Warning "      [WARNING] Fallback web iniciou, mas curl remoto localhost falhou em ${targetHost}:$chosenPort$webHealthPath."
}

$webScheme = "http"
$apiUrl = "http://${targetIp}:${chosenPort}${webHealthPath}"
for ($attempt = 1; $attempt -le $retries; $attempt++) {
    if (Test-HealthUrl -Url $apiUrl -Scheme $webScheme -SkipTls $false) {
        Write-Host "      [SUCCESS] Persona Web recuperada! $($Node.hostname) responde HTTP 200 em $apiUrl." -ForegroundColor Green
        return
    }
    if ($attempt -lt $retries) {
        Start-Sleep -Seconds $waitSeconds
    }
}

Write-Warning "      [ERROR] Health Check Web falhou em $($Node.hostname) após fallback, incluindo start forçado. URL final: $apiUrl."
