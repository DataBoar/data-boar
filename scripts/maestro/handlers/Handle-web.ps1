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

# Definimos as configurações base de rede.
# Nota SRE: O ideal seria o Node informar qual a porta web, mas assumiremos 8080 como default do Data Boar
$targetIp = $Node.ip
$webPort = 8080
$apiUrl = "http://${targetIp}:${webPort}/api/status" # Ajuste para um endpoint válido da sua aplicação

# Usamos as ferramentas nativas do PowerShell (Invoke-WebRequest) no Maestro PC para testar o nó remoto
try {
    # Definimos um timeout baixo para não travar o Maestro se o serviço estiver offline
    $response = Invoke-WebRequest -Uri $apiUrl -Method Get -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop

    if ($response.StatusCode -eq 200) {
        Write-Host "      [SUCCESS] Persona Web Ativa! $($Node.hostname) responde HTTP 200 na porta $webPort." -ForegroundColor Green
    } else {
        Write-Warning "      [WARNING] Persona Web de $($Node.hostname) retornou um status inesperado: $($response.StatusCode)"
    }
} catch {
    # Capturamos timeouts, recusas de conexão, etc.
    Write-Warning "      [ERROR] Health Check Web falhou em $($Node.hostname). Serviço inacessível no IP ${targetIp}:${webPort}."
}
