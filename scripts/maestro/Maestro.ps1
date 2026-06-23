#Requires -Version 7.6.1
<#
.NAME
 scripts/maestro/Maestro.ps1

.SYNOPSIS
 Orquestrador Central Agnóstico e inteligente do Lab-Op. [cite: 0]

.DESCRIPTION
 Controla sub-orquestradores baseando atividades nas Personas possíveis. [cite: 1]
 Parametrizado pelo inventory.json escondido em docs/private/homelab/data. [cite: 8]
 Aceita o parâmetro -Ref para testes de versões efêmeras, operando a wrking Tree por padrão. [cite: 14]
 Precisamos buscar liçoes aprendidas [cite: 10]
#>

param(
    [string]$Ref = "WorkingTree",
    [switch]$Collect, # <--- NOVA FLAG SRE
    [switch]$Deep,    # <--- NOVA FLAG PARA TESTES RC
    [ValidateSet("", "stable", "beta")]
    [string]$BenchTrack = "",
    [string]$BenchRunId = "",
    [switch]$BenchCompare,
    [int]$BenchWebPort = 0,
    [string]$BenchHealthUrl = ""
)

# 1. Localização do Inventário Privado (Zero PII no código)[cite: 8, 14, 16]
$inventoryPath = "$PSScriptRoot/../../docs/private/homelab/data/inventory.json"

# [cite: 1, 8]
if (-not (Test-Path $inventoryPath)) {
    Write-Error "ERRO: Inventário privado não encontrado em $inventoryPath"
    exit 1
}

# 2. Carregamento dos dados do Lab-Op [cite: 8, 16]
$inventory = Get-Content $inventoryPath | ConvertFrom-Json
. "$PSScriptRoot/Lab-MaestroCommon.ps1"
$script:MaestroRunMarker = Get-Date -Format "yyyyMMdd_HHmmss"
Write-Host "--- [Maestro] Iniciando Turno no Lab-Op (Ref: $Ref, run=$($script:MaestroRunMarker)) ---" -ForegroundColor Cyan
$warningCount = 0
$realFailCount = 0
# Personas that write /tmp/databoar_handler/<persona>_sentinel.txt (#831); web is inline health only.
$script:SentinelPersonas = @(
    "baremetal", "docker", "podman", "dockerswarm", "lxd", "microk8s",
    "target_nfs", "target_cifs", "target_sshfs",
    "target_postgres", "target_mariadb", "target_mongodb"
)
$dispatchedSentinelPersonas = [System.Collections.Generic.List[string]]::new()

# SRE FIX (#950): Fase de Pre-flight Global. O build do artefato de container so
# faz sentido se ALGUM no do inventario tem persona de container
# (docker/podman/dockerswarm) -- mesma regra do $isContainerHost no laco de
# despacho abaixo. Em um run baremetal-only isso evita trabalho/ruido redundante
# (o build incondicional nao crasha o Maestro, mas e desperdicio -- ver #950).
$fleetHasContainerPersona = $false
foreach ($member in $inventory.lab_members) {
    if (($member.personas -contains "docker") -or ($member.personas -contains "podman") -or ($member.personas -contains "dockerswarm")) {
        $fleetHasContainerPersona = $true
        break
    }
}

if ((-not $Collect) -and $fleetHasContainerPersona) {
    & "$PSScriptRoot/Build-ContainerArtefact.ps1"
}
elseif (-not $Collect) {
    Write-Host "   [Maestro] Build de container PULADO: nenhum no com persona container (docker/podman/dockerswarm) no inventario (#950)." -ForegroundColor DarkGray
}

