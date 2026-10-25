<#
.SYNOPSIS
    LAB-ROUTER-01 -- acessa a API do UniFi Dream Machine SE via API key (Bitwarden).

.DESCRIPTION
    Busca a API key do LAB-ROUTER-01 no Bitwarden (item "cursor.auto.ai" / LAB-ROUTER-01 Integration),
    autentica na API local e executa comandos de consulta de rede.

    Requer: bw CLI autenticado (bw unlock) + variavel BW_SESSION no ambiente.
    API key salva em Bitwarden com nome "LAB-ROUTER-01 cursor.auto.ai API key" (ou similar).

.PARAMETER Command
    status      Exibe estado basico do LAB-ROUTER-01 (versao, sitename, uptime)
    clients     Lista clientes conectados (IP, MAC, hostname, SSID/VLAN)
    wifi        Lista redes Wi-Fi e configuracoes
    vlans       Lista VLANs configuradas
    scan        Coleta TUDO: status + clients + wifi + vlans + security + alerts
    ports       Lista portas do switch (LAB-ROUTER-01-SE tem switch integrado)
    alerts      Lista alertas ativos

.PARAMETER BwItemName
    Nome do item no Bitwarden que contem a API key. Padrao: "LAB-ROUTER-01 cursor.auto.ai"

.PARAMETER ApiKey
    API key direta (para nao usar Bitwarden). Preferir BW_SESSION.

.PARAMETER Out
    Arquivo de saida para salvar o resultado (JSON). Padrao: stdout.

.EXAMPLE
    # Com Bitwarden (recomendado):
    $env:BW_SESSION = (bw unlock --raw)
    .\scripts\LAB-ROUTER-01.ps1 -Command scan

    # Com API key direta (temporario):
    .\scripts\LAB-ROUTER-01.ps1 -Command clients -ApiKey "minha-api-key"

    # Via dispatcher ATS:
    .\scripts\ats.ps1 LAB-ROUTER-01-scan
#>

param(
    [Parameter(Position=0)] [string]$Command = "status",
    [string]$BwItemName = "LAB-ROUTER-01 cursor.auto.ai",
    [string]$ApiKey = "",
    [string]$Out = ""
)

$LAB-ROUTER-01Base = "https://unifi.local"
$RepoRoot = Split-Path $PSScriptRoot -Parent

function Write-Header($msg) { Write-Host "`n=== $msg ===" -ForegroundColor Cyan }
function Write-Ok($msg)     { Write-Host "  OK  $msg" -ForegroundColor Green }
function Write-Warn($msg)   { Write-Host " WARN $msg" -ForegroundColor Yellow }
function Write-Info($msg)   { Write-Host "  ... $msg" -ForegroundColor Gray }

# --- Obter API key ---
function Get-LAB-ROUTER-01ApiKey {
    if ($ApiKey) { return $ApiKey }

    # Tentar Bitwarden CLI
    if (-not $env:BW_SESSION) {
        Write-Warn "BW_SESSION nao definido. Tente:"
        Write-Host '    $env:BW_SESSION = (bw unlock --raw)' -ForegroundColor Yellow
        Write-Host "    .\scripts\LAB-ROUTER-01.ps1 -Command status" -ForegroundColor Yellow
        exit 1
    }

    Write-Info "Buscando API key no Bitwarden: '$BwItemName'..."
    try {
        $bwOutput = bw get item $BwItemName --session $env:BW_SESSION 2>&1 | ConvertFrom-Json
        if ($bwOutput.login.password) {
            return $bwOutput.login.password
        } elseif ($bwOutput.fields) {
            $field = $bwOutput.fields | Where-Object { $_.name -imatch "api.?key|token|key" } | Select-Object -First 1
            if ($field) { return $field.value }
        }
        Write-Error "Item '$BwItemName' encontrado no BW mas sem campo de API key/password."
        exit 1
    } catch {
        Write-Error "Falha ao buscar no Bitwarden: $_"
        Write-Warn "Verifique se o item existe: bw list items --search 'LAB-ROUTER-01'"
        exit 1
    }
}

# --- Helper para chamadas API ---
function Invoke-LAB-ROUTER-01Api {
    param([string]$Path, [string]$Key)
    try {
        $r = Invoke-WebRequest -Uri "$LAB-ROUTER-01Base$Path" `
            -Headers @{"X-API-Key" = $Key; "Accept" = "application/json"} `
            -SkipCertificateCheck -TimeoutSec 10 -ErrorAction Stop
        return $r.Content | ConvertFrom-Json
    } catch {
        $code = $_.Exception.Response.StatusCode.value__
        if ($code -eq 401) { Write-Error "API key invalida ou expirada. Verifique no BW." }
        elseif ($code -eq 403) { Write-Error "Permissao negada para $Path (usuario auto.cursor tem permissoes limitadas)" }
        else { Write-Error "Erro $code em ${Path}: $_" }
        return $null
    }
}

function Save-Or-Print($data, $section) {
    $json = $data | ConvertTo-Json -Depth 8
    if ($Out) {
        $json | Add-Content -Path $Out -Encoding UTF8
        Write-Ok "Salvo em: $Out"
    } else {
        Write-Header $section
        $json | Out-Host
    }
}

# --- Comandos ---
Write-Header "LAB-ROUTER-01 API -- $Command"
$key = Get-LAB-ROUTER-01ApiKey