# 3. Processamento dos Membros do Laboratório
$globalReport = foreach ($node in $inventory.lab_members) {

    # #969: reset per-host status before probe so stale ~/.labop-status never reads as current.
    [void](Reset-LabOpStatus -Node $node -RunMarker $script:MaestroRunMarker)

    # Pre-flight Check: Injetando PII via argumentos (Agnosticismo)[cite: 14, 16]
    $status = & "$PSScriptRoot/Get-LabStatus.ps1" -TargetHost $node.hostname -TargetUser $node.user -RunMarker $script:MaestroRunMarker

    # SRE FIX: Se estivermos apenas coletando (-Collect), NÃO dispare a orquestração de novo!
    if ($status.SSH -eq "UP" -and -not $Collect) {

        # Sincronismo da Árvore de Arquivos
        # Inteligente: Prepara o terreno (WorkingTree ou Pasta Efêmera)
        $syncOk = [bool](& "$PSScriptRoot/Sync-WorkingTree.ps1" -Node $node -Ref $Ref)
        if (-not $syncOk) {
            Write-Warning "      [ERROR] Sync obrigatorio falhou em $($node.hostname). Skip de handlers neste turno."
            continue
        }

        # SRE FIX: Condicional rígida para Deploy de Container
        $isContainerHost = ($node.personas -contains "docker") -or ($node.personas -contains "podman") -or ($node.personas -contains "dockerswarm")
        if ($isContainerHost) {
            & "$PSScriptRoot/Sync-ContainerArtefact.ps1" -Node $node
        }

        # #960: gate readiness before handlers (ALARM non-Deep / REMEDIATE -Deep).
        $gateOk = Invoke-LabopGateReadiness -Node $node -Deep:$Deep
        if (-not $gateOk) {
            if ($Deep) { $realFailCount++ }
            continue
        }

        # Despacho para Handlers baseados em Persona [cite: 1]
        # Ordem SRE: container persona primeiro, web por último.
        $orderedPersonas = $node.personas | Sort-Object {
            switch ($_){
                "docker" { 0; break }
                "podman" { 0; break }
                "dockerswarm" { 0; break }
                "web" { 2; break }
                default { 1; break }
            }
        }

        foreach ($persona in $orderedPersonas) {
            $handler = "$PSScriptRoot/handlers/Handle-$persona.ps1"

            if (Test-Path $handler) {
                # O Node contém o path atualizado pelo Sync-WorkingTree (Injeção de Contexto) [cite:1]
                # PowerShell exige que você cole o valor no nome do parâmetro usando dois pontos (:), sem espaços!
                # Assim ele não vai achar no Handler que tem uma variável sobrando sem motivo (ex: sshfs, nfs, etc.)
                $handlerArgs = @{
                    Node = $node
                    Ref = $Ref
                    Deep = $Deep
                    BenchTrack = $BenchTrack
                    BenchRunId = $BenchRunId
                    BenchCompare = $BenchCompare
                    BenchWebPort = $BenchWebPort
                    BenchHealthUrl = $BenchHealthUrl
                }
                & $handler @handlerArgs
                # Capture real handler failures (#825): offline-skip already gated above;
                # exit != 0 here means allowlist rejection, SSH send-keys failure, etc.
                if ($LASTEXITCODE -ne 0) {
                    $realFailCount++
                    Write-Warning "      [REAL FAIL] Handler '$persona' em $($node.hostname) saiu com exit $LASTEXITCODE"
                } elseif ($script:SentinelPersonas -contains $persona) {
                    if (-not ($dispatchedSentinelPersonas -contains $persona)) {
                        $dispatchedSentinelPersonas.Add($persona)
                    }
                }
            } else {
                Write-Warning "      [WARNING] Handler ausente para persona '$persona' em $($node.hostname): $handler"
            }
        }

        # Refresh status for final report after handlers may have updated ~/.labop-status (#969).
        $status = & "$PSScriptRoot/Get-LabStatus.ps1" -TargetHost $node.hostname -TargetUser $node.user -RunMarker $script:MaestroRunMarker
    }

    $status # Acumula para o relatório final [cite: 10]
}

$onlineHosts = @{}
foreach ($status in $globalReport) {
    if (($status.SSH -eq "UP") -and $status.Node) {
        $onlineHosts[$status.Node] = $true
    }
}

# --- [Fase de Agregacao Real] Poll handler sentinels (#949 / #831) ---
if (-not $Collect -and $dispatchedSentinelPersonas.Count -gt 0) {
    $waitHosts = @($onlineHosts.Keys)
    Write-Host "`n--- [Maestro] Aguardando sentinels reais ($($dispatchedSentinelPersonas.Count) persona(s)) ---" -ForegroundColor DarkGray
    & "$PSScriptRoot/Wait-HandlerSentinel.ps1" -Personas @($dispatchedSentinelPersonas) -OnlyHosts $waitHosts
    if ($LASTEXITCODE -ne 0) {
        $realFailCount++
        Write-Warning "      [REAL FAIL] Wait-HandlerSentinel reportou falha ou timeout (resultado de scan/provision, nao so injecao tmux)."
    }
}

# 4. --- [Fase de Coleta SRE] ---
if ($Collect) {
    Write-Host "`n--- [Maestro] Iniciando Coleta de Artefatos (Post-Flight) ---" -ForegroundColor DarkCyan

    if ($onlineHosts.Count -eq 0) {
        Write-Error "Nenhum host com SSH UP no inventario para coletar artefatos."
        exit 6
    }

    foreach ($node in $inventory.lab_members) {
        if ($node.personas -contains "baremetal" -or $node.personas -contains "docker" -or $node.personas -contains "podman" -or $node.personas -contains "target_sshfs" -or $node.personas -contains "target_nfs") {
            if (-not $onlineHosts.ContainsKey($node.hostname)) {
                Write-Warning "      [WARNING] Coleta ignorada para $($node.hostname): host offline (SSH DOWN)."
                $warningCount++
                continue
            }

            $collectOk = & "$PSScriptRoot/Collect-Artifacts.ps1" -Node $node
            if (-not $collectOk) {
                $warningCount++
            }
        }
    }

    # Prepara o Template para o Cursor atuar
    $templatePath = "$PSScriptRoot/../../docs/private/homelab/COMPLETAO_SESSION_TEMPLATE.pt_BR.md"
    $newSessionPath = "$PSScriptRoot/../../docs/private/homelab/reports/COMPLETAO_SESSION_$(Get-Date -Format 'yyyy-MM-dd').md"

    if ((Test-Path $templatePath) -and -not (Test-Path $newSessionPath)) {
        Copy-Item $templatePath $newSessionPath
        Write-Host "   [Docs] Template instanciado em: $newSessionPath" -ForegroundColor Magenta
    }
}

# 5. Relatório Final Consolidado (Feedback Visual SRE) [cite: 10, 16]
Write-Host "`n--- [Status Final do Lab-Op] ---" -ForegroundColor Cyan
$globalReport | Format-Table -AutoSize

if ($Collect -and $warningCount -gt 0) {
    Write-Warning "[Maestro] Rodada concluida com warnings de coleta: $warningCount (sem hard-fail)."
}

# Aggregate REAL handler failures into exit code (#825).
# Offline-skip and Safe-Hold do NOT increment $realFailCount — only genuine handler errors do.
if ($realFailCount -gt 0) {
    Write-Error "[Maestro] $realFailCount handler(s) retornaram exit != 0 (falhas reais, nao offline-skip)."
    exit 1
}

exit 0