switch ($Command.ToLower()) {

    "status" {
        Write-Info "Consultando status do sistema..."
        $sys = Invoke-LAB-ROUTER-01Api "/proxy/network/integration/v1/system" $key
        if ($sys) { Save-Or-Print $sys "Status do Sistema LAB-ROUTER-01" }

        $site = Invoke-LAB-ROUTER-01Api "/proxy/network/api/s/default/stat/device-basic" $key
        if ($site) { Save-Or-Print $site "Dispositivos UniFi" }
    }

    "clients" {
        Write-Info "Listando clientes conectados..."
        $clients = Invoke-LAB-ROUTER-01Api "/proxy/network/api/s/default/stat/sta" $key
        if ($clients -and $clients.data) {
            Write-Host "`n--- Clientes conectados: $($clients.data.Count) ---"
            $clients.data | Select-Object @{N='Hostname';E={if($_.hostname){$_.hostname}else{'(sem nome)'}}} `
                , @{N='IP';E={$_.ip}} `
                , @{N='MAC';E={$_.mac}} `
                , @{N='SSID/VLAN';E={if($_.essid){$_.essid}else{"VLAN $($_.vlan)"}}} `
                , @{N='Signal';E={"$($_.signal) dBm"}} `
                , @{N='Tx/Rx(MB)';E={"$([math]::Round($_.tx_bytes/1MB,1))/$([math]::Round($_.rx_bytes/1MB,1))"}} |
                Sort-Object Hostname | Format-Table -AutoSize
        }
    }

    "wifi" {
        Write-Info "Listando redes Wi-Fi..."
        $wlans = Invoke-LAB-ROUTER-01Api "/proxy/network/api/s/default/rest/wlanconf" $key
        if ($wlans -and $wlans.data) {
            $wlans.data | Select-Object name, security, enabled, @{N='Band';E={$_.band}}, vlan_enabled, vlan |
                Format-Table -AutoSize
        }
    }

    "vlans" {
        Write-Info "Listando VLANs/redes..."
        $nets = Invoke-LAB-ROUTER-01Api "/proxy/network/api/s/default/rest/networkconf" $key
        if ($nets -and $nets.data) {
            $nets.data | Select-Object name, purpose, ip_subnet, vlan, dhcpd_enabled, igmp_snooping |
                Format-Table -AutoSize
        }
    }

    "alerts" {
        Write-Info "Buscando alertas ativos..."
        $alerts = Invoke-LAB-ROUTER-01Api "/proxy/network/api/s/default/stat/alarm" $key
        if ($alerts -and $alerts.data) {
            $alerts.data | Select-Object datetime, msg, key | Format-Table -AutoSize
        }
    }

    "ports" {
        Write-Info "Listando portas do switch integrado..."
        $ports = Invoke-LAB-ROUTER-01Api "/proxy/network/api/s/default/stat/device" $key
        if ($ports -and $ports.data) {
            $ports.data | Where-Object { $_.type -in @("usw","LAB-ROUTER-01") } | ForEach-Object {
                Write-Header "Dispositivo: $($_.name) ($($_.type))"
                $_.port_table | Select-Object port_idx, name, up, speed, full_duplex, poe_enable, poe_power |
                    Format-Table -AutoSize
            }
        }
    }

    "scan" {
        Write-Header "Scan completo da rede"
        if ($Out) { "# LAB-ROUTER-01 Scan - $(Get-Date -Format 'yyyy-MM-dd HH:mm')" | Set-Content $Out -Encoding UTF8 }

        foreach ($cmd in @("status", "clients", "wifi", "vlans", "alerts", "ports")) {
            Write-Info "Coletando: $cmd..."
            # Recursao interna nao funciona bem, usar Invoke diretamente
            switch ($cmd) {
                "status" {
                    $d = Invoke-LAB-ROUTER-01Api "/proxy/network/integration/v1/system" $key
                    if ($d) { Save-Or-Print $d "STATUS" }
                }
                "clients" {
                    $d = Invoke-LAB-ROUTER-01Api "/proxy/network/api/s/default/stat/sta" $key
                    if ($d -and $d.data) {
                        Write-Header "CLIENTES ($($d.data.Count))"
                        $d.data | Select-Object @{N='Host';E={$_.hostname}}, ip, mac, @{N='SSID';E={$_.essid}}, signal |
                            Format-Table -AutoSize
                    }
                }
                "wifi" {
                    $d = Invoke-LAB-ROUTER-01Api "/proxy/network/api/s/default/rest/wlanconf" $key
                    if ($d -and $d.data) { Save-Or-Print $d.data "WIFI" }
                }
                "vlans" {
                    $d = Invoke-LAB-ROUTER-01Api "/proxy/network/api/s/default/rest/networkconf" $key
                    if ($d -and $d.data) { Save-Or-Print $d.data "VLANS/REDES" }
                }
                "alerts" {
                    $d = Invoke-LAB-ROUTER-01Api "/proxy/network/api/s/default/stat/alarm" $key
                    if ($d -and $d.data) { Save-Or-Print $d.data "ALERTAS" }
                }
            }
        }
        Write-Ok "Scan completo."
    }

    default {
        Write-Error "Comando desconhecido: $Command. Opcoes: status, clients, wifi, vlans, alerts, ports, scan"
    }
}
